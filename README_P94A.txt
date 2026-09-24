NSC2Switch P94A — sequence-controller zero-extra trace (P40 drop-in)

Purpose
- Preserve proven P89 admission bridge and P93 runtime trace chain.
- Add NO new hook/trampoline and NO gameplay write.
- Trace the native sequence controller that static analysis linked to the generic 0x772594 action wrapper.

P93 runtime lock
- Vanilla successful UJ remains action707 until native handoff-arm state appears:
  E9C=137, BDA4=0, BDA8=1, then action710 at caller 0x7E6EC8.
- Custom semantic UJ leaves action707 early at EA4=0x258, BDA4=1/BDA8=0/E9C=0 and requests 708 at caller 0x7725D0.

Static v1.70 proof used by P94A
- 0x772594 is a generic action wrapper; 0x7725CC calls 0x766B8C with W1 already selected.
- Sole direct BL xref to 0x772594 is 0x48FE0 inside 0x48F18.
- 0x48F18 consumes actor-owned action sequence vectors and actor+0x1246C current index.
- Sequence controller families observed statically: actor+0x12470, +0x124A0, +0x124D0; mode at +0x12504.
- 0x7E8E2C is a separate target/opponent/timing predicate in the later 710 corridor; P94A does not alter it.

New read-only markers
- [NSC:P94A] SEQCTRL
  actor+12320, +12460, +12468, +1246C, +12500, +12504 and vector counts.
- [NSC:P94A] SEQVEC
  vector begin/end/cap, first six action IDs, and prev/current/next item for current index.

Safety locks
- zero extra trampolines
- no force708 / no force710
- no char281 gameplay branch
- no state writes
- no Event236 changes

Install/build
Extract at repo root, then:
  git add -A
  git commit -m "P94A sequence controller zero-extra trace"
  git push
Download CI artifact: NSC-P94A-sequence-controller-zero-extra-trace
