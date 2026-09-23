from pathlib import Path
import hashlib, sys
root=Path(sys.argv[1])
paths={
 'main':root/'atmosphere/contents/0100FA10190A0000/exefs/main',
 'subsdk9':root/'atmosphere/contents/0100FA10190A0000/exefs/subsdk9',
 'restore':root/'restore/atmosphere/contents/0100FA10190A0000/exefs/main'}
for k,p in paths.items(): assert p.is_file() and p.stat().st_size>10000,(k,p)
assert hashlib.sha256(paths['main'].read_bytes()).hexdigest()=='1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0'
assert hashlib.sha256(paths['restore'].read_bytes()).hexdigest()=='2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9'
assert paths['subsdk9'].read_bytes()[:4]==b'NSO0'
print('P90A_ARTIFACT_VERIFY=PASS')
