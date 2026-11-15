"""Read-only CPK entry extraction: synthetic uncompressed and CRILAYLA fixtures."""
import unittest
from test_cpk_events import cpk
from test_crilayla_readonly import fixture
from portlib.cpk_events import read_payload, mark

PATH = 'data/spc/sample.bin.xfbin'


class ReadCPKPayload(unittest.TestCase):
    def test_uncompressed_and_missing(self):
        archive = cpk([(PATH, b'ABC')])
        self.assertEqual(read_payload(archive, PATH), b'ABC')
        with self.assertRaises(ValueError):
            read_payload(archive, 'data/spc/absent')
        with self.assertRaises(ValueError):
            read_payload(archive, PATH, limit=2)

    def test_compressed_exact_size_and_no_mutation(self):
        raw = bytes(range(256)) + b'ABCABC'
        packed = fixture(b'ABCABC')
        def sizes(rows):
            rows[0]['ExtractSize'] = len(raw)
        archive = cpk([(PATH, packed)], mutator=sizes)
        original = bytes(archive)
        self.assertEqual(read_payload(archive, PATH), raw)
        self.assertEqual(archive, original)
        with self.assertRaises(ValueError):
            read_payload(archive, PATH, limit=5)
        with self.assertRaises(ValueError):
            mark(archive, [PATH])

    def test_wrong_extract_size_and_truncated_stream(self):
        packed = fixture(b'ABC')
        for payload, size in ((packed, 260), (packed[:-1], 259)):
            def sizes(rows):
                rows[0]['ExtractSize'] = size
            archive = cpk([(PATH, payload)], mutator=sizes)
            with self.assertRaises(ValueError):
                read_payload(archive, PATH)


if __name__ == '__main__':
    unittest.main()
