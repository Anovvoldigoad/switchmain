"""SHA-pinned full executable-text direct inbound census for native FileOpen BR sites.

A raw direct branch into a bounded window does not establish that its source
executes. Indirect predecessors, external code, lifetime and ABI remain unknown.
"""
import hashlib
import struct
from .native_cpk_graph import MAIN_SHA256
from .native_fileopen_br_provenance import SITES
from .native_fileopen_cfg_edges import decode_edge
from .nso_profile import segments


def inbound_census(code, base, sites, window=128):
    """Scan all aligned text words ONCE for direct incoming branches."""
    if not 1 <= window <= 512 or base % 4 or len(code) % 4:
        raise ValueError("Invalid aligned executable-text window")
    if not sites:
        raise ValueError("No branch sites")
    limit = base + len(code)
    found = {}
    for name, (site, register) in sites.items():
        if (not isinstance(register, str) or not register.startswith("x")
                or not register[1:].isdigit() or not 0 <= int(register[1:]) <= 30
                or site % 4 or not base <= site < limit):
            raise ValueError("Invalid site or register")
        if struct.unpack_from("<I", code, site-base)[0] != (
                0xd61f0000 | (int(register[1:]) << 5)):
            raise ValueError("BR site instruction mismatch")
        found[name] = {
            "site": hex(site), "register": register,
            "window_start": hex(max(base, site - 4*window)),
            "direct_inbound_from_outside_window": [],
            "direct_inbound_count": 0,
            "source_reachability_verified": False,
            "indirect_predecessors_resolved": False,
            "outside_text_predecessors_resolved": False,
            "native_consumer_abi_verified": False,
        }
    transfer_count = 0
    for i, (word,) in enumerate(struct.iter_unpack("<I", code)):
        pc = base + 4*i
        kind, target, _ = decode_edge(word, pc)
        if target is None or kind not in ("jump", "call", "conditional"):
            continue
        transfer_count += 1
        for entry in found.values():
            start, site = int(entry["window_start"], 16), int(entry["site"], 16)
            if start <= target <= site and not start <= pc <= site:
                entry["direct_inbound_from_outside_window"].append({
                    "from": hex(pc), "to": hex(target), "kind": kind,
                    "bytes_le": word.to_bytes(4, "little").hex(),
                    "source_in_text": True,
                    "source_reachability_verified": False,
                })
    for entry in found.values():
        entry["direct_inbound_count"] = len(entry["direct_inbound_from_outside_window"])
        entry["external_entry_path_summary"] = summarize_external_entries(code, base, entry)
    return {
        "text_sha256": hashlib.sha256(code).hexdigest(),
        "text_base": hex(base), "text_bytes": len(code),
        "instruction_words_scanned": len(code)//4,
        "direct_control_transfers_scanned": transfer_count,
        "sites": found, "complete_cfg_proven": False,
        "native_consumer_abi_verified": False,
    }



def _window_path(code, base, window_start, origin, site, forbid_calls=False):
    """Shortest byte-witnessed local path, not a feasible runtime trace.

    Direct and indirect calls are opaque fallthroughs unless forbidden. No indirect
    destination or out-of-window predecessor is invented.
    """
    from collections import deque
    pending = deque([origin])
    parents = {origin: None}
    visited = set()
    while pending:
        pc = pending.popleft()
        if pc in visited:
            continue
        visited.add(pc)
        if pc == site:
            break
        word = struct.unpack_from("<I", code, pc-base)[0]
        kind, target, fallthrough = decode_edge(word, pc)
        if forbid_calls and kind in ("call", "indirect_call"):
            continue
        successors = []
        if target is not None and kind != "call" and window_start <= target <= site:
            successors.append(target)
        if fallthrough and pc < site:
            successors.append(pc + 4)
        for successor in successors:
            if successor not in parents:
                parents[successor] = pc
                pending.append(successor)
    if site not in visited:
        return False, len(visited), []
    path = []
    cursor = site
    while cursor is not None:
        word = struct.unpack_from("<I", code, cursor-base)[0]
        path.append({"pc": hex(cursor), "bytes_le": word.to_bytes(4, "little").hex()})
        cursor = parents[cursor]
    path.reverse()
    return True, len(visited), path


def summarize_external_entries(code, base, entry):
    """Group observed inbound target addresses and bound their local paths.

    The source of each incoming branch and the paths' runtime feasibility
    are deliberately NOT considered proven.
    """
    start = int(entry["window_start"], 16)
    site = int(entry["site"], 16)
    groups = {}
    for row in entry["direct_inbound_from_outside_window"]:
        target = int(row["to"], 16)
        group = groups.setdefault(target, {"target": hex(target), "incoming_edges": 0,
                                           "call_edges": 0, "jump_edges": 0,
                                           "conditional_edges": 0})
        group["incoming_edges"] += 1
        group[row["kind"] + "_edges"] += 1
    # Separate true non-call transfers from BL callers: a BL to an
    # unrelated local function is not evidence of a BR-chain predecessor.
    # These are syntactic candidates only, never confirmed runtime edges.
    summary = []
    for target, group in sorted(groups.items()):
        reachable, visited_count, witness = _window_path(code, base, start, target, site)
        call_free, call_free_visited, call_free_witness = _window_path(
            code, base, start, target, site, forbid_calls=True)
        group["noncall_inbound_edges"] = (
            group["jump_edges"] + group["conditional_edges"])
        group["noncall_inbound_call_free_candidate"] = bool(
            group["noncall_inbound_edges"] and call_free)
        group["noncall_inbound_candidate_runtime_verified"] = False
        group["call_free_syntactic_path_to_br"] = call_free
        group["call_free_window_words_visited"] = call_free_visited
        group["shortest_call_free_path"] = call_free_witness
        group["syntactic_path_from_target_to_br"] = reachable
        group["window_words_visited"] = visited_count
        group["shortest_local_path"] = witness
        group["path_call_side_effects_resolved"] = False
        group["source_reachability_verified"] = False
        group["path_feasibility_verified"] = False
        summary.append(group)
    return summary


def analyze(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA mismatch")
    base, code, _ = segments(nso)[0]
    report = inbound_census(code, base, SITES)
    report.update({
        "main_sha256": digest,
        "scope": "full original text direct-edge census; indirect calls and source reachability unresolved",
        "ownership_verified": False,
        "archive_precedence_verified": False,
        "gameplay_verified": False,
    })
    return report
