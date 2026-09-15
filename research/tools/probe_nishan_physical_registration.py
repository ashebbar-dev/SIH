#!/usr/bin/env python3
"""Fixed exploratory registration diagnostic; no production changes.

Prespecified before scoring: all four akshay captures, original ORB alignment,
then ECC affine and homography refinements independently initialized from that
same ORB result. Each refinement uses source/capture pixels only. No recipient
scores select registration, parameters or a preferred decoder. Existing hard
scores and the already reviewed conditional-null helper score all 1000 rows.
H=4*3*1000 and epsilon=1e-6 apply only to this diagnostic family.
"""

from pathlib import Path
import argparse
import hashlib
import json
import sys

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from research.tools.probe_nishan_capture_channel import (  # noqa: E402
    conditional_null_threshold, tardos, tardos_carrier, watermark,
)
from nishan import registration  # noqa: E402

CAPTURES = ('akshay.jpeg', 'akshay1.jpeg', 'akshay2.jpeg', 'akshay3.jpeg')
PROFILES = (('orb', None), ('orb_ecc_affine', cv2.MOTION_AFFINE),
            ('orb_ecc_homography', cv2.MOTION_HOMOGRAPHY))


def refine(source, aligned, motion):
    """Return ECC refinement; ECC warp maps source coordinates into input."""
    matrix = np.eye(3, dtype=np.float32)
    if motion != cv2.MOTION_HOMOGRAPHY:
        matrix = matrix[:2]
    gray = lambda a: cv2.cvtColor(a, cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
    coefficient, matrix = cv2.findTransformECC(
        gray(source), gray(aligned), matrix, motion,
        (cv2.TERM_CRITERIA_COUNT | cv2.TERM_CRITERIA_EPS, 200, 1e-6), None, 5,
    )
    warp = cv2.warpPerspective if motion == cv2.MOTION_HOMOGRAPHY else cv2.warpAffine
    result = warp(aligned, matrix, (source.shape[1], source.shape[0]),
                  flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP,
                  borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))
    return result, {'ecc_coefficient': float(coefficient), 'inverse_warp': matrix.tolist()}


def self_check():
    """Check warp direction on a known translation before physical scoring."""
    source = np.full((240, 320, 3), 245, np.uint8)
    rng = np.random.default_rng(42)
    for _ in range(20):
        x, y = rng.integers(30, 190, size=2)
        cv2.rectangle(source, (int(x), int(y)), (int(x + 20), int(y + 10)), (30, 30, 30), -1)
    shifted = cv2.warpAffine(source, np.float32([[1, 0, 2], [0, 1, -1]]),
                             (320, 240), borderValue=(245, 245, 245))
    for _, mode in PROFILES[1:]:
        result, metrics = refine(source, shifted, mode)
        np.testing.assert_allclose(np.asarray(metrics['inverse_warp'])[:2, 2], [2, -1], atol=.15)
        before = np.mean(np.abs(shifted[10:-10, 10:-10].astype(float) - source[10:-10, 10:-10]))
        after = np.mean(np.abs(result[10:-10, 10:-10].astype(float) - source[10:-10, 10:-10]))
        assert after < before / 5, (mode, before, after)


def run(output):
    if output.exists():
        raise FileExistsError(output)
    cv2.setNumThreads(2)
    self_check()
    source_path = ROOT / 'artifacts/nishan/synthetic-source.pdf'
    source = watermark.load_pages(source_path, dpi=144)[0][0]
    secret = hashlib.sha3_256(b'NISHAN Tardos carrier public fixture v1').digest()
    config = tardos.parameters(1000, 5, 1e-6)
    p, codebook = tardos.generate_keyed(config, secret, 'public-benchmark-codebook/v1')
    rows, cols = source.shape[0] // 6, source.shape[1] // 6
    order, orientation, polarity = tardos_carrier._plan(
        secret, 'synthetic-source/full-tardos-profile-v1', rows * cols, config.code_length)
    templates = tardos_carrier._templates(6)[orientation] * polarity[:, None, None]
    prior = json.loads((ROOT / 'research/evidence/nishan-physical-conditional-2026-09-10.json').read_text())
    prior = {Path(r['file']).name: r for r in prior['captures']}
    payload = {'schema': 'nishan.physical-registration-diagnostic/v1',
               'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'helper_sha256': hashlib.sha256((ROOT / 'research/tools/probe_nishan_capture_channel.py').read_bytes()).hexdigest(),
               'source_sha256': hashlib.sha256(source_path.read_bytes()).hexdigest(),
               'opencv_version': cv2.__version__, 'self_check_passed': True,
               'fixed_config': {'captures': list(CAPTURES), 'profiles': [p[0] for p in PROFILES],
                                'max_iterations': 200, 'epsilon_stop': 1e-6, 'gaussian_size': 5,
                                'family_epsilon': 1e-6, 'hypotheses': 12000},
               'limitations': ['Exploratory same-page/public-codebook research, not independent confirmation.',
                               'ECC and conditional Chernoff calibration are established methods, not novelty.',
                               'Conditional-independent innocent bits and finite arithmetic are not certified.',
                               'No physical production guarantee or global lifetime error budget.',
                               'No profile selection; failed refinements remain explicit failures.'], 'results': []}
    for name in CAPTURES:
        path = Path('/home/user_end4/Downloads') / name
        capture = watermark.load_pages(path, dpi=144)[0][0]
        aligned, baseline_metrics = registration.align_page(source, capture)
        for profile, mode in PROFILES:
            item = {'capture': name, 'capture_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                    'profile': profile, 'orb_registration': baseline_metrics.to_dict()}
            try:
                candidate, metrics = ((aligned, {}) if mode is None else refine(source, aligned, mode))
            except cv2.error as error:
                item.update(status='refinement_failed', error=str(error))
                payload['results'].append(item)
                print(json.dumps(item), flush=True)
                continue
            residual = watermark._luma(candidate) - watermark._luma(source)
            blocks = (residual[:rows * 6, :cols * 6].reshape(rows, 6, cols, 6)
                      .transpose(0, 2, 1, 3).reshape(rows * cols, 6, 6))
            correlations = np.sum(blocks[order] * templates, axis=(1, 2))
            word = (correlations > 0).astype(np.uint8)
            scores = tardos.accusation_scores(p, codebook, word)
            if mode is None:
                np.testing.assert_allclose(scores, prior[name]['all_scores'], rtol=0, atol=1e-9)
            null = conditional_null_threshold(p, word, 1e-6, 12000)
            accused = [] if null['threshold'] is None else np.flatnonzero(scores > null['threshold']).tolist()
            item.update(status='scored', refinement=metrics, expected_score=float(scores[0]),
                        highest_other_score=float(scores[1:].max()),
                        historical_accused=tardos.accuse(scores, config).tolist(),
                        conditional_null=null, conditional_accused=accused,
                        bit_error_fraction=float(np.mean(word != codebook[0])),
                        zero_correlation_fraction=float(np.mean(correlations == 0)),
                        content_similarity=registration._similarity(registration._gray(source), registration._gray(candidate)))
            print(json.dumps(item), flush=True)
            item['all_scores'] = scores.tolist()
            payload['results'].append(item)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open('x') as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.output)
