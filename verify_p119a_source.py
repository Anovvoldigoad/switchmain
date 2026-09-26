from pathlib import Path
import hashlib,re,struct
root=Path('.')
cpp=(root/'overlay/source/program/nsc_cpk_bridge.cpp').read_text()
main=(root/'overlay/source/program/main.cpp').read_text()
hpp=(root/'overlay/source/program/nsc_cpk_bridge.hpp').read_text()
start=cpp.find('// P118B — exact event cursor / table identity census')
assert start>=0
block=cpp[start:]

def chk(n,v):
    print(n,'PASS' if v else 'FAIL'); assert v,n

checks={
 'entrypoint':'nsc::InstallP119AUjDamageProvenanceProbe();' in main,
 'decl':'void InstallP119AUjDamageProvenanceProbe();' in hpp,
 'ready':'[NSC:P119A] READY' in cpp,
 'link':'[NSC:P119A] LINK' in cpp,
 'damage':'[NSC:P119A] DAMAGE' in cpp,
 'snapshot_publish':'P119PublishAttackerSnapshot(actor, side, cid, semantic, st);' in cpp,
 'snapshot_read':'P119ReadAttackerSnapshot(atk)' in cpp,
 'generic_side0':'if (!actor || side != 0u) return;' in cpp,
 'uj_corridor':'st.action >= 700u && st.action <= 740u' in cpp,
 'opposite_side_pair':'side != atk.side' in cpp,
 'trace_gap_guard':'trace_gap <= 16u' in cpp,
 'gate10':'((raw_type & ~1u) == 10u)' in cpp,
 'cursor_name':'current_name' in cpp,
 'reuse_p118b_install':'const bool ok = InstallP118BEventTableIdentityInternal();' in cpp,
 'one_p118_trampoline':cpp.count('HOOK_DEFINE_TRAMPOLINE(P118')==1,
 'no_p119_trampoline':'HOOK_DEFINE_TRAMPOLINE(P119' not in cpp,
 'no_p119_inline':'HOOK_DEFINE_INLINE(P119' not in cpp,
 'parent_p96':'InstallP96AActionDescriptorTransitionTrace();' in cpp,
 'victim_shadow_preserved':'VIS_SHADOW' in cpp and 'CTRL14_SHADOW' in cpp,
}
for k,v in checks.items(): chk(k,v)

# No direct writes to actor/event memory in the P119 additions. Diagnostic atomic .store calls are allowed.
p119a=cpp[cpp.find('// P119A: final read-only UJ damage provenance correlation.'):cpp.find('P93CoreState ReadP93CoreState')]+cpp[cpp.find('// P119A final provenance correlation:'):cpp.find('// Historical P118B neighborhood dump retained')]+cpp[cpp.find('void InstallP119AUjDamageProvenanceProbe()'):cpp.find('} // namespace nsc',cpp.find('void InstallP119AUjDamageProvenanceProbe()'))]
code_no_comments=re.sub(r'//.*?$|/\*.*?\*/|"(?:\\.|[^"\\])*"','',p119a,flags=re.M|re.S)
chk('no_direct_pointer_write',not re.search(r'\*reinterpret_cast<[^>]+>\([^\n;]*\)\s*=',code_no_comments))
chk('no_force710',not re.search(r'Orig\s*\([^\n]*710|return\s+710',code_no_comments))
chk('no_force708',not re.search(r'Orig\s*\([^\n]*708|return\s+708',code_no_comments))
chk('no_char281_branch',not re.search(r'(?:char_id|cid|e54)\s*==\s*281|281\s*==\s*(?:char_id|cid|e54)',code_no_comments))

# Conservative logger bounds (<512 bytes) for P119 LINK/DAMAGE/READY.
def log_bound(tag,max_s=0):
    calls=[x for x in re.findall(r'Logging\.Log\((.*?)\);',cpp,re.S) if tag in x]
    assert calls,tag
    x=calls[-1]
    lits=re.findall(r'"((?:\\.|[^"\\])*)"',x)
    f=''.join(bytes(z,'utf8').decode('unicode_escape') for z in lits)
    total=0; last=0
    for m in re.finditer(r'%(?:0?8)?(?:l)?[duxps]',f):
        total+=len(f[last:m.start()]); sp=m.group(0)
        if sp in ('%u','%d'): total+=11
        elif sp=='%08x': total+=8
        elif sp=='%lx': total+=16
        elif sp=='%p': total+=18
        elif sp=='%s': total+=max_s
        last=m.end()
    total+=len(f[last:])
    print('log_bound',tag,total)
    chk(tag.replace('[NSC:P119A] ','').lower()+'_lt_512', total<512)
log_bound('[NSC:P119A] LINK')
log_bound('[NSC:P119A] DAMAGE',63)
log_bound('[NSC:P119A] READY')

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
paired=root/'paired/atmosphere/contents/0100FA10190A0000/exefs/main'
restore=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
print('paired main',sha(paired)); assert sha(paired)=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
print('restore main',sha(restore)); assert sha(restore)=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'

b=paired.read_bytes(); assert b[:4]==b'NSO0'
flags=struct.unpack_from('<I',b,0x0C)[0]
tf,tm,ts=struct.unpack_from('<III',b,0x10); assert (flags&1)==0
text=b[tf:tf+ts]
def word(off): return struct.unpack_from('<I',text,off)[0]
def bl_target(off):
    w=word(off); assert (w>>26)==0b100101
    imm=w&0x03ffffff
    if imm&0x02000000: imm-=0x04000000
    return off+(imm<<2)
for off,w in {
 0x3F4B00:0x13003C08,0x3F4B60:0x13003C08,0x3F4BC0:0xF000EA68,
 0x77B584:0x52973C88,0x77B588:0xAA0003F3,0x77B58C:0x78686800,
 0x77B590:0x97F1E55C,0x77B5A8:0x97F1E586,0x77B5AC:0x6B2022BF,
}.items():
    g=word(off); print(f'fp {off:#x}',f'{g:08x}','PASS' if g==w else 'FAIL'); assert g==w
print('bl 77b590 ->',hex(bl_target(0x77B590))); assert bl_target(0x77B590)==0x3F4B00
print('bl 77b5a8 ->',hex(bl_target(0x77B5A8))); assert bl_target(0x77B5A8)==0x3F4BC0

push=[]
for p in sorted((root/'.github/workflows').glob('*.yml')):
    ss=p.read_text()
    if re.search(r'^\s{2}push:\s*$',ss,re.M): push.append(p.name)
print('push_enabled_workflows',push); assert push==['build-subsdk9-p119a.yml']
print('P119A_DROPIN_SOURCE_VERIFY=PASS')
