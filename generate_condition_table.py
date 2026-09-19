#!/usr/bin/env python3
from pathlib import Path
import json, sys
root=Path(__file__).resolve().parent
src=Path(sys.argv[1]) if len(sys.argv)>1 else root/'condition_compat_manifest.json'
out=Path(sys.argv[2]) if len(sys.argv)>2 else root/'overlay/source/program/condition_compat_generated.hpp'
m=json.loads(src.read_text())
if m.get('format')!='NSC2SwitchConditionCompatManifestV1': raise SystemExit('bad manifest format')
native=int(m['native_condition_count']); entries=m['entries']
if native<1 or native>4095: raise SystemExit('native count out of range')
if not entries: raise SystemExit('no extra conditions')
if native+len(entries)>4095: raise SystemExit('total count exceeds immediate patch range')
names=set()
for i,e in enumerate(entries):
    name=e['name']
    if not name or '\x00' in name or name in names: raise SystemExit(f'bad/duplicate name at {i}')
    name.encode('ascii'); names.add(name)
    for k in ('field08','field0C','field10','field14','field18','field1C'):
        v=int(e[k]);
        if not 0<=v<=0xffffffff: raise SystemExit(f'{k} out of range at {i}')
lines=[]
lines += ['#pragma once','#include <cstddef>','#include <cstdint>','', 'namespace nsc::condition_compat_generated {','']
lines += ['struct ConditionDescriptor {','    const char* name;','    uint32_t field08;','    uint32_t field0C;','    uint32_t field10;','    uint32_t field14;','    uint32_t field18;','    uint32_t field1C;','};','static_assert(sizeof(ConditionDescriptor) == 0x20);','']
for i,e in enumerate(entries):
    esc=e['name'].replace('\\','\\\\').replace('"','\\"')
    lines.append(f'static constexpr char kName{i}[] = "{esc}";')
lines += ['',f'static constexpr uint32_t kNativeConditionCount = {native}u;',f'static constexpr uint32_t kExtraConditionCount = {len(entries)}u;', 'static constexpr uint32_t kTotalConditionCount = kNativeConditionCount + kExtraConditionCount;','']
lines.append('static const ConditionDescriptor kExtraConditions[kExtraConditionCount] = {')
for i,e in enumerate(entries):
    vals=', '.join(f'0x{int(e[k]):X}u' for k in ('field08','field0C','field10','field14','field18','field1C'))
    lines.append(f'    {{kName{i}, {vals}}},')
lines += ['};','','} // namespace nsc::condition_compat_generated','']
out.parent.mkdir(parents=True,exist_ok=True); out.write_text('\n'.join(lines))
print(f'generated {out} native={native} extra={len(entries)} total={native+len(entries)}')
