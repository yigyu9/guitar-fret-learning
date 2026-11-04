"""IO-only successor: preserve the sealed v1 controller, task and criteria."""
import json
from pathlib import Path

from guitar_learning.tool.experiments.right_strike.runtime import verify_manifest as original_verify
from guitar_learning.tool.experiments.right_strike.runtime import write as original_write


def verify_manifest(path, expected=None):
    manifest = original_verify(path, expected)
    for source in Path(__file__).parent.glob('*.py'):
        if str(source.resolve()) not in manifest['pins']:
            raise ValueError('Every IO-v2 execution module must be pinned')
    return manifest


def write(path, value):
    """Normalize NumPy snapshot values before the original exclusive JSON writer."""
    def encode(item):
        import numpy as np
        if isinstance(item, np.ndarray):
            return item.tolist()
        if isinstance(item, np.generic):
            return item.item()
        raise TypeError('Unsupported snapshot value: '+type(item).__name__)
    normalized = json.loads(json.dumps(value, default=encode, allow_nan=False))
    return original_write(path, normalized)
