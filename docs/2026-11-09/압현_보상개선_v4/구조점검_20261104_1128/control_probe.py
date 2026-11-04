"""실제 목표각 변환의 탐색 크기를 CPU에서 측정한다. 물리·학습 실행이 아니다."""
import hashlib
import json
from pathlib import Path

import torch

from guitar_learning.gpu.control import BatchedController


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent
CONTRACT = OUT.parent / '검증/native_train/J/training_contract.json'
SPEC = json.loads(CONTRACT.read_text())['native_backend']['control']


def controller(count):
    obj = BatchedController.__new__(BatchedController)
    obj.num_envs, obj.device = count, torch.device('cpu')
    obj.reference = torch.tensor(SPEC['reference105_rad'])
    obj.active = torch.tensor([SPEC['joint_names'].index(n) for n in SPEC['action_order']])
    obj.action_low = torch.tensor(SPEC['action_lower_rad'])
    obj.action_high = torch.tensor(SPEC['action_upper_rad'])
    obj.lower, obj.upper = obj.reference.clone(), obj.reference.clone()
    obj.lower[obj.active], obj.upper[obj.active] = obj.action_low, obj.action_high
    obj.alpha = torch.tensor(SPEC['smoothing_alpha'])
    obj.rate = torch.tensor(SPEC['rate_rad_s'])
    obj.zero = torch.tensor(SPEC['zero_indices'])
    obj.target = obj.reference.expand(count, -1).clone()
    # 발 IK는 손가락 채널을 변경하지 않으며 이 진단에서는 실행하지 않는다.
    obj._foot_targets = lambda target: target
    return obj


def run(label, support_std, finger_std):
    torch.manual_seed(7)
    obj = controller(8192)
    std = torch.tensor([support_std]*17 + [finger_std]*16)
    idx = obj.active[17:33]
    rows = []
    limited, total = 0, 0
    for tick in range(60):
        action = torch.zeros(obj.num_envs, 39)
        action[:, :33] = torch.tanh(torch.randn(obj.num_envs, 33)*std)
        reference = obj.reference[obj.active]
        requested = reference + torch.where(action >= 0,
            obj.action_high-reference, reference-obj.action_low)*action
        before = obj.target[:, idx].clone()
        exceeded = (requested[:, 17:33]-before).abs() > obj.rate[idx]/60
        limited += int(exceeded.sum())
        total += exceeded.numel()
        result = obj.targets(action, None)[:, idx]
        if tick in (0, 59):
            for column, name in enumerate(SPEC['action_order'][17:33]):
                rows.append(dict(tick=tick+1, joint=name,
                    request_std_deg=float(requested[:, 17+column].std()*180/torch.pi),
                    target_std_deg=float(result[:, column].std()*180/torch.pi),
                    request_mean_offset_deg=float((requested[:, 17+column]-obj.reference[idx[column]]).mean()*180/torch.pi),
                    target_mean_offset_deg=float((result[:, column]-obj.reference[idx[column]]).mean()*180/torch.pi),
                    rate_limited_fraction=float(exceeded[:, column].float().mean())))
    return dict(label=label, support_std=support_std, finger_std=finger_std,
        limited_fraction=limited/total, per_joint=rows)


if __name__ == '__main__':
    torch.set_num_threads(1)
    results = [run('v4 current default', float(torch.exp(torch.tensor(-3.))), float(torch.exp(torch.tensor(-3.)))),
               run('previous v2 long-run initialization', .15, .35)]
    report = dict(scope='zero-mean independent tanh-Normal,8192 samples,60 control steps; real BatchedController.targets; foot IK omitted; no physics, policy learning, force, or musical success claim',
        input_sha256=hashlib.sha256(CONTRACT.read_bytes()).hexdigest(),
        control_source_sha256=hashlib.sha256((ROOT/'guitar_learning/gpu/control.py').read_bytes()).hexdigest(),
        max_finger_target_step_deg=4/60*180/float(torch.pi), cases=results)
    (OUT/'control_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    for case in results:
        print(case['label'], 'rate-limited fraction', round(case['limited_fraction'],6))
        for tick in (1,60):
            rows = [r for r in case['per_joint'] if r['tick']==tick]
            print(' tick',tick,'mean request/target std degrees',
                round(sum(r['request_std_deg'] for r in rows)/16,6),
                round(sum(r['target_std_deg'] for r in rows)/16,6))
