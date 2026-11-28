"""Read-only DWARF .eh_frame_hdr / .eh_frame evidence for pinned Switch v1.70.

FDE ranges are unwind coverage ranges, not proof of a C++ function identity,
callback ABI, ownership, destructor, or permission to install a hook.
"""
import hashlib
import struct

from .native_cpk_graph import MAIN_SHA256, direct_branch
from .native_fileload_helper_callers import inspect as inspect_callers
from .nso_profile import segments

MAX_RECORD_BYTES = 1 << 20
MAX_FDE_COUNT = 250000
MAX_CIE_SCAN = 1000000
MIN_LINEAR_FDE_CLUSTER = 8
POINTER_SIZE = 8
TABLE_PATH_CALLS = (0x116B8A4, 0x116B928)
ANALYSIS_ANCHORS = {
    "fileload_helper_entry": 0x116B390,
    "fileload_helper_br_x2": 0x116B3D0,
    "registration_walk_candidate": 0x116B888,
    "second_table_path_range_start": 0x116B90C,
}


def _u(data, offset, size):
    if offset < 0 or size <= 0 or offset + size > len(data):
        raise ValueError("Encoded field outside segment")
    return int.from_bytes(data[offset:offset + size], "little", signed=False)


def _s(data, offset, size):
    if offset < 0 or size <= 0 or offset + size > len(data):
        raise ValueError("Encoded field outside segment")
    return int.from_bytes(data[offset:offset + size], "little", signed=True)


def _uleb(data, offset, limit=None):
    end = len(data) if limit is None else min(len(data), limit)
    value = shift = 0
    for _ in range(10):
        if offset >= end:
            raise ValueError("Truncated ULEB128")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, offset
        shift += 7
    raise ValueError("Oversized ULEB128")


def _sleb(data, offset, limit=None):
    end = len(data) if limit is None else min(len(data), limit)
    value = shift = 0
    byte = 0
    for _ in range(10):
        if offset >= end:
            raise ValueError("Truncated SLEB128")
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        shift += 7
        if not byte & 0x80:
            if shift < 64 and byte & 0x40:
                value |= -(1 << shift)
            return value, offset
    raise ValueError("Oversized SLEB128")


def _record(data, offset):
    length32 = _u(data, offset, 4)
    if length32 == 0:
        return None
    if length32 == 0xffffffff:
        length = _u(data, offset + 4, 8)
        header_size = 12
        id_size = 8
    else:
        length = length32
        header_size = 4
        id_size = 4
    if not 0 < length <= MAX_RECORD_BYTES:
        raise ValueError("DWARF record length outside bound")
    end = offset + header_size + length
    if end > len(data) or offset + header_size + id_size > end:
        raise ValueError("DWARF record exceeds segment")
    return {
        "offset": offset,
        "header_size": header_size,
        "id_size": id_size,
        "body_offset": offset + header_size,
        "id_offset": offset + header_size,
        "end": end,
        "length": length,
    }


def _encoded(data, offset, encoding, field_va, datarel_base=None,
             text_base=0, pointer_size=POINTER_SIZE):
    if encoding == 0xff or encoding & 0x80:
        raise ValueError("Omitted or indirect DW_EH_PE encoding is unsupported")
    application = encoding & 0x70
    form = encoding & 0x0f
    if application == 0x50:
        raise ValueError("Aligned DW_EH_PE encoding is unsupported")
    if form == 0x00:
        value = _u(data, offset, pointer_size)
        offset += pointer_size
    elif form == 0x01:
        value, offset = _uleb(data, offset)
    elif form == 0x02:
        value = _u(data, offset, 2)
        offset += 2
    elif form == 0x03:
        value = _u(data, offset, 4)
        offset += 4
    elif form == 0x04:
        value = _u(data, offset, 8)
        offset += 8
    elif form == 0x09:
        value, offset = _sleb(data, offset)
    elif form == 0x0a:
        value = _s(data, offset, 2)
        offset += 2
    elif form == 0x0b:
        value = _s(data, offset, 4)
        offset += 4
    elif form == 0x0c:
        value = _s(data, offset, 8)
        offset += 8
    else:
        raise ValueError("Unknown DW_EH_PE value format")
    if application == 0x00:
        base = 0
    elif application == 0x10:
        base = field_va
    elif application == 0x20:
        base = text_base
    elif application == 0x30:
        if datarel_base is None:
            raise ValueError("DW_EH_PE_datarel has no proven base")
        base = datarel_base
    else:
        raise ValueError("Unknown DW_EH_PE application")
    return base + value, offset



def _skip_encoded(data, offset, encoding):
    if encoding == 0xff or (encoding & 0x70) == 0x50:
        raise ValueError("Omitted or aligned personality pointer encoding is unsupported")
    form = encoding & 0x0f
    if form == 0x00:
        return offset + POINTER_SIZE
    if form == 0x01:
        return _uleb(data, offset)[1]
    if form == 0x02:
        return offset + 2
    if form == 0x03:
        return offset + 4
    if form == 0x04:
        return offset + 8
    if form == 0x09:
        return _sleb(data, offset)[1]
    if form == 0x0a:
        return offset + 2
    if form == 0x0b:
        return offset + 4
    if form == 0x0c:
        return offset + 8
    raise ValueError("Unknown personality pointer encoding")


def _cie(data, offset, segment_va, text_va):
    record = _record(data, offset)
    if record is None or _u(data, record["id_offset"], record["id_size"]) != 0:
        raise ValueError("Not a .eh_frame CIE")
    pos = record["id_offset"] + record["id_size"]
    if pos >= record["end"]:
        raise ValueError("Truncated CIE version")
    version = data[pos]
    pos += 1
    if version not in (1, 3, 4):
        raise ValueError("Unsupported CIE version")
    nul = data.find(b"\0", pos, min(record["end"], pos + 65))
    if nul < 0:
        raise ValueError("CIE augmentation string is missing or too long")
    raw_aug = bytes(data[pos:nul])
    try:
        augmentation = raw_aug.decode("ascii")
    except UnicodeDecodeError as exc:
        raise ValueError("CIE augmentation is not ASCII") from exc
    pos = nul + 1
    address_size = POINTER_SIZE
    segment_size = 0
    if version == 4:
        address_size = _u(data, pos, 1)
        segment_size = _u(data, pos + 1, 1)
        pos += 2
        if address_size != POINTER_SIZE or segment_size != 0:
            raise ValueError("CIE address/segment size is not AArch64 flat 64-bit")
    code_alignment, pos = _uleb(data, pos, record["end"])
    data_alignment, pos = _sleb(data, pos, record["end"])
    if code_alignment == 0:
        raise ValueError("CIE code alignment is zero")
    if version == 1:
        return_register = _u(data, pos, 1)
        pos += 1
    else:
        return_register, pos = _uleb(data, pos, record["end"])

    fde_encoding = 0x00
    lsda_encoding = 0xff
    has_z_augmentation = augmentation.startswith("z")
    if has_z_augmentation:
        augmentation_size, pos = _uleb(data, pos, record["end"])
        augmentation_end = pos + augmentation_size
        if augmentation_end > record["end"]:
            raise ValueError("CIE augmentation data exceeds record")
        for item in augmentation[1:]:
            if item == "L":
                lsda_encoding = _u(data, pos, 1)
                pos += 1
            elif item == "R":
                fde_encoding = _u(data, pos, 1)
                pos += 1
            elif item == "P":
                personality_encoding = _u(data, pos, 1)
                pos += 1
                pos = _skip_encoded(data, pos, personality_encoding)
                if pos > augmentation_end:
                    raise ValueError("CIE personality pointer exceeds augmentation data")
            elif item in ("S", "B", "G"):
                continue
            else:
                raise ValueError("Unknown CIE augmentation character")
        if pos > augmentation_end:
            raise ValueError("CIE augmentation fields exceed declared length")
        pos = augmentation_end
    elif augmentation:
        raise ValueError("Non-z CIE augmentation cannot be bounded safely")

    return {
        "offset": offset,
        "virtual_address": segment_va + offset,
        "end_offset": record["end"],
        "record_bytes": record["end"] - offset,
        "version": version,
        "augmentation": augmentation,
        "code_alignment": code_alignment,
        "data_alignment": data_alignment,
        "return_register": return_register,
        "address_size": address_size,
        "segment_size": segment_size,
        "fde_encoding": fde_encoding,
        "lsda_encoding": lsda_encoding,
        "has_z_augmentation": has_z_augmentation,
        "instructions_offset": pos,
        "instructions_end_offset": record["end"],
        "instructions_sha256": hashlib.sha256(data[pos:record["end"]]).hexdigest(),
    }


def _fde(data, offset, segment_va, text_va, text_size,
         expected_cie_va=None, cie_cache=None):
    record = _record(data, offset)
    if record is None:
        raise ValueError("Zero-length terminator is not an FDE")
    cie_pointer = _u(data, record["id_offset"], record["id_size"])
    if cie_pointer == 0:
        raise ValueError("Record is a CIE, not an FDE")
    cie_field_va = segment_va + record["id_offset"]
    cie_va = cie_field_va - cie_pointer
    cie_offset = cie_va - segment_va
    if cie_offset < 0 or cie_offset >= len(data):
        raise ValueError("FDE CIE back-reference leaves segment")
    if expected_cie_va is not None and cie_va != expected_cie_va:
        raise ValueError("FDE references a different CIE")
    cache_key = cie_offset
    if cie_cache is not None and cache_key in cie_cache:
        cie = cie_cache[cache_key]
    else:
        cie = _cie(data, cie_offset, segment_va, text_va)
        if cie_cache is not None:
            cie_cache[cache_key] = cie

    pos = record["id_offset"] + record["id_size"]
    initial_location, pos = _encoded(
        data, pos, cie["fde_encoding"], segment_va + pos,
        segment_va, text_va
    )
    range_encoding = cie["fde_encoding"] & 0x0f
    address_range, pos = _encoded(
        data, pos, range_encoding, segment_va + pos,
        segment_va, text_va
    )
    if cie["has_z_augmentation"]:
        augmentation_size, pos = _uleb(data, pos, record["end"])
        if pos + augmentation_size > record["end"]:
            raise ValueError("FDE augmentation data exceeds record")
        pos += augmentation_size
    text_end = text_va + text_size
    if (address_range <= 0 or initial_location < text_va
            or initial_location >= text_end
            or initial_location + address_range > text_end):
        raise ValueError("FDE code range leaves pinned executable text")
    return {
        "fde_offset": offset,
        "fde_virtual_address": segment_va + offset,
        "fde_record_bytes": record["end"] - offset,
        "cie_offset": cie_offset,
        "cie_virtual_address": cie_va,
        "start": initial_location,
        "range": address_range,
        "end": initial_location + address_range,
        "fde_sha256": hashlib.sha256(data[offset:record["end"]]).hexdigest(),
        "cie_augmentation": cie["augmentation"],
        "fde_encoding": cie["fde_encoding"],
        "instructions_offset": pos,
        "instructions_end_offset": record["end"],
        "instructions_sha256": hashlib.sha256(data[pos:record["end"]]).hexdigest(),
        "range_is_unwind_coverage_not_function_identity": True,
    }


def _header(data, segment_va, text_va, text_size, offset):
    if offset + 4 > len(data) or data[offset] != 1:
        raise ValueError("Not a version-1 .eh_frame_hdr")
    eh_pointer_encoding = data[offset + 1]
    count_encoding = data[offset + 2]
    table_encoding = data[offset + 3]
    pos = offset + 4
    header_va = segment_va + offset
    eh_frame_va, pos = _encoded(
        data, pos, eh_pointer_encoding, segment_va + pos,
        header_va, text_va
    )
    fde_count, pos = _encoded(
        data, pos, count_encoding, segment_va + pos,
        header_va, text_va
    )
    if not 0 < fde_count <= MAX_FDE_COUNT:
        raise ValueError("EH frame header FDE count outside bound")
    if not segment_va <= eh_frame_va < segment_va + len(data):
        raise ValueError("EH frame pointer leaves scanned segment")
    if table_encoding == 0xff:
        raise ValueError("EH frame header omits the search table")
    if (table_encoding & 0x70) not in (0x00, 0x10, 0x20, 0x30):
        raise ValueError("Unsupported EH frame header table base")
    table = []
    cache = {}
    previous_start = None
    for index in range(fde_count):
        initial_location, pos = _encoded(
            data, pos, table_encoding, segment_va + pos,
            header_va, text_va
        )
        fde_va, pos = _encoded(
            data, pos, table_encoding, segment_va + pos,
            header_va, text_va
        )
        if previous_start is not None and initial_location <= previous_start:
            raise ValueError("EH frame header table is not strictly sorted")
        previous_start = initial_location
        fde_offset = fde_va - segment_va
        if fde_va < eh_frame_va or fde_offset < 0 or fde_offset >= len(data):
            raise ValueError("EH frame table FDE pointer leaves scanned segment")
        fde = _fde(data, fde_offset, segment_va, text_va, text_size,
                   cie_cache=cache)
        if fde["start"] != initial_location:
            raise ValueError("EH frame table start disagrees with its FDE")
        table.append(fde)
    return {
        "source": "GNU_EH_FRAME_HDR",
        "segment_va": hex(segment_va),
        "header_offset": hex(offset),
        "header_va": hex(header_va),
        "header_sha256": hashlib.sha256(data[offset:pos]).hexdigest(),
        "eh_frame_va": hex(eh_frame_va),
        "fde_count": fde_count,
        "pointer_encodings": {
            "eh_frame_ptr": hex(eh_pointer_encoding),
            "fde_count": hex(count_encoding),
            "table": hex(table_encoding),
        },
        "fdes": table,
    }


def _scan_headers(data, segment_va, text_va, text_size):
    valid = []
    prefix_candidates = 0
    rejected = []
    for offset in range(0, max(0, len(data) - 3), 4):
        if data[offset] != 1:
            continue
        if data[offset + 1] not in (0x00, 0x03, 0x04, 0x0b, 0x0c, 0x1b, 0x2b, 0x3b):
            continue
        if data[offset + 2] not in (0x01, 0x03, 0x04):
            continue
        if data[offset + 3] not in (0x00, 0x03, 0x04, 0x0b, 0x0c, 0x13, 0x1b, 0x23, 0x2b, 0x33, 0x3b):
            continue
        prefix_candidates += 1
        try:
            valid.append(_header(data, segment_va, text_va, text_size, offset))
        except (ValueError, IndexError, struct.error) as exc:
            if len(rejected) < 32:
                rejected.append({"offset": hex(offset), "reason": str(exc)})
    return valid, {
        "prefix_candidates": prefix_candidates,
        "rejected_sample": rejected,
    }


def _scan_linear(data, segment_va, text_va, text_size):
    candidates = []
    scanned = 0
    for offset in range(0, max(0, len(data) - 16), 4):
        if scanned >= MAX_CIE_SCAN:
            break
        if offset + 9 > len(data) or _u(data, offset, 4) < 8:
            continue
        if _u(data, offset + 4, 4) != 0:
            continue
        if data[offset + 8] not in (1, 3, 4):
            continue
        scanned += 1
        try:
            cie = _cie(data, offset, segment_va, text_va)
        except (ValueError, IndexError, struct.error):
            continue
        if cie["end_offset"] & 3:
            continue
        position = cie["end_offset"]
        fdes = []
        cache = {offset: cie}
        while position + 8 <= len(data):
            try:
                record = _record(data, position)
                if record is None:
                    break
                if _u(data, record["id_offset"], record["id_size"]) == 0:
                    break
                fde = _fde(
                    data, position, segment_va, text_va, text_size,
                    expected_cie_va=segment_va + offset,
                    cie_cache=cache,
                )
            except (ValueError, IndexError, struct.error):
                break
            fdes.append(fde)
            position = record["end"]
        if len(fdes) >= MIN_LINEAR_FDE_CLUSTER:
            candidates.append({
                "source": "LINEAR_EH_FRAME_CIE_FDE_SEQUENCE",
                "segment_va": hex(segment_va),
                "cie_offset": hex(offset),
                "cie_augmentation": cie["augmentation"],
                "fde_count": len(fdes),
                "fdes": fdes,
                "sequence_bytes": position - offset,
                "sequence_sha256": hashlib.sha256(data[offset:position]).hexdigest(),
            })
    return candidates, {"cie_candidates_scanned": scanned}


def discover_metadata(rows):
    if len(rows) != 3:
        raise ValueError("Pinned NSO must contain exactly three loadable segments")
    text_va, text, _ = rows[0]
    if text_va != 0:
        raise ValueError("Pinned AArch64 text segment base changed")
    headers = []
    linear = []
    diagnostics = []
    for index, (segment_va, data, _stored) in enumerate(rows[1:], start=1):
        found, header_diag = _scan_headers(data, segment_va, text_va, len(text))
        diagnostics.append({
            "segment_index": index,
            "segment_va": hex(segment_va),
            "segment_bytes": len(data),
            "header_scan": header_diag,
        })
        for item in found:
            item["segment_index"] = index
            headers.append(item)
    if len(headers) == 1:
        selected = headers[0]
        return {
            "status": "GNU_EH_FRAME_HDR_VALIDATED",
            "selected": selected,
            "diagnostics": diagnostics,
            "fde_records": selected["fdes"],
        }
    if len(headers) > 1:
        return {
            "status": "AMBIGUOUS_EH_FRAME_HEADERS",
            "selected": None,
            "diagnostics": diagnostics,
            "valid_header_candidates": [
                {k: v for k, v in item.items() if k != "fdes"}
                for item in headers
            ],
            "fde_records": [],
        }

    for index, (segment_va, data, _stored) in enumerate(rows[1:], start=1):
        found, linear_diag = _scan_linear(data, segment_va, text_va, len(text))
        diagnostics[index - 1]["linear_scan"] = linear_diag
        for item in found:
            item["segment_index"] = index
            linear.append(item)
    if len(linear) == 1:
        selected = linear[0]
        return {
            "status": "LINEAR_EH_FRAME_SEQUENCE_VALIDATED",
            "selected": {k: v for k, v in selected.items() if k != "fdes"},
            "diagnostics": diagnostics,
            "fde_records": selected["fdes"],
        }
    if len(linear) > 1:
        return {
            "status": "AMBIGUOUS_LINEAR_EH_FRAME_SEQUENCES",
            "selected": None,
            "diagnostics": diagnostics,
            "valid_linear_candidates": [
                {k: v for k, v in item.items() if k != "fdes"}
                for item in linear
            ],
            "fde_records": [],
        }
    return {
        "status": "NO_RELIABLE_CFI_METADATA_FOUND",
        "selected": None,
        "diagnostics": diagnostics,
        "fde_records": [],
    }


def map_callers_to_fdes(callers, fdes, text):
    mappings = []
    for caller in callers:
        site = int(caller["site"], 16)
        matches = [fde for fde in fdes if fde["start"] <= site < fde["end"]]
        if len(matches) == 1:
            fde = matches[0]
            mappings.append({
                "call_site": caller["site"],
                "branch_kind": caller["branch_kind"],
                "fde_start": hex(fde["start"]),
                "fde_end_exclusive": hex(fde["end"]),
                "fde_offset": hex(fde["fde_offset"]),
                "cie_offset": hex(fde["cie_offset"]),
                "fde_sha256": fde["fde_sha256"],
                "mapping_status": "UNIQUE_FDE_COVERAGE",
                "function_entry_identity_verified": False,
            })
        else:
            mappings.append({
                "call_site": caller["site"],
                "branch_kind": caller["branch_kind"],
                "matching_fde_count": len(matches),
                "mapping_status": "UNMAPPED" if not matches else "AMBIGUOUS",
                "function_entry_identity_verified": False,
            })

    starts = {int(row["fde_start"], 16) for row in mappings
              if row["mapping_status"] == "UNIQUE_FDE_COVERAGE"}
    inbound = {start: [] for start in starts}
    for pc in range(0, len(text) - 3, 4):
        edge = direct_branch(struct.unpack_from("<I", text, pc)[0], pc)
        if edge is not None and edge[1] in inbound:
            kind, target = edge
            inbound[target].append({"site": hex(pc), "kind": kind})
    ranges = {}
    for fde in fdes:
        if fde["start"] in starts:
            ranges[fde["start"]] = {
                "start": hex(fde["start"]),
                "end_exclusive": hex(fde["end"]),
                "range_bytes": fde["range"],
                "fde_offset": hex(fde["fde_offset"]),
                "cie_offset": hex(fde["cie_offset"]),
                "fde_sha256": fde["fde_sha256"],
                "direct_inbound_edge_count": len(inbound[fde["start"]]),
                "direct_inbound_edge_samples": inbound[fde["start"]][:32],
                "range_is_unwind_coverage_not_function_identity": True,
            }
    return mappings, sorted(ranges.values(), key=lambda row: int(row["start"], 16))



def map_addresses_to_fdes(addresses, fdes):
    rows = []
    for name, address in addresses.items():
        matches = [fde for fde in fdes
                   if fde["start"] <= address < fde["end"]]
        if len(matches) == 1:
            fde = matches[0]
            rows.append({
                "name": name,
                "address": hex(address),
                "fde_start": hex(fde["start"]),
                "fde_end_exclusive": hex(fde["end"]),
                "fde_offset": hex(fde["fde_offset"]),
                "cie_offset": hex(fde["cie_offset"]),
                "fde_sha256": fde["fde_sha256"],
                "mapping_status": "UNIQUE_FDE_COVERAGE",
                "function_entry_identity_verified": False,
            })
        else:
            rows.append({
                "name": name,
                "address": hex(address),
                "matching_fde_count": len(matches),
                "mapping_status": "UNMAPPED" if not matches else "AMBIGUOUS",
                "function_entry_identity_verified": False,
            })
    return rows




def _clone_cfi_state(state):
    return {
        "cfa": None if state["cfa"] is None else dict(state["cfa"]),
        "registers": {
            str(register): dict(rule)
            for register, rule in state["registers"].items()
        },
        "ra_state_negated": bool(state["ra_state_negated"]),
        "args_size": state["args_size"],
    }


def _default_cfi_state():
    return {
        "cfa": None,
        "registers": {},
        "ra_state_negated": False,
        "args_size": None,
    }


def _cfi_block(data, offset, end):
    length, offset = _uleb(data, offset, end)
    if offset + length > end:
        raise ValueError("DW_CFA expression exceeds its instruction program")
    value = bytes(data[offset:offset + length])
    return value, offset + length


def _cfi_record_state(rows, location, state):
    snapshot = _clone_cfi_state(state)
    if rows and rows[-1]["pc"] == location:
        rows[-1] = {"pc": location, "state": snapshot}
    else:
        rows.append({"pc": location, "state": snapshot})


def _cfi_restore_register(state, baseline, register):
    key = str(register)
    if key in baseline["registers"]:
        state["registers"][key] = dict(baseline["registers"][key])
    else:
        state["registers"].pop(key, None)


def _run_cfi_program(data, start, end, cie, initial_state=None,
                     restore_baseline=None, start_pc=0,
                     allow_advance=True, max_pc=None):
    if not 0 <= start <= end <= len(data):
        raise ValueError("DW_CFA instruction range leaves its segment")
    state = _clone_cfi_state(
        _default_cfi_state() if initial_state is None else initial_state
    )
    baseline = _clone_cfi_state(
        state if restore_baseline is None else restore_baseline
    )
    location = start_pc
    rows = [{"pc": location, "state": _clone_cfi_state(state)}]
    saved_states = []
    position = start
    instruction_count = 0
    code_alignment = cie["code_alignment"]
    data_alignment = cie["data_alignment"]

    def advance(delta):
        nonlocal location
        if not allow_advance and delta:
            raise ValueError("CIE initial instructions unexpectedly advance PC")
        location += delta * code_alignment
        if max_pc is not None and location > max_pc:
            raise ValueError("DW_CFA advances beyond the FDE coverage range")
        _cfi_record_state(rows, location, state)

    def changed():
        _cfi_record_state(rows, location, state)

    while position < end:
        opcode = data[position]
        position += 1
        instruction_count += 1

        primary = opcode & 0xc0
        if primary == 0x40:
            advance(opcode & 0x3f)
            continue
        if primary == 0x80:
            factor, position = _uleb(data, position, end)
            state["registers"][str(opcode & 0x3f)] = {
                "kind": "offset",
                "cfa_offset": factor * data_alignment,
            }
            changed()
            continue
        if primary == 0xc0:
            _cfi_restore_register(state, baseline, opcode & 0x3f)
            changed()
            continue

        if opcode == 0x00:  # DW_CFA_nop
            continue
        if opcode == 0x01:  # DW_CFA_set_loc; deliberately fail closed
            raise ValueError("DW_CFA_set_loc is not implemented")
        if opcode == 0x02:
            delta = _u(data, position, 1)
            position += 1
            advance(delta)
            continue
        if opcode == 0x03:
            delta = _u(data, position, 2)
            position += 2
            advance(delta)
            continue
        if opcode == 0x04:
            delta = _u(data, position, 4)
            position += 4
            advance(delta)
            continue
        if opcode == 0x05:  # DW_CFA_offset_extended
            register, position = _uleb(data, position, end)
            factor, position = _uleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "offset",
                "cfa_offset": factor * data_alignment,
            }
            changed()
            continue
        if opcode == 0x06:  # DW_CFA_restore_extended
            register, position = _uleb(data, position, end)
            _cfi_restore_register(state, baseline, register)
            changed()
            continue
        if opcode == 0x07:  # DW_CFA_undefined
            register, position = _uleb(data, position, end)
            state["registers"][str(register)] = {"kind": "undefined"}
            changed()
            continue
        if opcode == 0x08:  # DW_CFA_same_value
            register, position = _uleb(data, position, end)
            state["registers"][str(register)] = {"kind": "same_value"}
            changed()
            continue
        if opcode == 0x09:  # DW_CFA_register
            register, position = _uleb(data, position, end)
            source_register, position = _uleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "register",
                "source_register": source_register,
            }
            changed()
            continue
        if opcode == 0x0a:  # DW_CFA_remember_state
            saved_states.append(_clone_cfi_state(state))
            continue
        if opcode == 0x0b:  # DW_CFA_restore_state
            if not saved_states:
                raise ValueError("DW_CFA_restore_state has no saved state")
            state = saved_states.pop()
            changed()
            continue
        if opcode == 0x0c:  # DW_CFA_def_cfa
            register, position = _uleb(data, position, end)
            offset, position = _uleb(data, position, end)
            state["cfa"] = {
                "kind": "register_offset",
                "register": register,
                "offset": offset,
            }
            changed()
            continue
        if opcode == 0x0d:  # DW_CFA_def_cfa_register
            register, position = _uleb(data, position, end)
            if state["cfa"] is None or state["cfa"]["kind"] != "register_offset":
                raise ValueError("DW_CFA_def_cfa_register has no register CFA rule")
            state["cfa"]["register"] = register
            changed()
            continue
        if opcode == 0x0e:  # DW_CFA_def_cfa_offset
            offset, position = _uleb(data, position, end)
            if state["cfa"] is None or state["cfa"]["kind"] != "register_offset":
                raise ValueError("DW_CFA_def_cfa_offset has no register CFA rule")
            state["cfa"]["offset"] = offset
            changed()
            continue
        if opcode == 0x0f:  # DW_CFA_def_cfa_expression
            expression, position = _cfi_block(data, position, end)
            state["cfa"] = {
                "kind": "expression",
                "expression_hex": expression.hex(),
            }
            changed()
            continue
        if opcode == 0x10:  # DW_CFA_expression
            register, position = _uleb(data, position, end)
            expression, position = _cfi_block(data, position, end)
            state["registers"][str(register)] = {
                "kind": "expression",
                "expression_hex": expression.hex(),
            }
            changed()
            continue
        if opcode == 0x11:  # DW_CFA_offset_extended_sf
            register, position = _uleb(data, position, end)
            factor, position = _sleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "offset",
                "cfa_offset": factor * data_alignment,
            }
            changed()
            continue
        if opcode == 0x12:  # DW_CFA_def_cfa_sf
            register, position = _uleb(data, position, end)
            factor, position = _sleb(data, position, end)
            state["cfa"] = {
                "kind": "register_offset",
                "register": register,
                "offset": factor * data_alignment,
            }
            changed()
            continue
        if opcode == 0x13:  # DW_CFA_def_cfa_offset_sf
            factor, position = _sleb(data, position, end)
            if state["cfa"] is None or state["cfa"]["kind"] != "register_offset":
                raise ValueError("DW_CFA_def_cfa_offset_sf has no register CFA rule")
            state["cfa"]["offset"] = factor * data_alignment
            changed()
            continue
        if opcode == 0x14:  # DW_CFA_val_offset
            register, position = _uleb(data, position, end)
            factor, position = _uleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "val_offset",
                "cfa_offset": factor * data_alignment,
            }
            changed()
            continue
        if opcode == 0x15:  # DW_CFA_val_offset_sf
            register, position = _uleb(data, position, end)
            factor, position = _sleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "val_offset",
                "cfa_offset": factor * data_alignment,
            }
            changed()
            continue
        if opcode == 0x16:  # DW_CFA_val_expression
            register, position = _uleb(data, position, end)
            expression, position = _cfi_block(data, position, end)
            state["registers"][str(register)] = {
                "kind": "val_expression",
                "expression_hex": expression.hex(),
            }
            changed()
            continue
        if opcode == 0x2d:  # DW_CFA_AARCH64_negate_ra_state
            state["ra_state_negated"] = not state["ra_state_negated"]
            changed()
            continue
        if opcode == 0x2e:  # DW_CFA_GNU_args_size
            state["args_size"], position = _uleb(data, position, end)
            changed()
            continue
        if opcode == 0x2f:  # DW_CFA_GNU_negative_offset_extended
            register, position = _uleb(data, position, end)
            factor, position = _uleb(data, position, end)
            state["registers"][str(register)] = {
                "kind": "offset",
                "cfa_offset": -(factor * data_alignment),
                "encoding": "DW_CFA_GNU_negative_offset_extended",
            }
            changed()
            continue
        raise ValueError("Unsupported DW_CFA opcode 0x%02x" % opcode)

    return rows, instruction_count


def decode_cfi_state(segment_data, segment_va, text_va, text_size,
                     fde, query_pc):
    if not isinstance(query_pc, int) or not fde["start"] <= query_pc < fde["end"]:
        raise ValueError("CFI query PC is outside the FDE coverage range")
    cie = _cie(segment_data, fde["cie_offset"], segment_va, text_va)
    full_fde = _fde(
        segment_data, fde["fde_offset"], segment_va, text_va, text_size,
        expected_cie_va=cie["virtual_address"],
        cie_cache={cie["offset"]: cie},
    )
    if full_fde["start"] != fde["start"] or full_fde["end"] != fde["end"]:
        raise ValueError("Re-decoded FDE range differs from selected metadata")
    cie_rows, cie_instruction_count = _run_cfi_program(
        segment_data,
        cie["instructions_offset"],
        cie["instructions_end_offset"],
        cie,
        start_pc=0,
        allow_advance=False,
    )
    cie_state = cie_rows[-1]["state"]
    fde_rows, fde_instruction_count = _run_cfi_program(
        segment_data,
        full_fde["instructions_offset"],
        full_fde["instructions_end_offset"],
        cie,
        initial_state=cie_state,
        restore_baseline=cie_state,
        start_pc=full_fde["start"],
        allow_advance=True,
        max_pc=full_fde["end"],
    )
    applicable = [row for row in fde_rows if row["pc"] <= query_pc]
    if not applicable:
        raise ValueError("No CFI row covers the requested PC")
    state = applicable[-1]["state"]
    return {
        "status": "DECODED_CFI_STATE",
        "pc": hex(query_pc),
        "fde_start": hex(full_fde["start"]),
        "fde_end_exclusive": hex(full_fde["end"]),
        "fde_sha256": full_fde["fde_sha256"],
        "cie_offset": hex(cie["offset"]),
        "cie_augmentation": cie["augmentation"],
        "code_alignment": cie["code_alignment"],
        "data_alignment": cie["data_alignment"],
        "return_register": cie["return_register"],
        "cfa": state["cfa"],
        "x19_rule": state["registers"].get("19", {"kind": "unspecified"}),
        "return_register_rule": state["registers"].get(
            str(cie["return_register"]), {"kind": "unspecified"}
        ),
        "register_rules": state["registers"],
        "ra_state_negated": state["ra_state_negated"],
        "args_size": state["args_size"],
        "cie_program_sha256": cie["instructions_sha256"],
        "fde_program_sha256": full_fde["instructions_sha256"],
        "cie_instruction_count": cie_instruction_count,
        "fde_instruction_count": fde_instruction_count,
        "cfi_state_is_static_unwind_metadata_not_runtime_register_capture": True,
    }


def _map_target_cfi_states(targets, fdes, rows, selected, text_va, text_size):
    mapped = []
    if selected is None:
        return [
            {"name": name, "pc": hex(address), "status": "NO_SELECTED_CFI_METADATA"}
            for name, address in targets.items()
        ]
    segment_index = selected["segment_index"]
    segment_va, segment_data, _stored = rows[segment_index]
    for name, address in targets.items():
        matches = [fde for fde in fdes if fde["start"] <= address < fde["end"]]
        if len(matches) != 1:
            mapped.append({
                "name": name,
                "pc": hex(address),
                "status": "UNMAPPED" if not matches else "AMBIGUOUS",
                "matching_fde_count": len(matches),
            })
            continue
        fde = matches[0]
        try:
            decoded = decode_cfi_state(
                segment_data, segment_va, text_va, text_size, fde, address
            )
        except ValueError as exc:
            mapped.append({
                "name": name,
                "pc": hex(address),
                "fde_start": hex(fde["start"]),
                "fde_end_exclusive": hex(fde["end"]),
                "status": "UNSUPPORTED_CFI_PROGRAM",
                "error": str(exc),
            })
            continue
        mapped.append({
            "name": name,
            "pc": hex(address),
            "fde_start": decoded["fde_start"],
            "fde_end_exclusive": decoded["fde_end_exclusive"],
            "fde_sha256": decoded["fde_sha256"],
            "status": decoded["status"],
            "cfi": decoded,
        })
    return mapped


def inspect(nso):
    digest = hashlib.sha256(nso).hexdigest()
    if digest != MAIN_SHA256:
        raise ValueError("Original Switch v1.70 main SHA256 mismatch")
    rows = segments(nso)
    caller_report = inspect_callers(nso)
    metadata = discover_metadata(rows)
    text_va, text, _ = rows[0]
    mappings, ranges = map_callers_to_fdes(
        caller_report["callers"], metadata["fde_records"], text
    )
    anchor_mappings = map_addresses_to_fdes(
        ANALYSIS_ANCHORS, metadata["fde_records"]
    )
    counts = {
        "unique_fde_coverage": sum(
            row["mapping_status"] == "UNIQUE_FDE_COVERAGE" for row in mappings
        ),
        "unmapped": sum(row["mapping_status"] == "UNMAPPED" for row in mappings),
        "ambiguous": sum(row["mapping_status"] == "AMBIGUOUS" for row in mappings),
    }
    table_paths = [
        row for row in mappings
        if int(row["call_site"], 16) in TABLE_PATH_CALLS
    ]
    selected = metadata["selected"]
    selected_summary = ({k: v for k, v in selected.items() if k != "fdes"}
                        if selected is not None else None)
    cfi_targets = dict(ANALYSIS_ANCHORS)
    cfi_targets.update({
        "table_path_call_0": TABLE_PATH_CALLS[0],
        "table_path_call_1": TABLE_PATH_CALLS[1],
    })
    cfi_states = _map_target_cfi_states(
        cfi_targets, metadata["fde_records"], rows, selected,
        text_va, len(text)
    )
    return {
        "status": "PINNED_FILELOAD_UNWIND_METADATA_STATIC_ONLY",
        "original_main_sha256": digest,
        "original_main_bytes": len(nso),
        "text_sha256": hashlib.sha256(text).hexdigest(),
        "text_va": hex(text_va),
        "text_bytes": len(text),
        "caller_census_dependency": {
            "target": caller_report["helper_target"],
            "raw_candidates": caller_report["raw_aligned_direct_b_bl_inbound_count"],
            "capstone_confirmed": caller_report["capstone_confirmed_direct_branch_count"],
            "unconfirmed": len(caller_report["capstone_unconfirmed_raw_candidates"]),
        },
        "metadata": {
            "status": metadata["status"],
            "selected": selected_summary,
            "diagnostics": metadata["diagnostics"],
            "fde_records_validated": len(metadata["fde_records"]),
        },
        "caller_mapping": {
            "total": len(mappings),
            "counts": counts,
            "rows": mappings,
            "unique_ranges_covering_callers": ranges,
        },
        "table_path_callers": table_paths,
        "analysis_anchor_mappings": anchor_mappings,
        "cfi_state_at_targets": cfi_states,
        "cfi_state_counts": {
            "decoded": sum(row["status"] == "DECODED_CFI_STATE" for row in cfi_states),
            "unsupported": sum(row["status"] == "UNSUPPORTED_CFI_PROGRAM" for row in cfi_states),
            "unmapped": sum(row["status"] == "UNMAPPED" for row in cfi_states),
            "ambiguous": sum(row["status"] == "AMBIGUOUS" for row in cfi_states),
        },
        "limits": {
            "fde_range_is_exact_cfi_coverage_only": True,
            "function_entry_identity_verified": False,
            "function_extent_identity_verified": False,
            "direct_inbound_edges_are_complete": False,
            "conditional_or_indirect_inbound_edges_resolved": False,
            "br_x2_target_resolved": False,
            "callback_identity_verified": False,
            "destructor_identity_verified": False,
            "object_type_verified": False,
            "ownership_lifecycle_verified": False,
            "lock_unlock_async_rollback_unbind_verified": False,
            "native_consumer_abi_verified": False,
            "archive_precedence_verified": False,
            "native_hook_added": False,
            "gameplay_verified": False,
            "full_moddingapi": False,
            "ready_for_gameplay_test": False,
            "emulator_tested": False,
        },
    }


if __name__ == "__main__":
    raise SystemExit("Use tests/test_native_fileload_unwind.py")
