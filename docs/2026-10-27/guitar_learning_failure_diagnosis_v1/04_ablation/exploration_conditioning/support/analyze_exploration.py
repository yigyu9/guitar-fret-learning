"""CPU-only prepared035 target-codec/FK exploration; no native simulation."""
import hashlib
import json
from pathlib import Path
import time
from types import SimpleNamespace

import numpy as np

ROOT = Path('/home/ajou/yigyu/3')
BASE = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'docs/2026-10-27/guitar_learning_failure_diagnosis_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stats(values):
    values = np.asarray(values)
    return dict(n=int(values.size), mean=float(values.mean()), median=float(np.median(values)),
                p05=float(np.quantile(values,.05)), p95=float(np.quantile(values,.95)), maximum=float(values.max()))


def main():
    from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.gpu.fingertip_pad import load_fingertip_pad
    import torch
    from guitar_learning.gpu.control import BatchedController
    torch.set_num_threads(1)
    started = time.monotonic()
    plan = json.loads((BASE/'precommit.json').read_text())
    metadata_path = SOURCE/'02_contact_reward/teacher_fixed_B_export/metadata.json'
    metadata = json.loads(metadata_path.read_text())
    contract = load_prepared_reset_contract()
    pad = load_fingertip_pad()
    names, bodies = metadata['joint_names'], metadata['human_bodies']
    ac = metadata['action_contract']
    active = np.array([names.index(n) for n in ac['action_order']])
    reference = np.array(ac['reference105_rad'],dtype=np.float32)
    lower = np.array(contract['initial']['native_PD_properties']['lower'],dtype=np.float32)
    upper = np.array(contract['initial']['native_PD_properties']['upper'],dtype=np.float32)
    low, high = np.array(ac['action_lower_rad'],dtype=np.float32), np.array(ac['action_upper_rad'],dtype=np.float32)
    alpha, rates = np.array(ac['smoothing_alpha'],dtype=np.float32), np.array(ac['rate_rad_s'],dtype=np.float32)
    assert rates.shape == (105,)
    assert np.all(alpha[:12] == np.float32(.2)) and np.all(rates[active[:12]] == 3.)
    assert ac['action_codec']['mode'] == 'incremental' and np.all(rates[active[12:33]] == 4.)
    assert np.array_equal(reference, np.array(contract['target105'],dtype=np.float32))
    original_pins = json.loads((SOURCE/'baseline/trace_initial/inputs_before.json').read_text())
    controller_file = ROOT/'guitar_learning/gpu/control.py'
    assert original_pins[str(controller_file)] == sha(controller_file)
    from guitar_learning.training.recording import project_source_paths
    import sys
    pins = dict(contract['source_sha256']); pins.update(pad['contract']['source_sha256'])
    pins.update({path:sha(path) for path in project_source_paths(list(sys.modules.items()))})
    extra = [Path(__file__), BASE/'precommit.json', metadata_path, SOURCE/'baseline/trace_initial/inputs_before.json',
             controller_file, ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py',
             ROOT/'guitar_learning/gpu/fingertip_pad.py']
    pins.update({str(p.resolve()):sha(p) for p in extra})
    (BASE/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
    q0 = np.array([r['pos'] for r in contract['state']['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=names,human_bodies=bodies,q_ref=q0),contract['state'])
    finger_names = ('index','middle','ring','pinky')
    local, valid = pad['points_local'], pad['valid']

    def points(q):
        poses = fk(q)
        return np.stack([poses['LH:'+name+'3'][0]+poses['LH:'+name+'3'][1].apply(local[f])
                         for f,name in enumerate(finger_names)])

    baseline = points(reference)
    centroid0 = np.stack([baseline[f,valid[f]].mean(0) for f in range(4)])
    ref = reference[active]

    def step(old, action):
        action = np.clip(action,-1,1)
        requested = ref+np.where(action>=0,high-ref,ref-low)*action
        smoothed = old+alpha*(requested-old)
        transformed = np.maximum(np.minimum(smoothed,old+rates[active]/60),old-rates[active]/60)
        transformed[:,12:33] = old[:,12:33]+action[:,12:33]*np.float32(4/60)
        clipped = np.maximum(np.minimum(transformed,high),low)
        clipped = np.maximum(np.minimum(clipped,old+rates[active]/60),old-rates[active]/60)
        clipped = np.maximum(np.minimum(clipped,upper[active]),lower[active])
        return clipped, np.abs(transformed-clipped)>1e-7

    # Call the production target method on CPU tensors to verify selected channels.
    # Foot IK is deliberately identity: its lower branch is outside both masks and
    # cannot alter these arm/finger channels. No scene, native API, PD or GPU is used.
    def oracle(n):
        obj = BatchedController.__new__(BatchedController)
        obj.num_envs, obj.device = n, torch.device('cpu')
        for name,value in dict(reference=reference,lower=lower,upper=upper,rate=rates,alpha=alpha,
                               action_low=low,action_high=high).items():
            setattr(obj,name,torch.tensor(value))
        obj.active = torch.tensor(active)
        obj.incremental_actions = torch.arange(12,33)
        obj.zero = torch.tensor(contract['initial']['zero_range_indices'])
        obj.target = torch.tensor(reference).expand(n,-1).clone()
        obj._foot_targets = lambda target:target
        return obj

    rng = np.random.default_rng(plan['seed'])
    single_z = rng.standard_normal((plan['one_tick_samples'],16)).astype(np.float32)
    path_z = rng.standard_normal((plan['trajectory_ticks'],plan['independent_trajectory_paths'],16)).astype(np.float32)
    sigma = np.float32(plan['latent_std'])
    single_a, path_a = np.tanh(single_z*sigma), np.tanh(path_z*sigma)
    arrays = dict(single_standard_normal=single_z,path_standard_normal=path_z,baseline_pad_points_W_m=baseline,
                  baseline_pad_centroid_W_m=centroid0,valid_pad_points=valid)
    results = dict(schema='exploration_conditioning_results.v1',plan=plan,groups={},
        controller_source_matches_original_baseline=True,production_codec_oracle_max_error_rad=0.,
        software_versions=dict(numpy=np.__version__,torch=torch.__version__,python=sys.version),
        geometry='target105 FK calibrated from prepared035 actual body/q; no predicted native actual motion')

    def distribution_geometry(values):
        mean=values.mean(0)
        return dict(centroid_mean_vector_mm=(mean*1000).tolist(),
            centroid_mean_offset_norm_mm=float(np.linalg.norm(mean)*1000),
            centroid_centered_rms_spread_mm=float(np.sqrt(((values-mean)**2).sum(-1).mean())*1000),
            centroid_total_rms_displacement_mm=float(np.sqrt((values**2).sum(-1).mean())*1000))

    def evaluate_targets(targets):
        centroids, rms, maximum = [], [], []
        for target in targets:
            q = reference.copy(); q[active] = target
            world = points(q)
            centers = np.stack([world[f,valid[f]].mean(0) for f in range(4)])
            distances2 = ((world-baseline)**2).sum(-1)
            centroids.append(centers-centroid0)
            rms.append([np.sqrt(distances2[f,valid[f]].mean()) for f in range(4)])
            maximum.append([np.sqrt(distances2[f,valid[f]].max()) for f in range(4)])
        return np.asarray(centroids),np.asarray(rms),np.asarray(maximum)

    for group,channels in (('arm12_only',np.arange(12)),('nonthumb16_only',np.arange(17,33))):
        action = np.zeros((len(single_a),39),dtype=np.float32);action[:,channels] = single_a[:,:len(channels)]
        initial = np.broadcast_to(ref,action.shape).copy()
        target,clamp = step(initial,action)
        actual = oracle(len(action)).targets(torch.tensor(action),None)[:,active].numpy()
        error = float(np.abs(actual-target).max()); assert error<2e-7,error
        results['production_codec_oracle_max_error_rad'] = max(results['production_codec_oracle_max_error_rad'],error)
        centers,rms,maximum = evaluate_targets(target)
        arrays[group+'_single_target39_rad'] = target
        arrays[group+'_single_centroid_delta_m'] = centers
        arrays[group+'_single_points_rms_m'] = rms
        single = dict(joint_delta_rms_deg=stats(np.rad2deg(np.sqrt(((target-initial)[:,channels]**2).mean(-1)))),
            joint_delta_l2_deg=stats(np.rad2deg(np.linalg.norm((target-initial)[:,channels],axis=-1))),
            per_finger={name:dict(**distribution_geometry(centers[:,f]),centroid_endpoint_mm=stats(np.linalg.norm(centers[:,f],axis=-1)*1000),
                points_rms_endpoint_mm=stats(rms[:,f]*1000),max_point_endpoint_mm=stats(maximum[:,f]*1000)) for f,name in enumerate(finger_names)})
        n = plan['independent_trajectory_paths'];old = np.broadcast_to(ref,(n,39)).copy(); obj=oracle(n)
        centers_path=[];rms_path=[];max_path=[];targets_path=[];clamps=[]
        for tick in range(plan['trajectory_ticks']):
            action = np.zeros((n,39),dtype=np.float32);action[:,channels] = path_a[tick,:,:len(channels)]
            old,clamp = step(old,action);actual = obj.targets(torch.tensor(action),None)[:,active].numpy()
            error = float(np.abs(actual-old).max()); assert error<2e-7,error
            results['production_codec_oracle_max_error_rad'] = max(results['production_codec_oracle_max_error_rad'],error)
            centers,rms,maximum = evaluate_targets(old)
            targets_path.append(old.copy());centers_path.append(centers);rms_path.append(rms);max_path.append(maximum);clamps.append(clamp[:,channels])
            if (tick+1)%60 == 0:print(group,'tick',tick+1,flush=True)
        c,r,m = np.asarray(centers_path),np.asarray(rms_path),np.asarray(max_path)
        all_targets = np.asarray(targets_path)
        arrays[group+'_path_target39_rad']=all_targets
        arrays[group+'_path_centroid_delta_m']=c
        arrays[group+'_path_points_rms_m']=r
        endpoints = {}
        norms = np.linalg.norm(c,axis=-1)
        lengths = np.linalg.norm(np.diff(np.concatenate((np.zeros_like(c[:1]),c),axis=0),axis=0),axis=-1)
        for endpoint in plan['reported_endpoints']:
            idx=endpoint-1;delta=all_targets[idx]-ref
            endpoints[str(endpoint)] = dict(
                joint_delta_rms_deg=stats(np.rad2deg(np.sqrt((delta[:,channels]**2).mean(-1)))),
                joint_delta_l2_deg=stats(np.rad2deg(np.linalg.norm(delta[:,channels],axis=-1))),
                clipped_axis_fraction_through_endpoint=float(np.asarray(clamps[:endpoint]).mean()),
                per_finger={name:dict(**distribution_geometry(c[idx,:,f]),centroid_endpoint_mm=stats(norms[idx,:,f]*1000),
                    points_rms_endpoint_mm=stats(r[idx,:,f]*1000),max_point_endpoint_mm=stats(m[idx,:,f]*1000),
                    centroid_max_excursion_mm=stats(norms[:endpoint,:,f].max(0)*1000),
                    centroid_target_path_length_mm=stats(lengths[:endpoint,:,f].sum(0)*1000)) for f,name in enumerate(finger_names)})
        results['groups'][group]=dict(channels=[ac['action_order'][i] for i in channels],one_tick=single,paths=endpoints)
    results['median_centroid_arm_over_nonthumb_ratios'] = {}
    for endpoint in ('one_tick','60','180'):
        def values(group):
            entry=results['groups'][group]
            return entry['one_tick'] if endpoint=='one_tick' else entry['paths'][endpoint]
        results['median_centroid_arm_over_nonthumb_ratios'][endpoint]={name:
            values('arm12_only')['per_finger'][name]['centroid_endpoint_mm']['median']/
            max(values('nonthumb16_only')['per_finger'][name]['centroid_endpoint_mm']['median'],1e-15) for name in finger_names}
    changed = [path for path,value in pins.items() if not Path(path).is_file() or sha(path)!=value]
    results.update(completed=not changed,changed_inputs=changed,wall_s=time.monotonic()-started)
    np.savez_compressed(BASE/'samples.npz',**arrays)
    (BASE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    (BASE/'inputs_after.json').write_text(json.dumps(dict(verified=not changed,changed_paths=changed,input_pins=pins),indent=2)+'\n')
    if changed:raise RuntimeError('Analysis inputs changed')
    print(json.dumps(dict(completed=True,wall_s=results['wall_s'],ratios=results['median_centroid_arm_over_nonthumb_ratios']),indent=2))


if __name__=='__main__':main()
