"""Frozen profiles and replay-safe scoring for the compact-carrier pilot."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

import numpy as np

from nishan import tardos


ROSTER_SIZE = 1000
COALITION_LIMIT = 5
FAMILYWISE_EPSILON = 1.0e-6
DPI = 144
STRENGTH = 4.0
SYMMETRIC_CUTOFF = 1.0 / 141.55
SYMMETRIC_THRESHOLD = 837.2843088602898


@dataclass(frozen=True)
class CarrierProfile:
    name: str
    logical_positions: int
    block_size: int
    repetitions: int
    physical_placements: int
    nominal_pixels: int
    threshold: float
    scorer: str
    family: str


_PROFILE_SEQUENCE = (
    CarrierProfile(
        name="original-6-r1",
        logical_positions=52500,
        block_size=6,
        repetitions=1,
        physical_placements=52500,
        nominal_pixels=1890000,
        threshold=2100.0,
        scorer="original-one-sided",
        family="original",
    ),
    CarrierProfile(
        name="symmetric-6-r4",
        logical_positions=12331,
        block_size=6,
        repetitions=4,
        physical_placements=49324,
        nominal_pixels=1775664,
        threshold=SYMMETRIC_THRESHOLD,
        scorer="symmetric-signed",
        family="symmetric",
    ),
    CarrierProfile(
        name="symmetric-12-r1",
        logical_positions=12331,
        block_size=12,
        repetitions=1,
        physical_placements=12331,
        nominal_pixels=1775664,
        threshold=SYMMETRIC_THRESHOLD,
        scorer="symmetric-signed",
        family="symmetric",
    ),
)

PROFILES: Mapping[str, CarrierProfile] = MappingProxyType(
    {profile.name: profile for profile in _PROFILE_SEQUENCE}
)


def original_configuration() -> tardos.Parameters:
    config = tardos.parameters(ROSTER_SIZE, COALITION_LIMIT, FAMILYWISE_EPSILON)
    if config.code_length != 52500 or config.threshold != 2100.0:
        raise RuntimeError("imported original profile no longer matches the frozen pilot")
    return config


def symmetric_configuration() -> tardos.Parameters:
    """Return an explicitly empirical Parameters-shaped generator input."""

    return replace(
        original_configuration(),
        code_length=12331,
        cutoff=SYMMETRIC_CUTOFF,
        threshold=SYMMETRIC_THRESHOLD,
        theorem_profile=(
            "Empirical symmetric carrier pilot; inherited keyed sampler baseline; "
            "not theorem-certified"
        ),
    )


def profile_manifest(profile: CarrierProfile) -> dict[str, object]:
    result = asdict(profile)
    result.update({"dpi": DPI, "strength": STRENGTH, "theorem_certified": False})
    return result


def symmetric_scores(
    codebook: np.ndarray,
    biases: np.ndarray,
    word: np.ndarray,
) -> np.ndarray:
    """Compute the frozen empirical symbol-symmetric score for every row."""

    codebook = np.asarray(codebook)
    biases = np.asarray(biases, dtype=np.float64)
    word = np.asarray(word)
    if codebook.ndim != 2:
        raise ValueError("codebook must be 2-D")
    if biases.shape != (codebook.shape[1],):
        raise ValueError("bias vector length does not match codebook")
    if word.shape != (codebook.shape[1],):
        raise ValueError("word length does not match codebook")
    if not np.all(np.isfinite(biases)) or np.any(biases <= 0.0) or np.any(
        biases >= 1.0
    ):
        raise ValueError("biases must be finite and strictly between zero and one")
    if np.any((codebook != 0) & (codebook != 1)):
        raise ValueError("codebook must be binary")
    if np.any((word != 0) & (word != 1)):
        raise ValueError("word must be binary")

    signed_output = 2.0 * word.astype(np.float64) - 1.0
    weights = signed_output / np.sqrt(biases * (1.0 - biases))
    scores = np.empty(codebook.shape[0], dtype=np.float64)
    for start in range(0, codebook.shape[0], 32):
        chunk = codebook[start : start + 32].astype(np.float64)
        scores[start : start + 32] = ((chunk - biases) * weights).sum(axis=1)
    if not np.all(np.isfinite(scores)):
        raise ValueError("score calculation produced a non-finite value")
    return scores


def collapse_correlations(
    correlations: np.ndarray,
    logical_positions: int,
    repetitions: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Sum analog repetitions before applying the strict positive-bit decision."""

    correlations = np.asarray(correlations, dtype=np.float64)
    if logical_positions < 1 or repetitions < 1:
        raise ValueError("logical_positions and repetitions must be positive")
    if correlations.ndim != 1:
        raise ValueError("correlations must be one-dimensional")
    if correlations.shape != (logical_positions * repetitions,):
        raise ValueError("correlation length does not match profile dimensions")
    if not np.all(np.isfinite(correlations)):
        raise ValueError("correlations must be finite")
    summed = correlations.reshape(repetitions, logical_positions).sum(axis=0)
    word = (summed > 0.0).astype(np.uint8)
    return word, summed


def sha3_file(path: Path) -> str:
    digest = hashlib.sha3_256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def array_commitment(array: np.ndarray, dtype: str) -> str:
    return hashlib.sha3_256(
        np.ascontiguousarray(array, dtype=dtype).tobytes()
    ).hexdigest()


def read_manifest(run: Path) -> dict[str, object]:
    manifest_path = run / "manifest.json"
    try:
        value = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read a valid run manifest: {error}") from error
    if not isinstance(value, dict):
        raise ValueError("run manifest must be a JSON object")
    return value


def load_replay_state(
    run: Path,
    manifest: dict[str, object] | None = None,
) -> dict[str, np.ndarray]:
    """Verify public commitments before loading the private, pickle-free NPZ."""

    run = Path(run)
    manifest = read_manifest(run) if manifest is None else manifest
    replay_metadata = manifest.get("private_replay")
    if not isinstance(replay_metadata, dict):
        raise ValueError("manifest lacks private replay metadata")
    relative = replay_metadata.get("path")
    expected_hash = replay_metadata.get("sha3_256")
    if relative != "private/replay-state.npz" or not _is_sha3_256(expected_hash):
        raise ValueError("manifest private replay metadata is invalid")
    replay_path = run / relative
    if not replay_path.is_file() or sha3_file(replay_path) != expected_hash:
        raise ValueError("replay-state hash mismatch")

    source_metadata = manifest.get("source")
    if not isinstance(source_metadata, dict):
        raise ValueError("manifest lacks valid source metadata")
    source_relative = source_metadata.get("run_path")
    source_input = source_metadata.get("input_path")
    source_hash = source_metadata.get("sha3_256")
    if (
        source_relative != "source/synthetic-source.pdf"
        or source_input != "artifacts/nishan/synthetic-source.pdf"
        or not _is_sha3_256(source_hash)
    ):
        raise ValueError("manifest source commitment is invalid")
    source_path = run / source_relative
    if not source_path.is_file() or sha3_file(source_path) != source_hash:
        raise ValueError("source hash mismatch")

    families = manifest.get("families")
    if not isinstance(families, dict) or set(families) != {"original", "symmetric"}:
        raise ValueError("manifest lacks complete family commitments")
    expected_shapes = {"original": [ROSTER_SIZE, 52500], "symmetric": [ROSTER_SIZE, 12331]}
    for family in ("original", "symmetric"):
        metadata = families.get(family)
        if not isinstance(metadata, dict):
            raise ValueError(f"manifest lacks {family} family commitments")
        if (
            not _is_sha3_256(metadata.get("biases_sha3_256"))
            or not _is_sha3_256(metadata.get("codebook_sha3_256"))
            or metadata.get("codebook_shape") != expected_shapes[family]
        ):
            raise ValueError(f"manifest {family} family commitments are invalid")

    try:
        with np.load(replay_path, allow_pickle=False) as archive:
            state = {name: np.array(archive[name], copy=True) for name in archive.files}
    except (OSError, ValueError, KeyError) as error:
        raise ValueError(f"private replay state is invalid: {error}") from error

    required = {
        "original_biases",
        "original_codebook",
        "original_key",
        "symmetric_biases",
        "symmetric_codebook",
        "symmetric_key",
        "carrier_key",
        "wrong_carrier_key",
        "context_uuid",
    }
    if set(state) != required:
        raise ValueError("private replay state has unexpected fields")
    if state["original_biases"].shape != (52500,) or state[
        "original_codebook"
    ].shape != (ROSTER_SIZE, 52500):
        raise ValueError("original replay arrays have invalid shapes")
    if state["symmetric_biases"].shape != (12331,) or state[
        "symmetric_codebook"
    ].shape != (ROSTER_SIZE, 12331):
        raise ValueError("symmetric replay arrays have invalid shapes")
    for key_name in ("original_key", "symmetric_key", "carrier_key", "wrong_carrier_key"):
        if state[key_name].dtype != np.uint8 or state[key_name].shape != (32,):
            raise ValueError(f"{key_name} has invalid encoding")
    if state["context_uuid"].shape != () or state["context_uuid"].dtype.kind not in {
        "S",
        "U",
    }:
        raise ValueError("context UUID has invalid encoding")

    for family, bias_name, codebook_name in (
        ("original", "original_biases", "original_codebook"),
        ("symmetric", "symmetric_biases", "symmetric_codebook"),
    ):
        metadata = families[family]
        if array_commitment(state[bias_name], "<f8") != metadata.get(
            "biases_sha3_256"
        ):
            raise ValueError(f"{family} bias commitment mismatch")
        if array_commitment(state[codebook_name], "u1") != metadata.get(
            "codebook_sha3_256"
        ):
            raise ValueError(f"{family} codebook commitment mismatch")
    return state


def _is_sha3_256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def context_for_profile(context_uuid: str, profile_name: str) -> str:
    if profile_name not in PROFILES:
        raise ValueError(f"unknown frozen profile: {profile_name}")
    return f"{context_uuid}/compact-carrier-v1/{profile_name}"


def decode_context_uuid(state: dict[str, np.ndarray]) -> str:
    value = state["context_uuid"].item()
    return value.decode("utf-8") if isinstance(value, bytes) else str(value)
