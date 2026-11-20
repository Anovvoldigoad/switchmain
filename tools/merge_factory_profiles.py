#!/usr/bin/env python3
"""Combine independently verified factory profiles in explicit mod priority order.

Offline selector composition only; never a native consumer or gameplay proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
from portlib.factory_profile import decode, encode


def merge(inputs, *, conflicts="last"):
    if conflicts not in ("last", "reject"):
        raise ValueError("Unknown collision policy")
    owners, ledger = {}, []
    for label, data, expected_sha in inputs:
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha or len(expected_sha) != 64:
            raise ValueError(f"{label}: profile SHA256 mismatch")
        mappings = decode(data)
        for owner, selector in mappings.items():
            previous = owners.get(owner)
            if previous is not None and conflicts == "reject":
                raise ValueError(f"{label}: owner {owner} collides")
            ledger.append({"source": label, "owner": owner, "selector": selector,
                           "replaced": previous is not None,
                           "previous_selector": previous})
            owners[owner] = selector
    return encode(owners), ledger


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs=3, metavar=("LABEL", "PROFILE", "SHA256"),
                   action="append", required=True)
    p.add_argument("--conflicts", choices=("last", "reject"), default="last")
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    labels = [s[0] for s in a.source]
    if len(set(labels)) != len(labels):
        p.error("Duplicate source label")
    inputs = [(label, Path(path).read_bytes(), sha)
              for label, path, sha in a.source]
    result, ledger = merge(inputs, conflicts=a.conflicts)
    report = {"sources": [{"label": label, "sha256": sha} for label, _, sha in inputs],
              "conflicts": a.conflicts, "records": ledger,
              "profile_sha256": hashlib.sha256(result).hexdigest(),
              "native_consumer_verified": False, "gameplay_verified": False}
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / "factory.profile").write_bytes(result)
    (a.output / "factory_merge_report.json").write_text(
        json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    main()
