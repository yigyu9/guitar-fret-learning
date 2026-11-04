"""네 조건의 공통 업데이트 평가와 확률 학습 로그를 읽기 전용으로 비교한다.

진행 중 마지막 미완성 JSONL 행은 다음 갱신까지 보류한다. 모델이나 원시
자료는 수정하지 않으며, 평균 정책 평가·확률 학습·최선 영상 모델을 분리한다.
"""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/matplotlib-a0-exploration-lr')
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

STUDY=Path(__file__).resolve().parents[1]
CONDITIONS={'C00':(.15,'existing'),'C10':(.20,'existing'),
            'C01':(.15,'recover_floor'),'C11':(.20,'recover_floor')}


class Reader:
    def __init__(self):self.pins={};self.pending=[];self.errors=[]
    def bytes(self,path):
        path=Path(path)
        if not path.is_file():return None
        data=path.read_bytes();self.pins[str(path.resolve())]=hashlib.sha256(data).hexdigest();return data
    def document(self,path,default=None):
        data=self.bytes(path)
        if data is None:return default
        try:return json.loads(data)
        except (ValueError,UnicodeError) as error:
            self.errors.append(dict(path=str(path),error=str(error)));return default
    def rows(self,path):
        data=self.bytes(path)
        if data is None:return []
        result=[];lines=data.splitlines()
        for index,line in enumerate(lines):
            if not line.strip():continue
            try:result.append(json.loads(line))
            except (ValueError,UnicodeError) as error:
                if index==len(lines)-1 and not data.endswith(b'\n'):
                    self.pending.append(dict(path=str(path),line=index+1));continue
                self.errors.append(dict(path=str(path),line=index+1,error=str(error)))
        return result


def save(path,value):
    temporary=path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    temporary.replace(path)


def safe(episode):
    termination=episode.get('termination',{})
    return bool(episode.get('valid') and not episode.get('song',{}).get('safety_invalidated')
        and not termination.get('physical_failure') and not termination.get('wrist_failure'))


def note_stats(rows):
    episodes=[row.get('episode',row) for row in rows];counts=dict(episodes=len(episodes),
        B_exposure_any=0,B_full_exposure=0,B_contact_any=0,B_contact_done=0,B_clean_any=0,
        B_achieved=0,B_safe_achieved=0,both_safe_achieved=0,physical=0,wrist=0,invalid=0,
        B_contact_total_s=0.,B_clean_total_s=0.,B_wrong_total_s=0.,B_best_streak_max_s=0.)
    for episode in episodes:
        values=episode.get('left_note_ledger',{}).get('values',{})
        if len(values.get('clean',[]))!=2:continue
        def b(key,default=0):return values.get(key,[default,default])[1]
        counts['B_exposure_any']+=b('exposure_time')>0
        counts['B_full_exposure']+=b('exposure_time')>=1.5-1e-8
        counts['B_contact_any']+=b('contact_time')>0
        counts['B_contact_done']+=bool(b('contact_done',False))
        counts['B_clean_any']+=b('clean')>0
        counts['B_achieved']+=bool(b('left',False))
        counts['B_safe_achieved']+=safe(episode) and bool(b('left',False))
        counts['both_safe_achieved']+=safe(episode) and episode['song'].get('stage_success',False) and all(values.get('left',[]))
        counts['physical']+=bool(episode.get('termination',{}).get('physical_failure'))
        counts['wrist']+=bool(episode.get('termination',{}).get('wrist_failure'))
        counts['invalid']+=not safe(episode)
        counts['B_contact_total_s']+=b('contact_time');counts['B_clean_total_s']+=b('clean');counts['B_wrong_total_s']+=b('wrong')
        counts['B_best_streak_max_s']=max(counts['B_best_streak_max_s'],b('best_clean_streak'))
    return counts


def collect(reader,state,study):
    results={}
    for label,(std,mode) in CONDITIONS.items():
        name=label+'_s7';case=state.get('cases',{}).get(name,{})
        training=state.get('tasks',{}).get(name+'_train400',{})
        out=Path(training.get('out',study/'실행'/ (name+'_train400')))
        metrics=reader.rows(out/'J/learning_metrics.jsonl');episodes=reader.rows(out/'J/episodes.jsonl')
        series=[]
        for row in metrics:
            lr=row.get('lr_recovery',{});accepted=lr.get('accepted_lr',[])
            series.append(dict(update=int(row.get('optimizer_updates',int(row.get('update_index',-1))+1)),
                actor_lr=row.get('actor_lr'),analytic_kl=row.get('analytic_kl'),recorded_lr_mode=lr.get('mode'),
                kl_retries=lr.get('kl_retries',row.get('kl_retries',0)),max_attempted_kl=row.get('max_attempted_kl'),
                recovered=bool(lr.get('recovered',False)),before_update_lr=lr.get('before_update_lr',[]),
                start_lr=lr.get('start_lr',[]),accepted_lr=accepted,
                actual_arm_latent_std=lr.get('actual_arm_latent_std',[]),
                actual_middle_latent_std=lr.get('actual_middle_latent_std',[])))
        evaluation={}
        for update,entry in case.get('evaluations',{}).items():
            result=dict(entry.get('result',{}));raw=reader.rows(Path(entry['out'])/'episodes.jsonl') if entry.get('out') else []
            stats=note_stats(raw);result.update(raw_note_stats=stats,update=int(update),out=entry.get('out'))
            result['B_contact_episodes']=stats['B_contact_any'] if raw else None
            result['B_safe_achieved']=stats['B_safe_achieved'] if raw else None
            result['mean_B_clean_s']=(stats['B_clean_total_s']/stats['episodes']) if raw else None
            result['raw_denominator_matches']=stats['episodes']==result.get('denominator') if raw else None
            evaluation[update]=result
        lr_summary=dict(recorded_updates=len(series),last_update=series[-1]['update'] if series else None,
            recovery_updates=sum(x['recovered'] for x in series),kl_retry_total=sum(x['kl_retries'] for x in series),
            kl_retry_updates=sum(x['kl_retries']>0 for x in series),
            accepted_below_floor_updates=sum(any(x<1.5e-5-1e-12 for x in r['accepted_lr']) for r in series),
            final=series[-1] if series else None)
        windows={str(u):note_stats([e for e in episodes if int(e.get('update_index',0))+1<=u]) for u in (100,200,400)}
        results[label]=dict(arm_initial_std=std,lr_mode=mode,status=case.get('status','대기'),
            finished=bool(case.get('finished')),evaluations=evaluation,training_all=note_stats(episodes),
            training_cumulative=windows,lr_summary=lr_summary,metric_series=series,
            selected_video_update=case.get('selected',{}).get('update'),videos=case.get('videos',{}),
            training_out=str(out))
    return results


def draw(results,out):
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for index,(label,case) in enumerate(results.items()):
        color='C'+str(index)
        evaluation=case['evaluations'];updates=sorted(map(int,evaluation))
        axes[0,0].plot(updates,[evaluation[str(u)].get('clean_fraction_by_target',[0,0])[1] for u in updates],marker='o',label=label,color=color)
        axes[0,1].plot(updates,[evaluation[str(u)].get('safe_success',0) for u in updates],marker='o',label=label,color=color)
        series=case['metric_series'];axes[1,0].plot([r['update'] for r in series],[r['actor_lr'] for r in series],label=label,color=color)
        for field,style in (('actual_arm_latent_std','-'),('actual_middle_latent_std','--')):
            present=[r for r in series if r[field]]
            axes[1,1].plot([r['update'] for r in present],[statistics.mean(r[field]) for r in present],style,label=label+(' arm' if style=='-' else ' middle'),color=color)
    titles=['Mean-policy B clean fraction','Mean-policy both-note safe success /16','Actual accepted actor LR','Actual latent std (arm solid / middle dashed)']
    for axis,title in zip(axes.flat,titles):
        axis.set_title(title);axis.set_xlabel('Update');axis.set_xlim(0,400);axis.grid(alpha=.25);axis.legend(fontsize=7)
    axes[0,0].set_ylim(-.02,1.02);axes[0,1].set_ylim(-.3,16.3)
    all_lr=[r['actor_lr'] for c in results.values() for r in c['metric_series'] if r['actor_lr'] is not None]
    all_std=[statistics.mean(r[f]) for c in results.values() for r in c['metric_series'] for f in ('actual_arm_latent_std','actual_middle_latent_std') if r[f]]
    axes[1,0].set_ylim(0,max([3.2e-5]+[x*1.1 for x in all_lr]));axes[1,1].set_ylim(0,max([.4]+[x*1.1 for x in all_std]))
    axes[1,0].axhline(1.5e-5,color='gray',linestyle=':',label='recovery start floor')
    target=out/'비교그래프.png';temp=out/'비교그래프.tmp.png';fig.savefig(temp,dpi=150);plt.close(fig);temp.replace(target)


def markdown(report,out):
    results=report['conditions'];lines=['# 중지 6→8프렛 탐색·학습률 비교 분석','',
        '갱신: '+report['updated_at'],'',
        '주 비교는 네 조건 모두 같은 400회 업데이트다. 100/200회는 학습 경과이며, 조건별 최선 모델의 영상은 400회 비교와 구분한다. 현재 공통 평가 업데이트: '+str(report['common_evaluation_updates'])+'。','',
        'C00: 팔 std 0.15·기존 LR, C10: 0.20·기존 LR, C01: 0.15·시작 LR 복구, C11: 0.20·시작 LR 복구. 중지 초기 std는 모두 0.35다.','',
        '## 평균 정책 평가','',
        '| 조건 | 회 | B 접촉 에피소드 | B 평균 clean 초 | B 안전 달성 | 두 음 안전 달성 | 오압현 union 초 | 물리/손목/무효 | 엄격 시각 통과 |','| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: |']
    def value(x):return '—' if x is None else f'{x:.4g}' if isinstance(x,float) else str(x)
    for label,case in results.items():
        for update in (100,200,400):
            r=case['evaluations'].get(str(update),{});den=r.get('denominator',16)
            lines.append('| '+ ' | '.join([label,str(update),value(r.get('B_contact_episodes')),value(r.get('mean_B_clean_s')),value(r.get('B_safe_achieved'))+'/'+str(den),value(r.get('safe_success'))+'/'+str(den),value(r.get('wrong_active_union_s')),'/'.join(value(r.get(k)) for k in ('physical','wrist','invalid')),value(r.get('strict_timing_pass'))+'/'+str(den)])+' |')
    lines+=['','## 확률 학습과 LR','',
        '| 조건 | 기록 업데이트 | 전체 완료 ep | B 노출/끝까지 노출 | B 접촉/clean ep | B 달성/두 음 안전 달성 | 누적 B 오압현 초 | LR 복구 update | KL retry | 마지막 실제 LR |','| --- | ---: | ---: | --- | --- | --- | ---: | ---: | ---: | ---: |']
    for label,case in results.items():
        t=case['training_all'];lr=case['lr_summary'];final=lr['final'] or {}
        lines.append('| '+' | '.join(map(str,[label,lr['recorded_updates'],t['episodes'],f"{t['B_exposure_any']}/{t['B_full_exposure']}",f"{t['B_contact_any']}/{t['B_clean_any']}",f"{t['B_achieved']}/{t['both_safe_achieved']}",value(t['B_wrong_total_s']),lr['recovery_updates'],lr['kl_retry_total'],value(final.get('actor_lr'))]))+' |')
    lines+=['','확률 학습 중 물리/손목 종료: '+', '.join(label+' '+str(c['training_all']['physical'])+'/'+str(c['training_all']['wrist']) for label,c in results.items())+'。']
    lines+=['','확률 학습 표는 현재까지의 누적 완료 에피소드다. 조건별 진행량이 다르면 이 표의 총합으로 우열을 비교하지 않는다. JSON에는 공통100/200/400회까지의 학습 누적치도 별도로 저장한다. B 접촉은 원장 contact_time>0, clean은 오압현 없이 유효 압현된 시간>0이다. 단일 접촉과 음 달성은 다르다.','',
        'LR 복구는 update 시작에서만 최소1.5e-5로 올린다. KL 재시도에서 원래 rollback·감소를 허용하므로 수용 LR은 하한보다 작을 수 있다. start_lr과 accepted_lr을 구분하며 그래프는 실제 actor_lr이다. std는 tanh 이전 Gaussian 값이며 각도 단위나 탐색 하한이 아니다.','',
        '## 대표 영상과 한계','']
    for label,case in results.items():
        videos=[p for p in case['videos'] if p.endswith('_hand.mp4')]
        lines.append('- '+label+': 최선 영상 모델 '+value(case['selected_video_update'])+'회'+(' · [손 확대]('+videos[0]+')' if videos else ' · 아직 영상 없음'))
    lines+=['','평가는 같은 준비 상태의 평균 정책16환경 재현이며 독립16학습시드가 아니다. 네 조건 모두 seed7 한 번의 학습이므로 일반화나 통계적 우위를 확정하지 않는다. 실패·무효·물리/손목 종료를 평가 분모에서 빼지 않는다. 오압현은 원인별 중복 합계가 아닌 활성 시간 union을 사용한다.','',
        '부분 JSONL 행 보류: '+str(report['pending_tail_rows']),'원시 읽기 오류: '+str(report['read_errors']),'',
        '![비교 그래프]('+str((out/'비교그래프.png').resolve())+')','']
    temporary=out/'비교분석.md.tmp';temporary.write_text('\n'.join(lines).replace('。','.'));temporary.replace(out/'비교분석.md')


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state',type=Path,default=STUDY/'진행상황.json');parser.add_argument('--out',type=Path,default=STUDY/'분석');args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=True);reader=Reader();reader.bytes(Path(__file__).resolve());state=reader.document(args.state,{}) or {};results=collect(reader,state,args.state.resolve().parent)
    common=set.intersection(*(set(c['evaluations']) for c in results.values()))
    report=dict(schema='guitar_learning.a0_exploration_lr_analysis.v1',analysis_generated=True,
        completed=all(c['finished'] and '400' in c['evaluations'] for c in results.values()) and not reader.errors and not reader.pending,
        updated_at=datetime.now(timezone.utc).isoformat(),conditions=results,
        common_evaluation_updates=sorted(map(int,common)),pending_tail_rows=reader.pending,read_errors=reader.errors,
        source_sha256=reader.pins,source_hash_scope='each file byte snapshot used for parsing; running append logs may grow later',
        comparison_update=400,training_seed=7,evaluation_scope='mean policy16 same-input reproductions; stochastic training separate')
    draw(results,args.out);save(args.out/'비교수치.json',report);markdown(report,args.out)
    print(json.dumps(dict(analysis_generated=True,completed=report['completed'],common_updates=report['common_evaluation_updates'],read_errors=len(reader.errors)),ensure_ascii=False))
    return 1 if reader.errors else 0


if __name__=='__main__':raise SystemExit(main())
