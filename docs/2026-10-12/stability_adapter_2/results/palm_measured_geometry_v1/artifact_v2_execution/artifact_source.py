"""Source palm approach/collision tradeoff and conditional scalar-hinge evidence."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT/'docs/2026-10-12/stability_adapter_2/results';PHASE=BASE/'palm_measured_geometry_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    out=PHASE/'artifacts_v2';assert not out.exists();geometry=read(PHASE/'analysis.json');hinge=read(BASE/'palm_single_hinge_pose_v1/analysis.json');inputs=dict(geometry['input_sha256']);inputs.update(hinge['input_sha256'])
    for p in [Path(__file__).resolve(),PHASE/'analysis.json',BASE/'palm_single_hinge_pose_v1/analysis.json']:inputs[str(p)]=sha(p)
    before={p:sha(p) for p in inputs};assert before==inputs;out.mkdir();fig,axes=plt.subplots(2,1,figsize=(11,7),sharex=True);fig.subplots_adjust(left=.1,right=.73,bottom=.14,top=.91,hspace=.3)
    for step,color in zip((0,24,120,1200),('#347ba6','#df914d','#79559a','#378574')):
        rows=sorted((r for r in geometry['rows'] if r['physics_step']==step),key=lambda r:r['fraction']);fraction=[r['fraction'] for r in rows];label=str(step/240)+' s saved pose';axes[0].plot(fraction,[r['palm_finite_patch_interval']['distance_m']*1000 for r in rows],'.-',color=color,label=label);axes[1].plot(fraction,[max([v['increase_m']*1000 for v in r['new_or_increased_source_intersections'] if v['kind']=='human_guitar' and v['a'] in ('LH:index3','LH:middle3')]+[0.]) for r in rows],'.-',color=color,label=label)
    for ax,y in zip(axes,('Palm patch gap upper (mm)','Finger radius increase (mm)')):ax.set_ylabel(y);ax.grid(alpha=.2);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=8)
    axes[-1].set_xlabel('Fraction of geometric arm12 dq (unexecuted)');fig.suptitle('Palm-only approach increases finger / guitar source overlap');fig.text(.5,.025,'Source convex common insphere radius, not native penetration depth/contact force. Actual measured finger poses held relative to palm; G fixed in this query.',ha='center',fontsize=8);p1=out/'palm_gap_and_finger_overlap.png';fig.savefig(p1,dpi=170,bbox_inches='tight');plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,5));fig.subplots_adjust(left=.09,right=.97,bottom=.24,top=.86,wspace=.35);rows=hinge['summary'];names=[r['body'][3:] for r in rows]
    for ax,key,mult,threshold,y in [(axes[0],'max_position_error_mm',1000,100,'Conditional child origin error (um)'),(axes[1],'max_rotation_error_rad',1e6,1000,'Conditional child rotation error (urad)')]:
        ax.bar(names,[r[key]*mult for r in rows],color='#347ba6');ax.axhline(threshold,color='#a74242',ls='--',label='Unchanged check bound');ax.set_yscale('log');ax.set_ylabel(y);ax.tick_params(axis='x',rotation=35);ax.grid(axis='y',alpha=.2);ax.legend(fontsize=8)
    fig.suptitle('Six scalar hinges: measured native parent supplied, t0 relative calibration only');fig.text(.5,.04,'24 saved frames per hinge / 144 rows. Conditional joint relation, not whole-hand FK or PD/contact/physical grip certification; no new native run.',ha='center',fontsize=8);p2=out/'conditional_single_hinge_errors.png';fig.savefig(p2,dpi=170,bbox_inches='tight');plt.close(fig)
    after={p:sha(p) for p in inputs};assert before==after;(out/'manifest.json').write_text(json.dumps(dict(input_sha256_before=before,input_sha256_after=after,outputs_sha256={str(p):sha(p) for p in (p1,p2)},producer_sha256=sha(__file__),native_calls=0,actual_producer='Sol/root fallback; agent thread limit reached',scope='source LP/witness and conditional actual-parent scalar hinge errors; not new Gym renders or physical controller trial'),indent=2)+'\n');print(json.dumps(dict(outputs=[str(p1),str(p2)])))
if __name__=='__main__':main()
