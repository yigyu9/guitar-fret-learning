"""Shared immutable inputs for the demonstration-initialized training commands."""
from pathlib import Path
from guitar_learning.training.recording import digest, write
from guitar_learning.native.paths import resolve_input_path, PROVENANCE, verify_provenance
from guitar_learning.core.dependency_inputs import pin_evidence
from collections.abc import Mapping

ROOT = Path(__file__).resolve().parents[2]
CONFIG = resolve_input_path(ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json')
BUNDLE = ROOT/'data/song_bundles/05_BN2-131-B_solo'


def pin_inputs(extra=()):
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths
    if isinstance(extra, Mapping):
        return pin_inputs_with_evidence((), extra)
    verify_provenance()
    paths = {CONFIG, PROVENANCE, ROOT/'guitar_learning/score/canonical.py'} | prepared_input_paths()
    paths |= {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    paths |= set((ROOT/'guitar_learning/native').rglob('*.py'))
    paths |= {p for p in BUNDLE.rglob('*') if p.is_file()}
    paths |= {resolve_input_path(p) for p in extra}
    return {str(p.resolve()): digest(p) for p in sorted(paths)}


def pin_inputs_with_evidence(extra, evidence):
    """Keep the saved proof identity separate from current execution source pins."""
    return pin_evidence(lambda config, extra: pin_inputs(extra), None, extra, evidence)


def verify_inputs(pinned):
    verify_provenance()
    changed = [p for p, sha in pinned.items() if digest(p) != sha]
    if changed:
        raise RuntimeError('consumed inputs changed: '+repr(changed))
    return True
