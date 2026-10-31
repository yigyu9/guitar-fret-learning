"""Route Fret finger targets and the prepared arm target into one owner command."""
import numpy as np


def compose_finger_play_targets(initial, source_policy_targets, held_arm_targets,
                                policy, fingers, left_arm, support, arm, prepared_left):
    desired = initial.copy()
    desired[policy] = source_policy_targets
    desired[left_arm] = prepared_left
    desired[support] = held_arm_targets[[j for j, i in enumerate(arm) if i in support]]
    assert np.array_equal(desired[left_arm], prepared_left)
    finger_slots = [j for j, i in enumerate(policy) if i in fingers]
    assert np.array_equal(desired[fingers], source_policy_targets[finger_slots])
    return desired
