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
    encoded_len = (count * 9 + 7) // 8
    if encoded_len > 0xffffffff:
        raise ValueError('CRILAYLA encoded length exceeds header')
    # Pack bits directly into the final reversed stream. Avoid a Python-int
    # list of nine entries per input byte (multi-GB at the supported limit).
    encoded = bytearray(encoded_len)
    bit_index = 0
    for value in reversed(decoded[0x100:]):
        bit_index += 1  # zero literal selector
        for shift in range(7, -1, -1):
            if (value >> shift) & 1:
                encoded[encoded_len - 1 - bit_index // 8] |= 1 << (7 - bit_index % 8)
            bit_index += 1
    return b'CRILAYLA' + struct.pack('<II', count, encoded_len) + encoded + decoded[:0x100]
