#!/usr/bin/env python3
"""Decode the existing R180 reference and reconstruct stock TEXT for tests.
The source NSO is read-only. Outputs are test inputs, never installable main.
"""
import argparse,hashlib,struct
from pathlib import Path
import lz4.block
NSO_SHA='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
STOCK_SHA='f6ec83dad4537b0fa53cf707c10f48a438117905581e2ed3f42cf3cf29a731d7'
def prepare(source,out):
 b=source.read_bytes();assert hashlib.sha256(b).hexdigest()==NSO_SHA
 flags=struct.unpack_from('<I',b,12)[0];off,va,size=struct.unpack_from('<III',b,16)
 packed=struct.unpack_from('<I',b,96)[0];assert va==0 and size==0x12f5fd0
 raw=b[off:off+(packed if flags&1 else size)]
 if flags&1:raw=lz4.block.decompress(raw,uncompressed_size=size)
 assert len(raw)==size and hashlib.sha256(raw).digest()==b[160:192]
 stock=bytearray(raw)
 for at,before,after in [(0x80fb64,0x52802328,0x52808008),(0x80fb78,0x52823200,0x52880000),
                         (0x80fbe4,0xf10466bf,0xf11002bf),(0x876188,0x7104669f,0x71046a9f)]:
  assert struct.unpack_from('<I',stock,at)[0]==after
  struct.pack_into('<I',stock,at,before)
 assert hashlib.sha256(stock).hexdigest()==STOCK_SHA
 out.mkdir(parents=True,exist_ok=True);(out/'r180.text').write_bytes(raw);(out/'stock.text').write_bytes(stock)
 print('Two exact text fixtures verified; source NSO unchanged.')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--r180-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
 a=p.parse_args();prepare(a.r180_main,a.output)
