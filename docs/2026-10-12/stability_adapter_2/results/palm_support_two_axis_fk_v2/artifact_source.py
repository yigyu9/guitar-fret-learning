"""Scientific FK-model discrepancy and source palm derivative figures; no physics."""
import json,hashlib
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';PHASE=BASE/'palm_support_two_axis_fk_v2'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=PHASE/'artifacts';assert not out.exists();d=read(PHASE/'analysis.json');p=read(BASE/'palm_support_runtime_fk_v1/analysis.json');scope=read(PHASE/'palm_scope_assessment.json');inputs=dict(d['input_sha256']);inputs.update(p['input_sha256']);inputs.update(scope['input_sha256'])
    for f in [Path(__file__).resolve(),PHASE/'analysis.json',PHASE/'palm_scope_assessment.json',BASE/'palm_support_runtime_fk_v1/analysis.json']:inputs[str(f)]=sha(f)
    before={f:sha(f) for f in inputs};assert before==inputs;out.mkdir();fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True);fig.subplots_adjust(left=.11,right=.74,bottom=.14,top=.91,hspace=.3)
    for mode,color,label in [('exp_sum','#347ba6','exp(sum)'),('xml_product','#b67640','XML-order product'),('reverse_product','#79559a','Reverse product'),('tangent_half','#378574','Tangent-half quaternion')]:
        rows=sorted((r for r in d['rows'] if r['mode']==mode),key=lambda r:r['physics_step']);t=[r['physics_step']/240 for r in rows]
        axes[0].plot(t,[r['max_position_error_mm'] for r in rows],'.-',color=color,label=label);axes[1].plot(t,[r['max_rotation_error_rad']*1000 for r in rows],'.-',color=color,label=label)
    for ax,threshold,y in zip(axes,[.1,1.],['Max left-chain origin error (mm)','Max left-chain rotation error (mrad)']):ax.axhline(threshold,color='#9e3434',ls='--',label='Unchanged FK check bound');ax.set_ylabel(y);ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    axes[-1].set_xlabel('Saved actual state time (s)');fig.suptitle('Four two-coordinate rotation hypotheses: all whole-hand checks failed');fig.text(.5,.025,'Same t0-only calibration and 4 diagnostic + 20 heldout saved frames. Lines connect samples; no new native run.',ha='center',fontsize=8);p1=out/'whole_hand_FK_hypotheses.png';fig.savefig(p1,dpi=170,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,1,figsize=(11,7));fig.subplots_adjust(left=.1,right=.88,bottom=.19,top=.9,hspace=.6)
    J=np.array(p['samples'][-1]['position_J_W_m_per_rad'])*1000;limit=np.abs(J).max();im=axes[0].imshow(J,cmap='coolwarm',vmin=-limit,vmax=limit,aspect='auto');axes[0].set_yticks(range(3));axes[0].set_yticklabels(['World X','World Y','World Z']);axes[0].set_xticks(range(12));short=[n.replace('L_','') for n in p['arm_joint_names']];axes[0].set_xticklabels(short,rotation=40,ha='right',fontsize=8);fig.colorbar(im,ax=axes[0],label='Source palm derivative (mm/rad)')
    for r,color in zip(p['samples'],['#347ba6','#df914d','#79559a','#378574']):axes[1].plot(range(12),[r['geometric_dq_rad'][n] for n in p['arm_joint_names']],'.-',color=color,label=str(r['time_s'])+' s')
    axes[1].axhline(.05,color='#555555',ls='--');axes[1].axhline(-.05,color='#555555',ls='--');axes[1].set_xticks(range(12));axes[1].set_xticklabels(short,rotation=40,ha='right',fontsize=8);axes[1].set_ylabel('Geometric angle proposal (rad)');axes[1].grid(alpha=.2);axes[1].legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    fig.suptitle('Accurate palm subchain: source derivative and unexecuted angle proposal');fig.text(.5,.025,'Palm/arm scope only. Finger FK still failed. Proposed dq is not a submitted PD target or native motion/contact certificate.',ha='center',fontsize=8);p2=out/'palm_J_and_geometric_proposals.png';fig.savefig(p2,dpi=170,bbox_inches='tight');plt.close(fig)
    after={f:sha(f) for f in inputs};assert before==after;(out/'manifest.json').write_text(json.dumps(dict(input_sha256_before=before,input_sha256_after=after,outputs_sha256={str(f):sha(f) for f in (p1,p2)},producer_sha256=sha(__file__),native_calls=0,actual_producer='Sol/root fallback; agent thread limit reached',scope='source FK errors and derivative/angle proposal only; not Isaac Gym render/new physical trial/stability success'),indent=2)+'\n');print(json.dumps(dict(outputs=[str(p1),str(p2)])))
if __name__=='__main__':main()
