"""Replay saved60Hz poses through diagnostic accumulators; no native physics/PPO."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
KEYS = ('palm_relative_rotvec_y_rms_rad','palm_relative_rotvec_y_max_abs_rad',
    'zero_y_command_rotation_error_rms_rad','zero_y_command_rotation_error_max_rad',
    'zero_y_command_local_xz_error_rms_rad','zero_y_command_local_xz_error_max_rad')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def reference_metrics(body, target, names, joints):
    import numpy as np
    from scipy.spatial.transform import Rotation
    bases = [names.index('human/LH:'+f+'1') for f in ('index','middle','ring','pinky')]
    axes = [[joints.index('LH:'+f+'1_'+a) for a in ('x','z')] for f in ('index','middle','ring','pinky')]
    palm = body[...,names.index('human/LH:palm'),3:7]
    parent = Rotation.from_quat(np.repeat(palm[...,None,:],4,axis=-2).reshape(-1,4))
    relative = parent.inv()*Rotation.from_quat(body[...,bases,3:7].reshape(-1,4))
    command = np.zeros(target.shape[:2]+(4,3)); command[...,(0,2)] = target[...,axes]
    error = (relative.inv()*Rotation.from_rotvec(command.reshape(-1,3))).as_rotvec().reshape(command.shape)
    y = relative.as_rotvec().reshape(command.shape)[...,1]
    full, xz = np.linalg.norm(error,axis=-1), np.linalg.norm(error[...,(0,2)],axis=-1)
    rows = [v for values in (y,full,xz) for v in (np.sqrt(np.mean(values**2,axis=0)),np.max(abs(values),axis=0))]
    return dict(zip(KEYS,rows))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--capture',type=Path,required=True); parser.add_argument('--manifest',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True); parser.add_argument('--device',default='cpu',choices=('cpu','cuda:0'))
    args = parser.parse_args(); manifest = json.loads(args.manifest.read_text()); source = manifest['source']
    original = json.loads((args.capture/'inputs_before.json').read_text())
    changed = sorted(p for p in source if p in original and source[p]!=original[p])
    added = sorted(set(source)-set(original))
    if changed!=sorted(manifest['changed_from435']) or added!=sorted(manifest['added_from435']):
        raise ValueError('Source deviations do not match the approved diagnostic manifest')
    pins = dict(original); pins.update(source)
    pins[str((args.capture/'inputs_before.json').resolve())] = digest(args.capture/'inputs_before.json')
    pins.update({str(args.manifest.resolve()):digest(args.manifest),str(Path(__file__).resolve()):digest(__file__)})
    def check(ok,message):
        if not ok: raise ValueError(message)
    def read(name):
        path = args.capture/name; pins[str(path.resolve())] = digest(path); return json.loads(path.read_text())
    check(all(Path(p).is_file() and digest(p)==h for p,h in pins.items()),'Current source pins differ')
    meta, report, settings, old = [read(n) for n in ('capture_metadata.json','report.json','settings.json','training_contract.json')]
    check(report['completed'] and report['schedule_completed'] and report['gpu_scene']['closed'] and
        report['actual_control_ticks']==525 and len(meta['cases'])==6,'Complete closed baseline N6/525 required')
    import numpy as np
    import torch
    from guitar_learning.gpu.environment import TensorSongEnvironment
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.training.recording import project_source_paths
    from guitar_learning.training import json_io
    torch.set_num_threads(1); metadata, sample = fixture(6)
    check(metadata['body_names']==meta['body_names'] and metadata['joint_names']==meta['joint_names'],'Source body/joint order differs')
    metadata['action_contract'] = old['action']['target_contract']
    env = TensorSongEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],hand='left',device=args.device)
    check(all(env.contract[k]==old[k] for k in ('observation','action','task','reward','termination')),'Training semantics changed')
    legacy = copy.deepcopy(env.contract['diagnostics']['left_finger_motion']); legacy.pop('base_rotation'); legacy['schema']='guitar_learning.gpu_left_finger_motion.v1'
    check(legacy==old['diagnostics']['left_finger_motion'],'Unexpected legacy diagnostic change')
    captures = []
    for row,case in enumerate(meta['cases']):
        path = args.capture/case['path']; check(case['env_id']==row and digest(path)==case['sha256'],'Capture pin/row differs')
        pins[str(path.resolve())] = digest(path)
        with np.load(path,allow_pickle=False) as a: captures.append({k:a[k].copy() for k in ('body_state','q','qd','target','action','clock')})
    arrays = {k:np.stack([a[k] for a in captures],axis=1) for k in captures[0]}
    check(all(np.isfinite(a).all() for a in arrays.values()) and arrays['body_state'].shape==(526,6,106,13) and
        np.array_equal(arrays['clock'],np.repeat((np.arange(526)*4)[:,None],6,axis=1)),'Invalid source frames/clock')
    tensors = {k:torch.as_tensor(v,device=args.device) for k,v in arrays.items() if k!='clock'}
    sample = {k:v.to(args.device) for k,v in sample.items()}
    sample.update({k:tensors[k][0] for k in ('body_state','q','qd','target')}); env.reset(list(range(6)),sample)
    for frame in range(1,526):
        env.snapshot = {k:tensors[k][frame] for k in ('body_state','q','qd','target')}; env.body = env.snapshot['body_state']
        env.action = tensors['action'][frame]; action = env.action[:,env.finger_action_indices]
        before = tensors['target'][frame-1,:,env.finger_joint_indices]
        env.finger_outward = ((before<=env.finger_lower+1e-6)&(action<0)) | ((before>=env.finger_upper-1e-6)&(action>0))
        env._record_finger_motion(); env.previous_action = env.action.clone(); env.steps += 1
    actual = [env._finger_motion_episode(i)['base_rotation'] for i in range(6)]
    expected = reference_metrics(arrays['body_state'][1:],arrays['target'][1:],meta['body_names'],meta['joint_names'])
    differences = {k:float(np.max(abs(np.asarray([v['values'][k] for v in actual])-expected[k]))) for k in KEYS}
    check(all(v['endpoint_samples']==525 and v['sampling_hz']==60 for v in actual) and max(differences.values())<1e-6,'SciPy diagnostic mismatch')
    missing = sorted(project_source_paths(list(sys.modules.items()))-set(pins)); check(not missing,'Unpinned imported sources: '+str(missing))
    check(all(Path(p).is_file() and digest(p)==h for p,h in pins.items()),'Inputs changed during replay')
    with args.out.open('x') as stream:
        json_io.dump(dict(completed=True,device=args.device,endpoint_samples=525,rows=6,max_abs_error_rad=differences,
            actual=actual,scipy={k:v.tolist() for k,v in expected.items()},inputs_sha256=pins,
            scope='Saved native60Hz endpoint replay of diagnostic formulas only; no new native physics, policy/PPO,240Hz extrema, drive torque or musical success.'),stream,indent=2,allow_nan=False)


if __name__=='__main__': main()
