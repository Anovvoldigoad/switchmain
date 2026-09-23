#!/usr/bin/env python3
from pathlib import Path
from capstone import *
from capstone.arm64 import *
import lz4.block
import hashlib, struct, sys
from collections import defaultdict

RESTORE = Path(
    "/storage/emulated/0/Downloads/restore/atmosphere/"
    "contents/0100FA10190A0000/exefs/main"
)

EXPECTED_SHA = (
    "2579b0cb85b79d5515a2518caeb5d572"
    "1168dbc1ec3f92c46eb372d13488ecd9"
)

# Known UJ/action states. 708 is now included explicitly.
ACTION_IDS = {700, 707, 708, 710, 711, 712, 713, 714, 740}

# Runtime anchors already established by previous probes.
ANCHORS = {
    0x7E35E8: "PlayAction700 callsite",
    0x7E35EC: "PlayAction700 return",
    0x7D3138: "F58",
    0x7D3AD0: "active BDA4/BDC8 producer",
    0x7E24EC: "P89 actor predicate",
    0x8B30E4: "UJ helper",
}

def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]

def die(s):
    raise SystemExit("ERROR: " + s)

if not RESTORE.is_file():
    die(f"restore main tidak ada: {RESTORE}")

raw = RESTORE.read_bytes()
sha = hashlib.sha256(raw).hexdigest()

print("=" * 78)
print("P90 NSO-AWARE UJ / CINEMATIC STATIC SWEEP")
print("=" * 78)
print("FILE   :", RESTORE)
print("SHA256 :", sha)
print("SIZE   :", len(raw))

if sha != EXPECTED_SHA:
    die("restore main SHA256 bukan canonical v1.70")

if raw[:4] != b"NSO0":
    die(f"magic bukan NSO0: {raw[:4]!r}")

print("NSO0   : PASS")

# ------------------------------------------------------------
# NSO0 header
#
# segment descriptors:
#   +0x10 text  : file_off, memory_off, decompressed_size
#   +0x20 rodata
#   +0x30 data
#
# compressed sizes:
#   +0x60 text
#   +0x64 rodata
#   +0x68 data
#
# flags bit 0/1/2 indicate text/ro/data compression.
# ------------------------------------------------------------

flags = u32(raw, 0x0C)

text_file = u32(raw, 0x10)
text_mem  = u32(raw, 0x14)
text_size = u32(raw, 0x18)
text_comp = u32(raw, 0x60)

print()
print("[NSO HEADER]")
print(f"flags          = 0x{flags:08X}")
print(f"text_file_off  = 0x{text_file:X}")
print(f"text_mem_off   = 0x{text_mem:X}")
print(f"text_size      = 0x{text_size:X}")
print(f"text_comp_size = 0x{text_comp:X}")

if not text_size:
    die("text_size=0")

compressed = bool(flags & 1)

if compressed:
    if not text_comp:
        die("text compressed flag aktif tetapi compressed size=0")
    blob = raw[text_file:text_file + text_comp]
    try:
        text = lz4.block.decompress(
            blob,
            uncompressed_size=text_size
        )
    except Exception as e:
        die(f"LZ4 text decompress gagal: {e}")
else:
    text = raw[text_file:text_file + text_size]

if len(text) != text_size:
    die(
        f"decompressed text size mismatch: "
        f"{len(text):#x} != {text_size:#x}"
    )

print(f"text compressed = {int(compressed)}")
print(f"text decoded     = 0x{len(text):X}")
print("TEXT DECODE      = PASS")

# Main-relative offsets in our previous analysis are relative to NSO memory
# base. text_mem is therefore accounted for when translating to text[].
def to_index(addr):
    return addr - text_mem

def in_text(addr):
    i = to_index(addr)
    return 0 <= i <= len(text) - 4

# Sanity: known anchors must exist inside executable text.
print()
print("[ANCHOR SANITY]")
for a, name in ANCHORS.items():
    ok = in_text(a)
    word = u32(text, to_index(a)) if ok else 0
    print(
        f"0x{a:08X}  {'PASS' if ok else 'FAIL'}  "
        f"{word:08X}  {name}"
    )
    if not ok:
        die(f"anchor 0x{a:X} outside .text")

# ------------------------------------------------------------
# Disassemble entire .text once.
# ------------------------------------------------------------

md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
md.detail = True
md.skipdata = True

print()
print("[DISASSEMBLING FULL TEXT]")
insns = [
    ins for ins in md.disasm(text, text_mem)
    if ins.mnemonic != ".byte"
]
print("instructions =", len(insns))

if len(insns) < 100000:
    die(f"Capstone decoded suspiciously few instructions: {len(insns)}")

by_addr = {i.address: i for i in insns}

# Direct BL target -> callsites.
callers = defaultdict(list)
for ins in insns:
    if ins.mnemonic == "bl" and ins.operands:
        op = ins.operands[0]
        if op.type == ARM64_OP_IMM:
            callers[op.imm].append(ins.address)

def fmt(ins):
    return f"{ins.address:08X}: {ins.mnemonic:8} {ins.op_str}"

def dump_window(center, before=0x80, after=0x100):
    lo = center - before
    hi = center + after
    for ins in insns:
        if lo <= ins.address < hi:
            mark = ">>" if ins.address == center else "  "
            print(mark, fmt(ins))

# ------------------------------------------------------------
# 1. Known anchor neighborhoods.
# ------------------------------------------------------------

print()
print("=" * 78)
print("KNOWN ANCHOR WINDOWS")
print("=" * 78)

for a, name in ANCHORS.items():
    print()
    print(f"--- {name}: 0x{a:X} ---")
    dump_window(a, 0x100, 0x180)

# ------------------------------------------------------------
# 2. Search immediate action IDs across full text.
#    We deliberately collect any instruction exposing one of the IDs,
#    then inspect context instead of assuming each hit is gameplay-related.
# ------------------------------------------------------------

hits = []

for ins in insns:
    found = set()
    try:
        for op in ins.operands:
            if op.type == ARM64_OP_IMM and op.imm in ACTION_IDS:
                found.add(op.imm)
    except Exception:
        pass

    # Capstone sometimes represents immediates in ways where lexical
    # inspection is useful as a secondary net.
    for n in ACTION_IDS:
        hx = f"#0x{n:x}"
        dec = f"#{n}"
        if hx in ins.op_str.lower() or dec in ins.op_str:
            found.add(n)

    for n in found:
        hits.append((ins.address, n, ins))

print()
print("=" * 78)
print("ACTION-ID IMMEDIATE HITS")
print("=" * 78)
print("hit_count =", len(hits))

for addr, n, ins in hits:
    print(f"ACTION={n:<3}  {fmt(ins)}")

# ------------------------------------------------------------
# 3. Context around every hit, deduplicated into clusters.
# ------------------------------------------------------------

clusters = []
for addr, n, ins in sorted(hits):
    if not clusters or addr - clusters[-1][-1][0] > 0x100:
        clusters.append([])
    clusters[-1].append((addr, n, ins))

print()
print("=" * 78)
print("ACTION-ID HIT CLUSTERS")
print("=" * 78)

for ci, cluster in enumerate(clusters):
    center_lo = cluster[0][0]
    center_hi = cluster[-1][0]
    ids = sorted({x[1] for x in cluster})

    print()
    print(
        f"--- CLUSTER {ci:03d} "
        f"0x{center_lo:X}..0x{center_hi:X} "
        f"IDs={ids} ---"
    )

    lo = center_lo - 0x100
    hi = center_hi + 0x180

    for ins in insns:
        if lo <= ins.address < hi:
            marker = ">>" if any(ins.address == x[0] for x in cluster) else "  "
            print(marker, fmt(ins))

# ------------------------------------------------------------
# 4. BL targets in/near action-ID clusters.
# ------------------------------------------------------------

candidate_targets = defaultdict(set)

for cluster in clusters:
    lo = cluster[0][0] - 0x120
    hi = cluster[-1][0] + 0x1A0

    for ins in insns:
        if not (lo <= ins.address < hi):
            continue

        if ins.mnemonic == "bl" and ins.operands:
            op = ins.operands[0]
            if op.type == ARM64_OP_IMM:
                candidate_targets[op.imm].add(ins.address)

print()
print("=" * 78)
print("HELPERS CALLED NEAR ACTION-ID CLUSTERS")
print("=" * 78)

for target in sorted(candidate_targets):
    cs = sorted(candidate_targets[target])
    print(
        f"TARGET 0x{target:08X} "
        f"cluster_callsites={','.join(f'0x{x:X}' for x in cs)} "
        f"global_direct_callers={len(callers.get(target, []))}"
    )

# ------------------------------------------------------------
# 5. Dump candidate helper entrypoints and their direct callers.
# ------------------------------------------------------------

print()
print("=" * 78)
print("CANDIDATE HELPER ENTRY WINDOWS")
print("=" * 78)

for target in sorted(candidate_targets):
    if not in_text(target):
        continue

    print()
    print(f"--- HELPER 0x{target:X} ---")
    print(
        "DIRECT CALLERS:",
        " ".join(f"0x{x:X}" for x in callers.get(target, [])[:100])
        or "none"
    )
    dump_window(target, 0x40, 0x140)

# ------------------------------------------------------------
# 6. Special wide corridor around known PlayAction700 selection.
# ------------------------------------------------------------

print()
print("=" * 78)
print("UJ ROUTING CORRIDOR 0x7E2000..0x7E5000")
print("=" * 78)

for ins in insns:
    if 0x7E2000 <= ins.address < 0x7E5000:
        print(fmt(ins))

# ------------------------------------------------------------
# 7. Branch/call inventory specifically around 0x7E3000..0x7E4000.
# ------------------------------------------------------------

print()
print("=" * 78)
print("UJ BRANCH/CALL INVENTORY 0x7E3000..0x7E4000")
print("=" * 78)

branch_mnems = {
    "bl", "b", "br", "blr",
    "cbz", "cbnz", "tbz", "tbnz",
    "b.eq", "b.ne", "b.lt", "b.le", "b.gt", "b.ge",
    "b.hi", "b.hs", "b.lo", "b.ls",
    "b.mi", "b.pl", "b.vs", "b.vc",
}

for ins in insns:
    if 0x7E3000 <= ins.address < 0x7E4000:
        if ins.mnemonic in branch_mnems or ins.mnemonic.startswith("b."):
            print(fmt(ins))

# ------------------------------------------------------------
# Summary for P90A design.
# ------------------------------------------------------------

print()
print("=" * 78)
print("P90 STATIC SUMMARY")
print("=" * 78)
print("ACTION_IDS       =", sorted(ACTION_IDS))
print("ACTION_HITS      =", len(hits))
print("HIT_CLUSTERS     =", len(clusters))
print("HELPER_TARGETS   =", len(candidate_targets))
print()
print("IMPORTANT:")
print("- Immediate hits are candidates, not automatically gameplay states.")
print("- No binary is modified.")
print("- Use vanilla-vs-custom runtime comparison before any compatibility write.")
print("- P89 admission bridge remains a separate already-proven layer.")
