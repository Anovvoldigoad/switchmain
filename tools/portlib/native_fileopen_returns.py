"""Read-only, SHA-gated AArch64 FileOpen return-register provenance census.

A bounded *syntactic* CFG is used. Successor paths assume that BL/BLR
returns; their W0 outcomes are UNKNOWN. Native CRI success/error semantics,
function ownership, file lifetime and hook ABI are NOT inferred.

Important: All 'returns' below means all CFG-reachable RETs *inside this
bounded analysis window*, not a complete function boundary proof.
"""
from collections import deque
import hashlib
import re

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from .native_cpk_graph import MAIN_SHA256
from .native_cpk_cfg import REGIONS, _edges, TERMINALS
from .nso_profile import segments

ENTRY, SIZE = REGIONS["file_open_1170fb0"]
END = ENTRY + SIZE
MAX_REACHED = 384
MAX_REACHING_DEFS = 96

# These are provenance *labels*, not evaluated AArch64 symbolic values.
INITIAL = "entry_w0_undefined_argument"
CALLER_SAVED = "unknown_caller_saved_call_return"


def _reads_w0(ins):
    """Capstone access flags may be conservative: use only write set for evidence."""
    _, written = ins.regs_access()
    return any(ins.reg_name(r).lower() in ("w0", "x0") for r in written)


def _definition(pc, ins):
    """W0 def site (or none). A call return overwrites W0 under AAPCS64.

    Interpret explicit MOV immediates only; all other writes remain
    unclassified. Do not infer booleans, positive errors or archive origin.
    """
    if ins.mnemonic in ("bl", "blr", "blraa", "blrab"):
        return {"at": hex(pc), "kind": "unresolved_call_return",
                "instruction": f"{ins.mnemonic} {ins.op_str}",
                "w0_observed_value": None}
    if not _reads_w0(ins):
        return None
    op = ins.op_str.lower().replace(" ", "")
    pattern = re.fullmatch(r"(?:w0|x0),#(-?0x[0-9a-f]+|-?\d+)", op)
    if ins.mnemonic == "mov" and pattern:
        n = int(pattern.group(1), 0)
        return {"at": hex(pc), "kind": "literal_register_assignment",
                "instruction": f"{ins.mnemonic} {ins.op_str}",
                "w0_observed_value": n & 0xffffffff}
    return {"at": hex(pc), "kind": "write_from_unresolved_register_or_memory",
            "instruction": f"{ins.mnemonic} {ins.op_str}",
            "w0_observed_value": None}


def _build_graph(text, start=ENTRY, end=END):
    dis = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    dis.detail = True
    graph = {}
    decoded = {}
    for pc in range(start, end, 4):
        r = list(dis.disasm(text[pc:pc+4], pc))
        if len(r) != 1 or r[0].size != 4:
            continue
        ins = r[0]
        decoded[pc] = ins
        graph[pc] = _edges(pc, ins.mnemonic, ins.op_str)
    return graph, decoded


def _trace(graph, decoded, start=ENTRY, lo=ENTRY, hi=END):
    """Monotone reaching-def union on every syntactically reached CFG edge.

    A single return may have multiple possible reaching definitions.
    Out-of-window and unresolved indirect edges never become proof of RET.
    """
    if start not in decoded:
        raise ValueError("Pinned FileOpen entrypoint undecodable")
    queue = deque([start])
    reaching = {start: {INITIAL}}
    processed = set()
    returns = {}
    escapes = {}
    unresolved_indirect_calls = set()
    defs = {}
    while queue:
        pc = queue.popleft()
        processed.add(pc)
        if len(processed) > MAX_REACHED:
            raise ValueError("FileOpen analysis node budget exceeded")
        ins = decoded[pc]
        definition = _definition(pc, ins)
        if definition is not None:
            defs[pc] = definition
        out = {f"def@{pc:x}"} if definition is not None else set(reaching[pc])
        if len(out) > MAX_REACHING_DEFS:
            raise ValueError("FileOpen reaching-def bound exceeded")
        if ins.mnemonic in ("ret", "retaa", "retab"):
            returns[pc] = set(reaching[pc])
        for kind, target in graph[pc]:
            if kind == "call":
                continue
            if target is None:
                if kind == "indirect_call_unresolved":
                    unresolved_indirect_calls.add(pc)
                else:
                    escapes[(pc, kind, None)] = True
                continue
            if not lo <= target < hi:
                escapes[(pc, kind, target)] = True
                continue
            if target not in decoded:
                escapes[(pc, "undecodable_successor", target)] = True
                continue
            current = reaching.setdefault(target, set())
            added = out - current
            if added:
                current.update(added)
                if len(current) > MAX_REACHING_DEFS:
                    raise ValueError("FileOpen reaching-def merge bound exceeded")
                queue.append(target)
    # A predecessor can reach RET and then change its reaching set through
    # a loop: use the final converged state, not the first-visit snapshot.
    for pc in returns:
        returns[pc] = set(reaching[pc])
    return {"reachable": processed, "definitions": defs, "returns": returns,
            "escapes": escapes, "unresolved_indirect_calls":
                unresolved_indirect_calls, "reaching": reaching}


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Exact original Switch v1.70 main SHA256 required")
    va, code, _ = segments(nso)[0]
    if va != 0 or END > len(code):
        raise ValueError("Pinned original executable geometry invalid")
    graph, decoded = _build_graph(code)
    tr = _trace(graph, decoded)
    if not tr["reachable"] or ENTRY not in tr["reachable"]:
        raise ValueError("Pinned FileOpen graph empty")
    # A capped analysis with only a window must never silently claim
    # function-wide completeness if a branch crosses the boundary.
    rows = []
    for pc in sorted(tr["returns"]):
        ins = decoded[pc]
        origins = []
        for label in sorted(tr["returns"][pc]):
            if label == INITIAL:
                origins.append({"kind": "entry_w0_unknown", "at": None,
                                "w0_observed_value": None})
            else:
                origin_pc = int(label.split("@", 1)[1], 16)
                if origin_pc not in tr["definitions"]:
                    raise ValueError("Lost W0 definition")
                origins.append(tr["definitions"][origin_pc])
        rows.append({"at": hex(pc), "word_le": code[pc:pc+4].hex(),
                     "instruction": f"{ins.mnemonic} {ins.op_str}".strip(),
                     "reaching_w0_definitions": origins,
                     "single_constant_w0_only": len(origins) == 1
                         and origins[0]["kind"] == "literal_register_assignment",
                     "actual_runtime_return_value_proven": False})
    exits = [{"from":hex(pc),"kind":kind,
              "target":hex(target) if target is not None else None}
             for pc,kind,target in sorted(
                 tr["escapes"],key=lambda x:(x[0],x[1],x[2] or 0))]
    return {
        "status": "ORIGINAL_PINNED_FILEOPEN_BOUNDED_RETURN_W0_PROVENANCE_ONLY",
        "main_sha256": digest,
        "entry_candidate": hex(ENTRY), "window_end_exclusive": hex(END),
        "bounded_window_not_function_extent": True,
        "reachable_decoded_instructions": len(tr["reachable"]),
        "all_reachable_within_window_return_sites": rows,
        "reachable_return_sites": len(rows),
        "other_terminations_or_out_of_window": exits,
        "indirect_calls_with_unknown_ABI": [
            hex(x) for x in sorted(tr["unresolved_indirect_calls"])],
        "reaching_w0_definition_sites": [
            {**tr["definitions"][pc], "word_le":code[pc:pc+4].hex()}
            for pc in sorted(tr["definitions"]) if pc in tr["reachable"]],
        "paths_assume_extern_calls_return": True,
        "caller_register_w0_is_32bit_truncation_of_x0": True,
        "native_CRI_zero_means_failure_proven": False,
        "real_FileOpen_return_values_tested": False,
        "all_function_exits_proven": False,
        "X20_ownership_and_object_lifetime_proven": False,
        "callback_async_unbind_or_archive_precedence_proven": False,
        "hook_ABI_safe_proven": False,
        "hook_installed": False,
        "Uzuy_tested": False, "gameplay_verified": False,
        "full_moddingapi": False
    }
