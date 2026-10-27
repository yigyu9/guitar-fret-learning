"""Plot actual recorded small-wrist response and guitar errors, with sealed inputs."""
import hashlib,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[1];B=ROOT/'docs/2026-10-12/stability_adapter_2/results';P=B/'small_wrist_motion_v1'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def lines(p):return [json.loads(v) for v in Path(p).read_text().splitlines()]
def main():
    analysis=read(P/'analysis.json');inputs=dict(analysis['input_sha256']);inputs[str(P/'analysis.json')]=sha(P/'analysis.json');inputs[str(Path(__file__).resolve())]=sha(__file__);assert all(sha(p)==h for p,h in inputs.items());out=P/'artifacts';out.mkdir(exist_ok=False)
    old=B/'torso_hold_native_collision_v1/native';new=P/'native';t0=lines(old/'trace.jsonl');t1=lines(new/'trace.jsonl');s0=lines(old/'states.jsonl');s1=lines(new/'states.jsonl');controls=lines(new/'controls.jsonl');i=read(new/'initial_values.json');k=i['human_joint_names'].index('L_Wrist_x');time=np.array([r['time_s'] for r in t1]);actual=np.array([a['human_dof_states'][k]['pos']-b['human_dof_states'][k]['pos'] for a,b in zip(s1,s0)]);command=np.array([0.]+[r['wrist_motion_delta_rad'] for r in controls])
    fig,axes=plt.subplots(3,1,figsize=(9,8),sharex=True);fig.subplots_adjust(left=.13,right=.97,bottom=.13,top=.93,hspace=.32)
    axes[0].plot(time,np.degrees(command),color='#b97837',label='Submitted goal delta');axes[0].plot(time,np.degrees(actual),color='#3d7a9b',label='Actual q minus static q');axes[0].set_ylabel('Wrist coordinate (deg)')
    for ax,key,mult,label in ((axes[1],'position_error_m',1000,'Initial position error (mm)'),(axes[2],'rotation_error_deg',1,'Initial rotation error (deg)')):
        ax.plot(time,[r[key]*mult for r in t0],color='#3d7a9b',label='Static baseline');ax.plot(time,[r[key]*mult for r in t1],color='#b97837',label='Small wrist motion');ax.set_ylabel(label)
    for ax in axes:ax.grid(alpha=.2);ax.axvspan(2,5,color='#7ea79a',alpha=.09);ax.legend(loc='best',fontsize=9)
    axes[-1].set_xlabel('Actual simulation time (s)');fig.suptitle('Small left-wrist motion on a quiet-hold baseline');fig.text(.5,.045,'One actual 5 s trial; same initial pose, strap and PD. Goal amplitude 0.005 rad at 1 Hz.\nTop: scalar coordinate response relative to matched static states; no bone-rotation equivalence.',ha='center',fontsize=9);output=out/'wrist_motion_and_guitar_errors.png';fig.savefig(output,dpi=170);plt.close(fig)
    assert all(sha(p)==h for p,h in inputs.items());(out/'manifest.json').write_text(json.dumps(dict(input_sha256_before=inputs,input_sha256_after={p:sha(p) for p in inputs},outputs_sha256={str(output):sha(output)},actual_producer='root fallback; Luna agent thread limit reached',native_calls=0),indent=2)+'\n');print(str(output))
if __name__=='__main__':main()
