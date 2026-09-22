#!/usr/bin/env python3

from pathlib import Path
import sys

ROOT = Path(".github/workflows")

if len(sys.argv) != 2:
    raise SystemExit(
        "usage: SET_ACTIVE_PROBE_WORKFLOW.py <workflow.yml>"
    )

ACTIVE = sys.argv[1]

if not (ROOT / ACTIVE).is_file():
    raise SystemExit(
        "FATAL active workflow missing: " + ACTIVE
    )

files = sorted(
    ROOT.glob("build-subsdk9-p*.yml")
)

def on_block(lines):
    start = None

    for i, line in enumerate(lines):
        if line.rstrip("\r\n") == "on:":
            start = i
            break

    if start is None:
        raise RuntimeError("top-level on: missing")

    end = start + 1

    while end < len(lines):
        line = lines[end]

        if line.strip() == "":
            end += 1
            continue

        if not line.startswith((" ", "\t")):
            break

        end += 1

    return start, end


for p in files:
    lines = p.read_text(
        encoding="utf-8"
    ).splitlines(True)

    start, end = on_block(lines)

    if p.name == ACTIVE:
        replacement = (
            "on:\n"
            "  push:\n"
            "    branches:\n"
            "      - main\n"
            "  workflow_dispatch:\n"
            "\n"
        )
        mode = "AUTO"
    else:
        replacement = (
            "on:\n"
            "  workflow_dispatch:\n"
            "\n"
        )
        mode = "MANUAL"

    p.write_text(
        "".join(
            lines[:start]
            + [replacement]
            + lines[end:]
        ),
        encoding="utf-8",
    )

    print(f"{mode:6} {p.name}")

print("WORKFLOW_SINGLE_ACTIVE_PATCH=PASS")
