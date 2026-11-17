"""Offline CRILAYLA encoder using deterministic bounded-distance backreferences.

No CPK rewriting; preserves the 256-byte decoded prefix verbatim.
"""
import struct


def encode_runs(decoded, *, limit=256 * 1024 * 1024):
    if not isinstance(decoded, bytes) or len(decoded) < 0x100:
        raise ValueError('CRILAYLA decoded input requires a 0x100-byte prefix')
    if not isinstance(limit, int) or limit < 0x100 or len(decoded) > limit:
        raise ValueError('CRILAYLA decoded input exceeds limit')
    size = len(decoded) - 0x100
    if size > 0xffffffff:
        raise ValueError('CRILAYLA decoded length exceeds header')
    encoded = bytearray()
    bit_index = 0

    def emit(value, width):
        nonlocal bit_index
        for shift in range(width - 1, -1, -1):
            if bit_index % 8 == 0:
                encoded.append(0)
            if (value >> shift) & 1:
                encoded[-1] |= 1 << (7 - bit_index % 8)
            bit_index += 1

    # Consume output from right to left. A match is valid only when its source begins in already decoded bytes.
    pos = len(decoded)
    while pos > 0x100:
        count = 0
        distance = 0
        # Search only the first 32 backward-decoding distances. Unlike the
        # distance-3-only path, this also compresses periodic non-run payloads.
        # A reference must start inside already decoded bytes to the right.
        for candidate in range(3, min(35, len(decoded) - pos + 1)):
            matched = 0
            while (pos - matched - 1 >= 0x100 and matched < 1024
                   and decoded[pos - matched - 1] ==
                   decoded[pos - matched - 1 + candidate]):
                matched += 1
            if matched > count:
                count, distance = matched, candidate
        if count >= 4:
            emit(1, 1)
            emit(distance - 3, 13)
            remaining = count - 3
            for width in (2, 3, 5):
                part = min(remaining, (1 << width) - 1)
                emit(part, width)
                remaining -= part
                if part != (1 << width) - 1:
                    break
            else:
                while True:
                    part = min(remaining, 255)
                    emit(part, 8)
                    remaining -= part
                    if part != 255:
                        break
            pos -= count
        else:
            pos -= 1
            emit(0, 1)
            emit(decoded[pos], 8)
    encoded.reverse()
    return b'CRILAYLA' + struct.pack('<II', size, len(encoded)) + encoded + decoded[:0x100]
