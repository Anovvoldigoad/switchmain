#!/usr/bin/env python3
from pathlib import Path
R=Path.cwd(); cp=R/'overlay/source/program/nsc_cpk_bridge.cpp'; hp=R/'overlay/source/program/nsc_cpk_bridge.hpp'; mp=R/'overlay/source/program/main.cpp'
c=cp.read_text(); h=hp.read_text(); m=mp.read_text()
if '[NSC:P87A]' in c: raise SystemExit('P87A already applied')
if 'void InstallP86ABda4Bdc8ProducerProbe()' not in c: raise SystemExit('requires current P86A source')
anchor='\n} // namespace\n\nvoid InstallP86ABda4Bdc8ProducerProbe()'; pos=c.find(anchor)
if pos<0: raise SystemExit('P86A anonymous namespace anchor not found')
block=r'''

// P87A corrected active producer probe — read only.
static constexpr ptrdiff_t kP87Prod=0x7D3AD0;
static constexpr ptrdiff_t kP87Helper=0x8B30E4;
static constexpr ptrdiff_t kP87ActorPred=0x7E24EC;
static std::atomic<uint32_t> g_p87_prod{0},g_p87_help{0},g_p87_actor{0};

HOOK_DEFINE_TRAMPOLINE(P87ProdHook) {
 static uint64_t Callback(void* actor){
  uint32_t side=0xFFFFFFFFu,cid=0xFFFFFFFFu; const bool valid=ReadActorIdentity(actor,side,cid);
  int32_t a=0x7FFFFFFF,d=0x7FFFFFFF;
  if(valid){auto*b=reinterpret_cast<volatile uint8_t*>(actor);a=*reinterpret_cast<volatile int32_t*>(b+0xBDA4);d=*reinterpret_cast<volatile int32_t*>(b+0xBDC8);}
  const uint64_t r=Orig(actor);
  if(valid&&side==0&&g_p87_prod.fetch_add(1,std::memory_order_relaxed)<4096){auto*b=reinterpret_cast<volatile uint8_t*>(actor);Logging.Log("[NSC:P87A] PROD actor=%p side=%u char=%u bda4=%d->%d bdc8=%d->%d ret=%lx",actor,side,cid,a,*reinterpret_cast<volatile int32_t*>(b+0xBDA4),d,*reinterpret_cast<volatile int32_t*>(b+0xBDC8),static_cast<unsigned long>(r));}
  return r;
 }
};
HOOK_DEFINE_TRAMPOLINE(P87HelperHook) {
 static uint32_t Callback(void* actor){const uint32_t r=Orig(actor);uint32_t s=0xFFFFFFFFu,cid=0xFFFFFFFFu;if(ReadActorIdentity(actor,s,cid)&&s==0&&g_p87_help.fetch_add(1,std::memory_order_relaxed)<4096){auto*b=reinterpret_cast<volatile uint8_t*>(actor);Logging.Log("[NSC:P87A] HELPER actor=%p side=%u char=%u bda4=%d bdc8=%d ret=%u",actor,s,cid,*reinterpret_cast<volatile int32_t*>(b+0xBDA4),*reinterpret_cast<volatile int32_t*>(b+0xBDC8),r);}return r;}
};
HOOK_DEFINE_TRAMPOLINE(P87ActorPredHook) {
 static uint32_t Callback(void* actor){const uint32_t r=Orig(actor);uint32_t s=0xFFFFFFFFu,cid=0xFFFFFFFFu;if(ReadActorIdentity(actor,s,cid)&&s==0&&g_p87_actor.fetch_add(1,std::memory_order_relaxed)<4096){auto*b=reinterpret_cast<volatile uint8_t*>(actor);Logging.Log("[NSC:P87A] ACTOR_PRED actor=%p side=%u char=%u bda4=%d bdc8=%d ret=%u",actor,s,cid,*reinterpret_cast<volatile int32_t*>(b+0xBDA4),*reinterpret_cast<volatile int32_t*>(b+0xBDC8),r);}return r;}
};
bool InstallP87Internal(){
 static constexpr uint32_t p[]={0xD10183FF,0xF9000BFE,0xA90267FA,0xA9035FF8,0xA90457F6,0xA9054FF4,0x52979D08,0x9108A014};
 static constexpr uint32_t h[]={0xA9BE57FE,0xA9014FF4,0x9108A014,0xAA0003F3,0xAA1403E0,0x97FC4911,0x340004A0,0xF9400268};
 static constexpr uint32_t a[]={0xF81F0FFE,0xF9400008,0xF94C7508,0xD63F0100,0x7100041F,0x1A9F17E0,0xF84107FE,0xD65F03C0};
 bool ok=true;if(!MatchWords(kP87Prod,p)){LogFingerprintFail("P87_PROD",kP87Prod);ok=false;}if(!MatchWords(kP87Helper,h)){LogFingerprintFail("P87_HELP",kP87Helper);ok=false;}if(!MatchWords(kP87ActorPred,a)){LogFingerprintFail("P87_ACTOR",kP87ActorPred);ok=false;}if(!ok)return false;
 P87ProdHook::InstallAtOffset(kP87Prod);P87HelperHook::InstallAtOffset(kP87Helper);P87ActorPredHook::InstallAtOffset(kP87ActorPred);return true;
}
'''
c=c[:pos]+block+c[pos:]
end=c.rfind('\n} // namespace nsc')
if end<0: raise SystemExit('namespace nsc end not found')
public=r'''

void InstallP87AActiveProducerProbe(){
 InstallP85AF58IntentProbe();
 const bool ok=InstallP87Internal();
 Logging.Log("[NSC:P87A] READY baseline_p85=1 active_producer=0x7d3ad0 helper=0x8b30e4 actor_pred=0x7e24ec probe=%d readonly=1 preserve_orig=1 no_bda4_write=1 no_bdc8_write=1 no_force_return=1 no_force87=1 no_force700=1 no_action445_rewrite=1 no_selector8=1 no_char281_branch=1",ok?1:0);
}
'''
c=c[:end]+public+c[end:]
needle='void InstallP86ABda4Bdc8ProducerProbe();'
if needle not in h: raise SystemExit('P86 header declaration not found')
h=h.replace(needle,needle+'\nvoid InstallP87AActiveProducerProbe();',1)
old='nsc::InstallP86ABda4Bdc8ProducerProbe();'
if old not in m: raise SystemExit('P86 main install call not found')
m=m.replace(old,'nsc::InstallP87AActiveProducerProbe();',1)
cp.write_text(c);hp.write_text(h);mp.write_text(m);print('P87A_SOURCE_PATCH=PASS')
