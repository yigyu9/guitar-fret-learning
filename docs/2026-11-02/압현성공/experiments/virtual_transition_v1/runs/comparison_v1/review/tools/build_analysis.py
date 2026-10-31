"""완료된 전환 비교의 학습 표본과 평균 정책 평가를 구분해 재집계한다."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import statistics

HERE=Path(__file__).resolve().parents[1]
RUN=HERE.parent


def sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
    return h.hexdigest()


def episodes(folder):
    metadata=json.loads((folder/'episode_metadata.json').read_text())
    rows=[]
    for line in (folder/'episodes.jsonl').read_text().splitlines():
        row=copy.deepcopy(json.loads(line)['episode'])
        for item in metadata['fields']:
            current=row
            for key in item['path'][:-1]:current=current.setdefault(key,{})
            current[item['path'][-1]]=copy.deepcopy(item['value'])
        rows.append(row)
    return rows


def main():
    state=json.loads((RUN/'progress.json').read_text())
    assert state['status']=='complete' and state['completed_train_updates']==1200 and state['completed_evaluations']==12
    for name,expected in state['source_seal'].items():
        root=next(p for p in RUN.parents if (p/'scripts/tab2body.py').is_file())
        assert sha(root/name)==expected,name
    for job in state['jobs'].values():
        for name,expected in job.get('evidence_sha256',{}).items():assert sha(Path(name))==expected,name
    summary=json.loads((RUN/'summary.json').read_text())
    data=dict(original_evidence_verified=True,completed_updates=1200,evaluations=12,training_last100={},evaluation={})
    for seed in (7,17):
        for condition in ('E0','E4'):
            label=f'seed{seed}_{condition}_u300';folder=RUN/'blocks'/label/'train/J'
            rows=episodes(folder);count=len(rows)
            safe=[r for r in rows if r['termination']['primary_reason']=='timeline_complete' and not r['failure_reasons']]
            item=dict(episodes=count,safe_timeline_episodes=len(safe),
                all_four_achieved_safe=sum(all(r['left_note_ledger']['values']['left']) for r in safe),
                note_achieved_counts=[sum(bool(r['left_note_ledger']['values']['left'][i]) for r in rows) for i in range(4)],
                clean_mean_s=[statistics.mean(r['left_note_ledger']['values']['clean'][i] for r in rows) for i in range(4)],
                clean_sd_s=[statistics.pstdev(r['left_note_ledger']['values']['clean'][i] for r in rows) for i in range(4)])
            logs=[]
            for total in (100,200,300):
                logs.extend(json.loads(line) for line in (RUN/'blocks'/f'seed{seed}_{condition}_u{total}'/'train/J/learning_metrics.jsonl').read_text().splitlines())
            item['learning']=dict(lr_initial=logs[0]['actor_lr'],lr_final=logs[-1]['actor_lr'],lr_min=min(r['actor_lr'] for r in logs),
                kl_mean=statistics.mean(r['analytic_kl'] for r in logs),kl_max=max(r['analytic_kl'] for r in logs),
                entropy_initial=logs[0]['diagnostics']['post_update']['latent_gaussian_entropy']['mean'],
                entropy_final=logs[-1]['diagnostics']['post_update']['latent_gaussian_entropy']['mean'])
            item['input_sha256']={str(folder/n):sha(folder/n) for n in ('episodes.jsonl','episode_metadata.json','learning_metrics.jsonl')}
            data['training_last100'][label]=item
            data['evaluation'][label]=summary[label]['metrics']
    (HERE/'analysis_details.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from matplotlib.font_manager import FontProperties
    font=FontProperties(fname='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')
    plt.rcParams['font.family']=font.get_name()
    fig,axes=plt.subplots(2,2,figsize=(12,6),sharex=True,constrained_layout=True)
    provenance={}
    for col,condition in enumerate(('E0','E4')):
        path=RUN/'blocks'/f'seed7_{condition}_u300/evaluation/finger_control_trace.jsonl.gz'
        with gzip.open(path,'rt') as f:rows=[json.loads(line) for line in f]
        first=rows[0]['episode_id'];rows=[r for r in rows if r['env_id']==0 and r['episode_id']==first]
        t=np.asarray([r['episode_time_s'] for r in rows]);goal=np.full(len(t),np.nan)
        for start,end,fret in ((3,4.5,6),(5,6.5,7),(7,8.5,6),(9,10.5,7)):goal[(t>=start)&(t<end)]=fret
        observed=np.asarray([6 if r['natural_preparation']['transition']['goals'][0]['press_candidate'] else
            7 if r['natural_preparation']['transition']['goals'][1]['press_candidate'] else np.nan for r in rows])
        axes[0,col].plot(t,goal,color='black',ls='--',lw=2,label='목표 프렛')
        axes[0,col].plot(t,observed,color='#336eb0',lw=2,label='유효 압현 셀')
        axes[0,col].set_yticks([6,7]);axes[0,col].set_ylim(5.7,7.3)
        axes[0,col].set_title(condition+' · seed7 · 300회 (env0 대표 궤적)',fontproperties=font)
        axes[0,col].legend(prop=font,loc='upper right',fontsize=8)
        distance=[r['natural_preparation']['transition']['goals'][1]['pad_distance_m']*1000 for r in rows]
        height=[r['natural_preparation']['transition']['goals'][1]['pad_height_m']*1000 for r in rows]
        axes[1,col].plot(t,distance,label='B 패드 거리',color='#d58124')
        axes[1,col].plot(t,height,label='B 패드 높이',color='#559749',ls=':')
        axes[1,col].set_ylim(-1,20);axes[1,col].set_ylabel('mm');axes[1,col].set_xlabel('초',fontproperties=font)
        axes[1,col].legend(prop=font,loc='upper right')
        for ax in axes[:,col]:
            ax.set_xlim(0,11)
            for start,end in ((5,6.5),(9,10.5)):ax.axvspan(start,end,color='#f5d7a2',alpha=.35)
            ax.grid(alpha=.2)
        provenance[str(path)]=sha(path)
    fig.suptitle('목표는 7프렛으로 바뀌지만 6프렛 압현을 계속 유지함',fontproperties=font)
    fig.savefig(HERE/'transition_timeline.png',dpi=160);plt.close(fig)
    (HERE/'figure_provenance.json').write_text(json.dumps(dict(scope='env0 first episode only, not32 mean',input_sha256=provenance),ensure_ascii=False,indent=2)+'\n')
    print('Verified original sources/evidence; wrote training aggregates and timeline')


if __name__=='__main__':main()
