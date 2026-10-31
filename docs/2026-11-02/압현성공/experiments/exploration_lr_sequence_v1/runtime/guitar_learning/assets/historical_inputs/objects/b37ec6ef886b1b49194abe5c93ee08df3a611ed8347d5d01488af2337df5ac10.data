"""Shared compact transition records for hand timing and quality."""
import copy


def timing_compact(env, info, action):
    from guitar_learning.skills.specialist_parallel import specialist_compact
    result = specialist_compact(env, info, action)
    result['timing'] = copy.deepcopy(info['timing'])
    result['score_time_s'] = info['score_time_s']
    return result

