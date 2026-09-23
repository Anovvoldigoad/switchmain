#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd(); cp=R/'overlay/source/program/nsc_cpk_bridge.cpp'; hp=R/'overlay/source/program/nsc_cpk_bridge.hpp'; mp=R/'overlay/source/program/main.cpp'
c=cp.read_text(); h=hp.read_text(); m=mp.read_text()
if '[NSC:P88B]' in c: raise SystemExit('P88B already applied')
if 'void InstallP87AActiveProducerProbe()' not in c: raise SystemExit('requires current P87A source')
end=c.rfind('\n} // namespace nsc')
if end<0: raise SystemExit('namespace nsc end not found')
block=r'''

// P88B boot-safe helper-only probe. Keep proven P87A producer instrumentation.
namespace {
static constexpr ptrdiff_t kP88BHelper=0x8B30E4;
static std::atomic<uint32_t> gP88BCount{0};
static constexpr uint32_t kP88BLimit=131072;
struct P88BSnap{int32_t bda4,bda8,bdc8,e94,e98,e9c,f7cc,s116f4,s133e0,s133e4;uint32_t c404,c408,c5a0;};
static P88BSnap P88BRead(void* actor){P88BSnap s{};auto*b=reinterpret_cast<volatile uint8_t*>(actor);auto*c=b+0x228;s.bda4=*reinterpret_cast<volatile int32_t*>(b+0xBDA4);s.bda8=*reinterpret_cast<volatile int32_t*>(b+0xBDA8);s.bdc8=*reinterpret_cast<volatile int32_t*>(b+0xBDC8);s.e94=*reinterpret_cast<volatile int32_t*>(b+0xE94);s.e98=*reinterpret_cast<volatile int32_t*>(b+0xE98);s.e9c=*reinterpret_cast<volatile int32_t*>(b+0xE9C);s.f7cc=*reinterpret_cast<volatile int32_t*>(b+0x7CC);s.s116f4=*reinterpret_cast<volatile int32_t*>(b+0x116F4);s.s133e0=*reinterpret_cast<volatile int32_t*>(b+0x133E0);s.s133e4=*reinterpret_cast<volatile int32_t*>(b+0x133E4);s.c404=*reinterpret_cast<volatile uint32_t*>(c+0x404);s.c408=*reinterpret_cast<volatile uint32_t*>(c+0x408);s.c5a0=*reinterpret_cast<volatile uint32_t*>(c+0x5A0);return s;}
HOOK_DEFINE_TRAMPOLINE(P88BHelperHook){static uint32_t Callback(void* actor){uint32_t side=~0u,cid=~0u;bool v=ReadActorIdentity(actor,side,cid);P88BSnap a{};if(v)a=P88BRead(actor);auto r=Orig(actor);if(v&&side==0&&gP88BCount.fetch_add(1)<kP88BLimit){auto z=P88BRead(actor);Logging.Log("[NSC:P88B] HELPER actor=%p side=%u char=%u ret=%u bda4=%d->%d bda8=%d->%d bdc8=%d->%d e94=%d->%d e98=%d->%d e9c=%d->%d f7cc=%d->%d s116f4=%d->%d s133e0=%d->%d s133e4=%d->%d c404=%08x->%08x c408=%08x->%08x c5a0=%08x->%08x",actor,side,cid,r,a.bda4,z.bda4,a.bda8,z.bda8,a.bdc8,z.bdc8,a.e94,z.e94,a.e98,z.e98,a.e9c,z.e9c,a.f7cc,z.f7cc,a.s116f4,z.s116f4,a.s133e0,z.s133e0,a.s133e4,z.s133e4,a.c404,z.c404,a.c408,z.c408,a.c5a0,z.c5a0);}return r;}};
static bool InstallP88BInternal(){static constexpr uint32_t sig[]={0xA9BE57FE,0xA9014FF4,0x9108A014,0xAA0003F3};if(!MatchWords(kP88BHelper,sig)){LogFingerprintFail("P88B_HELP",kP88BHelper);return false;}P88BHelperHook::InstallAtOffset(kP88BHelper);return true;}
} // anonymous P88B

void InstallP88BBootSafeUJHelperProbe(){InstallP87AActiveProducerProbe();const bool ok=InstallP88BInternal();Logging.Log("[NSC:P88B] READY baseline_p87=1 helper_only=1 probe=%d readonly=1 preserve_orig=1 no_shared_control_hooks=1 no_bda4_write=1 no_bdc8_write=1 no_force_return=1 no_force_f58=1 no_force87=1 no_force700=1 no_action445_rewrite=1 no_selector8=1 no_char281_branch=1 limit=%u",ok?1:0,kP88BLimit);}

'''
c=c[:end]+block+c[end:]
needle='void InstallP87AActiveProducerProbe();'
if needle not in h: raise SystemExit('P87 header declaration not found')
h=h.replace(needle,needle+'\nvoid InstallP88BBootSafeUJHelperProbe();',1)
old='nsc::InstallP87AActiveProducerProbe();'
if old not in m: raise SystemExit('P87 main install call not found')
m=m.replace(old,'nsc::InstallP88BBootSafeUJHelperProbe();',1)
cp.write_text(c);hp.write_text(h);mp.write_text(m);print('P88B_SOURCE_PATCH=PASS')
