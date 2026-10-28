"""Small supplementary plots; only after completed actual analysis, no raw writes."""
import argparse
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser();p.add_argument('--root-completed',action='store_true');args=p.parse_args()
    if not args.root_completed:print('완료 전 실제자료/그림 생성0');return
    s=importlib.util.spec_from_file_location('prefix_learning_plot_guard',HERE/'analyze.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);a.preflight()
    out=HERE/'results_v1';x=json.loads((out/'comparison.json').read_text());updates=list(a.UPDATES)
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.spatial.transform import Rotation
    path=out/'performance.png';assert not path.exists()
    fig,axes=plt.subplots(1,2,figsize=(10,3.5))
    for col,label in enumerate(('A4','B7','B8')):axes[0].plot(updates,[x['cases'][str(u)]['acceptance']['per_note'][col]['achieved_fraction'] for u in updates],marker='o',label=label)
    axes[0].plot(updates,[x['cases'][str(u)]['acceptance']['all3_achieved_fraction'] for u in updates],'k--',label='all3');axes[0].set(xlabel='update',ylabel='achieved fraction',ylim=(-.04,1.04));axes[0].legend()
    for j,label in ((2,'PIP'),(3,'DIP')):
        metrics=[list(x['cases'][str(u)]['env0']['notes'].values())[2]['phases']['audible']['metric_mean'] for u in updates]
        axes[1].plot(updates,[v[j] for v in metrics],marker='o',label=label+' actual');axes[1].plot(updates,[v[4+j] for v in metrics],'--',label=label+' target')
    axes[1].set(xlabel='update',ylabel='env0 B8 mean degrees');axes[1].legend(fontsize=8)
    for ax in axes:ax.grid(alpha=.2)
    fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)
    for u in x['selection']['video_updates']:
        path=out/('env0_%06d.png'%u);assert not path.exists();folder=a.BASE/('evaluation_%06d'%u)
        with np.load(folder/'trace_env0_episode0.npz') as z:t=dict(z)
        config=json.loads((folder/'settings.json').read_text());meta=json.loads((folder/'trace_metadata.json').read_text());short=config['song']['short_learning'];ids=[meta['joint_names'].index(n) for n in short['learned_action_names']]
        body=[meta['body_names'].index('human/LH:index'+str(i)) for i in (1,2,3)];w,g=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')];rg=Rotation.from_quat(t['body_state'][:,g,3:7])
        wrist=np.linalg.norm(t['body_state'][:,g,:3]+rg.apply(t['wrist_position_goal_G_m'])-t['body_state'][:,w,:3],axis=-1)*1000
        fig,axes=plt.subplots(4,1,figsize=(9,8),sharex=True)
        for j,label in ((2,'PIP'),(3,'DIP')):axes[0].plot(t['time_s'],np.rad2deg(t['q'][:,ids[j]]),label=label+' actual');axes[0].plot(t['time_s'],np.rad2deg(t['target'][:,ids[j]]),'--',label=label+' target')
        for j,b in enumerate(body):axes[1].plot(t['time_s'],np.linalg.norm(t['net_body_force_n'][:,b],axis=-1),label='index'+str(j+1))
        axes[2].plot(t['time_s'],wrist,label='wrist origin error')
        for field,col,label in (('candidate',0,'A candidate'),('candidate',1,'B7 candidate'),('wrong',1,'B7 wrong')):axes[3].step(t['time_s'],t[field][:,col].astype(int),where='post',label=label)
        for ax,ylabel in zip(axes,('degrees','body resultant N','wrist mm','saved flag')):
            for n in short['view']['source_targets']:ax.axvspan(n['onset_s']-short['view']['score_offset_s'],n['end_s']-short['view']['score_offset_s'],color='green',alpha=.08)
            ax.set_ylabel(ylabel);ax.grid(alpha=.2);ax.legend(fontsize=7)
        axes[0].set_title('env0 fixed evaluation update %d; first-attempt 60Hz'%u);axes[3].set_xlabel('local endpoint seconds');fig.tight_layout();fig.savefig(path,dpi=140);plt.close(fig)


if __name__=='__main__':main()
