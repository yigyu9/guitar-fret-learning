"""Measure sampled source geometry from saved short trials; no physics steps."""
import json
from pathlib import Path
from types import SimpleNamespace

from .thigh_palm_support import PHASE, intersection
from .build_fixed_lower_asset import read, sha
from .replay_contact_geometry import recorded_probe
from .render_best_run_video import set_saved_pose
from .search_hand_support import palm_neck_gap
from .pose_strap_inputs import pose_metrics
from .plot_neck_palm import geometry
import mujoco


def main():
    output = PHASE/'comparison.json'
    if output.exists():
        raise FileExistsError('preserve comparison')
    inputs = {str(Path(__file__).resolve()):sha(Path(__file__))}
    rows = []
    for name in ('reference','clear_50um','clear_100um','clear_150um'):
        run = PHASE/'short'/name
        for filename in ('report','states','trace','contacts'):
            p = run/(filename+'.json'); inputs[str(p)] = sha(p)
        report,states = read(run/'report.json'),read(run/'states.json')
        model,data,shapes = recorded_probe(run,0)
        samples = []
        for step in (0,1,12,24):
            state = states[step]
            set_saved_pose(model,mujoco,report,state); mujoco.mj_forward(model,data)
            scene = SimpleNamespace(human=0,guitar=1,human_bodies=report['human_body_names'],
                guitar_bodies=report['guitar_body_names'],bodies=lambda actor:state['human_body_states'] if actor==0 else state['guitar_body_states'])
            meshes = {s['geom_id']:geometry(model,data,s) for s in shapes}
            pairs = []
            for a in [s for s in shapes if s['body'].startswith('LH:') or s['body']=='L_Wrist']:
                for b in [s for s in shapes if s['body'].startswith('RH:') or s['body']=='R_Wrist']:
                    radius = intersection(meshes[a['geom_id']],meshes[b['geom_id']])
                    if radius>1e-7:
                        pairs.append({'left':a['body'],'right':b['body'],'common_interior_ball_radius_m':radius})
            samples.append({'physics_step':step,'palm_neck':palm_neck_gap((model,data,shapes)),
                'hand':pose_metrics(scene,(model,data,shapes)),'hand_intersections':pairs})
        rows.append({'name':name,'run':str(run),'max_position_error_mm':1000*report['max_position_error_m'],
            'max_rotation_error_deg':report['max_rotation_error_deg'],'absolute_rest_length_m':report['absolute_rest_length_m'],
            'support_contact_steps':report['support_contact_steps'],'source_samples':samples,
            'native_checks_pass':all(report['checks'].values()) and all(report['support_checks'].values())})
    if not all(sha(Path(p))==h for p,h in inputs.items()):
        raise ValueError('analysis inputs changed')
    output.write_text(json.dumps({'scope':'Four saved 0.1s trials; sampled source hull checks, not PhysX cooked clearance or full-time collision certification.',
        'rows':rows,'input_sha256':inputs,'inputs_verified_before_and_after':True,
        'decision':'No candidate has native left-palm contact; do not extend or adopt as stable two-point support.'},indent=2,allow_nan=False)+'\n')
    print(json.dumps([{'name':r['name'],'p_mm':r['max_position_error_mm'],'q_deg':r['max_rotation_error_deg'],
        'palm_gap_mm':[1000*s['palm_neck']['source_hull_distance_m'] for s in r['source_samples']],
        'hand_cross_counts':[len(s['hand_intersections']) for s in r['source_samples']]} for r in rows],indent=2))


if __name__=='__main__':
    main()
