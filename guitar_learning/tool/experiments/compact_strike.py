"""별도 compact 타현27: 학습·엄격 재개·전곡 평가·실제 오른손 영상."""
import argparse
import copy
import math
import os
from contextlib import contextmanager
from pathlib import Path
import sys
import time
from types import SimpleNamespace

if __name__ == '__main__' and not any(value in ('-h', '--help') for value in sys.argv):
    import isaacgym  # 실제 실행은 Torch/NumPy보다 native Gym을 먼저 로드한다.
import torch

from guitar_learning.portability import (ROOT, PATH_SCHEMA, portable, localize, settings_digest,
    checkpoint_inputs, validate_checkpoint_inputs, report_reference)
from guitar_learning.training.compact_strike import CompactStrikePolicy, POLICY_SCHEMA
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.training.rollout import TensorCollector
from guitar_learning.training.training_log_io import write, digest


SCHEMA = 'guitar_learning.compact_strike.v1'
RESUME_SCHEMA = 'guitar_learning.compact_strike_resume.v1'


def configuration():
    from guitar_learning.gpu.compact_strike import STATE_DIM, GOAL_DIM
    return dict(schema=SCHEMA, state_dim=STATE_DIM, event_dim=GOAL_DIM, priority_slots=2,
        state_hidden=[256, 256], goal_hidden=[64, 64], fusion_input=384,
        fusion_hidden=[512, 256], value_fusion_hidden=[256, 256], learned_action_dim=27,
        transport_action_dim=39, hold_ticks=1,
        width_selection='fixed; --size is recorded and does not change layer widths')


def validate_settings(settings):
    if (not isinstance(settings, dict) or settings.get('compact_strike') != configuration() or
            'finger_skill' in settings or settings.get('specialist', {}).get('role') != 'right' or
            settings.get('device') != 'cuda:0' or
            settings.get('song_training', {}).get('observation_dimension') != configuration()['state_dim']):
        raise ValueError('Explicit compact strike right27 GPU settings required')
    ppo = settings.get('ppo', {})
    if (ppo.get('advantage_normalization') != 'joint' or ppo.get('cost_weight') != 1. or
            ppo.get('episode_cost_budget') is not None or ppo.get('lambda_lr') != 0.):
        raise ValueError('Compact strike requires joint advantages and fixed cost weight one')
    for key in ('num_envs', 'horizon', 'updates', 'checkpoint_every'):
        if type(settings.get(key)) is not int or settings[key] < 1:
            raise ValueError('Positive integer '+key+' required')
    if settings['num_envs'] > 1024 or settings['num_envs']*settings['horizon'] < 2:
        raise ValueError('1..1024 environments and at least two rollout samples required')


def build_settings(*, song='00_SS1-68-E_comp', updates=100, num_envs=128, horizon=32,
                   size='medium', seed=7, checkpoint_every=250):
    """타현 입력을 직접 사전검사하며, 압현 전용 fret/단음 제약을 통과시키지 않는다."""
    from guitar_learning.training.launch import base_settings_document
    from guitar_learning.song.strike_task import load_strike_task
    if not isinstance(song, str) or not song or Path(song).name != song or song in ('.', '..'):
        raise ValueError('One registered song identifier required')
    if type(num_envs) is not int or not 1 <= num_envs <= 1024:
        raise ValueError('num_envs must be an integer in1..1024')
    bundle = ROOT/'data/song_bundles'/song
    song_config = dict(schema='guitar_learning.song.v1', pre_roll_s=3., tail_s=.5,
                       window_s=.5, left_fraction=.4)
    task = load_strike_task(bundle, pre_roll_s=3., tail_s=.5)
    settings = base_settings_document(dict(updates=updates, num_envs=min(num_envs, 2),
        horizon=horizon, size=size, seed=seed, checkpoint_every=checkpoint_every,
        device='cuda:0', stage='D', phrase_events=len(task.events)))
    settings.update(num_envs=num_envs,
        specialist=dict(role='right', left_checkpoint=None, right_checkpoint=None), song=song_config,
        physics_backend=dict(schema='guitar_learning.gpu_batch.v3', engine='GPU PhysX',
            tensor_pipeline='cuda', control='batched_tensor', measurement='compact_strike.v1',
            cpu_checkpoint_compatible=False),
        song_training=dict(schema='guitar_learning.compact_strike_song.v1', song_id=song,
            bundle=str(bundle.resolve()), target_count=len(task.events),
            control_ticks=math.ceil(task.duration_s*60), episode_duration_s=task.duration_s,
            score_clock='original_audio_plus_policy_pre_roll', observation_dimension=configuration()['state_dim']),
        simple_start=dict(schema='guitar_learning.song_start.v1', initial_pose='agreed035_v14',
                          initialization='fresh_unless_strict_resume'), compact_strike=configuration())
    settings['ppo'].update(minibatch_size=4096, gae_lambda=.98, advantage_normalization='joint',
                           cost_weight=1., episode_cost_budget=None, lambda_lr=0.)
    validate_settings(settings)
    return settings


def validate_metadata(metadata):
    if not isinstance(metadata, dict) or metadata.get('schema') != RESUME_SCHEMA:
        raise ValueError('Compact strike checkpoint required; old pressure/right6/right27 models cannot be converted')
    validate_settings(metadata.get('settings', {}))


def read_checkpoint(checkpoint):
    """장면 생성 전에 저장 설정·소스 SHA·전체 정책 계약부터 검증한다."""
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict):
        raise ValueError('PPO checkpoint dictionary required')
    metadata = payload.get('metadata')
    validate_metadata(metadata)
    validate_checkpoint_inputs(metadata)
    settings = localize(metadata['settings'])
    identity = payload.get('identity', {})
    architecture = identity.get('architecture', {})
    if (identity.get('schema') != DecisionPPOTrainer.schema or identity.get('path_schema') != PATH_SCHEMA or
            architecture.get('schema') != POLICY_SCHEMA):
        raise ValueError('Compact strike decision PPO identity required')
    spec = settings['compact_strike']
    with torch.random.fork_rng(devices=[]):
        expected = CompactStrikePolicy(spec['state_dim'], event_dim=spec['event_dim'],
            size=settings['size'], contract=architecture.get('contract')).architecture
    if portable(expected) != portable(architecture):
        raise ValueError('Complete compact strike architecture/contract mismatch')
    return settings


def _pins(settings, out, extra=()):
    # 이 공용 함수에는 J 상태 가정이 없으며 소스·자산·visual mesh까지 봉인한다.
    from guitar_learning.training.finger_skill_runner import _pins as input_pins
    return input_pins(settings, out, extra)


class CompactStrikeCollector(TensorCollector):
    """27축 명령을 그대로 전달한 기존 tick 수집 결과에 K1 결정 필드만 더한다."""
    def collect(self, horizon, **kwargs):
        buffer, completed = super().collect(horizon, **kwargs)
        buffer['duration'] = torch.ones_like(buffer['reward'], dtype=torch.long)
        buffer['valid'] = torch.ones_like(buffer['reward'], dtype=torch.bool)
        return buffer, completed


class CompactStrikeTrainer(DecisionPPOTrainer):
    """최적화는 압현과 같고, 저장/복원에 전용 입력 계약만 추가한다."""
    def __init__(self, policy, config=None, *, context=None):
        super().__init__(policy, config)
        self.context = context

    def save(self, path, metadata=None):
        if self.context is None:
            raise ValueError('Pinned compact strike run context required before save')
        context = self.context
        settings = context['settings']
        metadata = dict(metadata or {})
        metadata.update(schema=RESUME_SCHEMA, settings=portable(settings),
            settings_sha256=settings_digest(settings),
            input_contract=checkpoint_inputs(context['pins'], settings,
                settings_path=context['out']/'settings.json', lineage=context['lineage']),
            resume_scope='right27 model/Adam/RNG; fresh prepared physical episodes')
        return super().save(path, metadata)

    def load(self, path):
        read_checkpoint(path)
        return super().load(path)

    def update(self, buffer, completed_episodes=()):
        metrics = super().update(buffer, completed_episodes)
        if self.context is not None and self.context.get('pool') is not None:
            metrics['reward_component_means'] = self.context['pool'].environment.reward_window_means(
                int(buffer['valid'].sum()))
        return metrics


@contextmanager
def runtime(settings=None, out=None, resume=None):
    """명시된 실행 프로세스 범위에서 네 factory를 바꾸고 반드시 복원한다."""
    from guitar_learning.training import rollout, policy, ppo
    from guitar_learning.gpu.compact_strike import CompactStrikeEnvironment
    from guitar_learning.tool.experiments.right27.control import Right27Controller
    original = (rollout.GpuPool, rollout.TensorCollector, policy.SpecialistPolicy, ppo.PPOTrainer)
    base_pool = original[0]
    context = dict(settings=copy.deepcopy(settings), out=Path(out).resolve() if out is not None else None,
                   lineage=[Path(resume).resolve()] if resume is not None else [], pool=None, pins=None)

    class CompactStrikePool(base_pool):
        environment_class_override = CompactStrikeEnvironment

        def __init__(self, settings, out):
            validate_settings(settings)
            # legacy 실행기가 settings를 기록한 뒤, 장면/정책 생성 전에 입력을 고정한다.
            if context['out'] is not None:
                context['pins'] = _pins(context['settings'], context['out'], context['lineage'])
                write(context['out']/'compact_strike_inputs_before.json', context['pins'])
            super().__init__(settings, out)
            try:
                self.controller = Right27Controller(self.scene, base=self.controller)
                self.environment.bind_action_contract(self.controller.contract)
                native = copy.deepcopy(self.contract['native_backend'])
                native['control'] = copy.deepcopy(self.controller.contract)
                self.contract = copy.deepcopy(self.environment.contract)
                self.contract['native_backend'] = native
                self.observation = self.reset()[0]
                context['pool'] = self
            except BaseException:
                self.close()
                raise

    class PinnedTrainer(CompactStrikeTrainer):
        def __init__(self, policy, config=None):
            super().__init__(policy, config, context=context)

    rollout.GpuPool, rollout.TensorCollector = CompactStrikePool, CompactStrikeCollector
    policy.SpecialistPolicy, ppo.PPOTrainer = CompactStrikePolicy, PinnedTrainer
    try:
        yield SimpleNamespace(pool=CompactStrikePool, trainer=PinnedTrainer)
    finally:
        rollout.GpuPool, rollout.TensorCollector, policy.SpecialistPolicy, ppo.PPOTrainer = original


def train(args):
    from guitar_learning.tool.training.legacy_gpu_runner import run
    if args.resume:
        settings = read_checkpoint(args.resume)
        for key in ('song', 'size', 'num_envs', 'horizon', 'seed'):
            requested = getattr(args, key)
            saved = settings['song_training']['song_id'] if key == 'song' else settings[key]
            if requested is not None and requested != saved:
                raise ValueError('Resume must preserve saved '+key)
        settings['updates'] = args.updates
        if args.checkpoint_every is not None:
            settings['checkpoint_every'] = args.checkpoint_every
    else:
        options = {key: getattr(args, key) for key in ('song', 'size', 'num_envs', 'horizon', 'seed',
                   'checkpoint_every') if getattr(args, key) is not None}
        settings = build_settings(updates=args.updates, **options)
    if args.max_wall_seconds is not None:
        settings['max_wall_seconds'] = args.max_wall_seconds
    validate_settings(settings)
    with runtime(settings, args.out, args.resume):
        return run(settings, SimpleNamespace(out=args.out, resume=args.resume))


class _DeterministicPolicy:
    def __init__(self, policy):
        self.policy = policy

    def act(self, *inputs):
        return self.policy.act(*inputs, deterministic=True)

    def __call__(self, *inputs):
        return self.policy(*inputs)


def _cameras(scene, gymapi):
    """오른손 피크와 전신을 실제 native 장면의 두 카메라로 기록한다."""
    pick = scene.snapshot()['body_state'][0, scene.body_names.index('human/RH:pick'), :3].cpu().tolist()
    locations = dict(hand=(tuple(value+offset for value, offset in zip(pick, (.55, .40, .20))), tuple(pick)),
                     fullbody=((-.10, 2.7, 1.1), (-.15, -.10, .65)))
    cameras = {}
    for name, (position, target) in locations.items():
        props = gymapi.CameraProperties()
        props.width, props.height, props.horizontal_fov = 1280, 720, 55.
        camera = scene.gym.create_camera_sensor(scene.envs[0], props)
        if camera < 0:
            raise RuntimeError('Native '+name+' camera unavailable')
        scene.gym.set_camera_location(camera, scene.envs[0], gymapi.Vec3(*position), gymapi.Vec3(*target))
        cameras[name] = camera
    return cameras


def _replay(checkpoint, out, *, num_envs=None, video=False):
    """환경별 첫 에피소드만 평가하며 영상은 미리 정한 env0을 기록한다."""
    import isaacgym
    from isaacgym import gymapi
    import numpy as np
    from guitar_learning.tool.validation.hand_contact_probe import GraphicsGym, finish_video
    from guitar_learning.tool.demonstration.render_finger_skill import _EnvZeroCapture, _encoder
    checkpoint, out = Path(checkpoint).resolve(), Path(out).resolve()
    settings = read_checkpoint(checkpoint)
    if num_envs is not None:
        if type(num_envs) is not int or not 1 <= num_envs <= 1024:
            raise ValueError('num_envs must be an integer in1..1024')
        settings['num_envs'] = num_envs
    validate_settings(settings)
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', portable(settings))
    pins = _pins(settings, out, [checkpoint])
    write(out/'inputs_before.json', pins)
    torch.set_num_threads(1)
    torch.backends.cuda.matmul.allow_tf32 = False
    pool = capture = None
    videos, codes, cleanup_errors, rows = {}, {}, [], {}
    failure, unchanged = None, False
    started = time.monotonic()
    try:
        with runtime() as factories:
            original = gymapi.acquire_gym
            try:
                if video:
                    gymapi.acquire_gym = lambda: GraphicsGym(original())
                pool = factories.pool(settings, out/'scene')
            finally:
                gymapi.acquire_gym = original
            write(out/'training_contract.json', pool.contract)
            policy = CompactStrikePolicy(settings['compact_strike']['state_dim'], size=settings['size'],
                contract=pool.contract).to(settings['device'])
            trainer = CompactStrikeTrainer(policy, PPOConfig(**settings['ppo']))
            trainer.load(checkpoint)
            policy.eval()
            before = {key: value.detach().clone() for key, value in policy.state_dict().items()}
            pool.observation = pool.reset()[0]
            if video:
                cameras = _cameras(pool.scene, gymapi)
                for name in cameras:
                    videos[name] = _encoder(out/(name+'.mp4'))
                capture = _EnvZeroCapture(pool, gymapi, np, cameras, videos)
            collector = CompactStrikeCollector(_DeterministicPolicy(policy), pool)

            def record(tick, reward, cost, terminated, truncated, episodes):
                if capture is not None:
                    capture.record(tick, reward, cost, terminated, truncated, episodes)
                for episode in episodes:
                    rows.setdefault(episode['env_id'], copy.deepcopy(episode))

            maximum = math.ceil(pool.environment.task.duration_s*60)+settings['horizon']
            elapsed = 0
            while (capture.episode is None if video else len(rows) < settings['num_envs']) and elapsed < maximum:
                collector.collect(min(settings['horizon'], maximum-elapsed), transition_callback=record)
                elapsed += min(settings['horizon'], maximum-elapsed)
            if (capture.episode is None if video else len(rows) != settings['num_envs']):
                raise RuntimeError('First episodes did not finish within the task duration')
            unchanged = all(torch.equal(value, before[key]) for key, value in policy.state_dict().items())
            if not unchanged:
                raise RuntimeError('Replay changed policy weights or buffers')
            write(out/'episodes.json', [rows[key] for key in sorted(rows)])
            if capture is not None:
                write(out/'episode_env0000.json', capture.episode)
                write(out/'capture_metadata.json', dict(schema='guitar_learning.compact_strike_video.v1',
                    environment=0, first_episode_only=True, joint_names=pool.scene.names,
                    body_names=pool.scene.body_names, native_pixels=True, width=1280, height=720,
                    video_fps=30, capture_hz=60, source_physics_hz=240, policy_decision_ticks=1,
                    frame_times_s=capture.frame_times_s, no_reset_frames=True,
                    control='right27 deterministic means recomputed each60Hz; original native PD/forces',
                    frame_mapping='frame n maps to control endpoint 2*(n+1); no t0 frame'))
    except BaseException as error:
        failure = dict(type=type(error).__name__, message=str(error))
        raise
    finally:
        for name, process in videos.items():
            code, errors = finish_video(process)
            codes[name] = code
            cleanup_errors.extend(dict(component=name, message=error) for error in errors)
        if capture is not None and capture.samples:
            try:
                filename = 'poses_env0000.npz' if failure is None else 'partial_poses_env0000.npz'
                np.savez_compressed(out/filename, **{key: np.stack([row[key] for row in capture.samples])
                    for key in capture.samples[0]})
            except BaseException as error:
                cleanup_errors.append(dict(component='raw_capture', message=str(error)))
        if pool is not None:
            try:
                pool.close()
            except BaseException as error:
                cleanup_errors.append(dict(component='scene_close', message=str(error)))
        changed = [path for path, value in pins.items() if not Path(path).is_file() or digest(path) != value]
        audit = pool.scene.diagnostics if pool is not None and pool.scene is not None else None
        lifecycle = bool(audit and audit.get('closed') and audit.get('physx_use_gpu') and
            audit.get('use_gpu_pipeline') and audit.get('simulator_count') == 1 and
            audit.get('environment_count') == settings['num_envs'])
        complete = failure is None and unchanged and lifecycle and not changed and not cleanup_errors
        if video:
            complete = complete and len(codes) == 2 and all(value == 0 for value in codes.values())
        report = dict(schema='guitar_learning.compact_strike_'+('render' if video else 'evaluation')+'.v1',
            completed=complete, failure=failure, checkpoint=str(checkpoint), checkpoint_sha256=digest(checkpoint),
            portable_checkpoint_ref=report_reference(checkpoint, out), recorded_project_root=str(ROOT),
            scope='full_song', first_episode_only=True, policy_unchanged=unchanged, training_updates=0,
            completed_episodes=len(rows), episodes=[rows[key] for key in sorted(rows)],
            source_checkpoint_pins_validated=True, changed_inputs=changed, lifecycle_verified=lifecycle,
            cleanup_errors=cleanup_errors, gpu_scene=audit, encoding_exit_codes=codes,
            wall_s=time.monotonic()-started)
        write(out/'report.json', report)
        if failure is None and not complete:
            raise RuntimeError('Replay source, policy, encoding or native lifecycle checks failed; see report.json')
    return report


def evaluate(checkpoint, out, *, num_envs=None):
    return _replay(checkpoint, out, num_envs=num_envs)


def render(checkpoint, out, *, num_envs=None):
    return _replay(checkpoint, out, num_envs=num_envs, video=True)


def parser():
    result = argparse.ArgumentParser(description=__doc__,
        epilog='compact strike 폭은 고정입니다. --size는 기록되며 층 크기를 바꾸지 않습니다.')
    commands = result.add_subparsers(dest='command', required=True)
    command = commands.add_parser('train')
    command.add_argument('--out', type=Path, required=True)
    command.add_argument('--resume', type=Path)
    command.add_argument('--song')
    command.add_argument('--size', choices=('small', 'medium', 'large'))
    command.add_argument('--updates', type=int, default=100)
    for name in ('num-envs', 'horizon', 'seed', 'checkpoint-every'):
        command.add_argument('--'+name, type=int)
    command.add_argument('--max-wall-seconds', type=float)
    for name in ('evaluate', 'render'):
        command = commands.add_parser(name)
        command.add_argument('checkpoint', type=Path)
        command.add_argument('--out', type=Path, required=True)
        command.add_argument('--num-envs', type=int)
    return result


def main():
    args = parser().parse_args()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
        os.environ[key] = '1'
    if args.command == 'train':
        if args.max_wall_seconds is not None and (not math.isfinite(args.max_wall_seconds) or args.max_wall_seconds <= 0):
            raise ValueError('Positive finite wall budget required')
        return train(args)
    return globals()[args.command](args.checkpoint, args.out, num_envs=args.num_envs)


if __name__ == '__main__':
    main()
