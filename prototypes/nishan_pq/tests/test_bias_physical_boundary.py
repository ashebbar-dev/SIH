"""Small process-boundary fixtures; never access physical captures or a real roster."""
from contextlib import ExitStack
import json
from pathlib import Path
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.tools import probe_nishan_bias_physical as physical


class PhysicalBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def gate(self):
        gate = self.root / 'gate'
        gate.mkdir()
        dependency = physical.ROOT / 'research/tools/nishan_bias_registration.py'
        physical.dump(gate / 'manifest.json', {'code_sha256': {
            str(dependency.relative_to(physical.ROOT)): physical.digest(dependency)}})
        physical.dump(gate / 'results.json', {'completed': True, 'physical_gate_passed': True,
            'manifest_sha256': physical.digest(gate / 'manifest.json')})
        return gate

    def frozen(self):
        directory = self.root / 'prepared'
        directory.mkdir()
        p = np.array([.2, .5, .8])
        arrays = {'p': p}
        records = []
        for capture in physical.CAPTURES:
            for profile in physical.PROFILES:
                key = f'record_{len(records)}'
                arrays[key + '_word'] = np.array([1, 0, 1], np.uint8)
                arrays[key + '_correlations'] = np.array([1, -1, 2], np.float32)
                records.append({'capture': capture, 'profile': profile, 'status': 'prepared',
                    'word_key': key + '_word', 'correlations_key': key + '_correlations',
                    'raw_to_reference': np.eye(3).tolist(), 'objective': .1,
                    'content_similarity': .8})
        payload = {'completed': True, 'settings': physical.settings(), 'records': records,
                   'code_sha256': {}, 'array_sha256': {k: physical.reg.array_hash(v) for k, v in arrays.items()}}
        with (directory / 'prepared.npz').open('xb') as handle:
            np.savez_compressed(handle, **arrays)
        physical.dump(directory / 'preparation.json', payload)
        self.recommit(directory)
        return directory, p

    def recommit(self, directory):
        path = directory / 'commitment.json'
        if path.exists():
            path.unlink()
        physical.dump(path, {'completed': True, 'sha256': {
            name: physical.digest(directory / name) for name in ('preparation.json', 'prepared.npz')}})

    def test_prepare_rejects_failed_gate_before_loading_images(self):
        gate = self.gate()
        result = json.loads((gate / 'results.json').read_text())
        result['physical_gate_passed'] = False
        (gate / 'results.json').write_text(json.dumps(result))
        with patch.object(physical.watermark, 'load_pages', side_effect=AssertionError('image read')):
            with self.assertRaises(ValueError):
                physical.prepare(gate, self.root / 'output')

    def test_gate_rejects_manifest_hash_module_hash_and_escape(self):
        gate = self.gate()
        physical.validate_gate(gate)
        manifest = json.loads((gate / 'manifest.json').read_text())
        key = next(iter(manifest['code_sha256']))
        for changed in ({key: '0' * 64}, {'/tmp/outside.py': '0' * 64}):
            (gate / 'manifest.json').write_text(json.dumps({'code_sha256': changed}))
            result = {'completed': True, 'physical_gate_passed': True,
                      'manifest_sha256': physical.digest(gate / 'manifest.json')}
            (gate / 'results.json').write_text(json.dumps(result))
            with self.assertRaises(ValueError):
                physical.validate_gate(gate)
        (gate / 'manifest.json').write_text('{}')
        with self.assertRaises(ValueError):
            physical.validate_gate(gate)

    def test_exclusive_outputs_preserve_existing_evidence(self):
        existing = self.root / 'existing'
        existing.mkdir()
        with self.assertRaises(FileExistsError):
            physical.prepare(self.root / 'absent', existing)
        output = existing / 'scores.json'
        output.write_text('retained')
        with self.assertRaises(FileExistsError):
            physical.score(self.root / 'absent', output)
        self.assertEqual(output.read_text(), 'retained')

    def test_scoring_rejects_changed_file_and_changed_word(self):
        directory, _ = self.frozen()
        physical.validate_prepared(directory)
        with (directory / 'prepared.npz').open('ab') as handle:
            handle.write(b'changed')
        with self.assertRaises(ValueError):
            physical.score(directory, self.root / 'scores.json')
        self.recommit(directory)
        with np.load(directory / 'prepared.npz') as stored:
            arrays = {k: stored[k] for k in stored.files}
        arrays['record_0_word'][0] = 0
        with (directory / 'prepared.npz').open('wb') as handle:
            np.savez_compressed(handle, **arrays)
        self.recommit(directory)
        with self.assertRaises(ValueError):
            physical.validate_prepared(directory)

    def test_score_uses_frozen_words_profiles_and_8000_without_registration(self):
        directory, p = self.frozen()
        roster = np.array([[1, 0, 1], [0, 1, 0]], np.uint8)
        seen = []
        def threshold(biases, word, epsilon, hypotheses):
            seen.append((word.copy(), epsilon, hypotheses))
            return {'threshold': 0.0, 'hypotheses': hypotheses}
        with ExitStack() as stack:
            stack.enter_context(patch('builtins.print'))
            stack.enter_context(patch.object(physical, 'PRIOR', self.root / 'unused-prior.json'))
            for target, method in ((physical.reg, 'search_translation'),
                                   (physical.watermark, 'load_pages'),
                                   (physical.registration, 'align_page')):
                stack.enter_context(patch.object(target, method, side_effect=AssertionError('registration in score')))
            stack.enter_context(patch.object(physical.tardos, 'generate_keyed', return_value=(p, roster)))
            stack.enter_context(patch.object(physical, 'conditional_null_threshold', side_effect=threshold))
            stack.enter_context(patch.object(physical, 'load_prior_baselines', return_value={}))
            result = physical.score(directory, self.root / 'scores.json')
        self.assertEqual(physical.PROFILES, ('affine_baseline', 'affine_bias_translation'))
        self.assertEqual(result['settings']['hypotheses'], 8000)
        self.assertEqual(len(result['records']), 8)
        self.assertEqual({r['profile'] for r in result['records']}, set(physical.PROFILES))
        self.assertEqual(len(seen), 8)
        for word, epsilon, hypotheses in seen:
            np.testing.assert_array_equal(word, [1, 0, 1])
            self.assertEqual((epsilon, hypotheses), (1e-6, 8000))

    def test_prepare_commits_both_profiles_and_failures_without_roster_or_prior(self):
        gate = self.gate()
        source = np.full((12, 12, 3), 245, np.uint8)
        p = np.array([.2, .5, .8])
        mask = np.zeros((12, 12), bool)
        metrics = SimpleNamespace(homography_suspect_to_reference=np.eye(3).tolist(), to_dict=lambda: {})
        search = {'status': 'boundary_failure', 'reason': 'maximum_on_search_boundary',
                  'dx': 2., 'dy': 0., 'best_objective': .2, 'statistics': {},
                  'mask_sha256': physical.reg.array_hash(mask),
                  'objectives': [{'dx': 0., 'dy': 0., 'objective': .1}]}
        with ExitStack() as stack:
            stack.enter_context(patch('builtins.print'))
            stack.enter_context(patch.object(physical, 'digest', return_value='fixture-hash'))
            stack.enter_context(patch.object(physical, 'validate_gate', return_value={}))
            stack.enter_context(patch.object(physical.watermark, 'load_pages', return_value=([source], {})))
            stack.enter_context(patch.object(physical.reg, 'keyed_biases', return_value=p))
            stack.enter_context(patch.object(physical.tardos, 'generate_keyed', side_effect=AssertionError('roster')))
            stack.enter_context(patch.object(physical, 'load_prior_baselines', side_effect=AssertionError('prior scores')))
            stack.enter_context(patch.object(physical.tardos_carrier, '_plan', return_value=(np.arange(3), np.zeros(3, int), np.ones(3, np.int8))))
            stack.enter_context(patch.object(physical, 'source_response', return_value={'midpoint': mask.astype(float), 'pilot': mask.astype(float)}))
            stack.enter_context(patch.object(physical.registration, 'align_page', return_value=(source, metrics)))
            stack.enter_context(patch.object(physical, 'refine', return_value=(source, {'inverse_warp': np.eye(3)[:2].tolist()})))
            stack.enter_context(patch.object(physical, 'compose_and_render', return_value=(source, np.eye(3))))
            stack.enter_context(patch.object(physical.reg, 'search_translation', return_value=search))
            stack.enter_context(patch.object(physical.reg, 'common_coverage', return_value=mask))
            stack.enter_context(patch.object(physical.reg, 'prepare_projection', return_value={'mask': mask}))
            result = physical.prepare(gate, self.root / 'output')
        self.assertEqual(result['settings']['profiles'], list(physical.PROFILES))
        self.assertEqual(result['settings']['hypotheses'], 8000)
        self.assertEqual([r['status'] for r in result['records']], ['prepared', 'boundary_failure'] * 4)
        for record in result['records'][1::2]:
            self.assertNotIn('word_key', record)
        self.assertEqual({p.name for p in (self.root / 'output').iterdir()},
                         {'preparation.json', 'prepared.npz', 'commitment.json'})

    def test_source_response_uses_original_pdf_binary_endpoints_and_blur(self):
        source_path = self.root / 'original.pdf'
        rgb0, rgb1 = np.full((6, 6, 3), 240, np.uint8), np.full((6, 6, 3), 244, np.uint8)
        with patch.object(physical.tardos_carrier, 'embed_pdf') as embed, \
             patch.object(physical.watermark, 'load_pages', side_effect=[([rgb0], {}), ([rgb1], {})]), \
             patch.object(physical.reg, 'render_native', side_effect=AssertionError('raster replacement')):
            response = physical.source_response(source_path, (6, 6), np.array([.25]), np.array([0]))
        self.assertEqual(embed.call_count, 2)
        for bit, call in enumerate(embed.call_args_list):
            self.assertEqual(call.args[0], source_path)
            np.testing.assert_array_equal(call.args[2], [bit])
            self.assertEqual(call.kwargs, {'strength': 4., 'dpi': 144, 'block_size': 6})
            self.assertFalse(call.args[1].parent.exists())
        np.testing.assert_array_equal(response['q_image'], .25)
        np.testing.assert_allclose(response['midpoint'], 242, atol=2e-5)
        np.testing.assert_allclose(response['pilot'], -1, atol=2e-5)

    def test_decoder_preserves_float32_cancellation_and_strict_sign(self):
        source = np.zeros((6, 6), np.float32)
        image = np.zeros((6, 6), np.float64)
        image.flat[:3] = [2**24, 1, -(2**24)]
        templates = np.ones((1, 6, 6), np.float32)
        correlations, word = physical.decode_luma(image, source, np.array([0]), templates)
        expected = np.sum(image.astype(np.float32)[None] * templates, axis=(1, 2), dtype=np.float32)
        np.testing.assert_array_equal(correlations, expected)
        np.testing.assert_array_equal(word, expected > 0)
        self.assertEqual(correlations.dtype, np.float32)


if __name__ == '__main__':
    unittest.main()
