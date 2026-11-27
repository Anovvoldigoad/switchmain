"""Synthetic decoder and SHA-pinned original-main FileLoad guard regressions."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from portlib.native_fileload_guard_state import (
    MAIN_SHA256,
    _classify_range,
    _decode_adrp_add_words,
    _decode_adrp_ldr_words,
    _decode_adrp_page,
    inspect,
)


def expect_reject(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError(label + " was accepted")


def synthetic_decoders():
    pc = 0x116B7D4
    assert _decode_adrp_add_words(
        pc, 0xD0019033, 0x911F6273, 19
    ) == 0x43717D8
    assert _decode_adrp_ldr_words(
        0x116B7FC, 0xD0007F80, 0xF9415800, 0
    ) == (0x215D2B0, 0)

    # Negative ADRP page deltas must be sign-extended, not treated as unsigned.
    negative_pc = 0x200000
    target_page = 0x1000
    delta = (target_page - (negative_pc & ~0xFFF)) >> 12
    imm21 = delta & ((1 << 21) - 1)
    adrp = (0x90000000 | ((imm21 & 3) << 29)
            | (((imm21 >> 2) & 0x7FFFF) << 5) | 5)
    page, rd = _decode_adrp_page(adrp, negative_pc)
    assert (page, rd) == (target_page, 5)
    add = 0x91000000 | (0x123 << 10) | (5 << 5) | 5
    assert _decode_adrp_add_words(negative_pc, adrp, add, 5) == 0x1123

    expect_reject(
        lambda: _decode_adrp_add_words(pc, 0xD0019033, 0x911F6272, 19),
        "ADRP/ADD destination mismatch",
    )
    expect_reject(
        lambda: _decode_adrp_add_words(pc, 0xD0019033, 0x915F6273, 19),
        "shifted ADD after ADRP",
    )
    expect_reject(
        lambda: _decode_adrp_add_words(pc, 0x91000000, 0x911F6273, 19),
        "non-ADRP instruction",
    )
    expect_reject(
        lambda: _decode_adrp_ldr_words(
            0x116B7FC, 0xD0007F80, 0xF9415800, 1
        ),
        "ADRP/LDR base mismatch",
    )


def synthetic_regions():
    regions = [("data", 0x1000, 0x1100), ("bss", 0x1100, 0x1200)]
    assert _classify_range(0x1000, 1, regions) == "data"
    assert _classify_range(0x11F8, 8, regions) == "bss"
    assert _classify_range(0x11FF, 1, regions) == "bss"
    assert _classify_range(0x1200, 1, regions) == "outside_main_image"
    assert _classify_range(0x11FC, 8, regions) == "crosses_image_region_boundary"
    expect_reject(lambda: _classify_range(0x1000, 0, regions), "zero-width range")
    expect_reject(lambda: _classify_range(-1, 1, regions), "negative address")


def run(main, output):
    synthetic_decoders()
    synthetic_regions()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256

    guard = report["guarded_object_candidate"]
    assert guard["guard_address"] == "0x43717d8"
    assert guard["guard_region"] == "bss"
    assert guard["static_object_address"] == "0x43717e0"
    assert guard["static_object_region"] == "bss"
    assert guard["early_return_x0_address"] == guard["late_return_x0_address"]
    assert guard["object_extent"] == {
        "start": "0x43717e0", "end_exclusive": "0x4371800",
        "width": 0x20, "region": "bss",
    }
    assert guard["explicit_stores_all_in_bss"] is True
    assert [(row["address"], row["width"], row["region"])
            for row in guard["explicit_stores"]] == [
        ("0x43717e0", 8, "bss"),
        ("0x43717e8", 16, "bss"),
        ("0x43717f8", 8, "bss"),
    ]
    assert guard["acquire_import"]["symbol"] == "__cxa_guard_acquire"
    assert guard["release_import"]["symbol"] == "__cxa_guard_release"
    assert guard["acquire_import"]["argument_register_value"] == "0x43717d8"
    assert guard["release_import"]["argument_register_value"] == "0x43717d8"

    registration = report["registration_helper_candidate"]
    helper = registration["helper_observed"]
    assert registration["target"] == "0x290"
    assert registration["register_setup"]["x0"]["cell"] == "0x215d2b0"
    assert registration["register_setup"]["x1"]["value_at_callsite"] == "0x43717e0"
    assert registration["register_setup"]["x2"]["value_at_callsite"] == "0x1eb3000"
    assert helper["atomic_counter_address"] == "0x21620d8"
    assert helper["table_base_pointer_cell"]["address"] == "0x2143460"
    assert helper["table_limit_pointer_cell"]["address"] == "0x2143468"
    assert helper["record_stride_bytes"] == 24
    assert helper["stored_value_registers"] == ["x8", "x1", "x2"]
    assert helper["semantic_identity_verified"] is False
    assert helper["callback_identity_verified"] is False
    assert helper["destructor_identity_verified"] is False
    assert helper["table_pointer_values_runtime_resolved"] is False

    limits = report["stack_and_abi_limits"]
    assert limits["explicit_guarded_object_stores_proven_in_main_bss"] is True
    assert limits["explicit_guarded_object_stores_do_not_address_parent_entry_sp_minus_8"] is True
    assert limits["opaque_guard_import_side_effects_resolved"] is False
    assert limits["registration_helper_table_target_resolved"] is False
    for key in (
        "parent_x19_stack_preservation_proven",
        "native_consumer_abi_verified",
        "ownership_lifecycle_async_rollback_unbind_destructor_verified",
        "archive_precedence_verified",
        "safe_new_hook_abi_proven",
        "native_hook_added",
        "gameplay_verified",
        "full_moddingapi",
        "ready_for_gameplay_test",
        "emulator_tested",
    ):
        assert limits[key] is False

    mutated = bytearray(raw)
    mutated[0] ^= 1
    expect_reject(lambda: inspect(bytes(mutated)), "mutated original main")

    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_guard_state.json").write_text(
        json.dumps(report, indent=2) + "\n"
    )
    print(
        "PINNED_FILELOAD_GUARD_STATE_PASS",
        guard["guard_address"], guard["static_object_address"],
        "explicit_bss_stores", len(guard["explicit_stores"]),
        "registration_stride", helper["record_stride_bytes"],
        "NO_ABI_NO_DESTRUCTOR_CLAIM",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
