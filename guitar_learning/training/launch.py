"""J 전용 GPU 왼손 학습과 기존 song 실행의 공통 설정을 구성한다."""
import argparse
import math
import os
from dataclasses import asdict
from pathlib import Path


def base_settings_document(value):
    """공용 song 설정을 채우고 기존 CPU worker 수 계약으로 검증한다.

    GPU 환경 수와 J 전용 설정은 build_settings에서 이 결과에 덧붙인다.
    """
    from guitar_learning.training.ppo import PPOConfig
    settings = dict(
        num_envs=8, horizon=256, updates=1, device='cpu', seed=7, size='medium',
        initial_std=math.exp(-3), stage='B', checkpoint_every=5, max_wall_seconds=None,
        min_available_memory_gib=4., heartbeat_seconds=10.,
        resource_interval_seconds=5., worker_timeout_seconds=300.,
        music=dict(reward_mode='legacy', goal_event_indices=None),
        logging=dict(detail='standard', save_first_rollout=False),
        start_event_index=0, phrase_events=8, tempo_scale=1., ppo=asdict(PPOConfig()),
    )
    settings['ppo'].pop('advantage_normalization')
    unknown = set(value) - set(settings)
    if unknown:
        raise ValueError('unknown run settings: '+str(sorted(unknown)))
    settings.update(value)
    for key in (
        'num_envs', 'horizon', 'updates', 'seed', 'checkpoint_every',
        'start_event_index', 'phrase_events',
    ):
        if isinstance(settings[key], bool) or not isinstance(settings[key], int):
            raise ValueError('integer '+key+' required')
    if (settings['num_envs'] not in (1, 2, 4, 8, 16) or
            min(settings[k] for k in ('horizon', 'updates', 'checkpoint_every', 'phrase_events')) < 1):
        raise ValueError('supported worker count and positive budgets required')
    if settings['horizon'] * settings['num_envs'] < 2 or settings['start_event_index'] < 0:
        raise ValueError('at least two samples and nonnegative event index required')
    if settings['stage'] not in ('B', 'C', 'D') or settings['size'] not in ('small', 'medium', 'large'):
        raise ValueError('explicit supported stage/size required')
    if not isinstance(settings['device'], str) or settings['device'] not in ('cpu', 'cuda:0'):
        raise ValueError('device must be cpu or cuda:0')
    if (not math.isfinite(settings['initial_std']) or
            not math.exp(-5) <= settings['initial_std'] <= math.exp(2)):
        raise ValueError('initial_std must fit the policy log_std clamp')
    if not math.isfinite(settings['tempo_scale']) or settings['tempo_scale'] <= 0:
        raise ValueError('positive tempo_scale required')
    wall = settings['max_wall_seconds']
    if wall is not None and (not math.isfinite(wall) or wall <= 0):
        raise ValueError('positive optional wall budget required')
    for key in (
        'min_available_memory_gib', 'heartbeat_seconds',
        'resource_interval_seconds', 'worker_timeout_seconds',
    ):
        value = settings[key]
        if (isinstance(value, bool) or not isinstance(value, (int, float)) or
                not math.isfinite(value) or value <= 0):
            raise ValueError('positive finite '+key+' required')
    music = settings['music']
    if not isinstance(music, dict) or set(music) - {'reward_mode', 'goal_event_indices'}:
        raise ValueError('explicit supported music settings required')
    music = dict(dict(reward_mode='legacy', goal_event_indices=None), **music)
    if music['reward_mode'] not in ('legacy', 'dense_v2'):
        raise ValueError('supported reward_mode required')
    indices = music['goal_event_indices']
    if indices is not None and (
        not isinstance(indices, list) or not indices or
        any(isinstance(i, bool) or not isinstance(i, int) or i < 0 for i in indices) or
        len(set(indices)) != len(indices)
    ):
        raise ValueError('unique nonnegative goal_event_indices required')
    if indices is not None and settings['stage'] != 'B':
        raise ValueError('goal sampling currently requires stage B')
    settings['music'] = music
    logging = settings['logging']
    if not isinstance(logging, dict) or set(logging) - {'detail', 'save_first_rollout'}:
        raise ValueError('supported logging settings required')
    logging = dict(dict(detail='standard', save_first_rollout=False), **logging)
    if (logging['detail'] not in ('standard', 'diagnostic') or
            type(logging['save_first_rollout']) is not bool):
        raise ValueError('standard/diagnostic detail and boolean save_first_rollout required')
    settings['logging'] = logging
    settings['ppo'] = asdict(PPOConfig(**settings['ppo']))
    if settings['ppo']['advantage_normalization'] == 'joint':
        settings['ppo'].pop('advantage_normalization')
    return settings

DEFAULT_SONG = '05_BN2-131-B_solo'


def build_settings(hand, *, song=DEFAULT_SONG, updates=100, num_envs=None,
                      device='cuda:0', seed=7, horizon=None, size='medium', physics='auto',
                      checkpoint_every=250, finger_standby_rate=None, finger_shape=False,
                      finger_action_mode=None, learning_family='song'):
    """공용 song 설정을 만든 뒤 기본 J 학습의 설정·계약을 덧붙인다.

    원곡의 모든 음을 사용하며 수집 길이(horizon)의 끝을 곡 종료로 취급하지 않는다.
    """
    if hand not in ('left', 'right'):
        raise ValueError('left/right hand required')
    base_settings = base_settings_document
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
    if learning_family not in ('song', 'finger-skill'):
        raise ValueError('Unknown learning family; R/F stages have been retired')
    if learning_family == 'finger-skill' and (not gpu or hand != 'left' or
            finger_shape or finger_standby_rate not in (None, .02)):
        raise ValueError('J-only finger skill requires GPU left and default weak B')
    if type(finger_shape) is not bool:
        raise ValueError('finger_shape must be boolean')
    if (finger_standby_rate is not None or finger_shape) and not (gpu and hand == 'left'):
        raise ValueError('finger recovery options require GPU left training')
    if finger_action_mode is not None:
        if finger_action_mode != 'position':
            raise ValueError('finger action mode must be position; accumulated finger actions are retired')
        if not (gpu and hand == 'left'):
            raise ValueError('finger action mode requires GPU left training')
    environment_count = (128 if gpu else 2) if num_envs is None else num_envs
    if gpu and (type(environment_count) is not int or not 1 <= environment_count <= 1024):
        raise ValueError('GPU environment count must be an integer in1..1024')
    collection_ticks = (32 if gpu else ticks) if horizon is None else horizon
    # 공용 검증기는 CPU worker 수만 허용하므로 GPU는 임시로 최대 2를 전달한다.
    # GPU 환경 수는 위에서 별도로 검증했고, 공용 검증 직후 실제 값으로 되돌린다.
    settings = base_settings(dict(
        updates=updates,
        num_envs=min(environment_count, 2) if gpu else environment_count,
        device=device,
        seed=seed,
        horizon=collection_ticks,
        size=size,
        checkpoint_every=checkpoint_every,
        stage='D',
        phrase_events=task.provenance['song']['source_event_count'],
    ))
    # GPU 왼손 학습 외의 경로에서는 기존 설정 문서를 유지한다.
    settings['ppo'].pop('advantage_normalization',None)
    if gpu:
        settings['num_envs'] = environment_count
        settings['ppo']['minibatch_size'] = 4096
        settings['physics_backend'] = dict(schema='guitar_learning.gpu_batch.v3',
            engine='GPU PhysX', tensor_pipeline='cuda', control='batched_tensor',
            measurement='gpu_surface_loaded.v1', cpu_checkpoint_compatible=False)
    settings.update(
        specialist=dict(role=hand, left_checkpoint=None, right_checkpoint=None),
        song=config,
        song_training=dict(
            schema='guitar_learning.song_training.v1',
            song_id=song, bundle=str(bundle.resolve()), target_count=len(task.targets),
            control_ticks=ticks, episode_duration_s=task.duration_s,
            score_clock='original_audio_plus_policy_pre_roll', observation_dimension=500,
        ),
        simple_start=dict(
            schema='guitar_learning.song_start.v1',
            initial_pose='left_standby_v9' if gpu and hand == 'left' else 'agreed035_v14',
            initialization='fresh_unless_strict_resume',
        ),
    )
    if hand == 'left':
        if gpu:
            from guitar_learning.song.curriculum import gpu_default_config as default_config
            settings['song']['finger_action_mode'] = 'position'
            settings['ppo'].update(advantage_normalization='separate',gae_lambda=.98)
            settings['song']['surface_approach_gamma'] = settings['ppo']['gamma']
            from guitar_learning.gpu.finger_reward import finger_recovery_config
            settings['song']['finger_recovery'] = finger_recovery_config(dict(
                schema='guitar_learning.left_finger_recovery.v1',
                standby_rate_per_s=.02 if finger_standby_rate is None else finger_standby_rate,
                shape_rate_per_s=.004 if finger_shape else 0.))
        else:
            from guitar_learning.song.curriculum import cpu_default_config as default_config
        from guitar_learning.core.control import default_profile
        from guitar_learning.song.task import load_anchor_track
        load_anchor_track(bundle)
        settings['song']['left_curriculum'] = default_config()
        settings['song']['finger_control'] = default_profile()
        settings['song_training']['observation_dimension'] = 552 if gpu else 512
    # 여기까지는 기존 song 경로와 공유한다. 기본 J 경로의 차이만 아래에 덧붙인다.
    if learning_family == 'finger-skill':
        budget = updates*collection_ticks*environment_count
        settings['finger_skill'] = dict(schema='guitar_learning.finger_skill.v3',
            phase='J', exploration='independent', hold_ticks=1, scope='scheduled',
            planned_transitions=budget, full_song_after=budget//4)
        settings['ppo'].update(advantage_normalization='joint', cost_weight=1.,
                               episode_cost_budget=None, lambda_lr=0.)
        settings['song_training']['observation_dimension'] = 557
    return settings


def settings_document(hand='left', *, learning_family='finger-skill', **options):
    """기본 압현은 V5, 오른손·전신 공용 설정은 build_settings를 명시 사용한다."""
    if hand != 'left' or learning_family != 'finger-skill':
        raise ValueError('기본 실행은 V5 GPU 왼손 압현 전용입니다.')
    from guitar_learning.tool.experiments.compact_press_v5 import build_settings as v5_settings
    return v5_settings(**options)


def run(settings, args):
    """V5 계약을 먼저 검사한 뒤 공용 실행기를 V5 환경·정책으로 연결한다."""
    if settings.get('compact_press', {}).get('schema') != 'guitar_learning.compact_press.v5':
        raise ValueError('기본 실행에는 V5 압현 설정이 필요합니다.')
    import isaacgym
    from guitar_learning.tool.experiments.compact_press_v5 import validate_settings, runtime, clock_runtime
    from guitar_learning.training.finger_skill_runner import run as run_finger_skill
    validate_settings(settings)
    with clock_runtime(settings['song_training']['song_id']), runtime():
        return run_finger_skill(settings, args)


def add_train_arguments(command):
    """기본 진입점과 직접 V5 CLI가 같은 학습 옵션을 사용한다."""
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--song')
    command.add_argument('--size', choices=('small', 'medium', 'large'))
    command.add_argument('--num-envs', type=int)
    command.add_argument('--updates', type=int, default=100)
    command.add_argument('--horizon', type=int)
    command.add_argument('--seed', type=int)
    command.add_argument('--checkpoint-every', type=int)
    command.add_argument('--resume', type=Path)
    command.add_argument('--max-wall-seconds', type=float)
    pelvis = command.add_mutually_exclusive_group()
    pelvis.add_argument('--include-pelvis', dest='include_pelvis', action='store_true')
    pelvis.add_argument('--no-include-pelvis', dest='include_pelvis', action='store_false')
    command.set_defaults(include_pelvis=None)
    command.add_argument('--improvement-profile', choices=('corrected', 'preparation', 'full_hold', 'combined'),
        help='신규 기본corrected; 재개에서 생략하면 저장 조건 유지')
    command.add_argument('--initial-support-std', type=float, help='팔12·엄지5축 초기 std, 기본0.15')
    command.add_argument('--initial-finger-std', type=float, help='검지~소지16축 초기 std, 기본0.35')
    return command


def main():
    parser = add_train_arguments(argparse.ArgumentParser(description='V5 GPU 왼손 압현 학습'))
    args = parser.parse_args()
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[name] = '1'
    if args.updates < 1 or (args.checkpoint_every is not None and args.checkpoint_every < 1):
        parser.error('반복과 저장 간격은 양수여야 합니다.')
    if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0):
        parser.error('시간 예산은 유한한 양수여야 합니다.')
    # 실제 실행에서만 Isaac Gym을 텐서 라이브러리보다 먼저 불러온다.
    import isaacgym
    from guitar_learning.tool.experiments.compact_press_v5 import train
    return train(args)


if __name__ == '__main__':
    main()
