"""Source-pinned FileOpen branch and call dependency audit; no runtime inference.

This is an intra-window, path-insensitive syntactic graph. Conditional edge
reachability does NOT prove feasible paths, CRI return/error semantics, or ABI.
Calls are modeled as returning, without knowing their side effects.
"""
import hashlib
from collections import deque
from .native_cpk_graph import MAIN_SHA256
from .native_fileopen_returns import ENTRY, END, _build_graph, _trace
from .nso_profile import segments

RET_ONE = 0x1171068
RET_ZERO = 0x117107C
MAX_NODES = 384

def _reachable(graph, start, stops, lo, hi):
    queue = deque([start])
    seen = set()
    witnesses = {}
    parents = {start: None}
    escapes = []
    while queue:
        pc = queue.popleft()
        if pc in seen:
            continue
        seen.add(pc)
        if len(seen) > MAX_NODES:
            raise ValueError("FileOpen branch exploration exceeds budget")
        if pc in stops:
            path = []
            at = pc
            while at is not None:
                path.append(at)
                at = parents[at]
            witnesses[pc] = list(reversed(path))
            continue
        if pc not in graph or not lo <= pc < hi:
            escapes.append(pc)
            continue
        for kind, target in graph[pc]:
            if kind == "call":
                continue
            if target is not None and target not in parents:
                parents[target] = pc
                queue.append(target)
    return {"reachable_returns": witnesses, "visited_count": len(seen),
            "escapes": escapes}

def _branch_census(graph, decoded, code, reachable, ret_sites, lo, hi):
    rows = []
    for at in sorted(reachable):
        if at not in decoded:
            raise ValueError("Reachable undecodable instruction " + hex(at))
        ins = decoded[at]
        edges = [(k, dest) for k, dest in graph[at] if k != "call"]
        if len(edges) < 2:
            continue
        successors = []
        for kind, dest in edges:
            if dest is None:
                reached = {"reachable_returns": {}, "escapes": [at]}
            else:
                reached = _reachable(graph, dest, ret_sites, lo, hi)
            successors.append({
                "kind": kind, "target": hex(dest) if dest is not None else None,
                "syntactically_reaches_return": [
                    hex(x) for x in sorted(reached["reachable_returns"])],
                "shortest_syntactic_witness_paths": {
                    hex(x): [hex(v) for v in path]
                    for x, path in sorted(reached["reachable_returns"].items())},
                "unresolved_or_out_of_window": bool(reached["escapes"])
            })
        rows.append({
            "at": hex(at), "word_le": code[at:at+4].hex(),
            "instruction": (ins.mnemonic+" "+ins.op_str).strip(),
            "successors": successors, "feasibility_proven": False
        })
    return rows

def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Exact original Switch main SHA256 required")
    va, code, _ = segments(nso)[0]
    if va != 0 or END > len(code):
        raise ValueError("Pinned original text geometry mismatch")
    graph, decoded = _build_graph(code)
    trace = _trace(graph, decoded)
    reached = trace["reachable"]
    returns = set(trace["returns"])
    if returns != {RET_ONE, RET_ZERO} or trace["escapes"]:
        raise ValueError("Original bounded FileOpen returns/escapes changed")
    branches = _branch_census(graph, decoded, code, reached, returns, ENTRY, END)
    calls = []
    for at in sorted(reached):
        ins = decoded[at]
        if ins.mnemonic not in ("bl", "blr", "blraa", "blrab"):
            continue
        successors = [dest for kind, dest in graph[at]
                      if kind.startswith("fallthrough") and dest is not None]
        outcomes = set()
        for dest in successors:
            outcomes.update(_reachable(graph, dest, returns, ENTRY, END)["reachable_returns"])
        calls.append({
            "at": hex(at), "word_le": code[at:at+4].hex(),
            "instruction": (ins.mnemonic+" "+ins.op_str).strip(),
            "postcall_reachable_returns": [hex(x) for x in sorted(outcomes)],
            "callee_effect_and_return_unknown": True
        })
    # Capture the two literal-def witnesses from original pinned instructions,
    # not by interpreting any branch as 'success' or 'failure'.
    literal = {RET_ONE: (0x1171058, 1), RET_ZERO: (0x117106C, 0)}
    endpoints = []
    for ret, (definition, value) in literal.items():
        origins = trace["returns"][ret]
        if origins != {"def@%x" % definition}:
            raise ValueError("Pinned FileOpen return literal source changed")
        observed = trace["definitions"][definition]["w0_observed_value"]
        if observed != value:
            raise ValueError("Pinned FileOpen return literal value changed")
        endpoints.append({
            "ret": hex(ret), "definition": hex(definition),
            "definition_word_le": code[definition:definition+4].hex(),
            "constant_w0": value,
            "shortest_syntactic_entry_path": [
                hex(x) for x in _reachable(graph, ENTRY, {ret}, ENTRY, END)
                ["reachable_returns"][ret]],
            "runtime_return_condition_proven": False
        })
    return {
        "status": "PINNED_FILEOPEN_BRANCH_PREDICATE_AND_CALL_DEPENDENCIES_STATIC_ONLY",
        "original_main_sha256": digest, "entry": hex(ENTRY),
        "analysis_end_exclusive": hex(END),
        "reachable_instruction_count": len(reached),
        "bounded_return_literal_witnesses": endpoints,
        "conditional_branch_edge_census": branches,
        "reachable_external_callsite_census": calls,
        "calls_assumed_to_return_with_unknown_effects": True,
        "path_feasibility_or_CRI_error_semantics_proven": False,
        "callback_async_rollback_unbind_destructor_proven": False,
        "archive_priority_or_object_ownership_proven": False,
        "safe_hook_ABI_proven": False, "native_hook_installed": False,
        "gameplay_verified": False, "full_moddingapi": False
    }
