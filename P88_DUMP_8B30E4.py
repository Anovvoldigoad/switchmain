#!/usr/bin/env python3
import struct
from pathlib import Path
from capstone import *
from capstone.arm64 import *

MAIN = Path("paired/atmosphere/contents/0100FA10190A0000/exefs/main")
START = 0x8B2000
END   = 0x8B5000
FOCUS = 0x8B30E4

raw = MAIN.read_bytes()

if raw[:4] != b"NSO0":
    raise SystemExit("NOT_NSO0")

# NSO header segment descriptors.
text_file_off, text_mem_off, text_dec_size = struct.unpack_from("<III", raw, 0x10)
ro_file_off,   ro_mem_off,   ro_dec_size   = struct.unpack_from("<III", raw, 0x20)
data_file_off, data_mem_off, data_dec_size = struct.unpack_from("<III", raw, 0x30)

flags = struct.unpack_from("<I", raw, 0x0C)[0]

# Compressed sizes are stored later in the NSO header.
text_comp_size, ro_comp_size, data_comp_size = struct.unpack_from("<III", raw, 0x60)

print(f"NSO_FLAGS={flags:#x}")
print(f"TEXT file={text_file_off:#x} mem={text_mem_off:#x} dec={text_dec_size:#x} comp={text_comp_size:#x}")
print(f"RO   file={ro_file_off:#x} mem={ro_mem_off:#x} dec={ro_dec_size:#x} comp={ro_comp_size:#x}")
print(f"DATA file={data_file_off:#x} mem={data_mem_off:#x} dec={data_dec_size:#x} comp={data_comp_size:#x}")

def lz4_decompress(blob, expected):
    try:
        import lz4.block
    except Exception as e:
        raise SystemExit(f"LZ4_MODULE_MISSING: {e}")
    return lz4.block.decompress(blob, uncompressed_size=expected)

text_blob = raw[text_file_off:text_file_off + text_comp_size]

# NSO compression flag bit 0 = text.
if flags & 1:
    text = lz4_decompress(text_blob, text_dec_size)
    print("TEXT_DECOMPRESS=PASS")
else:
    text = raw[text_file_off:text_file_off + text_dec_size]
    print("TEXT_UNCOMPRESSED=1")

if len(text) != text_dec_size:
    raise SystemExit(f"TEXT_SIZE_FAIL got={len(text):#x} expected={text_dec_size:#x}")

if not (text_mem_off <= START < END <= text_mem_off + len(text)):
    raise SystemExit("REQUESTED_RANGE_OUTSIDE_TEXT")

region = text[START-text_mem_off:END-text_mem_off]

md = Cs(CS_ARCH_ARM64, CS_MODE_LITTLE_ENDIAN)
md.detail = True

branch_groups = {
    ARM64_GRP_JUMP,
    ARM64_GRP_CALL,
    ARM64_GRP_RET,
}

interesting = []

with open("P88_8B2000_8B5000_DISASM.txt", "w") as out:
    for ins in md.disasm(region, START):
        marker = " <=== 8B30E4" if ins.address == FOCUS else ""
        line = f"{ins.address:08X}: {ins.bytes.hex():8s}  {ins.mnemonic:8s} {ins.op_str}{marker}"
        out.write(line + "\n")

        m = ins.mnemonic.lower()
        if (
            any(g in ins.groups for g in branch_groups)
            or m.startswith(("cbz","cbnz","tbz","tbnz"))
            or (m.startswith("b.") and m != "b")
            or m in ("cmp","cmn","tst")
        ):
            interesting.append(line)

with open("P88_8B2000_8B5000_BRANCHES.txt", "w") as out:
    out.write("\n".join(interesting) + "\n")

print("DISASM=P88_8B2000_8B5000_DISASM.txt")
print("BRANCHES=P88_8B2000_8B5000_BRANCHES.txt")
print(f"INTERESTING={len(interesting)}")
