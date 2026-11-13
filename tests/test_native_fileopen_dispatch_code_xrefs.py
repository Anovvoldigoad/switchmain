"""Read-only code-to-relocation-base cross-reference proof."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.native_fileopen_dispatch_code_xrefs import referenced_bases, inspect
from portlib.native_cpk_graph import MAIN_SHA256

def run(main, output):
    # ADRP X3,#0 followed by LDR X5,[X3,#0x100] at PC=0.
    text = struct.pack("<II", 0x90000003, 0xf9408065)
    assert referenced_bases(text, {0x100}) == [(0, 0x100, "adrp_ldr")]
    assert referenced_bases(text, {0x108}) == []
    assert referenced_bases(text[:4], {0x100}) == []
    # LDR literal X0, [PC + 8].
    literal = struct.pack("<I", 0x58000040)
    assert referenced_bases(literal, {8}) == [(0, 8, "ldr_literal")]
    assert referenced_bases(literal, set()) == []
    raw = main.read_bytes()
    result = inspect(raw)
    assert result["original_main_sha256"] == MAIN_SHA256
    assert len(result["dispatches"]) == 2
    assert all(x["runtime_X8_base_proven"] is False for x in result["dispatches"])
    for key in ("consumer_abi_proven", "ownership_lifecycle_async_unbind_proven",
                "archive_precedence_proven", "new_runtime_hook",
                "full_moddingapi", "ready_for_gameplay_test", "emulator_tested"):
        assert result[key] is False
    try:
        wrong = bytearray(raw)
        wrong[81] ^= 1
        inspect(wrong)
    except ValueError:
        pass
    else:
        raise AssertionError("Wrong original main accepted")
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileopen_dispatch_code_xrefs.json").write_text(
        json.dumps(result, indent=2) + "\n")
    print("NATIVE_FILEOPEN_DISPATCH_CODE_XREFS_PASS",
          [(x["field_offset"], x["adjacent_instruction_reference_count"])
           for x in result["dispatches"]], "STATIC_ONLY")

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--main", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    run(args.main, args.output)
