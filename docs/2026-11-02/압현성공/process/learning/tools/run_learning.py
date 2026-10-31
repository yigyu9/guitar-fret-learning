"""기존 J33 학습기/PPO로 16개 가상 단일음을 독립 학습·평가한다."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'guitar_learning/train.py').is_file())
OUT=Path(__file__).resolve().parents[1]
BASE=OUT.parent.parent
sys.path.insert(0,str(ROOT))
from guitar_learning.training.training_log_io import active_source_paths, iter_episode_rows


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp');t.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');t.replace(p)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--updates',type=int,default=100)
    parser.add_argument('--num-envs',type=int,default=64)
    args=parser.parse_args()
    with (OUT/'runner.lock').open('w') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);run(args)


def run(args):
    goals=read(OUT/'targets.json')['targets']
    paths=active_source_paths(ROOT/'guitar_learning')|set((OUT/'tools').glob('*.py'))|{OUT/'targets.json'}
    paths.update(p for g in goals for p in (ROOT/'data/song_bundles'/g['song_id']).rglob('*') if p.is_file())
    pins={str(p.resolve()):sha(p) for p in sorted(paths)}
    settings=dict(updates=args.updates,num_envs=args.num_envs,horizon=32,size='large',seed=7,evaluation_envs=16)
    state_path=OUT/'run_manifest.json'
    if state_path.exists():
        if not args.resume:raise FileExistsError('기존 실행은 --resume 필요')
        manifest=read(state_path)
        if manifest['pins']!=pins or manifest['settings']!=settings:raise ValueError('Source/settings changed')
    else:
        manifest=dict(settings=settings,pins=pins,completed={});write(state_path,manifest)
    state=dict(phase='preparing',goal_count=len(goals),completed_goals=0,pid=os.getpid())
    def progress(**kw):
        state.update(kw,updated_at=datetime.now(timezone.utc).isoformat());write(OUT/'status.json',state)
        (OUT/'progress.md').write_text('# 실제 가상 압현 학습 진행\n\n'+json.dumps(state,ensure_ascii=False,indent=2)+'\n')
    env=dict(os.environ)
    env.update(PYTHONPATH=str(ROOT/'isaacgym/python')+':'+str(ROOT),
        PATH=str(Path(sys.executable).parent)+':/usr/local/cuda/bin:/usr/bin:/bin',
        LD_LIBRARY_PATH=str(Path(sys.executable).parent.parent/'lib'),
        PYTHONUTF8='1',PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1',LANG='C.UTF-8',LC_ALL='C.UTF-8',
        OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',MUJOCO_GL='osmesa',
        TORCH_EXTENSIONS_DIR=str(BASE/'process/cache/torch'),MPLCONFIGDIR=str(OUT/'cache/mpl'))
    def check_pins():
        changed=[p for p,h in pins.items() if not Path(p).is_file() or sha(Path(p))!=h]
        if changed:raise RuntimeError('Study inputs changed: '+str(changed[:5]))
    def execute(name,command,proof,output):
        check_pins()
        if name in manifest['completed']:
            for p,h in manifest['completed'][name].items():
                if not Path(p).is_file() or sha(Path(p))!=h:raise RuntimeError('Completed proof changed: '+p)
            return
        if output.exists():raise FileExistsError('Partial output preserved; inspect before retry: '+str(output))
        progress(phase=name)
        log=OUT/'logs'/(name+'.log');log.parent.mkdir(exist_ok=True,parents=True)
        with log.open('a') as stream:
            stream.write('\nSTART '+datetime.now(timezone.utc).isoformat()+'\n');stream.flush()
            child=subprocess.Popen([sys.executable,'-B','-X','utf8']+command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT)
            started=time.monotonic();progress(child_pid=child.pid,log=str(log.resolve()))
            try:
                while child.poll() is None:
                    try:child.wait(timeout=20)
                    except subprocess.TimeoutExpired:progress(elapsed_s=round(time.monotonic()-started,1))
            except BaseException:
                child.terminate();child.wait();raise
            if child.returncode:raise RuntimeError(name+' failed; '+str(log))
        check_pins();assert read(proof)['completed'],proof
        manifest['completed'][name]={str(proof.resolve()):sha(proof)};write(state_path,manifest)
        progress(child_pid=None)
    try:
        for i,g in enumerate(goals):
            label=g['song_id'].replace('virtual_finger_v9_','');folder=OUT/'runs'/label
            progress(goal_index=i,goal=g,completed_goals=i)
            train=folder/'train'
            execute(label+'_train',['-m','guitar_learning.train','--song',g['song_id'],'--size','large',
                '--num-envs',str(args.num_envs),'--horizon','32','--updates',str(args.updates),
                '--checkpoint-every','1000','--seed','7','--out',str(train)],train/'report.json',train)
            for checkpoint in ('initial','final'):
                evaluation=folder/('evaluate_'+checkpoint)
                execute(label+'_evaluate_'+checkpoint,['-m','guitar_learning.tool.evaluation.evaluate_finger_skill',
                    str(train/'J'/(checkpoint+'.pt')),'--num-envs','16','--scope','full_song','--out',str(evaluation)],
                    evaluation/'report.json',evaluation)
            progress(completed_goals=i+1)
            summarize(goals[:i+1])
        summary=summarize(goals)
        # 성공한 목표는 모두, 성공이 없는 손가락은 마지막 정책의 실패 예시 한 개를 남긴다.
        selected=[x for x in summary['goals'] if x['final_success_count']>0]
        for finger in range(1,5):
            own=[x for x in summary['goals'] if x['finger']==finger]
            if not any(x['final_success_count']>0 for x in own):
                selected.append(max(own,key=lambda x:x['final_mean_reward']))
        videos=[]
        for g in selected:
            label=g['label'];render=OUT/'rendering'/label
            execute(label+'_render',['-m','guitar_learning.tool.demonstration.render_finger_skill',
                '--checkpoint',g['final_checkpoint'],'--num-envs','4','--scope','full_song','--out',str(render)],
                render/'report.json',render)
            folder=BASE/'video/learning'/label;folder.mkdir(exist_ok=True,parents=True)
            paths={}
            for view in ('hand','fullbody'):
                original=render/(view+'.mp4');dest=folder/(view+'.mp4')
                if original.exists():original.replace(dest)
                assert dest.is_file();paths[view]=str(dest.resolve())
            videos.append(dict(label=label,evaluation_success_count=g['final_success_count'],videos=paths,
                native_render_report=str((render/'report.json').resolve())))
        write(OUT/'media_manifest.json',dict(videos=videos,scope='actual learned policy; env0 first episode, no best-episode selection'))
        progress(phase='complete',completed_goals=len(goals),video_pairs=len(videos),child_pid=None)
    except BaseException as e:
        progress(phase='failed',failure=repr(e));raise


def summarize(goals):
    rows=[]
    for g in goals:
        label=g['song_id'].replace('virtual_finger_v9_','');folder=OUT/'runs'/label
        records={kind:read(folder/('evaluate_'+kind)/'report.json') for kind in ('initial','final')}
        row=dict(g,label=label,final_checkpoint=str((folder/'train/J/final.pt').resolve()))
        for kind,r in records.items():
            summary=r['summary'];episodes=[x['episode'] for x in iter_episode_rows(folder/('evaluate_'+kind))]
            row[kind+'_success_count']=sum(e['song']['left_success_count']>0 and not e['termination']['physical_failure'] and not e['termination']['wrist_failure'] for e in episodes)
            row[kind+'_mean_reward']=summary['mean_reward']
            row[kind+'_evaluation']=summary
            streaks=[e['left_note_ledger']['values']['best_clean_streak'][0] for e in episodes]
            row[kind+'_mean_best_clean_streak_s']=sum(streaks)/len(streaks)
            row[kind+'_max_best_clean_streak_s']=max(streaks)
        rows.append(row)
    output=BASE/'analysis/learning';output.mkdir(parents=True,exist_ok=True)
    result=dict(goal_count=len(rows),goals=rows,scope='main J33 fresh PPO, virtual one-note target, original reward/termination/controller')
    write(output/'summary.json',result);return result


if __name__=='__main__':main()
