#!/usr/bin/env python3
"""Preflight PC MovesetPlus editor event indices against pinned Toolbox 2.1.2.1.

Input is an explicit JSON index manifest, NOT raw moveset bytes. Never guesses
binary offsets, argument types, Switch engine IDs or runtime ABI.
"""
import argparse
import hashlib
import json
from pathlib import Path
from pc_moveset_functions import CATALOG

def audit(spec):
    if type(spec) is not dict or set(spec) != {"source_version", "events"}:
        raise ValueError("Expected source_version and events only")
    version = spec["source_version"]
    if version not in ("ns4", "nsc"):
        raise ValueError("Unsupported PC source version")
    events = spec["events"]
    if type(events) is not list or not events or len(events) > 65536:
        raise ValueError("Expected 1..65536 explicit event records")
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    if len(catalog["ns4"]) != 289 or len(catalog["nsc"]) != 300 or catalog["ns4"] != catalog["nsc"][:289]:
        raise ValueError("Source-pinned index correspondence no longer holds")
    rows = []
    seen = set()
    for event in events:
        if type(event) is not dict or set(event) != {"event_id", "function_index"}:
            raise ValueError("Only event_id and function_index are accepted")
        eid, idx = event["event_id"], event["function_index"]
        if type(eid) is not str or not eid or len(eid) > 128 or eid in seen:
            raise ValueError("Missing, invalid or duplicate event_id")
        seen.add(eid)
        if type(idx) is not int or not 0 <= idx < len(catalog[version]):
            raise ValueError("Unknown PC function index for event " + eid)
        name = catalog[version][idx]
        rows.append({"event_id": eid, "source_index": idx, "source_name": name,
                     "target_nsc_index": idx, "target_nsc_name": catalog["nsc"][idx],
                     "source_index_preserved": True,
                     "target_native_switch_abi_verified": False})
    return {"status": "PC_EDITOR_EVENT_INDEX_PREFLIGHT_NOT_SWITCH_RUNTIME",
            "source_version": version, "target_version": "nsc",
            "source_catalog_commit": catalog["source_commit"],
            "source_catalog_blob": catalog["source_git_blob_sha"],
            "event_count": len(rows), "events": rows,
            "binary_layout_verified": False, "native_switch_abi_verified": False,
            "source_index_preservation_only": True}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--expected-sha256", required=True)
    p.add_argument("--output", required=True, type=Path)
    args = p.parse_args()
    try:
        raw = args.manifest.read_bytes()
        if len(raw) > 4 * 1024 * 1024 or len(args.expected_sha256) != 64 or hashlib.sha256(raw).hexdigest() != args.expected_sha256.lower():
            raise ValueError("Manifest size or SHA256 mismatch")
        result = audit(json.loads(raw))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(result, out, indent=2)
            out.write("\n")
    except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    print("PC_MOVESET_INDEX_PREFLIGHT", result["event_count"], "NOT_NATIVE_ABI")

if __name__ == "__main__":
    main()
