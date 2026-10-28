"""Compare completed index controls; historical source verified against preserved copies."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIX = HERE.parent
DIAG = FIX.parents[1]
ROOT = DIAG.parents[2]
ARCHIVE = ROOT/'guitar_learning/archive/20261027_before_wrist_position_jacobian_v2'
CASES = dict(original=DIAG/'03_short_learning/other_finger_precheck_v3',
             low_gain=DIAG/'05_verified_fixes/index_wrist_gain_probe',
             qpos_v2=FIX/'native_precheck')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment

    output = HERE/'results_v1'
    if output.exists() or output.is_symlink():
        raise ValueError('Existing output is preserved')
    torch.set_num_threads(1)
    manifest = read(ARCHIVE/'manifest.json')
    archived = {str(ROOT/r['path']): r for r in manifest['files']}
    hashes, source_checks, measurements, summaries, curves = {}, {}, {}, [], {}

    def remember(path):
        hashes[str(path)] = sha(path)

    def verify_source(path, expected, historical):
        key = (path, expected)
        if key in source_checks:
            return
        source = Path(path)
        if sha(source) == expected:
            source_checks[key] = dict(path=path, sha256=expected, verified_at=path)
        elif historical and path in archived and archived[path]['sha256'] == expected:
            copy = ARCHIVE/archived[path]['path']
            assert sha(copy) == expected
            source_checks[key] = dict(path=path, sha256=expected, verified_at=str(copy))
        else:
            raise ValueError('Source is neither unchanged nor preserved: '+path)

    def stats(a):
        return dict(min=np.min(a, axis=0).tolist(), median=np.median(a, axis=0).tolist(),
                    max=np.max(a, axis=0).tolist())

    metadata, _ = fixture(1)
    baseline_settings = None
    for label, base in CASES.items():
        assert read(base/'01_launcher.json')['returncode'] == 0
        assert read(base/'runs/report.json')['completed']
        remember(base/'01_launcher.json'); remember(base/'runs/report.json')
        measurements[label] = {}
        for control in ('reference', 'zero', 'random'):
            folder = base/'runs'/('index_'+control)
            before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json')
            report, scene = read(folder/'report.json'), read(folder/'gpu_scene_final.json')
            assert before == after['input_pins'] and after['verified']
            assert report['completed'] and report['closed'] and report['failure'] is None and scene['closed']
            for path, expected in before.items():
                verify_source(path, expected, label != 'qpos_v2')
            evaluation, settings, meta = [read(folder/n) for n in ('evaluation.json','settings.json','trace_metadata.json')]
            if baseline_settings is None:
                baseline_settings = copy.deepcopy(settings)
            normalized = copy.deepcopy(settings)
            normalized['song']['short_learning']['wrist_control'] = baseline_settings['song']['short_learning']['wrist_control']
            assert normalized == baseline_settings
            if label != 'low_gain':
                assert settings['song']['short_learning']['wrist_control']['correction_step_rad'] == np.deg2rad(.5)
            assert not evaluation['policy_performance'] and evaluation['condition'] == control
            episodes = evaluation['episodes']
            assert evaluation['assigned_quotas'] == [1]*4 and sorted(e['env_id'] for e in episodes) == list(range(4))
            assert len(episodes) == 4
            row = dict(case=label, control=control, achieved=sum(bool(e['achieved']) for e in episodes), attempts=4,
                clean=sum(e['clean_fraction'] for e in episodes)/4,
                wrong=sum(e['audible_wrong_fraction'] for e in episodes)/4,
                physical_failures=sum(bool(e['termination']['physical_failure']) for e in episodes),
                wrist_failures=sum(bool(e['termination']['wrist_failure']) for e in episodes))
            assert abs(evaluation['summary']['achieved_fraction']-row['achieved']/4) < 1e-12
            assert abs(evaluation['summary']['mean_clean_fraction']-row['clean']) < 1e-12
            assert abs(evaluation['summary']['mean_audible_wrong_fraction']-row['wrong']) < 1e-12
            summaries.append(row)
            trace = np.load(folder/'trace_env0_episode0.npz')
            spec = settings['song']['short_learning']; view = spec['view']
            assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
            guitar, wrist, distal, thumb = [meta['body_names'].index(n) for n in
                ('guitar/guitar','human/L_Wrist','human/LH:index3','human/LH:thumb3')]
            gr = Rotation.from_quat(trace['body_state'][:, guitar, 3:7])
            wrist_G = gr.inv().apply(trace['body_state'][:, wrist, :3]-trace['body_state'][:, guitar, :3])
            wrist_R = gr.inv()*Rotation.from_quat(trace['body_state'][:, wrist, 3:7])
            arm = [meta['joint_names'].index(n) for n in read(folder/'training_contract.json')['action']['names'][:12]]
            selected = [meta['joint_names'].index(n) for n in spec['learned_action_names']]
            data = dict(position_mm=np.linalg.norm(trace['wrist_goal_G_m']-wrist_G,axis=1)*1000,
                rotation_deg=np.rad2deg((Rotation.from_quat(trace['wrist_goal_G_xyzw']).inv()*wrist_R).magnitude()),
                arm_target_actual_max_deg=np.rad2deg(abs(trace['target'][:,arm]-trace['q'][:,arm])).max(1),
                arm_request_target_max_deg=np.rad2deg(abs(trace['wrist_requested_arm_rad']-trace['target'][:,arm])).max(1),
                arm_request_actual_max_deg=np.rad2deg(abs(trace['wrist_requested_arm_rad']-trace['q'][:,arm])).max(1),
                selected_target_actual_deg=np.rad2deg(trace['target'][:,selected]-trace['q'][:,selected]),
                pad_distance_mm=trace['surface_distance_m']*1000,
                distal_resultant_N=np.linalg.norm(trace['net_body_force_n'][:,distal],axis=1),
                thumb_resultant_N=np.linalg.norm(trace['net_body_force_n'][:,thumb],axis=1))
            env = ShortEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],
                skill=settings['finger_skill'],device='cpu')
            def snapshot(i):
                return dict(q=torch.tensor(trace['q'][i:i+1]),qd=torch.zeros(1,105),
                    target=torch.tensor(trace['target'][i:i+1]),body_state=torch.tensor(trace['body_state'][i:i+1]),
                    contact_force=torch.tensor(trace['net_body_force_n'][i:i+1]))
            env.reset([0],snapshot(0)); j = env.selected_index
            gates = []
            for i, now in enumerate(trace['time_s']):
                env.clock[0] = round(now*240); env._snapshot(snapshot(i))
                assert bool(env.candidate[0,j]) == bool(trace['candidate'][i])
                assert bool(env.wrong[0,j]) == bool(trace['wrong'][i])
                assert abs(float(env.surface_distance[0,j])-trace['surface_distance_m'][i]) < 1e-6
                gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,
                    env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
            phases = dict(audible=(trace['time_s'] >= view['local_onset_s']-1e-9) &
                (trace['time_s'] <= view['local_end_s']+1e-9),post_ramp=trace['time_s'] >= 2-1e-9)
            measurements[label][control] = dict(selected_names=spec['learned_action_names'],
                phases={p:dict(endpoints=int(mask.sum()),values={k:stats(v[mask]) for k,v in data.items()},
                    gate_counts=dict(zip(('loaded','position','position_facing','positive','candidate','wrong'),
                    np.array(gates)[mask].sum(0).tolist()))) for p,mask in phases.items()})
            if control == 'reference': curves[label] = dict(time=trace['time_s'],**data)
            for n in ('inputs_before.json','inputs_after.json','report.json','gpu_scene_final.json','settings.json',
                      'training_contract.json','evaluation.json','trace_metadata.json','trace_env0_episode0.npz'):
                remember(folder/n)
    assert not torch.cuda.is_initialized()
    output.mkdir()
    (output/'comparison.json').write_text(json.dumps(dict(summary=summaries,env0=measurements,
        scope='9 controls,36 assigned first attempts; scripted/zero/random only. Trace/gates/forces env0 60Hz only; no learned-policy or contact-pair force claim.'),indent=2)+'\n')
    (output/'verification.json').write_text(json.dumps(dict(CPU_only=True,input_sha256=hashes,
        source_verification=list(source_checks.values()),historical_source_archive=str(ARCHIVE/'manifest.json'),
        historical_strict_reload_claimed=False),indent=2)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2,2,figsize=(12,7),sharex=True)
    for axis, key, title in zip(axes.flat,('position_mm','rotation_deg','pad_distance_mm','distal_resultant_N'),
            ('Wrist position error (mm)','Wrist rotation error (deg)','Nearest pad distance (mm)','Index distal resultant (N)')):
        for label, data in curves.items(): axis.plot(data['time'],data[key],label=label)
        axis.set_title(title); axis.axvline(3,color='gray',linestyle=':'); axis.grid(alpha=.2)
    axes[0,0].legend(); axes[1,0].set_xlabel('Local time (s)'); axes[1,1].set_xlabel('Local time (s)')
    fig.suptitle('Scripted index reference, env0 first attempt, 60Hz endpoints'); fig.tight_layout()
    fig.savefig(output/'comparison.png',dpi=160); plt.close(fig)
    print(json.dumps(summaries,indent=2))


if __name__ == '__main__':
    main()
