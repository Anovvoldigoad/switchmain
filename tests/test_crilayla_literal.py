"""Literal-only CRILAYLA encoder: exact roundtrip, corruption, boundaries."""
import hashlib
import unittest
from portlib.crilayla import decompress
from portlib.crilayla_literal import encode_literals


class LiteralCRILAYLA(unittest.TestCase):
    def test_roundtrip_boundary_and_mixed_bytes(self):
        for payload in (b'', b'\0', bytes(range(256)), bytes(range(256))*4,
                        b'\xff\0\x80\x7f' * 257):
            raw = bytes(range(256)) + payload
            encoded = encode_literals(raw)
            self.assertEqual(decompress(encoded), raw)
            self.assertEqual(encoded[-256:], raw[:256])
            self.assertEqual(int.from_bytes(encoded[8:12], 'little'), len(payload))
            self.assertEqual(hashlib.sha256(decompress(encoded)).digest(), hashlib.sha256(raw).digest())
            self.assertEqual(encode_literals(raw), encoded)

    def test_fail_closed_and_decode_corruption(self):
        for raw, limit in ((b'', 256), (b'\0'*255, 256), (b'\0'*257, 256),
                           (b'\0'*256, 255), (bytearray(256), 256)):
            with self.subTest(size=len(raw), limit=limit), self.assertRaises(ValueError):
                encode_literals(raw, limit=limit)
        good = encode_literals(bytes(range(256)) + b'hello')
        with self.assertRaises(ValueError):
            decompress(good[:-1])
        with self.assertRaises(ValueError):
            decompress(good, limit=260)


    def test_packed_output_matches_independent_reference(self):
        # Reference bit-list implementation retained only for small test inputs.
        import struct
        def reference(raw):
            bits = []
            for byte in reversed(raw[256:]):
                bits.append(0)
                bits.extend((byte >> shift) & 1 for shift in range(7, -1, -1))
            bits.extend([0] * (-len(bits) % 8))
            payload = bytes(sum(bits[i + shift] << (7 - shift) for shift in range(8))
                            for i in range(0, len(bits), 8))[::-1]
            return b'CRILAYLA' + struct.pack('<II', len(raw)-256, len(payload)) + payload + raw[:256]

        for size in (256, 257, 258, 259, 260, 263, 264, 265, 1024, 4096):
            raw = bytes((i * 37 + size) % 256 for i in range(size))
            with self.subTest(size=size):
                packed = encode_literals(raw, limit=size)
                self.assertEqual(packed, reference(raw))
                self.assertEqual(decompress(packed), raw)
                self.assertEqual(len(packed), 16 + (size-256)*9//8 +
                                 (1 if (size-256)*9%8 else 0) + 256)

if __name__ == '__main__':
    unittest.main()
