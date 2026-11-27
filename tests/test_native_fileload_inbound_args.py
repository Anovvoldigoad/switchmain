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


def _direct_bl_inventory(instructions, end_exclusive):
    if end_exclusive < 0 or end_exclusive & 3:
        raise ValueError("Invalid direct-BL inventory boundary")
    calls = []
    previous_pc = None
    for row in instructions:
        try:
            pc = int(row["pc"], 16)
            raw = bytes.fromhex(row["word_le"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Malformed instruction row in direct-BL inventory") from exc
        if pc < 0 or pc & 3 or len(raw) != 4:
            raise ValueError("Unaligned or partial instruction in direct-BL inventory")
        if previous_pc is not None and pc <= previous_pc:
            raise ValueError("Instruction rows are not strictly ordered")
        previous_pc = pc
        if pc >= end_exclusive:
            continue
        word = struct.unpack("<I", raw)[0]
        # Independent A64 BL encoding decode: op[31:26] == 100101,
        # signed imm26 scaled by four and added to the instruction PC.
        if word & 0xFC000000 != 0x94000000:
            continue
        imm26 = word & 0x03FFFFFF
        if imm26 & 0x02000000:
            imm26 -= 0x04000000
        calls.append((hex(pc), hex(pc + (imm26 << 2))))
    return calls


def synthetic_direct_bl_inventory():
    # Positive forward/backward BLs; an unconditional B must not be inventoried.
    code = _bl(0, 0x100) + _b(4, 0x200) + _bl(8, 0)
    rows = [
        {"pc": hex(pc), "word_le": code[pc:pc + 4].hex()}
        for pc in range(0, len(code), 4)
    ]
    assert _direct_bl_inventory(rows, 12) == [("0x0", "0x100"), ("0x8", "0x0")]
    for bad_rows, boundary in (
        ([{"pc": "0x1", "word_le": _bl(0, 0x100).hex()}], 12),
        ([{"pc": "0x0", "word_le": "abcd"}], 12),
        ([{"pc": "0x4", "word_le": _bl(0, 0x100).hex()},
          {"pc": "0x0", "word_le": _b(4, 0x200).hex()}], 12),
        (rows, 10),
    ):
        try:
            _direct_bl_inventory(bad_rows, boundary)
        except ValueError:
            pass
        else:
            raise AssertionError("Malformed direct-BL inventory was accepted")


def synthetic():
    # Two exact register copies reach the sink.
    code = bytes.fromhex("e10317aae20314aa") + _bl(8, 0x2000)
    report = analyze_caller_window(code, 0, 12, 8, 0x2000)
    assert [x["at"] for x in report["possible_reaching_definitions"]["x1"]] == ["0x0"]
    assert [x["at"] for x in report["possible_reaching_definitions"]["x2"]] == ["0x4"]
    assert report["single_definition_proven_within_window"] == {"x1": True, "x2": True, "x19": False}

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

def synthetic_x19_call_preservation():
    # X19 survives only when the exact direct callee has a positive bounded proof.
    code = struct.pack("<I", 0xAA0503F3) + _bl(4, 0x100) + _bl(8, 0x200)
    proof = {"target": "0x100", "preserved": True, "reason": "SYNTHETIC_LEAF"}
    preserved = analyze_caller_window(
        code, 0, 12, 8, call_preservation={4: {"x19": proof}}
    )
    x19 = preserved["possible_reaching_definitions"]["x19"]
    assert [(x["kind"], x.get("at")) for x in x19] == [("definition", "0x0")]
    assert preserved["single_definition_proven_within_window"]["x19"] is True
    # The same call remains a hard barrier when the callee proof is absent or negative.
    blocked = analyze_caller_window(code, 0, 12, 8)
    x19_blocked = blocked["possible_reaching_definitions"]["x19"]
    assert len(x19_blocked) == 1 and x19_blocked[0]["kind"] == "call_barrier"
    assert x19_blocked[0]["target"] == "0x100"
    negative = analyze_caller_window(
        code, 0, 12, 8,
        call_preservation={4: {"x19": {"target": "0x100", "preserved": False, "reason": "REGISTER_WRITTEN"}}}
    )
    assert negative["possible_reaching_definitions"]["x19"][0]["kind"] == "call_barrier"
    # A proof for a different callee must never preserve the incoming X19 value.
    try:
        analyze_caller_window(
            code, 0, 12, 8,
            call_preservation={4: {"x19": {"target": "0x104", "preserved": True, "reason": "FORGED_TARGET"}}}
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Mismatched X19 callee proof was accepted")
    # Conditional paths retain both reaching X19 definitions at the sink.
    words = [0xB4000060, 0xAA0503F3, 0x14000002, 0xAA0603F3]
    merged_code = b"".join(struct.pack("<I", word) for word in words) + _bl(16, 0x2000)
    merged = analyze_caller_window(merged_code, 0, 20, 16)
    assert {x["at"] for x in merged["possible_reaching_definitions"]["x19"]} == {"0x4", "0xc"}
    assert merged["single_definition_proven_within_window"]["x19"] is False


def run(main, output):
    synthetic()
    synthetic_x19_call_preservation()
    synthetic_direct_bl_inventory()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["incoming_direct_call_count"] == 1
    assert report["incoming_direct_calls"][0]["source"] == hex(CALLSITE)
    assert report["incoming_direct_calls"][0]["kind"] == "BL"
    caller = report["caller_window"]
    assert caller["tracked_registers"] == ["x1", "x2", "x19"]
    assert caller["callsite"] == hex(CALLSITE)
    assert caller["sink_target"] == hex(ENTRY)
    assert caller["sink_reachable_from_bounded_window"]
    assert caller["decoded_instruction_count"] > 64
    assert len(caller["window_sha256"]) == 64
    assert caller["source_register_origins_not_traced"] is True
    x2_origin = caller["possible_reaching_definitions"]["x2"][0]
    assert x2_origin["instruction"]["read_registers"] == ["x19"]
    assert caller["possible_reaching_definitions"]["x19"]
    # Derive the expected call inventory independently from the original
    # little-endian instruction words, rather than duplicating a hand-entered
    # target list or the production direct_branch helper.
    expected_calls = _direct_bl_inventory(caller["instructions"], CALLSITE)
    proofs = report["caller_call_preservation_proofs"]
    actual_calls = [(x["site"], x["target"]) for x in proofs]
    assert actual_calls == expected_calls, (
        "Caller BL proof inventory differs from independent A64 immediate decode: "
        f"expected={expected_calls!r} actual={actual_calls!r}"
    )
    assert all(x["proof"]["register"] == "x19" for x in proofs)
    assert all(isinstance(x["proof"]["preserved"], bool) for x in proofs)
    assert all(x["proof"]["bounded_window_not_function_extent"] is True for x in proofs)
    assert report["caller_x19_numeric_value_proven"] is False
    assert report["caller_x19_pointer_type_verified"] is False
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
          "origins", origins, "x19_calls",
          [(x["site"], x["proof"]["preserved"], x["proof"]["reason"])
           for x in report["caller_call_preservation_proofs"]],
          "NO_OWNERSHIP_NO_ABI_NO_GAMEPLAY")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.main, args.output)
