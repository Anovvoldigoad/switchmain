NSC2Switch P89A COMPLETE DROP-IN BUILD KIT
Target: Storm Connections Switch v1.70 / Program 0100FA10190A0000
Baseline: boot-proven P88B lineage, paired main SHA256 1adc4dfe...

DEPLOYMENT (no APPLY script, no source edits):
1. Extract this ZIP directly over the repository root with overwrite enabled.
2. python3 verify_p89a_source.py
3. git add -A
4. git commit -m "P89A complete drop-in phase3 actor predicate bridge"
5. git push origin main
6. Use ONLY workflow: Build NSC P89A complete drop-in phase3 actor predicate bridge
7. Download artifact: NSC-P89A-complete-dropin

P87A/P88A workflow files are overwritten as workflow_dispatch-only historical stubs,
so a normal push launches only P89A.

P89A policy:
- hook whole function at main+0x7E24EC using fingerprint already used by P87A runtime probe
- preserve native TRUE
- bridge native FALSE only at BDA4=3, BDC8=1
- require semantic UJ permission and generated OugiAwakening membership
- generic: no char281 branch
- no BDA4/BDC8/F58/action/state writes
- P88B helper probe remains parent instrumentation

Test matrix after boot:
1. vanilla ordinary XA x2
2. vanilla native UJ x2
3. custom ordinary XA x2
4. custom intended XXA/UJ x2
Capture full emulator log and upload it.
