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
    assert report["single_definition_proven_within_window"] == {"x0": False, "x1": True, "x2": True, "x19": False}

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




def synthetic_x19_stack_restore():
    from tools.portlib.native_fileload_call_targets import analyze_stack_register_restore

    good = bytes.fromhex("fe4fbfa9f30300aafe4fc1a8c0035fd6")
    report = analyze_stack_register_restore(good, 0, len(good), "x19")
    assert report["preservation_proven"] is True
    assert report["save_sites"] == [{
        "pc": "0x0", "entry_sp_slot": "-0x8",
        "width": 8, "saved_register_origin": "entry"
    }]
    assert report["restore_sites"] == [{
        "pc": "0x8", "entry_sp_slot": "-0x8", "width": 8
    }]
    assert report["sp_balanced_on_all_returns"] is True

    mismatch = bytes.fromhex("fe4fbfa9f30300aafe53c1a8c0035fd6")
    report = analyze_stack_register_restore(mismatch, 0, len(mismatch), "x19")
    assert report["preservation_proven"] is False
    assert report["all_return_paths_restore_entry_register"] is False

    overwrite = bytes.fromhex("fe4fbfa9f30300aae00700f9fe4fc1a8c0035fd6")
    report = analyze_stack_register_restore(overwrite, 0, len(overwrite), "x19")
    assert report["preservation_proven"] is False
    assert report["all_return_paths_restore_entry_register"] is False

    with_call = bytes.fromhex("fe4fbfa9f30300aa03000094fe4fc1a8c0035fd6c0035fd6")
    report = analyze_stack_register_restore(with_call, 0, len(with_call), "x19")
    assert report["local_restore_on_all_returns"] is True
    assert report["preservation_proven"] is False
    assert report["reason"] == "NESTED_CALL_STACK_EFFECT_UNPROVEN"

    unknown_store = bytes.fromhex("fe4fbfa9f30300aa410000f9fe4fc1a8c0035fd6")
    report = analyze_stack_register_restore(unknown_store, 0, len(unknown_store), "x19")
    assert report["local_restore_on_all_returns"] is True
    assert report["preservation_proven"] is False
    assert report["reason"] == "UNKNOWN_MEMORY_ALIAS_STORE"

    bypass = bytes.fromhex("800000b4fe4fbfa9f30300aafe4fc1a8c0035fd6")
    report = analyze_stack_register_restore(bypass, 0, len(bypass), "x19")
    assert report["preservation_proven"] is True
    assert len(report["return_states"]) == 1
    assert len(report["reachable_instructions"]) == 5

    branch_clobber = bytes.fromhex("a00000b4fe4fbfa9f30301aafe4fc1a8c0035fd6f30300aac0035fd6")
    report = analyze_stack_register_restore(branch_clobber, 0, len(branch_clobber), "x19")
    assert report["preservation_proven"] is False
    assert report["all_return_paths_restore_entry_register"] is False

    unbalanced = bytes.fromhex("fe4fbfa9f30300aafe4fc0a8c0035fd6")
    report = analyze_stack_register_restore(unbalanced, 0, len(unbalanced), "x19")
    assert report["all_return_paths_restore_entry_register"] is True
    assert report["sp_balanced_on_all_returns"] is False
    assert report["preservation_proven"] is False


    # The caller passes an SP-relative object pointer through X0. A nested
    # callee may write through that pointer only when the exact range is
    # proven disjoint from the saved incoming-X19 slot.
    def put(code, address, word):
        struct.pack_into("<I", code, address, word)

    def bl_word(site, target):
        delta = target - site
        assert delta % 4 == 0
        return 0x94000000 | ((delta >> 2) & 0x03ffffff)

    nested = bytearray(0x400)
    put(nested, 0x00, 0xA9BF4FFE)  # stp x30, x19, [sp, #-0x10]!
    put(nested, 0x04, 0xAA0003F3)  # mov x19, x0
    put(nested, 0x08, bl_word(0x08, 0x100))
    put(nested, 0x0c, 0xF9001268)  # str x8, [x19, #0x20]
    put(nested, 0x10, 0xA8C14FFE)  # ldp x30, x19, [sp], #0x10
    put(nested, 0x14, 0xD65F03C0)  # ret
    put(nested, 0x100, 0xF9001008) # str x8, [x0, #0x20]
    put(nested, 0x104, 0xD65F03C0)
    report = analyze_stack_register_restore(
        bytes(nested), 0, 0x200, "x19",
        initial_register_offsets={"x0": 0x30},
    )
    assert report["preservation_proven"] is True
    assert report["sp_balanced_on_all_returns"] is True
    assert report["sp_delta_trusted_on_all_returns"] is True
    assert report["unknown_memory_writes_while_saved"] == []
    assert report["protected_slot_clobbers"] == []
    assert report["nested_call_proofs"][0]["preserved"] is True

    # Exact overlap with the saved slot is rejected through a nested pointer.
    overlap = bytearray(nested)
    put(overlap, 0x100, 0xF9000008)  # str x8, [x0], X0 == entry SP - 8
    report = analyze_stack_register_restore(
        bytes(overlap), 0, 0x200, "x19",
        initial_register_offsets={"x0": -8},
    )
    assert report["preservation_proven"] is False
    assert report["nested_call_proofs"][0]["preserved"] is False
    assert report["nested_call_proofs"][0]["reason"] == "PROTECTED_CALLER_STACK_SLOT_CLOBBERED"

    # A one-byte write into the last byte of the protected slot is also rejected.
    partial = bytearray(nested)
    put(partial, 0x100, 0x3900001F)  # strb wzr, [x0], X0 == entry SP - 1
    report = analyze_stack_register_restore(
        bytes(partial), 0, 0x200, "x19",
        initial_register_offsets={"x0": -1},
    )
    assert report["preservation_proven"] is False
    assert report["nested_call_proofs"][0]["protected_slot_clobber_count"] == 1

    # Pair stores use the full 16-byte range; the second XZR element overlaps.
    pair = bytearray(nested)
    put(pair, 0x100, 0xA9007C1F)  # stp xzr, xzr, [x0], X0 == entry SP - 0x10
    report = analyze_stack_register_restore(
        bytes(pair), 0, 0x200, "x19",
        initial_register_offsets={"x0": -0x10},
    )
    assert report["preservation_proven"] is False
    assert report["nested_call_proofs"][0]["protected_slot_clobber_count"] == 1

    # A write beginning exactly after the protected 8-byte slot is disjoint.
    boundary = bytearray(nested)
    put(boundary, 0x100, 0xF9000008)  # str x8, [x0], X0 == entry SP
    report = analyze_stack_register_restore(
        bytes(boundary), 0, 0x200, "x19",
        initial_register_offsets={"x0": 0},
    )
    assert report["preservation_proven"] is True

    # Unknown pointer provenance and an unbalanced nested stack remain barriers.
    unknown = analyze_stack_register_restore(bytes(nested), 0, 0x200, "x19")
    assert unknown["preservation_proven"] is False
    assert unknown["nested_call_proofs"][0]["preserved"] is False

    unbalanced = bytearray(nested)
    put(unbalanced, 0x100, 0xD10043FF)  # sub sp, sp, #0x10
    put(unbalanced, 0x104, 0xD65F03C0)
    report = analyze_stack_register_restore(
        bytes(unbalanced), 0, 0x200, "x19",
        initial_register_offsets={"x0": 0x30},
    )
    assert report["preservation_proven"] is False
    assert report["nested_call_proofs"][0]["sp_balanced_on_all_returns"] is False

    # A nested direct-call cycle is never accepted.
    cycle = bytearray(nested)
    put(cycle, 0x100, bl_word(0x100, 0x00))
    put(cycle, 0x104, 0xD65F03C0)
    report = analyze_stack_register_restore(
        bytes(cycle), 0, 0x200, "x19",
        initial_register_offsets={"x0": 0x30},
    )
    assert report["preservation_proven"] is False
    assert report["nested_call_proofs"][0]["reason"] == "NESTED_CALL_STACK_EFFECT_UNPROVEN"

    for start, end in ((1, 16), (0, 15), (0, len(good) + 4)):
        try:
            analyze_stack_register_restore(good, start, end, "x19")
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid stack-restore window was accepted")


def run(main, output):
    synthetic()
    synthetic_x19_call_preservation()
    synthetic_direct_bl_inventory()
    synthetic_x19_stack_restore()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert report["incoming_direct_call_count"] == 1
    assert report["incoming_direct_calls"][0]["source"] == hex(CALLSITE)
    assert report["incoming_direct_calls"][0]["kind"] == "BL"
    caller = report["caller_window"]
    assert caller["tracked_registers"] == ["x0", "x1", "x2", "x19"]
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
    x0_input = caller["call_input_register_origins"]["0x116f280"]["x0"]
    assert len(x0_input) == 1
    assert x0_input[0]["at"] == "0x116f278"
    assert x0_input[0]["instruction"]["word_le"] == "e0c30091"
    assert x0_input[0]["stack_relative_offset"] == 0x30
    assert report["fileload_predecessor_call"]["initial_register_offsets"] == {"x0": 0x30}
    assert report["caller_x19_numeric_value_proven"] is False
    assert report["caller_x19_pointer_type_verified"] is False
    x19_sink_call = next(x for x in report["caller_call_preservation_proofs"]
                         if x["site"] == "0x116f280")
    assert x19_sink_call["target"] == "0x120a6c8"
    stack_restore = x19_sink_call["proof"]["stack_restore_analysis"]
    assert stack_restore["initial_register_offsets"] == {"x0": 0x30}
    assert len(stack_restore["reachable_instructions"]) == 25
    assert stack_restore["nested_calls"] == [
        {"site": "0x120a6d0", "target": "0x116b698"},
        {"site": "0x120a6e8", "target": "0x1188104"},
        {"site": "0x120a6f0", "target": "0x1170f7c"},
        {"site": "0x120a6f8", "target": "0x1160c64"},
    ]
    assert len(stack_restore["nested_call_proofs"]) == 4
    assert x19_sink_call["proof"]["preserved"] == stack_restore["preservation_proven"]
    assert isinstance(stack_restore["preservation_proven"], bool)
    if stack_restore["preservation_proven"]:
        assert stack_restore["all_return_paths_restore_entry_register"] is True
        assert stack_restore["sp_balanced_on_all_returns"] is True
        assert stack_restore["sp_delta_trusted_on_all_returns"] is True
        assert stack_restore["unknown_memory_writes_while_saved"] == []
        assert stack_restore["protected_slot_clobbers"] == []
        assert all(x["preserved"] for x in stack_restore["nested_call_proofs"])
        assert not any(x["kind"] == "call_barrier" and x["at"] == "0x116f280"
                       for x in caller["possible_reaching_definitions"]["x19"])
    else:
        assert any(x["kind"] == "call_barrier" and x["at"] == "0x116f280"
                   for x in caller["possible_reaching_definitions"]["x19"])
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
