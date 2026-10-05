# R252 hardware result — uzuy_log(36).txt

Input log:
- bytes: 190779
- SHA256: 2ed49a45d76c7434e80bf8da8c28733d724471cafa7978d626210b2bf7be80d0

Hard runtime facts:
- R252 installs read-only with six hooks and no main/gameplay/ID/path/return override.
- target registry capture succeeds for `data/ui/max/crsel/c/mtobcharsel.xfbin`.
- target reaches Wait state (`state5c=3`, `phase6c=0`).
- `[self+0x140]=1`.
- immediately after Wait enter and throughout the bounded Wait-update trace:
  - `[self+0x188]=0`
  - `[self+0x190]=0`
  - `child_count=0`
- no `WAIT_READY_GATE`, `WAIT_SECONDARY_GATE`, or `WAIT_CONSUME` event occurs.

Locked interpretation:
- `R252_WAIT_CHILD_VECTOR=EMPTY`
- `R252_WAIT_READY_GATE_NOT_REACHED=HARD_PASS`
- prior hypothesis "a populated Wait child exists but readiness returns zero" is FALSIFIED.
- Wait is the visible stall state, but the missing prerequisite is earlier: the child vector was never constructed.
