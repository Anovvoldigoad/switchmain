NSC2Switch P95A — queued-action + wrapper-parent zero-extra trace (P40 drop-in)

Why P95A
- P94A runtime falsified the current actor+0x12460/+0x1246C sequence-controller hypothesis for the observed custom 707->708 transition: all three +0x12470/+0x124A0/+0x124D0 vectors were invalid at the decisive call.
- Direct-BL scanning was incomplete because main+0x772594 is also reached through virtual dispatch.
- Static v1.70 code around main+0x7732A0 loads W1 from actor+0x10600 and calls vtable+0xEB0; a second vtable+0xEB0 call exists at main+0x7EFF88. Direct main+0x48FE0 remains a third known parent class.

What P95A adds (read-only, no new hook)
1) [NSC:P95A] QUEUECTRL
   Samples actor+0x104DC/+0x104E0 and the nearby +0x105E8..+0x10610 family, with explicit +0x105F4/+0x105F8/+0x105FC/+0x10600 values.
   Also logs the actor vtable+0xEB0 target and its main-relative offset.
2) [NSC:P95A] WRAPPER_PARENT
   Only when existing PlayAction sees caller_off=0x7725D0 in UJ range.
   Captures SP at PlayAction callback entry, then read-only scans upward for AArch64 BL/BLR return addresses.
   Explicitly reports known parent returns:
   - 0x48FE4  : direct 0x48F18 -> 0x772594 path
   - 0x7732A8 : virtual vtable+0xEB0 path whose W1 is loaded from actor+0x10600
   - 0x7EFF8C : alternate virtual vtable+0xEB0 path whose W1 comes from a helper result
   It also records generic call-return candidates plus any stack return preceded by LDR X8,[X8,#0xEB0]; BLR X8.

Safety locks
- parent remains P94/P93/P89 functional lineage
- zero extra trampolines
- no inline P95 hook
- no gameplay/state writes
- no force708 / no force710
- no character-281 gameplay branch
- no Event236 change

Fast test
A. Vanilla character: connect a successful UJ through 707 -> 710.
B. Custom semantic character: reproduce 707 -> 708.
C. Send the complete log. If desired, locally run:
   python3 analyze_p95a_log.py uzuy_log.txt

Interpretation of a 708 WRAPPER_PARENT line
- hit7732a8=1 AND q10600=000002c4 (708 decimal): producer is localized to the actor+0x10600 queued-action path.
- hit7eff8c=1: producer is the alternate helper-selected virtual path; do NOT patch +0x10600 based on that run.
- hit48fe4=1: P94 sequence-path rejection must be revisited with exact parent proof.
- none of the three: use e0..e5/c0..c7 return candidates to identify another indirect parent without another blind direct-xref assumption.

Install/build
Extract at repository root, then:
  git add -A
  git commit -m "P95A queued action parent zero-extra trace"
  git push
Download CI artifact:
  NSC-P95A-queued-action-parent-zero-extra-trace
