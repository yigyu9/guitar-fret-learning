"""Exact aborted-prefix replay plus deterministic full-task qualifications.

Invoke in the native launcher environment; Isaac Gym loads before Torch.
This script performs no policy sampling or optimizer updates.
"""
import argparse
import json
from pathlib import Path
import traceback


def save(path,value):
    with path.open('x') as stream: json.dump(value,stream,indent=2,allow_nan=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--mode',choices=('replay','qualification','all'),default='all')
    parser.add_argument('--random-amplitude',type=float,default=.8)
    args = parser.parse_args()
    import isaacgym  # Must precede gymtorch/Torch imports.
    import numpy as np
    from .environment_v3 import MusicGuitarEnvironment,collect_inputs
    from ..initial_pose_noise_v1 import sha
    if not 0<args.random_amplitude<=1: raise ValueError('bounded random amplitude required')
    args.out.mkdir(parents=True,exist_ok=False)
    hashes = collect_inputs(args.bundle)
    hashes.update({str(p.resolve()):sha(p) for p in (args.source/'commands.jsonl',args.source/'transitions.jsonl',args.source/'config.json')})
    save(args.out/'inputs_before.json',hashes)
    commands = [json.loads(line) for line in (args.source/'commands.jsonl').read_text().splitlines()]
    prefix = [json.loads(line) for line in (args.source/'transitions.jsonl').read_text().splitlines()]
    results = []
    cases = [('replay','B')] if args.mode in ('replay','all') else []
    if args.mode in ('qualification','all'): cases += [(mode,stage) for mode in ('zero','random') for stage in ('B','C','D')]
    for mode,stage in cases:
        out = args.out/(mode+'_'+stage)
        out.mkdir()
        env = MusicGuitarEnvironment(args.bundle,stage=stage,seed=101)
        failure = None
        counters = dict(controls=0,physics_checks=0,current=0,previous_k_minus_1=0,
                        current_COM_max_m_s=0.,previous_COM_max_m_s=0.,angular_max_rad_s=0.,support_max_m_s=0.)
        prefix_checks = dict(compared_controls=0,all_exact=True,first_difference=None)
        final_info = None
        try:
            env.reset()
            rng = np.random.default_rng(101)
            original = env.controller
            with (out/'alignment.jsonl').open('x') as alignment,(out/'transitions.jsonl').open('x') as transitions:
                def control():
                    effort = original()
                    report = original.alignment_report
                    alignment.write(json.dumps(report,allow_nan=False)+'\n')
                    counters['physics_checks'] += 1
                    counters[report['selected']] += 1
                    for name,stats in report['candidates'].items():
                        key = 'current_COM_max_m_s' if name=='current' else 'previous_COM_max_m_s'
                        counters[key] = max(counters[key],stats['COM_max_m_s'])
                        counters['angular_max_rad_s'] = max(counters['angular_max_rad_s'],stats['angular_max_rad_s'])
                        counters['support_max_m_s'] = max(counters['support_max_m_s'],stats['support_point_max_m_s'])
                    return effort
                env.scene.right_effort_controller = control
                while not env.finished:
                    index = counters['controls']
                    if mode=='replay' and index>=len(commands): break
                    if mode=='replay':
                        command = commands[index]
                        if env.scene.steps!=command['physics_step_before']: raise RuntimeError('exact command clock differs')
                        action = np.array(command['action54'])
                    elif mode=='zero': action = np.zeros(54)
                    else: action = rng.uniform(-args.random_amplitude,args.random_amplitude,54)
                    observation,reward,cost,terminated,truncated,info = env.step(action)
                    counters['controls'] += 1
                    final_info = info
                    transitions.write(json.dumps(dict(index=index,reward=reward,cost=cost,terminated=terminated,
                                                      truncated=truncated,info=info),allow_nan=False)+'\n')
                    if mode=='replay' and index<len(prefix):
                        old = prefix[index]['info']
                        exact = dict(native_motion=info['native_motion']==old['native_motion'],
                                     targets=info['submitted_target81_rad']==old['submitted_target81_rad'],
                                     effort=info['effort_control']['submitted_effort81_Nm']==old['effort_control']['submitted_effort81_Nm'])
                        prefix_checks['compared_controls'] += 1
                        if not all(exact.values()):
                            prefix_checks['all_exact'] = False
                            if prefix_checks['first_difference'] is None: prefix_checks['first_difference'] = dict(index=index,fields=exact)
        except BaseException as error:
            failure = dict(type=type(error).__name__,message=str(error),traceback=traceback.format_exc(),
                           diagnostic=getattr(error,'diagnostic',None))
        finally:
            physics_step = env.scene.steps if env.scene else 0
            env.close()
        replay_complete = (counters['controls']==len(commands) and
                           prefix_checks['compared_controls']==len(prefix) and
                           prefix_checks['all_exact'] and physics_step>611)
        report = dict(mode=mode,stage=stage,completed=failure is None and (replay_complete if mode=='replay' else env.finished),
                      failure=failure,counters=counters,physics_step=physics_step,prefix_checks=prefix_checks,
                      full_timeline_completed=bool(env.finished),training_updates=0,random_amplitude=args.random_amplitude,
                      progressed_past_original_fault=physics_step>611 if mode=='replay' else None)
        save(out/'report.json',report)
        results.append(report)
        print(mode,stage,'steps',physics_step,'failure',failure['message'] if failure else None,flush=True)
    unchanged = all(sha(p)==h for p,h in hashes.items())
    save(args.out/'report.json',dict(results=results,inputs_unchanged=unchanged,
         all_cases_passed=unchanged and all(r['completed'] and r['prefix_checks']['all_exact'] for r in results),
         qualification_scope='velocity sampling compatibility; not solver cause, torque-J correctness or music success'))


if __name__=='__main__': main()
