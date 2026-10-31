"""Summarize saved native properties and total DOF-force observations."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/palm_hold_observation_v1'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())


def main():
    if (PHASE/'analysis.json').exists():raise FileExistsError('preserve previous analysis')
    observations={};hashes={};labels=('baseline','full')
    for label in labels:
        p=PHASE/label/'observation.json';hashes[str(p)]=sha(p);observations[label]=read(p)
    paths=[Path(p) for a in observations.values() for p in a['input_sha256']]+[Path(__file__).resolve(),PHASE/'execution.json',PHASE/'environment.json']
    paths += [PHASE/label/'native'/(n+'.json') for label in labels for n in ('report','states','trace','tasks','contacts','controls')]
    hashes.update({str(p):sha(p) for p in paths});summary=[];curves={};all_properties=[]
    for label in labels:
        a=observations[label];props=a['properties'];folder=PHASE/label/'native';raw={n:read(folder/(n+'.json')) for n in ('report','states','trace','tasks','contacts','controls')};r=raw['report']
        if any(sha(p)!=h for p,h in a['input_sha256'].items()) or not all(a['checks'].values()) or a['physics_steps']!=24 or a['native_initializations']!=1:raise AssertionError('observation contracts')
        if a['t0_force_measurement'] is not None or len(a['samples'])!=24 or any(v['physics_step']!=i+1 or abs(v['time_s']-(i+1)/240)>1e-9 for i,v in enumerate(a['samples'])):raise AssertionError('sensor coverage/time')
        if r['failure'] or not all(r['checks'].values()) or len(raw['states'])!=25 or len(raw['trace'])!=25 or len(raw['controls'])!=24:raise AssertionError('native coverage')
        if any(raw[n]!=read(Path(a['reference_run'])/(n+'.json')) for n in ('states','trace','tasks','contacts','controls')):raise AssertionError('reference arrays')
        if props['human_joint_names']!=r['human_joint_names'] or len(props['human_joint_names'])!=81 or any(u!='Nm' for u in props['native_DOF_units']):raise AssertionError('rotational layout')
        arm=r['arm_indices'];target=raw['controls'][0]['final_target_rad']
        if any(v['final_target_rad']!=target for v in raw['controls']):raise AssertionError('constant submitted target')
        stats=[];joint_curves={}
        for j,i in enumerate(arm):
            forces=[s['native_total_DOF_force'][i] for s in a['samples']];position=[s['human_dof_states'][i]['pos'] for s in raw['states']];velocity=[s['human_dof_states'][i]['vel'] for s in raw['states']];errors=[q-target[j] for q in position];name=r['human_joint_names'][i]
            joint_curves[name]={'native_coordinate_error_rad':errors,'native_velocity_rad_s':velocity,'total_DOF_force_Nm':forces}
            stats.append({'name':name,'kp':props['drive_properties']['stiffness'][i],'kd':props['drive_properties']['damping'][i],'effort_property':props['drive_properties']['effort'][i],
                'force_min_Nm':min(forces),'force_max_Nm':max(forces),'force_end_Nm':forces[-1],'terminal_native_coordinate_error_rad':errors[-1],'terminal_native_velocity_rad_s':velocity[-1]})
        summary.append({'label':label,'left_arm_stats':stats,'max_guitar_position_error_mm':max(t['position_error_m'] for t in raw['trace'])*1000,
            'max_guitar_rotation_error_deg':max(t['rotation_error_deg'] for t in raw['trace']),'end_point_error_mm':sum(v*v for v in raw['tasks'][-1][:3])**.5*1000,'nonzero_force_samples':a['nonzero_force_samples']})
        curves[label]={'state_time_s':[i/240 for i in range(25)],'force_time_s':[v['time_s'] for v in a['samples']],'joints':joint_curves};all_properties.append(props)
    checks={'two_observer_contracts_and_reference_arrays':True,'24_sensor_samples_no_t0':True,'native_properties_same_two_conditions':all_properties[0]==all_properties[1],
        'two_executions_exit_zero':len(read(PHASE/'execution.json'))==2 and all(r['exit_code']==0 for r in read(PHASE/'execution.json')),
        'inputs_unchanged':all(sha(p)==h for p,h in hashes.items())}
    if not all(checks.values()):raise AssertionError(checks)
    result={'checks':checks,'input_sha256':hashes,'counts':{'native_initializations':2,'physics_steps':48},'properties':all_properties[0],'summary':summary,'curves':curves,
        'scope':'completed-step total native DOF forces; coordinate error against constant Python submitted target from first integration, not native target getter or whole-joint SO3 error; no actuator-only torque, saturation or causal certification; sensor addition reproduces five raw arrays exactly'}
    (PHASE/'analysis.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n');print(json.dumps({'checks':checks,'summary':summary},indent=2))


if __name__=='__main__':main()
