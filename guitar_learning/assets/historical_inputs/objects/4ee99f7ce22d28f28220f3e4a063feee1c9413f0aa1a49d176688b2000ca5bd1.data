"""CPU geometry checks for the diagnostic-only R22 capsule proxy."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.safety import segment_segment_distance


def main():
    # Interior crossing must be caught (endpoint-only checks would miss this).
    a0 = torch.tensor([[-1.0, 0.0, 0.0]])
    a1 = torch.tensor([[1.0, 0.0, 0.0]])
    b0 = torch.tensor([[0.0, -1.0, 0.0]])
    b1 = torch.tensor([[0.0, 1.0, 0.0]])
    assert torch.allclose(segment_segment_distance(a0, a1, b0, b1), torch.zeros(1))

    # Parallel, separated and endpoint-nearest cases.
    b0 = torch.tensor([[-1.0, 0.020, 0.0]])
    b1 = torch.tensor([[1.0, 0.020, 0.0]])
    assert torch.allclose(segment_segment_distance(a0, a1, b0, b1),
                          torch.tensor([0.020]), atol=1e-6)
    b0 = torch.tensor([[2.0, 0.030, 0.0]])
    b1 = torch.tensor([[3.0, 0.030, 0.0]])
    expected = torch.sqrt(torch.tensor(1.0 + 0.030 ** 2))
    assert torch.allclose(segment_segment_distance(a0, a1, b0, b1),
                          expected[None], atol=1e-6)

    # Broadcasted 3x3 segment-pair grid, matching the runtime monitor layout.
    starts_a = torch.zeros(2, 3, 1, 3)
    ends_a = starts_a.clone(); ends_a[..., 0] = 1.0
    starts_b = torch.zeros(2, 1, 3, 3); starts_b[..., 1] = 0.05
    ends_b = starts_b.clone(); ends_b[..., 0] = 1.0
    grid = segment_segment_distance(starts_a, ends_a, starts_b, ends_b)
    assert grid.shape == (2, 3, 3)
    assert torch.allclose(grid, torch.full_like(grid, 0.05))
    print("PASS: R22 exact segment distance and broadcast capsule-pair geometry")


if __name__ == "__main__":
    main()
