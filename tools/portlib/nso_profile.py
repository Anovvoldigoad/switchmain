"""Bounded NSO profile edit, using only Python's standard library on Android."""
import hashlib
import struct
from .factory_profile import MAGIC, PROFILE_SIZE, decode

MAX_SEGMENT = 64 * 1024 * 1024


def decompress_lz4(data, expected):
    if not 0 <= expected <= MAX_SEGMENT:
        raise ValueError('LZ4 output limit')
    out, p = bytearray(), 0
    def length(n):
        nonlocal p
        if n == 15:
            while True:
                if p >= len(data):
                    raise ValueError('Truncated LZ4 length')
                x = data[p]; p += 1; n += x
                if n > expected:
                    raise ValueError('LZ4 length exceeds output')
                if x != 255:
                    break
        return n
    while p < len(data):
        token = data[p]; p += 1; n = length(token >> 4)
        if p+n > len(data) or len(out)+n > expected:
            raise ValueError('LZ4 literal bounds')
        out.extend(data[p:p+n]); p += n
        if p == len(data):
            break
        if p+2 > len(data):
            raise ValueError('Missing LZ4 offset')
        distance = data[p] | data[p+1] << 8; p += 2
        n = length(token & 15) + 4
        if not distance or distance > len(out) or len(out)+n > expected:
            raise ValueError('LZ4 match bounds')
        for _ in range(n):
            out.append(out[-distance])
    if len(out) != expected:
        raise ValueError('LZ4 size mismatch')
    return bytes(out)


def segments(nso):
    if len(nso) < 256 or nso[:12] != b'NSO0' + bytes(8):
        raise ValueError('Expected NSO0 version 0')
    flags = struct.unpack_from('<I', nso, 12)[0]
    if flags & ~0x3f or flags & 0x38 != 0x38:
        raise ValueError('NSO segment hashes required')
    rows, disk_spans, memory_end = [], [], 0
    for i in range(3):
        off, va, size = struct.unpack_from('<III', nso, 16+i*16)
        packed_size = struct.unpack_from('<I', nso, 96+i*4)[0]
        stored_size = packed_size if flags & (1 << i) else size
        if not 0 < size <= MAX_SEGMENT or not 0 < stored_size <= MAX_SEGMENT:
            raise ValueError('NSO segment size limit')
        if off < 256 or off+stored_size > len(nso) or va % 4096 or va < memory_end:
            raise ValueError('NSO segment bounds')
        if any(off < end and off+stored_size > start for start, end in disk_spans):
            raise ValueError('Overlapping NSO file segments')
        disk_spans.append((off, off+stored_size))
        stored = nso[off:off+stored_size]
        raw = decompress_lz4(stored, size) if flags & (1 << i) else stored
        if hashlib.sha256(raw).digest() != nso[160+i*32:192+i*32]:
            raise ValueError('NSO segment hash mismatch')
        rows.append((va, raw, stored))
        memory_end = va + size
    return rows


def configure_payload(nso, profile, expected_sha256, magic, profile_size, validate):
    if len(expected_sha256) != 64 or hashlib.sha256(nso).hexdigest() != expected_sha256:
        raise ValueError('Input module SHA256 mismatch')
    validate(profile)
    rows = segments(nso)
    data = rows[2][1]
    locations, pos = [], 0
    while True:
        pos = data.find(magic, pos)
        if pos < 0:
            break
        locations.append(pos); pos += 1
    if len(locations) != 1:
        raise ValueError('Expected exactly one embedded profile in module data')
    pos = locations[0]
    validate(data[pos:pos+profile_size])
    changed = data[:pos] + profile + data[pos+profile_size:]
    header = bytearray(nso[:256])
    flags = struct.unpack_from('<I', header, 12)[0]
    struct.pack_into('<I', header, 12, flags & ~4)  # data becomes uncompressed
    struct.pack_into('<I', header, 104, len(changed))
    header[224:256] = hashlib.sha256(changed).digest()
    payload = bytearray()
    for i, (_, _, stored) in enumerate(rows):
        struct.pack_into('<I', header, 16+i*16, 256+len(payload))
        payload.extend(changed if i == 2 else stored)
    result = bytes(header + payload)
    checked = segments(result)
    if checked[0][:2] != rows[0][:2] or checked[1][:2] != rows[1][:2]:
        raise ValueError('Executable/readonly segment unexpectedly changed')
    if checked[2][0] != rows[2][0] or len(checked[2][1]) != len(data):
        raise ValueError('Module data layout unexpectedly changed')
    return result, {'template_sha256': expected_sha256,
                    'configured_sha256': hashlib.sha256(result).hexdigest(),
                    'profile_sha256': hashlib.sha256(profile).hexdigest(),
                    'profile_data_offset': pos,
                    'text_rodata_unchanged': True, 'gameplay_verified': False,
                    'full_moddingapi': False}


def configure(nso, profile, expected_sha256):
    result, report = configure_payload(nso, profile, expected_sha256, MAGIC, PROFILE_SIZE, decode)
    report['class_mappings'] = len(decode(profile))
    return result, report
