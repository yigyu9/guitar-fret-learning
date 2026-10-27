"""Sequential fixed-teacher fresh PPO pilot, strict evaluation and CPU analysis.

Dry run by default. --execute may be used only after the root GPU handoff.
No active package imports or edits; each child owns and closes its one simulator.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[5]
BASE = Path(__file__).resolve().parents[1]
TEACHER = BASE.parent/'02_contact_reward/short_finger_wrist_teacher_middle_row8_v2.json'
REFERENCE = BASE/'reference_middle_row8_v2.json'
PYTHON = Path('/home/ajou/miniconda3/envs/rl38/bin/python')
MODULE = 'guitar_learning.tool.experiments.short_finger_learning'
AFFINITY = '0-13'
STDS = dict(incremental=.1711710544767014, position=.01)
TERMS = ('song_left_approach','song_left_contact','song_clean_hold','song_left_success',
         'song_wrong_press','song_performance_deficit','song_finger_standby','song_thumb_support','action_change')
LABELS = ('목표 패드 접근','최초 접촉','압현 유지','압현 달성','오압현','음 수행 부족','대기 자세','엄지 안내','행동 변화')


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False)
        stream.write('\n')


def jobs(output, mode, seed):
    prefix=['taskset','-c',AFFINITY,'env','KMP_AFFINITY=disabled','OMP_PROC_BIND=false',
            'OMP_NUM_THREADS=1','MKL_NUM_THREADS=1',str(PYTHON),'-m',MODULE]
    train=output/'train'
    result=[dict(name='train',out=str(train),args=prefix+['train','--teacher',str(TEACHER),
        '--mode',mode,'--initial-std',str(STDS[mode]),'--size','large','--num-envs','128',
        '--horizon','32','--updates','300','--save-every','50','--seed',str(seed),'--out',str(train)])]
    cases=[('initial_'+control,'initial.pt',control) for control in ('policy','zero','random','reference')]
    cases += [('%06d'%update,'final.pt' if update==300 else 'evaluation_%06d.pt'%update,'policy')
              for update in (50,100,150,200,250,300)]
    for name, checkpoint, control in cases:
        out=output/('evaluation_'+name)
        args=prefix+['evaluate','--checkpoint',str(train/checkpoint),'--control',control,
                     '--episodes','128','--out',str(out)]
        if control=='reference': args += ['--reference',str(REFERENCE)]
        result.append(dict(name='evaluation_'+name,out=str(out),args=args,control=control,checkpoint=checkpoint))
    return result


def validate(job, mode, seed):
    folder=Path(job['out']); report=read(folder/'report.json')
    after=read(folder/'inputs_after.json'); before=read(folder/'inputs_before.json')
    if (report.get('completed') is not True or report.get('closed') is not True or report.get('failure') is not None or
            report.get('changed_inputs') or report.get('unpinned_project_sources') or after.get('verified') is not True or
            not before or after.get('input_pins')!=before):
        raise ValueError('Incomplete or unsealed child: '+job['name'])
    changed=[filename for filename,digest in before.items() if not Path(filename).is_file() or sha(filename)!=digest]
    if changed: raise ValueError('Inputs changed after child: '+str(changed[:5]))
    settings=read(folder/'settings.json'); spec=settings['song']['short_learning']
    expected=dict(size='large',num_envs=128,horizon=32,updates=300,seed=seed,checkpoint_every=50)
    if any(settings.get(key)!=value for key,value in expected.items()):
        raise ValueError('Pilot settings mismatch')
    if (spec['schema']!='guitar_learning.short_finger_learning.v2' or spec['mode']!=mode or
            spec['initial_std']!=STDS[mode] or settings['initial_std']!=STDS[mode] or
            spec['teacher']['input_sha256']!=sha(TEACHER) or spec['teacher']['input_path']!=str(TEACHER)):
        raise ValueError('Pilot teacher/control/exploration mismatch')
    if job['name']=='train':
        rows=[json.loads(line) for line in (folder/'metrics.jsonl').read_text().splitlines()]
        if len(rows)!=300 or [row['update'] for row in rows]!=list(range(1,301)):
            raise ValueError('Expected exactly300 completed updates')
        if rows[-1]['total_transitions']!=1228800 or any(set(row['reward_component_means'])!=set(TERMS) for row in rows):
            raise ValueError('Wrong rollout count or missing nine reward terms')
        for name in ['initial.pt','final.pt']+['evaluation_%06d.pt'%i for i in (50,100,150,200,250)]:
            if not (folder/name).is_file() or not (folder/name).stat().st_size: raise ValueError('Missing checkpoint: '+name)
        return dict(updates=300,transitions=1228800,wall_s=report['wall_s'])
    evaluation=read(folder/'evaluation.json')
    rows=evaluation['episodes']
    if (evaluation['condition']!=job['control'] or evaluation['assigned_quotas']!=[1]*128 or len(rows)!=128 or
            sorted(row['env_id'] for row in rows)!=list(range(128)) or any(row['selected_target_count']!=1 for row in rows)):
        raise ValueError('Evaluation must contain exactly first attempt of every128 environment')
    return dict(summary=evaluation['summary'],wall_s=report['wall_s'])


def run_child(job, output, env, identity):
    log=output/'logs'/(job['name']+'.log')
    with log.open('x') as stream:
        process=subprocess.Popen(job['args'],cwd=str(ROOT),env=env,stdout=stream,stderr=subprocess.STDOUT)
        try:
            while True:
                try:
                    status=process.wait(timeout=30)
                    if status: raise subprocess.CalledProcessError(status,job['args'])
                    break
                except subprocess.TimeoutExpired:
                    if sha(__file__)!=identity['script_sha256']:
                        raise ValueError('Orchestrator changed during execution')
                    pinfile=Path(job['out'])/'inputs_before.json'
                    pins=read(pinfile) if pinfile.exists() else identity['active_source_pins']
                    changed=[name for name,value in pins.items() if not Path(name).is_file() or sha(name)!=value]
                    if changed: raise ValueError('Input seal changed during execution: '+str(changed[:5]))
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try: process.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    process.kill();process.wait()
            raise


def analyze(output):
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family']=font.get_name(); plt.rcParams['axes.unicode_minus']=False
    result=output/'analysis'; result.mkdir(exist_ok=False)
    settings=read(output/'train/settings.json'); spec=settings['song']['short_learning']
    metrics=[json.loads(line) for line in (output/'train/metrics.jsonl').read_text().splitlines()]
    evals={folder.name:read(folder/'evaluation.json') for folder in sorted(output.glob('evaluation_*')) if folder.is_dir()}
    angles={}
    for name,value in evals.items():
        names=value['episodes'][0]['angles']['joint_names']
        arrays={key:np.asarray([row['angles']['values'][key] for row in value['episodes']])
                for key in value['episodes'][0]['angles']['values']}
        angles[name]=dict(joint_names=names,denominator=len(value['episodes']),sampling_hz=60,
            statistics={key:dict(median=np.median(array,axis=0).tolist(),p95=np.quantile(array,.95,axis=0).tolist(),
                                maximum=array.max(axis=0).tolist()) for key,array in arrays.items()})
    summary={name:value['summary'] for name,value in evals.items()}
    write(result/'analysis.json',dict(schema='short_comparison_analysis.v1',settings=settings,
        scope=spec['result_scope'],evaluations=summary,angles=angles,
        limitations=['single source target and seed;128 parallel first attempts, not128 independent seeds',
                     'scripted reference is teacher-assisted positive control, not learned policy',
                     'angle endpoint samples60Hz; native-limit fractions are not240Hz extrema',
                     'env0 trace is one prespecified attempt, not representative of all128']))
    fig,axes=plt.subplots(3,3,figsize=(15,10),sharex=True)
    for ax,key,label in zip(axes.flat,TERMS,LABELS):
        y=np.asarray([row['reward_component_means'][key] for row in metrics]);x=np.arange(1,len(y)+1)
        ax.plot(x,y,alpha=.45,lw=.7,label='업데이트 평균')
        ax.plot(x[9:],np.convolve(y,np.ones(10)/10,'valid'),lw=1.4,label='10회 이동평균')
        ax.set_title(label);ax.grid(alpha=.2)
    for ax in axes[-1]: ax.set_xlabel('PPO 업데이트')
    axes[0,0].set_ylabel('원시60Hz 전이당 보상');axes[0,0].legend(fontsize=8)
    fig.suptitle('보상9항 · 준비 구간 포함 · 실패 비용은 별도');fig.tight_layout()
    fig.savefig(result/'reward_terms.png',dpi=140);plt.close(fig)
    ordered=['evaluation_initial_policy']+['evaluation_%06d'%i for i in (50,100,150,200,250,300)]
    x=[0,50,100,150,200,250,300]
    fig,axes=plt.subplots(1,2,figsize=(12,4))
    for key,label in [('achieved_fraction','압현 달성'),('mean_clean_fraction','clean 유지'),('mean_audible_wrong_fraction','오압현')]:
        axes[0].plot(x,[summary[n][key] for n in ordered],marker='o',label=label)
    axes[0].axhline(summary['evaluation_initial_reference']['achieved_fraction'],ls='--',color='gray',label='script reference 달성')
    for key,label in [('physical_failure_fraction','물리 실패'),('wrist_failure_fraction','손목 실패')]:
        axes[1].plot(x,[summary[n][key] for n in ordered],marker='o',label=label)
    for ax in axes: ax.set_ylim(-.03,1.03);ax.set_xlabel('PPO 업데이트');ax.grid(alpha=.2);ax.legend()
    fig.suptitle('각 평가128환경 첫 시도 · 실패도 분모128에 포함');fig.tight_layout()
    fig.savefig(result/'performance.png',dpi=140);plt.close(fig)
    selected=spec['learned_action_names']
    fig,axes=plt.subplots(4,3,figsize=(15,11),sharex=True)
    for col,condition in enumerate(('evaluation_initial_policy','evaluation_000300','evaluation_initial_reference')):
        trace=np.load(output/condition/'trace_env0_episode0.npz');meta=read(output/condition/'trace_metadata.json')
        for row,name in enumerate(selected):
            i=meta['joint_names'].index(name);ax=axes[row,col]
            ax.plot(trace['time_s'],np.degrees(trace['q'][:,i]),label='실제각')
            ax.plot(trace['time_s'],np.degrees(trace['target'][:,i]),ls='--',label='목표각')
            ax.axvspan(spec['view']['local_onset_s'],spec['view']['local_end_s'],color='green',alpha=.15)
            ax.set_title(condition.replace('evaluation_','')+' / '+name);ax.grid(alpha=.2)
            if col==0:ax.set_ylabel('도(deg)')
    axes[0,0].legend();[ax.set_xlabel('초') for ax in axes[-1]]
    fig.suptitle('사전 지정env0 첫 시도 · 녹색은 원곡 audible 창');fig.tight_layout()
    fig.savefig(result/'selected_finger_trace.png',dpi=140);plt.close(fig)
    baseline=angles['evaluation_initial_policy'];final=angles['evaluation_000300'];names=final['joint_names']
    fig,axes=plt.subplots(3,1,figsize=(13,10),sharex=True);xs=np.arange(len(names))
    for ax,key,label,scale in zip(axes,('actual_range_rad','actual_native_limit_fraction','target_native_limit_fraction'),
            ('실제각 범위 중앙값(deg)','실제각 한계 체류 평균 비율','목표각 한계 체류 평균 비율'),(180/math.pi,1,1)):
        for offset,name,source in [(-.2,'초기',baseline),(.2,'최종',final)]:
            values=source['statistics'][key]['median']
            if key.endswith('fraction'):
                e=evals['evaluation_initial_policy' if name=='초기' else 'evaluation_000300']['episodes']
                values=np.mean([row['angles']['values'][key] for row in e],axis=0)
            ax.bar(xs+offset,np.asarray(values)*scale,.38,label=name)
        ax.set_ylabel(label);ax.legend();ax.grid(axis='y',alpha=.2)
    axes[-1].set_xticks(xs);axes[-1].set_xticklabels([n.replace('LH:','') for n in names],rotation=70)
    fig.suptitle('LH21 · 128개 시도 · 실제/명령 한계 체류 구분(60Hz)');fig.tight_layout()
    fig.savefig(result/'joint_motion_limits.png',dpi=140);plt.close(fig)
    lines=['# 고정 손목 teacher 조건의 1음 PPO pilot','',
           '이 결과는 고정 기타·중지1음·teacher 팔·나머지B 조건이다. 전곡 또는 자유 기타 성과가 아니다.',
           '평가는128환경의 첫 에피소드128개이며 조기 종료를 분모에서 제외하지 않았다. 같은 목표·seed의 병렬시도이므로 독립128seed로 해석하지 않는다.','',
           '| 평가 | 달성/128 | clean 평균 | 오압현 평균 | 물리 실패/128 | 손목 실패/128 |',
           '|---|---:|---:|---:|---:|---:|']
    for name in ['evaluation_initial_policy','evaluation_initial_zero','evaluation_initial_random','evaluation_initial_reference']+ordered[1:]:
        a=summary[name];lines.append('| %s | %d | %.3f | %.3f | %d | %d |'%(name.replace('evaluation_',''),
            round(128*a['achieved_fraction']),a['mean_clean_fraction'],a['mean_audible_wrong_fraction'],
            round(128*a['physical_failure_fraction']),round(128*a['wrist_failure_fraction'])))
    lines += ['', 'script reference는 손가락도 스크립트로 제어한 도달 대조이며 정책 학습 성과가 아니다. 초기policy/zero/random과 함께 비교해 teacher만으로 발생하는 접촉을 구분한다.',
              '보상 곡선은 원시60Hz 전이 평균이며 준비 구간을 포함한다. 선택 손가락 영상용 trace는 env0 첫 시도뿐이므로128환경 전체 성공을 대표하지 않는다.',
              '성과·관절 수치 전체는 analysis.json, 그림은 reward_terms.png/performance.png/selected_finger_trace.png/joint_motion_limits.png에 있다.']
    (result/'RESULTS.md').write_text('\n'.join(lines)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode',choices=tuple(STDS),default='incremental')
    parser.add_argument('--seed',type=int,default=7)
    parser.add_argument('--out',type=Path)
    parser.add_argument('--execute',action='store_true',help='requires explicit root GPU handoff')
    parser.add_argument('--continue-evaluations',action='store_true',help='reuse only complete strict-verified stages; never resumes training')
    parser.add_argument('--analyze-only',action='store_true')
    args=parser.parse_args()
    output=(args.out or BASE/('pilot_%s_seed%d_v2'%(args.mode,args.seed))).resolve()
    plan=jobs(output,args.mode,args.seed)
    if args.analyze_only:
        for job in plan: validate(job,args.mode,args.seed)
        analyze(output);return
    if not args.execute:
        print(json.dumps(dict(output=str(output),jobs=plan),indent=2));return
    os.sched_setaffinity(0,set(range(14)))
    output.mkdir(parents=True,exist_ok=args.continue_evaluations)
    (output/'logs').mkdir(exist_ok=args.continue_evaluations)
    plan_path=output/'comparison_plan.json'
    identity=dict(mode=args.mode,seed=args.seed,jobs=plan,script_path=str(Path(__file__).resolve()),script_sha256=sha(__file__),
                  teacher_sha256=sha(TEACHER),reference_sha256=sha(REFERENCE),affinity=AFFINITY,
                  source_frozen=True,active_source_pins={str(p):sha(p) for p in sorted((ROOT/'guitar_learning').rglob('*.py')) if 'archive' not in p.relative_to(ROOT/'guitar_learning').parts},
                  scope='one original target/fixed guitar; teacher-supported; no full-song claim')
    if plan_path.exists():
        if read(plan_path)!=identity:raise ValueError('Existing plan/input/script identity differs')
    else:write(plan_path,identity)
    env=os.environ.copy();env.update(KMP_AFFINITY='disabled',OMP_PROC_BIND='false',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1')
    env['PATH']=str(PYTHON.parent)+os.pathsep+env.get('PATH','')
    env['PYTHONPATH']=str(ROOT/'isaacgym/python')+os.pathsep+str(ROOT)+(os.pathsep+env['PYTHONPATH'] if env.get('PYTHONPATH') else '')
    env['LD_LIBRARY_PATH']=str(PYTHON.parent.parent/'lib')+(os.pathsep+env['LD_LIBRARY_PATH'] if env.get('LD_LIBRARY_PATH') else '')
    completed=[];started=time.time()
    for job in plan:
        folder=Path(job['out'])
        if folder.exists():
            if not args.continue_evaluations:raise FileExistsError(folder)
            checked=validate(job,args.mode,args.seed)
        else:
            print('START '+job['name'],flush=True)
            run_child(job,output,env,identity)
            checked=validate(job,args.mode,args.seed)
        completed.append(dict(name=job['name'],verification=checked))
        print('COMPLETE '+job['name']+' '+json.dumps(checked),flush=True)
    if sha(__file__)!=identity['script_sha256']:raise ValueError('Orchestrator source changed')
    write(output/'comparison_completed.json',dict(completed=True,stages=completed,wall_s=time.time()-started))
    analyze(output)


if __name__=='__main__':main()
