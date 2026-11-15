"""Offline CRILAYLA encoder using deterministic distance-3 run backreferences.

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

    # Consume output from right to left. A distance-3 match is valid only
    # when three already decoded bytes are available to the right.
    pos = len(decoded)
    while pos > 0x100:
        count = 0
        if pos + 2 < len(decoded):
            while (pos - count - 1 >= 0x100 and count < 1024
                   and decoded[pos - count - 1] == decoded[pos - count + 2]):
                count += 1
        if count >= 4:
            emit(1, 1)
            emit(0, 13)
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
