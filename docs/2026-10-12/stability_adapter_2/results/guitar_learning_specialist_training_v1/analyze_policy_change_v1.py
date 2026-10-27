"""Fixed recorded observations: output changes, not a physical policy test."""
import hashlib
import json
from pathlib import Path
import sys
import torch

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
from guitar_learning.specialist_policy import SpecialistPolicy

PHASE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    torch.set_num_threads(1)
    result = {}
    for hand in ('left', 'right'):
        folder = PHASE/(hand+'_run_v1')
        if not json.loads((folder/'report.json').read_text())['completed']:
            raise RuntimeError('closed successful native run required')
        rollout = torch.load(folder/'rollout_first.pt', map_location='cpu', weights_only=False)
        inputs = [rollout[k].flatten(0, 1) for k in ('state', 'events', 'mask', 'priority_events', 'priority_mask')]
        paths = [folder/'initial.pt', *sorted(folder.glob('checkpoint_*.pt')), folder/'final.pt']
        rows = []
        for path in paths:
            payload = torch.load(path, map_location='cpu', weights_only=False)
            architecture = payload['identity']['architecture']
            model = SpecialistPolicy(architecture['state_dim'], size=architecture['size'],
                contract=architecture['contract'], role=architecture['role'], frozen_partner=architecture['frozen_partner'])
            model.load_state_dict(payload['model'], strict=True)
            with torch.no_grad():
                selected = model.role_slices[hand]
                output = model.act(*inputs, deterministic=True)['action'][:, selected]
            half = torch.tensor(architecture['contract']['action']['offset_half_range_rad'])[selected]
            rows.append(dict(checkpoint=str(path), sha256=sha(path), updates=payload['updates'],
                deterministic_action_rms_normalized=float(output.square().mean().sqrt()),
                deterministic_action_abs_max_normalized=float(output.abs().max()),
                unfiltered_requested_offset_rms_rad=float((output*half).square().mean().sqrt()),
                active_raw_std_mean=float(model.log_std[selected].exp().mean())))
        result[hand] = dict(recorded_state_count=inputs[0].shape[0],
            rollout_sha256=sha(folder/'rollout_first.pt'), checkpoints=rows)
    with (PHASE/'policy_change_v1.json').open('x') as stream:
        json.dump(dict(roles=result,
            scope='deterministic neural outputs on fixed first-rollout observations; offsets are before codec smoothing/rate/joint limits; not actual joint motion or held-out native success'), stream, indent=2)
        stream.write('\n')
    print(json.dumps({hand: result[hand]['checkpoints'][-1] for hand in result}))


if __name__ == '__main__':
    main()
