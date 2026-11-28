#!/usr/bin/env python3
"""Source-pinned PC Toolbox Moveset function index names, not Switch ABI.

This catalog is a name/index lookup for an editor; no PRM binary offsets,
native function pointers, callback contracts or runtime hooks are inferred.
"""
import argparse
import json
from pathlib import Path

CATALOG = Path(__file__).resolve().parents[1] / "profiles" / "pc_moveset_function_names_2121.json"
COMMAND_CATALOG = Path(__file__).resolve().parents[1] / "profiles" / "pc_movesetplus_commands_2121.json"


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




def commands():
    """Return the separate numeric meTest registry, never the ME_* index list."""
    source = json.loads(COMMAND_CATALOG.read_text(encoding="utf-8"))
    if (source.get("status") !=
            "SOURCE_GROUNDED_PC_MOVESETPLUS_NUMERIC_DISPATCH_NOT_SWITCH_ABI"
            or source.get("switch_engine_abi_verified") is not False):
        raise ValueError("PC command registry source or Switch-ABI guard changed")
    rows = source.get("commands")
    if (not isinstance(rows, list)
            or [row.get("id") for row in rows] != [27, 28, 29]
            or any(row.get("me_function_index") is not None for row in rows)):
        raise ValueError("PC meTest commands must remain distinct from ME_* indices")
    return source


def lookup_command(command_id):
    if type(command_id) is not int or command_id < 0:
        raise ValueError("Command id must be a nonnegative integer")
    source = commands()
    for row in source["commands"]:
        if row["id"] == command_id:
            return {
                "source_commit": source["source_commit"],
                "command": row,
                "switch_engine_abi_verified": False,
            }
    raise ValueError("Command id absent from pinned PC meTest registry")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("ns4", "nsc"))
    parser.add_argument("--index", type=int)
    parser.add_argument("--compare", action="store_true")
    parser.add_argument("--commands", action="store_true",
                        help="show numeric PC meTest command registry; not ME_* indices")
    parser.add_argument("--command-id", type=int,
                        help="look up a source-pinned numeric PC meTest command")
    args = parser.parse_args()
    if args.commands:
        if (args.compare or args.version is not None or args.index is not None
                or args.command_id is not None):
            parser.error("--commands cannot be combined with another mode")
        result = commands()
    elif args.command_id is not None:
        if args.compare or args.version is not None or args.index is not None:
            parser.error("--command-id cannot be combined with another mode")
        try:
            result = lookup_command(args.command_id)
        except ValueError as error:
            parser.error(str(error))
    elif args.compare:
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
