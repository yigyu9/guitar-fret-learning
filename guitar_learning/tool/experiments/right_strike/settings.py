"""Original legacy GPU-right settings with one verified diagnostic task."""
from pathlib import Path

from .prepare import DEFAULT_INPUT, TARGET_SPEC, validate_inputs


def build_settings(bundle=DEFAULT_INPUT, *, updates=100, num_envs=64, horizon=32,
                   size='medium', seed=7):
    from guitar_learning.training.launch import build_settings as original_settings
    task = validate_inputs(bundle)
    settings = original_settings('right', learning_family='song',
        song='virtual_finger_v9_middle_s3_f6', updates=updates, num_envs=num_envs,
        horizon=horizon, size=size, seed=seed, device='cuda:0', physics='gpu')
    settings['phrase_events'] = task.provenance['song']['source_event_count']
    settings['song_training'].update(song_id=Path(bundle).name, bundle=str(Path(bundle).resolve()),
        target_count=len(task.targets), control_ticks=task.provenance['song']['control_ticks'],
        episode_duration_s=task.duration_s)
    settings['right_strike'] = dict(schema='guitar_learning.right_strike.v1',
        condition=TARGET_SPEC['condition'], target_ids=[target.target_id for target in task.targets],
        runtime_string=2, standard_string_1based=3, direction=1, onset_s=3., episode_duration_s=5.,
        reward_original=True, left_clean_required=False,
        scope='Right-hand pick crossing diagnostics; no left pressure, pitch or acoustic success assertion')
    return settings
