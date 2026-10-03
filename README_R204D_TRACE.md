# R204D — native mtob completion-writer trace

Read-only diagnostic for Switch v1.70 / Build ID 48ECE454B61412B9FB46FAB2BE3F5EF7B2804F39.

R209A proved that even the byte-exact historical Tobi `mtobcharsel.xfbin` opens and enters
PROCESS with status=1/readerr=0 but does not visibly complete to status=2, while the parent
`mtobprm_load` does complete. R204D therefore stops changing payload data and observes the
exact native state writers.

Additional exact hooks:
- main+0x120661C: generic nuccFileLoad status setter
- main+0x1206690: success setter; stores resource pointer at +0x50 and status=2 at +0x68

Static disassembly proves the success setter has one direct BL caller at main+0x116F370.
R204D maps load-object pointers back to the paths seen by LOAD_CREATE/LOAD_REQ and logs:

    [NSC:R204D] STATE_SET ... path=... requested=N before=N after=N
    [NSC:R204D] SUCCESS_SET ... path=... resource=... before=N after=2

No status, return, path, CPK binding, ID range, gameplay, or main override is changed.
Use with the R209A seven-file sound.cpk control and no external ModdingAPI CPK.
