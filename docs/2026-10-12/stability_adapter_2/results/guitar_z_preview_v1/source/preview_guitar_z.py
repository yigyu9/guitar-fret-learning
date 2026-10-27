"""Static source geometry at saved initial poses with guitar-only Z offsets."""
import argparse
import hashlib
import json
from pathlib import Path

from .replay_contact_geometry import recorded_probe
from .initial_overlap import mujoco, np, query_pairs
from .environment import CONFIG_PATH
from .strap import cable_forces
from .trial_settings import source_hashes


def preview(run):
    paths = [run/name for name in ('report.json','trace.json','states.json')]
    paths += [Path(__file__).resolve(), CONFIG_PATH,
        Path(__file__).with_name('replay_contact_geometry.py'),
        Path(__file__).with_name('initial_overlap.py'), Path(__file__).with_name('strap.py')]
    def hashes():
        result = source_hashes()
        result.update({str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
        return result
    before = hashes()
    report = json.loads((run/'report.json').read_text())
    initial = json.loads((run/'trace.json').read_text())[0]
    config = json.loads(CONFIG_PATH.read_text())
    model,data,shapes = recorded_probe(run,0)
    origins = model.body_pos.copy()
    guitar_ids = [mujoco.mj_name2id(model,mujoco.mjtObj.mjOBJ_BODY,'guitar/'+s['body'])
        for s in shapes if s['actor']=='guitar']
    guitar_ids = np.unique(guitar_ids)
    route0 = np.array(initial['route_points_m'])
    rows = []
    for offset_mm in (0,2,5,10,15):
        model.body_pos[:] = origins
        model.body_pos[guitar_ids,2] += offset_mm/1000
        mujoco.mj_forward(model,data)
        distances = query_pairs(model,data,shapes)
        route = route0.copy()
        route[[0,-1],2] += offset_mm/1000
        _,tension,length,_ = cable_forces(route,np.zeros_like(route),
            report['absolute_rest_length_m'],config['strap']['stiffness_n_per_m'],
            config['strap']['damping_n_s_per_m'],config['strap']['max_tension_n'])
        rows.append({'guitar_z_offset_mm':offset_mm,
            'candidate_initial_position_m':(np.array(initial['guitar_position_m'])
                +[0,0,offset_mm/1000]).tolist(),
            'initial_rotation_change_deg':0,'source_geometry':distances,
            'initial_route_length_m':length,'absolute_rest_length_m':report['absolute_rest_length_m'],
            'static_tension_zero_velocity_n':tension})
    model.body_pos[:] = origins
    mujoco.mj_forward(model,data)
    if hashes()!=before or not np.isclose(rows[0]['initial_route_length_m'],initial['strap_length_m'],atol=1e-12):
        raise AssertionError('preview inputs changed or baseline strap route differs')
    return {'scope':'static MuJoCo source-shape preview only; no native rollout or target change',
        'native_source_run':str(run.resolve()),'source_sha256':before,
        'source_files_unchanged':True,'source_goal_position_m':report['guitar_goal_position_m'],
        'unchanged_quaternion_xyzw':report['guitar_goal_quaternion_xyzw'],
        'humanoid_initial_pose_unchanged':True,'rows':rows,
        'not_verified':['PhysX cooked shape clearance','floor/chair/self collisions',
            'guitar stability','solver stability','hand support','feedback']}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('preserve previous preview')
    result = preview(args.run)
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps([{'offset_mm':r['guitar_z_offset_mm'],
        'negative_pairs':r['source_geometry']['negative_gap_pair_count'],
        'route_m':r['initial_route_length_m'],'tension_n':r['static_tension_zero_velocity_n'],
        'near_pairs':[(p['human_body'],p['guitar_body'],p['signed_gap_m']*1000)
            for p in r['source_geometry']['pairs_within_limit']]}
        for r in result['rows']],indent=2))


if __name__=='__main__':
    main()
