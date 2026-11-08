"""Read-only CRILAYLA payload decoder; never rewrites a CPK or game resource."""
import struct

MAX_DECODED = 256 * 1024 * 1024


def decompress(data, *, limit=MAX_DECODED):
    if len(data) < 0x110 or data[:8] != b'CRILAYLA':
        raise ValueError('Not a complete CRILAYLA stream')
    decoded_size, compressed_size = struct.unpack_from('<II', data, 8)
    if decoded_size > limit or compressed_size > len(data) - 0x110:
        raise ValueError('CRILAYLA size exceeds bounds')
    end = 0x10 + compressed_size
    if end + 0x100 != len(data):
        raise ValueError('CRILAYLA stored length mismatch')
    result = bytearray(decoded_size + 0x100)
    result[:0x100] = data[end:]
    pos = decoded_size + 0x100
    cursor = end - 1
    bitbuf = 0
    bits_left = 0

    def bits(count):
        nonlocal cursor, bitbuf, bits_left
        value = 0
        for _ in range(count):
            if not bits_left:
                if cursor < 0x10:
                    raise ValueError('Truncated CRILAYLA bitstream')
                bitbuf = data[cursor]
                cursor -= 1
                bits_left = 8
            bits_left -= 1
            value = (value << 1) | ((bitbuf >> bits_left) & 1)
        return value

    while pos > 0x100:
        if not bits(1):
            pos -= 1
            result[pos] = bits(8)
            continue
        distance = bits(13) + 3
        count = 3
        for width in (2, 3, 5):
            n = bits(width)
            count += n
            if n != (1 << width) - 1:
                break
        else:
            while True:
                n = bits(8)
                count += n
                if n != 255:
                    break
        if count > pos - 0x100 or pos + distance > len(result):
            raise ValueError('Invalid CRILAYLA backreference')
        for _ in range(count):
            pos -= 1
            result[pos] = result[pos + distance]
    return bytes(result)
