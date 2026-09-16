"""Small fail-closed checks shared by semantic module loaders."""
from __future__ import annotations

from collections.abc import Mapping

import torch


def validate_finite_state_dict(
        state_dict: Mapping[str, object], *, label: str) -> None:
    """Reject non-finite checkpoint tensors before mutating a module."""
    for name, value in state_dict.items():
        if (isinstance(value, torch.Tensor)
                and (value.is_floating_point() or value.is_complex())
                and not torch.isfinite(value).all()):
            raise RuntimeError(
                f"{label} checkpoint tensor {name!r} is non-finite")


__all__ = ["validate_finite_state_dict"]
