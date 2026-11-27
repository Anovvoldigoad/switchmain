"""Resolve exact FileLoad PLT/GOT slots to original NSO dynamic symbols.

A relocation-backed symbol name is not proof of runtime binding, the imported
implementation, lock semantics, object lifetime, or a safe hook ABI.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_cpk_indirect import adrp_add_target, adrp_ldr_slot
from .native_fileopen_import import _read_image, _scan_relocations, _symbol, _tags

PLT_SPECS = {
    "thread_context_provider": {
        "callsite": 0x1158C9C,
        "plt": 0x12F4CF0,
        "expected_words": (0xD0007270, 0xF9451611, 0x9128A210, 0xD61F0220),
    },
    "lock_primitive_import": {
        "callsite": 0x12A35B8,
        "plt": 0x12F4D90,
        "expected_words": (0xD0007270, 0xF9453E11, 0x9129E210, 0xD61F0220),
    },
    "unlock_primitive_import": {
        "callsite": 0x12A35C0,
        "plt": 0x12F4DA0,
        "expected_words": (0xD0007270, 0xF9454211, 0x912A0210, 0xD61F0220),
    },
    "thread_token_provider": {
        "callsite": 0x1158CA4,
        "plt": 0x12F50E0,
        "expected_words": (0xB0007270, 0xF9461211, 0x91308210, 0xD61F0220),
    },
    "fileload_nested_import_0x116b7e0": {
        "callsite": 0x116B7E0,
        "plt": 0x12F3690,
        "expected_words": (0xD0007270, 0xF9477E11, 0x913BE210, 0xD61F0220),
    },
    "fileload_nested_import_0x116b818": {
        "callsite": 0x116B818,
        "plt": 0x12F36A0,
        "expected_words": (0xD0007270, 0xF9478211, 0x913C0210, 0xD61F0220),
    },
}

SERVICE_WRAPPERS = {
    "lock_primitive_import": (0x12A35B4, 0x12F4D90),
    "unlock_primitive_import": (0x12A35BC, 0x12F4DA0),
}


def _word(text, at):
    if at < 0 or at + 4 > len(text) or at % 4:
        raise ValueError("Instruction address outside aligned original text")
    return struct.unpack_from("<I", text, at)[0]


def _decode_plt(text, pc, expected_words):
    if len(expected_words) != 4:
        raise ValueError("AArch64 PLT thunk must contain four words")
    words = tuple(_word(text, pc + i * 4) for i in range(4))
    if words != tuple(expected_words):
        raise ValueError("Pinned PLT instruction words changed at " + hex(pc))
    if (words[0] & 31) != 16 or (words[1] & 31) != 17:
        raise ValueError("PLT ADRP/LDR registers are not X16/X17")
    slot = adrp_ldr_slot(words[0], words[1], pc)
    if slot is None or adrp_add_target(words[0], words[2], pc) != slot:
        raise ValueError("PLT GOT slot materialization is inconsistent")
    if words[3] != 0xD61F0220:  # br x17
        raise ValueError("PLT thunk does not branch through X17")
    return slot, words


def _require_branch(text, at, kind, target):
    decoded = direct_branch(_word(text, at), at)
    if decoded != (kind, target):
        raise ValueError("Pinned direct branch changed at " + hex(at))


def _resolve_slot(memory, tags, slot):
    rows = _scan_relocations(memory, tags, slot)
    if len(rows) > 1:
        raise ValueError("Ambiguous dynamic relocations for PLT GOT slot " + hex(slot))
    if not rows:
        return {"slot": hex(slot), "relocation": None, "symbol": None,
                "resolution": "NO_DYNAMIC_RELOCATION_FOUND"}
    relocation = rows[0]
    symbol = _symbol(memory, tags, relocation["symbol_index"])
    resolved = (relocation["type_name"] in
                ("R_AARCH64_JUMP_SLOT", "R_AARCH64_GLOB_DAT") and
                bool(symbol.get("name")))
    return {"slot": hex(slot), "relocation": relocation,
            "symbol": symbol,
            "resolution": "DYNAMIC_SYMBOL_NAME_RESOLVED" if resolved
                          else "RELOCATION_PRESENT_SYMBOL_UNRESOLVED"}


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows, memory = _read_image(nso)
    if not rows or rows[0][0] != 0:
        raise ValueError("Original NSO text segment is not based at zero")
    text = rows[0][1]

    # The two providers are called directly by the exact wrapper. The local
    # lock/unlock adapters first dereference their object argument, then tail
    # branch to the two imported PLT thunks.
    _require_branch(text, 0x1158C9C, "BL", 0x12F4CF0)
    _require_branch(text, 0x1158CA4, "BL", 0x12F50E0)
    _require_branch(text, 0x116B7E0, "BL", 0x12F3690)
    _require_branch(text, 0x116B818, "BL", 0x12F36A0)
    _require_branch(text, 0x1158CBC, "BL", 0x12A35B4)
    _require_branch(text, 0x1158D08, "B", 0x12A35BC)
    _require_branch(text, 0x1158D2C, "B", 0x12A35BC)
    wrappers = {}
    for role, (entry, plt) in SERVICE_WRAPPERS.items():
        if _word(text, entry) != 0xF9400000:  # ldr x0, [x0]
            raise ValueError("Pinned service adapter load changed at " + hex(entry))
        _require_branch(text, entry + 4, "B", plt)
        wrappers[role] = {"entry": hex(entry), "load_word_le": text[entry:entry+4].hex(),
                          "tail_branch": hex(plt), "pointer_dereference_verified": True}

    tags = _tags(memory)
    imports = {}
    for role, spec in PLT_SPECS.items():
        slot, _ = _decode_plt(text, spec["plt"], spec["expected_words"])
        resolution = _resolve_slot(memory, tags, slot)
        imports[role] = {
            "callsite": hex(spec["callsite"]),
            "callsite_kind": "BL" if role in
                ("thread_context_provider", "thread_token_provider",
                 "fileload_nested_import_0x116b7e0",
                 "fileload_nested_import_0x116b818") else "B",
            "plt": hex(spec["plt"]),
            "plt_words_le": [text[spec["plt"] + i*4:spec["plt"] + i*4 + 4].hex()
                             for i in range(4)],
            "plt_window_sha256": hashlib.sha256(text[spec["plt"]:spec["plt"]+16]).hexdigest(),
            "got_slot": hex(slot),
            "relocation": resolution["relocation"],
            "symbol": resolution["symbol"],
            "resolution": resolution["resolution"],
            "plt_add_and_ldr_address_agree": True,
            "branches_through_x17": True,
        }

    edge_targets = {spec["plt"] for spec in PLT_SPECS.values()}
    edge_targets.update(entry for entry, _ in SERVICE_WRAPPERS.values())
    incoming = {target: [] for target in edge_targets}
    for pc in range(0, len(text) - 3, 4):
        decoded = direct_branch(struct.unpack_from("<I", text, pc)[0], pc)
        if decoded and decoded[1] in incoming:
            incoming[decoded[1]].append({"caller": hex(pc), "kind": decoded[0]})
    required_incoming = {
        0x12F4CF0: (0x1158C9C, "BL"),
        0x12F50E0: (0x1158CA4, "BL"),
        0x12A35B4: (0x1158CBC, "BL"),
        0x12A35BC: (0x1158D2C, "B"),
    }
    for target, (caller, kind) in required_incoming.items():
        if not any(edge["caller"] == hex(caller) and edge["kind"] == kind
                   for edge in incoming[target]):
            raise ValueError("Expected original service incoming edge missing at " + hex(caller))

    return {
        "status": "SHA_PINNED_FILELOAD_PLT_GOT_IMPORT_EVIDENCE_ONLY",
        "original_main_sha256": digest,
        "service_wrapper_callsites_verified": True,
        "service_wrappers": wrappers,
        "imports": imports,
        "incoming_direct_edges": {hex(k): v for k, v in incoming.items()},
        "symbol_names_are_dynamic_relocation_evidence_only": True,
        "imported_implementations_proven": False,
        "runtime_import_binding_verified": False,
        "thread_context_provider_semantics_verified": False,
        "thread_token_provider_semantics_verified": False,
        "mutex_lock_unlock_semantics_verified": False,
        "concurrent_behavior_verified": False,
        "native_consumer_abi_verified": False,
        "ownership_lifecycle_async_rollback_unbind_destructor_verified": False,
        "archive_precedence_verified": False,
        "safe_new_hook_abi_proven": False,
        "native_hook_added": False,
        "gameplay_verified": False,
        "full_moddingapi": False,
        "ready_for_gameplay_test": False,
        "emulator_tested": False,
    }
