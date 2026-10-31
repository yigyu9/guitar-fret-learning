"""Audit migrated native inputs against their original baseline identities."""
import json
from pathlib import Path
from guitar_learning.native.paths import PROVENANCE, original_input_path, resolve_input_path, verify_provenance
from guitar_learning.training.training_log_io import digest


def parity_errors(paths, expected):
    """Require both the recorded original SHA and the current internal SHA."""
    verify_provenance()
    manifest = json.loads(PROVENANCE.read_text())
    moved = {row['internal']: row for row in manifest['files']}
    generated = {row['internal'] for row in manifest.get('generated_files', [])}
    errors = []
    for path in paths:
        path = str(Path(path).resolve())
        if path in generated:
            continue  # New resolver/package files were checked by provenance above.
        row = moved.get(path)
        original = str(original_input_path(path))
        wanted = expected.get(original)
        actual = row['original_sha256'] if row else digest(path)
        if wanted != actual:
            errors.append(path)
    return sorted(errors)


def pin_evidence(pin, config, extra, evidence):
    """Pin current execution and exact historical evidence as distinct inputs."""
    from guitar_learning.historical_inputs import evidence_input_pins, fingerprint_paths
    required = {}
    for path, sha in evidence_input_pins(evidence).items():
        local = str(resolve_input_path(path))
        if local in required and required[local] != sha:
            raise RuntimeError('conflicting relocated physical evidence SHA')
        required[local] = sha
    sources = set(extra) | set(required)
    result = pin(config, extra=sources)
    if any(result.get(path) != sha for path, sha in required.items()):
        raise RuntimeError('initialization physical evidence changed while pinning')
    if fingerprint_paths(evidence) != evidence:
        raise RuntimeError('initialization evidence changed while pinning')
    return result
