#!/usr/bin/env python3
from pathlib import Path

R = Path.cwd()
cp = R / "overlay/source/program/nsc_cpk_bridge.cpp"
hp = R / "overlay/source/program/nsc_cpk_bridge.hpp"
mp = R / "overlay/source/program/main.cpp"
wf88 = R / ".github/workflows/build-subsdk9-p88b.yml"

for p in (cp, hp, mp):
    if not p.exists():
        raise SystemExit(f"P89A_FAIL missing baseline file: {p}")

c = cp.read_text()
h = hp.read_text()
m = mp.read_text()

for x in [
    "void InstallP88BBootSafeUJHelperProbe()",
    "[NSC:P88B] READY",
    "P64QuerySemanticUltimateJutsu",
    "ContainsOugiAwakeningId",
]:
    if x not in c:
        raise SystemExit(f"P89A_FAIL baseline missing marker: {x}")

if "nsc::InstallP88BBootSafeUJHelperProbe();" not in m:
    raise SystemExit("P89A_FAIL main.cpp is not activating P88B baseline")
if "[NSC:P89A]" in c or "InstallP89APhase3ActorPredBridge" in c:
    raise SystemExit("P89A_FAIL P89A already applied")

# Correct P88B observational-only snapshot transcription offsets.
for old, new in [
    ("s116f4", "s106f4"),
    ("s133e0", "s123e0"),
    ("s133e4", "s123e4"),
    ("0x116F4", "0x106F4"),
    ("0x133E0", "0x123E0"),
    ("0x133E4", "0x123E4"),
]:
    c = c.replace(old, new)

end = c.rfind("\n} // namespace nsc")
if end < 0:
    raise SystemExit("P89A_FAIL namespace nsc end not found")

block = r'''
// P89A generic phase-3 actor-predicate compatibility bridge.
// Preserve native TRUE. Bridge native FALSE only for exact phase-3,
// semantic UJ permission + generated OugiAwakening membership.
// No character-ID hardcode and no gameplay-state/action writes.
namespace {
static constexpr ptrdiff_t kP89ActorPred = 0x7E24EC;
static constexpr uint32_t kP89Limit = 131072;
static std::atomic<uint32_t> gP89Count{0};

HOOK_DEFINE_TRAMPOLINE(P89ActorPredBridgeHook) {
    static uint32_t Callback(void* actor) {
        const uint32_t native_ret = Orig(actor);

        uint32_t side = 0xFFFFFFFFu;
        uint32_t cid = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, cid);

        uint32_t bda4 = 0xFFFFFFFFu;
        uint32_t bdc8 = 0xFFFFFFFFu;
        bool semantic = false;
        bool member = false;
        bool bridge = false;

        if (valid && actor) {
            auto* b = reinterpret_cast<volatile uint8_t*>(actor);
            bda4 = *reinterpret_cast<volatile uint32_t*>(b + 0xBDA4);
            bdc8 = *reinterpret_cast<volatile uint32_t*>(b + 0xBDC8);
            semantic = P64QuerySemanticUltimateJutsu(actor);
            member = ContainsOugiAwakeningId(cid);
            bridge =
                native_ret == 0 &&
                bda4 == 3 &&
                bdc8 == 1 &&
                semantic &&
                member;
        }

        const uint32_t out = bridge ? 1u : native_ret;

        if (valid && side == 0 &&
            gP89Count.fetch_add(1, std::memory_order_relaxed) < kP89Limit) {
            Logging.Log(
                "[NSC:P89A] ACTOR_PRED actor=%p side=%u char=%u "
                "bda4=%u bdc8=%u native=%u semantic=%u member=%u bridge=%u out=%u",
                actor, side, cid, bda4, bdc8, native_ret,
                semantic ? 1u : 0u, member ? 1u : 0u,
                bridge ? 1u : 0u, out);
        }
        return out;
    }
};

static bool InstallP89Internal() {
    static constexpr uint32_t sig[] = {
        0xF81F0FFE, 0xF9400008, 0xF94C7508, 0xD63F0100,
        0x7100041F, 0x1A9F17E0, 0xF84107FE, 0xD65F03C0
    };
    if (!MatchWords(kP89ActorPred, sig)) {
        LogFingerprintFail("P89_ACTOR_PRED", kP89ActorPred);
        return false;
    }
    P89ActorPredBridgeHook::InstallAtOffset(kP89ActorPred);
    return true;
}
} // anonymous P89A

void InstallP89APhase3ActorPredBridge() {
    InstallP88BBootSafeUJHelperProbe();
    const bool ok = InstallP89Internal();
    Logging.Log(
        "[NSC:P89A] READY parent_p88b=1 actor_pred=0x7e24ec probe=%d "
        "generic=1 phase3_only=1 preserve_native_true=1 semantic_gate=1 "
        "membership_gate=1 corrected_snapshots=1 no_bda4_write=1 "
        "no_bdc8_write=1 no_force_f58=1 no_force700=1 "
        "no_action445_rewrite=1 no_selector8=1 no_char281_branch=1 limit=%u",
        ok ? 1 : 0, kP89Limit);
}
'''
c = c[:end] + block + c[end:]

needle = "void InstallP88BBootSafeUJHelperProbe();"
if needle not in h:
    raise SystemExit("P89A_FAIL P88B header declaration missing")
h = h.replace(needle, needle + "\nvoid InstallP89APhase3ActorPredBridge();", 1)

m = m.replace(
    "nsc::InstallP88BBootSafeUJHelperProbe();",
    "nsc::InstallP89APhase3ActorPredBridge();",
    1,
)

# Stop the old P88B workflow from also firing.
if wf88.exists():
    wf88.unlink()

cp.write_text(c)
hp.write_text(h)
mp.write_text(m)
print("P89A_APPLY=PASS")
print("P89A_OLD_P88B_WORKFLOW_REMOVED=1")
