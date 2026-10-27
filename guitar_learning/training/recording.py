"""Shared source census and result serialization for native probes."""
import gzip
import hashlib
from guitar_learning.training import json_io
from pathlib import Path


def bridge_dependency(filename):
    if '/guitar_learning/native/' in filename:
        return False
    return any('/' + folder + '/' in filename for folder in ('guitar_learning', 'free_guitar_learning_v1', 'music_pipeline_v2', 'music_pipeline_v3'))


def project_source_paths(modules):
    """Namespace packages have __file__=None and are not source-file entries."""
    paths = set()
    for name, module in modules:
        filename = getattr(module, '__file__', None)
        if (name == 'guitar_learning' or name.startswith('guitar_learning.')) and isinstance(filename, str) and filename.endswith('.py'):
            paths.add(str(Path(filename).resolve()))
    return paths


def active_source_paths(folder):
    """Collect Python inputs without traversing archived directories or links."""
    paths = set()
    for path in Path(folder).iterdir():
        if path.name == 'archive':
            continue
        if path.is_dir() and not path.is_symlink():
            paths.update(active_source_paths(path))
        elif path.suffix == '.py':
            paths.add(path)
    return paths


def digest(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def write(path, value, compressed=False):
    import numpy as np
    def encode(value):
        if isinstance(value, np.ndarray):
            return value.tolist()
        if isinstance(value, np.generic):
            return value.item()
        raise TypeError(type(value).__name__)
    opener = gzip.open if compressed else open
    with opener(path, 'xt') as stream:
        json_io.dump(value, stream, allow_nan=False, default=encode)
        stream.write('\n')
