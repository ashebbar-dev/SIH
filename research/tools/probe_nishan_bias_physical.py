#!/usr/bin/env python3
"""Frozen Task2 physical experiment: prepare pixels/words, score in a fresh CLI.

Preparation has bias-only access through the reviewed zero-row generator. The
only recipient-roster generation and prior physical score reads occur in score.
"""
from dataclasses import asdict
from pathlib import Path
import argparse
import hashlib
import json
import sys
import tempfile

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.tools import nishan_bias_registration as reg
from research.tools.probe_nishan_capture_channel import conditional_null_threshold
from research.tools.probe_nishan_physical_registration_single import refine, compose_and_render
from nishan import registration, tardos, tardos_carrier, watermark

CAPTURES = ('akshay.jpeg', 'akshay1.jpeg', 'akshay2.jpeg', 'akshay3.jpeg')
PROFILES = ('affine_baseline', 'affine_bias_translation')
SOURCE = ROOT / 'artifacts/nishan/synthetic-source.pdf'
DOWNLOADS = Path('/home/user_end4/Downloads')
SECRET = hashlib.sha3_256(b'NISHAN Tardos carrier public fixture v1').digest()
BIAS_CONTEXT = 'public-benchmark-codebook/v1'
CARRIER_CONTEXT = 'synthetic-source/full-tardos-profile-v1'
PRIOR = ROOT / 'research/evidence/nishan-physical-registration-single-2026-09-10.json'
DEPENDENCIES = (
    'research/tools/probe_nishan_bias_physical.py',
    'research/tools/nishan_bias_registration.py',
    'research/tools/probe_nishan_physical_registration_single.py',
    'research/tools/probe_nishan_capture_channel.py',
    'prototypes/nishan_pq/nishan/registration.py',
    'prototypes/nishan_pq/nishan/tardos.py',
    'prototypes/nishan_pq/nishan/tardos_carrier.py',
    'prototypes/nishan_pq/nishan/watermark.py',
    'prototypes/nishan_pq/tests/test_bias_physical_boundary.py',
)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write('\n')


def settings():
    return {'captures': list(CAPTURES), 'profiles': list(PROFILES),
            'hypotheses': 8000, 'family_epsilon': 1e-6, 'historical_threshold': 2100,
            'config': asdict(tardos.parameters(1000, 5, 1e-6)),
            'bias_context': BIAS_CONTEXT, 'carrier_context': CARRIER_CONTEXT,
            'fixture_secret': "sha3_256(b'NISHAN Tardos carrier public fixture v1')",
            'strength': 4.0, 'dpi': 144, 'block_size': 6, 'blur_sigma': .75,
            'blur_kernel': [0, 0], 'blur_border': 'BORDER_DEFAULT',
            'translation_grid': reg.GRID.tolist(), 'tile_size': 96,
            'minimum_blocks': 1000, 'minimum_pilot_energy_fraction': .2,
            'source_range_limit': 8, 'source_dilation_pixels': 6,
            'capture_support_margin': 4, 'ecc_motion': 'affine',
            'ecc_max_iterations': 200, 'ecc_epsilon_stop': 1e-6, 'ecc_gaussian_size': 5,
            'opencv_threads': 2, 'render': 'original RGB8 INTER_LANCZOS4, white border, then watermark._luma',
            'decoder': 'float32 luma/residual/templates/block sum; strict corr>0',
            'objective': 'Task1 float64 projection and normalized shared pilot correlation',
            'content_similarity': 'existing gradient similarity on rounded source/candidate luma uint8',
            'sample_probability': 'floor(p * 2^32) / 2^32'}


def validate_code_hashes(recorded):
    for name, expected in recorded.items():
        path = (ROOT / name).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError(f'code dependency escapes workspace: {name}')
        if not path.is_file() or digest(path) != expected:
            raise ValueError(f'code dependency hash mismatch: {name}')


def validate_gate(gate_directory: Path) -> dict:
    gate = Path(gate_directory)
    results = json.loads((gate / 'results.json').read_text())
    if results.get('completed') is not True or results.get('physical_gate_passed') is not True:
        raise ValueError('synthetic physical gate did not pass')
    if results.get('manifest_sha256') != digest(gate / 'manifest.json'):
        raise ValueError('gate manifest hash mismatch')
    manifest = json.loads((gate / 'manifest.json').read_text())
    if not manifest.get('code_sha256'):
        raise ValueError('gate has no code dependencies')
    validate_code_hashes(manifest['code_sha256'])
    return {'directory': str(gate.resolve()), 'results_sha256': digest(gate / 'results.json'),
            'manifest_sha256': results['manifest_sha256'], 'physical_gate_passed': True,
            'code_sha256': manifest['code_sha256']}


def validate_prepared(prepared_directory: Path) -> dict:
    directory = Path(prepared_directory)
    commitment = json.loads((directory / 'commitment.json').read_text())
    if commitment.get('completed') is not True:
        raise ValueError('incomplete preparation commitment')
    if set(commitment.get('sha256', {})) != {'preparation.json', 'prepared.npz'}:
        raise ValueError('commitment must cover both preparation files')
    for name, expected in commitment['sha256'].items():
        if digest(directory / name) != expected:
            raise ValueError(f'prepared file hash mismatch: {name}')
    payload = json.loads((directory / 'preparation.json').read_text())
    if payload.get('completed') is not True or payload.get('settings') != settings():
        raise ValueError('incomplete or changed fixed preparation settings')
    validate_code_hashes(payload['code_sha256'])
    expected_pairs = [(c, p) for c in CAPTURES for p in PROFILES]
    if [(r['capture'], r['profile']) for r in payload['records']] != expected_pairs:
        raise ValueError('preparation must retain all eight ordered profiles')
    with np.load(directory / 'prepared.npz', allow_pickle=False) as arrays:
        if set(arrays.files) != set(payload['array_sha256']):
            raise ValueError('prepared array inventory mismatch')
        for key, expected in payload['array_sha256'].items():
            if reg.array_hash(arrays[key]) != expected:
                raise ValueError(f'prepared array hash mismatch: {key}')
        p = arrays['p']
        if p.ndim != 1 or not np.all(np.isfinite(p) & (p > 0) & (p < 1)):
            raise ValueError('invalid stored biases')
        for record in payload['records']:
            if record['status'] == 'prepared':
                word, corr = arrays[record['word_key']], arrays[record['correlations_key']]
                if (word.shape != p.shape or corr.shape != p.shape or word.dtype != np.uint8
                        or corr.dtype != np.float32 or not np.isfinite(corr).all()
                        or not np.array_equal(word, (corr > 0).astype(np.uint8))):
                    raise ValueError('invalid stored word/correlations')
            elif 'word_key' in record or 'correlations_key' in record:
                raise ValueError('failed profile cannot contain a successful word')
    return payload


def decode_luma(rendered, source_luma, order, templates):
    residual = np.asarray(rendered, np.float32) - np.asarray(source_luma, np.float32)
    rows, cols = residual.shape[0] // 6, residual.shape[1] // 6
    blocks = (residual[:rows * 6, :cols * 6].reshape(rows, 6, cols, 6)
              .transpose(0, 2, 1, 3).reshape(rows * cols, 6, 6))
    correlations = np.sum(blocks[order] * np.asarray(templates, np.float32),
                          axis=(1, 2), dtype=np.float32)
    return correlations, (correlations > 0).astype(np.uint8)


def source_response(source_path, source_shape, p, order):
    """Render original vector/text PDF endpoints; no raster-source substitute."""
    endpoints = []
    with tempfile.TemporaryDirectory(prefix='nishan-bias-endpoints-') as temporary:
        for bit in (0, 1):
            output = Path(temporary) / f'endpoint-{bit}.pdf'
            tardos_carrier.embed_pdf(source_path, output, np.full(len(p), bit, np.uint8),
                                    SECRET, CARRIER_CONTEXT, strength=4., dpi=144, block_size=6)
            endpoints.append(watermark._luma(watermark.load_pages(output, dpi=144)[0][0]).astype(np.float64))
    height, width = source_shape
    rows, cols = height // 6, width // 6
    q = np.floor(p * 2**32) / 2**32
    blocks = np.full(rows * cols, .5)
    blocks[order] = q
    q_image = np.full(source_shape, .5)
    q_image[:rows * 6, :cols * 6] = np.repeat(np.repeat(blocks.reshape(rows, cols), 6, axis=0), 6, axis=1)
    native_midpoint, native_pilot = reg.endpoint_expectation(*endpoints, q_image)
    return {'r0': endpoints[0], 'r1': endpoints[1], 'q': q, 'q_image': q_image,
            'native_midpoint': native_midpoint, 'native_pilot': native_pilot,
            'midpoint': cv2.GaussianBlur(native_midpoint, (0, 0), .75),
            'pilot': cv2.GaussianBlur(native_pilot, (0, 0), .75)}


def prepare(gate_directory: Path, output_directory: Path) -> dict:
    output = Path(output_directory)
    if output.exists():
        raise FileExistsError(output)
    gate = validate_gate(gate_directory)
    output.mkdir(parents=True, exist_ok=False)
    cv2.setNumThreads(2)
    source_pages = watermark.load_pages(SOURCE, dpi=144)[0]
    if len(source_pages) != 1:
        raise ValueError('fixed physical fixture requires exactly one source page')
    source = source_pages[0]
    source_luma = watermark._luma(source)
    config = tardos.parameters(1000, 5, 1e-6)
    if config.code_length != 52500:
        raise ValueError('fixed profile must decode 52500 symbols')
    p = reg.keyed_biases(config, SECRET, BIAS_CONTEXT)
    rows, cols = source.shape[0] // 6, source.shape[1] // 6
    order, orientation, polarity = tardos_carrier._plan(SECRET, CARRIER_CONTEXT, rows * cols, len(p))
    templates = tardos_carrier._templates(6)[orientation] * polarity[:, None, None]
    active = np.zeros(rows * cols, bool)
    active[order] = True
    active = active.reshape(rows, cols)
    arrays = {'p': p, 'source_luma': source_luma, 'order': order, 'orientation': orientation,
              'polarity': polarity, 'active_blocks': active}
    arrays.update(source_response(SOURCE, source_luma.shape, p, order))
    payload = {'schema': 'nishan.bias-physical-preparation/v1', 'completed': True,
               'gate': gate, 'settings': settings(), 'opencv_version': cv2.__version__,
               'numpy_version': np.__version__, 'source_path': str(SOURCE),
               'source_sha256': digest(SOURCE), 'input_sha256': {},
               'code_sha256': {name: digest(ROOT / name) for name in DEPENDENCIES},
               'warnings': ['Exploratory same-page public fixture; no independent physical confirmation.',
                            'Global bounded translation cannot establish recovery from local page curvature.',
                            'No recipient roster or previous physical score JSON was loaded in preparation.',
                            'Scientific search failures remain failures; no fallback or profile selection.'],
               'records': []}
    for capture_name in CAPTURES:
        path = DOWNLOADS / capture_name
        payload['input_sha256'][str(path)] = digest(path)
        capture = watermark.load_pages(path, dpi=144)[0][0]
        common = {'capture': capture_name, 'capture_sha256': payload['input_sha256'][str(path)]}
        try:
            aligned, metrics = registration.align_page(source, capture)
            common['orb_registration'] = metrics.to_dict()
            if metrics.homography_suspect_to_reference is None:
                raise ValueError('initialization has no accepted ORB homography')
            _, ecc = refine(source, aligned, cv2.MOTION_AFFINE)
            baseline_rgb, baseline = compose_and_render(capture, source.shape,
                metrics.homography_suspect_to_reference, ecc['inverse_warp'])
            common['refinement'] = ecc
            common['baseline_raw_to_reference'] = baseline.tolist()
        except (cv2.error, ValueError, np.linalg.LinAlgError) as error:
            for profile in PROFILES:
                payload['records'].append(dict(common, profile=profile,
                    status='initialization_failed', reason=str(error)))
            print(json.dumps({'capture': capture_name, 'status': 'initialization_failed', 'reason': str(error)}), flush=True)
            continue
        search = reg.search_translation(capture, source_luma, baseline,
                                        arrays['midpoint'], arrays['pilot'], active)
        # Preserve the exact selected-pixel mask as well as Task1's hash/counts.
        coverage = reg.common_coverage(source_luma.shape, capture.shape, baseline)
        projection = reg.prepare_projection(source_luma, arrays['pilot'], coverage, active)
        mask_key = f'capture_{CAPTURES.index(capture_name)}_mask'
        arrays[mask_key] = projection['mask']
        if reg.array_hash(arrays[mask_key]) != search['mask_sha256']:
            raise ValueError('search mask reproduction mismatch')
        zero_objective = next(c['objective'] for c in search['objectives'] if c['dx'] == 0 and c['dy'] == 0)
        for profile in PROFILES:
            record = dict(common, profile=profile, mask_key=mask_key)
            if profile == 'affine_bias_translation':
                record['search'] = search
                if search['status'] != 'accepted':
                    record.update(status=search['status'], reason=search['reason'],
                                  objective=search['best_objective'], content_similarity=None)
                    payload['records'].append(record)
                    continue
                matrix = np.asarray(search['raw_to_reference'])
                rendered = reg.render_capture(capture, matrix, source_luma.shape)
                objective = search['best_objective']
            else:
                matrix = baseline
                rendered = watermark._luma(baseline_rgb)
                objective = zero_objective
            correlations, word = decode_luma(rendered, source_luma, order, templates)
            key = f'record_{len(payload["records"])}'
            arrays[key + '_word'], arrays[key + '_correlations'] = word, correlations
            record.update(status='prepared', raw_to_reference=matrix.tolist(),
                          transform_sha256=reg.array_hash(matrix), objective=objective,
                          word_key=key + '_word', correlations_key=key + '_correlations',
                          content_similarity=registration._similarity(
                              np.rint(source_luma).astype(np.uint8), np.rint(rendered).astype(np.uint8)))
            payload['records'].append(record)
        print(json.dumps({'capture': capture_name, 'baseline': 'prepared',
                          'bias_translation': search['status'], 'dx': search['dx'], 'dy': search['dy'],
                          'objective': search['best_objective'], 'statistics': search['statistics']}), flush=True)
    payload['array_sha256'] = {key: reg.array_hash(value) for key, value in arrays.items()}
    with (output / 'prepared.npz').open('xb') as handle:
        np.savez_compressed(handle, **arrays)
    dump(output / 'preparation.json', payload)
    dump(output / 'commitment.json', {'schema': 'nishan.bias-physical-commitment/v1', 'completed': True,
        'sha256': {name: digest(output / name) for name in ('preparation.json', 'prepared.npz')}})
    print(json.dumps({'completed': True, 'output': str(output),
                      'commitment_sha256': digest(output / 'commitment.json')}), flush=True)
    return payload


def load_prior_baselines():
    prior = json.loads(PRIOR.read_text())
    return {r['capture']: r for r in prior['results'] if r['profile'] == 'orb_ecc_affine'}


def compare_baseline(record, scores, prior):
    if prior is None:
        return {'status': 'missing_prior', 'scores_match': False, 'matrices_match': False}
    result = {'status': 'compared', 'rtol': 0, 'atol': 1e-9, 'scores_match': False, 'matrices_match': False}
    if record['status'] != 'scored' or prior.get('status') != 'scored':
        result['status'] = 'profile_failure'
        result['prepared_status'], result['prior_status'] = record['status'], prior.get('status')
        return result
    previous_scores = np.asarray(prior['all_scores'])
    previous_matrix = np.asarray(prior['refinement']['composed_raw_to_reference'])
    matrix = np.asarray(record['raw_to_reference'])
    result['scores_match'] = bool(scores.shape == previous_scores.shape and np.allclose(scores, previous_scores, rtol=0, atol=1e-9))
    result['matrices_match'] = bool(np.allclose(matrix, previous_matrix, rtol=0, atol=1e-9))
    result['maximum_score_difference'] = float(np.max(np.abs(scores - previous_scores))) if scores.shape == previous_scores.shape else None
    result['maximum_matrix_difference'] = float(np.max(np.abs(matrix - previous_matrix)))
    return result


def score(prepared_directory: Path, output_file: Path) -> dict:
    output = Path(output_file)
    if output.exists():
        raise FileExistsError(output)
    prepared = Path(prepared_directory)
    payload = validate_prepared(prepared)
    config = tardos.parameters(1000, 5, 1e-6)
    p, codebook = tardos.generate_keyed(config, SECRET, BIAS_CONTEXT)
    with np.load(prepared / 'prepared.npz', allow_pickle=False) as arrays:
        if not np.array_equal(p, arrays['p']):
            raise ValueError('roster biases differ from committed preparation biases')
        prior = load_prior_baselines()
        result = {'schema': 'nishan.bias-physical-scores/v1', 'completed': True,
                  'settings': payload['settings'], 'preparation_sha256': digest(prepared / 'preparation.json'),
                  'prepared_npz_sha256': digest(prepared / 'prepared.npz'),
                  'commitment_sha256': digest(prepared / 'commitment.json'),
                  'code_sha256': payload['code_sha256'], 'records': [],
                  'prior_baseline_path': str(PRIOR), 'prior_baseline_sha256': digest(PRIOR) if PRIOR.exists() else None,
                  'warnings': payload.get('warnings', []) + [
                      'Row0 is evaluation only; no score feedback or profile selection.',
                      'Conditional-independent innocent bits and finite arithmetic are not certified.',
                      'No production security guarantee or global lifetime error budget.']}
        for item in payload['records']:
            record = {k: item[k] for k in ('capture', 'profile', 'status', 'reason', 'objective',
                       'content_similarity', 'raw_to_reference') if k in item}
            scores = None
            if item['status'] == 'prepared':
                word, corr = arrays[item['word_key']], arrays[item['correlations_key']]
                scores = tardos.accusation_scores(p, codebook, word)
                null = conditional_null_threshold(p, word, 1e-6, 8000)
                accused = [] if null['threshold'] is None else np.flatnonzero(scores > null['threshold']).tolist()
                record.update(status='scored', expected_row=0, expected_score=float(scores[0]),
                    highest_other_score=float(scores[1:].max()), all_scores=scores.tolist(),
                    conditional_null=null, conditional_accused=accused, row0_accused=0 in accused,
                    historical_threshold=2100, historical_accused=np.flatnonzero(scores > 2100).tolist(),
                    bit_error_fraction=float(np.mean(word != codebook[0])),
                    zero_correlation_fraction=float(np.mean(corr == 0)),
                    word_sha256=reg.array_hash(word), correlations_sha256=reg.array_hash(corr))
            else:
                record.update(conditional_accused=[], historical_accused=[], row0_accused=False,
                              all_scores=None, conditional_null=None)
            if item['profile'] == 'affine_baseline':
                record['baseline_comparison'] = compare_baseline(record, scores, prior.get(item['capture']))
            result['records'].append(record)
            print(json.dumps({k: v for k, v in record.items() if k not in ('all_scores', 'raw_to_reference')}), flush=True)
    result['all_baseline_controls_match'] = all(r['baseline_comparison']['scores_match'] and
        r['baseline_comparison']['matrices_match'] for r in result['records'] if r['profile'] == 'affine_baseline')
    output.parent.mkdir(parents=True, exist_ok=True)
    dump(output, result)
    print(json.dumps({'completed': True, 'output': str(output), 'sha256': digest(output),
                      'all_baseline_controls_match': result['all_baseline_controls_match']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    preparation = commands.add_parser('prepare')
    preparation.add_argument('--gate', required=True, type=Path)
    preparation.add_argument('--output', required=True, type=Path)
    scoring = commands.add_parser('score')
    scoring.add_argument('--prepared', required=True, type=Path)
    scoring.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.gate, args.output)
    else:
        score(args.prepared, args.output)
