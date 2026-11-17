"""Batch editor changes must authenticate before applying any operation."""
import hashlib
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from merge_pc_moveset_nsc_manifests import merge
from patch_pc_moveset_nsc_mods import patch_verified
from verify_pc_moveset_nsc_sources import verify


def source(name, event):
    raw = json.dumps({'source_version': 'nsc', 'events': [
        {'event_id': event, 'function_index': 0}]}).encode()
    return name, raw, hashlib.sha256(raw).hexdigest()


class BatchPatchTests(unittest.TestCase):
    def setUp(self):
        self.sources = [source('a', 'a'), source('b', 'b'), source('c', 'c')]
        self.payload, self.proof = merge(self.sources)

    def test_remove_and_replace_in_one_transaction(self):
        replacement = source('c', 'new')
        result, proof = patch_verified(self.payload, self.proof, self.sources,
                                       ['a'], [replacement])
        self.assertEqual((result, proof), merge([self.sources[1], replacement]))
        self.assertEqual(verify(result, proof, [self.sources[1], replacement])['source_count'], 2)
        self.assertEqual((self.payload, self.proof), merge(self.sources))

    def test_rejects_duplicate_and_conflicting_changes(self):
        for removals, replacements in [(['a', 'a'], []),
                                       (['a'], [source('a', 'x')]),
                                       ([], [source('b', 'x'), source('b', 'y')]),
                                       ([], [])]:
            with self.subTest(removals=removals, replacements=replacements):
                with self.assertRaises(ValueError):
                    patch_verified(self.payload, self.proof, self.sources, removals, replacements)

    def test_rejects_unknown_all_removed_and_collision(self):
        for removals, replacements in [(['missing'], []),
                                       (['a', 'b', 'c'], []),
                                       ([], [source('b', 'a')])]:
            with self.subTest(removals=removals, replacements=replacements):
                with self.assertRaises(ValueError):
                    patch_verified(self.payload, self.proof, self.sources, removals, replacements)

    def test_forged_old_or_new_sha_fails_closed(self):
        forged = dict(self.proof, output_sha256='0' * 64)
        with self.assertRaises(ValueError):
            patch_verified(self.payload, forged, self.sources, ['a'])
        name, raw, _ = source('b', 'new')
        with self.assertRaises(ValueError):
            patch_verified(self.payload, self.proof, self.sources, [],
                           [(name, raw, '0' * 64)])

    def test_add_new_mod_and_replay_exact_source_provenance(self):
        added = source('d', 'd')
        result, proof = patch_verified(self.payload, self.proof, self.sources,
                                       additions=[added])
        self.assertEqual((result, proof), merge(self.sources + [added]))
        self.assertEqual(verify(result, proof, self.sources + [added])['source_count'], 4)
        self.assertEqual((self.payload, self.proof), merge(self.sources))

    def test_atomic_remove_replace_and_add(self):
        added = source('d', 'd')
        replacement = source('b', 'b2')
        updated = [replacement, self.sources[2], added]
        result, proof = patch_verified(self.payload, self.proof, self.sources,
                                       ['a'], [replacement], [added])
        self.assertEqual((result, proof), merge(updated))
        self.assertEqual(verify(result, proof, updated)['source_count'], 3)

    def test_add_rejects_name_collision_event_collision_and_bad_hash(self):
        for additions in ([source('a', 'new')], [source('d', 'a')],
                          [source('d', 'd'), source('d', 'e')],
                          [('d', source('d', 'd')[1], '0' * 64)]):
            with self.subTest(additions=additions), self.assertRaises(ValueError):
                patch_verified(self.payload, self.proof, self.sources,
                               additions=additions)

    def test_add_boundary_and_invalid_old_proof(self):
        extra = [source('d' + str(i), 'e' + str(i)) for i in range(61)]
        result, proof = patch_verified(self.payload, self.proof, self.sources,
                                       additions=extra)
        self.assertEqual(verify(result, proof, self.sources + extra)['source_count'], 64)
        with self.assertRaises(ValueError):
            patch_verified(self.payload, self.proof, self.sources,
                           additions=extra + [source('overflow', 'overflow')])
        forged = dict(self.proof, output_sha256='0' * 64)
        with self.assertRaises(ValueError):
            patch_verified(self.payload, forged, self.sources,
                           additions=[source('d', 'd')])

    def test_single_source_replacement_boundary(self):
        original = [source('only', 'old')]
        payload, proof = merge(original)
        new = source('only', 'new')
        self.assertEqual(patch_verified(payload, proof, original, [], [new]), merge([new]))


if __name__ == '__main__':
    unittest.main()
