#!/usr/bin/env python3
"""Read-only exact main FileOpen bounded return W0 provenance (NOT gameplay)."""
import argparse
import json
from pathlib import Path
from portlib.native_fileopen_returns import inspect


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--main", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    x = p.parse_args()
    proof = inspect(x.main.read_bytes())
    x.output.mkdir(parents=True, exist_ok=False)
    (x.output / "native_fileopen_returns.json").write_text(
        json.dumps(proof, indent=2) + "\n"
    )
    print("PINNED_FILEOPEN_RETURN_PROVENANCE",
          "reachable", proof["reachable_decoded_instructions"],
          "RET_sites", proof["reachable_return_sites"],
          "unresolved_exits", len(proof["other_terminations_or_out_of_window"]),
          "w0_def_sites", len(proof["reaching_w0_definition_sites"]),
          "NOT_CRI_OR_GAMEPLAY")


if __name__ == "__main__":
    main()
