"""Compare saved native body9-PD experiment with its same-pose baseline."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';PHASE=BASE/'torso_hold_native_collision_v1';OLD=BASE/'palm_patch_priority_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=PHASE/'artifacts';assert not out.exists();inputs={str(Path(__file__).resolve()):sha(__file__)};data=[]
    for phase in (OLD,PHASE):
        item={}
        for name in ('analysis.json','early_motion_audit.json','native_feature_analysis.json'):
            d=read(phase/name);inputs.update(d['input_sha256']);inputs[str(phase/name)]=sha(phase/name);item[name]=d
        p=phase/'native/trace.jsonl';inputs[str(p)]=sha(p);item['trace']=[json.loads(v) for v in p.read_text().splitlines()];data.append(item)
    before={p:sha(p) for p in inputs};assert before==inputs;out.mkdir()
    colors=['#347ba6','#df914d'];labels=['Stored body9 gain x1','New body9 stiffness x2 / damping sqrt2']
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True);fig.subplots_adjust(left=.1,right=.68,bottom=.12,top=.92,hspace=.25)
    for item,label,color in zip(data,labels,colors):
        c=item['analysis.json']['curves']['palm_wide_near17']
        for ax,key in zip(axes[:2],('position_error_mm','rotation_error_deg')):ax.plot(c['time_s'],c[key],color=color,label=label)
        axes[2].plot(c['time_s'],[abs(v['torso_drift_deg']) for v in item['trace']],color=color,label=label)
    for ax,label in zip(axes,('World guitar position error (mm)','World guitar rotation error (deg)','Max body9 coordinate drift (deg)')):ax.set_ylabel(label);ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    axes[-1].set_xlabel('Actual simulation time (s)');fig.suptitle('Same initial81 / old81 targets / strap: only body9 PD changed')
    fig.text(.5,.025,'One fresh native5s and stored baseline. DOF coordinate drift is not bone SO(3) rotation. No palm support certification.',ha='center',fontsize=8)
    p1=out/'G_and_body9_comparison.png';fig.savefig(p1,dpi=170,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,8));fig.subplots_adjust(left=.16,right=.73,bottom=.13,top=.92,hspace=.38)
    for item,label,color in zip(data,labels,colors):
        s=item['early_motion_audit.json']['samples'];t=[r['time_s'] for r in s];upper=[r['source_palm_patch_interval']['distance_m']*1000 for r in s];lower=[r['source_palm_patch_interval']['distance_lower_bound_m']*1000 for r in s]
        axes[0].plot(t,upper,'o-',color=color,label=label);axes[0].fill_between(t,lower,upper,alpha=.2,color=color)
    axes[0].set_ylabel('Source palm-patch gap (mm)');axes[0].set_xlabel('Saved actual-pose sample time (s)');axes[0].grid(alpha=.2);axes[0].legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    ticks=[];rowlabels=[]
    for n,body in enumerate(('LH:thumb3','LH:index3','LH:middle3','LH:palm')):
        for j,item in enumerate(data):
            y=n*3+j;g=item['native_feature_analysis.json']['summary'][0]['by_body'].get(body,{});steps=g.get('near_positive_steps',[]);axes[1].scatter(np.array(steps)/240,np.full(len(steps),y),color=colors[j],s=3);ticks.append(y);rowlabels.append(body[3:]+' '+('x1' if j==0 else 'x2')+' n='+str(len(steps)))
    axes[1].set_yticks(ticks);axes[1].set_yticklabels(rowlabels);axes[1].set_xlim(0,5);axes[1].invert_yaxis();axes[1].set_xlabel('Physics step / 240 (s)');axes[1].grid(axis='x',alpha=.2)
    fig.suptitle('Source gap and SDK feature proximity to requested finite patches')
    fig.text(.5,.025,'Finite-patch projection + signed plane <=2mm + twin-point residual <=1um + raw lambda>0. Not actual face / force N / continuous support.',ha='center',fontsize=8)
    p2=out/'palm_gap_and_patch_features.png';fig.savefig(p2,dpi=170,bbox_inches='tight');plt.close(fig)
    after={p:sha(p) for p in inputs};assert before==after
    (out/'artifact_manifest.json').write_text(json.dumps(dict(input_sha256_before=before,input_sha256_after=after,outputs_sha256={str(p):sha(p) for p in (p1,p2)},producer_sha256=sha(__file__),native_initializations_by_producer=0,physics_steps_by_producer=0,actual_producer='root fallback; agent thread limit reached',scope='actual raw G/body coordinate curves; saved-pose source intervals and near-positive SDK step marks, no support certification'),indent=2)+'\n');print(json.dumps(dict(outputs=[str(p1),str(p2)],input_files=len(inputs))))
if __name__=='__main__':main()
