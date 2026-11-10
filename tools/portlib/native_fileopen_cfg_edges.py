"""Conservative read-only ARM64 direct-edge census near pinned FileOpen BR sites.

Edges are syntactic; a bounded window cannot establish complete predecessors,
runtime pointer values, call contracts, or engine consumer ownership.
"""
import hashlib
import struct
from .native_cpk_graph import MAIN_SHA256
from .nso_profile import segments
from .native_fileopen_br_provenance import SITES


def _signed(value, bits):
    return value - (1 << bits) if value & (1 << (bits - 1)) else value


def decode_edge(word, pc):
    """Return (kind, target, falls_through), never infer an indirect target."""
    if word & 0x7c000000 == 0x14000000:  # B / BL
        displacement = _signed(word & 0x3ffffff, 26) << 2
        call = bool(word & 0x80000000)
        return ("call" if call else "jump", pc + displacement, call)
    if word & 0xff000010 == 0x54000000:  # B.cond
        return ("conditional", pc + (_signed((word >> 5) & 0x7ffff, 19) << 2), True)
    if word & 0x7e000000 == 0x34000000:  # CBZ / CBNZ
        return ("conditional", pc + (_signed((word >> 5) & 0x7ffff, 19) << 2), True)
    if word & 0x7e000000 == 0x36000000:  # TBZ / TBNZ
        return ("conditional", pc + (_signed((word >> 5) & 0x3fff, 14) << 2), True)
    if word & 0xfffffc1f in (0xd61f0000, 0xd65f0000, 0xd69f0000):
        return ("indirect_or_return", None, False)
    return ("linear_or_unclassified", None, True)


def census(code, base, site, window=128):
    if not 1 <= window <= 512 or base % 4 or site % 4 or site < base or site + 4 > base + len(code):
        raise ValueError("Invalid aligned bounded code window")
    start = max(base, site - 4 * window)
    edges = []
    unresolved = []
    incoming = {}
    for pc in range(start, site + 4, 4):
        word = struct.unpack_from("<I", code, pc - base)[0]
        kind, target, fallthrough = decode_edge(word, pc)
        if target is not None:
            row = {"from": hex(pc), "to": hex(target), "kind": kind,
                   "within_window": start <= target <= site}
            edges.append(row)
            if row["within_window"]:
                incoming.setdefault(target, []).append(pc)
            else:
                unresolved.append(row)
        if fallthrough and pc < site:
            incoming.setdefault(pc + 4, []).append(pc)
    # Window start is only a hypothetical entry, not a proven function entry.
    successors = {}
    for pc in range(start, site + 4, 4):
        word = struct.unpack_from("<I", code, pc - base)[0]
        kind, target, fallthrough = decode_edge(word, pc)
        next_pc = []
        if target is not None and start <= target <= site and kind != "call":
            next_pc.append(target)
        if fallthrough and pc < site:
            next_pc.append(pc + 4)
        successors[pc] = next_pc
    reachable = set()
    pending = [start]
    while pending:
        pc = pending.pop()
        if pc in reachable:
            continue
        reachable.add(pc)
        pending.extend(x for x in successors[pc] if x not in reachable)
    reachable_merges = [hex(pc) for pc, preds in sorted(incoming.items())
                        if pc in reachable and len({p for p in preds
                        if p in reachable and pc in successors[p]}) > 1]
    merges = [{"address": hex(pc), "predecessors": sorted(hex(x) for x in set(pred))}
              for pc, pred in sorted(incoming.items())
              if len(set(pred)) > 1]
    return {"site": hex(site), "window_start": hex(start),
            "window_entry_reachable_instructions": len(reachable),
            "site_reachable_from_window_start": site in reachable,
            "window_entry_reachable_merges": reachable_merges,
            "window_instruction_count": (site - start) // 4 + 1,
            "direct_edges": edges, "out_of_window_edges": unresolved,
            "in_window_merges": merges,
            "site_in_window_predecessors": sorted(hex(x) for x in set(incoming.get(site, []))),
            "external_predecessors_unknown": True,
            "complete_cfg_proven": False, "memory_values_proven": False,
            "engine_consumer_abi_verified": False}


def analyze(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original main SHA mismatch")
    base, code, _ = segments(nso)[0]
    return {"main_sha256": digest, "text_sha256": hashlib.sha256(code).hexdigest(),
            "sites": {name: census(code, base, site) for name, (site, _) in SITES.items()},
            "scope": "bounded syntactic direct-edge census; external predecessors unknown",
            "ownership_verified": False, "archive_precedence_verified": False,
            "gameplay_verified": False}
