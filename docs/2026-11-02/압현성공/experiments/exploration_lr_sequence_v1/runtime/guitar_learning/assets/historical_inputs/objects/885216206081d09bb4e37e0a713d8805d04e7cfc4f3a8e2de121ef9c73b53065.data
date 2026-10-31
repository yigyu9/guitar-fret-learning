"""Export actual native motion from one recorded evaluation, not target angles."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1048576),b''):
            digest.update(block)
    return digest.hexdigest()


def export(run, out):
    run, out = Path(run).resolve(), Path(out).resolve()
    inputs = {name:sha(run/name) for name in ('attempt.json','config.json','initial_state.json','native_properties.json','report.json','transitions.jsonl')}
    read = lambda name:json.loads((run/name).read_text())
    report = read('report.json')
    if report['mode'] not in ('baseline','eval'):
        raise ValueError('motion export requires a single baseline or evaluation episode')
    names = read('native_properties.json')['joint_names']
    initial = read('initial_state.json')
    if len(names)!=81 or len(set(names))!=81:
        raise ValueError('expected81 unique native scalar joint names')
    frames = [dict(physics_time_s=0., score_time_s=0.,
        q81_rad=[v['pos'] for v in initial['human_dof_states']],
        qdot81_rad_s=[v['vel'] for v in initial['human_dof_states']],
        guitar_root_body_state=initial['guitar_body_states'][0])]
    for line in (run/'transitions.jsonl').open():
        row = json.loads(line)
        info = row['info']
        frame = dict(physics_time_s=info['clock']['physics_time_s'],score_time_s=info['score_time_s'],**info['native_motion'])
        if frame['physics_time_s']<=frames[-1]['physics_time_s'] or len(frame['q81_rad'])!=81 or len(frame['qdot81_rad_s'])!=81:
            raise ValueError('nonmonotonic or invalid native motion frame')
        frames.append(frame)
    if len(frames)-1!=report['process_counters']['valid_controls']:
        raise ValueError('motion count differs from valid native controls')
    out.mkdir(parents=True,exist_ok=False)
    with (out/'motion.jsonl').open('x') as stream:
        for frame in frames:
            stream.write(json.dumps(frame,allow_nan=False)+'\n')
    manifest=dict(schema='fresh_music.native_motion.v1',source_run=str(run),frames=len(frames),
        completed_episode=report['completed'],failure=report['failure'],joint_names=names,
        initial_human_body_states=initial['human_body_states'],root_and_lower_fixed=True,
        joint_units='scalar native joint position rad; velocity rad/s; suffixes are not world axes',
        guitar_units='native root rigid-body pose in world meters/quaternion xyzw; velocity m/s and rad/s',
        control_hz=60,source_input_sha256=inputs,source_input_unchanged=all(sha(run/name)==h for name,h in inputs.items()),
        export_source_sha256=sha(__file__),motion_sha256=sha(out/'motion.jsonl'),
        scope='Native joint/guitar state trajectory. Requires original skeleton and assets; not a retargeted BVH/FBX animation.')
    with (out/'manifest.json').open('x') as stream:
        json.dump(manifest,stream,indent=2,ensure_ascii=False,allow_nan=False)
    return manifest


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(export(args.run,args.out),ensure_ascii=False))
