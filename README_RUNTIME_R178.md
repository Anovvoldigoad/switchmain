# NSC2Switch Runtime R178 — D-Pad Animation Eligibility Parity

Parent: R177 exact source lineage, retaining R172 UJ hardware-PASS path, P128 exact 30-word runtime patch, V2N/V2P stage probes, and R175–R177 D-pad diagnostics.

## Why R178 changed direction
R176/R177 proved Right mode3 requests action922 and the actor-local action922 record is empty. However, forensic comparison against historical `P4_TOBI_DECRYPT_COMPILE_STAGE` proves the original PC mod staging also omits `PL_ANM_SPTYPE_ACTION02`. Therefore missing action922 is source-consistent and is **not** repaired here.

The PC UltimateStormAPI source contains a separate native `//Dpad animations` compatibility patch. For PC v1.70 it changes the hard-coded eligibility check `[actor+0xE64] == 124` into `[actor+0xF30] == 1`.

Switch has two independently proven actor-layout shifts of -0x10: `E64→E54` (CharID) and `12B88→12B78` (D-pad charge). R178 therefore maps the PC enable field `F30` to Switch `F20`.

## Exact R178 delta
- Event236 opcode13 now writes `actor+0xF20`, not native Switch `actor+0xF30`.
- Separate fail-closed two-word patch at `main+0x59CEB4`:
  - `B94E5768` `LDR W8,[X27,#0xE54]` → `B94F2368` `LDR W8,[X27,#0xF20]`
  - `7101F11F` `CMP W8,#0x7C` → `7100051F` `CMP W8,#1`
- The frozen V2D/P128 `WordPatch plan[30]` is unchanged.
- Non-UJ opcode23 behavior is unchanged in R178.
- No action force, registry insertion, descriptor clone, char281 gameplay branch, or new trampoline.

## Expected markers
- `[NSC:R178] READY parity=1 ...`
- `[NSC:R178] DPAD_ENABLE ... f20=... f30_observed=...`

## Test
Use a fresh boot for each direction:
1. Left once; save log.
2. Right once; save log.

Build through the included GitHub Actions workflow. The artifact name is `NSC-RUNTIME-R178-dpad-animation-eligibility-parity`.
