"""Canonical paths for curated per-song inputs.

Generated intermediates live under package-local ``_gen`` directories. Files
reviewed for use by Isaac Gym live under ``data/song_bundles/<song_id>``.
"""
from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
SONG_BUNDLES_ROOT = PROJECT_ROOT / "data" / "song_bundles"
DEFAULT_SONG_ID = "02_Jazz1-200-B_solo"


def validate_song_id(song_id: str) -> str:
    """Return a safe single-directory song identifier."""
    if not isinstance(song_id, str) or not song_id:
        raise ValueError("song_id must be a non-empty string")
    path = Path(song_id)
    if path.name != song_id or song_id in {".", ".."}:
        raise ValueError(f"song_id must be one path component: {song_id!r}")
    return song_id


def bundle_path(song_id: str = DEFAULT_SONG_ID) -> Path:
    return SONG_BUNDLES_ROOT / validate_song_id(song_id)


def audio_path(song_id: str = DEFAULT_SONG_ID) -> Path:
    return bundle_path(song_id) / "source" / "audio.wav"


def fret_goal_path(song_id: str = DEFAULT_SONG_ID) -> Path:
    return bundle_path(song_id) / "training" / "fret_training.json"


def hand_targets_path(song_id: str = DEFAULT_SONG_ID) -> Path:
    return bundle_path(song_id) / "training" / "hand_position_targets.json"


def strike_goal_path(song_id: str = DEFAULT_SONG_ID) -> Path:
    return bundle_path(song_id) / "training" / "strike_training.json"


def song_id_from_training_path(path: str | Path, suffix: str) -> str:
    """Resolve identity from either a canonical bundle or a legacy filename."""
    path = Path(path).resolve()
    try:
        relative = path.relative_to(SONG_BUNDLES_ROOT.resolve())
    except ValueError:
        relative = None
    if relative is not None and len(relative.parts) >= 3:
        return relative.parts[0]
    return path.name[:-len(suffix)] if path.name.endswith(suffix) else path.stem
