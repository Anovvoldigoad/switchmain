#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd(); cp=R/'overlay/source/program/nsc_cpk_bridge.cpp'; hp=R/'overlay/source/program/nsc_cpk_bridge.hpp'; mp=R/'overlay/source/program/main.cpp'
c=cp.read_text(); h=hp.read_text(); m=mp.read_text()
if '[NSC:P88A]' in c: raise SystemExit('P88A already applied')
if 'void InstallP87AActiveProducerProbe()' not in c: raise SystemExit('requires current P87A source')
end=c.rfind('\n} // namespace nsc')
if end<0: raise SystemExit('namespace nsc end not found')
block=r'''

// P88A wide native UJ admission trace. Observation only; every hook calls Orig.
namespace {
static constexpr ptrdiff_t kP88Prod=0x7D3AD0, kP88Helper=0x8B30E4, kP88ActorPred=0x7E24EC;
static constexpr ptrdiff_t kP88CtrlMode=0x7C553C, kP88Input=0x7C6074, kP88Mask=0x7C5FB0;
static constexpr ptrdiff_t kP88State2=0x7D5C10, kP88Gate14=0x78FDC0;
static std::atomic<uint32_t> g88prod{0},g88help{0},g88actor{0},g88ctrl{0},g88input{0},g88mask{0},g88state2{0},g88gate14{0};
static constexpr uint32_t kP88Limit=65536;
struct P88Snap {int32_t bda4,bdc8,e94,e98,e9c,s116f4,s133e0,s133e4,f7cc;uint32_t c404,c408,c5a0;};
static P88Snap P88Read(void* actor){P88Snap s{};auto*b=reinterpret_cast<volatile uint8_t*>(actor);auto*c=b+0x228;
 s.bda4=*reinterpret_cast<volatile int32_t*>(b+0xBDA4);s.bdc8=*reinterpret_cast<volatile int32_t*>(b+0xBDC8);
 s.e94=*reinterpret_cast<volatile int32_t*>(b+0xE94);s.e98=*reinterpret_cast<volatile int32_t*>(b+0xE98);s.e9c=*reinterpret_cast<volatile int32_t*>(b+0xE9C);
 s.s116f4=*reinterpret_cast<volatile int32_t*>(b+0x116F4);s.s133e0=*reinterpret_cast<volatile int32_t*>(b+0x133E0);s.s133e4=*reinterpret_cast<volatile int32_t*>(b+0x133E4);s.f7cc=*reinterpret_cast<volatile int32_t*>(b+0x7CC);
 s.c404=*reinterpret_cast<volatile uint32_t*>(c+0x404);s.c408=*reinterpret_cast<volatile uint32_t*>(c+0x408);s.c5a0=*reinterpret_cast<volatile uint32_t*>(c+0x5A0);return s;}
static bool P88ActorFromCtrl(void* ctrl,void*&actor,uint32_t&side,uint32_t&cid){if(!ctrl)return false;actor=reinterpret_cast<uint8_t*>(ctrl)-0x228;return ReadActorIdentity(actor,side,cid);}
static void P88LogSnap(const char*tag,void*actor,uint32_t side,uint32_t cid,const P88Snap&a,const P88Snap&z,unsigned long r,unsigned arg=0){
 Logging.Log("[NSC:P88A] %s actor=%p side=%u char=%u arg=%u ret=%lu bda4=%d->%d bdc8=%d->%d e94=%d->%d e98=%d->%d e9c=%d->%d s116f4=%d->%d s133e0=%d->%d s133e4=%d->%d f7cc=%d c404=%08x c408=%08x c5a0=%08x",tag,actor,side,cid,arg,r,a.bda4,z.bda4,a.bdc8,z.bdc8,a.e94,z.e94,a.e98,z.e98,a.e9c,z.e9c,a.s116f4,z.s116f4,a.s133e0,z.s133e0,a.s133e4,z.s133e4,a.f7cc,a.c404,a.c408,a.c5a0);}
HOOK_DEFINE_TRAMPOLINE(P88ProdHook){static uint64_t Callback(void* actor){uint32_t s=~0u,c=~0u;bool v=ReadActorIdentity(actor,s,c);P88Snap a{};if(v)a=P88Read(actor);auto r=Orig(actor);if(v&&s==0&&g88prod.fetch_add(1)<kP88Limit)P88LogSnap("PROD",actor,s,c,a,P88Read(actor),(unsigned long)r);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88HelperHook){static uint32_t Callback(void* actor){uint32_t s=~0u,c=~0u;bool v=ReadActorIdentity(actor,s,c);P88Snap a{};if(v)a=P88Read(actor);auto r=Orig(actor);if(v&&s==0&&g88help.fetch_add(1)<kP88Limit)P88LogSnap("HELPER_8B30E4",actor,s,c,a,P88Read(actor),r);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88ActorPredHook){static uint32_t Callback(void* actor){uint32_t s=~0u,c=~0u;bool v=ReadActorIdentity(actor,s,c);P88Snap a{};if(v)a=P88Read(actor);auto r=Orig(actor);if(v&&s==0&&g88actor.fetch_add(1)<kP88Limit)P88LogSnap("ACTOR_7E24EC",actor,s,c,a,P88Read(actor),r);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88CtrlModeHook){static uint32_t Callback(void* ctrl){void*a=nullptr;uint32_t s=~0u,c=~0u;bool v=P88ActorFromCtrl(ctrl,a,s,c);P88Snap q{};if(v)q=P88Read(a);auto r=Orig(ctrl);if(v&&s==0&&g88ctrl.fetch_add(1)<kP88Limit)P88LogSnap("CTRL_7C553C",a,s,c,q,P88Read(a),r);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88InputHook){static uint32_t Callback(void* ctrl){void*a=nullptr;uint32_t s=~0u,c=~0u;bool v=P88ActorFromCtrl(ctrl,a,s,c);P88Snap q{};if(v)q=P88Read(a);auto r=Orig(ctrl);if(v&&s==0&&g88input.fetch_add(1)<kP88Limit)P88LogSnap("INPUT_7C6074",a,s,c,q,P88Read(a),r);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88MaskHook){static uint32_t Callback(void* ctrl,uint32_t arg){void*a=nullptr;uint32_t s=~0u,c=~0u;bool v=P88ActorFromCtrl(ctrl,a,s,c);P88Snap q{};if(v)q=P88Read(a);auto r=Orig(ctrl,arg);if(v&&s==0&&g88mask.fetch_add(1)<kP88Limit)P88LogSnap("MASK_7C5FB0",a,s,c,q,P88Read(a),r,arg);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88State2Hook){static uint32_t Callback(void* actor,uint32_t arg){uint32_t s=~0u,c=~0u;bool v=ReadActorIdentity(actor,s,c);P88Snap q{};if(v)q=P88Read(actor);auto r=Orig(actor,arg);if(v&&s==0&&g88state2.fetch_add(1)<kP88Limit)P88LogSnap("STATE2_7D5C10",actor,s,c,q,P88Read(actor),r,arg);return r;}};
HOOK_DEFINE_TRAMPOLINE(P88Gate14Hook){static uint64_t Callback(void* actor,uint32_t arg){uint32_t s=~0u,c=~0u;bool v=ReadActorIdentity(actor,s,c);P88Snap q{};if(v)q=P88Read(actor);auto r=Orig(actor,arg);if(v&&s==0&&g88gate14.fetch_add(1)<kP88Limit)P88LogSnap("GATE_78FDC0",actor,s,c,q,P88Read(actor),(unsigned long)r,arg);return r;}};
static bool InstallP88Internal(){
 static constexpr uint32_t prod[]={0xD10183FF,0xF9000BFE,0xA90267FA,0xA9035FF8};
 static constexpr uint32_t help[]={0xA9BE57FE,0xA9014FF4,0x9108A014,0xAA0003F3};
 static constexpr uint32_t actor[]={0xF81F0FFE,0xF9400008,0xF94C7508,0xD63F0100};
 static constexpr uint32_t ctrl[]={0xB946A800,0xD65F03C0};
 static constexpr uint32_t input[]={0xB945A008,0xB9440409,0x6A08013F,0x1A9F07E0};
 static constexpr uint32_t mask[]={0xB9440808,0x6A01011F,0x1A9F07E0,0xD65F03C0};
 static constexpr uint32_t state2[]={0x5297B688,0xD000CB69,0xD000CB6A,0xB8686808};
 static constexpr uint32_t gate14[]={0xF81C0FFE,0xA9015FF8,0xA90257F6,0xA9034FF4};
 bool ok=true;
 #define P88CHK(n,o,p) do{if(!MatchWords(o,p)){LogFingerprintFail(n,o);ok=false;}}while(0)
 P88CHK("P88_PROD",kP88Prod,prod);P88CHK("P88_HELP",kP88Helper,help);P88CHK("P88_ACTOR",kP88ActorPred,actor);P88CHK("P88_CTRL",kP88CtrlMode,ctrl);P88CHK("P88_INPUT",kP88Input,input);P88CHK("P88_MASK",kP88Mask,mask);P88CHK("P88_STATE2",kP88State2,state2);P88CHK("P88_GATE14",kP88Gate14,gate14);
 #undef P88CHK
 if(!ok)return false;
 P88ProdHook::InstallAtOffset(kP88Prod);P88HelperHook::InstallAtOffset(kP88Helper);P88ActorPredHook::InstallAtOffset(kP88ActorPred);P88CtrlModeHook::InstallAtOffset(kP88CtrlMode);P88InputHook::InstallAtOffset(kP88Input);P88MaskHook::InstallAtOffset(kP88Mask);P88State2Hook::InstallAtOffset(kP88State2);P88Gate14Hook::InstallAtOffset(kP88Gate14);return true;
}
} // anonymous P88

void InstallP88AWideUJAdmissionTrace(){
 InstallP85AF58IntentProbe();
 const bool ok=InstallP88Internal();
 Logging.Log("[NSC:P88A] READY baseline_p85=1 wide=1 probe=%d readonly=1 preserve_orig=1 no_bda4_write=1 no_bdc8_write=1 no_force_return=1 no_force_f58=1 no_force87=1 no_force700=1 no_action445_rewrite=1 no_selector8=1 no_char281_branch=1 limit=%u",ok?1:0,kP88Limit);
}
'''
c=c[:end]+block+c[end:]
needle='void InstallP87AActiveProducerProbe();'
if needle not in h: raise SystemExit('P87 header declaration not found')
h=h.replace(needle,needle+'\nvoid InstallP88AWideUJAdmissionTrace();',1)
old='nsc::InstallP87AActiveProducerProbe();'
if old not in m: raise SystemExit('P87 main install call not found')
m=m.replace(old,'nsc::InstallP88AWideUJAdmissionTrace();',1)
cp.write_text(c);hp.write_text(h);mp.write_text(m);print('P88A_SOURCE_PATCH=PASS')
