"""전신37 전용 실행: 기존 GPU 물리·수집·PPO를 변경 없이 연결한다."""
import copy
from dataclasses import asdict
import json
from pathlib import Path
import random
import time

import numpy as np
import torch

from guitar_learning.gpu.whole_body import WholeBodyEnvironment, STATE_DIM
from guitar_learning.gpu.whole_body_control import WholeBodyController
from guitar_learning.native.paths import ROOT, pin, verify
from guitar_learning.portability import checkpoint_inputs, localize, portable, settings_digest, validate_checkpoint_inputs
from guitar_learning.training.ppo import DecisionPPOTrainer, PPOConfig
from guitar_learning.training.rollout import GpuPool, TensorCollector
from guitar_learning.training.training_log_io import active_source_paths
from guitar_learning.training.whole_body import WholeBodyPolicy, POLICY_SCHEMA


SCHEMA = 'guitar_learning.whole_body_run.v1'
RESUME_SCHEMA = 'guitar_learning.whole_body_resume.v1'


def configuration(*, num_envs=128, horizon=32, updates=100, checkpoint_every=25,
                  duration_s=10., seed=7, device='cuda:0'):
    settings = dict(schema=SCHEMA, num_envs=num_envs, horizon=horizon, updates=updates,
        checkpoint_every=checkpoint_every, duration_s=duration_s, seed=seed, device=device,
        ppo=asdict(PPOConfig(gae_lambda=.98, minibatch_size=4096, lambda_lr=0.)))
    validate_settings(settings)
    return settings


def validate_settings(settings):
    keys = {'schema', 'num_envs', 'horizon', 'updates', 'checkpoint_every', 'duration_s', 'seed', 'device', 'ppo'}
    if not isinstance(settings, dict) or set(settings) != keys or settings.get('schema') != SCHEMA:
        raise ValueError('explicit whole body run settings required')
    for key in ('num_envs', 'horizon', 'updates', 'checkpoint_every'):
        if type(settings[key]) is not int or settings[key] < 1:
            raise ValueError('positive integer '+key+' required')
    duration = settings['duration_s']
    if (isinstance(duration, bool) or not isinstance(duration, (int, float)) or
            not np.isfinite(duration) or duration <= 0 or abs(duration*60-round(duration*60)) > 1e-7):
        raise ValueError('positive duration on control grid required')
    if type(settings['seed']) is not int or not 0 <= settings['seed'] < 2**32:
        raise ValueError('uint32 seed required')
    if not isinstance(settings['device'], str) or torch.device(settings['device']).type not in ('cpu', 'cuda'):
        raise ValueError('CPU tensor checks or CUDA physical execution required')
    expected = asdict(PPOConfig(gae_lambda=.98, minibatch_size=4096, lambda_lr=0.))
    if settings['ppo'] != expected or settings['num_envs']*settings['horizon'] < 2:
        raise ValueError('fixed whole body PPO configuration and at least two decisions required')


def write(path, value):
    Path(path).write_text(json.dumps(portable(value), ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def _pins(settings, out, lineage=()):
    from guitar_learning.runtime.prepared_reset_v1 import prepared_input_paths, BASELINE_CONFIG
    sources = active_source_paths(ROOT/'guitar_learning')
    sources.update((ROOT/'guitar_learning/assets').rglob('*.json'))
    sources.update(p for p in (ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1').rglob('*') if p.is_file())
    sources.update(prepared_input_paths())
    sources.update(Path(p).resolve() for p in lineage)
    sources.add(Path(out)/'settings.json')
    return pin(BASELINE_CONFIG, extra=sources)


class WholeBodyPool(GpuPool):
    """공용 step/reset/close를 재사용하되 손 정책 전용 초기화는 호출하지 않는다."""
    def __init__(self, settings, out):
        from guitar_learning.gpu.scene import GpuScene
        validate_settings(settings)
        if torch.device(settings['device']).type != 'cuda':
            raise ValueError('physical whole body training requires explicit CUDA; no CPU physics fallback')
        self.num_envs, self.out = settings['num_envs'], Path(out)
        self.scene, self.closed, self.valid = None, False, True
        self.finger_control_diagnostics = None
        try:
            self.scene = GpuScene(self.num_envs, 'left', device=settings['device'], out=out)
            self.controller = WholeBodyController(self.scene)
            metadata = copy.deepcopy(self.scene.metadata)
            metadata.update(body_mass=self.scene.mass.cpu().tolist(),
                            action_contract=copy.deepcopy(self.controller.contract))
            self.environment = WholeBodyEnvironment(metadata, duration_s=settings['duration_s'], device=settings['device'])
            self.contract = copy.deepcopy(self.environment.contract)
            self.contract['native_backend'].update(control=copy.deepcopy(self.controller.contract),
                guitar_representation=copy.deepcopy(metadata['guitar_representation']),
                hand_collision=copy.deepcopy(metadata['hand_collision']), reset=metadata['reset_body_source'],
                environment_aggregate=copy.deepcopy(metadata['environment_aggregate']), policy_role='whole_body37')
            self.last_valid_efforts = self.scene.efforts.clone()
            self.observation = self.reset()[0]
        except BaseException:
            self.close()
            raise

    def step(self, actions):
        if (not isinstance(actions, torch.Tensor) or actions.shape != (self.num_envs, 39) or
                not actions.is_floating_point() or not torch.isfinite(actions).all() or
                (actions.abs() > 1).any() or (actions[:, 37:] != 0).any()):
            raise ValueError('body37 plus two inert zero transport channels required')
        return super().step(actions[:, :37])


class WholeBodyCollector(TensorCollector):
    def collect(self, horizon, **kwargs):
        buffer, episodes = super().collect(horizon, **kwargs)
        buffer['duration'] = torch.ones_like(buffer['reward'], dtype=torch.long)
        buffer['valid'] = torch.ones_like(buffer['reward'], dtype=torch.bool)
        return buffer, episodes


def checkpoint_metadata(settings, pins, out, lineage=()):
    return dict(schema=RESUME_SCHEMA, settings=portable(settings), settings_sha256=settings_digest(settings),
        input_contract=checkpoint_inputs(pins, settings, settings_path=Path(out)/'settings.json', lineage=lineage),
        resume_scope='model, Adam and RNG; new prepared physical episodes',
        task_scope='fixed-root support with prepared hands; no three-policy joint learning')


def read_checkpoint(path):
    payload = torch.load(path, map_location='cpu', weights_only=False)
    if not isinstance(payload, dict) or not isinstance(payload.get('metadata'), dict):
        raise ValueError('whole body checkpoint dictionary required')
    metadata = payload['metadata']
    if metadata.get('schema') != RESUME_SCHEMA:
        raise ValueError('whole body checkpoint required; other policies cannot be converted')
    settings = localize(metadata['settings'])
    validate_settings(settings)
    validate_checkpoint_inputs(metadata)
    architecture = payload.get('identity', {}).get('architecture', {})
    if architecture.get('schema') != POLICY_SCHEMA:
        raise ValueError('whole body architecture required')
    with torch.random.fork_rng(devices=[]):
        policy = WholeBodyPolicy(STATE_DIM, contract=localize(architecture.get('contract')))
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
    if trainer._identity() != payload['identity']:
        raise ValueError('whole body policy/control/PPO identity mismatch')
    policy.load_state_dict(payload['model'], strict=True)
    if not all(torch.isfinite(v).all() for v in policy.state_dict().values()):
        raise ValueError('nonfinite saved whole body weights')
    return settings, policy


def run(settings, out, *, resume=None):
    validate_settings(settings)
    if resume is not None:
        saved, _ = read_checkpoint(resume)
        for key in settings:
            if key not in ('updates', 'checkpoint_every') and settings[key] != saved[key]:
                raise ValueError('strict resume setting mismatch: '+key)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    lineage = [Path(resume).resolve()] if resume is not None else []
    pins = _pins(settings, out, lineage)
    write(out/'inputs_before.json', pins)
    random.seed(settings['seed'])
    np.random.seed(settings['seed'])
    torch.manual_seed(settings['seed'])
    torch.set_num_threads(1)
    pool = None
    started = time.monotonic()
    report = dict(schema=SCHEMA, completed=False, requested_updates=settings['updates'],
                  updates=0, transitions=0, completed_episodes=0, safe_completions=0)
    try:
        pool = WholeBodyPool(settings, out)
        policy = WholeBodyPolicy(STATE_DIM, contract=pool.contract).to(settings['device'])
        trainer = DecisionPPOTrainer(policy, PPOConfig(**settings['ppo']))
        if resume is not None:
            trainer.load(resume)
        collector = WholeBodyCollector(policy, pool)
        write(out/'training_contract.json', pool.contract)
        trainer.save(out/'initial.pt', checkpoint_metadata(settings, pins, out, lineage))
        with (out/'learning_metrics.jsonl').open('x') as metrics_file, (out/'episodes.jsonl').open('x') as episode_file:
            for update in range(settings['updates']):
                write(out/'status.json', dict(phase='collecting', update=update+1, total=settings['updates']))
                buffer, episodes = collector.collect(settings['horizon'])
                metrics = trainer.update(buffer, episodes)
                report['updates'] += 1
                report['transitions'] += int(buffer['valid'].sum())
                report['completed_episodes'] += len(episodes)
                report['safe_completions'] += sum(bool(e['safe_completion']) for e in episodes)
                metrics.update(update=trainer.updates, transitions=report['transitions'],
                               elapsed_s=time.monotonic()-started)
                metrics_file.write(json.dumps(metrics, ensure_ascii=False, allow_nan=False)+'\n')
                metrics_file.flush()
                for episode in episodes:
                    episode_file.write(json.dumps(episode, ensure_ascii=False, allow_nan=False)+'\n')
                episode_file.flush()
                if trainer.updates % settings['checkpoint_every'] == 0:
                    trainer.save(out/f'checkpoint_{trainer.updates:06d}.pt', checkpoint_metadata(settings, pins, out, lineage))
        trainer.save(out/'final.pt', checkpoint_metadata(settings, pins, out, lineage))
        if not verify(pins):
            raise ValueError('run inputs changed during training')
        report.update(completed=True, final_checkpoint=str(out/'final.pt'), elapsed_s=time.monotonic()-started)
    except BaseException as error:
        report.update(error=type(error).__name__+': '+str(error), elapsed_s=time.monotonic()-started)
        raise
    finally:
        try:
            if pool is not None:
                pool.close()
        except BaseException as error:
            report.update(completed=False, close_error=type(error).__name__+': '+str(error))
            raise
        finally:
            write(out/'report.json', report)
            write(out/'status.json', dict(phase='complete' if report['completed'] else 'failed', **report))
    return report


def evaluate(checkpoint, out):
    """각 환경 첫 에피소드만 집계하며 Actor만 실행한다. 재시작으로 성공을 선별하지 않는다."""
    settings, policy = read_checkpoint(checkpoint)
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    write(out/'settings.json', settings)
    pins = _pins(settings, out, [Path(checkpoint).resolve()])
    write(out/'inputs_before.json', pins)
    pool = None
    records, seen = [], set()
    try:
        pool = WholeBodyPool(settings, out)
        if portable(pool.contract) != portable(policy.architecture['contract']):
            raise ValueError('evaluation physical/observation/control contract mismatch')
        policy.to(settings['device']).eval()
        observation = pool.observation
        with torch.no_grad():
            for _ in range(round(settings['duration_s']*60)):
                active = policy.actor_action(observation['state'], deterministic=True)
                actions = torch.cat((active, active.new_zeros(len(active), 2)), -1)
                observation, reward, cost, terminated, truncated, episodes = pool.step(actions)
                for episode in episodes:
                    if episode['env_id'] not in seen:
                        seen.add(episode['env_id'])
                        records.append(episode)
                if len(seen) == pool.num_envs:
                    break
                done = (terminated | truncated).nonzero().flatten()
                if done.numel():
                    observation = pool.reset(done)[0]
        if len(seen) != pool.num_envs or not verify(pins):
            raise ValueError('incomplete first-episode evaluation or changed inputs')
        result = dict(schema='guitar_learning.whole_body_evaluation.v1', completed=True,
            checkpoint=str(Path(checkpoint).resolve()), environment_count=pool.num_envs,
            safe_completions=sum(bool(e['safe_completion']) for e in records), episodes=records,
            scope='first episode per environment; fixed-root prepared-hand support; not musical success')
        write(out/'evaluation.json', result)
        return result
    finally:
        if pool is not None:
            pool.close()
