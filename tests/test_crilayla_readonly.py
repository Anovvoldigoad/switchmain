"""Synthetic literal-only CRILAYLA proof; not a game-archive fixture."""
import unittest
from portlib.crilayla import decompress


def fixture(raw):
    bits = []
    for b in reversed(raw):
        bits.append(0)
        bits.extend((b >> i) & 1 for i in range(7, -1, -1))
    bits.extend([0] * ((-len(bits)) % 8))
    encoded = bytes(sum(bits[j + k] << (7 - k) for k in range(8))
                    for j in range(0, len(bits), 8))[::-1]
    return b'CRILAYLA' + len(raw).to_bytes(4, 'little') + len(encoded).to_bytes(4, 'little') + encoded + bytes(range(256))


class ReadOnlyCRILAYLA(unittest.TestCase):
    def test_literals_and_prefix(self):
        for raw in (b'', b'Z', bytes(range(33)), b'hello' * 100):
            stream = fixture(raw)
            before = bytes(stream)
            self.assertEqual(decompress(stream), bytes(range(256)) + raw)
            self.assertEqual(stream, before)

    def test_backward_overlap_copy_and_corrupt_distance(self):
        # CRILAYLA decodes from the end: literal C,B,A, then a 3-byte
        # backreference at distance 3 must reconstruct ABCABC.
        def packed(tokens):
            bits = []
            for value, width in tokens:
                bits.extend((value >> shift) & 1 for shift in range(width - 1, -1, -1))
            bits.extend([0] * ((-len(bits)) % 8))
            return bytes(sum(bits[j + k] << (7 - k) for k in range(8))
                         for j in range(0, len(bits), 8))[::-1]
        literals = [(0, 1), (ord('C'), 8), (0, 1), (ord('B'), 8),
                    (0, 1), (ord('A'), 8)]
        def stream(distance):
            encoded = packed(literals + [(1, 1), (distance - 3, 13), (0, 2)])
            return (b'CRILAYLA' + (6).to_bytes(4, 'little') +
                    len(encoded).to_bytes(4, 'little') + encoded + bytes(range(256)))
        self.assertEqual(decompress(stream(3)), bytes(range(256)) + b'ABCABC')
        with self.assertRaises(ValueError):
            decompress(stream(7))

    def test_invalid(self):
        valid = fixture(b'ABC')
        cases = [b'', valid[:-1], valid + b'X',
                 valid[:8] + (2**32-1).to_bytes(4, 'little') + valid[12:],
                 valid[:12] + (2**32-1).to_bytes(4, 'little') + valid[16:],
                 valid[:19] + bytes([valid[19] | 0x80]) + valid[20:]]
        for case in cases:
            with self.subTest(case=case[:20]):
                with self.assertRaises(ValueError):
                    decompress(case)
        with self.assertRaises(ValueError):
            decompress(valid, limit=2)


if __name__ == '__main__':
    unittest.main()
