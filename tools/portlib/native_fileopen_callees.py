"""SHA256-pinned read-only interprocedural FileOpen evidence.

The preceding FileOpen census identified three branch sites and four calls.
Here we recover incoming register/flag writer *candidates* and follow each
direct BL into a bounded original-text CFG.  The output is machine evidence,
NOT an inferred CRI ABI, control-path feasibility or proof of lifecycle.
"""
import hashlib
from collections import deque

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileopen_returns import ENTRY, END, _build_graph, _trace
from .native_fileopen_branch_dependencies import inspect as inspect_branches
from .native_cpk_cfg import _edges
from .nso_profile import segments

CALLEE_SPAN = 0x300
MAX_CALLEE_NODES = 192
MAX_BACKWARD_NODES = 384
MAX_WRITER_HOPS = 200
CALLERSAVED = {f"x{i}" for i in range(19)} | {"x30"}

def _target_register(ins):
    """Register consulted by an original native conditional branch."""
    m = ins.mnemonic
    if m.startswith("b.") or m in ("b.cond",):
        return "nzcv"
    if m in ("cbz", "cbnz", "tbz", "tbnz"):
        reg = ins.op_str.split(",", 1)[0].strip().lower()
        if reg.startswith(("x", "w")) and reg[1:].isdigit():
            return "x"+reg[1:]
    raise ValueError("Unexpected native conditional branch form: "+m)

def _is_writer(ins, register):
    if ins.mnemonic in ("bl", "blr", "blraa", "blrab"):
        # Calls can clobber NZCV and all AAPCS64 caller-saved registers.
        if register == "nzcv" or register in CALLERSAVED:
            return "unknown_call_clobber"
    _, writes = ins.regs_access()
    targets = ({register} if register == "nzcv" else
               {register, "w"+register[1:]})
    if any(ins.reg_name(x).lower() in targets for x in writes):
        return "native_instruction_write"
    # Capstone may not explicitly report NZCV for all flag setting
    # aliases; flag-origin conservative fallback prevents false proof.
    if register == "nzcv" and (ins.mnemonic in
        ("cmp", "cmn", "tst", "ccmp", "ccmn", "fcmp", "fcmpe") or
        ins.mnemonic.endswith("s") and ins.mnemonic in
        ("adds", "subs", "ands", "bics", "adcs", "sbcs", "negs")):
        return "native_flag_setting_instruction"
    return None

def _predecessors(graph, reachable, lo, hi):
    backwards = {pc: set() for pc in reachable}
    for src in reachable:
        for kind, dst in graph[src]:
            if kind == "call" or dst is None:
                continue
            if lo <= dst < hi and dst in backwards:
                backwards[dst].add(src)
    return backwards

def _writer_origins(pred, decoded, site, register, entry=ENTRY):
    """Enumerate nearest writers on every possible reverse CFG path.

    The path analysis ignores branch predicates and assumes calls return.
    It has no argument-alias, heap memory or original function ABI proof.
    """
    queue = deque([(site, 0)])
    seen = set()
    origins = {}
    unresolved = []
    while queue:
        at, depth = queue.popleft()
        if at in seen:
            continue
        seen.add(at)
        if len(seen) > MAX_BACKWARD_NODES:
            raise ValueError("FileOpen reverse CFG node budget exceeded")
        if depth > MAX_WRITER_HOPS:
            unresolved.append({"at":hex(at),"reason":"reverse_path_budget"})
            continue
        if at == entry:
            unresolved.append({"at":hex(at),"reason":"entry_argument_or_flags_unknown"})
            continue
        parents = pred.get(at)
        if not parents:
            unresolved.append({"at":hex(at),"reason":"no_predecessors_in_analysis_window"})
            continue
        for parent in sorted(parents):
            ins = decoded.get(parent)
            if ins is None:
                unresolved.append({"at":hex(parent),"reason":"undecoded_predecessor"})
                continue
            kind = _is_writer(ins, register)
            if kind:
                origins[parent] = {"at":hex(parent),"kind":kind,
                                   "instruction":(ins.mnemonic+" "+ins.op_str).strip()}
            elif parent not in seen:
                queue.append((parent,depth+1))
    return {"consulted_register":register,
            "possible_immediate_reaching_writers":[origins[a] for a in sorted(origins)],
            "unresolved_entry_or_bounded_paths":unresolved,
            "single_writer_on_all_feasible_paths_proven":False}

def _decode_window(text, start, stop):
    cs = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    cs.detail = True
    decoded, graph = {}, {}
    for pc in range(start,stop,4):
        one = list(cs.disasm(text[pc:pc+4],pc))
        if len(one) == 1 and one[0].size == 4:
            decoded[pc] = one[0]
            graph[pc] = _edges(pc,one[0].mnemonic,one[0].op_str)
    return decoded, graph

def _callee_walk(graph, decoded, start, lo, hi):
    q = deque([start])
    seen = set()
    returns = set()
    other_exits = set()
    calls = set()
    memory = {}
    while q:
        at = q.popleft()
        if at in seen:
            continue
        if len(seen) >= MAX_CALLEE_NODES:
            raise ValueError("Native callee bounded CFG node limit exceeded")
        seen.add(at)
        if not lo <= at < hi:
            other_exits.add((at,"out_of_bounded_window"))
            continue
        ins = decoded.get(at)
        if ins is None:
            other_exits.add((at,"undecoded_instruction"))
            continue
        m = ins.mnemonic
        if m in ("ldr","ldrb","ldrh","ldrsw","ldur","str","strb","strh",
                 "stur","ldp","stp","ldxr","stxr"):
            memory[at] = (m+" "+ins.op_str)
        if m in ("ret","retaa","retab"):
            returns.add(at)
        if m in ("bl","blr","blraa","blrab"):
            calls.add(at)
        for kind, dst in graph[at]:
            if kind == "call":
                continue
            if dst is None:
                if kind not in ("return_or_indirect_terminator",
                                "indirect_call_unresolved"):
                    other_exits.add((at,kind))
                if kind == "return_or_indirect_terminator" and m not in (
                        "ret","retaa","retab"):
                    other_exits.add((at,"indirect_branch_terminator"))
            elif dst not in seen:
                q.append(dst)
    return {"visited":len(seen),
            "return_sites":[hex(x) for x in sorted(returns)],
            "external_or_indirect_calls":[hex(x) for x in sorted(calls)],
            "other_exits":[{"at":hex(a),"kind":k}
                           for a,k in sorted(other_exits)],
            "memory_access_samples":[{"at":hex(a),"instruction":memory[a]}
                                     for a in sorted(memory)[:32]],
            "memory_access_sample_truncated":len(memory)>32}

def _call_target_report(text, site, instr, max_span=CALLEE_SPAN):
    byteword = text[site:site+4]
    branch = direct_branch(int.from_bytes(byteword,"little"),site)
    result = {"at":hex(site), "word_le":byteword.hex(),
              "instruction":(instr.mnemonic+" "+instr.op_str).strip(),
              "direct_original_target":None,
              "target_inside_original_text":False,
              "target_window_is_not_function_boundary":True,
              "callee_semantics_and_abi_proven":False}
    if instr.mnemonic == "bl" and branch and branch[0] == "BL":
        target = branch[1]
        result["direct_original_target"] = hex(target)
        if target % 4 or not (0 <= target < len(text) - 4):
            result["unresolved_reason"] = "direct_target_not_in_original_text"
            return result
        result["target_inside_original_text"] = True
        end = min(target+max_span,len(text))
        end -= (end-target)%4
        decoded, graph = _decode_window(text,target,end)
        result["target_first_word_le"] = text[target:target+4].hex()
        result["bounded_target_window_sha256"] = hashlib.sha256(text[target:end]).hexdigest()
        result["window_end_exclusive"] = hex(end)
        result["bounded_callee_cfg"] = _callee_walk(graph,decoded,target,target,end)
        # Exact original words, but sequential transcript can cross actual
        # function boundaries; neither size nor call ownership is proven.
        result["target_first_words"] = [
            {"at":hex(pc),"word_le":text[pc:pc+4].hex(),
             "instruction":(decoded[pc].mnemonic+" "+decoded[pc].op_str).strip()
                             if pc in decoded else "UNDECODED"}
            for pc in range(target,min(target+0x60,end),4)]
    else:
        result["unresolved_reason"]="indirect_call_target_register_not_resolved"
    return result

def inspect(nso):
    digest=hashlib.sha256(nso).hexdigest()
    if digest!=MAIN_SHA256:
        raise ValueError("Exact pinned original Switch 1.70 main required")
    va,code,_=segments(nso)[0]
    if va or END>len(code):
        raise ValueError("Original executable NSO geometry mismatch")
    previous=inspect_branches(nso)
    graph,decoded=_build_graph(code)
    tr=_trace(graph,decoded)
    reachable=tr["reachable"]
    reverse=_predecessors(graph,reachable,ENTRY,END)
    branches=[]
    for item in previous["conditional_branch_edge_census"]:
        at=int(item["at"],16)
        if at not in reachable:
            raise ValueError("Original conditional branch no longer reachable")
        instruction=decoded[at]
        register=_target_register(instruction)
        producer=_writer_origins(reverse,decoded,at,register)
        branches.append({**item,
                         "source_kind": "condition_flags" if register=="nzcv" else
                                        "register_value",
                         "original_machine_condition_source":producer,
                         "predicate_feasibility_proven":False})
    calls=[]
    for item in previous["reachable_external_callsite_census"]:
        at=int(item["at"],16)
        if at not in reachable:
            raise ValueError("Original FileOpen caller list changed")
        report=_call_target_report(code,at,decoded[at])
        calls.append({**item,"original_target_evidence":report})
    if len(branches)!=3 or len(calls)!=4:
        raise ValueError("Pinned original FileOpen branch/callsite totals changed")
    return {
        "status":"ORIGINAL_SHA_PINNED_FILEOPEN_CALLEE_AND_BRANCH_SOURCE_BOUNDED_ONLY",
        "original_main_sha256":digest,
        "native_FileOpen_entry":hex(ENTRY),
        "native_FileOpen_analysis_end_exclusive":hex(END),
        "branch_sites_with_source_producers":branches,
        "original_callsite_target_windows":calls,
        "original_condition_site_count":len(branches),
        "original_callsite_count":len(calls),
        "callee_windows_are_not_function_boundaries":True,
        "register_sources_are_syntactic_not_feasible":True,
        "calls_assumed_to_return":True,
        "native_CRI_error_semantics_proven":False,
        "object_layout_and_ownership_proven":False,
        "callback_lock_async_unbind_destructor_proven":False,
        "archive_precedence_proven":False,
        "safe_new_hook_ABI_proven":False,
        "actual_game_runtime_verified":False,
        "full_moddingapi":False,
        "ready_for_gameplay_test":False,
        "emulator_tested":False
    }
