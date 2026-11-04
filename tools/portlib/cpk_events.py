"""Preserve a CPK byte-for-byte except explicitly selected uncompressed PRMs.

This is an ownership-marker integration step, not a general PC asset converter.
Compressed PRMs and CRC-protected archives require a separate verified repacker.
"""
import hashlib
import struct
from pathlib import PurePosixPath
from .prm_events import mark as mark_prm


def utf(blob):
    if len(blob)<32 or blob[:4]!=b'@UTF':
        raise ValueError('Expected plaintext @UTF table')
    size=struct.unpack_from('>I',blob,4)[0]+8
    version,rowoff=struct.unpack_from('>HH',blob,8)
    stroff,dataoff=struct.unpack_from('>II',blob,12)
    rowoff+=8;stroff+=8;dataoff+=8
    cols,stride,count=struct.unpack_from('>HHI',blob,24)
    if version not in (0,1) or not 32<=rowoff<=stroff<=dataoff<=size<=len(blob):
        raise ValueError('UTF table bounds/version')
    if cols>100 or count>100000 or rowoff+count*stride>stroff:
        raise ValueError('UTF row bounds')
    def string(offset):
        start=stroff+offset
        if not stroff<=start<dataoff:raise ValueError('UTF string offset')
        end=blob.find(b'\0',start,dataoff)
        if end<0:raise ValueError('UTF unterminated string')
        return blob[start:end].decode('utf-8')
    widths={0:1,1:1,2:2,3:2,4:4,5:4,6:8,7:8,10:4,11:8}
    definitions=[];pos=32;names=set()
    for _ in range(cols):
        if pos+5>rowoff:raise ValueError('UTF column descriptor bounds')
        flag=blob[pos];typ=flag&15;storage=flag&240
        if typ not in widths or storage not in (0x10,0x30,0x50):
            raise ValueError('Unsupported UTF column encoding')
        name=string(struct.unpack_from('>I',blob,pos+1)[0]);pos+=5
        if name in names:raise ValueError('Duplicate UTF column')
        names.add(name);constant=None
        if storage==0x30:
            n=widths[typ]
            if pos+n>rowoff:raise ValueError('UTF constant bounds')
            constant=int.from_bytes(blob[pos:pos+n],'big');pos+=n
        definitions.append((name,typ,storage,constant))
    rows=[]
    for i in range(count):
        pos=rowoff+i*stride;end=pos+stride;row={}
        for name,typ,storage,constant in definitions:
            value=constant
            if storage==0x50:
                n=widths[typ]
                if pos+n>end:raise ValueError('UTF field bounds')
                value=int.from_bytes(blob[pos:pos+n],'big');pos+=n
            if typ==10 and value is not None:value=string(value)
            row[name]=value
        if pos!=end:raise ValueError('UTF row stride mismatch')
        rows.append(row)
    return rows


def _number(row,key):
    value=row.get(key)
    if type(value) is not int or value<0:raise ValueError('Missing CPK integer: '+key)
    return value


def canonical(path):
    if not isinstance(path,str) or not path or '\\' in path or '\0' in path:
        raise ValueError('Invalid CPK path')
    p=PurePosixPath(path)
    if p.is_absolute() or str(p)!=path or any(x in ('.','..') for x in p.parts):
        raise ValueError('Noncanonical CPK path: '+path)
    return path


def entries(data):
    def table(at,magic):
        if at<0 or at+16>len(data) or data[at:at+4]!=magic:
            raise ValueError('CPK chunk header')
        size=struct.unpack_from('<Q',data,at+8)[0]
        if not 32<=size<=64*1024*1024 or at+16+size>len(data):
            raise ValueError('CPK table bounds')
        return utf(data[at+16:at+16+size]),(at,at+16+size)
    headers,hspan=table(0,b'CPK ')
    if len(headers)!=1:raise ValueError('Expected one CPK header row')
    h=headers[0]
    # Updating opaque checksum schemes without recomputation is forbidden.
    for key in ('EnableTocCrc','EnableFileCrc','CrcMode','CrcTable','TocCrc','ItocCrc'):
        if h.get(key) not in (None,0):raise ValueError('Unsupported CPK CRC: '+key)
    for key in ('ItocOffset','GtocOffset','HtocOffset','HgtocOffset','EtocOffset'):
        if h.get(key) not in (None,0):raise ValueError('Unsupported auxiliary CPK table: '+key)
    toc=_number(h,'TocOffset');content=_number(h,'ContentOffset')
    if content<16 or content>len(data):raise ValueError('CPK content offset')
    rows,tspan=table(toc,b'TOC ')
    if hspan[1]>toc or tspan[1]>content:raise ValueError('Overlapping CPK metadata')
    if len(rows)!=_number(h,'Files'):raise ValueError('CPK entry count mismatch')
    base=min(toc,content);result={};ids=set();spans=[];case_paths=set()
    for row in rows:
        directory=row.get('DirName') or '';name=row.get('FileName')
        if not isinstance(name,str) or '/' in name or not isinstance(directory,str):
            raise ValueError('CPK filename/directory')
        path=canonical((directory+'/' if directory else '')+name)
        if path.casefold() in case_paths:raise ValueError('Duplicate CPK path')
        case_paths.add(path.casefold())
        start=base+_number(row,'FileOffset');size=_number(row,'FileSize')
        extracted=_number(row,'ExtractSize');entry_id=_number(row,'ID')
        if entry_id in ids:raise ValueError('Duplicate CPK ID')
        ids.add(entry_id)
        if start<content or start+size>len(data):raise ValueError('CPK payload bounds')
        if size:spans.append((start,start+size))
        result[path]={'offset':start,'stored_size':size,'size':extracted,'id':entry_id}
    spans.sort()
    if any(a[1]>b[0] for a,b in zip(spans,spans[1:])):
        raise ValueError('Overlapping CPK payloads')
    return result


def mark(data,paths):
    selected=[canonical(p) for p in paths]
    if not selected or len(set(selected))!=len(selected):
        raise ValueError('Select one or more unique known PC ModdingAPI PRM paths')
    table=entries(data);changes=[];reports=[]
    # Parse all selected inputs before producing any output.
    for path in selected:
        if path not in table:raise ValueError('CPK path absent: '+path)
        entry=table[path];off=entry['offset'];end=off+entry['stored_size']
        if entry['stored_size']!=entry['size'] or data[off:off+8]==b'CRILAYLA':
            raise ValueError('Compressed PRM requires verified repacking: '+path)
        converted,report=mark_prm(data[off:end])
        if len(converted)!=entry['stored_size']:raise ValueError('PRM length changed')
        changes.append((off,end,converted))
        reports.append({'path':path,'id':entry['id'],'archive_offset':off,
                        **{k:v for k,v in report.items() if k!='changes'}})
    result=bytearray(data)
    for off,end,converted in changes:result[off:end]=converted
    # All nonselected bytes, including tables, IDs, offsets and padding, match.
    cursor=0
    for off,end,_ in sorted(changes):
        if result[cursor:off]!=data[cursor:off]:raise ValueError('Unexpected archive change')
        cursor=end
    if result[cursor:]!=data[cursor:]:raise ValueError('Unexpected archive tail change')
    result=bytes(result)
    if entries(result)!=table:raise ValueError('CPK metadata changed')
    return result,{'source_sha256':hashlib.sha256(data).hexdigest(),
                   'output_sha256':hashlib.sha256(result).hexdigest(),
                   'archive_bytes':len(data),'entries':len(table),'selected_prms':reports,
                   'metadata_and_other_payloads_unchanged':True,
                   'gameplay_verified':False,'full_moddingapi':False}
