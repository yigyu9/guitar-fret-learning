"""Shared input validation and settings for current and explicit legacy launchers."""
from pathlib import Path


DEFAULT_SONG = '05_BN2-131-B_solo'


def settings_document(hand, *, song=DEFAULT_SONG, updates=100, num_envs=None,
                      device='cuda:0', seed=7, horizon=None, size='medium', physics='auto',
                      checkpoint_every=250, finger_standby_rate=None, finger_shape=False,
                      finger_action_mode=None, learning_family='song', skill_phase='auto',
                      skill_exploration='independent', skill_hold_ticks=1, skill_scope=None):
    """Use every source note; a collection boundary never ends the song."""
    if hand not in ('left', 'right'):
        raise ValueError('left/right hand required')
    from guitar_learning.training.runner import settings_document as base_settings
    from guitar_learning.song.task import make_task
    if not isinstance(song, str) or not song or Path(song).name != song or song in ('.', '..'):
        raise ValueError('song must be one registered song identifier')
    bundle = Path(__file__).resolve().parents[2]/'data/song_bundles'/song
    config = dict(schema='guitar_learning.song.v1', pre_roll_s=3., tail_s=.5,
                  window_s=.5, left_fraction=.4)
    task = make_task(bundle, pre_roll_s=config['pre_roll_s'], tail_s=config['tail_s'])
    if any(not target.fret for target in task.targets):
        raise ValueError('song training currently requires fretted notes; open strings are unsupported')
    ticks = task.provenance['song']['control_ticks']
    if device == 'auto':
        import torch
        device = 'cuda:0' if torch.cuda.is_available() else 'cpu'
    if physics not in ('auto', 'cpu', 'gpu'):
        raise ValueError('physics must be auto/cpu/gpu')
    gpu = physics == 'gpu' or (physics == 'auto' and device == 'cuda:0')
    if gpu and device != 'cuda:0':
        raise ValueError('GPU physics requires --device cuda:0')
    if learning_family not in ('song', 'finger-skill-v24', 'finger-skill'):
        raise ValueError('Unknown learning family')
    if (skill_phase not in ('auto', 'R', 'F', 'J') or
            skill_exploration not in ('independent', 'correlated') or
            type(skill_hold_ticks) is not int or skill_hold_ticks not in (1, 3, 6) or
            skill_scope not in (None, 'phrases', 'full_song')):
        raise ValueError('Invalid finger skill phase/exploration/hold/scope')
    if learning_family == 'song' and (skill_phase != 'auto' or skill_exploration != 'independent' or
                                     skill_hold_ticks != 1 or skill_scope is not None):
        raise ValueError('Skill options require --learning-family finger-skill-v24')
    if learning_family in ('finger-skill-v24', 'finger-skill') and (not gpu or hand != 'left' or
            finger_action_mode == 'position' or finger_shape or finger_standby_rate not in (None, .02)):
        raise ValueError('Finger skill requires GPU left, incremental control and default weak B without shape prior')
    if learning_family == 'finger-skill' and (skill_phase not in ('auto', 'J') or
            skill_exploration != 'independent' or skill_hold_ticks != 1 or skill_scope is not None):
        raise ValueError('Finger skill uses joint learning, independent exploration, K1 and fixed exposure scope')
    if skill_phase == 'auto' and skill_scope is not None:
        raise ValueError('Automatic stages select their own phrase/full-song scope')
    if type(finger_shape) is not bool:
        raise ValueError('finger_shape must be boolean')
    if (finger_standby_rate is not None or finger_shape) and not (gpu and hand == 'left'):
        raise ValueError('finger recovery options require GPU left training')
    if finger_action_mode is not None:
        if finger_action_mode not in ('position', 'incremental'):
            raise ValueError('finger action mode must be position/incremental')
        if not (gpu and hand == 'left'):
            raise ValueError('finger action mode requires GPU left training')
    count = (128 if gpu else 2) if num_envs is None else num_envs
    if gpu and (type(count) is not int or not 1 <= count <= 1024):
        raise ValueError('GPU environment count must be an integer in1..1024')
    collection = (32 if gpu else ticks) if horizon is None else horizon
    settings = base_settings(dict(updates=updates, num_envs=min(count, 2) if gpu else count, device=device,
        seed=seed, horizon=collection, size=size, checkpoint_every=checkpoint_every,
        stage='D', phrase_events=task.provenance['song']['source_event_count']))
    # Keep the legacy settings document unchanged outside GPU left training.
    settings['ppo'].pop('advantage_normalization',None)
    if gpu:
        settings['num_envs'] = count
        settings['ppo']['minibatch_size'] = 4096
        settings['physics_backend'] = dict(schema='guitar_learning.gpu_batch.v3',
            engine='GPU PhysX', tensor_pipeline='cuda', control='batched_tensor',
            measurement='gpu_surface_loaded.v1', cpu_checkpoint_compatible=False)
    settings.update(specialist=dict(role=hand, left_checkpoint=None, right_checkpoint=None),
        song=config, song_training=dict(schema='guitar_learning.song_training.v1',
            song_id=song, bundle=str(bundle.resolve()), target_count=len(task.targets),
            control_ticks=ticks, episode_duration_s=task.duration_s,
            score_clock='original_audio_plus_policy_pre_roll', observation_dimension=500),
        simple_start=dict(schema='guitar_learning.song_start.v1', initial_pose='agreed035_v14',
            initialization='fresh_unless_strict_resume'))
    if hand == 'left':
        if gpu:
            from guitar_learning.song.gpu_left_curriculum import default_config
            settings['song']['finger_action_mode'] = finger_action_mode or 'incremental'
            settings['ppo'].update(advantage_normalization='separate',gae_lambda=.98)
            settings['song']['surface_approach_gamma'] = settings['ppo']['gamma']
            from guitar_learning.gpu.finger_reward import finger_recovery_config
            settings['song']['finger_recovery'] = finger_recovery_config(dict(
                schema='guitar_learning.left_finger_recovery.v1',
                standby_rate_per_s=.02 if finger_standby_rate is None else finger_standby_rate,
                shape_rate_per_s=.004 if finger_shape else 0.))
        else:
            from guitar_learning.song.left_curriculum import default_config
        from guitar_learning.core.finger_control import default_profile
        from guitar_learning.song.wrist_guide import load_anchor_track
        load_anchor_track(bundle)
        settings['song']['left_curriculum'] = default_config()
        settings['song']['finger_control'] = default_profile()
        settings['song_training']['observation_dimension'] = 552 if gpu else 512
    if learning_family == 'finger-skill-v24':
        settings['finger_skill'] = dict(schema='guitar_learning.finger_skill.v1',
            phase=skill_phase, exploration=skill_exploration, hold_ticks=skill_hold_ticks,
            scope=skill_scope or ('full_song' if skill_phase == 'J' else 'phrases'),
            preparation_updates=32, finger_updates=256)
        settings['song_training']['observation_dimension'] = 557
    if learning_family == 'finger-skill':
        budget = updates*collection*count
        settings['finger_skill'] = dict(schema='guitar_learning.finger_skill.v2',
            phase='J', exploration='independent', hold_ticks=1, scope='scheduled',
            planned_transitions=budget, full_song_after=budget//4)
        settings['ppo'].update(advantage_normalization='joint', cost_weight=1.,
                               episode_cost_budget=None, lambda_lr=0.)
        settings['song_training']['observation_dimension'] = 561
    return settings

