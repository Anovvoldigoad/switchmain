"""Encode decoded CRILAYLA bytes as literal-only stream (offline, no CPK edits).

The 0x100-byte prefix is stored verbatim; the remainder is emitted in
reverse decode order. This is not a size-optimized compressor.
"""
import struct


def encode_literals(decoded, *, limit=256 * 1024 * 1024):
    if not isinstance(decoded, bytes) or len(decoded) < 0x100:
        raise ValueError('CRILAYLA decoded input requires a 0x100-byte prefix')
    if not isinstance(limit, int) or limit < 0x100 or len(decoded) > limit:
        raise ValueError('CRILAYLA decoded input exceeds limit')
    count = len(decoded) - 0x100
    if count > 0xffffffff:
        raise ValueError('CRILAYLA decoded length exceeds header')
    bits = []
    for byte in reversed(decoded[0x100:]):
        bits.append(0)
        bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
    bits.extend([0] * (-len(bits) % 8))
    encoded = bytes(sum(bits[i + shift] << (7 - shift) for shift in range(8))
                    for i in range(0, len(bits), 8))[::-1]
    if len(encoded) > 0xffffffff:
        raise ValueError('CRILAYLA encoded length exceeds header')
    return b'CRILAYLA' + struct.pack('<II', count, len(encoded)) + encoded + decoded[:0x100]
