"""Fixed, bounded observation contract; no native import."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[1]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'
VIDEO = OLD/'native_video_index_reference'
CHECKPOINT = OLD/'runs/index_initial/initial.pt'
CLOCKS = (476, 596, 716, 776)
LIMIT = 4_000_000


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def reused():
    spec = importlib.util.spec_from_file_location('coordinate_original_prechecks', OLD/'run_prechecks.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def owned(out, identity):
    return identity is not None and out.is_dir() and (out.stat().st_dev, out.stat().st_ino) == identity


def reject_existing(out):
    if out.exists() or out.is_symlink():
        raise FileExistsError(str(out))


def protocol():
    return dict(schema='jacobian_position_coordinate_audit.v1', environments=4,
        start_clocks=list(CLOCKS), native_jacobian_shape=[4, 65, 6, 105],
        uncompressed_byte_limit=LIMIT, control='reference', checkpoint=str(CHECKPOINT),
        hook='before original ShortPool.step; snapshot clones only; original step exactly once',
        native_J='raw fixed-base human tensor; human body i uses row i-1; production helper assumes world linear COM/angular rows and native qd columns; frame/COM/coordinate audit pending',
        scope='coordinate diagnosis only; unchanged fixed-guitar reference; not policy performance')
