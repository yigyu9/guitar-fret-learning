"""One compact actual comparison figure; no producer/raw writes."""
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
if __name__=='__main__':
    s=importlib.util.spec_from_file_location('acquired_plot_completion',HERE/'analyze.py');a=importlib.util.module_from_spec(s);s.loader.exec_module(a);a.preflight()
    x=json.loads((HERE/'results_v1/comparison.json').read_text());out=HERE/'results_v1/comparison.png';assert not out.exists()
    import numpy as np
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from scipy.spatial.transform import Rotation
    fig,axes=plt.subplots(2,2,figsize=(10,6),sharex=True);colors=('tab:blue','tab:orange')
    for mode,color in zip(a.MODES,colors):
        folder=a.BASE/'runs'/mode
        with np.load(folder/'trace_env0_episode0.npz') as z:t=dict(z)
        meta=json.loads((folder/'trace_metadata.json').read_text());config=json.loads((folder/'settings.json').read_text());short=config['song']['short_learning']
        for col,name in enumerate(('LH:index2','LH:index3')):
            j=meta['joint_names'].index(name);axes[0,col].plot(t['time_s'],np.rad2deg(t['q'][:,j]),color=color,label=mode+' actual');axes[0,col].plot(t['time_s'],np.rad2deg(t['target'][:,j]),'--',color=color,label=mode+' target')
        for body,style in (('human/LH:index3','-'),('human/LH:index1',':')):
            j=meta['body_names'].index(body);axes[1,0].plot(t['time_s'],np.linalg.norm(t['net_body_force_n'][:,j],axis=-1),style,color=color,label=mode+' '+body.split(':')[-1])
        w,g=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')];rg=Rotation.from_quat(t['body_state'][:,g,3:7]);error=np.linalg.norm(t['body_state'][:,g,:3]+rg.apply(t['wrist_position_goal_G_m'])-t['body_state'][:,w,:3],axis=-1)*1000
        axes[1,1].plot(t['time_s'],error,color=color,label=mode)
    for ax in axes.flat:
        for n in short['view']['source_targets']:ax.axvspan(n['onset_s']-short['view']['score_offset_s'],n['end_s']-short['view']['score_offset_s'],color='green',alpha=.08)
        ax.axvline(764/240,color='gray',ls=':',alpha=.7);ax.legend(fontsize=7);ax.grid(alpha=.2)
    axes[0,0].set_ylabel('PIP degrees');axes[0,1].set_ylabel('DIP degrees');axes[1,0].set_ylabel('body resultant N');axes[1,1].set_ylabel('wrist origin error mm')
    for ax in axes[1]:ax.set_xlabel('env0 local endpoint seconds')
    fig.suptitle('Frozen300: retained-contact gate changes joint allocation, not 3-note success');fig.tight_layout();fig.savefig(out,dpi=150);plt.close(fig)
