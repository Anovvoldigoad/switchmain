import argparse
import json
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R))
from tools.portlib.native_fileload_inbound_args import (
    CALLSITE, ENTRY, MAIN_SHA256, WINDOW_END, WINDOW_START,
    analyze_caller_window, inspect,
)


def _bl(pc, target):
    imm = (target - pc) // 4
    return struct.pack("<I", 0x94000000 | (imm & 0x03FFFFFF))


def _b(pc, target):
    imm = (target - pc) // 4
    return struct.pack("<I", 0x14000000 | (imm & 0x03FFFFFF))


def synthetic():
    # Two exact register copies reach the sink.
    code = bytes.fromhex("e10317aae20314aa") + _bl(8, 0x2000)
    report = analyze_caller_window(code, 0, 12, 8, 0x2000)
    assert [x["at"] for x in report["possible_reaching_definitions"]["x1"]] == ["0x0"]
    assert [x["at"] for x in report["possible_reaching_definitions"]["x2"]] == ["0x4"]
    assert report["single_definition_proven_within_window"] == {"x1": True, "x2": True}

    # An earlier call is a hard barrier for X1/X2; a later definition supersedes it.
    code = _bl(0, 0x2100) + bytes.fromhex("e10313aa") + _bl(8, 0x2200)
    report = analyze_caller_window(code, 0, 12, 8, 0x2200)
    assert [x["kind"] for x in report["possible_reaching_definitions"]["x1"]] == ["definition"]
    assert [x["kind"] for x in report["possible_reaching_definitions"]["x2"]] == ["call_barrier"]

    # Both sides of a conditional merge must be retained, not arbitrarily selected.
    words = [
        0xB4000060,  # cbz x0, #0xc
        0xAA1303E1,  # mov x1, x19
        0x14000002,  # b #0x10
        0xAA1403E1,  # mov x1, x20
    ]
    code = b"".join(struct.pack("<I", x) for x in words) + _bl(16, 0x2000)
    report = analyze_caller_window(code, 0, 20, 16, 0x2000)
    assert {x["at"] for x in report["possible_reaching_definitions"]["x1"]} == {"0x4", "0xc"}
    assert report["single_definition_proven_within_window"]["x1"] is False

    # Stack-relative and memory-loaded argument sources remain explicit.
    code = struct.pack("<I", 0x910083E1) + struct.pack("<I", 0xF9400A62) + _bl(8, 0x2200)
    report = analyze_caller_window(code, 0, 12, 8, 0x2200)
    x1 = report["possible_reaching_definitions"]["x1"][0]
    x2 = report["possible_reaching_definitions"]["x2"][0]
    assert x1["definition_kind"] == "stack_relative_address"
    assert x1["instruction"]["memory_operands"] == []
    assert x2["definition_kind"] == "memory_load"
    assert x2["instruction"]["memory_operands"][0]["base_register"] == "x19"
    assert x2["instruction"]["memory_operands"][0]["displacement"] == 16

    # A window with no local definition stays explicitly unknown.
    code = struct.pack("<I", 0xD503201F) + _bl(4, 0x2300)
    report = analyze_caller_window(code, 0, 8, 4, 0x2300)
    assert all(x["kind"] == "window_entry_unknown"
               for reg in ("x1", "x2")
               for x in report["possible_reaching_definitions"][reg])

    for args in ((b"12345678", 1, 8, 4), (b"12345678", 0, 7, 4)):
        try:
            analyze_caller_window(*args)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid caller window was accepted")

def run(main, output):
    synthetic()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["incoming_direct_call_count"] == 1
    assert report["incoming_direct_calls"][0]["source"] == hex(CALLSITE)
    assert report["incoming_direct_calls"][0]["kind"] == "BL"
    caller = report["caller_window"]
    assert caller["callsite"] == hex(CALLSITE)
    assert caller["sink_target"] == hex(ENTRY)
    assert caller["sink_reachable_from_bounded_window"]
    assert caller["decoded_instruction_count"] > 64
    assert len(caller["window_sha256"]) == 64
    for key in (
        "caller_function_extent_verified",
        "caller_argument_identity_verified",
        "object_type_or_ownership_verified",
        "constructor_or_destructor_verified",
        "native_consumer_abi_verified",
        "callback_async_rollback_unbind_verified",
        "archive_precedence_verified",
        "native_hook_added",
        "gameplay_verified",
        "full_moddingapi",
        "ready_for_gameplay_test",
        "emulator_tested",
    ):
        assert report[key] is False

    tampered = bytearray(raw)
    tampered[0] ^= 1
    try:
        inspect(bytes(tampered))
    except ValueError as exc:
        assert "SHA256" in str(exc)
    else:
        raise AssertionError("Mutated original main was accepted")

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        source = root / "main"
        source.write_bytes(raw)
        cmd = [
            sys.executable,
            str(R / "tools/audit_native_fileload_inbound_args.py"),
            "--main", str(source),
            "--output", str(root / "good"),
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        saved = json.loads((root / "good/native_fileload_inbound_args.json").read_text())
        assert saved == report
        broken = bytearray(raw)
        broken[0] ^= 1
        source.write_bytes(broken)
        cmd[-1] = str(root / "rejected")
        assert subprocess.run(cmd, capture_output=True).returncode
        assert not (root / "rejected").exists()

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_inbound_args.json").write_text(json.dumps(report, indent=2) + "\n")
    origins = {
        reg: [(x["kind"], x.get("at"), x.get("definition_kind"))
              for x in caller["possible_reaching_definitions"][reg]]
        for reg in ("x1", "x2")
    }
    print("PINNED_FILELOAD_INBOUND_ARGUMENTS_PASS",
          "caller", hex(CALLSITE), "window", hex(WINDOW_START), hex(WINDOW_END),
          "origins", origins, "NO_OWNERSHIP_NO_ABI_NO_GAMEPLAY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.main, args.output)
