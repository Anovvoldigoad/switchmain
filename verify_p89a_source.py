#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd()
cp=R/"overlay/source/program/nsc_cpk_bridge.cpp"
hp=R/"overlay/source/program/nsc_cpk_bridge.hpp"
mp=R/"overlay/source/program/main.cpp"
for p in (cp,hp,mp):
    if not p.exists(): raise SystemExit(f"P89A_SOURCE_SANITY=FAIL missing {p}")
c=cp.read_text(); h=hp.read_text(); m=mp.read_text()
start=c.find("// P89A generic phase-3 actor-predicate compatibility bridge.")
section=c[start:] if start >= 0 else ""
checks={
 "MAIN_ACTIVE":m.count("nsc::InstallP89APhase3ActorPredBridge();")==1,
 "P88B_MAIN_INACTIVE":"nsc::InstallP88BBootSafeUJHelperProbe();" not in m,
 "HEADER":h.count("void InstallP89APhase3ActorPredBridge();")==1,
 "READY":"[NSC:P89A] READY" in c,
 "ACTOR_LOG":"[NSC:P89A] ACTOR_PRED" in c,
 "TARGET":"kP89ActorPred = 0x7E24EC" in c,
 "FULL_FINGERPRINT":all(x in section for x in ["0xF81F0FFE","0xF9400008","0xF94C7508","0xD63F0100","0x7100041F","0x1A9F17E0","0xF84107FE","0xD65F03C0"]),
 "P88B_PARENT":"InstallP88BBootSafeUJHelperProbe();" in section,
 "PHASE_GATE":"bda4 == 3" in section and "bdc8 == 1" in section,
 "SEMANTIC_GATE":"P64QuerySemanticUltimateJutsu(actor)" in section,
 "MEMBERSHIP_GATE":"ContainsOugiAwakeningId(cid)" in section,
 "PRESERVE_NATIVE":"const uint32_t out = bridge ? 1u : native_ret;" in section,
 "CORRECT_OFFSETS":all(x in c for x in ["s106f4","0x106F4","s123e0","0x123E0","s123e4","0x123E4"]),
 "NO_WRONG_OFFSETS":all(x not in c for x in ["s116f4","0x116F4","s133e0","0x133E0","s133e4","0x133E4"]),
 "NO_CHAR281_BRANCH":"==281" not in section.replace(" ",""),
}
for k,v in checks.items(): print(f"P89A_{k}={'PASS' if v else 'FAIL'}")
if not all(checks.values()): raise SystemExit("P89A_SOURCE_SANITY=FAIL")
print("P89A_SOURCE_SANITY=PASS")
