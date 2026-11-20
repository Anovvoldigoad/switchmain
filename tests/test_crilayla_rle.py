"""Offline CRILAYLA bounded-distance encoder regressions; no CPK or game writes."""
import random
import unittest
from portlib.crilayla_rle import encode_runs
from portlib.crilayla import decompress
from portlib.crilayla_literal import encode_literals


class Runs(unittest.TestCase):
    def test_boundary_random_repeating_and_periodic(self):
        rng = random.Random(1170)
        for n in (256, 257, 258, 259, 260, 263, 264, 300, 1024, 4096):
            for suffix in (bytes(rng.randrange(256) for _ in range(n - 256)),
                           b'\0' * (n - 256),
                           (b'abc' * ((n - 256) // 3 + 1))[:n - 256]):
                decoded = bytes(range(256)) + suffix
                with self.subTest(n=n, suffix=suffix[:8]):
                    self.assertEqual(decompress(encode_runs(decoded)), decoded)

    def test_repeated_zero_payload_reduces_stored_bytes(self):
        decoded = bytes(range(256)) + b'\0' * 8192
        self.assertLess(len(encode_runs(decoded)), len(encode_literals(decoded)) // 5)

    def test_invalid_and_bound(self):
        for decoded in (b'', b'x' * 255, bytearray(256)):
            with self.assertRaises(ValueError):
                encode_runs(decoded)
        with self.assertRaises(ValueError):
            encode_runs(b'x' * 257, limit=256)

    def test_periodic_non_run_matches_and_exact_replay(self):
        prefix = bytes(range(256))
        for period in (5, 7, 13, 31):
            suffix = bytes((i * 29 + period) % 256 for i in range(period)) * 512
            decoded = prefix + suffix
            with self.subTest(period=period):
                encoded = encode_runs(decoded)
                self.assertEqual(decompress(encoded), decoded)
                self.assertEqual(encode_runs(decoded), encoded)
                self.assertLess(len(encoded), len(encode_literals(decoded)) // 3)

    def test_long_period_127_and_251(self):
        prefix = bytes(range(256))
        for period in (127, 251):
            suffix = bytes((i * 37 + i // 7 + period) % 256 for i in range(period)) * 20
            decoded = prefix + suffix
            with self.subTest(period=period):
                encoded = encode_runs(decoded)
                self.assertEqual(decompress(encoded), decoded)
                self.assertEqual(encoded, encode_runs(decoded))
                self.assertLess(len(encoded), len(encode_literals(decoded)) // 3)

    def test_random_input_and_long_run_boundary(self):
        rng = random.Random(170)
        for n in (256, 257, 260, 511, 1024, 8192):
            decoded = bytes(range(256)) + bytes(rng.randrange(256) for _ in range(n - 256))
            with self.subTest(n=n):
                self.assertEqual(decompress(encode_runs(decoded)), decoded)
        decoded = bytes(range(256)) + b'Z' * 4096
        self.assertEqual(decompress(encode_runs(decoded)), decoded)

if __name__ == "__main__":
    unittest.main()
