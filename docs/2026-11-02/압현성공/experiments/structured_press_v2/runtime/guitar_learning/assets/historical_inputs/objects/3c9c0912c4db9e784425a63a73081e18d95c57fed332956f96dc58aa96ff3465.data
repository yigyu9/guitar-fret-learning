"""Replay preserved episode20 actions; inspect the next read-only controller call."""
import json
from pathlib import Path
import shutil
import traceback


def save(path,value):
    with path.open('x') as f: json.dump(value,f,indent=2,allow_nan=False)


def main():
    import isaacgym
    from .environment_v3 import FreshGuitarEnvironment,JacobianConsistencyError,ROOT,collect_inputs
    from ..run_joint_hold import native_state
    source = ROOT/'docs/2026-10-12/stability_adapter_2/results/fresh_learning_v1/pilot64_v3'
    out = source.parent/'diagnostic_v3'
    out.mkdir(exist_ok=False)
    hashes = collect_inputs()
    for path in (source/'transitions.jsonl',source/'final_state.json',source/'config.json'):
        import hashlib
        hashes[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    save(out/'inputs_before.json',hashes)
    for text in hashes:
        path = Path(text)
        if path.suffix=='.py' and str(path).startswith(str(ROOT)+'/'):
            target = out/'source_before'/path.relative_to(ROOT)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
    rows = [json.loads(line) for line in (source/'transitions.jsonl').read_text().splitlines()]
    actions = [r['info']['requested_action54'] for r in rows if r['episode']==20]
    save(out/'replayed_actions.json',actions)
    env = FreshGuitarEnvironment(recording=False,seed=121)
    report = {'source_episode':20,'seed':121,'actions':len(actions),'no_policy_loaded':True}
    try:
        env.reset(seed=121)
        import numpy as np
        samples = []
        previous_hook = env.scene.after_physics
        def sample(owner):
            if previous_hook is not None: previous_hook(owner)
            if owner.steps<260: return
            state = native_state(owner)
            owner.gym.refresh_jacobian_tensors(owner.sim)
            jac = env.controller.tensor.detach().cpu().numpy()[0]
            indices = [owner.human_bodies.index(name) for name in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist','LH:palm','LH:thumb_top','LH:middle_top','R_Shoulder')]
            samples.append({'step':owner.steps,'qdot':[v['vel'] for v in state['human_dof_states']],
                'bodies':{owner.human_bodies[i]:{'jacobian':jac[i-1].tolist(),'state':state['human_body_states'][i]} for i in indices}})
        env.scene.after_physics = sample
        for i,action in enumerate(actions):
            _,_,_,terminated,truncated,info = env.step(action)
            if terminated or truncated: raise RuntimeError('replay ended early at action '+str(i))
        before = native_state(env.scene)
        save(out/'replayed_state.json',before)
        original = json.loads((source/'final_state.json').read_text())
        report['exact_original_final_state'] = before==original
        report['physics_step_before_probe'] = env.scene.steps
        save(out/'temporal_jacobian_samples.json',samples)
        alignments = []
        for prev,current in zip(samples,samples[1:]):
            for name,body in current['bodies'].items():
                qdot = np.array(current['qdot'])
                native = np.array([body['state']['vel']['linear'][a] for a in 'xyz'])
                jcurrent = np.array(body['jacobian'])[:3]
                jprevious = np.array(prev['bodies'][name]['jacobian'])[:3]
                alignments.append({'step':current['step'],'body':name,
                    'current_J_current_qdot_error_m_s':float(np.linalg.norm(jcurrent@qdot-native)),
                    'previous_J_current_qdot_error_m_s':float(np.linalg.norm(jprevious@qdot-native)),
                    'midpoint_J_current_qdot_error_m_s':float(np.linalg.norm((jcurrent+jprevious)/2@qdot-native))})
        save(out/'temporal_alignment.json',alignments)
        try:
            # No target or effort submission: evaluate the controller only.
            env.controller()
            report['consistency_fault_reproduced'] = False
        except JacobianConsistencyError as error:
            save(out/'consistency_diagnostic.json',error.diagnostic)
            report['consistency_fault_reproduced'] = True
            report['diagnostic_kind'] = error.diagnostic['kind']
        report['read_only_probe_preserved_state'] = native_state(env.scene)==before
        report['forbidden_calls'] = env.scene.forbidden_calls
    except BaseException as error:
        report['failure'] = {'type':type(error).__name__,'message':str(error),'traceback':traceback.format_exc()}
    finally:
        if env.scene is not None:
            save(out/'final_state.json',native_state(env.scene))
            env.close()
        import hashlib
        report['changed_inputs'] = [p for p,h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
        save(out/'report.json',report)
        print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__': main()
