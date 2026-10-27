"""Compare saved PALM_RATE rollouts at the three approved fixed lengths."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
RAW = ('states','trace','controls','contacts','hands','queries','leg_torques')


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve previous comparison')
    audit = read(args.run/'strap_inputs.json')
    selection = read(args.run/'selection.json')
    executions = read(args.run/'rollout_executions.json')
    reference = ROOT/'docs/2026-10-12/stability_adapter_2/results/quiescent_3s_v1/on/report.json'
    base = read(reference)
    originals = {'short':ROOT/'docs/2026-10-12/stability_adapter_2/results/native_target_readback_v1/native',
        'hold_05s':ROOT/'docs/2026-10-12/stability_adapter_2/results/dof_force_observation_v1/attempt_v2/native'}
    paths = [reference,args.run/'strap_inputs.json',args.run/'selection.json',
        args.run/'rollout_executions.json',Path(__file__).resolve()]
    rows = []
    records = {r['id']:r for r in audit['records']}
    for group,steps in (('short',24),('hold_05s',120)):
        runs = [('load_00n',originals[group])]
        runs += [(name,args.run/group/name) for name in
            (selection['short_ids'] if group=='short' else selection['hold_ids'])]
        for name,run in runs:
            data = {n:read(run/(n+'.json')) for n in RAW}
            report = read(run/'report.json')
            states,trace,controls,contacts = [data[n] for n in ('states','trace','controls','contacts')]
            if any(len(data[n])!=(steps if n in ('controls','contacts') else steps+1) for n in RAW):
                raise ValueError('saved coverage differs: '+str(run))
            if ([s['physics_step'] for s in states]!=list(range(steps+1)) or
                [q['physics_step'] for q in data['queries']]!=list(range(steps+1)) or
                [c['physics_step'] for c in controls]!=list(range(1,steps+1)) or
                [c['physics_step'] for c in contacts]!=list(range(1,steps+1)) or
                [t['time_s'] for t in trace]!=[k/240 for k in range(steps+1)] or
                [c['updated_before_step'] for c in controls]!=[k%4==0 for k in range(steps)]):
                raise ValueError('saved timing/control schedule differs')
            q = np.array([[d['pos'] for d in s['human_dof_states']] for s in states])
            command = np.array([c['final_arm_targets_rad'] for c in controls])
            arm = base['arm_indices']
            if q.shape!=(steps+1,105) or command.shape!=(steps,24) or not all(np.isfinite(a).all() for a in (q,command)):
                raise ValueError('finite DOF/target shapes required')
            contact_counts = {}
            for sample in contacts:
                for contact in sample['contacts']:
                    pair = [contact['body0_name'],contact['body1_name']]
                    if any(n.startswith('guitar/') for n in pair):
                        for n in pair:
                            if n.startswith('human/'):
                                contact_counts[n] = contact_counts.get(n,0)+1
            checks = {'native_contracts':all(report['checks'].values()),'initial_audit_accepted':records[name]['accepted_for_diagnostic'],
                'same_full_initial_states':states[0]==read(originals[group]/'states.json')[0],
                'same_initial_q':report['initial_joint_targets_rad']==base['initial_joint_targets_rad'],
                'same_arm_box':all(report[k]==base[k] for k in ('arm_indices','diagnostic_lower_rad','diagnostic_upper_rad')),
                'same_palm_task_goal':data['queries'][0]['palm_goal_world_m']==read(originals[group]/'queries.json')[0]['palm_goal_world_m'],
                'fixed_expected_length':all(t['strap_rest_length_m']==records[name]['settings']['strap_rest_length_m'] for t in trace),
                'initial_law_force_matches':abs(trace[1]['last_applied_tension_n']-records[name]['initial_law_tension_n'])<1e-9,
                'finite_trace':all(t['finite'] for t in trace)}
            if group=='hold_05s':
                short = originals['short'] if name=='load_00n' else args.run/'short'/name
                checks['seven_short_prefix_exact'] = all(data[n][:24 if n in ('controls','contacts') else 25]==read(short/(n+'.json')) for n in RAW)
                paths += [short/(n+'.json') for n in RAW]
            palm = np.array([r['left_source_world_m'] for r in data['queries']])
            displacement = np.linalg.norm(palm-np.array(data['queries'][0]['palm_goal_world_m']),axis=1)*1000
            violation = np.maximum(np.maximum(np.array(base['native_joint_lower_rad'])[arm]-q[:,arm],
                q[:,arm]-np.array(base['native_joint_upper_rad'])[arm]),0)
            rows.append({'name':name,'group':group,'run':str(run),'reused_baseline':name=='load_00n','checks':checks,
                'rest_length_m':records[name]['settings']['strap_rest_length_m'],
                'initial_law_tension_n':records[name]['initial_law_tension_n'],
                'max_guitar_position_mm':max(t['position_error_m'] for t in trace)*1000,
                'max_guitar_rotation_deg':max(t['rotation_error_deg'] for t in trace),
                'final_guitar_position_mm':trace[-1]['position_error_m']*1000,'final_guitar_rotation_deg':trace[-1]['rotation_error_deg'],
                'max_left_palm_displacement_mm':float(displacement.max()),
                'max_actual_arm_scalar_limit_violation_deg':float(np.degrees(violation).max()),
                'max_applied_tension_n':max(t['last_applied_tension_n'] for t in trace[1:]),
                'contact_rows_by_human_body':contact_counts,
                'LH_contact_rows':sum(v for n,v in contact_counts.items() if n.startswith('human/LH:')),
                'RH_contact_rows':sum(v for n,v in contact_counts.items() if n.startswith('human/RH:')),
                'observed_upward_proxy_all_samples':all(h['palm_normal_valid'] and h['palm_up_dot']>=0 for h in data['hands'])})
            paths += [run/(n+'.json') for n in RAW+('report',)]+[Path(p) for p in report['input_sha256']]
            if not all(sha(p)==h for p,h in report['input_sha256'].items()):
                raise ValueError('native input sources differ')
    checks = {'initial_audit_contracts':audit['runtime_sources_unchanged'] and all(all(r['checks'].values()) for r in audit['records']),
        'selected_unique_and_accepted':len(set(selection['short_ids']))==len(selection['short_ids']) and
            len(set(selection['hold_ids']))==len(selection['hold_ids']) and
            set(selection['short_ids'])<={'load_01n','load_02n'} and
            set(selection['hold_ids'])<=set(selection['short_ids']) and all(records[n]['accepted_for_diagnostic'] for n in selection['short_ids']),
        'declared_fresh_run_coverage':len(executions)==sum(not r['reused_baseline'] for r in rows) and
            {e['command'][e['command'].index('--out')+1] for e in executions}==
            {r['run'] for r in rows if not r['reused_baseline']} and all(e['returncode']==0 for e in executions),
        'initial_audit_sources_current':all(sha(p)==h for p,h in audit['source_sha256'].items()),
        'all_run_checks_pass':all(all(r['checks'].values()) for r in rows)}
    paths += [Path(p) for p in audit['source_sha256']]
    output = {'checks':checks,'rows':rows,'input_sha256':{str(p.resolve()):sha(p) for p in paths},
        'scope':'same PALM_RATE/PD/initial pose, fixed initial strap length comparison; no guitar stabilization/playing certificate',
        'semantics':'initial law force is not constant runtime force; contact rows are not force/depth/causation; scalar limit check is not body rotation'}
    args.out.write_text(json.dumps(output,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'checks':checks,'rows':[{k:r[k] for k in ('name','group','max_guitar_position_mm','max_guitar_rotation_deg','max_left_palm_displacement_mm')} for r in rows]},indent=2))
    if not all(checks.values()):
        raise AssertionError(checks)


if __name__=='__main__':
    main()
