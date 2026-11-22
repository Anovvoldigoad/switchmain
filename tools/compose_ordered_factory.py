#!/usr/bin/env python3
"""Compose SHA-pinned raw PC and factory profiles in actual mod load order.

Offline class-selector editor only; not a native Switch engine consumer.
"""
import argparse
import ctypes
import errno
import hashlib
import json
import os
import shutil
import tempfile
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


def publish_new_directory(stage, output):
    """Atomic Linux no-replace publication; unsupported hosts fail closed."""
    libc = ctypes.CDLL(None, use_errno=True)
    fn = getattr(libc, "renameat2", None)
    if fn is None:
        raise OSError(errno.ENOSYS, "renameat2 required for exclusive publication")
    fn.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int,
                   ctypes.c_char_p, ctypes.c_uint)
    fn.restype = ctypes.c_int
    if fn(-100, os.fsencode(stage), -100, os.fsencode(output), 1):
        code = ctypes.get_errno()
        raise OSError(code, os.strerror(code), str(output))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", nargs=4, action="append", required=True,
                   metavar=("RAW_OR_PROFILE", "LABEL", "PATH", "SHA256"))
    p.add_argument("--exclude", action="append", default=[], metavar="LABEL",
                   help="Remove a mod and replay remaining sources in original order")
    p.add_argument("--conflicts", choices=("last", "reject"), default="last")
    p.add_argument("--owner-map", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--verify-output", action="store_true", help="Verify existing profile and provenance by source replay")
    p.add_argument("--baseline-report", nargs=2, metavar=("PATH", "SHA256"),
                   help="Authenticate prior ordered report and detect same-selector ownership transfers")
    p.add_argument("--baseline-profile", nargs=2, metavar=("PATH", "SHA256"),
                   help="Compare against a SHA-pinned existing factory profile before deployment")
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
    # Last writer for each owner is the effective mod after ordered composition.
    effective = {}
    for row in ledger:
        effective[row["owner"]] = {"source": row["source"], "kind": row["kind"],
                                   "selector": row["selector"]}
    baseline = None
    if a.baseline_profile:
        baseline_path, expected_sha = a.baseline_profile
        baseline_bytes = Path(baseline_path).read_bytes()
        baseline_sha = hashlib.sha256(baseline_bytes).hexdigest()
        if baseline_sha != expected_sha.lower() or len(expected_sha) != 64:
            p.error("Baseline profile SHA256 mismatch")
        baseline = decode(baseline_bytes)
    baseline_owners = None
    if a.baseline_report:
        if baseline is None:
            p.error("--baseline-report requires --baseline-profile")
        report_path, report_expected = a.baseline_report
        report_bytes = Path(report_path).read_bytes()
        report_sha = hashlib.sha256(report_bytes).hexdigest()
        if len(report_expected) != 64 or report_sha != report_expected.lower():
            p.error("Baseline report SHA256 mismatch")
        try:
            prior = json.loads(report_bytes)
            if prior["profile_sha256"] != baseline_sha:
                raise ValueError("Baseline report/profile digest mismatch")
            prior_owners = prior["effective_owners"]
            if not isinstance(prior_owners, list):
                raise ValueError("Invalid baseline owners")
            baseline_owners = {}
            for entry in prior_owners:
                owner = entry["owner"]
                if not isinstance(owner, int) or owner in baseline_owners or owner not in baseline:
                    raise ValueError("Invalid or duplicate baseline owner")
                if entry["selector"] != baseline[owner] or not isinstance(entry["source"], str) or not isinstance(entry["kind"], str):
                    raise ValueError("Baseline owner/profile mismatch")
                baseline_owners[owner] = entry
            if set(baseline_owners) != set(baseline):
                raise ValueError("Incomplete baseline ownership")
        except (ValueError, KeyError, TypeError) as exc:
            p.error(f"Invalid baseline report: {exc}")
    changes = []
    if baseline is not None:
        current = decode(result)
        for owner in sorted(set(baseline) | set(current)):
            before, after = baseline.get(owner), current.get(owner)
            if before == after and baseline_owners is not None and before is not None:
                prior_owner = baseline_owners[owner]
                current_owner = effective[owner]
                if (prior_owner["source"], prior_owner["kind"]) != (current_owner["source"], current_owner["kind"]):
                    changes.append({"owner": owner, "before": before, "after": after,
                                    "operation": "transfer",
                                    "before_source": prior_owner["source"],
                                    "after_source": current_owner["source"]})
            if before != after:
                change = {"owner": owner, "before": before, "after": after,
                          "operation": "add" if before is None else
                          "remove" if after is None else "replace"}
                if baseline_owners is not None:
                    change["before_source"] = (baseline_owners[owner]["source"]
                                               if before is not None else None)
                    change["after_source"] = (effective[owner]["source"]
                                              if after is not None else None)
                changes.append(change)
    report = {"effective_owners": [{"owner": owner, **effective[owner]}
                                    for owner in sorted(effective)],
              "sources": provenance, "records": ledger,
              **({"baseline_sha256": baseline_sha, "changes": changes} if baseline is not None else {}),
              **({"baseline_report_sha256": report_sha} if baseline_owners is not None else {}),
              "excluded_labels": a.exclude,
              "profile_sha256": hashlib.sha256(result).hexdigest(),
              "native_consumer_verified": False, "gameplay_verified": False}
    if a.verify_output:
        if not a.output.is_dir() or {x.name for x in a.output.iterdir()} != {"factory.profile", "factory_ordered_report.json"}:
            p.error("Missing or unexpected verification files")
        if (a.output / "factory.profile").read_bytes() != result:
            p.error("Factory profile replay mismatch")
        try:
            saved = json.loads((a.output / "factory_ordered_report.json").read_text())
        except (ValueError, UnicodeError) as exc:
            p.error(f"Invalid report: {exc}")
        if saved != report:
            p.error("Factory provenance replay mismatch")
        return
    # Publish both files together; clean staging if either write fails.
    if a.output.exists():
        raise FileExistsError(a.output)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=".factory-ordered-", dir=a.output.parent))
    try:
        (stage / "factory.profile").write_bytes(result)
        (stage / "factory_ordered_report.json").write_text(json.dumps(report, indent=2) + "\n")
        publish_new_directory(stage, a.output)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


if __name__ == "__main__":
    main()
