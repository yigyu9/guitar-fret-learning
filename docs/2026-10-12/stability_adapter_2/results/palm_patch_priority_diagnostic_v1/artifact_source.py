"""Scientific figures for actual palm-priority trial and exact early motion decomposition."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'palm_patch_priority_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=PHASE/'artifacts';assert not out.exists()
    analysis=read(PHASE/'analysis.json');early=read(PHASE/'early_motion_audit.json');baseline=read(BASE/'three_face_near_contact_diagnostic_v1/analysis_v2.json');source=read(BASE/'palm_patch_priority_initial_v1/proposal.json')
    inputs=dict(analysis['input_sha256']);inputs.update(early['input_sha256']);inputs.update(baseline['input_sha256']);inputs.update(source['input_sha256'])
    for p in [Path(__file__).resolve(),PHASE/'analysis.json',PHASE/'early_motion_audit.json',BASE/'three_face_near_contact_diagnostic_v1/analysis_v2.json',BASE/'palm_patch_priority_initial_v1/proposal.json']:inputs[str(p)]=sha(p)
    before={p:sha(p) for p in inputs};assert before==inputs;out.mkdir()
    fig,axes=plt.subplots(3,1,figsize=(11,10),sharex=True);fig.subplots_adjust(left=.09,right=.72,bottom=.12,top=.93,hspace=.27)
    curves=[baseline['curves']['original_targets'],analysis['curves']['palm_wide_near17']]
    for color,label,curve in zip(['#347ba6','#df914d'],['Stored previous initial pose','New palm-priority initial pose'],curves):
        for ax,key in zip(axes[:2],['position_error_mm','rotation_error_deg']):ax.plot(curve['time_s'],curve[key],color=color,label=label)
    samples=early['samples'];t=[r['time_s'] for r in samples];upper=[r['source_palm_patch_interval']['distance_m']*1000 for r in samples];lower=[r['source_palm_patch_interval']['distance_lower_bound_m']*1000 for r in samples]
    axes[2].plot(t,upper,'o-',color='#6d5197',label='New palm source finite-patch gap upper');axes[2].fill_between(t,lower,upper,color='#6d5197',alpha=.2)
    axes[2].axvline(early['first_positive_palm_body_step']/240,color='#a74242',ls='--',label='First palm-body positive raw lambda')
    for ax,y in zip(axes,['World guitar position error (mm)','World guitar rotation error (deg)','Source palm-patch gap (mm)']):ax.set_ylabel(y);ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.015,1),fontsize=8)
    axes[-1].set_xlabel('Actual simulation time (s)');fig.suptitle('Preserved old81 targets / same strap: new initialleft33 pose')
    fig.text(.5,.025,'Stored baseline, one fresh native5s. Source gap is not cooked clearance; no requested palm-patch feature was observed.',ha='center',fontsize=9)
    p1=out/'actual_G_and_palm_gap.png';fig.savefig(p1,dpi=170,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True);fig.subplots_adjust(left=.1,right=.73,bottom=.14,top=.93,hspace=.22)
    for component,ax in enumerate(axes):
        for key,label,color,style in [('Chest_pose_contribution_W_mm','Chest pose contribution','#347ba6','-'),('arm_chain_contribution_W_mm','Arm-chain relative contribution','#df914d','-'),('world_anchor_delta_mm','Actual world point displacement','#555555','--')]:ax.plot(t,[r[key][component] for r in samples],style,marker='o',color=color,label=label)
        ax.set_ylabel('World '+ 'XYZ'[component]+' displacement (mm)');ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.015,1),fontsize=8)
    axes[-1].set_xlabel('Actual simulation time (s)');fig.suptitle('Source palm anchor: exact vector decomposition of actual saved native poses')
    fig.text(.5,.03,'Per axis: Chest contribution + arm-chain contribution = actual displacement. Vector norms are not additive; not a causal ablation.',ha='center',fontsize=8)
    p2=out/'early_Chest_arm_vectors.png';fig.savefig(p2,dpi=170,bbox_inches='tight');plt.close(fig)
    after={p:sha(p) for p in inputs};assert before==after
    (out/'artifact_manifest.json').write_text(json.dumps(dict(input_sha256_before=before,input_sha256_after=after,outputs_sha256={str(p):sha(p) for p in (p1,p2)},producer_sha256=sha(__file__),native_initializations_by_producer=0,physics_steps_by_producer=0,actual_producer='root fallback; agent thread limit reached',scope='raw actual G/source hull gap and exact saved-body vector decomposition; not source collision mesh certification or stable grip'),indent=2)+'\n')
    print(json.dumps(dict(outputs=[str(p1),str(p2)],inputs=len(inputs))))
if __name__=='__main__':main()
