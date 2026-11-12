"""Synthetic offline batch export; no game ABI or installable output."""
import hashlib
import pathlib
import tempfile
import unittest
from test_cpk_events import cpk
from test_prm_marker import fixture, event
from test_compressed_prm_events import literal_stream
from export_decoded_prm_batch import export_batch


class BatchDecodedExport(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.paths = ["data/spc/one.bin.xfbin", "data/spc/two.bin.xfbin"]
        raw = fixture([event(14), event(0), event(15)])
        self.source = cpk([(p, literal_stream(raw)) for p in self.paths],
                          lambda rows: [row.update({"ExtractSize": len(raw)}) for row in rows])
        self.archive = self.root / "original.cpk"
        self.archive.write_bytes(self.source)
        self.sha = hashlib.sha256(self.source).hexdigest()
        self.out = self.root / "out"
        self.out.mkdir()

    def manifest(self):
        return {"members": [{"path": self.paths[0], "output": "one.bin"},
                            {"path": self.paths[1], "output": "two.bin"}]}

    def test_two_candidates_and_unchanged_source(self):
        report = export_batch(self.archive, self.sha, self.manifest(), self.out)
        self.assertEqual(len(report["members"]), 2)
        self.assertFalse(report["output_is_installable"])
        for row in report["members"]:
            self.assertEqual(hashlib.sha256((self.out / row["output"]).read_bytes()).hexdigest(),
                             row["candidate_decoded_sha256"])
            self.assertEqual(row["marked_records"], 2)
        self.assertEqual(self.archive.read_bytes(), self.source)

    def test_fail_before_output_for_invalid_second_member(self):
        for bad in ("data/spc/absent.bin.xfbin", self.paths[0]):
            m = self.manifest()
            m["members"][1]["path"] = bad
            with self.assertRaises(ValueError):
                export_batch(self.archive, self.sha, m, self.out)
            self.assertEqual(list(self.out.iterdir()), [])

    def test_wrong_hash_duplicate_casefold_and_existing_output(self):
        with self.assertRaises(ValueError):
            export_batch(self.archive, "0" * 64, self.manifest(), self.out)
        m = self.manifest()
        m["members"][1]["output"] = "ONE.BIN"
        with self.assertRaises(ValueError):
            export_batch(self.archive, self.sha, m, self.out)
        (self.out / "two.bin").write_bytes(b"preserve")
        with self.assertRaises(ValueError):
            export_batch(self.archive, self.sha, self.manifest(), self.out)
        self.assertEqual((self.out / "two.bin").read_bytes(), b"preserve")
        self.assertFalse((self.out / "one.bin").exists())

    def test_unsafe_names_and_limits(self):
        for name in ("../escape", "/absolute", "folder/file", "..", "a\\b"):
            m = self.manifest()
            m["members"][0]["output"] = name
            with self.subTest(name=name), self.assertRaises(ValueError):
                export_batch(self.archive, self.sha, m, self.out)
        with self.assertRaises(ValueError):
            export_batch(self.archive, self.sha, self.manifest(), self.out, limit=256)
        self.assertEqual(list(self.out.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
