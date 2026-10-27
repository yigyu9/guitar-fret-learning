"""Plot recorded native motion, frames and failed source searches; no simulation."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results'
PHASE=BASE/'three_face_near_contact_diagnostic_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=PHASE/'artifacts';assert not out.exists()
    analysis=read(PHASE/'analysis_v2.json');assert all(analysis['checks'].values())
    inputs=dict(analysis['input_sha256']);inputs[str(PHASE/'analysis_v2.json')]=sha(PHASE/'analysis_v2.json');inputs[str(Path(__file__).resolve())]=sha(__file__)
    data=[]
    for name in ('three_face_wider_hand_initial_v1','three_face_support_plane_initial_v1'):
        p=BASE/name/'proposal.json';d=read(p);assert not d['rows'] and d['native_initializations']==d['physics_steps']==0
        inputs[str(p)]=sha(p);inputs.update(d['input_sha256']);data.extend(d['rejected'])
    before={p:sha(p) for p in inputs};assert before==inputs;out.mkdir()
    colors=['#347ba6','#df914d']
    fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True);fig.subplots_adjust(left=.09,right=.73,bottom=.16,top=.9,hspace=.25)
    for color,r in zip(colors,analysis['summary']):
        curve=analysis['curves'][r['label']]
        for ax,key in zip(axes,('position_error_mm','rotation_error_deg')):ax.plot(curve['time_s'],curve[key],color=color,label=r['label'].replace('_',' '),linewidth=1.7)
    for ax,yl in zip(axes,('Guitar world position error (mm)','Guitar world rotation error (deg)')):
        ax.set_ylabel(yl);ax.grid(alpha=.22);ax.legend(loc='upper left',bbox_to_anchor=(1.02,1),fontsize=8)
    axes[-1].set_xlabel('Actual continuous simulation time (s)');fig.suptitle('Same initial81 / strap / arm targets: left finger21 target comparison')
    fig.text(.5,.035,'Raw recorded Gym trace, 240Hz physics. Source support gates remain unmet; neither run is certified stable grip.',ha='center',fontsize=9)
    curvefile=out/'native_guitar_motion.png';fig.savefig(curvefile,dpi=170,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(2,2,figsize=(14,9));fig.subplots_adjust(left=.01,right=.99,bottom=.09,top=.91,hspace=.17,wspace=.03)
    selected=[]
    for row,label in enumerate(('original_targets','initial_finger_targets')):
        for col,frame in enumerate((0,150)):
            p=PHASE/'native'/label/'frames/hands'/f'{frame:05d}.png';assert str(p) in inputs
            axes[row,col].imshow(plt.imread(p));axes[row,col].axis('off');axes[row,col].set_title(f'{label.replace("_"," ")} | actual t={frame/30:.1f}s',fontsize=11);selected.append(str(p))
    fig.suptitle('Actual Isaac Gym native hands-camera frames; no pose replay',fontsize=15)
    fig.text(.5,.03,'Green = left hand; magenta = right hand; blue = guitar. Visible proximity does not certify face contact or penetration.',ha='center',fontsize=10)
    framefile=out/'native_initial_and_end.png';fig.savefig(framefile,dpi=150,bbox_inches='tight');plt.close(fig)
    x=np.arange(len(data));fig,axes=plt.subplots(2,1,figsize=(15,9),sharex=True);fig.subplots_adjust(left=.065,right=.8,bottom=.2,top=.9,hspace=.24)
    for ax,body,color in zip(axes,('LH:thumb3','LH:palm'),colors):
        vals=[r['anchor_goal_error_mm'][body] for r in data];ax.bar(x,vals,color=color)
        ax.set_ylabel(body+' source point error (mm)');ax.axvline(11.5,color='#666',linestyle='--');ax.grid(axis='y',alpha=.2)
        for i,v in enumerate(vals):ax.text(i,v+max(vals)*.025,f'{v:.2f}',ha='center',fontsize=7)
        ax.set_ylim(0,max(vals)*1.23)
    axes[0].set_title('Wide left33: 12 candidates | whole-tip support-plane: 3 candidates (all source support rejected)')
    axes[1].set_xticks(x);axes[1].set_xticklabels([r['label'] for r in data],rotation=45,ha='right',fontsize=8)
    fig.text(.82,.72,'Each search:\narm12 +/-0.15rad\nfingers21 +/-0.3rad\nother48 held\nold absolute81 targets\n\nBounds intersect native/\nAug19/C02/target limits.',fontsize=9)
    fig.text(.5,.045,'Source proxy errors, not contact points or guitar drift. Nonidentical starts and objectives: not a causal ablation.',ha='center',fontsize=10)
    sourcefile=out/'source_fifteen_candidates.png';fig.savefig(sourcefile,dpi=170,bbox_inches='tight');plt.close(fig)
    after={p:sha(p) for p in inputs};assert before==after
    (out/'artifact_manifest.json').write_text(json.dumps(dict(input_sha256_before=before,input_sha256_after=after,outputs_sha256={str(p):sha(p) for p in (curvefile,framefile,sourcefile)},selected_native_frames=selected,source_candidates=15,native_initializations_by_producer=0,physics_steps_by_producer=0,producer_sha256=sha(__file__),actual_producer_role='root; Luna delegation unavailable: agent thread limit reached',scope='raw native motion/unaltered camera frame scientific figures plus source failed search; not certified face support/cooked penetration/stability'),indent=2)+'\n')
    print(json.dumps(dict(outputs=[str(p) for p in (curvefile,framefile,sourcefile)],inputs=len(inputs))))
if __name__=='__main__':main()
