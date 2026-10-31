"""Joint ownership and initial-reference target composition, in radians."""
import numpy as np

MAIN_PREFIXES = (
    "L_Thorax", "L_Shoulder", "L_Elbow", "L_Wrist", "LH:",
    "R_Thorax", "R_Shoulder", "R_Elbow", "R_Wrist", "RH:",
)
TORSO_PREFIXES = ("Torso", "Spine", "Chest")


def control_indices(names):
    if len(set(names)) != len(names):
        raise ValueError("duplicate joint names")
    main = np.array([i for i, n in enumerate(names) if n.startswith(MAIN_PREFIXES)])
    torso = np.array([i for i, n in enumerate(names) if n.startswith(TORSO_PREFIXES)])
    for prefix in MAIN_PREFIXES + TORSO_PREFIXES:
        expected = 21 if prefix in ("LH:", "RH:") else 3
        if sum(n.startswith(prefix) for n in names) != expected:
            raise ValueError("joint layout mismatch for " + prefix)
    return main, torso


def compose_targets(initial, main_indices, offsets, lower, upper):
    offsets = np.asarray(offsets, dtype=np.float32)
    if offsets.shape != main_indices.shape or not np.isfinite(offsets).all():
        raise ValueError("main offsets must be a finite 66-vector in radians")
    target = initial.copy()
    target[main_indices] = np.clip(initial[main_indices] + offsets,
                                   lower[main_indices], upper[main_indices])
    return target
