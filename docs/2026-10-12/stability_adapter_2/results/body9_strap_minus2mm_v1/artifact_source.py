"""Plot recorded guitar errors and submitted cable-law tension for the -2mm trial."""
import hashlib,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'docs/2026-10-12/stability_adapter_2/results';P=B/'body9_strap_minus2mm_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def main():
    analysis=read(P/'analysis.json');inputs=dict(analysis['input_sha256']);inputs[str(P/'analysis.json')]=sha(P/'analysis.json');inputs[str(Path(__file__).resolve())]=sha(__file__);assert all(sha(p)==h for p,h in inputs.items());out=P/'artifacts';out.mkdir(exist_ok=False)
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True);fig.subplots_adjust(left=.12,right=.70,bottom=.13,top=.93,hspace=.32)
    for folder,label,color in [(B/'small_wrist_motion_v1/native','Original rest length','#3d7a9b'),(P/'native','Rest length -2 mm','#b97837')]:
        trace=[json.loads(v) for v in (folder/'trace.jsonl').read_text().splitlines()];time=[r['time_s'] for r in trace]
        for ax,key,mult,y in [(axes[0],'position_error_m',1000,'Initial position error (mm)'),(axes[1],'rotation_error_deg',1,'Initial rotation error (deg)'),(axes[2],'last_applied_tension_n',1,'Submitted cable-law T (N)')]:
            ax.plot(time,[r[key]*mult for r in trace],color=color,label=label);ax.set_ylabel(y)
    for ax in axes:ax.grid(alpha=.2);ax.axvspan(2,5,color='#7ea79a',alpha=.09);ax.legend(loc='upper left',bbox_to_anchor=(1.01,1),fontsize=9)
    axes[-1].set_xlabel('Actual simulation time (s)');fig.suptitle('Same wrist motion, shorter passive strap');fig.text(.5,.045,'Same initial state, PD and wrist trajectory; only passive rest length differs by 2 mm.\nT is the law value submitted before the stored state; not a measured contact force.',ha='center',fontsize=9);image=out/'guitar_errors_and_strap_tension.png';fig.savefig(image,dpi=170);plt.close(fig)
    assert all(sha(p)==h for p,h in inputs.items());(out/'manifest.json').write_text(json.dumps(dict(input_sha256_before=inputs,input_sha256_after={p:sha(p) for p in inputs},outputs_sha256={str(image):sha(image)},native_calls=0,actual_producer='root fallback; Luna thread limit reached'),indent=2)+'\n');print(str(image))
if __name__=='__main__':main()
