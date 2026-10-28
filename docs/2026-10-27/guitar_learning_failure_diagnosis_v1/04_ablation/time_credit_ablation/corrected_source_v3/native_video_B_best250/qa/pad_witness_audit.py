"""Read-only CPU reconstruction of the eight saved audible pad witnesses."""
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import torch

from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
from guitar_learning.tests.test_gpu_environment import BUNDLE, fixture
from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment


HERE = Path(__file__).resolve().parent
ROOT = Path('/home/ajou/yigyu/3')
SOURCE = ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/support/current_contact_replay.py'


def main():
    output = HERE/'pad_witness_audit.json'
    if output.exists():
        raise FileExistsError(str(output))
    settings = json.loads((HERE.parent/'settings.json').read_text())
    view = settings['song']['short_learning']['view']
    raw = np.load(HERE.parent/'poses_env0000.npz', allow_pickle=False)
    audible = ((raw['source_time_s'] >= view['source_target']['onset_s']) &
               (raw['source_time_s'] < view['source_target']['end_s']))
    count = int(audible.sum())
    metadata, snapshot = fixture(count)
    capture = json.loads((HERE.parent/'capture_metadata.json').read_text())
    assert metadata['body_names'] == capture['body_names']
    assert metadata['joint_names'] == capture['joint_names']
    for key in snapshot:
        snapshot[key] = torch.tensor(raw[key][audible])
    env = ShortEnvironment(metadata, bundle=BUNDLE, song=settings['song'],
                           skill=settings['finger_skill'], device='cpu')
    env.reset(torch.arange(count), snapshot)
    spec = importlib.util.spec_from_file_location('existing_pad_masks', SOURCE)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    indices = torch.full((count,), env.selected_index, dtype=torch.long)
    mask = replay.sample_masks(env, [None]*count, indices)['positive_mask'].numpy()
    assert np.array_equal(mask.any(-1), env.contact_loaded_target[:, env.selected_index].numpy())
    assert np.array_equal(raw['candidate'][audible], env.candidate[:, env.selected_index].numpy())
    assert np.array_equal(raw['wrong'][audible], env.wrong[:, env.selected_index].numpy())
    pad = load_fingertip_pad()
    low, high = pad['contract']['fingers_diagnostics'][1]['mesh_y_bounds_m']
    u = (high-pad['points_local'][1, :, 1])/(high-low)
    nearest = env.surface_sample[:, env.selected_index].numpy()-128
    rows = [dict(local_time_s=float(t), positive_samples=int(w.sum()),
                 positive_u_min=float(u[w].min()), positive_u_max=float(u[w].max()),
                 positive_distal_quarter_samples=int((w & (u >= .75)).sum()),
                 nearest_u=float(u[n]))
            for t, w, n in zip(raw['time_s'][audible], mask, nearest)]
    paths = [Path(__file__).resolve(), SOURCE, HERE.parent/'poses_env0000.npz',
             HERE.parent/'settings.json', HERE.parent/'capture_metadata.json',
             ROOT/'guitar_learning/gpu/fingertip_pad.py',
             ROOT/'guitar_learning/tests/test_gpu_environment.py']
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    recorded = json.loads((HERE.parent/'inputs_before.json').read_text())
    source_pins_match = all(recorded[str(p)] == pins[str(p)] for p in paths[-2:])
    assert source_pins_match and not torch.cuda.is_initialized()
    result = dict(scope='env0 first attempt, eight audible60Hz endpoints; source-mesh geometric witnesses, not actual contact points or pair pressure',
                  u_definition='(mesh_ymax-local_y)/(mesh_ymax-mesh_ymin); distal quarter u>=0.75',
                  candidate_wrong_and_positive_aggregate_match=True,
                  recorded_source_pins_match=source_pins_match, cuda_initialized=False,
                  rows=rows, input_sha256=pins)
    with output.open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(rows))


if __name__ == '__main__':
    main()
