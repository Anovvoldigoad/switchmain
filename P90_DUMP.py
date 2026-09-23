from capstone import *
from pathlib import Path
import hashlib, os

WANT = "1adc4dfe948d616cbb7c6d9b3672842aba8e7d86bf0763e668505dff84234de0"

roots = [
    Path.home(),
    Path("/storage/emulated/0"),
]

found = None

for root in roots:
    if not root.exists():
        continue
    for dp, dns, fns in os.walk(root):
        # Hindari beberapa direktori besar/tidak relevan
        dns[:] = [d for d in dns if d not in {
            ".git", "node_modules", "__pycache__"
        }]
        if "main" not in fns:
            continue

        p = Path(dp) / "main"
        try:
            h = hashlib.sha256(p.read_bytes()).hexdigest()
        except Exception:
            continue

        if h == WANT:
            found = p
            break
    if found:
        break

if not found:
    raise SystemExit(
        "PAIRED MAIN TIDAK DITEMUKAN\n"
        "Expected SHA256: " + WANT
    )

b = found.read_bytes()

print("FILE =", found)
print("SHA256 =", hashlib.sha256(b).hexdigest())
print("SIZE =", len(b))
print("RANGE = 0x7E3000..0x7E5000")
print()

START = 0x7E3000
END   = 0x7E5000

if len(b) < END:
    raise SystemExit(f"FILE TERLALU KECIL: {len(b):#x}")

md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
md.detail = False

for ins in md.disasm(b[START:END], START):
    print(f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}")
