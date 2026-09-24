# NSC2Switch MASTER CHECKPOINT — 2026-09-24 R101

## Locked baseline
Program ID: `0100FA10190A0000`
Build ID: `48ece454b61412b9fb46fab2be3f5ef7b2804f39`
Paired main SHA256: `1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0`
Restore main SHA256: `2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9`
exlaunch pin: `229bbd6`

## Corrected custom-UJ sequence
User confirms required custom sequence: `700 -> 707 -> 708 -> 710 -> cinematic`.
P97A suppress-708 experiment is retired and MUST NOT be treated as a fix. Runtime P97 removed the original 707->708 edge but never armed 710; user-visible opponent positioning became wrong.

## Earliest proven post-708 divergence
P96 native path:
- 707 requests 708 through descriptor key `PL_ANM_SPSKILL_1_LOOP`.
- 708 begins with E94=63, E98=136, E9C=0, BDA4=1, BDA8=0; EA4/EA8 restart and advance.
- around EA4=0x5DC / EA8=0x578, while action708 is still active, E9C becomes125.
- state125 then commits: E94=125, E98=63, E9C=0, BDA4=0, BDA8=1.
- downstream main+0x7DE554 requests PlayAction261; action later falls to74.
Therefore 261 is downstream. The first proven wrong fork is the request that queues state125 during action708.

## Static state-request proof
- main+0x7A89A4 is a state-request implementation. It receives requested state in W1 and writes W1 to actor+E9C at main+0x7A89F0 after native validation.
- main+0x7A8A9C is a direct/simple E9C setter.
- main+0x138D14 is a subclass override of the same virtual request-state slot as 0x7A89A4.
- relocation topology proves that request-state virtual slot is `vtable+0xE28`.
- 155 native vtables use 0x7A89A4 at +0xE28; one uses override 0x138D14.
- historical runtime custom actor vtable is main+0x201BF58. Exact pinned relocation mapping of that table: +0xE28 -> 0x7A89A4, +0xE40 -> 0x7B468C, +0xEB0 -> 0x772594. The latter two are independently runtime-proven.

## P98B design
P98B uses P96 as functional parent, so native 707->708 is restored and P97 guard is absent.
It adds one observation-only whole-function trampoline at main+0x7A89A4. Callback always calls Orig exactly once with unchanged arguments/result.
It logs requested state, args, caller LR/call instruction, actor vtable +0xE28 target, and pre/post action/E94/E98/E9C/EA4/EA8/BDA4/BDA8/BDC8.

### Decision
- If `STATE_REQ req=125 action=708` appears: `caller_off` is exact state125 producer. Disassemble/fix that producer generically; do not block261 or force710.
- If E9C=125 still appears but no P98B req=125: state125 bypasses base vslot; pivot to direct/non-virtual writer 0x7A8A9C family.

## Non-negotiable
No char281 gameplay branch. No force700/708/710. No E9C/E94/EA4/BDA writes. Preserve P50 victim safety and P89 admission bridge.
