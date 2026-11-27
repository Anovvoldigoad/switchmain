"""Synthetic PLT/GOT and pinned original FileLoad import evidence tests."""
import argparse
import json
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from portlib.native_fileload_imports import (
    MAIN_SHA256, PLT_SPECS, _decode_plt, _resolve_slot, inspect
)
from portlib.native_fileopen_import import _symbol


def synthetic_plt():
    expected_slots = {
        "thread_context_provider": 0x2142A28,
        "lock_primitive_import": 0x2142A78,
        "unlock_primitive_import": 0x2142A80,
        "thread_token_provider": 0x2142C20,
        "fileload_nested_import_0x116b7e0": 0x2141EF8,
        "fileload_nested_import_0x116b818": 0x2141F00,
    }
    for role, spec in PLT_SPECS.items():
        text = bytearray(spec["plt"] + 16)
        struct.pack_into("<4I", text, spec["plt"], *spec["expected_words"])
        slot, _ = _decode_plt(text, spec["plt"], spec["expected_words"])
        assert slot == expected_slots[role], (role, hex(slot))

    spec = PLT_SPECS["thread_context_provider"]
    for index, replacement in ((1, 0xF9451610), (2, 0x9128A230), (3, 0xD61F0200)):
        bad_words = list(spec["expected_words"])
        bad_words[index] = replacement
        bad = bytearray(spec["plt"] + 16)
        struct.pack_into("<4I", bad, spec["plt"], *bad_words)
        try:
            _decode_plt(bad, spec["plt"], tuple(bad_words))
        except ValueError:
            pass
        else:
            raise AssertionError("Semantically malformed PLT thunk accepted at word " + str(index))
    text = bytearray(spec["plt"] + 16)
    struct.pack_into("<4I", text, spec["plt"], *spec["expected_words"])
    try:
        _decode_plt(text, spec["plt"] + 4, spec["expected_words"])
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-range PLT thunk accepted")


def synthetic_relocations():
    memory = bytearray(1024)
    strings = b"\0xxx\0pthread_mutex_lock\0"
    memory[280:280 + len(strings)] = strings
    struct.pack_into("<IBBHQQ", memory, 120 + 24, 5, 0x12, 0, 0, 0, 0)
    slot = 0x2142A78
    struct.pack_into("<QQq", memory, 400, slot, (1 << 32) | 1026, 0)
    tags = {6: 120, 5: 280, 10: len(strings), 11: 24,
            23: 400, 2: 24, 20: 7}
    resolved = _resolve_slot(memory, tags, slot)
    assert resolved["resolution"] == "DYNAMIC_SYMBOL_NAME_RESOLVED"
    assert resolved["symbol"]["name"] == "pthread_mutex_lock"
    assert resolved["relocation"]["type_name"] == "R_AARCH64_JUMP_SLOT"
    assert _symbol(memory, tags, 0)["name"] is None
    assert _resolve_slot(memory, tags, slot + 8)["symbol"] is None
    glob_dat = bytearray(memory)
    struct.pack_into("<QQq", glob_dat, 400, slot, (1 << 32) | 1025, 0)
    assert _resolve_slot(glob_dat, tags, slot)["resolution"] == "DYNAMIC_SYMBOL_NAME_RESOLVED"
    unknown_type = bytearray(memory)
    struct.pack_into("<QQq", unknown_type, 400, slot, (1 << 32) | 9999, 0)
    assert _resolve_slot(unknown_type, tags, slot)["resolution"] == "RELOCATION_PRESENT_SYMBOL_UNRESOLVED"

    duplicate = bytearray(memory)
    struct.pack_into("<QQq", duplicate, 424, slot, (1 << 32) | 1026, 0)
    duplicate_tags = dict(tags)
    duplicate_tags[2] = 48
    try:
        _resolve_slot(duplicate, duplicate_tags, slot)
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate relocation for one GOT slot accepted")

    invalid = dict(tags)
    invalid[20] = 17
    try:
        _resolve_slot(memory, invalid, slot)
    except ValueError:
        pass
    else:
        raise AssertionError("Non-RELA PLT table accepted")

    bad_symbol = dict(tags)
    bad_symbol[10] = 5
    try:
        _symbol(memory, bad_symbol, 1)
    except ValueError:
        pass
    else:
        raise AssertionError("Out-of-range dynamic symbol name accepted")


def run(main, output):
    synthetic_plt()
    synthetic_relocations()
    raw = main.read_bytes()
    report = inspect(raw)
    assert report["original_main_sha256"] == MAIN_SHA256
    assert len(report["imports"]) == 6
    assert report["service_wrapper_callsites_verified"]
    assert report["imports"]["thread_context_provider"]["got_slot"] == "0x2142a28"
    assert report["imports"]["lock_primitive_import"]["got_slot"] == "0x2142a78"
    assert report["imports"]["unlock_primitive_import"]["got_slot"] == "0x2142a80"
    assert report["imports"]["thread_token_provider"]["got_slot"] == "0x2142c20"
    for role, callsite, plt, slot in (
        ("fileload_nested_import_0x116b7e0", "0x116b7e0", "0x12f3690", "0x2141ef8"),
        ("fileload_nested_import_0x116b818", "0x116b818", "0x12f36a0", "0x2141f00"),
    ):
        item = report["imports"][role]
        assert item["callsite"] == callsite
        assert item["callsite_kind"] == "BL"
        assert item["plt"] == plt
        assert item["got_slot"] == slot
        assert item["resolution"] == "DYNAMIC_SYMBOL_NAME_RESOLVED"
        assert item["symbol"]["name"]
    for key in ("imported_implementations_proven", "runtime_import_binding_verified",
                "thread_context_provider_semantics_verified",
                "thread_token_provider_semantics_verified",
                "mutex_lock_unlock_semantics_verified", "concurrent_behavior_verified",
                "native_consumer_abi_verified",
                "ownership_lifecycle_async_rollback_unbind_destructor_verified",
                "archive_precedence_verified", "safe_new_hook_abi_proven",
                "native_hook_added", "gameplay_verified", "full_moddingapi",
                "ready_for_gameplay_test", "emulator_tested"):
        assert report[key] is False
    bad = bytearray(raw)
    bad[0] ^= 1
    try:
        inspect(bytes(bad))
    except ValueError:
        pass
    else:
        raise AssertionError("Mutated original main passed SHA guard")
    output.mkdir(parents=True, exist_ok=True)
    (output / "native_fileload_imports.json").write_text(json.dumps(report, indent=2) + "\n")
    names = {k: v["symbol"]["name"] if v["symbol"] else None
             for k, v in report["imports"].items()}
    print("PINNED_FILELOAD_PLT_GOT_IMPORTS_PASS", names,
          "NO_IMPLEMENTATION_BINDING_OR_ABI")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--main", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.main, args.output)
