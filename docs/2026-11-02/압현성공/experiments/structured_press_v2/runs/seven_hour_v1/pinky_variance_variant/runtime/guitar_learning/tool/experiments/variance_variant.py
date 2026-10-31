"""격리 B 학습에서 목표 손가락4축의 유효 Gaussian sigma만 비교한다."""
if __name__ == '__main__':
    import isaacgym
    from guitar_learning.tool.experiments.structured_geometry import nested_input_paths
    _entry = nested_input_paths(); _entry.__enter__()

import argparse
import copy
from contextlib import contextmanager
import hashlib
import json
import math
from pathlib import Path
from types import SimpleNamespace
import torch
from guitar_learning.portability import localize
from guitar_learning.training import finger_skill_runner as official
from guitar_learning.training.ppo import PPOConfig
from guitar_learning.tool.experiments import structured_press as sp
from guitar_learning.tool.experiments.variance_reset_protocol import fixed_reset_context

ROOT = Path(__file__).resolve().parents[3]
STUDY = ROOT.parent
TRANSFER = ROOT/'transfer_inputs/index_A100.pt'
BASE_POLICY = sp.StructuredPolicy
FACTORS = (.05, .1)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def verify_audit():
    seal = json.loads((STUDY/'source_seal.json').read_text())
    manifest = json.loads((STUDY/'copy_manifest.json').read_text())
    for name, sha in seal['files'].items():
        if not (ROOT/name).is_file() or digest(ROOT/name) != sha:
            raise ValueError('variant source/input changed: '+name)
    for name, sha in manifest['base_files'].items():
        if digest(Path(manifest['original_runtime'])/name) != sha:
            raise ValueError('original frozen runtime changed: '+name)
    if digest(TRANSFER) != manifest['checkpoint_sha256'] or digest(manifest['original_checkpoint']) != manifest['checkpoint_sha256']:
        raise ValueError('original/copied A100 checkpoint changed')
    return digest(STUDY/'source_seal.json')


def variance_config(factor, finger):
    if factor not in FACTORS: raise ValueError('factor must be .05 or .1')
    start = 17+4*sp.FINGERS.index(finger)
    return dict(schema='guitar_learning.finger_variance.v1', factor=factor,
        selected_axes=list(range(start, start+4)),
        distribution='기존 forward/floor 후 선택4축 log_std에 log(factor) 추가; 확률·KL·entropy 모두 같은 분포 사용',
        all_other_axes='변경 없음', base_floor=.10, effective_floor=.10*factor)


class VariancePolicy(BASE_POLICY):
    schema = 'guitar_learning.structured_variance_policy.v1'

    def __init__(self, *args, factor, **kwargs):
        super().__init__(*args, **kwargs)
        self.variance = variance_config(factor, self.structured['finger'])
        self.architecture['variance_variant'] = copy.deepcopy(self.variance)

    def forward(self, *inputs):
        result = super().forward(*inputs)
        first = self.variance['selected_axes'][0]
        std = result['log_std']
        result['log_std'] = torch.cat((std[:, :first],
            std[:, first:first+4]+math.log(self.variance['factor']), std[:, first+4:]), -1)
        return result

    def initialize_from(self, checkpoint, *, expected_sha256):
        if digest(checkpoint) != expected_sha256: raise ValueError('transfer SHA mismatch')
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        source = payload['identity']['architecture']
        with torch.random.fork_rng(devices=[]):
            if source['schema'] == BASE_POLICY.schema:
                # 원래 base B 이전 경로가 source의 전체 identity/input/인접단계를 그대로 검증한다.
                bridge = BASE_POLICY(self.architecture['state_dim'], size=self.architecture['size'],
                    contract=self.architecture['contract'], structured=self.structured)
                bridge.initialize_from(checkpoint, expected_sha256=expected_sha256)
                weights = bridge.state_dict()
            elif source['schema'] == self.schema:
                official._validate_pins(payload['metadata'])
                saved = localize(payload['metadata']['settings'])
                old = saved['structured_press']
                if (self.structured['stage'] != 'free_v9' or old['stage'] != 'B' or
                    old['song'] != self.structured['song'] or old['geometry_sha256'] != self.structured['geometry_sha256'] or
                    saved['variance_variant'] != self.variance or saved['size'] != self.architecture['size']):
                    raise ValueError('explicit same-factor/song/geometry B -> free_v9 transfer required')
                previous = VariancePolicy(source['state_dim'], size=saved['size'],
                    contract=localize(source['contract']), structured=old, factor=self.variance['factor'])
                trainer = sp.StructuredTrainer(previous, PPOConfig(**saved['ppo']))
                if trainer._identity() != payload['identity']: raise ValueError('original variant identity mismatch')
                previous.load_state_dict(payload['model'], strict=True)
                weights = previous.state_dict(); weights['active_mask'] = self.active_mask
            else: raise ValueError('unsupported source schema')
        if not all(torch.isfinite(v).all() for v in weights.values()): raise ValueError('nonfinite transfer')
        if digest(checkpoint) != expected_sha256: raise ValueError('transfer source changed')
        self.load_state_dict(weights, strict=True)


@contextmanager
def variant_runtime(settings, source=None):
    config, variance = settings['structured_press'], settings['variance_variant']
    if variance != variance_config(variance['factor'], config['finger']): raise ValueError('variance settings mismatch')
    with sp.structured_runtime(config):
        original = official._policy, official._pins, official.checkpoint_metadata
        def factory(current, pool):
            if current.get('variance_variant') != variance: raise ValueError('saved variance settings mismatch')
            policy = VariancePolicy(pool.observation['state'].shape[-1], size=current['size'],
                contract=pool.contract, structured=config, factor=variance['factor']).to(current['device'])
            if source is not None: policy.initialize_from(source, expected_sha256=digest(TRANSFER))
            return policy
        def pins(current, out, extra=()):
            return original[1](current, out, list(extra)+([TRANSFER] if source else []))
        def metadata(*args, **kwargs):
            if source: kwargs['lineage'] = list(kwargs.get('lineage', ()))+[TRANSFER]
            return original[2](*args, **kwargs)
        official._policy, official._pins, official.checkpoint_metadata = factory, pins, metadata
        try: yield
        finally: official._policy, official._pins, official.checkpoint_metadata = original


def train_settings(factor, updates=100, seed=7):
    payload = torch.load(TRANSFER, map_location='cpu', weights_only=False)
    saved = localize(payload['metadata']['settings'])
    old = saved['structured_press']
    settings = sp.build_settings(old['song'], 'B', old['geometry'], num_envs=64,
        updates=updates, size='large', seed=seed)
    settings['variance_variant'] = variance_config(factor, old['finger'])
    settings['structured_transfer'] = dict(source=str(TRANSFER), sha256=digest(TRANSFER),
        scope='엄격한 base A100 -> 새 분산 B 가중치만 이전; 새 Adam/RNG')
    return settings



def initial_audit(out):
    source = torch.load(TRANSFER, map_location='cpu', weights_only=False)
    initial = torch.load(out/'J/initial.pt', map_location='cpu', weights_only=False)
    changed = [name for name, value in source['model'].items() if name != 'active_mask'
               and not torch.equal(value, initial['model'][name])]
    if changed: raise ValueError('initial model differs from A100 source: '+str(changed[:8]))
    tensor_sha = lambda value: hashlib.sha256(value.cpu().numpy().tobytes()).hexdigest()
    result = dict(all_initial_model_tensors_equal_source_except_active_mask=True,
        torch_rng_sha256=tensor_sha(initial['torch_rng']),
        cuda_rng_sha256=[tensor_sha(value) for value in initial['cuda_rng']] if initial['cuda_rng'] else [])
    control = STUDY.parent/'index_B_seed7_v1/100/train/J/initial.pt'
    if control.is_file():
        previous = torch.load(control, map_location='cpu', weights_only=False)
        result.update(control_initial_checkpoint=str(control), control_initial_sha256=digest(control),
            control_cpu_torch_rng_equal=torch.equal(previous['torch_rng'], initial['torch_rng']),
            control_cuda_rng_equal=(previous['cuda_rng'] is not None and initial['cuda_rng'] is not None and
                len(previous['cuda_rng']) == len(initial['cuda_rng']) and
                all(torch.equal(a, b) for a, b in zip(previous['cuda_rng'], initial['cuda_rng']))))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('train', 'evaluate', 'render', 'evaluate-free-v9'))
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--factor', type=float, choices=FACTORS)
    parser.add_argument('--checkpoint', type=Path)
    parser.add_argument('--updates', type=int, default=100)
    parser.add_argument('--seed', type=int, default=7)
    parser.add_argument('--reset-seed', type=int, default=4242)
    args = parser.parse_args()
    args.out = args.out.resolve()
    if args.out.exists(): raise FileExistsError('existing output must not be overwritten')
    audit = verify_audit()
    source = TRANSFER if args.operation == 'train' else args.checkpoint
    if source is None: parser.error('evaluation/render requires --checkpoint')
    source = source.resolve(); source_sha = digest(source)
    if args.operation == 'train':
        if args.factor is None or args.checkpoint: parser.error('fresh transfer training requires --factor only')
        if args.updates < 1: parser.error('positive updates required')
        settings = train_settings(args.factor, args.updates, args.seed)
    else:
        payload = torch.load(source, map_location='cpu', weights_only=False)
        settings = localize(payload['metadata']['settings'])
        factor = settings['variance_variant']['factor']
        if args.factor is not None and factor != args.factor: parser.error('saved factor mismatch')
        if payload['identity']['architecture']['schema'] != VariancePolicy.schema: raise ValueError('variant schema required')
    record = None
    if args.operation == 'evaluate-free-v9':
        original = sp.StructuredPolicy
        sp.StructuredPolicy = lambda *a, **k: VariancePolicy(*a, factor=settings['variance_variant']['factor'], **k)
        try: sp.evaluate_free_v9(source, args.out, num_envs=32)
        finally: sp.StructuredPolicy = original
    else:
        with variant_runtime(settings, source if args.operation == 'train' else None):
            if args.operation == 'train':
                official.run(settings, SimpleNamespace(out=args.out, resume=None))
            elif args.operation == 'evaluate':
                with fixed_reset_context(sp, official, args.reset_seed, settings['structured_press']) as record:
                    official.evaluate_checkpoint(source, args.out, num_envs=32, scope='full_song', max_episodes=32)
            else:
                from guitar_learning.tool.demonstration.render_finger_skill import render
                render(source, args.out, num_envs=4, scope='full_song')
    if digest(source) != source_sha or verify_audit() != audit: raise ValueError('source or sealed inputs changed')
    path = args.out/'report.json'; report = json.loads(path.read_text())
    report.update(variance_variant=settings['variance_variant'], variance_source_seal_sha256=audit,
        operation=args.operation, source_sha256=source_sha, original_source_checkpoint_unchanged=True,
        exported_policy_schema_is_distinct=True,
        distinct_policy_schema=VariancePolicy.schema, original_frozen_runtime_unchanged=True)
    if args.operation == 'train': report['initial_transfer_audit'] = initial_audit(args.out)
    if record:
        if record['initial_conditions'] is None: raise ValueError('paired reset capture missing')
        report.update(reset_seed=args.reset_seed, initial_conditions=record['initial_conditions'],
            reset_audit_events=record['events'], cross_model_pairing_verified=False)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    try: main()
    finally: _entry.__exit__(None, None, None)
