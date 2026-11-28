"""Synthetic CFG/dataflow regressions plus SHA-pinned FileLoad return provenance."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_registration_target import analyze_window
from portlib.fileload_return_provenance import inspect, trace_return_registers

RET = 0xD65F03C0


def put_word(code, offset, value):
    code[offset:offset + 4] = int(value & 0xffffffff).to_bytes(4, "little")


def encode_mov64(rd, rm):
    return 0xAA0003E0 | (rm << 16) | rd


def encode_movz64(rd, immediate):
    if not 0 <= immediate <= 0xffff:
        raise ValueError("MOVZ immediate out of range")
    return 0xD2800000 | (immediate << 5) | rd


def encode_ldr64(rt, rn, displacement):
    if displacement < 0 or displacement % 8 or displacement // 8 > 0xfff:
        raise ValueError("LDR displacement out of range")
    return 0xF9400000 | ((displacement // 8) << 10) | (rn << 5) | rt


def encode_branch(site, target, link=False):
    delta = target - site
    if delta % 4 or not -(1 << 27) <= delta < (1 << 27):
        raise ValueError("Branch target out of range")
    opcode = 0x94000000 if link else 0x14000000
    return opcode | ((delta >> 2) & 0x03ffffff)


def encode_cbz64(site, target, rt):
    delta = target - site
    if delta % 4 or not -(1 << 20) <= delta < (1 << 20):
        raise ValueError("CBZ target out of range")
    return 0xB4000000 | (((delta >> 2) & 0x7ffff) << 5) | rt


def synthetic_register_copy_and_load():
    code = bytearray(0x80)
    put_word(code, 0x00, encode_mov64(0, 1))
    put_word(code, 0x04, RET)
    window = analyze_window(code, 0x00, 0x40)
    report = trace_return_registers(code, window)
    assert report["return_sites"][0]["x0_origins"] == ["ENTRY_X1"]

    code = bytearray(0x80)
    put_word(code, 0x00, encode_ldr64(0, 1, 0x58))
    put_word(code, 0x04, RET)
    window = analyze_window(code, 0x00, 0x40)
    report = trace_return_registers(code, window)
    assert report["return_sites"][0]["x0_origins"] == [
        "LOAD(MEM(ENTRY_X1+88))"
    ]


def synthetic_call_barrier_and_redefinition():
    code = bytearray(0x200)
    put_word(code, 0x00, encode_branch(0x00, 0x100, link=True))
    put_word(code, 0x04, RET)
    window = analyze_window(code, 0x00, 0x40)
    report = trace_return_registers(code, window)
    assert report["return_sites"][0]["x0_origins"] == [
        "UNKNOWN_AFTER_CALL@0x0"
    ]
    assert report["call_barrier_sites"] == ["0x0"]

    code = bytearray(0x200)
    put_word(code, 0x00, encode_branch(0x00, 0x100, link=True))
    put_word(code, 0x04, encode_movz64(0, 42))
    put_word(code, 0x08, RET)
    window = analyze_window(code, 0x00, 0x40)
    report = trace_return_registers(code, window)
    assert report["return_sites"][0]["x0_origins"] == ["CONST(0x2a)"]


def synthetic_conditional_paths():
    code = bytearray(0x40)
    put_word(code, 0x00, encode_cbz64(0x00, 0x10, 1))
    put_word(code, 0x04, encode_mov64(0, 1))
    put_word(code, 0x08, RET)
    put_word(code, 0x10, RET)
    window = analyze_window(code, 0x00, 0x20)
    report = trace_return_registers(code, window)
    assert report["classification"] == "PATH_DEPENDENT_ORIGINS"
    assert [row["return_site"] for row in report["return_sites"]] == [
        "0x8", "0x10"
    ]
    assert report["return_sites"][0]["x0_origins"] == ["ENTRY_X1"]
    assert report["return_sites"][1]["x0_origins"] == ["ENTRY_X0"]


def expect_reject(call, label):
    try:
        call()
    except (ValueError, TypeError):
        return
    raise AssertionError("Expected rejection: " + label)


def synthetic_rejections():
    expect_reject(lambda: trace_return_registers("not bytes", {}),
                  "non-bytes text")
    expect_reject(lambda: trace_return_registers(bytes(0x40), {}),
                  "missing CFG metadata")
    expect_reject(lambda: analyze_window(bytes(0x40), 0x04, 0x04),
                  "empty CFG window")
    expect_reject(lambda: encode_branch(0, 3),
                  "unaligned branch target")


def run(main, output):
    synthetic_register_copy_and_load()
    synthetic_call_barrier_and_redefinition()
    synthetic_conditional_paths()
    synthetic_rejections()

    raw = main.read_bytes()
    report = inspect(raw)
    assert hashlib.sha256(raw).hexdigest() == MAIN_SHA256
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["target"] == "0x116b82c"
    assert report["caller_context"]["call_site"] == "0x116b3b0"
    assert report["bounded_cfg"]["return_sites"] == [
        "0x116b858", "0x116b870"
    ]
    assert report["return_provenance"]["return_site_count"] == 2
    assert [row["pc"] for row in report["bounded_cfg"]["x0_write_sites"]] == [
        "0x116b84c"
    ]
    assert report["return_provenance"]["post_call_registers_are_unknown_without_callee_proof"]
    assert report["return_provenance"]["memory_values_are_symbolic_not_read_from_runtime_objects"]
    assert all(value is False for value in report["limits"].values())

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated pinned original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_return_provenance.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_RETURN_PROVENANCE_PASS",
        "return_sites", report["return_provenance"]["return_site_count"],
        "classification", report["return_provenance"]["classification"],
        "call_barriers", len(report["return_provenance"]["call_barrier_sites"]),
        "NO_ABI_NO_OWNER_NO_UZUY_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
