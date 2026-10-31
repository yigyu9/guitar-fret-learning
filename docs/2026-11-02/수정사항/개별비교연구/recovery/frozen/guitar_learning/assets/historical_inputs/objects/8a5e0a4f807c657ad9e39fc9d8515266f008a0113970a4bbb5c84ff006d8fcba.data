"""Export recovery data using exact float64 codec-history validation."""
from unittest.mock import patch

from guitar_learning.tool.experiments.contact_recovery import audit as _base_audit
from guitar_learning.tool.experiments.contact_recovery import dataset as _base_dataset
from guitar_learning.tool.experiments.contact_recovery.audit_v2 import audit_capture

_ORIGINAL_EXPORT = _base_dataset.export


def export(captures, out, *, expected_contract=None):
    with patch.object(_base_audit, 'audit_capture', audit_capture):
        return _ORIGINAL_EXPORT(captures, out, expected_contract=expected_contract)


def main():
    # The original CLI retains IsaacGym-before-NumPy/Torch initialization and
    # checked JSON Observer/activation/publication for both success and failure.
    with patch.object(_base_dataset, 'export', export):
        _base_dataset.main()


if __name__ == '__main__':
    main()
