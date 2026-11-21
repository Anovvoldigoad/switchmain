#!/usr/bin/env python3
"""Compose SHA-pinned raw PC and factory profiles in actual mod load order.

Offline class-selector editor only; not a native Switch engine consumer.
"""
import argparse
import hashlib
import json
from pathlib import Path

from portlib.factory_profile import compile_records, decode, encode


def compose(sources, *, conflicts="last", owner_map=None, exclude=()):
    if conflicts not in ("last", "reject"):
        raise ValueError("Invalid conflict policy")
    owners, ledger, provenance = {}, [], []
    exclude = tuple(exclude)
    if len(set(exclude)) != len(exclude):
        raise ValueError("Duplicate excluded source label")
    excluded = set(exclude)
    if excluded - {source[1] for source in sources}:
        raise ValueError("Unknown excluded source label")
    seen = set()
    for kind, label, data, expected in sources:
        if label in seen:
            raise ValueError("Duplicate source label")
        seen.add(label)
        digest = hashlib.sha256(data).hexdigest()
        if len(expected) != 64 or digest != expected.lower():
            raise ValueError(f"{label}: SHA256 mismatch")
        if kind not in ("raw", "profile"):
            raise ValueError("Unknown source kind")
        if label in excluded:
            provenance.append({"kind": kind, "label": label, "sha256": digest,
                               "excluded": True})
            continue
        if kind == "raw":
            # Compile one raw source at a time so its position is respected.
            profile, records = compile_records([(label, data)], owner_map,
                                               conflicts=conflicts)
            mappings = decode(profile)
            # Preserve every original raw record for duplicate detection.
            if conflicts == "reject" and any(row["switch_owner"] in owners for row in records):
                raise ValueError(f"{label}: owner collision")
            rows = [(row["switch_owner"], row["selector"]) for row in records]
        elif kind == "profile":
            mappings = decode(data)
            rows = list(mappings.items())
        else:
            raise ValueError("Unknown source kind")
        for owner, selector in rows:
            previous = owners.get(owner)
            if previous is not None and conflicts == "reject":
                raise ValueError(f"{label}: owner {owner} collides")
            ledger.append({"source": label, "kind": kind, "owner": owner,
                           "selector": selector, "previous_selector": previous,
                           "replaced": previous is not None})
            owners[owner] = selector
        provenance.append({"kind": kind, "label": label, "sha256": digest,
                           "excluded": False})
    return encode(owners), ledger, provenance


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs=4, action="append", required=True,
                   metavar=("RAW_OR_PROFILE", "LABEL", "PATH", "SHA256"))
    p.add_argument("--exclude", action="append", default=[], metavar="LABEL",
                   help="Remove a mod and replay remaining sources in original order")
    p.add_argument("--conflicts", choices=("last", "reject"), default="last")
    p.add_argument("--owner-map", type=Path)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    mapping = None
    if a.owner_map:
        raw = json.loads(a.owner_map.read_text())
        if not isinstance(raw, dict) or any(str(int(k)) != k for k in raw):
            p.error("Owner map must use canonical decimal keys")
        mapping = {int(k): v for k, v in raw.items()}
    inputs = [(kind, label, Path(path).read_bytes(), sha)
              for kind, label, path, sha in a.source]
    result, ledger, provenance = compose(inputs, conflicts=a.conflicts, owner_map=mapping, exclude=a.exclude)
    report = {"sources": provenance, "records": ledger,
              "excluded_labels": a.exclude,
              "profile_sha256": hashlib.sha256(result).hexdigest(),
              "native_consumer_verified": False, "gameplay_verified": False}
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / "factory.profile").write_bytes(result)
    (a.output / "factory_ordered_report.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
