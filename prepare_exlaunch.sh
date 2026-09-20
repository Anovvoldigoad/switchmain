#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXL="${1:-$ROOT/exlaunch}"
if [[ ! -d "$EXL" ]]; then echo "[!] Missing exlaunch tree: $EXL"; exit 1; fi
cp "$ROOT/overlay/source/program/main.cpp" "$EXL/source/program/main.cpp"
cp "$ROOT/overlay/source/program/nsc_cpk_bridge.cpp" "$EXL/source/program/nsc_cpk_bridge.cpp"
cp "$ROOT/overlay/source/program/nsc_cpk_bridge.hpp" "$EXL/source/program/nsc_cpk_bridge.hpp"
cp "$ROOT/overlay/source/program/condition_compat_generated.hpp" "$EXL/source/program/condition_compat_generated.hpp"
python3 - "$EXL/config.mk" <<'PY'
from pathlib import Path
import re, sys
p=Path(sys.argv[1]); s=p.read_text()
s,n1=re.subn(r'(?m)^LOAD_KIND\s*:=.*$', 'LOAD_KIND := Module', s, count=1)
s,n2=re.subn(r'(?m)^PROGRAM_ID\s*:=.*$', 'PROGRAM_ID := 0100FA10190A0000', s, count=1)
s,n3=re.subn(r'(?m)^CXX_FLAGS\s*:=.*$', 'CXX_FLAGS := -Wno-non-c-typedef-for-linkage', s, count=1)
s,n4=re.subn(r'(?m)^ELF_EXTRACT\s*:=.*$', 'ELF_EXTRACT := $(PWD)/p59a_final.elf', s, count=1)
if (n1,n2,n3,n4)!=(1,1,1,1): raise SystemExit(f'config patch failed {(n1,n2,n3,n4)}')
p.write_text(s)
PY
echo "[+] P59A action-mode-dispatch overlay prepared"
grep -E '^(LOAD_KIND|PROGRAM_ID|CXX_FLAGS|ELF_EXTRACT)[[:space:]]*:=' "$EXL/config.mk"
