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


if __name__ == '__main__':
    unittest.main()
