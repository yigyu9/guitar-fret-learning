"""Complete read-only artifact review using independent training-data checks."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path('/home/ajou/yigyu/3')
sys.path.insert(0,str(ROOT))
RESULT=Path(__file__).resolve().parent.parent


def main():
    import numpy as np
    import torch
    from guitar_learning.training.gpu_log_records import iter_episode_rows
    from guitar_learning.song.task import make_task
    from guitar_learning.gpu.geometry import apply,conjugate
    from guitar_learning.gpu.wrist_region import load_wrist_region_track,measure_wrist_region
    torch.set_num_threads(1)
    read=lambda p:json.loads(p.read_text())
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    data=read(RESULT/'support/native_review_data.json')
    assert data['completed'] and set(data['runs'])=={'large1024','resume1024','large128'}
    task=make_task(ROOT/'data/song_bundles/05_BN2-131-B_solo',pre_roll_s=3.,tail_s=.5)
    expected_terms={'song_left_approach','song_left_contact','song_clean_hold','song_left_success','song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change'}
    def episode(e):
        assert e['song']['denominator']==e['song']['target_count']==e['finger_skill']['selected_target_count']==67
        assert e['finger_skill']['scope']=='full_song' and e['finger_skill_eval']['scope']=='full_song'
        assert set(e['reward_components'])==expected_terms
        assert abs(sum(e['reward_components'].values())-e['reward'])<1e-4
        ledger=e['left_note_ledger'];v=ledger['values'];assert all(ledger['focus_mask']) and len(ledger['focus_mask'])==67
        assert ledger['target_ids']==[t.target_id for t in task.targets]
        assert sum(x['target_count'] for x in e['left_curriculum']['finger_metrics'])==67
        now=e['finger_skill']['source_task_time_s'];counts=Counter(t.finger for t in task.targets);budget=0.
        for i,t in enumerate(task.targets):
            w=67/(len(counts)*counts[t.finger]);missing=min(1.,max(0.,v['missing'][i]/(t.end_s-t.onset_s)))
            ending=now+1e-10>=t.end_s
            assert bool(v['performance_settled'][i])==ending
            deficit=max(0.,1-v['best_clean_streak'][i]/ledger['required_clean_s'][i])
            expected=.1*w*(max(missing,deficit) if ending else missing)
            assert abs(v['performance_paid'][i]-expected)<1e-6
            if not ending:budget+=.15*w*max(0.,t.end_s-max(now,t.onset_s))/(t.end_s-t.onset_s)+max(0.,.1*w-v['performance_paid'][i])
        assert abs(e['reward_components']['song_performance_deficit']+sum(v['performance_paid']))<1e-5
        failed=e['termination']['physical_failure'] or e['termination']['wrist_failure']
        cost=5+2*max(0.,e['finger_skill']['local_duration_s']-e['steps']/60.)+budget if failed else 0.
        assert abs(cost-e['cost'])<1e-4 and abs(sum(e['cost_components'].values())-e['cost'])<1e-4
        assert e['cost_components']['running_physics']==0.
    evaluation=read(RESULT/'full_song_evaluation/report.json')
    rows=list(iter_episode_rows(RESULT/'full_song_evaluation'))
    assert evaluation['completed'] and evaluation['episodes']==len(rows)==16 and evaluation['failed_episodes_in_denominator']
    assert {r['episode']['env_id'] for r in rows}==set(range(16))
    assert [r['episode_id'] for r in rows]==list(range(16))
    assert evaluation['first_episode_per_env_per_batch'] and evaluation['batches']==1
    for r in rows:episode(r['episode'])
    assert sum(r['episode']['steps'] for r in rows)==evaluation['selected_episode_transitions']
    summary=Counter(r['episode']['termination']['primary_reason'] for r in rows)
    target=RESULT/'large128/J/final.pt';checkpoint_sha=digest(target)
    assert checkpoint_sha==evaluation['checkpoint_sha256']
    video=read(RESULT/'video/report.json');meta=read(RESULT/'video/capture_metadata.json');contract=read(RESULT/'video/training_contract.json')
    assert video['completed'] and video['checkpoint_sha256']==meta['checkpoint_sha256']==checkpoint_sha
    assert video['policy_unchanged'] and video['training_updates']==meta['training_updates']==0
    assert video['first_episode_only'] and meta['environment']==0 and meta['no_reset_frames']
    assert video['source_pins_unchanged'] and video['source_checkpoint_pins_validated'] and video['lifecycle_verified'] and not video['cleanup_errors']
    assert video['encoding_exit_codes']==dict(hand=0,fullbody=0)
    episode(video['episode'])
    poses=np.load(RESULT/'video/poses_env0000.npz')
    for k in poses:assert np.isfinite(poses[k]).all()
    length=len(poses['time_s']);assert length==video['episode']['steps']
    assert np.array_equal(poses['control_tick'],np.arange(1,length+1))
    assert np.array_equal(poses['physics_step'],4*np.arange(1,length+1))
    assert np.allclose(poses['time_s'],np.arange(1,length+1)/60.,atol=1e-12,rtol=0)
    assert poses['wrist_termination_state'].shape==(length,4)
    assert np.all(poses['action'][:,33:]==0.) and np.any(poses['action'][:,:17]!=0.) and np.any(poses['action'][:,17:33]!=0.)
    end=video['episode']['wrist_termination'];timers=poses['wrist_termination_state'];seconds=poses['time_s']
    assert np.allclose(timers[:,2],np.maximum(0.,3-seconds)/3,atol=1e-7,rtol=0)
    assert np.all(timers[seconds<3,0:2]==0.)
    assert np.all(np.isin(timers[:,0],[0.,1.])) and np.all(timers[:,1:]>=0.)
    assert np.allclose(timers[:,1]*180,np.round(timers[:,1]*180),atol=2e-5,rtol=0)
    assert np.allclose(timers[:,3]*24,np.round(timers[:,3]*24),atol=2e-5,rtol=0)
    assert abs(timers[-1,1]*.75-end['elapsed_s'])<1e-7 and abs(timers[-1,3]*.1-end['severe_elapsed_s'])<1e-7
    bodies=torch.from_numpy(poses['body_state']);names=meta['body_names']
    wrist=bodies[:,names.index('human/L_Wrist'),:3];guitar=bodies[:,names.index('guitar/guitar')]
    wrist_local=apply(conjugate(guitar[:,3:7]),wrist-guitar[:,:3])
    track=load_wrist_region_track(ROOT/'data/song_bundles/05_BN2-131-B_solo',contract['observation']['surface_geometry']['press_surface'])
    timestamp=torch.from_numpy(np.maximum(3.,seconds)-3.)
    measured=measure_wrist_region(wrist_local,timestamp,torch.tensor(track['times_s'],dtype=torch.float64),torch.tensor(track['lower_G_m'],dtype=torch.float32),torch.tensor(track['upper_G_m'],dtype=torch.float32))
    excess=measured['delta'].abs().amax(-1).numpy();active=timers[:,0]>0
    assert np.all(active[(seconds>=3)&(excess>.030001)])
    assert not np.any(active[excess<.019999])
    assert not np.any(timers[excess<.099999,3])
    for name in ('hand','fullbody'):
        stream=read_json_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,avg_frame_rate,duration,nb_frames','-of','json',str(RESULT/'video'/(name+'.mp4'))])['streams'][0]
        assert stream['width']==1280 and stream['height']==720 and stream['avg_frame_rate']=='30/1' and int(stream['nb_frames'])==length//2
        assert abs(float(stream['duration'])-(length//2)/30.)<1e-6
    assert np.allclose(meta['frame_times_s'],np.arange(2,length+1,2)/60.,rtol=0,atol=1e-12)
    assert video['frames']==meta['frames']==length//2
    initial_eval=next(r['episode'] for r in rows if r['episode']['env_id']==0)
    assert initial_eval['steps']==video['episode']['steps'] and initial_eval['termination']==video['episode']['termination'] and initial_eval['song']['left_success_count']==video['episode']['song']['left_success_count']
    assert initial_eval['left_note_ledger']['values']==video['episode']['left_note_ledger']['values']
    for r in read(RESULT/'support/source_manifest.json'):assert digest(Path(r['path']))==r['sha256']
    for entry in map(json.loads,(target.parent/'checkpoint_manifest.jsonl').read_text().splitlines()):
        if entry['path']=='final.pt':assert entry['sha256']==checkpoint_sha
    data.update(verdict='문제없음',critical=[],warning=[],evaluation=dict(episodes=16,first_episode_each_environment=True,fixed_target_denominator=67,selected_control_transitions=evaluation['selected_episode_transitions'],actual_simulated_transitions=evaluation['actual_simulated_transitions'],reasons=dict(summary),mean_achieved=evaluation['summary']['mean_left_success_count'],reward_and_terminal_budget_verified=True),video=dict(checkpoint_sha256=checkpoint_sha,actual_native_pixels=True,first_environment_first_episode=True,control_endpoints=length,frames=length//2,fps=30,width=1280,height=720,physics_steps_exact_and_consecutive=True,first_episode_no_reset_frames=True,all_arrays_finite=True,timer_state_matches_raw_wrist_geometry_and_terminal_ledger=True,source_checkpoint_unchanged=True,policy_no_training_code_and_native_unchanged_audit=True,evaluation_env0_ledger_exact=True,visual_layout_review='root agent responsibility'),limitations=['Functional/native integration passed; this is not a long-training convergence or naturalness validation.','All16 full-song first episodes terminated on wrist and achieved0/67: short-model musical performance did not pass.','Continuous wrist timing is240Hz internally; independent captured geometry checks are60Hz endpoints.'])
    (RESULT/'support/native_review.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(data,ensure_ascii=False,indent=2))


def read_json_output(command):return json.loads(subprocess.check_output(command))

if __name__=='__main__':main()
