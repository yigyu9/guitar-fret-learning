"""Compare real OFF/ON recordings at matched physical time and source goal."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .playing_posture_diagnostic import target_markers
from .live_fret_geometry import position_geometry, pose
from .underneck_initial_search import BASE


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,r):Path(p).write_text(json.dumps(r,indent=2,allow_nan=False)+'\n')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=Path,required=True);args=parser.parse_args()
    phase=args.phase.resolve();out=phase/'analysis';out.mkdir(exist_ok=False)
    controls={}; traces={};summary={}; reports={};checks={};inputs={}
    bodies=read(BASE)['human_body_names'];chest=bodies.index('Chest');pelvis=bodies.index('Pelvis')
    for mode in ('OFF','ON'):
        data=phase/mode/'data';report=read(data/'report.json');reports[mode]=report
        all_controls=read(data/'controls.json');rows=[r for r in all_controls if r['actor_used']];controls[mode]=rows
        traces[mode]=read(data/'trace.json');trace=traces[mode];_,gr0=pose(trace[0]['native_state']['guitar_body_states'][0])
        cz=pose(trace[0]['native_state']['human_body_states'][chest])[0][2]
        for r in trace:r['geometry']=position_geometry(r['native_state']['guitar_body_states'][0],r['native_state']['human_body_states'][pelvis],gr0,cz)
        for r in rows:r['markers'],r['saved_wrist_vector_mm']=target_markers(r['observation'][0])
        terminal=read(data/'terminal_info.json')
        summary[mode]=dict(physics_s=report['recorded_physics_duration_s'],frames=report['frame_count'],actor_steps=report['actor_steps'],
            completed_recording=report['completed_recording'],terminal={k:v for k,v in terminal.items() if k.startswith('episode_')},
            wrist_error_mm_first_last_min_max=[rows[0]['arm_correction']['wrist_error_m']*1000,rows[-1]['arm_correction']['wrist_error_m']*1000,min(r['arm_correction']['wrist_error_m']*1000 for r in rows),max(r['arm_correction']['wrist_error_m']*1000 for r in rows)],
            max_guitar_position_change_mm=max(r['position_change_m'] for r in trace)*1000,
            max_guitar_rotation_deg=max(r['rotation_change_deg'] for r in trace),
            position_box_outside_frames=sum(not r['geometry']['user_position_inside'] for r in trace),
            position_box_max_excess_mm=max(r['geometry']['user_position_box_distance_m'] for r in trace)*1000,
            fit_not_converged_count=sum(not r['arm_correction'].get('fit_success',True) for r in rows))
        checks[mode+'_full_native_recording']=report['completed_recording'] and trace[0]['physics_step']==0 and trace[-1]['physics_step']==report['physics_steps']
        checks[mode+'_all_native_checks']=all(report['checks'].values())
        checks[mode+'_input_preservation']=read(phase/mode/'inputs_after.json')['inputs_unchanged']
        checks[mode+'_wrist_obs_agreement']=max(abs(r['saved_wrist_vector_mm']-r['arm_correction']['wrist_error_m']*1000) for r in rows)<.001
        checks[mode+'_capture_trace_steps']= [r['physics_step'] for r in read(data/'images/capture.json')['frames']]==[r['physics_step'] for r in trace]
        for p in [data/'report.json',data/'trace.json',data/'controls.json',data/'terminal_info.json',data/'initial_values.json',data/'images/capture.json']:
            inputs[str(p)]=sha(p)
    initial_off=read(phase/'OFF/data/initial_values.json');initial_on=read(phase/'ON/data/initial_values.json')
    checks['identical_native_initial_state']=initial_off['native_initial_state']==initial_on['native_initial_state']
    prep_off=[r for r in traces['OFF'] if r['physics_step']<=480];prep_on=[r for r in traces['ON'] if r['physics_step']<=480]
    checks['identical_2s_preparation']= [r['native_state'] for r in prep_off]==[r['native_state'] for r in prep_on]
    original=phase.parents[0]/'fret_fingers_arm_hold_v1/native/data'
    original_controls=read(original/'controls.json');original_trace=read(original/'trace.json')
    checks['OFF_original_controls_exact']=len(original_controls)==len(read(phase/'OFF/data/controls.json')) and all(a['submitted_targets_rad']==b['submitted_targets_rad'] and a.get('actor_action')==b.get('actor_action') and a.get('source_info')==b.get('source_info') for a,b in zip(original_controls,read(phase/'OFF/data/controls.json')))
    checks['OFF_original_native_trace_exact']=len(original_trace)==len(traces['OFF']) and all(a['native_state']==b['native_state'] for a,b in zip(original_trace,traces['OFF']))
    off={round(r['time_s']*240):r for r in controls['OFF']}; matched=[]
    for on in controls['ON']:
        step=round(on['time_s']*240);control=off.get(step)
        if control is not None and on['source_frame_before']==control['source_frame_before']:
            matched.append(dict(time_s=on['time_s'],frame=on['source_frame_before'],
                wrist_OFF_mm=control['arm_correction']['wrist_error_m']*1000,wrist_ON_mm=on['arm_correction']['wrist_error_m']*1000,
                markers_OFF=control['markers'],markers_ON=on['markers']))
    checks['same_goal_comparison_nonempty']=bool(matched)
    differences=[r['wrist_ON_mm']-r['wrist_OFF_mm'] for r in matched]
    summary['matched_goals']=dict(controls=len(matched),first_s=matched[0]['time_s'],last_s=matched[-1]['time_s'],
        mean_wrist_ON_minus_OFF_mm=float(np.mean(differences)),last_wrist_OFF_ON_mm=[matched[-1]['wrist_OFF_mm'],matched[-1]['wrist_ON_mm']])
    idx=[initial_on['joint_names'].index(n) for n in initial_on['control_owners']['prepared_left9']]
    reference=np.array(read(phase/'ON/data/handoff_values.json')['prepared_left_targets_rad'])
    summary['ON_max_target_change_from_handoff_rad']=float(np.max(abs(np.array([r['submitted_targets_rad'] for r in controls['ON']])[:,idx]-reference)))
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True,constrained_layout=True)
    for mode,color in [('OFF','#777777'),('ON','#146bc4')]:
        c=controls[mode];t=traces[mode]
        axes[0].plot([r['time_s'] for r in c],[r['arm_correction']['wrist_error_m']*1000 for r in c],color=color,label=mode)
        axes[1].plot([r['time_s'] for r in t],[r['position_change_m']*1000 for r in t],color=color,label=mode)
        axes[2].plot([r['time_s'] for r in t],[r['rotation_change_deg'] for r in t],color=color,label=mode)
    for ax,label in zip(axes,['Current wrist target error (mm)','Guitar root displacement from t0 (mm)','Guitar rotation from t0 (deg)']):
        ax.set_ylabel(label);ax.axvline(2,color='black',ls='--');ax.grid(alpha=.2);ax.legend()
    axes[0].set_title('Native Isaac Gym / frozen Fret21 / bounded arm9 OFF vs ON\nCurves contain changing source goals; matched-goal comparisons in JSON')
    axes[-1].set_xlabel('Physical time (s)');fig.savefig(out/'timeline.png',dpi=150);plt.close(fig)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',24)
    selected=[];common=min(reports[m]['recorded_physics_duration_s'] for m in reports)
    for tm in (2.,min(3.,common),common):
        for view in ('whole_body','hands'):
            canvas=Image.new('RGB',(2560,790),'#17212e');draw=ImageDraw.Draw(canvas)
            entry={'requested_time_s':tm,'view':view,'frames':{}}
            for panel,mode in enumerate(('OFF','ON')):
                frames=read(phase/mode/'data/images/capture.json')['frames'];i=min(range(len(frames)),key=lambda k:abs(frames[k]['time_s']-tm))
                frame=frames[i];imagepath=phase/mode/'data/images/frames'/view/('%05d.png'%i)
                image=Image.open(imagepath).convert('RGB');canvas.paste(image,(panel*1280,70));draw.text((panel*1280+25,15),f"{mode} | native Isaac Gym | t={frame['time_s']:.3f}s",font=font,fill='white')
                inputs[str(imagepath)]=sha(imagepath);entry['frames'][mode]={'frame':i,'physics_step':frame['physics_step'],'time_s':frame['time_s']}
            path=out/(view+'_'+str(round(tm*240))+'.png');canvas.save(path);entry['path']=str(path);selected.append(entry)
    save(out/'matched_goals.json',matched)
    summary.update(checks=checks,selected=selected,input_sha256=inputs,
        limitations='Raw native videos through first original failure. No learning. Wrist norm/marker distances are not pressure/contact/slip certification; full rotation tolerance membership unassessed. Whole episode lengths differ; matched goal/time only for causal comparisons.')
    checks['analysis_inputs_unchanged']=all(sha(p)==h for p,h in inputs.items())
    save(out/'summary.json',summary);print(json.dumps(dict(checks=checks,OFF=summary['OFF'],ON=summary['ON'],matched=summary['matched_goals']),indent=2))
    if not all(checks.values()):raise AssertionError(checks)


if __name__=='__main__':main()
