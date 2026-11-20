#!/usr/bin/env python3
"""Compose SHA-pinned PC MovesetPlus editor indices, not binary/engine ABI."""
import argparse
import hashlib
import json
from pathlib import Path
from export_pc_moveset_nsc_manifest import convert

def analyze_collisions(sources):
    """Authenticate PC editor sources and report duplicate event IDs without merging."""
    if not 1 <= len(sources) <= 64:
        raise ValueError("Expected 1..64 source manifests")
    seen_names, owners, conflicts, inputs = set(), {}, [], []
    for name, raw, expected_sha in sources:
        if not isinstance(name, str) or not name or len(name) > 128 or name in seen_names:
            raise ValueError("Invalid or duplicate mod name")
        seen_names.add(name)
        converted, proof = convert(raw, expected_sha)
        rows = json.loads(converted)["events"]
        inputs.append({"name": name, "input_sha256": proof["input_sha256"],
                       "converted_sha256": hashlib.sha256(converted).hexdigest()})
        for row in rows:
            event_id = row["event_id"]
            if event_id in owners:
                conflicts.append({"event_id": event_id, "first_source": owners[event_id],
                                  "second_source": name})
            else:
                owners[event_id] = name
    return {"status": "PC_EDITOR_EVENT_COLLISION_REPORT_ONLY",
            "sources": inputs, "collisions": conflicts,
            "native_switch_abi_verified": False}


def merge(sources):
    if not 1 <= len(sources) <= 64:
        raise ValueError("Expected 1..64 source manifests")
    seen_names, seen_events, events, origins = set(), set(), [], []
    for name, raw, expected_sha in sources:
        if not isinstance(name, str) or not name or len(name) > 128 or name in seen_names:
            raise ValueError("Invalid or duplicate mod name")
        seen_names.add(name)
        converted, proof = convert(raw, expected_sha)
        records = json.loads(converted)["events"]
        for row in records:
            if row["event_id"] in seen_events:
                raise ValueError("Cross-mod event_id collision: " + row["event_id"])
            seen_events.add(row["event_id"])
            events.append(row)
        origins.append({"name": name, "input_sha256": proof["input_sha256"],
                        "source_version": proof["source_version"], "event_count": len(records),
                        "start": len(events) - len(records),
                        "converted_sha256": hashlib.sha256(converted).hexdigest()})
    if len(events) > 65536:
        raise ValueError("Combined event count exceeds editor manifest limit")
    payload = (json.dumps({"source_version": "nsc", "events": events},
                          ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    proof = {"status": "PC_MULTI_MOD_EDITOR_INDEX_ONLY", "sources": origins,
             "output_sha256": hashlib.sha256(payload).hexdigest(),
             "event_count": len(events), "binary_layout_verified": False,
             "native_switch_abi_verified": False, "gameplay_verified": False}
    return payload, proof

def split(payload, proof):
    """Reconstruct exact per-mod NSC editor manifests from a merged artifact."""
    if hashlib.sha256(payload).hexdigest() != proof["output_sha256"]:
        raise ValueError("Merged payload SHA256 mismatch")
    doc = json.loads(payload)
    if doc.get("source_version") != "nsc" or not isinstance(doc.get("events"), list):
        raise ValueError("Invalid merged manifest")
    events = doc["events"]
    if len(events) != proof["event_count"]:
        raise ValueError("Merged event count mismatch")
    result = []
    cursor = 0
    for origin in proof["sources"]:
        count = origin["event_count"]
        if origin["start"] != cursor or not isinstance(count, int) or count < 0:
            raise ValueError("Invalid source event range")
        cursor += count
        if cursor > len(events):
            raise ValueError("Source event range exceeds merged payload")
        part = (json.dumps({"source_version": "nsc", "events": events[cursor-count:cursor]},
                           ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if hashlib.sha256(part).hexdigest() != origin["converted_sha256"]:
            raise ValueError("Source converted SHA256 mismatch")
        result.append((origin["name"], part))
    if cursor != len(events):
        raise ValueError("Unattributed merged events")
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs=3, action="append", metavar=("NAME", "PATH", "SHA256"), required=True)
    p.add_argument("--collisions-only", action="store_true", help="Report authenticated event-ID conflicts without merging")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--evidence", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.output == args.evidence or args.output.exists() or args.evidence.exists():
            raise ValueError("Outputs must be distinct and absent")
        sources = [(name, Path(path).read_bytes(), sha) for name, path, sha in args.source]
        if args.collisions_only:
            report = analyze_collisions(sources)
            payload = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
            proof = {"status": "PC_EDITOR_COLLISION_DIAGNOSTIC_ONLY",
                     "report_sha256": hashlib.sha256(payload).hexdigest(),
                     "source_count": len(sources), "collision_count": len(report["collisions"]),
                     "native_switch_abi_verified": False}
        else:
            payload, proof = merge(sources)
        proof_bytes = (json.dumps(proof, indent=2) + "\n").encode()
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("xb") as out:
            out.write(payload)
        try:
            with args.evidence.open("xb") as out:
                out.write(proof_bytes)
        except BaseException:
            args.output.unlink()
            raise
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as exc:
        p.error(str(exc))
    if args.collisions_only:
        print("PC_EDITOR_COLLISION_REPORT", proof["collision_count"], "NOT_SWITCH_ABI")
    else:
        print("PC_MULTI_MOD_INDEX_MERGE", proof["event_count"], "NOT_SWITCH_ABI")

if __name__ == "__main__":
    main()
