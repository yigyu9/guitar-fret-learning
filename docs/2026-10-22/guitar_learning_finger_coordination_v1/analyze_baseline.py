"""CPU-only audit of sealed 60 Hz captures; no policy/native imports or replay."""
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation

ROOT = Path('/home/ajou/yigyu/3')
OLD = ROOT/'docs/2026-10-22/guitar_learning_long_training_v4'
OUT = Path(__file__).resolve().parent
FINGERS = ('index', 'middle', 'ring', 'pinky')
SUFFIXES = ('1_x', '1_z', '2', '3')
DEG = 180/np.pi


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def stats(values):
    x = np.asarray(values, dtype=np.float64)
    if not x.size:
        return None
    assert np.isfinite(x).all()
    return dict(n=int(x.size), mean=float(x.mean()), min=float(x.min()),
                p05=float(np.percentile(x, 5)), median=float(np.median(x)),
                p95=float(np.percentile(x, 95)), max=float(x.max()))


def angle(u, v):
    return np.arccos(np.clip((u*v).sum(-1)/(
        np.linalg.norm(u, axis=-1)*np.linalg.norm(v, axis=-1)), -1, 1))*DEG


def main():
    pins = {}
    seal = json.loads((OLD/'result_manifest.json').read_text())
    pins[str(OLD/'result_manifest.json')] = sha(OLD/'result_manifest.json')

    def sealed(relative):
        path = OLD/relative
        actual = sha(path)
        assert actual == seal['files'][relative]['sha256'], relative
        pins[str(path)] = actual
        return path

    def read(relative):
        return json.loads(sealed(relative).read_text())

    contract = read('train2000/training_contract.json')['action']['target_contract']
    targets = read('evaluation_final_1024/targets.json')
    sealed('source_training/guitar_learning/gpu/finger_reward.py')
    inputs = read('evaluation_final_1024/inputs_before.json')
    xml = ROOT/'guitar_learning/assets/tab2body/assets/smpl_mpl_hands_body.xml'
    assert sha(xml) == inputs[str(xml)]
    pins[str(xml)] = sha(xml)
    asset = ET.parse(xml)
    joint_xml = {j.get('name'): j for j in asset.iter('joint') if j.get('name')}
    axes = {}
    for f in FINGERS:
        for suffix in SUFFIXES:
            name = 'LH:'+f+suffix
            elem = joint_xml[name]
            axes[name] = dict(axis=[float(v) for v in elem.get('axis').split()],
                              asset_range_deg=[float(v) for v in elem.get('range').split()])
        # All segment offsets point along -y, no authored rest rotations.
        for part in ('1', '2', '3'):
            b = asset.find(".//body[@name='LH:%s%s']" % (f, part))
            assert not any(b.get(k) for k in ('quat', 'euler', 'axisangle'))
        for part in ('2', '3', '_top'):
            b = asset.find(".//body[@name='LH:%s%s']" % (f, part))
            offset = np.array([float(v) for v in b.get('pos').split()])
            assert offset[1] < 0 and abs(offset[0])+abs(offset[2]) < 1e-12
    onset = np.array([t['onset_s'] for t in targets])
    end = np.array([t['end_s'] for t in targets])
    press = np.array([t['press_s'] for t in targets])
    assignment = np.array([t['finger'] for t in targets])
    result = dict(schema='guitar_learning.finger_coordination_baseline.v1',
                  scope='Stored deterministic fixed-policy 60Hz endpoints only; no native/GL/PPO execution',
                  source_phase=str(OLD), axes=axes,
                  role_definition='Action interval start k-1/60: audible onset<=t<end wins; else preparation press-2<=t<end; else no_selected_target. Earliest end/onset and original-order ties. This is a score/reward role, not actual contact.',
                  outward_action_definition='Endpoint target within 2deg of native lower/upper plus action pointing outward (magnitude>1e-5). Not previous-target exact-bound outward, actual clamp occurrence, or a 240Hz event.',
                  endpoint_definition='t0 excluded from statistics; frame k action applied over preceding four physics steps; q and target are endpoint values. Post10 means endpoint time>=10s. No 240Hz extrema.',
                  thresholds=dict(limit_proximity_deg=2, straight_middle_below_deg=10,
                                  bent_distal_above_deg=60, base_opposite_reference_below_deg=0),
                  captures={})
    for tag, envs in (('final', range(8)), ('update_1500', (0,))):
        directory = 'evaluation_final_1024' if tag == 'final' else 'evaluation_update_1500_1024'
        meta = read(directory+'/capture_metadata.json')
        report = read(directory+'/report.json')
        assert report['completed'] and report['gpu_scene']['closed']
        assert meta['source_optimizer_updates'] == (2000 if tag == 'final' else 1500)
        rows = {}
        for env_id in envs:
            entry = next(e for e in meta['captures'] if e['env_id'] == env_id)
            path = sealed(directory+'/'+entry['path'])
            assert sha(path) == entry['sha256']
            d = np.load(path, allow_pickle=False)
            assert np.all(np.diff(d['clock']) == 4)
            n = len(d['clock'])-1
            q, target, action = (d[k].astype(np.float64) for k in ('q', 'target', 'action'))
            bodies = d['body_state'].astype(np.float64)
            assert all(np.isfinite(d[k]).all() for k in d.files)
            endpoint_time = d['clock'][1:]/240.
            start_time = d['clock'][:-1]/240.
            finger_rows = {}
            for fi, f in enumerate(FINGERS, 1):
                audible = (assignment == fi)[None] & (onset[None] <= start_time[:, None]) & (start_time[:, None] < end[None])
                preparing = (assignment == fi)[None] & (press[None]-2 <= start_time[:, None]) & (start_time[:, None] < end[None])
                selected = np.where(audible.any(1), np.where(audible, end, np.inf).argmin(1),
                                    np.where(preparing, onset, np.inf).argmin(1))
                role = np.where(audible.any(1), 2, np.where(preparing.any(1), 1, 0))
                selected[role == 0] = -1
                masks = dict(all=np.ones(n, bool), post10=endpoint_time >= 10,
                             audible=role == 2, preparation=role == 1, no_selected_target=role == 0)
                qr = {}; joint_indices = []
                for suffix in SUFFIXES:
                    name = 'LH:'+f+suffix
                    j = meta['joint_names'].index(name)
                    a = contract['action_order'].index(name)
                    joint_indices.append(j)
                    lo, hi = contract['action_lower_rad'][a], contract['action_upper_rad'][a]
                    assert np.allclose(np.array(axes[name]['asset_range_deg'])/DEG, [lo, hi], atol=1e-6)
                    v, t, act = q[1:, j], target[1:, j], action[1:, a]
                    dv = np.diff(q[:, j])*60
                    reversal = (act[:-1]*act[1:] < 0) & (np.abs(act[:-1]) > 1e-5) & (np.abs(act[1:]) > 1e-5)
                    fields = {}
                    for name_role, mask in masks.items():
                        fields[name_role] = dict(q_deg=stats(v[mask]*DEG), target_deg=stats(t[mask]*DEG),
                            action=stats(act[mask]), mean_abs_action=float(np.abs(act[mask]).mean()) if mask.any() else None,
                            q_speed_deg_s=stats(dv[mask]*DEG), native_endpoint_qd_deg_s=stats(d['qd'][1:,j][mask]*DEG), target_speed_deg_s=stats(np.diff(target[:, j])[mask]*60*DEG),
                            q_target_rms_deg=float(np.sqrt(np.mean((v[mask]-t[mask])**2))*DEG) if mask.any() else None,
                            q_lower_2deg_fraction=float((v[mask] <= lo+2/DEG).mean()) if mask.any() else None,
                            q_upper_2deg_fraction=float((v[mask] >= hi-2/DEG).mean()) if mask.any() else None,
                            target_lower_2deg_fraction=float((t[mask] <= lo+2/DEG).mean()) if mask.any() else None,
                            target_upper_2deg_fraction=float((t[mask] >= hi-2/DEG).mean()) if mask.any() else None,
                            target_within2deg_outward_action_fraction=float(((((t<=lo+2/DEG)&(act < -1e-5))|((t>=hi-2/DEG)&(act > 1e-5)))[mask]).mean()) if mask.any() else None)
                    qr[suffix] = dict(native_bounds_deg=[lo*DEG, hi*DEG], initial_q_deg=q[0,j]*DEG,
                        initial_target_deg=target[0,j]*DEG, final_q_deg=q[-1,j]*DEG, final_target_deg=target[-1,j]*DEG,
                        action_positive_fraction=float((act > 1e-5).mean()), action_negative_fraction=float((act < -1e-5).mean()),
                        adjacent_sign_reversals=int(reversal.sum()), by_role=fields)
                points = [bodies[:, meta['body_names'].index('human/LH:'+f+s), :3] for s in ('1','2','3','_top')]
                proximal, middle, distal = [b-a for a,b in zip(points[:-1],points[1:])]
                pip, dip = angle(proximal, middle), angle(middle, distal)
                palm = Rotation.from_quat(bodies[:,meta['body_names'].index('human/LH:palm'),3:7])
                local_prox = palm.inv().apply(proximal)
                signed_base = np.arctan2(-local_prox[:,2], -local_prox[:,1])*DEG
                base_rotation = palm.inv()*Rotation.from_quat(bodies[:,meta['body_names'].index('human/LH:'+f+'1'),3:7])
                base_rotvec = base_rotation.as_rotvec()*DEG
                base_deflection = angle(local_prox, np.broadcast_to([0.,-1.,0.], local_prox.shape))
                baseq, _, midq, endq = (q[1:,j]*DEG for j in joint_indices)
                shape = {}
                for name_role, mask in masks.items():
                    shape[name_role] = dict(n=int(mask.sum()),
                        middle_below10_distal_above60_fraction=float(((midq[mask]<10)&(endq[mask]>60)).mean()) if mask.any() else None,
                        base_negative_middle_below10_distal_above60_fraction=float(((baseq[mask]<0)&(midq[mask]<10)&(endq[mask]>60)).mean()) if mask.any() else None,
                        actual_bone_pip_bend_deg=stats(pip[1:][mask]), actual_bone_dip_bend_deg=stats(dip[1:][mask]),
                        actual_palm_frame_base_signed_bend_deg=stats(signed_base[1:][mask]),
                        actual_palm_frame_base_total_deflection_deg=stats(base_deflection[1:][mask]),
                        actual_palm_relative_so3_rotvec_deg={a:stats(base_rotvec[1:,i][mask]) for i,a in enumerate('xyz')} )
                finger_rows[f] = dict(role_ticks={k:int(v.sum()) for k,v in masks.items()},
                    role_selected_target_indices={k:sorted(set(selected[v].tolist())-{-1}) for k,v in masks.items() if k in ('audible','preparation')},
                    joints=qr, shape=shape, initial_bone_angles_deg=dict(pip=float(pip[0]),dip=float(dip[0]),base_signed=float(signed_base[0]),base_total_deflection=float(base_deflection[0]),
                    palm_relative_so3_rotvec_deg=base_rotvec[0].tolist()),
                    bone_angle_abs_q_difference_max_deg=dict(pip=float(np.max(np.abs(pip-np.abs(q[:,joint_indices[2]]*DEG)))),dip=float(np.max(np.abs(dip-np.abs(q[:,joint_indices[3]]*DEG))))))
            rows[str(env_id)] = dict(endpoint_ticks=n, duration_s=float(endpoint_time[-1]), full_safe=entry['full_safe'],
                achieved_notes=int(d['left_count'][-1]), fingers=finger_rows)
        result['captures'][tag] = rows
    assert all(sha(Path(p)) == h for p,h in pins.items())
    result['inputs_sha256'] = pins
    result['analysis_script_sha256'] = sha(Path(__file__))
    (OUT/'analysis_baseline.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,indent=2)+'\n')
    for env_id, row in result['captures']['final'].items():
        print('env',env_id,'notes',row['achieved_notes'])
        if env_id != '0': continue
        for f,fr in row['fingers'].items():
            print(f,'roles',fr['role_ticks'],'shape',fr['shape']['post10']['middle_below10_distal_above60_fraction'])
            for s,j in fr['joints'].items():
                a=j['by_role']['post10']; print(s,'q0/final/mean',round(j['initial_q_deg'],2),round(j['final_q_deg'],2),round(a['q_deg']['mean'],2),'tmean',round(a['target_deg']['mean'],2),'a',round(a['action']['mean'],5),'lo/hi',round(a['q_lower_2deg_fraction'],3),round(a['q_upper_2deg_fraction'],3))


if __name__ == '__main__':
    main()
