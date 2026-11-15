#!/usr/bin/env python3
"""Audit pinned native FileOpen->status5 register/body witnesses (NOT gameplay)."""
import argparse
import json
from pathlib import Path

from portlib.native_fileload_result_flow import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    a = p.parse_args()
    result = inspect(a.main.read_bytes())
    a.output.mkdir(parents=True, exist_ok=False)
    (a.output / "native_fileload_result_flow.json").write_text(
        json.dumps(result, indent=2) + "\n"
    )
    print("PINNED_ORIGINAL_FILEOPEN_RESULT_FLOW_PASS",
          "path_length", len(result["first_status5_shortest_syntactic_path"]),
          "conditional_decisions", len(result["first_status5_path_conditional_decisions"]),
          "assumed_external_returns", len(result["first_status5_path_calls_assumed_to_return"]),
          "unresolved_exits", len(result["possible_unresolved_exits_without_status"]),
          "NO_REAL_CRI_OR_GAMEPLAY_PROOF")


if __name__ == "__main__":
    main()
