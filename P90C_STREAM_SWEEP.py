from pathlib import Path
from capstone import *
import hashlib, struct, lz4.block

MAIN = Path(
    "/storage/emulated/0/Downloads/restore/atmosphere/"
    "contents/0100FA10190A0000/exefs/main"
)

WANT = "2579b0cb85b79d5515a2518caeb5d5721168dbc1ec3f92c46eb372d13488ecd9"

raw = MAIN.read_bytes()
sha = hashlib.sha256(raw).hexdigest()

print("P90C STREAMING STATIC SWEEP", flush=True)
print("FILE =", MAIN, flush=True)
print("SHA256 =", sha, flush=True)

if sha != WANT:
    raise SystemExit("BAD RESTORE HASH")

if raw[:4] != b"NSO0":
    raise SystemExit("NOT NSO0")

def u32(off):
    return struct.unpack_from("<I", raw, off)[0]

flags     = u32(0x0C)
text_file = u32(0x10)
text_mem  = u32(0x14)
text_size = u32(0x18)
text_comp = u32(0x60)

if flags & 1:
    text = lz4.block.decompress(
        raw[text_file:text_file + text_comp],
        uncompressed_size=text_size
    )
else:
    text = raw[text_file:text_file + text_size]

print(
    f"TEXT mem=0x{text_mem:X} size=0x{len(text):X} "
    f"compressed={int(bool(flags & 1))}",
    flush=True
)

if len(text) != text_size:
    raise SystemExit("TEXT SIZE MISMATCH")

md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
md.detail = False
md.skipdata = True

def disasm_range(start, end):
    lo = start - text_mem
    hi = end - text_mem

    if lo < 0 or hi > len(text):
        return

    for i in md.disasm(text[lo:hi], start):
        if i.mnemonic != ".byte":
            yield i

def line(i):
    return f"{i.address:08X}: {i.mnemonic:8} {i.op_str}"

# ============================================================
# A. Known critical windows
# ============================================================

windows = [
    (0x7D3000, 0x7D3300, "F58"),
    (0x7D3900, 0x7D4200, "ACTIVE PRODUCER"),
    (0x7E2300, 0x7E2700, "P89 ACTOR PRED"),
    (0x7E3000, 0x7E5000, "UJ ROUTE / PLAYACTION"),
    (0x8B2F00, 0x8B3300, "UJ HELPER"),
]

for start, end, name in windows:
    print(flush=True)
    print("=" * 78, flush=True)
    print(
        f"WINDOW {name} 0x{start:X}..0x{end:X}",
        flush=True
    )
    print("=" * 78, flush=True)

    count = 0
    for i in disasm_range(start, end):
        print(line(i), flush=True)
        count += 1

    print(f"WINDOW_COUNT={count}", flush=True)

# ============================================================
# B. Search action immediates across text CHUNK BY CHUNK.
# No giant Capstone list.
# ============================================================

ACTIONS = [700, 707, 708, 710, 711, 712, 713, 714, 740]

print(flush=True)
print("=" * 78, flush=True)
print("FULL TEXT ACTION IMMEDIATE SWEEP", flush=True)
print("=" * 78, flush=True)

CHUNK = 0x100000
hits = []

for off in range(0, len(text), CHUNK):
    end = min(off + CHUNK, len(text))

    # ARM64 fixed-width alignment.
    start_va = text_mem + off

    for i in md.disasm(text[off:end], start_va):
        if i.mnemonic == ".byte":
            continue

        s = i.op_str.lower()

        found = []
        for n in ACTIONS:
            if f"#0x{n:x}" in s or f"#{n}" in s:
                found.append(n)

        if found:
            hits.append((i.address, tuple(found), i.mnemonic, i.op_str))
            print(
                f"HIT ids={found} {line(i)}",
                flush=True
            )

    print(
        f"PROGRESS 0x{end:X}/0x{len(text):X} hits={len(hits)}",
        flush=True
    )

print(flush=True)
print("TOTAL_ACTION_HITS =", len(hits), flush=True)

# ============================================================
# C. Context around every action hit.
# ============================================================

print(flush=True)
print("=" * 78, flush=True)
print("ACTION HIT CONTEXT", flush=True)
print("=" * 78, flush=True)

seen = set()

for addr, ids, _, _ in hits:
    # Merge nearby hits approximately by 0x100-byte buckets.
    bucket = addr & ~0xFF
    if bucket in seen:
        continue
    seen.add(bucket)

    start = max(text_mem, bucket - 0x100)
    end = min(text_mem + len(text), bucket + 0x200)

    print(flush=True)
    print(
        f"--- CONTEXT 0x{start:X}..0x{end:X} ---",
        flush=True
    )

    for i in disasm_range(start, end):
        marker = ">>" if any(abs(i.address - h[0]) < 4 for h in hits) else "  "
        print(marker + " " + line(i), flush=True)

# ============================================================
# D. Focused branch/call inventory around known UJ route.
# ============================================================

print(flush=True)
print("=" * 78, flush=True)
print("UJ 0x7E3000..0x7E5000 BRANCH/CALL INVENTORY", flush=True)
print("=" * 78, flush=True)

for i in disasm_range(0x7E3000, 0x7E5000):
    m = i.mnemonic

    if (
        m == "bl" or
        m == "blr" or
        m == "br" or
        m == "b" or
        m.startswith("b.") or
        m in ("cbz", "cbnz", "tbz", "tbnz")
    ):
        print(line(i), flush=True)

print(flush=True)
print("=" * 78, flush=True)
print("P90C COMPLETE", flush=True)
print("TOTAL_ACTION_HITS =", len(hits), flush=True)
print("=" * 78, flush=True)
