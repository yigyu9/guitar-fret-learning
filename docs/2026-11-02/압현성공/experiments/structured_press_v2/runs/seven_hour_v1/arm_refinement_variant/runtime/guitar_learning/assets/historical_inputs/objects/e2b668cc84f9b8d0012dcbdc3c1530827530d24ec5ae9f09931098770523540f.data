"""Compare completed native runs; plot measured contacts and guitar motion."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PIL import Image,ImageDraw,ImageFont


def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=Path,required=True)
    args=parser.parse_args();phase=args.phase.resolve();out=phase/'analysis_posture_retry';out.mkdir(exist_ok=False)
    runs=['baseline_v4','candidate_off','candidate_on','posture_on_retry'];paths={Path(__file__).resolve()}
    root=Path(__file__).resolve().parents[1]
    paths.update(p for p in (root/'stability_adapter_2').glob('*.py'))
    paths.update(p for p in (root/'stability_adapter_2').glob('*.md'))
    paths.add(Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    for name in runs:
        paths.add(phase/name/'inputs_after.json')
        paths.update(p for p in (phase/name/'data').rglob('*') if p.suffix in ('.json','.png'))
    hashes={str(p):sha(p) for p in sorted(paths)}
    (out/'inputs_before.json').write_text(json.dumps(hashes,indent=2)+'\n')
    for p in paths:
        if p.parent==root/'stability_adapter_2':
            dst=out/'source_before'/p.relative_to(root);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    results={};traces={};contact_curves={}
    for name in runs:
        data=phase/name/'data';report=read(data/'report.json')
        if not report['completed_5s']:raise ValueError('comparison requires complete 5s '+name)
        if not read(phase/name/'inputs_after.json')['inputs_unchanged']:raise ValueError('native consumed input changed '+name)
        trace=read(data/'trace.json');contacts=read(data/'contacts.json');initial=read(data/'initial_values.json')
        flags=[];palm_features=[];thumb_features=[]
        for row in contacts:
            palm=[];thumb=[]
            for c in row['contacts']:
                pair={c['body0_name'],c['body1_name']}
                if 'guitar/guitar' not in pair:continue
                if 'human/LH:palm' in pair:palm.append(c)
                elif any(n.startswith('human/LH:thumb') for n in pair):thumb.append(c)
            palm_positive=any(c['lambda']>0 for c in palm);thumb_positive=any(c['lambda']>0 for c in thumb)
            flags.append([row['time_s'],bool(palm),bool(thumb),palm_positive,thumb_positive,palm_positive and thumb_positive])
            for group,dest in ((palm,palm_features),(thumb,thumb_features)):
                for c in group:
                    if c['lambda']>0:
                        local=c['localPos0'] if c['body0_name']=='guitar/guitar' else c['localPos1']
                        dest.append([local[a] for a in 'xyz'])
        flags=np.asarray(flags,dtype=float);count=len(flags);traces[name]=trace;contact_curves[name]=flags
        names=initial['human_body_names'];chest_z=initial['native_initial_state']['human_body_states'][names.index('Chest')]['pose']['p']['z']
        p=np.array([r['position_W_m'] for r in trace]);low=np.array([-.5,-.15,.65]);high=np.array([-.15,.15,chest_z])
        excess=np.maximum(np.maximum(low-p,p-high),0)
        rows=dict(physics_steps=report['physics_steps'],duration_s=report['recorded_physics_duration_s'],
            frame_count=report['frame_count'],contact_steps=count,
            palm_pair_steps=int(flags[:,1].sum()),thumb_pair_steps=int(flags[:,2].sum()),
            palm_positive_raw_lambda_steps=int(flags[:,3].sum()),thumb_positive_raw_lambda_steps=int(flags[:,4].sum()),
            simultaneous_positive_raw_lambda_steps=int(flags[:,5].sum()),
            simultaneous_positive_fraction=float(flags[:,5].mean()),
            palm_min_up=float(min(r['palm_normal_up'] for r in contacts)),
            max_actor_root_displacement_mm=max(r['position_change_m'] for r in trace)*1000,
            final_actor_root_displacement_mm=trace[-1]['position_change_m']*1000,
            max_shortest_rotation_deg=max(r['rotation_change_deg'] for r in trace),
            final_shortest_rotation_deg=trace[-1]['rotation_change_deg'],
            position_box_max_excess_mm=float(excess.max()*1000),position_box_outside_frames=int(np.any(excess>1e-6,axis=1).sum()),
            original_position_box_W_m=dict(lower=low.tolist(),upper=high.tolist()),
            source_surface_gaps_mm={k:v['minimum_distance_m']*1000 for k,v in read(data/'initial_audit.json')['surface_gaps'].items()},
            native_checks=report['checks'],inputs_unchanged=read(phase/name/'inputs_after.json')['inputs_unchanged'])
        for label,features in (('palm',palm_features),('thumb',thumb_features)):
            rows[label+'_positive_contact_feature_local_G_bounds_m']=dict(min=np.min(features,axis=0).tolist(),max=np.max(features,axis=0).tolist()) if features else None
        results[name]=rows
    b=results[runs[0]]; eligible=[]
    for name in runs[1:]:
        n=results[name]
        if (n['simultaneous_positive_raw_lambda_steps']>b['simultaneous_positive_raw_lambda_steps'] and
            n['max_actor_root_displacement_mm']<b['max_actor_root_displacement_mm'] and
            n['max_shortest_rotation_deg']<b['max_shortest_rotation_deg']): eligible.append(name)
    winner=min(eligible,key=lambda name:results[name]['max_actor_root_displacement_mm']/b['max_actor_root_displacement_mm']+
               results[name]['max_shortest_rotation_deg']/b['max_shortest_rotation_deg']) if eligible else None
    stage3=winner is not None
    summary=dict(runs=results,fret_gate_passed=stage3,fret_candidate_condition=winner,scope='actual native 60Hz control-before-step pair/raw-solver response; extrema from 30Hz pose/60Hz contact samples; no force-unit conversion or friction/slip certification',
        rotation_scope='shortest rotation from initial quaternion, not full natural-pose membership',
        position_scope='actor-root historical world box; not team pelvis-relative body-centre bounds')
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    fig,axes=plt.subplots(3,1,figsize=(10,8),sharex=True)
    for name in runs:
        trace=traces[name];t=[r['time_s'] for r in trace]
        axes[0].plot(t,[r['position_change_m']*1000 for r in trace],label=name)
        axes[1].plot(t,[r['rotation_change_deg'] for r in trace],label=name)
        flags=contact_curves[name]
        # Per-second fraction includes all 60Hz samples, not selected frames.
        bins=np.arange(0,5.0001,.25);fraction=[]
        for a,z in zip(bins[:-1],bins[1:]):
            mask=(flags[:,0]>=a)&(flags[:,0]<z);fraction.append(float(flags[mask,5].mean()))
        axes[2].stairs(fraction,bins,label=name)
    for ax,label in zip(axes,['Guitar actor-root displacement (mm)','Shortest rotation from initial (deg)','Palm + thumb positive raw response fraction']):
        ax.set_ylabel(label);ax.grid(alpha=.25);ax.legend(loc='best')
    axes[2].set_xlabel('Actual simulation time (s)');axes[2].set_ylim(-.05,1.05)
    fig.tight_layout();fig.savefig(out/'timeline.png',dpi=160);plt.close(fig)
    font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
    # Resize uniformly, preserving the native 16:9 ratio.
    for view in ('hands','whole_body'):
        for idx in (0,60,150):
            canvas=Image.new('RGB',(960,len(runs)*(540+36)),'white');draw=ImageDraw.Draw(canvas)
            for j,name in enumerate(runs):
                im=Image.open(phase/name/'data/images/frames'/view/('%05d.png'%idx)).convert('RGB').resize((960,540));y=j*576
                canvas.paste(im,(0,y+36));draw.text((10,y+6),name+' | native Isaac Gym | t='+str(idx/30)+' s',fill='black',font=font)
            canvas.save(out/(view+'_t'+str(idx//30)+'.png'))
    changed=[p for p,h in hashes.items() if sha(Path(p))!=h]
    checks=dict(inputs_unchanged=not changed,four_complete_1200_step_runs=all(r['physics_steps']==1200 for r in results.values()),
                all_60Hz_contacts=all(r['contact_steps']==300 for r in results.values()),
                all_native_checks=all(all(r['native_checks'].values()) for r in results.values()),
                native_consumed_inputs_unchanged=all(r['inputs_unchanged'] for r in results.values()),
                frame_count_151=all(r['frame_count']==151 for r in results.values()))
    (out/'inputs_after.json').write_text(json.dumps(dict(checks=checks,changed=changed,input_count=len(hashes)),indent=2)+'\n')
    assert all(checks.values()),checks
    print(json.dumps(summary,indent=2))


if __name__=='__main__':main()
