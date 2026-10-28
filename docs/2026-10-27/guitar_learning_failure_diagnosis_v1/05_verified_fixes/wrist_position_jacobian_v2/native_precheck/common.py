"""Fixed index precheck paths and output guard; no active/native import."""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIAG = HERE.parents[2]
ROOT = DIAG.parents[2]
OLD = DIAG/'03_short_learning/other_finger_precheck_v3'
OLD_INITIAL = OLD/'runs/index_initial/initial.pt'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def reject_existing(path):
    if path.exists() or path.is_symlink():
        raise FileExistsError(str(path))


def owned(out, identity):
    return identity is not None and out.is_dir() and (out.stat().st_dev, out.stat().st_ino) == identity


def reused():
    spec = importlib.util.spec_from_file_location('wrist_v2_original_prechecks', OLD/'run_prechecks.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
