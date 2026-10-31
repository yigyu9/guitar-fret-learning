"""Shared immutable inputs for the demonstration-initialized training commands."""
from pathlib import Path
from .recording import digest, write

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT/'paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json'
BUNDLE = ROOT/'data/song_bundles/05_BN2-131-B_solo'


def pin_inputs(extra=()):
    from .prepared_reset_v1 import prepared_input_paths
    paths = {CONFIG, ROOT/'tab2body/full/events.py'} | prepared_input_paths()
    paths |= {p for p in (ROOT/'guitar_learning').rglob('*.py') if 'archive' not in p.parts}
    paths |= set((ROOT/'stability_adapter_2').rglob('*.py'))
    paths |= {p for p in BUNDLE.rglob('*') if p.is_file()}
    paths |= {Path(p).resolve() for p in extra}
    return {str(p.resolve()): digest(p) for p in sorted(paths)}


def verify_inputs(pinned):
    changed = [p for p, sha in pinned.items() if digest(p) != sha]
    if changed:
        raise RuntimeError('consumed inputs changed: '+repr(changed))
    return True
