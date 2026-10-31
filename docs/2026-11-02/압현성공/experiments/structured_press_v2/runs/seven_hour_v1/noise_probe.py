"""A 고정 체크포인트의 활성 손가락 탐색 잡음만 바꾸는 평가 진단이다.

새 모델을 저장하지 않으며 학습 성과나 원래 결정적 평가와 구분한다.
"""
if __name__ == '__main__':
    import isaacgym  # native 라이브러리를 torch보다 먼저 로드한다.

import argparse
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
STUDY = ROOT.parents[1]
RUNTIME = STUDY/'runtime'
sys.path.insert(0, str(RUNTIME))
SCALES = (0., .25, .5, 1.)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            result.update(chunk)
    return result.hexdigest()


def validate_scale(scale):
    if isinstance(scale, bool) or not isinstance(scale, (int, float)) or scale not in SCALES:
        raise ValueError('scale must be one of 0, .25, .5, 1')
    return float(scale)


def scaled_result(result, active, scale):
    """저장 분포의 floor를 포함한 원래 forward 이후 활성 축 sigma에만 배수를 준다."""
    scale = validate_scale(scale)
    adjusted = dict(result)
    if scale > 0 and scale != 1:
        adjusted['log_std'] = result['log_std']+active.to(result['log_std'].dtype)*math.log(scale)
    return adjusted


class SamplingPolicy:
    def __init__(self, policy, scale):
        self.policy, self.phase, self.scale = policy, policy.phase, validate_scale(scale)

    def __call__(self, *inputs):
        return self.policy(*inputs)

    def act(self, *inputs):
        return self.policy.act(*inputs, deterministic=self.scale == 0)


def verify_source_seal():
    seal_path = STUDY/'source_seal.json'
    seal = json.loads(seal_path.read_text())
    if len(seal['files']) != 3148:
        raise ValueError('expected immutable 3148-file source seal')
    changed = [name for name, sha in seal['files'].items()
               if not (RUNTIME/name).is_file() or digest(RUNTIME/name) != sha]
    if changed:
        raise ValueError('frozen runtime changed: '+str(changed[:8]))
    return digest(seal_path)


@contextmanager
def sampling_override(sp, official, scale):
    """저장 architecture/가중치는 유지하고 평가의 분포 출력·표본화만 임시 교체한다."""
    validate_scale(scale)
    original_forward = sp.StructuredPolicy.forward
    original_wrapper, original_pins = official._DeterministicPolicy, official._pins
    def forward(policy, *inputs):
        return scaled_result(original_forward(policy, *inputs), policy.active_mask, scale)
    def pins(settings, out, extra=()):
        return original_pins(settings, out, list(extra)+[Path(__file__).resolve()])
    sp.StructuredPolicy.forward = forward
    official._DeterministicPolicy = lambda policy: SamplingPolicy(policy, scale)
    official._pins = pins
    try:
        yield
    finally:
        sp.StructuredPolicy.forward = original_forward
        official._DeterministicPolicy, official._pins = original_wrapper, original_pins


def validate_payload(payload, sp, official):
    import torch
    from guitar_learning.portability import localize
    from guitar_learning.training.ppo import PPOConfig
    metadata = payload.get('metadata')
    official._validate_metadata_schema(metadata)
    official._validate_pins(metadata)
    settings = localize(metadata['settings'])
    config = settings['structured_press']
    start = 17+4*sp.FINGERS.index(config['finger'])
    if config['stage'] != 'A' or config['active_axes'] != list(range(start, start+4)):
        raise ValueError('noise probe supports A with exactly its assigned four finger axes only')
    # 표본화 override 설치 전에 저장본 identity/모델 키·형상·유한값을 검사한다.
    architecture = localize(payload['identity']['architecture'])
    policy = sp.StructuredPolicy(architecture['state_dim'], size=settings['size'],
        contract=architecture['contract'], structured=config)
    trainer = sp.StructuredTrainer(policy, PPOConfig(**settings['ppo']))
    if trainer._identity() != payload['identity']:
        raise ValueError('original checkpoint identity/config/input architecture mismatch')
    if not all(torch.isfinite(value).all() for value in payload['model'].values()):
        raise ValueError('nonfinite original model')
    policy.load_state_dict(payload['model'], strict=True)
    del trainer, policy, payload
    return settings, config


def run(checkpoint, scale, out):
    scale = validate_scale(scale)
    checkpoint, out = Path(checkpoint).resolve(), Path(out).resolve()
    if out.exists():
        raise FileExistsError('existing diagnostic output must not be overwritten: '+str(out))
    before = digest(checkpoint)
    script_before = digest(__file__)
    source_seal = verify_source_seal()
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    # render_policy.py와 동일하게 모듈이 준비 입력을 읽기 전에 경로 컨텍스트에 진입한다.
    with nested_input_paths():
        import random
        import numpy as np
        import torch
        from guitar_learning.training import finger_skill_runner as official
        from guitar_learning.tool.experiments import structured_press as sp
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        settings, config = validate_payload(payload, sp, official)
        del payload
        seed = settings['seed']
        random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
        annotation = dict(schema='diagnostic_sampling_override.v1',
            sampling_mode='deterministic_mean' if scale == 0 else 'stochastic_latent_gaussian',
            scale=scale, checkpoint_training_seed=seed,
            sampling_rng='official strict load restores saved checkpoint CPU/CUDA RNG; same checkpoint state for every scale',
            original_saved_distribution=scale == 1, policy_mean_unchanged=True,
            model_parameters_unchanged=True, source_checkpoint=str(checkpoint), source_sha256=before,
            diagnostic_script_sha256=script_before, frozen_source_seal_sha256=source_seal,
            original_identity_validated_before_sampling=True, new_checkpoint_saved=False,
            active_noise_axes=config['active_axes'], failed_episodes_in_denominator=True,
            diagnostic_only=True, limitations=[
                'evaluation-only A supported aligned noise diagnostic; no training or new checkpoint',
                'fixed checkpoint RNG and 32 first episodes; not a multi-seed generalization estimate'])
        try:
            with sp.structured_runtime(config):
                with sampling_override(sp, official, scale):
                    report, rows = official.evaluate_checkpoint(checkpoint, out, num_envs=32,
                        scope='full_song', max_batches=1, max_episodes=32)
        finally:
            # 부분 실패도 공식 성능 평가로 오인되지 않도록 보고서에 진단임을 남긴다.
            report_path = out/'report.json'
            if report_path.is_file():
                recorded = json.loads(report_path.read_text())
                recorded['original_report_schema'] = recorded['schema']
                recorded.update(annotation)
                report_path.write_text(json.dumps(recorded, ensure_ascii=False, indent=2)+'\n')
    if not report['completed'] or len(rows) != 32 or {row['env_id'] for row in rows} != set(range(32)):
        raise ValueError('completed first episode for each of 32 environments required')
    if before != digest(checkpoint) or script_before != digest(__file__) or source_seal != verify_source_seal():
        raise ValueError('source checkpoint, diagnostic script or sealed runtime changed')
    original_report_schema = report['schema']
    report.update(annotation)
    report.update(
        original_report_schema=original_report_schema,
        failure_episode_count=sum(bool(row['termination']['physical_failure'] or
            row['termination']['wrist_failure']) for row in rows),
        first_episode_per_env=True,
        limitations=['evaluation-only sampling override; no training or new checkpoint',
            'A supported aligned initial distribution only; no unassisted-v9 claim',
            'scale1 samples the saved distribution; scale0 is its deterministic mean',
            'sigma scaling is applied after saved forward/floor; inactive axes and policy means are unchanged',
            'one fixed saved checkpoint RNG and 32 first episodes; not a multi-seed generalization estimate',
            'compares noise at one fixed model; evolving-policy training episode success is a separate statistic'])
    (out/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--scale', required=True, type=float, choices=SCALES)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    run(args.checkpoint, args.scale, args.out)


if __name__ == '__main__':
    main()
