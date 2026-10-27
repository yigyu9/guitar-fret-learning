"""Prepare four single-axis initial candidates and directly gate them in order."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

R = Path(__file__).resolve().parents[1]
A = R / 'stability_adapter_2'
D = R / 'docs/2026-10-12/stability_adapter_2'
P = D / 'results/source_hand_thumb_base_native_v1'
OLD = D / 'results/fixed_strap_source_hand_initial_v1'
RANGES = D / 'results/fixed_strap_source_compatibility_v1/joint_ranges.jsonl'
PLAN = A / 'SOURCE_HAND_THUMB_BASE_NATIVE_PLAN.md'
CANDIDATES = [('thumb1_x_minus005', 'LH:thumb1_x', -.05),
              ('thumb1_y_plus005', 'LH:thumb1_y', .05),
              ('thumb1_x_minus010', 'LH:thumb1_x', -.10),
              ('thumb1_y_plus010', 'LH:thumb1_y', .10)]


def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def save(p, data): Path(p).write_text(json.dumps(data, indent=2, allow_nan=False)+'\n')


def freeze(stage, paths, direct):
    assert not (P/(stage+'_execution.json')).exists()
    before = {str(p): sha(p) for p in sorted(set(paths), key=str)}
    manifest = {}
    for p in sorted(set(direct), key=str):
        rel = p.relative_to(R) if str(p).startswith(str(R)+'/') else Path('external')/Path(*p.parts[1:])
        dest = P/(stage+'_source')/rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        assert sha(dest) == before[str(p)]
        manifest[str(p)] = dict(snapshot=str(dest), sha256=before[str(p)])
    save(P/(stage+'_source_manifest.json'), manifest)
    return before


def prepare():
    from .environment import np
    from .warmstart_targets import compose
    assert not (P/'proposal.json').exists()
    P.mkdir(exist_ok=True)
    direct = {Path(__file__).resolve(), A/'run_thumb_base_candidate.py', A/'run_source_hand_initial.py',
              A/'run_small_wrist_recorded_diagnostic.py', A/'warmstart_targets.py', PLAN,
              OLD/'proposal.json', OLD/'native/initial_values.json', OLD/'artifact_inventory.json',
              RANGES, RANGES.parent/'artifact_inventory.json'}
    old = read(OLD/'proposal.json')
    original_path = Path(old['rows'][0]['trial_path'])
    direct.add(original_path)
    paths = direct | {Path(p) for p in old['input_sha256']}
    before = freeze('preparation', paths, direct)
    assert all(before[p] == h for p,h in old['input_sha256'].items())
    assert before[str(original_path)] == old['rows'][0]['trial_sha256']
    assert before[str(RANGES)] == read(RANGES.parent/'artifact_inventory.json')[str(RANGES)]['sha256']
    initial = read(OLD/'native/initial_values.json')
    names = initial['human_joint_names']
    qold = np.array(initial['initial_PD_target_rad'], dtype=np.float32)
    told = np.array(initial['preserved_absolute_targets_rad'], dtype=np.float32)
    main = [names.index(n) for n in initial['main_control_joint_names']]
    props = initial['PD_properties']
    bound = {(v['kind'],v['name']):v for v in (json.loads(s) for s in RANGES.read_text().splitlines()) if v['label'] == 'initial_aligned'}
    original = read(original_path)
    folder = A/'trials/source_hand_thumb_base_native_v1'
    folder.mkdir(exist_ok=False)
    prepared = []
    checks = dict(baseline_checks=all(old['checks'].values()), four_candidates=len(CANDIDATES) == 4)
    for label, name, delta in CANDIDATES:
        i = names.index(name)
        qnew, tnew = qold.copy(), told.copy()
        assert qold[i] == told[i]
        qnew[i] = np.float32(float(qold[i])+delta)
        tnew[i] = qnew[i]
        trial = copy.deepcopy(original)
        trial['initial_settings']['joint_angles_rad'][name] = float(qnew[i])
        trial['main_target_offsets_rad'][name] = 0.
        restored = copy.deepcopy(trial)
        restored['initial_settings']['joint_angles_rad'][name] = original['initial_settings']['joint_angles_rad'][name]
        restored['main_target_offsets_rad'][name] = original['main_target_offsets_rad'][name]
        offsets = np.array([trial['main_target_offsets_rad'].get(names[j],0.) for j in main])
        target = compose(qnew, main, offsets, props['lower'], props['upper'])
        other = [j for j in range(len(names)) if j != i]
        checks[label+'_only_one_initial_and_held_change'] = restored == original and bool(np.array_equal(qnew[other],qold[other]) and np.array_equal(target[other],told[other]))
        checks[label+'_exact_unclipped_targets'] = bool(np.array_equal(target,tnew))
        checks[label+'_all81_effective_ranges'] = all(bound[k,n]['effective_lower_rad'] <= float(values[j]) <= bound[k,n]['effective_upper_rad'] for k,values in [('actual_initial',qnew),('held',target)] for j,n in enumerate(names))
        for sign in [-1,1]:
            moving = offsets.copy()
            moving[main.index(names.index('L_Wrist_x'))] += sign*.005
            command = compose(qnew,main,moving,props['lower'],props['upper'])
            checks[label+'_wrist_extreme_'+str(sign)] = all(bound['held',n]['effective_lower_rad'] <= float(command[j]) <= bound['held',n]['effective_upper_rad'] for j,n in enumerate(names))
        assert trial['initial_settings']['strap_rest_length_m'] == 1.1018469719600776
        trial_path = folder/(label+'.json')
        save(trial_path,trial)
        row = copy.deepcopy(old['rows'][0])
        row.pop('source_state',None)
        row.update(label=label,alpha=None,trial_path=str(trial_path),trial_sha256=sha(trial_path),
                   expected_initial_angles_rad=qnew.astype(float).tolist(),expected_absolute_targets_rad=target.astype(float).tolist(),
                   admission_scope='Numeric bounds only; fresh actual native source geometry still required',
                   finger_target_policy='One thumb1 base axis initial=held, offset0; other80 initial/held preserved from source-hand5 baseline')
        proposal = copy.deepcopy(old)
        proposal.update(checks={},input_sha256=before,rows=[row],scope='One-axis numeric candidate; no multi-axis FK geometry prediction')
        proposal_path = P/(label+'_proposal.json')
        prepared.append(dict(label=label,name=name,requested_delta_rad=delta,actual_delta_rad=float(qnew[i])-float(qold[i]),initial_rad=float(qnew[i]),held_rad=float(target[i]),trial_path=str(trial_path),trial_sha256=sha(trial_path),proposal_path=str(proposal_path)))
        save(proposal_path,proposal)
    checks['inputs_preserved'] = all(sha(p) == h for p,h in before.items())
    assert all(checks.values()),checks
    for item in prepared:
        proposal = read(item['proposal_path'])
        proposal['checks'] = checks
        save(item['proposal_path'],proposal)
    save(P/'proposal.json',dict(checks=checks,candidates=prepared,input_sha256=before,scope='Four one-axis numeric candidates; fresh native gate required; at most one completed5s'))
    log = json.dumps(dict(checks=checks,candidates=prepared),indent=2)+'\n'
    (P/'preparation.log').write_text(log)
    save(P/'preparation_execution.json',dict(command=[sys.executable,'-m','stability_adapter_2.run_thumb_base_native_phase','prepare'],exit_code=0,terminal_state='completed',input_sha256_before=before,input_sha256_after={p:sha(p) for p in before},log_sha256=sha(P/'preparation.log')))
    print(log)


def native():
    proposal = read(P/'proposal.json')
    assert all(proposal['checks'].values()) and all(sha(p) == h for p,h in proposal['input_sha256'].items())
    assert not (P/'native_batch.json').exists()
    assert sha(A/'run_source_hand_initial.py') == 'a318a62b47f93dce1d3c526a64297d419341cc4983784e0aa4e2443b4f11a8b7'
    assert sha(A/'run_small_wrist_recorded_diagnostic.py') == '34d50c9f95a1b100efce621470a099d0aa259df7bbf307e5c7e44c6927598ef6'
    prior = read(OLD/'native_execution.json')['input_sha256_before']
    assert all(sha(p) == h for p,h in prior.items())
    summary = dict(attempts=[],selected=None,physical_initializations=0,physical_steps=0,scope='Sequential fresh native admission; first passing candidate continues same initialization5s; bounded maximum4initializations/1completed5s')
    env = dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MUJOCO_GL='disable',MPLBACKEND='Agg',MPLCONFIGDIR='/tmp/stability2_thumb_base',PYTHONPATH=str(R/'isaacgym/python')+':'+str(R),LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib')
    for item in proposal['candidates']:
        label = item['label']
        direct = {Path(__file__).resolve(), A/'run_thumb_base_candidate.py', PLAN,
                  P/'proposal.json',P/'preparation_execution.json',OLD/'native_execution.json',
                  Path(item['proposal_path']),Path(item['trial_path'])}
        paths = {Path(p) for p in prior} | {Path(p) for p in proposal['input_sha256']} | direct
        before = freeze(label,paths,direct)
        command = [sys.executable,'-m','stability_adapter_2.run_thumb_base_candidate','--trial',item['trial_path'],'--proposal',item['proposal_path'],'--out',str(P/'native'/label)]
        start = time.monotonic()
        with (P/(label+'.log')).open('xb') as log:
            result = subprocess.run(command,cwd=R,env=env,stdout=log,stderr=subprocess.STDOUT)
        report_path = P/'native'/label/'report.json'
        report = read(report_path) if report_path.exists() else {}
        terminal = 'completed' if result.returncode == 0 and report.get('completed') else 'error'
        if result.returncode != 0 and report.get('physics_steps') == 0 and report.get('checks',{}).get('direct_native_source_gate') is False:
            terminal = 'initial_geometry_rejected_zero_steps'
        after = {p:sha(p) for p in before}
        save(P/(label+'_execution.json'),dict(command=command,environment={k:env[k] for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MUJOCO_GL','MPLBACKEND','MPLCONFIGDIR','PYTHONPATH','LD_LIBRARY_PATH']},exit_code=result.returncode,terminal_state=terminal,wall_seconds=time.monotonic()-start,input_sha256_before=before,input_sha256_after=after,log_sha256=sha(P/(label+'.log'))))
        attempt = dict(label=label,terminal_state=terminal,exit_code=result.returncode,physics_steps=report.get('physics_steps'),native_initializations=report.get('native_initializations'),frame_count=report.get('frame_count'))
        summary['attempts'].append(attempt)
        summary['physical_initializations'] += report.get('native_initializations',0)
        summary['physical_steps'] += report.get('physics_steps',0)
        if terminal == 'completed':
            assert report['physics_steps'] == 1200 and report['frame_count'] == 151
            summary['selected'] = label
        save(P/'native_batch.json',summary)
        print(json.dumps(attempt),flush=True)
        assert before == after and terminal != 'error', 'native execution failed; preserve partial outputs and use a new plan/version'
        if summary['selected'] is not None:
            break


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage',choices=['prepare','native'])
    args = parser.parse_args()
    prepare() if args.stage == 'prepare' else native()
