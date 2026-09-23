#!/usr/bin/env python3

from pathlib import Path
import hashlib
import struct
import subprocess
import shutil
import sys
import tempfile

import lz4.block


TARGET_BID = "48ece454b61412b9fb46fab2be3f5ef7b2804f39"

F58       = 0x7D3138
POST_GATE = 0x7D2DE4
CTRL_GET  = 0x7C6280

ACTIVE_RET      = 0x7F46B8
ACTIVE_CALLSITE = ACTIVE_RET - 4

A33_HOMOLOG = 0x7F2A9C

DEPLOY = Path(
    "deploy/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)

RESTORE = Path(
    "restore/atmosphere/contents/"
    "0100FA10190A0000/exefs/main"
)


def fatal(s):
    raise SystemExit("FATAL: " + s)


def u32(b, o):
    return struct.unpack_from("<I", b, o)[0]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sign(v, bits):
    m = 1 << (bits - 1)
    return (v ^ m) - m


def decode_nso(path):
    raw = path.read_bytes()

    if raw[:4] != b"NSO0":
        fatal(f"{path}: bukan NSO0")

    bid20 = raw[0x40:0x54].hex()

    if bid20.lower() != TARGET_BID.lower():
        fatal(
            f"{path}: Build ID mismatch "
            f"{bid20}"
        )

    flags = u32(raw, 0x0C)

    text_file = u32(raw, 0x10)
    text_mem  = u32(raw, 0x14)
    text_size = u32(raw, 0x18)
    comp_size = u32(raw, 0x60)

    src = raw[text_file:text_file + comp_size]

    if flags & 1:
        text = lz4.block.decompress(
            src,
            uncompressed_size=text_size
        )
    else:
        text = raw[
            text_file:
            text_file + text_size
        ]

    if len(text) != text_size:
        fatal(
            f"{path}: decoded text size mismatch "
            f"{len(text):x}/{text_size:x}"
        )

    return {
        "path": path,
        "raw": raw,
        "text": text,
        "mem": text_mem,
        "size": text_size,
        "flags": flags,
        "sha": sha(raw),
    }


def word(img, va):
    off = va - img["mem"]

    if off < 0 or off + 4 > len(img["text"]):
        fatal(f"VA 0x{va:X} outside text")

    return struct.unpack_from(
        "<I",
        img["text"],
        off
    )[0]


def decode_bl_target(pc, w):
    if (w & 0xFC000000) != 0x94000000:
        return None

    imm = sign(
        w & 0x03FFFFFF,
        26
    ) << 2

    return pc + imm


def direct_callers(img, target):
    out = []

    t = img["text"]
    base = img["mem"]

    for i in range(0, len(t) - 3, 4):
        w = struct.unpack_from("<I", t, i)[0]
        pc = base + i

        dst = decode_bl_target(pc, w)

        if dst == target:
            out.append(pc)

    return out


def branch_target(pc, w):
    # B / BL
    op = w & 0xFC000000

    if op in (0x14000000, 0x94000000):
        imm = sign(
            w & 0x03FFFFFF,
            26
        ) << 2

        return pc + imm

    # B.cond
    if (w & 0xFF000010) == 0x54000000:
        imm = sign(
            (w >> 5) & 0x7FFFF,
            19
        ) << 2

        return pc + imm

    # CBZ / CBNZ, W/X
    if (w & 0x7E000000) == 0x34000000:
        imm = sign(
            (w >> 5) & 0x7FFFF,
            19
        ) << 2

        return pc + imm

    # TBZ / TBNZ
    if (w & 0x7E000000) == 0x36000000:
        imm = sign(
            (w >> 5) & 0x3FFF,
            14
        ) << 2

        return pc + imm

    return None


def branch_edges(img, lo, hi):
    print(
        f"\n===== BRANCH EDGES "
        f"0x{lo:X}..0x{hi:X} ====="
    )

    for pc in range(lo, hi, 4):
        w = word(img, pc)
        dst = branch_target(pc, w)

        if dst is not None:
            print(
                f"0x{pc:08X} "
                f"{w:08X} "
                f"-> 0x{dst:08X}"
            )


def make_elf(img, outdir, tag):
    clang = (
        shutil.which("clang")
        or fatal("clang missing; pkg install clang")
    )

    ld = (
        shutil.which("ld.lld")
        or fatal("ld.lld missing; pkg install lld")
    )

    raw = outdir / f"{tag}_text.bin"
    asm = outdir / f"{tag}_wrap.S"
    obj = outdir / f"{tag}_text.o"
    elf = outdir / f"{tag}_text.elf"

    raw.write_bytes(img["text"])

    # incbin absolute path avoids cwd ambiguity.
    asm.write_text(
        '.section .text,"ax",@progbits\n'
        '.global _start\n'
        '_start:\n'
        f'.incbin "{raw}"\n'
    )

    subprocess.run(
        [
            clang,
            "-c",
            str(asm),
            "-o",
            str(obj),
        ],
        check=True
    )

    subprocess.run(
        [
            ld,
            "-m",
            "aarch64elf",
            f"-Ttext=0x{img['mem']:X}",
            "--entry=_start",
            "-o",
            str(elf),
            str(obj),
        ],
        check=True
    )

    return elf


def disasm(elf, lo, hi, title):
    od = (
        shutil.which("llvm-objdump")
        or fatal("llvm-objdump missing")
    )

    print(
        "\n"
        + "=" * 100
    )
    print(title)
    print(
        "=" * 100
    )

    p = subprocess.run(
        [
            od,
            "-d",
            f"--start-address=0x{lo:X}",
            f"--stop-address=0x{hi:X}",
            str(elf),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=True
    )

    print(p.stdout)


def main():
    for p in (DEPLOY, RESTORE):
        if not p.is_file():
            fatal(f"missing {p}")

    deploy = decode_nso(DEPLOY)
    restore = decode_nso(RESTORE)

    print(
        "===== TARGET ====="
    )
    print(
        "BUILD_ID=" + TARGET_BID
    )
    print(
        f"DEPLOY_SHA256={deploy['sha']}"
    )
    print(
        f"RESTORE_SHA256={restore['sha']}"
    )
    print(
        f"DEPLOY_TEXT_MEM=0x{deploy['mem']:X}"
    )
    print(
        f"DEPLOY_TEXT_SIZE=0x{deploy['size']:X}"
    )

    print(
        "\n===== SOURCE-PARITY WORD ====="
    )

    dw = word(
        deploy,
        A33_HOMOLOG
    )

    rw = word(
        restore,
        A33_HOMOLOG
    )

    print(
        f"DEPLOY  0x{A33_HOMOLOG:X}: "
        f"{dw:08X}"
    )

    print(
        f"RESTORE 0x{A33_HOMOLOG:X}: "
        f"{rw:08X}"
    )

    print(
        "\n===== DIRECT BL CALLERS ====="
    )

    for name, target in [
        ("F58", F58),
        ("POST_GATE", POST_GATE),
        ("CTRL_GET", CTRL_GET),
    ]:
        calls = direct_callers(
            deploy,
            target
        )

        print(
            f"{name} target=0x{target:X} "
            f"count={len(calls)}"
        )

        for c in calls:
            print(
                f"  BL @0x{c:08X} "
                f"return=0x{c+4:08X}"
            )

    # Exact machine word at active callsite.
    w = word(
        deploy,
        ACTIVE_CALLSITE
    )

    dst = decode_bl_target(
        ACTIVE_CALLSITE,
        w
    )

    print(
        "\n===== ACTIVE CALLSITE CHECK ====="
    )

    print(
        f"callsite=0x{ACTIVE_CALLSITE:X} "
        f"word={w:08X} "
        f"target="
        + (
            f"0x{dst:X}"
            if dst is not None
            else "NOT_BL"
        )
    )

    # Print every local control-flow edge in the active input classifier.
    branch_edges(
        deploy,
        0x7F4500,
        0x7F47A0
    )

    tmpbase = (
        Path(
            "/data/data/com.termux/files/usr/tmp"
        )
        / "nsc_p66_pre_f58"
    )

    tmpbase.mkdir(
        parents=True,
        exist_ok=True
    )

    elf = make_elf(
        deploy,
        tmpbase,
        "deploy"
    )

    # Main active vanilla-UJ classification region.
    disasm(
        elf,
        0x7F4500,
        0x7F47A0,
        "A) ACTIVE INPUT/UJ CLASSIFIER AROUND 0x7F46B4"
    )

    # Source-parity NOP region: proves what the P65 paired main actually runs.
    disasm(
        elf,
        0x7F2A50,
        0x7F2AD0,
        "B) P65 SOURCE-PARITY REGION 0x7F2A9C"
    )

    # Ordinary jutsu action-selection implementation that emits 445.
    disasm(
        elf,
        0x7B4A80,
        0x7B4B70,
        "C) ORDINARY JUTSU 445 OWNER"
    )

    # Caller which enters base action-mode implementation.
    disasm(
        elf,
        0x7A82C0,
        0x7A83C0,
        "D) ACTION-MODE CALLER / MODE0"
    )

    print(
        "\n===== MACHINE CONCLUSION INPUT ====="
    )
    print(
        "Need identify predicate/branch BEFORE "
        "BL@0x7F46B4 that controls entry to "
        "the UJ classifier."
    )
    print(
        "Do NOT patch F58, action445, action700 "
        "or E94 from this script."
    )


if __name__ == "__main__":
    main()
