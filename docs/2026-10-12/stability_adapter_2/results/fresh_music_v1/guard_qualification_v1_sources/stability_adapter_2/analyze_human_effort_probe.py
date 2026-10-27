"""Compare saved native ON/OFF response, without simulator or measured-torque claims."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--phase',type=Path,required=True);parser.add_argument('--out',type=Path,required=True);args=parser.parse_args()
    phase=args.phase.resolve();out=args.out.resolve();out.mkdir(parents=True,exist_ok=False)
    paths=[Path(__file__).resolve()]+[phase/name/'data'/file for name in ('off','on') for file in ('states.json','commands.json','report.json','initial_values.json','native_EFFORT_PD_properties.json','mass_matrix_initial.json')]+[phase/name/'inputs_after.json' for name in ('off','on')]
    hashes={str(p):sha(p) for p in paths};(out/'inputs_before.json').write_text(json.dumps({'sha256':hashes},indent=2)+'\n')
    off,on=[read(phase/name/'data/states.json') for name in ('off','on')]
    a,b=[read(phase/name/'data/initial_values.json') for name in ('off','on')]
    assert a['native_initial_state']==b['native_initial_state'] and a['PD_properties']==b['PD_properties'] and a['requested_targets_rad']==b['requested_targets_rad']
    assert a['original_PD_properties']==b['original_PD_properties']
    native_props=[read(phase/name/'data/native_EFFORT_PD_properties.json') for name in ('off','on')]
    assert native_props[0]==native_props[1]==a['PD_properties']
    masses=[read(phase/name/'data/mass_matrix_initial.json') for name in ('off','on')]
    assert masses[0]==masses[1] and masses[0]['shape']==[1,81,81] and np.isfinite(masses[0]['matrix']).all()
    for name in ('off','on'):
        report=read(phase/name/'data/report.json');assert report['completed_5s'] and all(report['checks'].values())
        assert read(phase/name/'inputs_after.json')['inputs_unchanged']
    assert len(off)==len(on) and [s['physics_step'] for s in off]==[s['physics_step'] for s in on]
    rows=[];j=a['joint_names'].index(a['stepped_joint']);maximum=0.
    for x,y in zip(off,on):
        u,v=x['native_state'],y['native_state'];qo=np.array([[r['pos'],r['vel']] for r in u['human_dof_states']]);qn=np.array([[r['pos'],r['vel']] for r in v['human_dof_states']]);delta=qn-qo;maximum=max(maximum,float(abs(delta[:,0]).max()))
        rows.append({'physics_step':x['physics_step'],'time_s':x['physics_step']/240,'all_native_state_exact':u==v,'max_dof_angle_difference_rad':float(abs(delta[:,0]).max()),'max_dof_velocity_difference_rad_s':float(abs(delta[:,1]).max()),'step_joint_on_minus_off_angle_rad':float(delta[j,0]),'step_joint_on_minus_off_velocity_rad_s':float(delta[j,1])})
    commands=[read(phase/name/'data/commands.json') for name in ('off','on')]
    first=[c[0]['requested_human_joint_torque_Nm'][j] for c in commands]
    exact=all(r['all_native_state_exact'] for r in rows)
    result={'initial_states_PD_targets_exact':True,'native_EFFORT_properties_exact':True,'initial_mass_matrices_exact':True,'mass_matrix_shape':masses[0]['shape'],'mass_max_asymmetry':masses[0]['max_asymmetry'],'sample_count':len(rows),'all_native_states_exact':exact,'maximum_joint_angle_difference_rad':maximum,'initial_requested_step_rad':a['requested_step_rad'],'first_requested_step_joint_torque_OFF_ON_Nm':first,'first_four_step_comparison':next(r for r in rows if r['physics_step']==4),'rows':rows,'interpretation':'No native response evidence for four-frame EFFORT tensor actuation in this probe.' if exact else 'Native ON/OFF response differs; verify sign and scale before adopting any controller.','music_success':False,'scope':'saved physical state response comparison; requested commands are not measured joint torques'}
    (out/'summary.json').write_text(json.dumps(result,indent=2)+'\n')
    changed=[p for p,h in hashes.items() if sha(Path(p))!=h];(out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n');assert not changed
    print({k:v for k,v in result.items() if k!='rows'})


if __name__=='__main__':main()
