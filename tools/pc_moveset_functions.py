#!/usr/bin/env python3
"""Source-pinned PC Toolbox Moveset function index names, not Switch ABI.

This catalog is a name/index lookup for an editor; no PRM binary offsets,
native function pointers, callback contracts or runtime hooks are inferred.
"""
import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "profiles" / "pc_moveset_function_names_2121.json"


def lookup(version, index):
    if version not in ("ns4", "nsc"):
        raise ValueError("Only source-verified ns4/nsc catalogs are supported")
    if type(index) is not int or index < 0:
        raise ValueError("Function index must be nonnegative integer")
    names = json.loads(CATALOG.read_text(encoding="utf-8"))[version]
    if index >= len(names):
        raise ValueError("Function index absent from pinned PC catalog")
    return {"source_version": version, "index": index, "name": names[index],
            "native_switch_abi_verified": False}


def compare():
    source = json.loads(CATALOG.read_text(encoding="utf-8"))
    ns4, nsc = source["ns4"], source["nsc"]
    if len(ns4) != 289 or len(nsc) != 300 or ns4 != nsc[:len(ns4)]:
        raise ValueError("Pinned PC catalog no longer has proven prefix equivalence")
    return {"shared_same_index": len(ns4), "nsc_only": [
        {"index": i, "name": name} for i, name in enumerate(nsc[len(ns4):], len(ns4))
    ], "switch_projectiles_target_index_proven": False,
        "start_stop_deflect_index_proven": False,
        "switch_engine_abi_verified": False,
        "source_commit": source["source_commit"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("ns4", "nsc"))
    parser.add_argument("--index", type=int)
    parser.add_argument("--compare", action="store_true")
    args = parser.parse_args()
    if args.compare:
        if args.version is not None or args.index is not None:
            parser.error("--compare cannot be combined with lookup")
        result = compare()
    else:
        if args.version is None or args.index is None:
            parser.error("--version and --index are both required")
        try:
            result = lookup(args.version, args.index)
        except ValueError as error:
            parser.error(str(error))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
