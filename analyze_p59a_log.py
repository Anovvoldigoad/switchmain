#!/usr/bin/env python3
import collections,re,sys
from pathlib import Path

if len(sys.argv) != 2:
    raise SystemExit('usage: analyze_p59a_log.py uzuy_log.txt')
text = Path(sys.argv[1]).read_text(errors='replace')

def u32hex(s):
    return int(s, 16) & 0xFFFFFFFF

def call_kind(word):
    w = word & 0xFFFFFFFF
    if (w & 0xFC000000) == 0x94000000:
        return 'BL'
    if (w & 0xFFFFFC1F) == 0xD63F0000:
        return 'BLR'
    if (w & 0xFC000000) == 0x14000000:
        return 'B'
    if (w & 0xFFFFFC1F) == 0xD61F0000:
        return 'BR'
    return 'OTHER'

def decode_bl_target(callsite, word):
    if call_kind(word) != 'BL':
        return None
    imm26 = word & 0x03FFFFFF
    if imm26 & (1 << 25):
        imm26 -= 1 << 26
    return (callsite + (imm26 << 2)) & 0xFFFFFFFFFFFFFFFF

ready = '[NSC:P59A] READY' in text

mode_re = re.compile(
    r'\[NSC:P59A\] MODE_BASE n=(\d+) actor=(\S+) valid=(\d+) side=(\d+) char=(\d+) mode=(\d+) '
    r'caller_lr=(\S+) caller_main=(\d+) caller_off=0x([0-9a-fA-F]+) callsite_off=0x([0-9a-fA-F]+) '
    r'call_m8=([0-9a-fA-F]{8}) call_m4=([0-9a-fA-F]{8}) vtable=(\S+) slot_e40=(\S+) '
    r'slot_main=(\d+) slot_off=0x([0-9a-fA-F]+) slot_word0=([0-9a-fA-F]{8}) base_impl=(\d+) '
    r'action=(\d+)->(\d+) e60=(-?\d+)->(-?\d+) e94=(-?\d+)->(-?\d+) e9c=(-?\d+)->(-?\d+) '
    r'ea0=(-?\d+)->(-?\d+) skills=(\d+)/(\d+)/(\d+)->(\d+)/(\d+)/(\d+)'
)
mode_rows=[]
for m in mode_re.finditer(text):
    g=m.groups()
    row={
        'n':int(g[0]), 'actor':g[1], 'valid':int(g[2]), 'side':int(g[3]), 'char':int(g[4]),
        'mode':int(g[5]), 'lr':g[6], 'caller_main':int(g[7]), 'caller':int(g[8],16),
        'callsite':int(g[9],16), 'm8':u32hex(g[10]), 'm4':u32hex(g[11]), 'vtable':g[12],
        'slot':g[13], 'slot_main':int(g[14]), 'slot_off':int(g[15],16), 'slot_word0':u32hex(g[16]),
        'base_impl':int(g[17]), 'action_pre':int(g[18]), 'action_post':int(g[19]),
        'e60_pre':int(g[20]), 'e60_post':int(g[21]), 'e94_pre':int(g[22]), 'e94_post':int(g[23]),
        'e9c_pre':int(g[24]), 'e9c_post':int(g[25]), 'ea0_pre':int(g[26]), 'ea0_post':int(g[27]),
        'skills_pre':tuple(map(int,g[28:31])), 'skills_post':tuple(map(int,g[31:34])),
    }
    row['call_kind']=call_kind(row['m4'])
    row['bl_target']=decode_bl_target(row['callsite'], row['m4']) if row['caller_main'] else None
    mode_rows.append(row)

play_re = re.compile(
    r'\[NSC:P59A\] PLAY_CALL n=(\d+) actor=(\S+) valid=(\d+) side=(\d+) char=(\d+) index=(-?\d+) '
    r'a2=(-?\d+) a3=(-?\d+) a4=(-?\d+) a5=(-?\d+) pre=(\d+) post=(\d+) ret=(-?\d+) '
    r'caller_lr=(\S+) caller_main=(\d+) caller_off=0x([0-9a-fA-F]+) callsite_off=0x([0-9a-fA-F]+) '
    r'call_m8=([0-9a-fA-F]{8}) call_m4=([0-9a-fA-F]{8}) setter=(\S+) setter_off=0x([0-9a-fA-F]+)'
)
play_rows=[]
for m in play_re.finditer(text):
    g=m.groups()
    play_rows.append({
        'n':int(g[0]), 'actor':g[1], 'valid':int(g[2]), 'side':int(g[3]), 'char':int(g[4]),
        'index':int(g[5]), 'a2':int(g[6]), 'a3':int(g[7]), 'a4':int(g[8]), 'a5':int(g[9]),
        'pre':int(g[10]), 'post':int(g[11]), 'ret':int(g[12]), 'caller_main':int(g[14]),
        'caller':int(g[15],16), 'callsite':int(g[16],16), 'm8':u32hex(g[17]), 'm4':u32hex(g[18]),
        'setter':g[19], 'setter_off':int(g[20],16),
    })

print('P59A_READY=' + ('PASS' if ready else 'FAIL'))
print('MODE_ROWS=' + str(len(mode_rows)))
print('PLAY_ROWS=' + str(len(play_rows)))
print('MODE_BY_CHAR=' + repr(dict(collections.Counter(r['char'] for r in mode_rows))))
print('MODE_COUNTS=' + repr(dict(collections.Counter((r['char'],r['mode']) for r in mode_rows))))
print('PLAY_INDEX_COUNTS=' + repr(dict(collections.Counter((r['char'],r['index']) for r in play_rows))))

for r in mode_rows:
    tgt = f'0x{r["bl_target"]:x}' if r['bl_target'] is not None else '-'
    print('MODE n={n} char={char} side={side} mode={mode} action={action_pre}->{action_post} '
          'e94={e94_pre}->{e94_post} caller_main={caller_main} caller_off=0x{caller:x} '
          'callsite=0x{callsite:x} call_kind={call_kind} bl_target={tgt} '
          'slot_main={slot_main} slot_off=0x{slot_off:x} slot_word0={slot_word0:08x} base_impl={base_impl}'.format(tgt=tgt,**r))

# Current fixture ID only for a targeted convenience summary; the build itself is generic.
tobi=[r for r in mode_rows if r['char']==281]
print('TOBI_MODE_ROWS='+str(len(tobi)))
print('TOBI_MODES='+repr(dict(collections.Counter(r['mode'] for r in tobi))))
print('TOBI_SLOT_TARGETS='+repr(dict(collections.Counter(hex(r['slot_off']) for r in tobi if r['slot_main']))))
print('TOBI_CALLERS='+repr(dict(collections.Counter(hex(r['caller']) for r in tobi if r['caller_main']))))

wrong445=[r for r in play_rows if r['char']==281 and r['index']==445]
print('TOBI_PLAY445_ROWS='+str(len(wrong445)))
print('TOBI_PLAY445_CALLSITES='+repr(dict(collections.Counter(hex(r['callsite']) for r in wrong445))))

# High-confidence acceptance signal: at least one custom mode0 row and a 445 PlayAction row.
mode0=[r for r in tobi if r['mode']==0]
if ready and mode0 and wrong445:
    print('P59A_WRONG_ROUTE_CORRELATED=YES')
else:
    print('P59A_WRONG_ROUTE_CORRELATED=NO')

# Never overclaim LR-4 when the saved word is not a call.
if mode0:
    kinds=collections.Counter(r['call_kind'] for r in mode0)
    print('TOBI_MODE0_CALL_KINDS='+repr(dict(kinds)))
    if all(r['call_kind'] in ('BL','BLR') for r in mode0):
        print('P59A_MODE0_CALLER_PROVEN=YES')
    else:
        print('P59A_MODE0_CALLER_PROVEN=PARTIAL_USE_SLOT_TARGET')
else:
    print('P59A_MODE0_CALLER_PROVEN=NO_MODE0_ROW')
