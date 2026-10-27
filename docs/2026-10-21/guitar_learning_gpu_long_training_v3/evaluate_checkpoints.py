"""Paired deterministic prepared-pose checks after the long run, no PPO updates.

Use the training batch size of1024, retaining the first ended episode per env.
These instances are not independent seeds or held-out-song generalization.
Each saved curriculum also changes observations; compare whole checkpoint
states and geometric metrics, not changing rewards or calibrated pressure/sound.
First-episode per-note ledgers are newly captured before evaluation resets;
they do not reconstruct missing per-note training histories.
"""
import copy
import faulthandler
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback
faulthandler.enable(all_threads=True)
import isaacgym
import torch
from guitar_learning.training.gpu_pool import GpuPool,FIELDS
from guitar_learning.skills.specialist_policy import SpecialistPolicy
from guitar_learning.training.ppo import PPOTrainer,PPOConfig
from guitar_learning.song.curriculum_runtime import CurriculumCoordinator

torch.set_num_threads(1)
torch.backends.cuda.matmul.allow_tf32=False
NUM_ENVS=1024
NOTE_FIELDS=('left','left_missed','ever','released','reach_done','contact_done',
             'clean','wrong','missing','held','dwell','release_s','reached','contact_time')
p=Path(__file__).resolve().parent
run=p/'train1024_large_2000'
r=json.loads((run/'report.json').read_text())
assert r['completed'] and r['optimizer_updates']==2000 and r['transitions']==65_536_000
settings=json.loads((run/'settings.json').read_text())
assert settings['num_envs']==NUM_ENVS and settings['size']=='large' and settings['horizon']==32
settings=copy.deepcopy(settings); settings['num_envs']=NUM_ENVS
results=[]
for name in ('initial','final'):
    out=p/('evaluation_'+name+'_1024');out.mkdir(exist_ok=False)
    checkpoint=run/(name+'.pt')
    pins={path:value for path,value in json.loads((run/'inputs_before.json').read_text()).items()}
    (out/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
    pins[str(out/'settings.json')]=hashlib.sha256((out/'settings.json').read_bytes()).hexdigest()
    pins[str(Path(__file__).resolve())]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    pins[str(checkpoint)]=hashlib.sha256(checkpoint.read_bytes()).hexdigest()
    (out/'inputs_before.json').write_text(json.dumps(pins,indent=2)+'\n')
    pool=None
    started=time.perf_counter()
    ticks=0
    completed={}
    def lifecycle(stage,**fields):
        state=dict(stage=stage,ticks=ticks,completed_first_episodes=len(completed),
            wall_s=time.perf_counter()-started,checkpoint=str(checkpoint),**fields)
        (out/'lifecycle.json.tmp').write_text(json.dumps(state)+'\n')
        (out/'lifecycle.json.tmp').replace(out/'lifecycle.json')
    lifecycle('creating_pool')
    try:
        pool=GpuPool(settings,out)
        lifecycle('pool_created')
        policy=SpecialistPolicy(512,size='large',contract=pool.contract,role='left').to('cuda:0')
        coordinator=CurriculumCoordinator(policy,pool)
        trainer=PPOTrainer(policy,PPOConfig(**settings['ppo']))
        trainer.load(checkpoint)
        assert trainer.updates==(0 if name=='initial' else 2000)
        observation=coordinator.restore()
        policy.eval()
        lifecycle('checkpoint_restored')
        note_ledgers={}
        targets=copy.deepcopy(pool.environment.task.provenance['song']['schedule'])
        assert len(targets)==pool.environment.M==67
        assert [t['target_id'] for t in targets]==[t.target_id for t in pool.environment.task.targets]
        required_clean_s=pool.environment.required.detach().cpu().tolist()
        for i,target in enumerate(targets):
            target.update(target_index=i,canonical_string_1based=target['string']+1,required_clean_s=required_clean_s[i])
        with torch.no_grad():
            while len(completed)<NUM_ENVS and ticks<settings['song_training']['control_ticks']:
                result=policy.act(*(observation[k] for k in FIELDS),deterministic=True)
                observation,reward,cost,terminated,truncated,episodes=pool.step(result['action'])
                first_ended=[e for e in episodes if e['env_id'] not in completed]
                if first_ended:
                    indices=torch.tensor([e['env_id'] for e in first_ended],device=pool.scene.device)
                    captured={key:pool.environment.note[key][indices].detach().cpu().tolist() for key in NOTE_FIELDS}
                    for offset,e in enumerate(first_ended):
                        index=e['env_id']
                        ledger={key:captured[key][offset] for key in NOTE_FIELDS}
                        assert all(len(value)==67 for value in ledger.values())
                        assert sum(ledger['left'])==e['song']['left_success_count']
                        assert abs(sum(ledger['contact_done'])/67-e['left_curriculum']['contact_fraction'])<1e-6
                        completed[index]=e
                        note_ledgers[index]=dict(env_id=index,reason=e['reason'],full_safe=e['left_curriculum']['full_safe'],
                            end_task_time_s=e['task_time_s'],ledger=ledger)
                done=(terminated|truncated).nonzero().flatten()
                if done.numel() and len(completed)<NUM_ENVS and ticks+1<settings['song_training']['control_ticks']:
                    observation=pool.reset(done)[0]
                ticks+=1
                if ticks%60==0:
                    status=dict(ticks=ticks,completed_first_episodes=len(completed),wall_s=time.perf_counter()-started,checkpoint=str(checkpoint))
                    (out/'status.json.tmp').write_text(json.dumps(status)+'\n')
                    (out/'status.json.tmp').replace(out/'status.json')
        status=dict(ticks=ticks,completed_first_episodes=len(completed),wall_s=time.perf_counter()-started,checkpoint=str(checkpoint))
        (out/'status.json.tmp').write_text(json.dumps(status)+'\n')
        (out/'status.json.tmp').replace(out/'status.json')
        lifecycle('stepping_complete')
        assert len(completed)==NUM_ENVS
        torch.cuda.synchronize(pool.scene.device)
        lifecycle('checking_input_pins')
        changed=[path for path,value in pins.items() if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=value]
        lifecycle('input_pins_checked',changed_inputs=changed)
        assert not changed,changed
        episodes=[completed[i] for i in range(NUM_ENVS)]
        assert set(note_ledgers)==set(range(NUM_ENVS))
        safe_ids=[i for i in range(NUM_ENVS) if completed[i]['left_curriculum']['full_safe']]
        lifecycle('aggregating_note_ledgers')
        per_note=[]
        for j,target in enumerate(targets):
            row=dict(target)
            for group,ids in (('all_first',range(NUM_ENVS)),('full_safe_first',safe_ids)):
                count=len(ids)
                achieved=sum(note_ledgers[i]['ledger']['left'][j] for i in ids)
                row[group]=dict(episodes=count,left_success_count=achieved,
                    left_success_fraction=achieved/count if count else None)
                for key in ('clean','held','contact_time','reached'):
                    row[group]['mean_'+key+'_s']=sum(note_ledgers[i]['ledger'][key][j] for i in ids)/count if count else None
                for key in ('reach_done','contact_done'):
                    row[group][key+'_fraction']=sum(note_ledgers[i]['ledger'][key][j] for i in ids)/count if count else None
            per_note.append(row)
        ledger_path=out/'first_episode_note_ledgers.json'
        ledger_path.write_text(json.dumps(dict(schema='guitar_learning.evaluation_left_note_ledger.v1',
            checkpoint=str(checkpoint),targets=targets,episodes=[note_ledgers[i] for i in range(NUM_ENVS)],
            field_scope=dict(left='Audible valid-candidate time reaches required_clean_s; not real string pressure or sound',
                ever='Candidate observed at any episode time, not necessarily inside this note timing window',
                left_missed='Missed flag is set only after the note ends; false on an unreached future note is not success',
                clean_and_held='Valid-candidate audible overlap integral in seconds',
                wrong_and_missing='Audible wrong/missing-candidate overlap integral in seconds',
                contact_time='Valid-candidate press_s..end_s overlap integral in seconds',
                reached='Wrist-ready overlap integral in seconds',dwell='Current contiguous candidate duration at episode end, not maximum duration',
                release_s='Recorded release time only when released=true; otherwise zero is a sentinel'),
            scope='New evaluation first-episode tensors copied before reset, not reconstructed training data. Arrays follow target_index; string is0 high-e..5 low-E. All-first includes failed songs and unreached future notes; full-safe-first excludes failed songs.'),
            indent=2,allow_nan=False)+'\n')
        lifecycle('note_ledger_written')
        result=dict(completed=True,checkpoint=str(checkpoint),source_optimizer_updates=trainer.updates,
            deterministic=True,num_envs=NUM_ENVS,ticks=ticks,episodes=episodes,
            first_episode_note_ledger_path=ledger_path.name,per_note=per_note,
            per_note_scope='One first episode per env; all_first denominator1024; full_safe_first denominator is the number of safe whole first songs. These are geometric candidate ledgers, not acoustic success or past training note histories.',
            scope='Initial/final full checkpoint states at the same1024-env GPU batch size as training; no PPO updates; only the first ended episode per environment is scored.',
            curriculum_progress=coordinator.state.progress,
            limitation='Same song and prepared pose, but each checkpoint restores its own curriculum and corresponding observation weights; this compares full saved policy states, not weights under identical observations. 1024 env instances are not independent randomized trials or held-out generalization. Finished environments are reset as needed to keep the batch stepping, but their later episodes are not scored. Geometric contact candidates do not certify real string pressure or acoustic success.',
            wall_s=time.perf_counter()-started,input_pins_verified=len(pins))
        lifecycle('result_prepared')
    except BaseException as error:
        (out/'python_exception.json').write_text(json.dumps(dict(error=repr(error),traceback=traceback.format_exc()),indent=2)+'\n')
        traceback.print_exc()
        sys.stderr.flush()
        lifecycle('python_exception',error=repr(error))
        raise
    finally:
        if pool is not None:
            lifecycle('synchronizing_before_close')
            torch.cuda.synchronize(pool.scene.device)
            lifecycle('destroying_simulator')
            pool.close()
            lifecycle('pool_closed')
    result['gpu_scene']=pool.scene.diagnostics
    assert result['gpu_scene']['closed'] and result['gpu_scene']['environment_count']==NUM_ENVS
    assert result['gpu_scene']['physx_use_gpu'] and result['gpu_scene']['use_gpu_pipeline']
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n')
    lifecycle('report_written')
    results.append(result)
(p/'checkpoint_evaluation.json').write_text(json.dumps({'completed':True,'results':results},indent=2)+'\n')
print(json.dumps({'completed':True,'evaluated_checkpoints':[r['source_optimizer_updates'] for r in results]}))
