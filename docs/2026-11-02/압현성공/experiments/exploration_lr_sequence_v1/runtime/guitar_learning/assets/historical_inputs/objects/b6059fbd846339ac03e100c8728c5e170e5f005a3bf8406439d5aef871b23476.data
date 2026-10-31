"""Full smoothed-target episodes; conservative guard is not a safety certificate."""
import hashlib
import json
from pathlib import Path
import shutil
import traceback


def save(path,value):
    with path.open('x') as f: json.dump(value,f,indent=2,allow_nan=False)


def main():
    import isaacgym
    import numpy as np
    from .environment_v5 import FreshGuitarEnvironment,ROOT,collect_inputs
    from ..run_joint_hold import native_state
    source = ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v4'
    out = source.parent/'diagnostic_v7'
    out.mkdir(exist_ok=False)
    hashes = collect_inputs()
    for path in (source/'commands.jsonl',source/'final_state.json'):
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(out/'inputs_before.json',hashes)
    for text in hashes:
        path = Path(text)
        if path.suffix=='.py' and str(path).startswith(str(ROOT)+'/'):
            target = out/'source_before'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
    rows = [json.loads(line) for line in (source/'commands.jsonl').read_text().splitlines()]
    replay = [r['action54'] for r in rows if r['episode']==20]
    trials = [('smoothed_68_commands_then_neutral',121,replay+[np.zeros(54).tolist()]*(300-len(replay))),
              ('neutral_5s',101,[np.zeros(54).tolist()]*300)]
    for seed in (700,701):
        rng = np.random.default_rng(seed)
        trials.append(('random_%d'%seed,seed,rng.uniform(-1,1,size=(300,54)).tolist()))
    report = {'trials':[],'no_policy_loaded':True}
    for name,seed,actions in trials:
        env = FreshGuitarEnvironment(recording=False,seed=seed)
        stats = []
        trial = {'name':name,'seed':seed,'requested_control_steps':len(actions)}
        try:
            env.reset(seed=seed)
            def control():
                efforts = env.controller()
                row = env.controller.last
                stats.append({key:row[key] for key in ('physics_step','velocity_error_m_s','current_pose_velocity_error_m_s','validation_jacobian_physics_step','effort_jacobian_physics_step')})
                return efforts
            env.scene.right_effort_controller = control
            transitions = []
            for action in actions:
                _,reward,cost,terminated,truncated,info = env.step(action)
                transitions.append({'reward':reward,'cost':cost,'terminated':terminated,'truncated':truncated,
                    'guitar_displacement_m':info['guitar_displacement_m'],'guitar_rotation_rad':info['guitar_rotation_rad']})
                if terminated or truncated: break
            state = native_state(env.scene)
            save(out/(name+'_final_state.json'),state)
            save(out/(name+'_transitions.json'),transitions)
            if name=='smoothed_68_commands_then_neutral': trial['preserved_prefix_commands'] = len(replay)
            trial.update(completed=True,control_steps=len(transitions),physics_steps=env.scene.steps,
                         forbidden_calls=env.scene.forbidden_calls)
        except BaseException as error:
            trial['completed'] = False
            trial['failure'] = {'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
            if hasattr(error,'diagnostic'): save(out/(name+'_failure_diagnostic.json'),error.diagnostic)
        finally:
            save(out/(name+'_physics_guard_rows.json'),stats)
            env.close()
            report['trials'].append(trial)
    report['changed_inputs'] = [p for p,h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    save(out/'report.json',report)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__': main()
