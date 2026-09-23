P85A CI LINEAGE FIX
===================
The observed failure:
  python3 verify_p83a_kit.py
  FATAL P83 active main count
is expected after main.cpp moves from P83/P84 to P85.
It is a stale historical verifier failure, NOT a P85 source or gameplay failure.

This fix:
1. keeps P83 workflow(s) for workflow_dispatch/manual history;
2. removes their automatic push trigger;
3. installs build-subsdk9-p85a.yml as the active push workflow;
4. installs verify_p85a_source.py / README_P85A.txt / analyzer;
5. verifies main -> P85 -> P84 lineage before allowing commit.

Run from /storage/emulated/0/Downloads after extracting this kit there:

  python3 FIX_P85_CI_LINEAGE.py
  python3 verify_p85a_source.py
  git diff --check
  git status --short

Then stage EXPLICITLY:
  git add .github/workflows/build-subsdk9-p85a.yml \
          verify_p85a_source.py README_P85A.txt analyze_p85a_log.py \
          overlay/source/program/main.cpp \
          overlay/source/program/nsc_cpk_bridge.cpp \
          overlay/source/program/nsc_cpk_bridge.hpp

Also stage each P83 workflow printed as P83_MANUAL_ONLY=... because its push trigger was removed.
Do NOT use git add .

Commit/push:
  git commit -m "P85A activate F58 intent probe CI"
  git push

Expected CI preflight now includes:
  P85A_SOURCE_SANITY=PASS
and MUST NOT run verify_p83a_kit.py on push.
