#!/usr/bin/env python3
from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'artifact')
sub=root/'atmosphere/contents/0100FA10190A0000/exefs/subsdk9'
main=root/'atmosphere/contents/0100FA10190A0000/exefs/main'
rest=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
for path in (sub,main,rest):
    if not path.is_file(): raise SystemExit(f'MISSING {path}')
    if path.read_bytes()[:4] != b'NSO0': raise SystemExit(f'NSO0_FAIL {path}')
print('subsdk9_NSO0=PASS size=',sub.stat().st_size)
for path,want in [(main,'1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),(rest,'2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
    got=hashlib.sha256(path.read_bytes()).hexdigest(); print(path,got); assert got==want
for marker in (b'[NSC:P99A] READY',b'[NSC:P99A] GATE1278',b'[NSC:P99A] TOPO',b'[NSC:P96A] READY',b'[NSC:P89A] READY'):
    if marker not in sub.read_bytes(): raise SystemExit(f'MARKER_MISSING {marker!r}')
print('P99A_ARTIFACT_VERIFY=PASS')
