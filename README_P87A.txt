P87A — ACTIVE BDA4/BDC8 PRODUCER PROBE (READ ONLY)

P86A hooked base virtual implementation main+0x11F080, but log26 produced zero probe records.
Independent RELA slot-family enumeration proves the same virtual slot is overwhelmingly overridden by main+0x7D3AD0 in player-character vtables.

Static proof in paired main:
- 0x7D3AD0 builds actor+0xBCE8 base.
- BDA4 = BCE8+0xBC; BDC8 = BCE8+0xE0.
- 0x7D3C60 writes BDC8=0.
- 0x7D3EB0 MOV W9,#2; 0x7D3EB4 writes BDC8=2.
- 0x7D40D8 MOV W9,#3; 0x7D40DC writes BDC8=3.
- before BDC8=2: 0x7D3E88 -> 0x8B30E4, 0x7D3E98 -> 0x7E24EC, 0x7D3EA8 -> 0x78FDC0(actor,14).

P87A is observation-only. It does not force BDC8/F58/state87/action700/selector8 and has no char281 gameplay branch.

Apply from current P86A source repo:
  python3 APPLY_P87A_ACTIVE_PRODUCER_PROBE.py
  python3 verify_p87a_source.py
  git diff --check
Then commit/push and run: Build NSC P87A active producer probe

Hardware order:
1 vanilla ordinary XA x2
2 same vanilla native UJ x2
3 custom ordinary XA x2
4 custom intended XXA/UJ x2
Return full log. Run victim-UJ safety once if possible.
