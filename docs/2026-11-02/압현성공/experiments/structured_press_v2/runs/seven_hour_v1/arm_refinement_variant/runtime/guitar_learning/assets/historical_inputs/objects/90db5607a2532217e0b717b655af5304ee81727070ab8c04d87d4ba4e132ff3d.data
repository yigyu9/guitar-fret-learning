"""Resolve runtime files locally while retaining original evidence identities."""
import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NATIVE = Path(__file__).resolve().parent
ASSETS = NATIVE.parent / 'assets'
A = ASSETS / 'stability_adapter_2'
PROVENANCE = ASSETS / 'native_provenance.json'


@lru_cache(maxsize=1)
def provenance_records():
    return tuple(json.loads(PROVENANCE.read_text())['files'])


@lru_cache(maxsize=1)
def _mapping():
    forward = {str(Path(row['original']).resolve()): Path(row['internal']) for row in provenance_records()}
    reverse = {str(path.resolve()): Path(original) for original, path in forward.items()}
    return forward, reverse


def resolve_input_path(path):
    """Map an original absolute/project-relative input to its internal copy."""
    path = Path(path)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    internal = _mapping()[0].get(str(path))
    if internal is not None:
        return internal
    if any((ROOT / name) in path.parents for name in ('tab2body', 'stability_adapter_2')):
        raise FileNotFoundError('Legacy runtime input has no internal copy: ' + str(path))
    return path


def original_input_path(path):
    """Return the original recorded identity for a moved input or native module."""
    path = Path(path).resolve()
    return _mapping()[1].get(str(path), path)


def rebase_paths(value):
    """Rebase known input path values, leaving proof keys and numeric data intact."""
    if isinstance(value, dict):
        return {key: rebase_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [rebase_paths(item) for item in value]
    if isinstance(value, str):
        if value.startswith('/') or value.startswith(('tab2body/', 'stability_adapter_2/', 'paper/', 'docs/')):
            path = Path(value)
            original = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
            resolved = _mapping()[0].get(str(original))
            if resolved is not None:
                return str(resolved)
    return value


def verify_provenance():
    """Verify current bytes against the explicit migration manifest, on every call."""
    import hashlib
    manifest = json.loads(PROVENANCE.read_text())
    records = manifest['files'] + manifest.get('generated_files', [])
    for row in records:
        path = Path(row['internal'])
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['internal_sha256']:
            raise ValueError('Internal native provenance SHA mismatch: ' + str(path))
    return {'verified_files': len(records), 'manifest': str(PROVENANCE)}
