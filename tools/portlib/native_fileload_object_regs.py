"""Exact-main bounded original FileLoad X20/X22 register-definition audit.

Enumerate possible register *write origins* at already proven native
status callsites and context-error guard. Do not infer class identity,
ownership, object type, destructor, async completion or safe hook ABI.
Original AAPCS64 callee-saved preservation is an explicit assumption.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from .native_cpk_graph import MAIN_SHA256
from .native_cpk_cfg import _edges
from .native_fileload_corridor_cfg import ENTRY, END
from .native_fileload_status import inspect as inspect_status
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


def _trace_register(graph, instructions, reg, start, sites, low, high):
    """Forward reaching-def union with kill on an actual write to X/Wn.

    Calls are assumed to return and respect the ABI-preserved X20/X22
    registers, but this is not evidence about *real* foreign callbacks.
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
        # Under AAPCS64, X1/X2 are caller-saved; an opaque BL/BLR
        # invalidates any incoming X1/X2 argument value even if Capstone
        # does not report these implicit ABI effects. X20/X22 are
        # callee-saved and remain modeled as preserved across calls.
        clobber=(reg in ("x1","x2") and
                 ins.mnemonic in ("bl","blr","blraa","blrab"))
        if _written(ins, reg) or clobber:
            definitions[pc] = {
                "at":hex(pc), "register":reg,
                "instruction":f"{ins.mnemonic} {ins.op_str}".strip(),
                "kind":"caller_saved_call_clobber" if clobber
                       else "original_instruction_write",
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
                    "kind":("incoming_caller_saved_argument_value"
                            if reg in ("x1","x2")
                            else "incoming_callee_saved_value"),
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
    traces={}
    for reg in ("x20","x22","x1","x2"):
        sites={k:site for k,(r,site) in SITES.items() if r==reg}
        traces[reg]=_trace_register(graph,ins,reg,ENTRY,sites,ENTRY,END)
    if status["verified_status_argument_and_callsite_words"][1]["at"]!="0x116f51c":
        raise ValueError("Status caller word order changed")
    for name,(reg,site) in SITES.items():
        if not traces[reg]["sites"][name]["possible_reaching_writes"]:
            raise ValueError("Original object register origin missing: "+name)
        if site not in ins:
            raise ValueError("Original object source site no longer decoded")
    # The original machine instructions and reaching definitions now
    # distinguish the status object source X2 from the guard source X1.
    # These are register mappings, not class/ownership/lifetime proofs.
    pinned = [
        ("first_status_X20_argument_move", "x20",
         "0x116f434", "mov x20, x2", "X2"),
        ("second_status_X20_argument_move", "x20",
         "0x116f434", "mov x20, x2", "X2"),
        ("second_guard_X22_field_base", "x22",
         "0x116f438", "mov x22, x1", "X1")
    ]
    alias_proofs = []
    entry_checks = {
        "X2": ("x2","X2_before_X20_capture"),
        "X1": ("x1","X1_before_X22_capture")
    }
    for name,reg,at,phrase,source in pinned:
        origin = traces[reg]["sites"][name]["possible_reaching_writes"]
        if len(origin) != 1 or origin[0]["at"] != at or origin[0]["instruction"] != phrase:
            raise ValueError("Pinned native caller register provenance changed: "+name)
        origin_pc = int(at,16)
        src_reg,src_site=entry_checks[source]
        src_origins=traces[src_reg]["sites"][src_site]["possible_reaching_writes"]
        unchanged=(len(src_origins)==1 and src_origins[0]["kind"]==
                   "incoming_caller_saved_argument_value" and src_origins[0]["at"] is None)
        alias_proofs.append({
            "at":at, "original_word_le":code[origin_pc:origin_pc+4].hex(),
            "original_instruction":phrase, "source_register_at_copy":source,
            "destination_saved_register":reg.upper(),
            "observed_at":traces[reg]["sites"][name]["at"],
            "source_register_inbound_origin_candidates":src_origins,
            "source_register_unchanged_since_entry_in_bounded_static_CFG":unchanged,
            "argument_source_AAPCS64_caller_saved_call_clobbers_modeled":True,
            "pointer_type_and_ownership_proven":False
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
        "AAPCS64_callee_saved_registers_assumed_not_runtime_proven":True,
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
