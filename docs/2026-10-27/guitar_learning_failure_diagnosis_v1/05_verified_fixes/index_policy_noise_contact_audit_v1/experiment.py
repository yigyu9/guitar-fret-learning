"""Frozen V7 evaluator with private policy noise and read-only raw-ledger observers."""
import argparse
from contextlib import contextmanager
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
V7 = HERE.parent/'index_reward_value_warmup_v7'
CHECKPOINT = V7/'runs/ppo/final.pt'
CASES = {'det':None,'private7':7,'private17':17,'private27':27}
CAUSES = ['other_higher','own_wrong_fret','own_wrong_string']
BODIES = ['human/LH:'+finger+str(segment) for finger in ('thumb','index','middle','ring','pinky') for segment in (2,3)]
SAMPLE_KEYS = ('mean','log_std','latent','action')


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def require(ok,message):
    if not ok: raise ValueError(message)

spec = importlib.util.spec_from_file_location('private_noise_v7_experiment',V7/'experiment.py')
parent = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = parent;spec.loader.exec_module(parent)
base = parent.base


def evidence():
    pins = dict(parent.gate())
    review_path = V7/'actual_final_review.json'
    review = read(review_path)
    require(review['verdict'] == 'PASS' and not review['findings'],'Actual V7 final review required')
    require(len(review['reviewed_sha256']) == 903,'Expected reviewed903 input map')
    require(all(sha(p) == h for p,h in review['reviewed_sha256'].items()),'Reviewed V7 inputs changed')
    pins.update(review['reviewed_sha256']);pins[str(review_path)] = sha(review_path)
    require(pins[str(CHECKPOINT)] == sha(CHECKPOINT),'Final checkpoint changed')
    return pins


def prepare():
    pins = evidence()
    for name in ('PLAN.md','experiment.py','cpu_check.py','cpu_verification.json'):
        path = HERE/name;pins[str(path)] = sha(path)
    write(HERE/'preparation_seal.json',dict(independent_review='pending',input_pins=pins,
        cases=CASES,checkpoint=str(CHECKPOINT),fit_steps=0,value_warmup_steps=0,PPO_updates=0,
        collection='Original V7 evaluate; raw note ledgers and selected4 actor samples only'))
    require(not any(n in sys.modules for n in ('numpy','torch','isaacgym')),'Numerical import before gate')
    return dict(prepared=True,pins=len(pins),stdlib_only=True)


def gate():
    original = evidence();old = base.HERE
    try:
        base.HERE = HERE;pins = base.gate()
    finally: base.HERE = old
    require(all(pins.get(p) == h for p,h in original.items()),'Prepared map does not contain V7 evidence')
    return pins


def validate_raw_ledger(row):
    ledger = row['left_note_ledger'];source = ledger['wrong_press_sources']
    require(ledger['schema'] == 'guitar_learning.surface_note_ledger.v8','Current surface ledger v8 required')
    require(source['contract']['schema'] == 'guitar_learning.wrong_press_sources.v2' and
            source['contract']['causes'] == CAUSES,'Current wrong-source v2 cause order required')
    require(source['body_names'] == BODIES,'Wrong source body order changed')
    require(all(k in source['values'] for k in ('wrong_source_time','wrong_source_fret_min','wrong_source_fret_max')),'Source ledger fields missing')
    count = len(ledger['target_ids'])
    require(count > 8 and len(ledger['required_clean_s']) == count,'Compiled source target map missing')
    for key in ('wrong_source_time','wrong_source_fret_min','wrong_source_fret_max'):
        values = source['values'][key]
        require(len(values) == count and all(len(v) == 10 for v in values),'Wrong target/body source shape')
        if key == 'wrong_source_time': require(all(len(c) == 3 for v in values for c in v),'Wrong cause axis')
    require(all(k in ledger['values'] for k in ('wrong','wrong_supported_time','wrong_ambiguous_time','wrong_next_preparation_time',* [c+'_time' for c in CAUSES])),'Source timing fields missing')
    return ledger


@contextmanager
def observe(rt,noise_seed,state):
    """Delegate original constructor, bound act and step; restore every hook and global RNG."""
    import numpy as np
    import torch
    original_factory,original_step = rt.GoalPolicy,rt.GoalPool.step
    own_step = 'step' in rt.GoalPool.__dict__
    policies = []
    python_rng,numpy_rng = random.getstate(),np.random.get_state()
    state.update(actor_rows=[],raw_ledgers=[],act_calls=0,act_attempts=0,step_calls=0,step_attempts=0,private_seed=noise_seed)
    devices = list(range(torch.cuda.device_count())) if torch.cuda.is_available() else []
    with torch.random.fork_rng(devices=devices):
        def factory(*args,**kwargs):
            policy = original_factory(*args,**kwargs)
            own_act = 'act' in policy.__dict__
            original_act = policy.act
            policies.append((policy,own_act,original_act))
            private = dict(rng=None,device=None)
            def act(*inputs,**options):
                device = next(policy.parameters()).device
                active = policy._active_mask()
                require(tuple(inputs[0].shape[:1]) == (128,) and active.nonzero().flatten().tolist() == [17,18,19,20],
                        'Original full128 selected4 Gaussian required')
                require(options.get('deterministic',False) is (noise_seed is None),'Unexpected original evaluation mode')
                gpu = device.type == 'cuda';device_id = device.index or 0
                def get_rng(): return torch.cuda.get_rng_state(device_id) if gpu else torch.get_rng_state()
                def set_rng(value):
                    if gpu: torch.cuda.set_rng_state(value,device_id)
                    else: torch.set_rng_state(value)
                if private['rng'] is None:
                    private['device'] = str(device)
                    private['rng'] = torch.Generator(device=device).manual_seed(7 if noise_seed is None else noise_seed).get_state()
                    if noise_seed in (None,7):
                        require(torch.equal(private['rng'],get_rng()),'First private7 state must match original post-load seed7 boundary')
                    state['private_initial_rng_sha256'] = hashlib.sha256(private['rng'].cpu().numpy().tobytes()).hexdigest()
                require(private['device'] == str(device),'Policy RNG device changed')
                with torch.random.fork_rng(devices=[device_id] if gpu else []):
                    set_rng(private['rng'])
                    state['act_attempts'] += 1
                    try: result = original_act(*inputs,**options)
                    finally: private['rng'] = get_rng().clone()
                state['private_final_rng_sha256'] = hashlib.sha256(private['rng'].cpu().numpy().tobytes()).hexdigest()
                state['act_calls'] += 1
                state['pending_actor'] = {key:result[key][:,17:21].detach().clone() for key in SAMPLE_KEYS}
                return result
            policy.act = act
            return policy
        def step(pool,action):
            if 'source_notes' not in state:
                env = pool.environment
                state['source_notes'] = [dict(source_index=i,press_s=float(env.press[i]),onset_s=float(env.onset[i]),end_s=float(env.end[i]),
                    audible_duration_s=float(env.end[i]-env.onset[i]),string_1based=int(env.string[i])+1,fret=int(env.fret[i]),finger=int(env.finger[i])) for i in (4,7,8)]
            first = pool.first.detach().clone()  # Parent step marks completed rows false.
            require(state['act_calls'] == state['step_calls']+1,'One original act must precede each original step')
            pending = state.pop('pending_actor')
            start_clock = pool.environment.clock.detach().clone()
            start_source = pool.environment._score_time().detach().clone()
            state['step_attempts'] += 1
            result = original_step(pool,action)
            state['step_calls'] += 1
            env_ids = first.nonzero().flatten()
            row = {key:value[env_ids].cpu().numpy().copy() for key,value in pending.items()}
            row.update(env_id=env_ids.cpu().numpy().copy(),
                control_tick=np.full(len(env_ids),state['step_calls']-1,dtype=np.int64),
                start_clock=start_clock[env_ids].cpu().numpy().copy(),
                start_source_time_s=start_source[env_ids].cpu().numpy().copy(),
                end_source_time_s=pool.environment._score_time()[env_ids].detach().cpu().numpy().copy())
            state['actor_rows'].append(row)
            for raw in result[-1]:
                if bool(first[raw['env_id']]):
                    ledger = validate_raw_ledger(raw)
                    require(ledger['wrong_press_sources']['contract'] == pool.contract['diagnostics']['wrong_press'],'Raw ledger contract differs from actual pool contract')
                    state['raw_ledgers'].append(dict(env_id=raw['env_id'],steps=raw['steps'],
                        source_time_s=float(pool.environment._score_time()[raw['env_id']]),
                        selected_source_indices=[4,7,8],left_note_ledger=copy.deepcopy(ledger)))
            return result
        try:
            rt.GoalPolicy = factory;rt.GoalPool.step = step
            yield state
        finally:
            rt.GoalPolicy = original_factory
            if own_step: rt.GoalPool.step = original_step
            else: del rt.GoalPool.step
            for policy,own_act,original_act in policies:
                if own_act: policy.act = original_act
                else: del policy.act
            random.setstate(python_rng);np.random.set_state(numpy_rng)
            state['hooks_restored'] = rt.GoalPolicy is original_factory and rt.GoalPool.step is original_step


def compare_evaluation(folder,source):
    import numpy as np
    require(read(folder/'evaluation.json') == read(source/'evaluation.json'),'Original full128 ledger/nine-reward reproduction failed')
    with np.load(folder/'learning_control_env0.npz',allow_pickle=False) as current,np.load(source/'learning_control_env0.npz',allow_pickle=False) as reference:
        require(current.files == reference.files,'Original trace keys changed')
        for key in current.files:
            if key != 'net_body_force_n': np.testing.assert_array_equal(current[key],reference[key])
        force = float(np.max(np.abs(current['net_body_force_n']-reference['net_body_force_n'])))
    return dict(full128_ledger_nine_rewards_exact=True,all_nonforce_trace_fields_exact=True,force_max_abs_difference_N=force,force_difference_separate=True)


def invariance_gate(runs):
    pins = {}
    for case in ('det','private7'):
        folder = Path(runs)/case
        report = read(folder/'observer_report.json')
        require(report['completed'] and not report['failure'] and not report['changed_inputs'],'Both mean/private7 observer runs must pass before17/27')
        require(report['invariance']['full128_ledger_nine_rewards_exact'] and report['invariance']['all_nonforce_trace_fields_exact'],'Mean/private7 invariance failed')
        for p,h in report['input_pins'].items(): require(sha(p) == h,'Prior invariance input changed')
        for p,h in report['output_sha256'].items(): require(sha(p) == h,'Prior invariance output changed')
        pins[str(folder/'observer_report.json')] = sha(folder/'observer_report.json')
        pins.update(report['output_sha256'])
    return pins


def execute(case,out,runs):
    pins = gate()
    if case in ('private17','private27'): pins.update(invariance_gate(runs))
    import isaacgym
    import numpy as np
    out = Path(out).resolve();out.mkdir(parents=True,exist_ok=False)
    state,failure,invariance = {},None,None
    write(out/'inputs_before.json',pins)
    try:
        with parent.local_modules(include_learn=True) as modules:
            rt,learn = modules['runtime'],modules['learn']
            settings = read(V7/'runs/ppo_eval_000300_det/settings.json')
            learn.ready(CHECKPOINT)  # Own accepted V7 metadata; original evaluate repeats strict load.
            with observe(rt,CASES[case],state):
                learn.evaluate(CHECKPOINT,settings,pins,out/'evaluation',stochastic=case != 'det')
            ledgers = state['raw_ledgers']
            require(len(ledgers) == 128 and sorted(r['env_id'] for r in ledgers) == list(range(128)),'Original128 first attempts required')
            evaluation = read(out/'evaluation/evaluation.json')
            require(evaluation['assigned_quotas'] == [1]*128 and len(evaluation['episodes']) == 128,'Original128 quotas required')
            require(all([n['source_index'] for n in e['notes']] == [4,7,8] for e in evaluation['episodes']),'Original384 opportunities required')
            freeze = read(out/'evaluation/evaluation_freeze.json')
            require(freeze['model_optimizers_updates_frozen'] and freeze['checkpoint_frozen'],'Frozen policy audit failed')
            require(read(out/'evaluation/learning_report.json')['checkpoint_updates'] == 300,'Original last300 required')
            if case in ('det','private7'):
                source = V7/('runs/ppo_eval_000300_det' if case == 'det' else 'runs/ppo_eval_000300_stochastic')
                invariance = compare_evaluation(out/'evaluation',source)
    except BaseException as error:
        failure = dict(type=type(error).__name__,message=str(error));raise
    finally:
        try:
            write(out/'raw_ledgers.json',dict(complete=failure is None,assigned_quotas=[1]*128,
                selected_note_opportunities=384,episodes=state.get('raw_ledgers',[])))
            rows = state.get('actor_rows',[])
            if rows: np.savez_compressed(out/'actor_selected4.npz',**{k:np.concatenate([r[k] for r in rows]) for k in rows[0]})
            changed = [p for p,h in pins.items() if not Path(p).is_file() or sha(p) != h]
            outputs = {str(p):sha(p) for p in out.rglob('*') if p.is_file() and p.name != 'observer_report.json'}
            write(out/'observer_report.json',dict(completed=failure is None and not changed,failure=failure,changed_inputs=changed,
                case=case,private_policy_noise_seed=CASES[case],physical_reset_seed=7,checkpoint=str(CHECKPOINT),
                fit_steps=0,value_warmup_steps=0,PPO_updates=0,act_calls=state.get('act_calls',0),act_attempts=state.get('act_attempts',0),step_calls=state.get('step_calls',0),step_attempts=state.get('step_attempts',0),
                source_notes=state.get('source_notes'),body_names=BODIES,cause_order=CAUSES,policy_sample_shape=[128,4],private_initial_rng_sha256=state.get('private_initial_rng_sha256'),
                private_final_rng_sha256=state.get('private_final_rng_sha256'),input_pins=pins,output_sha256=outputs,invariance=invariance,
                global_RNG_scope_restored=state.get('hooks_restored',False),factory_and_step_restored=state.get('hooks_restored',False),scope='First128 attempts with failures; raw v2 cumulative240Hz source time, actor samples at60Hz; no GAE/state/event buffers. Source/cause times may overlap; no pressure or acoustic certification.'))
            if failure is None and changed: raise RuntimeError('Observer inputs changed')
        except BaseException as error:
            if failure is None: raise
            print('Secondary observer cleanup error: '+repr(error),file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__);sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('prepare');sub.add_parser('gate-check')
    p = sub.add_parser('collect');p.add_argument('--case',required=True,choices=CASES);p.add_argument('--out',required=True);p.add_argument('--runs',default=str(HERE/'runs'))
    args = parser.parse_args()
    if args.command == 'prepare': print(json.dumps(prepare()))
    elif args.command == 'gate-check':
        gate();require(not any(n in sys.modules for n in ('numpy','torch','isaacgym')),'Numerical import before gate');print('{"ready":true,"stdlib_only":true}')
    else: execute(args.case,args.out,args.runs)
