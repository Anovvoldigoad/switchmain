"""Bounds-checked PRM ver0.000 event marking. No character-ID heuristic."""
import hashlib
import struct
MARKER = 0x4E53


def binary_chunks(data):
    if len(data) < 68 or data[:4] != b'NUCC':
        raise ValueError('Expected plaintext NUCC XFBIN')
    tc,ts,pc,ps,nc,ns,mc,ms,ic,rc = struct.unpack_from('>10I',data,28)
    pos,tables=68,[]
    for count,size in [(tc,ts),(pc,ps),(nc,ns)]:
        if pos+size > len(data) or count > size:
            raise ValueError('NUCC string table bounds')
        raw=data[pos:pos+size];pos+=size
        if count==0:
            if size:raise ValueError('Unexpected empty string table')
            tables.append([]);continue
        if not raw.endswith(b'\0'):raise ValueError('Unterminated NUCC strings')
        strings=raw[:-1].split(b'\0')
        if len(strings)!=count:raise ValueError('NUCC string count mismatch')
        tables.append(strings)
    pos=(pos+3)&~3
    if ms!=mc*12 or pos+ms+rc*8+ic*4>len(data):
        raise ValueError('NUCC map/index bounds')
    maps=[]
    for _ in range(mc):
        ids=struct.unpack_from('>3I',data,pos);pos+=12
        if any(ids[j]>=len(tables[j]) for j in range(3)):
            raise ValueError('NUCC string index out of bounds')
        maps.append(tuple(tables[j][ids[j]] for j in range(3)))
    pos+=rc*8
    indices=struct.unpack_from('>'+str(ic)+'I',data,pos);pos+=ic*4
    if any(i>=mc for i in indices):raise ValueError('NUCC map index out of bounds')
    base,used_refs=0,0;chunks=[];last=None
    while pos<len(data):
        if pos+12>len(data):raise ValueError('Truncated NUCC chunk')
        size,index,version,unknown=struct.unpack_from('>IIHH',data,pos)
        if pos+12+size>len(data) or base+index>=ic:
            raise ValueError('NUCC chunk data/index out of bounds')
        kind,path,name=maps[indices[base+index]];start=pos+12;last=kind
        if kind==b'nuccChunkBinary':
            if size<4 or struct.unpack_from('>I',data,start)[0]!=size-4:
                raise ValueError('Binary payload length mismatch')
            chunks.append((name.decode('ascii'),start,size))
        elif kind==b'nuccChunkPage':
            if size<8:raise ValueError('Short NUCC page')
            advance,refs=struct.unpack_from('>II',data,start)
            base+=advance;used_refs+=refs
            if base>ic or used_refs>rc:raise ValueError('NUCC page totals exceed tables')
        pos+=12+size
    if last!=b'nuccChunkPage' or base!=ic or used_refs!=rc:
        raise ValueError('Incomplete NUCC pages')
    return chunks


def has_damage(event, following):
    # Native 1.70 reader 0x81d15c..0x81d29c and predicate 0x7938d0.
    # It is NOT safe to guess every record size by scanning for PL_ANM text.
    forced=event==94 or (193<=event<=217 and (0x015502A5>>(event-193))&1)
    return bool(forced or event in (138,139) or
                (event==131 and following.startswith(b'SPSKILL_END')) or
                (160<=event<=166 and following.startswith(b'SKL_ATK')))


def records(data):
    result=[];animation_chunks=0
    for name,start,size in binary_chunks(data):
        payload=data[start:start+size]
        if not payload[4:].startswith(b'ver'):continue
        if size<68 or payload[4:52].split(b'\0',1)[0]!=b'ver0.000':
            raise ValueError(f'{name}: unsupported PRM version')
        animation_chunks+=1
        count=struct.unpack_from('<I',payload,52)[0];pos=68
        if count>(size-pos)//212:raise ValueError(f'{name}: animation count out of bounds')
        for animation_index in range(count):
            if pos+212>size:raise ValueError(f'{name}: truncated animation')
            name_bytes=payload[pos:pos+32]
            if b'\0' not in name_bytes:raise ValueError(f'{name}: unterminated animation name')
            animation=name_bytes.split(b'\0',1)[0].decode('ascii')
            functions=struct.unpack_from('<I',payload,pos+80)[0];pos+=212
            if functions>(size-pos)//64:raise ValueError(f'{name}: function count out of bounds')
            for function_index in range(functions):
                if pos+64>size:raise ValueError(f'{name}: truncated event')
                event=struct.unpack_from('<H',payload,pos+34)[0]
                width=160 if has_damage(event,payload[pos+64:pos+76]) else 64
                if pos+width>size:raise ValueError(f'{name}: truncated damage event')
                result.append({'chunk':name,'animation':animation,'function':function_index,
                               'offset':start+pos,'size':width,'event':event})
                pos+=width
        if pos!=size:raise ValueError(f'{name}: unconsumed PRM bytes ({size-pos})')
    if not animation_chunks:raise ValueError('No supported PRM animation chunks')
    return result


def mark(data):
    rows=records(data);result=bytearray(data);changed=[];already=0;native236=0
    for row in rows:
        if row['event']!=236:continue
        off=row['offset'];op=struct.unpack_from('<h',data,off+36)[0]
        marker=struct.unpack_from('<H',data,off+42)[0]
        if not 1<=op<=29:
            if marker==MARKER:raise ValueError('Marked event has invalid ModdingAPI operation')
            native236+=1;continue
        if marker not in (0,MARKER):
            raise ValueError(f'{row["chunk"]}:{off}: API marker field already occupied')
        if marker==MARKER:already+=1;continue
        struct.pack_into('<H',result,off+42,MARKER)
        changed.append({**row,'opcode':op})
    expected={r['offset']+n for r in changed for n in [42,43]}
    actual={i for i,(a,b) in enumerate(zip(data,result)) if a!=b}
    if actual!=expected:raise ValueError('Unexpected PRM changes')
    return bytes(result),{'source_sha256':hashlib.sha256(data).hexdigest(),
                          'output_sha256':hashlib.sha256(result).hexdigest(),
                          'function_records':len(rows),'marked_records':len(changed),
                          'already_marked':already,'native_event236_preserved':native236,
                          'changes':changed,'gameplay_verified':False,'full_moddingapi':False}
