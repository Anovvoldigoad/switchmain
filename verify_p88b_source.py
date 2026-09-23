from pathlib import Path
R=Path.cwd();c=(R/'overlay/source/program/nsc_cpk_bridge.cpp').read_text();h=(R/'overlay/source/program/nsc_cpk_bridge.hpp').read_text();m=(R/'overlay/source/program/main.cpp').read_text()
checks={'MAIN':m.count('nsc::InstallP88BBootSafeUJHelperProbe();')==1,'HEADER':h.count('void InstallP88BBootSafeUJHelperProbe();')==1,'READY':'[NSC:P88B] READY' in c,'HELPER':'[NSC:P88B] HELPER' in c,'TARGET':'0x8B30E4' in c,'P85_CHAIN':'void InstallP88BBootSafeUJHelperProbe(){InstallP85AF58IntentProbe();' in c,'NO_P87_CHAIN':'void InstallP88BBootSafeUJHelperProbe(){InstallP87AActiveProducerProbe();' not in c,'NO_P88A_MAIN':'InstallP88AWideUJAdmissionTrace();' not in m,'NO_281':'==281' not in c[c.find('// P88B boot-safe'):c.find('} // anonymous P88B')+20]}
for k,v in checks.items():print(f'P88B_{k}={"PASS" if v else "FAIL"}')
if not all(checks.values()):raise SystemExit('P88B_SOURCE_SANITY=FAIL')
print('P88B_SOURCE_SANITY=PASS')
