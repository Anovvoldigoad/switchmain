# R204C native mtob PROCESS trace

R204C fixes the R204B PROCESS hook offset typo: `0x106F404` -> `0x116F404`.

The clean Switch v1.70 main contains the exact 8-word PROCESS fingerprint at `main+0x116F404`. R204B proved `mtobprm_load` opens and reaches status 2, while `mtobcharsel.xfbin` opens successfully but is repeatedly requested without a recorded status-2 transition. R204C adds the missing read-only PROCESS observation and requires it to install successfully so the post-open XFBIN processing result can be classified.

No game `main` override, CPK binding, ID patching, path rewriting, return overriding, or gameplay mutation is installed.

Expected startup marker:

```text
[NSC:R204C] READY installed=1 process_installed=1 ...
```

Deploy this temporary `subsdk9` only with the same R203A RomFS carrier used for the empty Naruto preview control.
