"""Bounded source-only FileOpen return corridor and native status argument provenance.

The source is the exact SHA-256-pinned *original* Switch v1.70 main.
Do not interpret a syntactic path or an external-call fallthrough as a
live CRI failure, safe hook ABI, archive precedence or gameplay proof.
"""
from collections import deque
import hashlib

from capstone import Cs, CS_ARCH_ARM64, CS_MODE_ARM

from .native_cpk_graph import MAIN_SHA256
from .native_cpk_cfg import _edges
from .native_fileload_corridor_cfg import ENTRY, END
from .native_fileload_zero_return import (
    inspect as inspect_zero, ZERO_TARGET, STATUS1, STATUS2,
)
from .native_fileload_status import inspect as inspect_status
from .nso_profile import segments

MAX_NODES = 256
PINNED_SEQUENCE = {
    0x116F518: ("mov", "w1, #5"),
    0x116F51C: ("mov", "x0, x20"),
    0x116F520: ("bl", "#0x120661c"),
    0x1206628: ("mov", "x21, x0"),
    0x1206630: ("mov", "w20, w1"),
    0x1206638: ("ldr", "w8, [x21, #0x68]"),
    0x120663C: ("cmp", "w8, #3"),
    0x1206640: ("ccmp", "w8, #5, #4, ne"),
    0x1206644: ("b.ne", "#0x1206658"),
    0x1206658: ("str", "w20, [x21, #0x68]"),
}


def _walk(graph, origin, stops, lo, hi, budget=MAX_NODES):
    """Walk intra-window branch edges; call targets are NOT descended into.

    Exits without a reached status site remain unresolved. A path is only
    a syntactic possibility, and graph traversal does not solve predicates.
    """
    queue = deque([origin])
    parent = {origin: None}
    exits = []
    indirect_calls = []
    def route(node):
        seq = []
        while node is not None:
            seq.append(node)
            node = parent[node]
        return list(reversed(seq))
    while queue:
        pc = queue.popleft()
        if len(parent) > budget:
            raise ValueError("Bounded FileLoad exploration limit exceeded")
        if pc in stops:
            continue
        if pc not in graph:
            exits.append({"kind": "undecoded", "path": route(pc)})
            continue
        for kind, nxt in graph[pc]:
            if kind == "call":
                continue
            if kind == "indirect_call_unresolved":
                indirect_calls.append(pc)
                continue
            if nxt is None:
                exits.append({"kind": kind, "path": route(pc)})
            elif not lo <= nxt < hi:
                exits.append({"kind": "out_of_window", "from": pc,
                              "target": nxt, "path": route(pc)})
            elif nxt not in parent:
                parent[nxt] = pc
                queue.append(nxt)
    return {"paths": {s: route(s) if s in parent else None for s in stops},
            "visited": len(parent), "exits": exits,
            "indirect_calls": sorted(set(indirect_calls))}


def _instructions(code, addrs):
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    result = {}
    for pc in sorted(set(addrs)):
        word = code[pc:pc + 4]
        decoded = list(decoder.disasm(word, pc))
        if len(decoded) != 1 or decoded[0].size != 4:
            raise ValueError("Pinned AArch64 instruction undecodable at " + hex(pc))
        result[pc] = decoded[0]
    return result


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Exact original Switch v1.70 main SHA256 required")
    earlier = inspect_zero(nso)
    status = inspect_status(nso)
    va, code, _ = segments(nso)[0]
    if va or max(PINNED_SEQUENCE) + 4 > len(code) or END > len(code):
        raise ValueError("Pinned executable section bounds mismatch")
    decoder = Cs(CS_ARCH_ARM64, CS_MODE_ARM)
    graph = {}
    mnemonics = {}
    for pc in range(ENTRY, END, 4):
        one = list(decoder.disasm(code[pc:pc + 4], pc))
        if len(one) == 1 and one[0].size == 4:
            ins = one[0]
            graph[pc] = _edges(pc, ins.mnemonic, ins.op_str)
            mnemonics[pc] = (ins.mnemonic, ins.op_str)
    if ZERO_TARGET not in graph:
        raise ValueError("Pinned CBZ target not decoded")
    walk = _walk(graph, ZERO_TARGET, {STATUS1, STATUS2}, ENTRY, END)
    if (walk["paths"][STATUS1] is None or walk["paths"][STATUS2] is not None
            or earlier["first_status5"]["reachable_from_CBZ_zero_taken"] is not True
            or earlier["second_status5"]["reachable_from_CBZ_zero_taken"] is not False):
        raise ValueError("Regression in original FileOpen zero-result CFG")
    words = _instructions(code, PINNED_SEQUENCE)
    for pc, wanted in PINNED_SEQUENCE.items():
        observed = (words[pc].mnemonic, words[pc].op_str)
        if observed != wanted:
            raise ValueError("Original native argument/body word differs at "
                             + hex(pc) + ": " + repr(observed))
    path = walk["paths"][STATUS1]
    decisions = []
    assumed_returns = []
    for a, b in zip(path, path[1:]):
        possibilities = graph[a]
        matched = [kind for kind, target in possibilities
                   if target == b and kind != "call"]
        if not matched:
            raise ValueError("Broken static predecessor edge")
        if len([x for x in possibilities if x[0] not in
                ("call", "indirect_call_unresolved")]) > 1:
            decisions.append({"at": hex(a), "word_le": code[a:a+4].hex(),
                              "mnemonic": mnemonics[a][0],
                              "operands": mnemonics[a][1],
                              "chosen_successor": hex(b)})
        if mnemonics[a][0] in ("bl", "blr"):
            assumed_returns.append(hex(a))
    # Only machine-code register transfer is proven here. This does not
    # establish X20's class, X20 lifetime or the actual FileOpen result.
    return {
        "status": "PINNED_FILEOPEN_ZERO_PATH_AND_NATIVE_STATUS_ARG_WITNESSES_ONLY",
        "original_main_sha256": digest,
        "original_fileopen_result_check": "0x116f480 CBZ W0,0x116F4D8",
        "zero_result_branch_machine_code_verified": True,
        "status5_first_reachable_syntactically": True,
        "status5_second_reachable_syntactically": False,
        "first_status5_shortest_syntactic_path": [hex(a) for a in path],
        "first_status5_path_conditional_decisions": decisions,
        "first_status5_path_calls_assumed_to_return": assumed_returns,
        "zero_branch_graph_nodes_visited": walk["visited"],
        "possible_unresolved_exits_without_status": [
            {k: ([hex(x) for x in v] if k == "path" else
                 hex(v) if isinstance(v, int) else v)
             for k, v in item.items()} for item in walk["exits"][:32]
        ],
        "unresolved_exit_list_truncated": len(walk["exits"]) > 32,
        "indirect_calls_unresolved": [hex(x) for x in walk["indirect_calls"]],
        "first_status_call_arg_registers": {
            "status_value": 5, "source_register": "W1",
            "object_argument_register": "X0",
            "object_source_register": "X20",
            "verified_at": ["0x116f518", "0x116f51c", "0x116f520"],
        },
        "native_status_helper_original_body": {
            "entry": "0x120661c", "object_argument_moved": "X0 -> X21",
            "value_argument_moved": "W1 -> W20",
            "status_field_access": "[X21,#0x68]",
            "old_status_3_or_5_guard_seen": True,
            "stored_on_eligible_path": "W20 to [X21,#0x68]",
            "exact_word_witnesses": [
                {"at": hex(pc), "bytes_le": code[pc:pc+4].hex(),
                 "mnemonic": words[pc].mnemonic, "operands": words[pc].op_str}
                for pc in sorted(PINNED_SEQUENCE)
            ],
            "modeled_lock_scenarios_not_reexecuted_here": 32,
        },
        "status_helper_source_transcript_sha256":
            status["helper_code"]["window_sha256"],
        "unknown_object_X20_ownership": True,
        "original_CRI_FileOpen_returned_zero_in_runtime": False,
        "zero_result_to_status5_unconditional_execution_proven": False,
        "real_lock_and_async_lifecycle_proven": False,
        "archive_precedence_and_unbind_proven": False,
        "safe_hook_or_trampoline_ABI_proven": False,
        "native_hook_written": False,
        "gameplay_verified": False,
        "full_moddingapi": False,
    }
