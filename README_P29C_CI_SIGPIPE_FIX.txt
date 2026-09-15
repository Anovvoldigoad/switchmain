P29C CI SIGPIPE FIX
===================

Scope: CI-only fix. Runtime tracer source and prepare_exlaunch.sh are unchanged from P29B.

Observed failure:
  `set -euxo pipefail` + `make --version | head -n 1` caused exit code 141 (SIGPIPE).
  `head` exits after receiving the requested lines; the producer can then receive SIGPIPE,
  and `pipefail` propagates that as a failed GitHub Actions step.

Changes in .github/workflows/build-subsdk9-p29.yml:
  1. `make --version | head -n 1` -> `make --version`
  2. `aarch64-none-elf-g++ --version | head -n 2` -> full `--version`
  3. diagnostic `find | sort | head -n 100 || true` -> `find | sort | sed -n '1,100p' || true`

No changes to:
  - overlay/source/program/main.cpp
  - overlay/source/program/nsc_cpk_bridge.cpp
  - overlay/source/program/nsc_cpk_bridge.hpp
  - prepare_exlaunch.sh
  - analyze_p29_log.py

Expected next CI stage after this fix:
  Clone pinned exlaunch -> apply P29 overlay -> make -j2 -> collect subsdk9.
