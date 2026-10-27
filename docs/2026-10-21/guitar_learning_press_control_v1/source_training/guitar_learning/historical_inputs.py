"""Revalidate immutable source bytes pinned by historical learning evidence.

Historical code is data only. Current execution sources are fingerprinted
separately; passing an old evidence manifest never imports its old program.
"""
from collections.abc import Mapping
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path

_STORE = Path(__file__).resolve().parent / 'assets/historical_inputs'
_PROJECT = Path(__file__).resolve().parents[1]
_LEGACY_ROOTS = tuple(str(_PROJECT / name) + '/' for name in ('tab2body', 'stability_adapter_2'))


@lru_cache(maxsize=1)
def _index():
    document = json.loads((_STORE / 'index.json').read_text())
    if document.get('schema') != 'guitar_learning.historical_inputs.v1':
        raise ValueError('unsupported historical input index')
    return document['entries']


def _digest(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def _checked_sha(value):
    if (not isinstance(value, str) or len(value) != 64
            or any(char not in '0123456789abcdef' for char in value)):
        raise ValueError('expected input SHA256 must be lowercase hexadecimal')
    return value


def fingerprint_paths(paths):
    """Hash live inputs or verify exact preserved versions of historical inputs.

    A Mapping supplies expected SHA256 values and retains its original keys.
    Registered historical (path, SHA) versions are rehashed from internal data.
    All other Mapping entries require the exact live SHA. For an iterable,
    current paths use the live file, while legacy paths use their unique sealed
    original version. Unknown legacy paths never fall back to the old folders.
    """
    expected = paths if isinstance(paths, Mapping) else None
    result = {}
    for source in paths:
        # Normalize legacy names lexically: resolving symlinks would inspect
        # removed external directories before selecting their preserved bytes.
        lexical = os.path.abspath(os.fspath(source))
        legacy = lexical.startswith(_LEGACY_ROOTS)
        wanted = _checked_sha(expected[source]) if expected is not None else None
        entry = _index().get(lexical) if legacy or wanted is not None else None
        if legacy and wanted is None:
            wanted = entry.get('default_sha256') if entry else None
            if wanted is None:
                raise ValueError('unknown or ambiguous historical input: ' + lexical)
        if entry and wanted in entry['versions']:
            actual = _digest(_STORE / 'objects' / (wanted + '.data'))
            if actual != wanted:
                raise RuntimeError('historical input SHA mismatch: ' + lexical)
            key = source if expected is not None else lexical
        elif legacy:
            raise ValueError('unknown historical input SHA: ' + lexical)
        else:
            path = Path(source).resolve()
            actual = _digest(path)
            if wanted is not None and actual != wanted:
                raise RuntimeError('live input SHA mismatch: ' + str(path))
            key = source if expected is not None else str(path)
        result[key] = actual
    return result


def evidence_input_pins(expected):
    """Return required physical SHA values for an exact evidence Mapping.

    Required source SHA values survive the conversion to physical paths; a
    subsequent census must compare its readback against these original values.
    """
    if not isinstance(expected, Mapping):
        raise TypeError('expected input SHA Mapping required')
    fingerprint_paths(expected)
    pins = {}

    def require(path, sha):
        key = str(path)
        if key in pins and pins[key] != sha:
            raise RuntimeError('conflicting physical evidence SHA: ' + key)
        pins[key] = sha

    for source, wanted in expected.items():
        lexical = os.path.abspath(os.fspath(source))
        entry = _index().get(lexical)
        if entry and wanted in entry['versions']:
            index_path = _STORE / 'index.json'
            if str(index_path) not in pins:
                require(index_path, _digest(index_path))
            require(_STORE / 'objects' / (wanted + '.data'), wanted)
        else:
            require(Path(source).resolve(), wanted)
    return pins


def evidence_input_paths(expected):
    """Return consumed paths while preserving the exact evidence Mapping."""
    return {Path(path) for path in evidence_input_pins(expected)}
