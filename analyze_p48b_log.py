#!/usr/bin/env python3
import re, sys
from collections import Counter, defaultdict

PATTERNS = {
    'play': re.compile(r'PLAY_ACTION actor=(0x[0-9a-fA-F]+|\(nil\)) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) ret=(-?\d+) n=(\d+).*?pre4712=(\d+).*?post4712=(\d+)'),
    'lookup': re.compile(r'ACTION_LOOKUP actor=(0x[0-9a-fA-F]+|\(nil\)) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) flag=(-?\d+) result=(0x[0-9a-fA-F]+|\(nil\)|0x0) n=(\d+) pre_action=(\d+) post_action=(\d+)'),
    'gate': re.compile(r'ACTION_GATE actor=(0x[0-9a-fA-F]+|\(nil\)) valid=(\d+) side=(\d+) char=(\d+) ret=(\d+) n=(\d+) pre_action=(\d+) post_action=(\d+)'),
    'remap': re.compile(r'ACTION_REMAP actor=(0x[0-9a-fA-F]+|\(nil\)) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) resolved=(-?\d+) n=(\d+) action=(\d+)'),
}

def nonnull(x):
    return x not in ('(nil)','0x0','0')

def main(path):
    lines=open(path,errors='replace').read().splitlines()
    counts=Counter(); bychar=defaultdict(lambda: Counter())
    lookup_rows=[]; gate_rows=[]; play_rows=[]; remap_rows=[]
    for line in lines:
        if '[NSC:P48B]' not in line: continue
        for kind,rx in PATTERNS.items():
            m=rx.search(line)
            if not m: continue
            counts[kind]+=1
            if kind=='play':
                actor,valid,side,ch,idx,ret,n,pre,post=m.groups(); ch=int(ch); idx=int(idx); ret=int(ret); pre=int(pre); post=int(post)
                bychar[ch][f'play:{idx}:ret={ret}']+=1; play_rows.append((ch,idx,ret,pre,post,actor))
            elif kind=='lookup':
                actor,valid,side,ch,idx,flag,res,n,pre,post=m.groups(); ch=int(ch); idx=int(idx); pre=int(pre); post=int(post)
                ok=nonnull(res); bychar[ch][f'lookup:{idx}:found={int(ok)}']+=1; lookup_rows.append((ch,idx,int(flag),ok,res,pre,post,actor))
            elif kind=='gate':
                actor,valid,side,ch,ret,n,pre,post=m.groups(); ch=int(ch); ret=int(ret); pre=int(pre); post=int(post)
                bychar[ch][f'gate:action={pre}:ret={ret}']+=1; gate_rows.append((ch,ret,pre,post,actor))
            else:
                actor,valid,side,ch,idx,resolved,n,action=m.groups(); ch=int(ch); idx=int(idx); resolved=int(resolved); action=int(action)
                bychar[ch][f'remap:{idx}->{resolved}']+=1; remap_rows.append((ch,idx,resolved,action,actor))
            break

    print('=== P48B parsed records ===')
    for k in ('play','lookup','gate','remap'): print(f'{k:8s}: {counts[k]}')
    print('\n=== cinematic decision summary by char ===')
    chars=sorted(c for c in bychar if c < 0x1000)
    for ch in chars:
        relevant={k:v for k,v in bychar[ch].items() if any(t in k for t in ('707','708','709','710'))}
        if not relevant: continue
        print(f'char={ch}')
        for k,v in sorted(relevant.items()): print(f'  {k}: {v}')

    print('\n=== decisive 707/708 chain ===')
    for ch in chars:
        l708=[r for r in lookup_rows if r[0]==ch and r[1]==708]
        g707=[r for r in gate_rows if r[0]==ch and r[2]==707]
        p707=[r for r in play_rows if r[0]==ch and r[1]==707]
        p708=[r for r in play_rows if r[0]==ch and r[1]==708]
        p710=[r for r in play_rows if r[0]==ch and r[1]==710]
        if not (l708 or g707 or p707 or p708 or p710): continue
        print(f'char={ch}: play707={len(p707)} lookup708={len(l708)} '
              f'lookup708_found={sum(r[3] for r in l708)} gate707_ret1={sum(r[1]!=0 for r in g707)} '
              f'play708={len(p708)} play710={len(p710)}')
        for r in l708[:8]:
            print(f'  lookup708 flag={r[2]} found={int(r[3])} result={r[4]} pre={r[5]} post={r[6]} actor={r[7]}')

    print('\nInterpretation target: if the modded char shows lookup(708) FOUND while a working vanilla control shows NULL/0, and both pass the 707 gate, the divergence is action-availability/resolution rather than PlayAction(707) return.')

if __name__=='__main__':
    if len(sys.argv)!=2:
        raise SystemExit(f'usage: {sys.argv[0]} <nxlink-log.txt>')
    main(sys.argv[1])
