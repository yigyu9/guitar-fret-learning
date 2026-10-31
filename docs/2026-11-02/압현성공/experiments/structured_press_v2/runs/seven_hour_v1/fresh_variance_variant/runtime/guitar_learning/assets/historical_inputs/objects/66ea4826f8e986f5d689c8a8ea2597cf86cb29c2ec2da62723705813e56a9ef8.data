"""CPU unit checks for R14 analytical guitar-solid penetration geometry."""
from pathlib import Path
import sys

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.safety import dof_torque_limit, guitar_solid_inside_depth


def main():
    points = torch.tensor([
        [0.0, 0.0, 0.0],       # neck center: deeply inside
        [0.0, 0.0, 0.020],     # safely above the neck
        [0.0, -0.4, -0.0217],  # guitar body center
        [0.0, -0.328, 0.0063], # raised pluck/body surface center
        [0.3, 0.3, 0.3],       # outside every solid
    ])
    depth, solid = guitar_solid_inside_depth(points)
    assert depth[0] > 0.005 and solid[0].item() == 0
    assert depth[1].item() == 0.0
    assert depth[2] > 0.015 and solid[2].item() == 1
    assert depth[3] > 0.005 and solid[3].item() == 2
    assert depth[4].item() == 0.0

    assert dof_torque_limit("LH:index2") == 20.0
    assert dof_torque_limit("LH:thumb2") == 4.0
    assert dof_torque_limit("L_Wrist_x") == 60.0
    assert dof_torque_limit("L_Elbow_y") == 100.0
    assert dof_torque_limit("L_Shoulder_z") == 150.0
    assert dof_torque_limit("Spine_x") == 300.0
    print("PASS: R14 guitar solids and finger<wrist<elbow<shoulder torque caps")


if __name__ == "__main__":
    main()
