#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXL="${1:?usage: prepare_exlaunch.sh /path/to/exlaunch}"

[ -d "$EXL/source/program" ] || {
  echo "STOP: exlaunch tree missing: $EXL" >&2
  exit 1
}

cp -f "$ROOT/overlay/source/program/main.cpp" "$EXL/source/program/main.cpp"
cp -f "$ROOT/overlay/source/program/nsc_cpk_bridge.cpp" "$EXL/source/program/nsc_cpk_bridge.cpp"
cp -f "$ROOT/overlay/source/program/nsc_cpk_bridge.hpp" "$EXL/source/program/nsc_cpk_bridge.hpp"

python3 - "$EXL/config.mk" <<'PY'
from pathlib import Path
import re, sys
p = Path(sys.argv[1])
s = p.read_text()
s, n1 = re.subn(r'(?m)^LOAD_KIND\s*:=.*$', 'LOAD_KIND := Module', s, count=1)
s, n2 = re.subn(r'(?m)^PROGRAM_ID\s*:=.*$', 'PROGRAM_ID := 0100FA10190A0000', s, count=1)
s, n3 = re.subn(r'(?m)^CXX_FLAGS\s*:=.*$', 'CXX_FLAGS := -Wno-non-c-typedef-for-linkage', s, count=1)
if (n1, n2, n3) != (1, 1, 1):
    raise SystemExit(f'config patch failed: {(n1, n2, n3)}')
p.write_text(s)
PY

echo "===== EXLAUNCH CONFIG ====="
grep -E '^(LOAD_KIND|PROGRAM_ID|CXX_FLAGS)[[:space:]]*:=' "$EXL/config.mk"
echo "R276H19B_PREPARE=PASS"
