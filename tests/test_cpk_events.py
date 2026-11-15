"""CPK marker integration: preserve metadata and every nonselected byte."""
import argparse,hashlib,json,struct,sys,tempfile,subprocess
from pathlib import Path
from test_prm_marker import fixture,event
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from portlib.cpk_events import mark,entries
from portlib.prm_events import records,MARKER


def utf(columns,rows):
    strings=bytearray(b'Table\0');offsets={'Table':0}
    def name(s):
        if s not in offsets:offsets[s]=len(strings);strings.extend(s.encode()+b'\0')
        return offsets[s]
    descriptors=bytearray();packed=bytearray()
    widths={4:4,6:8,10:4}
    for key,typ in columns:descriptors+=bytes([0x50|typ])+struct.pack('>I',name(key))
    stride=sum(widths[t] for _,t in columns)
    for row in rows:
        for key,typ in columns:
            value=name(row[key]) if typ==10 else row[key]
            packed+=value.to_bytes(widths[typ],'big')
    rowoff=32+len(descriptors);stroff=rowoff+len(packed);dataoff=stroff+len(strings)
    header=struct.pack('>4sIIII IHHI',b'@UTF',dataoff-8,rowoff-8,stroff-8,dataoff-8,0,len(columns),stride,len(rows))
    return header+descriptors+packed+strings


def cpk(payloads,mutator=None,header_change=None):
    toc_at=512;content=2048;offset=content-toc_at;rows=[];data=bytearray(content)
    for i,(path,payload) in enumerate(payloads):
        directory,filename=path.rsplit('/',1)
        rows.append({'DirName':directory,'FileName':filename,'FileSize':len(payload),
                     'ExtractSize':len(payload),'FileOffset':offset,'ID':31-i})
        data+=payload;offset+=len(payload)
        padding=(-len(data))%16;data+=bytes([0x71])*padding;offset+=padding
    if mutator:mutator(rows)
    h={'TocOffset':toc_at,'ContentOffset':content,'Files':len(rows),'EnableFileCrc':0}
    if header_change:h.update(header_change)
    header=utf([(k,6 if k.endswith('Offset') else 4) for k in h],[h])
    toc=utf([('DirName',10),('FileName',10),('FileSize',4),('ExtractSize',4),('FileOffset',6),('ID',4)],rows)
    assert len(header)+16<=toc_at and toc_at+16+len(toc)<=content
    def write(at,magic,table):data[at:at+16+len(table)]=magic+struct.pack('<IQ',255,len(table))+table
    write(0,b'CPK ',header);write(toc_at,b'TOC ',toc)
    return bytes(data)


def run(out,real_cpk=None):
    prm=fixture([event(14),event(15),event(0),event(26,b'S_PL_DMG_test')])
    # Names are intentionally unsorted and IDs nonsequential. Conversion must
    # preserve existing mappings rather than rebuilding them by row order.
    payloads=[('data/spc/zprm.bin.xfbin',prm),('data/spc/untouched.bin.xfbin',prm),
              ('data/other/opaque',bytes(range(256))),('data/spc/aprm.bin.xfbin',prm)]
    raw=cpk(payloads);paths=[payloads[0][0],payloads[3][0]]
    result,report=mark(raw,paths);table=entries(raw)
    assert len(raw)==len(result) and entries(result)==table
    expected=set()
    for path in paths:
        off=table[path]['offset']
        expected.update(off+r['offset']+n for r in records(prm) if r['event']==236 and struct.unpack_from('<h',prm,r['offset']+36)[0] in (14,15,26) for n in [42,43])
    assert {i for i,(a,b) in enumerate(zip(raw,result)) if a!=b}==expected
    assert mark(result,paths)[0]==result
    for row in report['selected_prms']:
        assert row['marked_records']==3 and row['native_event236_preserved']==1
    bads=[b'',raw[:100],raw[:-20]]
    for field,value in [('FileOffset',0),('FileOffset',2**63),('FileSize',2**32-1),('ExtractSize',1)]:
        bads.append(cpk(payloads,lambda rows,k=field,v=value:rows[0].update({k:v})))
    bads.extend([
        cpk(payloads,lambda rows:rows[1].update({'ID':rows[0]['ID']})),
        cpk(payloads,lambda rows:rows[1].update({'FileName':rows[0]['FileName']})),
        cpk(payloads,lambda rows:rows[1].update({'FileName':rows[0]['FileName'].upper()})),
        cpk(payloads,lambda rows:rows[1].update({'FileOffset':rows[0]['FileOffset']})),
        cpk(payloads,lambda rows:rows[0].update({'DirName':'../data'})),
        cpk(payloads,header_change={'EnableFileCrc':1}),
        cpk(payloads,header_change={'Files':4+1}),
        cpk(payloads,header_change={'ContentOffset':2}),
        cpk([(payloads[0][0],b'CRILAYLA'+prm[8:])]+payloads[1:]),
    ])
    for key in ('EnableTocCrc','CrcMode','CrcTable','TocCrc','ItocCrc',
                'ItocOffset','GtocOffset','HtocOffset','HgtocOffset','EtocOffset'):
        bads.append(cpk(payloads,header_change={key:1}))
    for off,fmt,value in [(8,'<Q',2**63),(512+8,'<Q',2**63),
                          (512+16+12,'>I',2**32-1),(512+16+28,'>I',2**32-1)]:
        bad=bytearray(raw);struct.pack_into(fmt,bad,off,value);bads.append(bytes(bad))
    rejected=0
    for bad in bads:
        try:mark(bad,paths)
        except (ValueError,UnicodeDecodeError):rejected+=1
        else:raise AssertionError('Invalid archive accepted')
    for bad_paths in [[],[paths[0],paths[0]],['data/spc/missing'],['../'+paths[0]],['/'+paths[0]]]:
        try:mark(raw,bad_paths)
        except ValueError:rejected+=1
        else:raise AssertionError('Invalid selected path accepted')
    # The command must validate BEFORE creating any output. A valid first PRM
    # followed by a malformed second PRM cannot leave a partly converted CPK.
    with tempfile.TemporaryDirectory() as td:
        td=Path(td);p=td/'input.cpk';p.write_bytes(raw);dest=td/'out'
        cmd=[sys.executable,str(R/'tools/mark_cpk_events.py'),'--cpk',str(p),
             '--expected-sha256',hashlib.sha256(raw).hexdigest(),'--output',str(dest)]
        for path in paths:cmd+=['--pc-api-prm',path]
        subprocess.run(cmd,check=True,capture_output=True)
        assert (dest/p.name).read_bytes()==result and p.read_bytes()==raw
        wrong=cmd.copy();wrong[wrong.index('--expected-sha256')+1]='0'*64
        wrong[wrong.index('--output')+1]=str(td/'wrong')
        assert subprocess.run(wrong,capture_output=True).returncode!=0 and not (td/'wrong').exists()
        malformed=cpk(payloads[:3]+[(paths[1],b'INVALID')]);p.write_bytes(malformed)
        wrong[wrong.index('--expected-sha256')+1]=hashlib.sha256(malformed).hexdigest()
        assert subprocess.run(wrong,capture_output=True).returncode!=0 and not (td/'wrong').exists()
    result_report={'status':'PASS','synthetic_prms_marked':2,'exact_changed_bytes':len(expected),
      'malformed_inputs_rejected':rejected,'idempotent':True,'input_preserved':True,
      'validation_precedes_output_creation':True,'metadata_ids_offsets_padding_preserved':True,
      'unsupported_compression_crc_and_auxiliary_tables_rejected':True,
      'gameplay_verified':False,'full_moddingapi':False}
    out.mkdir(parents=True,exist_ok=True)
    (out/'cpk_events.json').write_text(json.dumps(result_report,indent=2)+'\n')
    if real_cpk:
        data=real_cpk.read_bytes();converted,real=mark(data,['data/spc/mtobprm.bin.xfbin'])
        selected=real['selected_prms'][0]
        assert selected['marked_records']==561 and selected['native_event236_preserved']==5
        assert selected['function_records']==4876
        assert sum(a!=b for a,b in zip(data,converted))==1122
        assert mark(converted,['data/spc/mtobprm.bin.xfbin'])[0]==converted
        real.update({'status':'PASS','exact_changed_bytes':1122,'idempotent':True})
        (out/'cpk_events_real_tobi.json').write_text(json.dumps(real,indent=2)+'\n')
    print('CPK event conversion PASS:',rejected,'invalid inputs rejected; exact byte preservation verified')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--real-cpk',type=Path)
    a=p.parse_args();run(a.output,a.real_cpk)
