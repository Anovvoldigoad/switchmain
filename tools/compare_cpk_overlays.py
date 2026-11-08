#!/usr/bin/env python3
"""Compare source-pinned CPK overlays without guessing native archive precedence."""
import argparse
import json
from pathlib import Path

from inspect_cpk_payloads import inventory


def compare(sources, suffix=None):
    if not 2 <= len(sources) <= 16:
        raise ValueError("Compare two to sixteen distinct CPK sources")
    reports = []
    seen = set()
    for path, sha in sources:
        resolved = Path(path).resolve()
        if resolved in seen:
            raise ValueError("Duplicate archive source")
        seen.add(resolved)
        reports.append(inventory(path, sha, suffix=suffix))
    paths = {}
    for i, report in enumerate(reports):
        for row in report["entries"]:
            paths.setdefault(row["entry"].casefold(), []).append((i, row))
    conflicts = []
    for key, occurrences in sorted(paths.items()):
        if len(occurrences) < 2:
            continue
        records = [{
            "archive_index": i,
            "archive_sha256": reports[i]["cpk_sha256"],
            "entry": row["entry"],
            "id": row["id"],
            "stored_sha256": row["stored_sha256"],
            "stored_bytes": row["stored_bytes"],
            "extract_bytes": row["extract_bytes"],
            "encoding": row["encoding"]
        } for i, row in occurrences]
        conflicts.append({
            "casefold_path": key, "occurrences": records,
            "stored_payloads_identical": len({r["stored_sha256"] for r in records}) == 1,
            "decoded_payloads_identical": None,
            "native_winner": None
        })
    return {
        "status": "STATIC_CPK_OVERLAP_EVIDENCE_NO_NATIVE_PRECEDENCE",
        "archives": [{
            "index": i, "filename": report["cpk_filename"],
            "sha256": report["cpk_sha256"],
            "indexed_entries": report["indexed_entries"],
            "selected_entries": report["selected_entries"]
        } for i, report in enumerate(reports)],
        "overlapping_paths": len(conflicts),
        "conflicts": conflicts,
        "native_archive_precedence_verified": False,
        "native_consumer_abi_verified": False,
        "uzuy_tested": False
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", action="append", nargs=2,
                        metavar=("CPK_PATH", "SHA256"), required=True,
                        help="Repeat for each original CPK; order is input order, NOT native priority")
    parser.add_argument("--suffix", help="Optional case-insensitive filename suffix")
    args = parser.parse_args()
    try:
        result = compare(args.archive, suffix=args.suffix)
    except (ValueError, OSError, UnicodeError) as error:
        parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
