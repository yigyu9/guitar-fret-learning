"""Audit completed native artifacts without changing them or running physics."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path('/home/ajou/yigyu/3')
sys.path.insert(0, str(ROOT))
FOLDER = Path(__file__).resolve().parent
RESULT = FOLDER.parent


def read(path):
    return json.loads(path.read_text())


def main():
    import numpy as np
    import torch
    from guitar_learning.training.gpu_log_records import iter_gpu_transitions, iter_episode_rows, iter_learning_metrics
    from guitar_learning.training.training_log_io import iter_transitions
    from guitar_learning.song.task import make_task
    manifest = read(FOLDER/'source_manifest.json')
    assert all(hashlib.sha256(Path(r['path']).read_bytes()).hexdigest() == r['sha256'] for r in manifest)
    task = make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo', pre_roll_s=3., tail_s=.5)
    terms = {'song_left_approach', 'song_left_contact', 'song_clean_hold', 'song_left_success',
             'song_wrong_press', 'song_performance_deficit', 'song_finger_standby', 'song_thumb_support', 'action_change'}

    def same(a, b):
        if isinstance(a, torch.Tensor):
            return isinstance(b, torch.Tensor) and a.dtype == b.dtype and torch.equal(a, b)
        if isinstance(a, np.ndarray):
            return isinstance(b, np.ndarray) and a.dtype == b.dtype and np.array_equal(a, b)
        if isinstance(a, dict):
            return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
        if isinstance(a, (list, tuple)):
            return type(a) == type(b) and len(a) == len(b) and all(same(x,y) for x,y in zip(a,b))
        return a == b

    def episode_checks(e):
        assert set(e['reward_components']) == terms
        assert abs(sum(e['cost_components'].values())-e['cost']) < 1e-4
        assert e['cost_components']['running_physics'] == 0.
        failed = e['termination']['physical_failure'] or e['termination']['wrist_failure']
        assert e['cost_components']['termination_base'] == (5. if failed else 0.)
        remaining = max(0., e['finger_skill']['local_duration_s']-e['steps']/60.)
        assert abs(e['cost_components']['termination_remaining_time']-(2*remaining if failed else 0.)) < 1e-4
        ledger = e['left_note_ledger']
        assert len(ledger['target_ids']) == 67 and ledger['target_ids'] == [t.target_id for t in task.targets]
        selected = ledger['focus_mask']
        count = sum(selected)
        counts = Counter(t.finger for keep,t in zip(selected,task.targets) if keep)
        weights = [count/(len(counts)*counts[t.finger]) if keep else 0. for keep,t in zip(selected,task.targets)]
        paid, settled = ledger['values']['performance_paid'], ledger['values']['performance_settled']
        now = e['finger_skill']['source_task_time_s']
        budget = 0.
        for i,t in enumerate(task.targets):
            assert -1e-12 <= paid[i] <= .1*weights[i]+1e-8
            if not selected[i]:
                assert paid[i] == 0. and not settled[i]
            if settled[i]:
                assert selected[i] and now+1e-10 >= t.end_s
            if selected[i] and not settled[i]:
                budget += .15*weights[i]*max(0.,t.end_s-max(now,t.onset_s))/(t.end_s-t.onset_s)+max(0.,.1*weights[i]-paid[i])
        assert abs(e['cost_components']['termination_remaining_negative_note_budget']-(budget if failed else 0.)) < 1e-4
        assert e['finger_skill']['scope'] == ('full_song' if count == 67 else 'phrase')
        assert e['finger_skill_eval']['scope'] == e['finger_skill']['scope']
        assert 'weights' not in e['left_curriculum'] and 'progress' not in e['left_curriculum']

    runs = {}
    for name, updates, n in [('large1024',8,1024),('resume1024',1,1024),('large128',64,128)]:
        path = RESULT/name/'J'
        report = read(path/'report.json')
        assert report['completed'] and report['updates_in_run'] == updates
        assert report['transitions'] == updates*32*n
        assert report['lifecycle_verified'] and not report['changed_inputs'] and not report['missing_import_pins']
        assert report['gpu_scene']['closed'] and report['gpu_scene']['environment_count'] == n
        assert report['min_cuda_free_bytes'] >= 1024**3
        metrics = list(iter_learning_metrics(path, expand_episodes=True))
        assert len(metrics) == updates
        assert all(set(m['reward_component_means']) == terms for m in metrics)
        assert all(m['cost_weight'] == 1. for m in metrics)
        rows = list(iter_episode_rows(path))
        for row in rows:
            episode_checks(row['episode'])
        status = {}
        raw_count = raw_total = raw_cost_events = 0
        for row in iter_gpu_transitions(path, diagnostics=status):
            assert len(row['reward']) == len(row['cost']) == n
            assert all(math.isfinite(x) for x in row['reward']+row['cost'])
            for c,term in zip(row['cost'],row['terminated']):
                assert c >= 0. and (c == 0. or term)
                raw_cost_events += c > 0.
            raw_count += 1
            raw_total += n
        assert status['complete'] and raw_count == updates*32 and raw_total == report['transitions']
        decision_status = {}
        decision_count = 0
        decision_keys = set()
        for row in iter_transitions(path/'decisions.jsonl.gz',diagnostics=decision_status):
            assert row['planned_ticks'] == row['duration'] == 1
            assert row['end_control_tick']-row['start_control_tick'] == 1
            key = (row['update_index'],row['env_id'],row['start_control_tick'])
            assert key not in decision_keys
            decision_keys.add(key)
            decision_count += 1
        assert decision_status['complete'] and decision_count == raw_total
        init = torch.load(path/'initial.pt',map_location='cpu',weights_only=False)
        final = torch.load(path/'final.pt',map_location='cpu',weights_only=False)
        assert all(bool(torch.isfinite(v).all()) for v in final['model'].values())
        changes = {group:[k for k,v in final['model'].items() if k.startswith(group) and not torch.equal(v,init['model'][k])]
                   for group in ('support_', 'finger_')}
        assert all(changes.values())
        assert final['cost_weight'] == 1. and final['metadata']['schema'] == 'guitar_learning.finger_skill_resume.v2'
        scope = final['metadata']['exposure_transitions']
        assert sum(scope.values()) == final['metadata']['curriculum']['committed_transitions']
        runs[name] = dict(completed=True,updates=updates,transitions=raw_total,raw_rows=raw_count,
            decision_rows=decision_count,raw_crc_complete=True,decisions_crc_complete=True,
            episode_count=len(rows),reasons=dict(Counter(r['episode']['termination']['primary_reason'] for r in rows)),
            scopes=dict(Counter(r['episode']['finger_skill']['scope'] for r in rows)),
            cost_events=raw_cost_events,scope_exposure=scope,changed_parameters={k:len(v) for k,v in changes.items()},
            min_cuda_free_gib=report['min_cuda_free_bytes']/1024**3,wall_s=report['wall_s'],
            fixed_schedule=final['metadata']['curriculum']['config'])
    a = torch.load(RESULT/'large1024/J/final.pt',map_location='cpu',weights_only=False)
    b = torch.load(RESULT/'resume1024/J/initial.pt',map_location='cpu',weights_only=False)
    resume_fields = ('identity','model','actor_optimizer','value_optimizer','cost_weight','updates',
                     'torch_rng','numpy_rng','python_rng','cuda_rng')
    assert all(same(a[k],b[k]) for k in resume_fields)
    assert same(a['metadata']['curriculum'],b['metadata']['curriculum'])
    assert a['metadata']['settings']['finger_skill']['full_song_after'] == 65536
    assert runs['resume1024']['fixed_schedule'] == runs['large1024']['fixed_schedule']
    assert runs['resume1024']['scope_exposure']['full_song'] > runs['large1024']['scope_exposure']['full_song']
    ev = read(RESULT/'full_song_evaluation/report.json')
    assert ev['completed'] and ev['episodes'] == 16 and ev['failed_episodes_in_denominator']
    erows = list(iter_episode_rows(RESULT/'full_song_evaluation'))
    for row in erows:
        episode_checks(row['episode'])
        assert row['episode']['finger_skill']['selected_target_count'] == 67
    video = read(RESULT/'video/report.json')
    assert video['completed'] and video['checkpoint_sha256'] == ev['checkpoint_sha256']
    poses = np.load(RESULT/'video/poses_env0000.npz')
    assert all(np.isfinite(poses[k]).all() for k in poses)
    frames = len(poses['time_s'])
    assert np.array_equal(poses['control_tick'], np.arange(1,frames+1))
    assert np.array_equal(poses['physics_step'],4*np.arange(1,frames+1))
    assert poses['wrist_termination_state'].shape == (frames,4)
    assert np.all(poses['action'][:,33:] == 0.)
    assert np.any(poses['action'][:,:17] != 0.) and np.any(poses['action'][:,17:33] != 0.)
    metadata = read(RESULT/'video/capture_metadata.json')
    assert metadata['no_reset_frames'] and metadata['training_updates'] == 0
    assert len(metadata['termination_observation']['fields']) == 4
    assert np.allclose(poses['wrist_termination_state'][:,2], np.maximum(3.-poses['time_s'],0)/3., atol=1e-6)
    from guitar_learning.core.control import ACTIVE_NAMES
    groups = dict(arm=ACTIVE_NAMES[:12],thumb=ACTIVE_NAMES[12:17],fingers=ACTIVE_NAMES[17:33])
    angles = {}
    for group,names in groups.items():
        indices = [metadata['joint_names'].index(name) for name in names]
        spans = np.ptp(poses['q'][:,indices],axis=0)*180/np.pi
        angles[group] = dict(mean_joint_excursion_deg=float(spans.mean()),max_joint_excursion_deg=float(spans.max()))
    paths = np.array([r['episode']['finger_skill_diagnostics']['motion']['path_m'] for r in erows])
    motion = erows[0]['episode']['finger_skill_diagnostics']['motion']
    media = {}
    for name in ('hand','fullbody'):
        video_path = RESULT/'video'/(name+'.mp4')
        ff = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=width,height,avg_frame_rate,duration,nb_frames','-of','json',str(video_path)]))['streams'][0]
        assert int(ff['nb_frames']) == frames//2 and ff['avg_frame_rate'] == '30/1'
        media[name] = ff
        subprocess.run(['ffmpeg','-loglevel','error','-n','-ss',str(min(2.,frames/120)),
            '-i',str(video_path),'-frames:v','1',str(FOLDER/(name+'_preview.png'))],check=True)
    cpu = read(FOLDER/'cpu_checks.json')
    report = dict(completed=True,source_files=len(manifest),source_unchanged=True,
        cpu_modules=len(cpu),cpu_tests=sum(int(re.search(r'Ran (\d+) test',r['output']).group(1)) for r in cpu),
        runs=runs,strict_resume_exact_fields=list(resume_fields)+['curriculum'],
        shadow='shadow/report.json',evaluation=dict(summary=ev['summary'],episodes=16,targets_each=67),
        video=dict(control_endpoints=frames,consecutive_physics_steps=True,all_arrays_finite=True,
            timer_shape=list(poses['wrist_termination_state'].shape),inactive_right_zero=True,media=media,
            env0_success=video['episode']['song']['left_success_count'],
            endpoint_excursion=angles,
            mean_absolute_action_support=float(np.abs(poses['action'][:,:17]).mean()),
            mean_absolute_action_fingers=float(np.abs(poses['action'][:,17:33]).mean())),
        material_point_motion=dict(phases=motion['phases'],components=motion['components'],
            mean_path_mm=(1000*paths.mean(axis=0)).tolist(),units='millimetres per episode, mean across16 fixed full-song first episodes',
            limitation='60Hz endpoints; same128 source material points. Component norm paths are not additive or causal force shares.'),
        limits=['short validation; not convergence/naturalness evidence','geometric contact candidates, not calibrated pressure or acoustic result'])
    (RESULT/'verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
