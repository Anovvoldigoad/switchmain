#!/usr/bin/env python3
from pathlib import Path
import hashlib, shutil, sys

ROOT = Path.cwd()
if not (ROOT / 'overlay/source/program/nsc_cpk_bridge.cpp').exists():
    fallback = Path('/storage/emulated/0/Downloads')
    if (fallback / 'overlay/source/program/nsc_cpk_bridge.cpp').exists():
        ROOT = fallback
    else:
        raise SystemExit('ERROR: run from NSC2Switch repo root; overlay/source/program/nsc_cpk_bridge.cpp not found')

CPP = ROOT / 'overlay/source/program/nsc_cpk_bridge.cpp'
HPP = ROOT / 'overlay/source/program/nsc_cpk_bridge.hpp'
MAIN = ROOT / 'overlay/source/program/main.cpp'
for p in (CPP,HPP,MAIN):
    if not p.exists(): raise SystemExit(f'ERROR: missing {p}')

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def backup(p):
    q=p.with_name(p.name+'.pre_p85a')
    if not q.exists(): shutil.copy2(p,q)
    return q

cpp=CPP.read_text()
hpp=HPP.read_text()
main=MAIN.read_text()

# Strict parent/source sanity. We intentionally do NOT patch a historical source tree.
required_cpp = ['InstallP84AIntentDiscriminator', '[NSC:P84A] READY', '[NSC:P84A] SLOT1928_NATIVE', '[NSC:P84A] H750170']
missing=[s for s in required_cpp if s not in cpp]
if missing:
    raise SystemExit('ERROR: P84A parent source not recognized; missing: '+', '.join(missing))
if 'nsc::InstallP84AIntentDiscriminator();' not in main:
    if 'nsc::InstallP85AF58IntentProbe();' in main and '[NSC:P85A]' in cpp:
        print('P85A already applied; no changes.')
        for p in (CPP,HPP,MAIN): print(f'{p}: {sha(p)}')
        raise SystemExit(0)
    raise SystemExit('ERROR: main.cpp is not the expected P84A parent')
if '[NSC:P85A]' in cpp or 'InstallP85AF58IntentProbe' in cpp:
    raise SystemExit('ERROR: P85A marker already exists in cpp but main is inconsistent; inspect manually')

for p in (CPP,HPP,MAIN):
    print(f'BEFORE {p}: {sha(p)}')
    print(f'BACKUP {backup(p)}')

P85 = r'''

// ============================================================================
// P85A — read-only F58 intent/input probe.
// Parent: P84A observation-only discriminator.
//
// Why this target:
//  * main+0x7F46B4 calls actor vtable +0xF58 and returns at 0x7F46B8.
//  * relocation audit resolves the custom actor's +0xF58 slot to main+0x7D3138.
//  * historical runtime: vanilla XA => F58 ret=0, vanilla UJ => F58 ret=1,
//    at the same exact caller with E94=1. Thus F58 is a real native
//    XA-vs-UJ decision boundary, but P85A NEVER changes its result.
//
// P85A logs raw input/control masks before Orig() so XA vs XXA can be diffed
// without guessing a Switch equivalent for the PC MovesetPlus latch.
// ============================================================================
namespace {

constexpr ptrdiff_t kP85F58Offset = 0x7D3138;
constexpr ptrdiff_t kP85F58CallerStart = 0x7F46A4;
constexpr ptrdiff_t kP85F58CallerReturn = 0x7F46B8;

struct P85F58Snapshot {
    uint32_t e60, e94, e98, e9c, ea0;
    uint32_t gate10f40, mask11710, bdc8;
    uint32_t in3fc, in404, in408, in40c, in410;
    uint32_t m594, m598, m59c, m5a0;
    uint32_t m5a4, m5a8, m5ac, m5b0;
    uint32_t m5b4, m5b8, m5bc, m5c0, m5c4, m5c8;
};

static P85F58Snapshot P85ReadF58Snapshot(void* actor) {
    P85F58Snapshot s{};
    if (!actor) return s;
    auto* b = reinterpret_cast<const volatile uint8_t*>(actor);
    auto* c = b + 0x228;
    auto rw = [](const volatile uint8_t* p, ptrdiff_t off) -> uint32_t {
        return *reinterpret_cast<const volatile uint32_t*>(p + off);
    };
    s.e60 = rw(b,0xE60); s.e94 = rw(b,0xE94); s.e98 = rw(b,0xE98);
    s.e9c = rw(b,0xE9C); s.ea0 = rw(b,0xEA0);
    s.gate10f40 = rw(b,0x10F40); s.mask11710 = rw(b,0x11710); s.bdc8 = rw(b,0xBDC8);
    s.in3fc = rw(c,0x3FC); s.in404 = rw(c,0x404); s.in408 = rw(c,0x408);
    s.in40c = rw(c,0x40C); s.in410 = rw(c,0x410);
    s.m594 = rw(c,0x594); s.m598 = rw(c,0x598); s.m59c = rw(c,0x59C); s.m5a0 = rw(c,0x5A0);
    s.m5a4 = rw(c,0x5A4); s.m5a8 = rw(c,0x5A8); s.m5ac = rw(c,0x5AC); s.m5b0 = rw(c,0x5B0);
    s.m5b4 = rw(c,0x5B4); s.m5b8 = rw(c,0x5B8); s.m5bc = rw(c,0x5BC); s.m5c0 = rw(c,0x5C0);
    s.m5c4 = rw(c,0x5C4); s.m5c8 = rw(c,0x5C8);
    return s;
}

static std::atomic<uint32_t> g_p85_f58_seq{0};

HOOK_DEFINE_TRAMPOLINE(P85F58IntentProbeHook) {
    static uint32_t Callback(void* actor, uint32_t mode, uint32_t context) {
        uintptr_t caller_lr = 0;
        asm volatile("mov %0, x30" : "=r"(caller_lr));
        const ptrdiff_t caller_off = MainRelativeOffset(caller_lr);

        uint32_t side = 0xFFFFFFFFu, char_id = 0xFFFFFFFFu;
        const bool valid = ReadActorIdentity(actor, side, char_id);
        const bool semantic = valid && P64QuerySemanticUltimateJutsu(actor);
        const P85F58Snapshot pre = P85ReadF58Snapshot(actor);

        // Preserve native behavior exactly. No override, no second call.
        const uint32_t ret = Orig(actor, mode, context);

        if (valid && side == 0u && caller_off == kP85F58CallerReturn) {
            const uint32_t seq = g_p85_f58_seq.fetch_add(1, std::memory_order_relaxed);
            Logging.Log("[NSC:P85A] F58 seq=%u actor=%p side=%u char=%u semantic=%u mode=%u context=%u ret=%u caller=0x%lx e60=%u e94=%u e98=%u e9c=%u ea0=%u g10f40=%u m11710=%08x bdc8=%u",
                        seq, actor, side, char_id, semantic ? 1u : 0u, mode, context, ret,
                        static_cast<unsigned long>(caller_off), pre.e60, pre.e94, pre.e98,
                        pre.e9c, pre.ea0, pre.gate10f40, pre.mask11710, pre.bdc8);
            Logging.Log("[NSC:P85A] INPUT seq=%u i3fc=%08x i404=%08x i408=%08x i40c=%08x i410=%08x m594=%08x m598=%08x m59c=%08x m5a0=%08x",
                        seq, pre.in3fc, pre.in404, pre.in408, pre.in40c, pre.in410,
                        pre.m594, pre.m598, pre.m59c, pre.m5a0);
            Logging.Log("[NSC:P85A] MAP seq=%u m5a4=%08x m5a8=%08x m5ac=%08x m5b0=%08x m5b4=%08x m5b8=%08x m5bc=%08x m5c0=%08x m5c4=%08x m5c8=%08x",
                        seq, pre.m5a4, pre.m5a8, pre.m5ac, pre.m5b0, pre.m5b4,
                        pre.m5b8, pre.m5bc, pre.m5c0, pre.m5c4, pre.m5c8);
        }
        return ret;
    }
};

static bool InstallP85F58IntentProbeHook() {
    static constexpr uint32_t kF58Expected[] = {
        0xFC1C0FE8, 0xA9015FFE, 0xA90257F6, 0xA9034FF4,
        0x5281E808, 0x72A00028, 0xB8686808, 0x2A010108, 0x340000C8,
    };
    static constexpr uint32_t kCallerExpected[] = {
        0xF9400268, 0xAA1303E0, 0x2A1F03E1,
        0xF947AD08, 0xD63F0100, 0x34000400,
    };
    bool ok = true;
    if (!MatchWords(kP85F58Offset, kF58Expected)) {
        LogFingerprintFail("P85_F58", kP85F58Offset); ok = false;
    }
    if (!MatchWords(kP85F58CallerStart, kCallerExpected)) {
        LogFingerprintFail("P85_F58_CALLER", kP85F58CallerStart); ok = false;
    }
    if (!ok) return false;
    P85F58IntentProbeHook::InstallAtOffset(kP85F58Offset);
    return true;
}

} // anonymous namespace — P85A

void InstallP85AF58IntentProbe() {
    // Exactly one parent installation path. P84A keeps its native/observation-only
    // slot1928 + H750170 instrumentation and installs its proven lower baselines.
    InstallP84AIntentDiscriminator();
    const bool f58 = InstallP85F58IntentProbeHook();
    Logging.Log("[NSC:P85A] READY baseline_p84=1 f58_probe=%d f58=0x7d3138 caller=0x7f46b8 readonly=1 preserve_orig=1 no_force_return=1 no_force87=1 no_force700=1 no_action445_rewrite=1 no_selector8=1 no_char281_branch=1",
                f58 ? 1 : 0);
}
'''

# Insert source immediately before the final namespace close.
close='} // namespace nsc'
pos=cpp.rfind(close)
if pos < 0: raise SystemExit('ERROR: cannot find final namespace nsc close')
cpp = cpp[:pos] + P85 + '\n' + cpp[pos:]

# Add public declaration after P84 declaration; this is intentionally strict.
needle='void InstallP84AIntentDiscriminator();'
if needle not in hpp:
    raise SystemExit('ERROR: header does not declare InstallP84AIntentDiscriminator')
hpp = hpp.replace(needle, needle+'\nvoid InstallP85AF58IntentProbe();', 1)

# One installation path: main -> P85 -> P84.
main = main.replace('nsc::InstallP84AIntentDiscriminator();','nsc::InstallP85AF58IntentProbe();',1)
main = main.replace('NSC P84A intent discriminator exception','NSC P85A F58 intent probe exception')
main = main.replace('NSC P84A exception','NSC P85A F58 intent probe exception')

CPP.write_text(cpp)
HPP.write_text(hpp)
MAIN.write_text(main)

print('P85A_SOURCE_PATCH=PASS')
for p in (CPP,HPP,MAIN): print(f'AFTER  {p}: {sha(p)}')
print('NEXT: python verify_p85a_source.py && git diff --check')
