from pathlib import Path
import hashlib,sys
root=Path(sys.argv[1] if len(sys.argv)>1 else 'artifact')
sub=root/'atmosphere/contents/0100FA10190A0000/exefs/subsdk9'
main=root/'atmosphere/contents/0100FA10190A0000/exefs/main'
rest=root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'
for p in (sub,main,rest):
 if not p.is_file(): raise SystemExit(f'MISSING {p}')
data=sub.read_bytes()
for marker in (b'[NSC:P89A] READY',b'[NSC:P89A] ACTOR_PRED',b'[NSC:P88B] READY'):
 ok=marker in data; print(marker.decode(), 'PASS' if ok else 'FAIL');
 if not ok: sys.exit(1)
if data[:4] != b'NSO0': raise SystemExit('subsdk9 NSO0 FAIL')
print('subsdk9_NSO0=PASS')
for p,w in [(main,'1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'),(rest,'2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9')]:
 g=hashlib.sha256(p.read_bytes()).hexdigest(); print(p,g); assert g==w
print('P89A_ARTIFACT_VERIFY=PASS')
