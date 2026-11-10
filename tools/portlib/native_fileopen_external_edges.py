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
    return {
        "text_sha256": hashlib.sha256(code).hexdigest(),
        "text_base": hex(base), "text_bytes": len(code),
        "instruction_words_scanned": len(code)//4,
        "direct_control_transfers_scanned": transfer_count,
        "sites": found, "complete_cfg_proven": False,
        "native_consumer_abi_verified": False,
    }


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
