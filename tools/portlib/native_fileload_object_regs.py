"""Exact-main bounded original FileLoad X20/X22 register-definition audit.

Enumerate possible register *write origins* at already proven native
status callsites and context-error guard. Do not infer class identity,
ownership, object type, destructor, async completion or safe hook ABI.
Register preservation across calls is proven only from bounded original callee code.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from .native_cpk_graph import MAIN_SHA256
from .native_cpk_cfg import _edges
from .native_fileload_corridor_cfg import ENTRY, END
from .native_fileload_status import inspect as inspect_status
from .native_fileload_call_targets import inspect as inspect_call_targets
from .nso_profile import segments

SITES = {
    "first_status_X20_argument_move": ("x20", 0x116F51C),
    "second_status_X20_argument_move": ("x20", 0x116F5BC),
    "second_guard_X22_field_base": ("x22", 0x116F5AC),
    "X2_before_X20_capture": ("x2", 0x116F434),
    "X1_before_X22_capture": ("x1", 0x116F438),
}
MAX_NODES = 256
MAX_DEFINITIONS = 64


def _written(ins, reg):
    _, written = ins.regs_access()
    aliases = {reg.lower(), "w"+reg[1:]} if reg.startswith("x") else {reg.lower()}
    return any(ins.reg_name(x).lower() in aliases for x in written)


def _trace_register(graph, instructions, reg, start, sites, low, high,
                    call_preservation=None):
    """Forward reaching-def union with conservative direct-callee call barriers.

    A call preserves a tracked register only when its exact bounded target and
    every nested direct callee are proven not to write it on any returning path.
    No platform calling convention or foreign-callback behavior is assumed.
    """
    entry = f"entry_{reg}_caller_value"
    incoming = {start: {entry}}
    q = deque([start])
    done = set()
    definitions = {}
    escapes = set()
    indirect_calls = set()
    while q:
        pc = q.popleft()
        done.add(pc)
        if len(done) > MAX_NODES:
            raise ValueError("Object-register CFG node bound exceeded")
        ins = instructions.get(pc)
        if ins is None:
            raise ValueError("Undecodable reached instruction in register audit")
        call_edges = [target for kind, target in graph[pc] if kind == "call"]
        indirect_call = any(kind == "indirect_call_unresolved"
                            for kind, _ in graph[pc])
        call_present = bool(call_edges or indirect_call)
        proof = (call_preservation or {}).get(pc, {}).get(reg)
        call_clobber = call_present and not (proof and proof.get("preserved") is True)
        if _written(ins, reg) or call_clobber:
            definitions[pc] = {
                "at":hex(pc), "register":reg,
                "instruction":f"{ins.mnemonic} {ins.op_str}".strip(),
                "kind":"unproven_call_clobber" if call_clobber
                       else "original_instruction_write",
                "callee_targets":[hex(x) for x in call_edges],
                "callee_preservation_reason":(
                    proof.get("reason") if proof else
                    ("INDIRECT_CALL_TARGET_UNRESOLVED" if indirect_call else
                     "NO_EXACT_CALLEE_PRESERVATION_PROOF")),
                "assignment_source_semantics_resolved":False}
            out={f"def@{pc:x}"}
        else:
            out=set(incoming[pc])
        for kind, nxt in graph[pc]:
            if kind=="call":
                continue
            if nxt is None:
                if kind=="indirect_call_unresolved":
                    indirect_calls.add(pc)
                else:
                    escapes.add((pc,kind,None))
                continue
            if not low<=nxt<high:
                escapes.add((pc,kind,nxt))
                continue
            if nxt not in instructions:
                escapes.add((pc,"undecodable",nxt))
                continue
            state=incoming.setdefault(nxt,set())
            delta=out-state
            if delta:
                state.update(delta)
                if len(state)>MAX_DEFINITIONS:
                    raise ValueError("Reaching object-register def bound exceeded")
                q.append(nxt)
    result={}
    for name,site in sites.items():
        labels=incoming.get(site)
        if labels is None:
            raise ValueError("Required pinned native status/guard site unreachable: "+hex(site))
        origins=[]
        for label in sorted(labels):
            if label==entry:
                origins.append({
                    "at":None,
                    "kind":"incoming_register_value",
                    "register":reg,
                    "source_identity_proven":False})
            else:
                pc=int(label.split("@")[1],16)
                origins.append({**definitions[pc]})
        result[name]={"at":hex(site), "possible_reaching_writes":origins,
                      "all_runtime_paths_executed":False}
    return {
        "sites":result,
        "reachable_instructions":len(done),
        "definition_sites":[definitions[pc] for pc in sorted(definitions)],
        "unresolved_exits":[{"from":hex(pc),"kind":kind,
                             "target":hex(nxt) if nxt is not None else None}
                            for pc,kind,nxt in sorted(escapes,
                                key=lambda e:(e[0],e[1],e[2] or 0))],
        "indirect_calls_without_verified_target":[hex(x) for x in sorted(indirect_calls)]
    }


def inspect(nso):
    actual=hashlib.sha256(nso).hexdigest()
    if actual!=MAIN_SHA256:
        raise ValueError("Exact SHA-pinned v1.70 original main mandatory")
    status=inspect_status(nso)
    va,code,_=segments(nso)[0]
    if va or END>len(code):
        raise ValueError("Original executable layout mismatch")
    cs=Cs(CS_ARCH_ARM64,CS_MODE_ARM)
    cs.detail=True
    ins={}
    graph={}
    for pc in range(ENTRY,END,4):
        one=list(cs.disasm(code[pc:pc+4],pc))
        if len(one)==1 and one[0].size==4:
            ins[pc]=one[0]
            graph[pc]=_edges(pc,one[0].mnemonic,one[0].op_str)
    call_report=inspect_call_targets(nso)
    call_preservation={
        int(row["site"],16):row["registers"]
        for row in call_report["pre_status_call_register_preservation"]
    }
    traces={}
    for reg in ("x20","x22","x1","x2"):
        sites={k:site for k,(r,site) in SITES.items() if r==reg}
        traces[reg]=_trace_register(
            graph,ins,reg,ENTRY,sites,ENTRY,END,call_preservation
        )
    if status["verified_status_argument_and_callsite_words"][1]["at"]!="0x116f51c":
        raise ValueError("Status caller word order changed")
    for name,(reg,site) in SITES.items():
        if not traces[reg]["sites"][name]["possible_reaching_writes"]:
            raise ValueError("Original object register origin missing: "+name)
        if site not in ins:
            raise ValueError("Original object source site no longer decoded")
    # The two MOV instructions capture caller-entry register values.
    # Their later use is separately gated by exact direct-callee code proofs.
    capture_specs = [
        ("X2_to_X20_capture", "x20", 0x116F434, "mov x20, x2",
         "x2", "X2_before_X20_capture",
         ("first_status_X20_argument_move", "second_status_X20_argument_move")),
        ("X1_to_X22_capture", "x22", 0x116F438, "mov x22, x1",
         "x1", "X1_before_X22_capture",
         ("second_guard_X22_field_base",)),
    ]
    alias_proofs = []
    for name, reg, at, phrase, src_reg, src_site, observations in capture_specs:
        if at not in ins or ins[at].mnemonic != "mov" or ins[at].op_str != phrase:
            raise ValueError("Pinned native capture instruction changed: " + name)
        src_origins = traces[src_reg]["sites"][src_site]["possible_reaching_writes"]
        unchanged = (len(src_origins) == 1 and src_origins[0]["kind"] ==
                     "incoming_register_value" and src_origins[0]["at"] is None)
        observed = []
        for observation in observations:
            origins = traces[reg]["sites"][observation]["possible_reaching_writes"]
            capture_only = (len(origins) == 1 and origins[0].get("at") == hex(at)
                            and origins[0].get("kind") == "original_instruction_write")
            observed.append({
                "site": traces[reg]["sites"][observation]["at"],
                "possible_reaching_writes": origins,
                "capture_value_only_reaches_observation": capture_only,
            })
        alias_proofs.append({
            "name": name,
            "capture_at": hex(at),
            "capture_word_le": code[at:at+4].hex(),
            "capture_instruction": phrase,
            "source_register_at_capture": src_reg.upper(),
            "destination_register": reg.upper(),
            "source_register_inbound_origin_candidates": src_origins,
            "source_register_unchanged_since_entry_in_bounded_static_CFG": unchanged,
            "observations": observed,
            "preservation_to_all_observations_proven": all(
                x["capture_value_only_reaches_observation"] for x in observed
            ),
            "pointer_type_and_ownership_proven": False,
        })
    return {
        "status":"SHA_PINNED_ORIGINAL_FILELOAD_X20_X22_REACHING_WRITE_SITES_ONLY",
        "original_caller_argument_register_alias_witnesses":alias_proofs,
        "original_main_sha256":actual,
        "original_entry_candidate":hex(ENTRY),
        "window_end_exclusive":hex(END),
        "status_callsite_witnesses":["0x116f51c MOV X0,X20",
                                      "0x116f5bc MOV X0,X20"],
        "separate_guard_witness":"0x116f5ac LDR W8,[X22,#0x1D8]",
        "register_traces":traces,
        "call_preservation_proofs":call_report["pre_status_call_register_preservation"],
        "call_preservation_method":call_report["call_preservation_method"],
        "no_platform_calling_convention_assumed":True,
        "AAPCS64_callee_saved_registers_assumed_not_runtime_proven":False,
        "register_write_origin_not_pointer_class_or_ownership":True,
        "X1_X2_entry_argument_proven_at_capture_only_if_unmodified":True,
        "all_function_paths_proven":False,
        "object_X20_type_or_lifetime_verified":False,
        "X22_guard_context_type_verified":False,
        "source_archive_priority_verified":False,
        "native_CRI_async_unbind_and_destructor_verified":False,
        "safe_hook_ABI_proven":False,
        "hook_added":False,
        "Uzuy_gameplay_verified":False,
        "full_moddingapi":False
    }
