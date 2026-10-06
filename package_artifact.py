from pathlib import Path
import hashlib, shutil, sys

root = Path(__file__).resolve().parent
exl = root / 'exlaunch'

cands = []
for p in exl.rglob('subsdk9'):
    try:
        if p.is_file() and p.read_bytes()[:4] == b'NSO0':
            cands.append(p)
    except OSError:
        pass

if not cands:
    raise SystemExit('STOP: no NSO0 subsdk9 found under exlaunch after build')

# Multiple deploy/build copies are acceptable only when byte-identical.
def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()

hashes = {}
for p in cands:
    hashes.setdefault(sha(p), []).append(p)

print('===== SUBSDK9 CANDIDATES =====')
for h, paths in hashes.items():
    for p in paths:
        print(h, p.relative_to(root))

if len(hashes) != 1:
    raise SystemExit(f'STOP: multiple non-identical subsdk9 outputs: {list(hashes)}')

h, paths = next(iter(hashes.items()))
src = paths[0]
out = root / 'artifact'
dst = out / 'atmosphere/contents/0100FA10190A0000/exefs/subsdk9'
if out.exists():
    shutil.rmtree(out)
dst.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(src, dst)

assert dst.read_bytes()[:4] == b'NSO0'
assert sha(dst) == h

(out / 'SHA256SUMS.txt').write_text(
    f'{h}  atmosphere/contents/0100FA10190A0000/exefs/subsdk9\n'
)
(out / 'BUILD_INFO.txt').write_text(
    'R276H19B minimal mount-only binder\n'
    'exlaunch_ref=229bbd6\n'
    'active_hook_count=1\n'
    'hook=main+0x473190\n'
    'path=sim:data/moddingapi/Tobi_Switch.cpk\n'
    'priority=32\n'
    'plaintext_descriptor_fields=zero\n'
    f'subsdk9_sha256={h}\n'
)

print('SUBSDK9_SIZE =', dst.stat().st_size)
print('SUBSDK9_SHA256 =', h)
print('R276H19B_ARTIFACT_PACKAGE=PASS')
