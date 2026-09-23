P88A — WIDE NATIVE UJ ADMISSION TRACE (READ ONLY)

Purpose: locate the first native divergence that prevents a custom/mod character from advancing BDC8 1->2 and therefore reaching F58/state87/action700. No gameplay fix is applied.

Whole-function trampoline probes only: 0x7D3AD0 producer, 0x8B30E4 helper, 0x7E24EC actor predicate, 0x7C553C control mode, 0x7C6074 live mask predicate, 0x7C5FB0 mask/arg predicate, 0x7D5C10 state2 predicate, 0x78FDC0 gate14. Every hook calls Orig and preserves its return.

Snapshots: BDA4, BDC8, E94/E98/E9C, actor+116F4, +133E0, +133E4, +7CC, control+404/+408/+5A0. P85 F58/action baseline remains installed. No char-ID-specific gameplay branch.

Apply from current P87A repo:
  python3 APPLY_P88A_WIDE_UJ_ADMISSION_TRACE.py
  python3 verify_p88a_source.py
  git diff --check
  git add -A && git commit -m "P88A wide UJ admission trace" && git push

Workflow auto-runs on push main and may also be dispatched manually. Ensure prepare_exlaunch.sh stages p81_ougi_awake_ids.hpp.

Runtime matrix, exact order:
1 vanilla ordinary XA x2
2 same vanilla native UJ x2
3 custom ordinary XA x2
4 custom intended XXA/UJ x2
5 optional victim-UJ safety once
Return the complete log. Analyze with: python3 analyze_p88a_log.py uzuy_log.txt

Do NOT force BDC8=2, F58, E94=0x87, action700, selector8, or restore raw Event236.
