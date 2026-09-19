NSC2Switch P50A — SC 1.70 CONDITION COMPATIBILITY CORE
======================================================

Purpose
-------
P50A ports the proven SC 1.70 condition-lookup compatibility concept to Switch.
It is a functional candidate, not a 708->710 force patch and not a Tobi-ID patch.

Why this build exists
---------------------
Official Switch 1.70 has the same key boundary shape found in the PC SC 1.70
compatibility regression:
- native condition descriptor getter main+0x754A80 stops at the vanilla geometry;
- condition name/hash loops stop at 512;
- current merged Tobi conditionprm has five additional conditions, total 517.
Historical P41A installed the five entries but hardware still resolved SW_MTOB_XH
as 0. P50A changes the consumer architecture: the native getter is trampoline-
extended with a generated runtime descriptor table, while the paired main expands
only the native loop/raw-table bounds.

Functional core retained
------------------------
- CPK bridge main+0x473190.
- Generic custom Event236 compatibility main+0x816300, including the P48C-safe
  visibility/control shadow behavior that prevents opponent disappearance.
- PlayAction probe main+0x766B8C for UJ progression only.

New P50A condition compatibility
--------------------------------
- Condition descriptor getter hook main+0x754A80.
- Event121 SELF parity hook main+0x8134F8.
- Generated condition table from condition_compat_manifest.json.
- Paired main raises native raw/name/hash loop bounds 512 -> 517 at exactly:
  0x747878, 0x7774DC, 0x777770, 0x777938, 0x777A6C.
- No split-bank text cave, no donor char alias, no forced awakening, no 708->710.
- Active trampolines: exactly 5.

Current generated conditions
----------------------------
512 SW_MTOB_XH
513 SW_MTOB_ST
514 YXNQ_MTOB
515 SW_MTOB_BREAK
516 WC_MTOB_BREAK

The implementation is manifest-generated. Future mod sets should regenerate the
manifest/table + paired main together instead of adding character-ID branches.

MANDATORY paired deployment
---------------------------
P50A subsdk9 MUST be used with the P50A paired main from deploy/, not the restore
main and not an older main.

P50A paired main SHA256:
  8219e048a23335197c7eeb3fe9d9016eab7d8a1c434dc24a0cd4cb541c45b6be

Restore/rollback main SHA256:
  2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9

Build ID remains:
  48ece454b61412b9fb46fab2be3f5ef7b2804f39

Keep unchanged:
- current P33A Sorted=0 Tobi_Switch.cpk;
- current loose charicon / current RomFS merged parameters.

Build
-----
Use the included GitHub Actions workflow or the same pinned devkitA64/exlaunch
workflow used for P48C/P49A. The workflow outputs both the compiled subsdk9 and
the mandatory paired main.

Hardware test order
-------------------
1. Fresh boot. READY must show cpk=1 event236=1 play=1 cond=1 and
   installed_trampolines=5.
2. Normal Tobi battle smoke test: opponent must remain visible/hittable.
3. Trigger Tobi custom D-Pad/Izanagi condition if available.
4. Attempt True Awakening several times.
5. Use Tobi Kamui UJ once and let the sequence finish/fail naturally.
6. Run one vanilla Naruto UJ control.
7. Stop emulator and run: python3 analyze_p50a_log.py uzuy_log.txt

Decisive markers
----------------
Expected condition success looks like:
  [NSC:P50A] COND_GET index=512 ... name=SW_MTOB_XH ...
  [NSC:P50A] EVT121_SELF ... text=SW_MTOB_XH ... resolved=512 ... executed=1 ...

If this appears and Kamui reaches PlayAction 710, the condition-lookup gap is a
causal part of the UJ bug. If custom conditions resolve correctly but Kamui still
stops on 708 and True Awakening remains unavailable, the next isolated consumer
is specialCond/ougiAwakening membership; do not force action 710.
