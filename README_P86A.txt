P86A — BDA4/BDC8 NATIVE PRODUCER PROBE (READ ONLY)
=====================================================

Purpose
-------
P85 proved F58 is downstream of a stronger split: vanilla native UJ arrives at
F58 with actor+BDC8=2, while vanilla XA and all four custom attempts arrive
with BDC8=1. Static 1.70 disassembly proves F58 mode0 literally rejects
BDC8<2 and proves main+0x11F080 owns the BDA4/BDC8 producer state machine.

P86 observes, without mutation:
- main+0x11F080 BDA4/BDC8 native state transitions;
- main+0x7C6074 exact phase1/phase3 input predicate;
- main+0x7E24EC exact phase1/phase3 actor predicate;
- raw native control selector slots used by 0x11F080.

APPLY
-----
cd /storage/emulated/0/Downloads
python3 APPLY_P86A_BDA4_BDC8_PRODUCER_PROBE.py
python3 verify_p86a_source.py
python3 FIX_P86_CI_LINEAGE.py
git diff --check
git status --short

Stage intended files only; never git add .
The CI fixer prints the historical P85 workflow it changed to manual-only.
Stage that exact file too. Example:
git add overlay/source/program/main.cpp \
        overlay/source/program/nsc_cpk_bridge.cpp \
        overlay/source/program/nsc_cpk_bridge.hpp \
        verify_p86a_source.py analyze_p86a_log.py README_P86A.txt P86_STATIC_AUDIT.txt \
        .github/workflows/build-subsdk9-p86a.yml \
        .github/workflows/build-subsdk9-p85a.yml

git diff --cached --check
git commit -m "P86A trace BDA4 BDC8 native producer"
git push

HARDWARE
--------
Use the same controlled order as P85, from neutral state:
1) vanilla ordinary XA x2
2) same vanilla native UJ x2
3) custom ordinary XA x2
4) custom intended XXA/UJ x2
Tobi/custom begins already awakened; do not activate awakening first.
Return the COMPLETE log. Log size is not a blocker.
Afterward, separately run the victim-safety reproducer once if possible.

Expected new markers
--------------------
[NSC:P86A] READY
[NSC:P86A] STATE
[NSC:P86A] CTRL
[NSC:P86A] INPUT_PRED
[NSC:P86A] ACTOR_PRED

Decision
--------
The first native difference between vanilla UJ and custom XXA decides the fix:
- input predicate differs -> restore the upstream input producer/semantic bridge;
- input predicate matches but actor predicate differs -> bridge only that exact native policy;
- both match but phase fails to advance -> trace the phase1->2 producer/event path.
Never force BDC8=2 or F58=1.
