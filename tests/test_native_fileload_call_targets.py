"""Pinned FileLoad direct-callee register-effect inventory regressions."""
import argparse
import json
import sys
from pathlib import Path

R = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(R / "tools"))
from portlib.native_cpk_graph import MAIN_SHA256
from portlib.native_fileload_call_targets import analyze_window, inspect


def _words(*values):
    return b"".join(x.to_bytes(4, "little") for x in values)


def synthetic():
    # STP X20/X22 -> overwrite X20 -> opaque BL -> LDP X20/X22 -> RET.
    good = analyze_window(_words(
        0xA9015BF4,  # stp x20, x22, [sp, #0x10]
        0xAA0103F4,  # mov x20, x1
        0x94000040,  # bl outside this bounded window; fallthrough remains
        0xA9415BF4,  # ldp x20, x22, [sp, #0x10]
        0xD65F03C0,  # ret
    ), 0, 20)
    assert good["return_sites"] == ["0x10"]
    assert good["nested_direct_calls"] == [{"site": "0x8", "target": "0x108"}]
    for reg in ("x20", "x22"):
        assert good["register_effects"][reg]["same_displacement_stack_store_load_candidates"] == [
            {"store_pc": "0x0", "load_pc": "0xc", "sp_displacement": 16}
        ]
        assert good["register_effects"][reg]["preservation_proven"] is False

    # A different stack displacement is not a matching restore candidate.
    mismatch = analyze_window(_words(
        0xA9015BF4,  # stp x20, x22, [sp, #0x10]
        0xA941DBF4,  # ldp x20, x22, [sp, #0x18]
        0xD65F03C0,
    ), 0, 12)
    assert mismatch["register_effects"]["x20"]["same_displacement_stack_store_load_candidates"] == []
    assert mismatch["register_effects"]["x22"]["same_displacement_stack_store_load_candidates"] == []

    # A store through X0 is not mislabeled as a current-SP save.
    nonstack = analyze_window(_words(
        0xF9000814,  # str x20, [x0, #0x10]
        0xD65F03C0,
    ), 0, 8)
    assert nonstack["register_effects"]["x20"]["same_displacement_stack_store_load_candidates"] == []
    assert nonstack["register_effects"]["x20"]["stack_accesses"][0]["base_register"] == "x0"

    # Pre/post-indexed stack accesses are inventoried but not matched by raw displacement.
    writeback = analyze_window(_words(
        0xA9BE5BF4,  # stp x20, x22, [sp, #-0x20]!
        0xA8C25BF4,  # ldp x20, x22, [sp], #0x20
        0xD65F03C0,
    ), 0, 12)
    assert all(x["writeback"] for x in writeback["register_effects"]["x20"]["stack_accesses"])
    assert writeback["register_effects"]["x20"]["same_displacement_stack_store_load_candidates"] == []

    # Out-of-window branches and indirect terminals remain explicit unknowns.
    outside = analyze_window(_words(0x14000040, 0xD65F03C0), 0, 8)
    assert outside["other_or_out_of_window_exits"] == [
        {"from": "0x0", "kind": "jump", "target": "0x100"}
    ]
    indirect = analyze_window(_words(0xD61F0060, 0xD65F03C0), 0, 8)
    assert indirect["indirect_terminators"] == ["0x0"]

    try:
        analyze_window(b"\x00\x00", 0, 2)
    except ValueError:
        pass
    else:
        raise AssertionError("Accepted a partial ARM64 instruction window")


def run(main, output):
    synthetic()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    tampered = bytearray(raw)
    tampered[0] ^= 1
    try:
        inspect(bytes(tampered))
    except ValueError as exc:
        assert "SHA256" in str(exc)
    else:
        raise AssertionError("Accepted a mutated original-main image")
    expected = [
        ("0x116f43c", "0x116d3c0"),
        ("0x116f444", "0x11708d8"),
        ("0x116f458", "0x11709a0"),
        ("0x116f45c", "0x116d420"),
        ("0x116f47c", "0x1170fb0"),
        ("0x116f48c", "0x11705f0"),
        ("0x116f49c", "0x130b8"),
        ("0x116f4e0", "0x12155a0"),
        ("0x116f4f8", "0x12155a0"),
        ("0x116f504", "0x12155a0"),
        ("0x116f514", "0x12155a0"),
    ]
    assert [(x["site"], x["target"]) for x in report["pre_status_direct_calls"]] == expected
    assert len(report["target_reports"]) == 8
    assert all(x["bounded_window_not_function_extent"] for x in report["target_reports"])
    assert all(not x["preservation_proven"] for x in report["target_reports"])
    assert report["register_preservation_proven"] is False
    assert report["consumer_abi_proven"] is False
    assert report["object_ownership_lifetime_proven"] is False
    assert report["archive_precedence_proven"] is False
    assert report["native_hook_installed"] is False
    assert report["gameplay_verified"] is False
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_call_targets.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print("PINNED_FILELOAD_DIRECT_CALLEE_INVENTORY_PASS",
          len(report["pre_status_direct_calls"]), "calls",
          len(report["unique_pre_status_targets"]), "targets",
          "NO_ABI_NO_OWNERSHIP")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    run(args.main, args.output)
