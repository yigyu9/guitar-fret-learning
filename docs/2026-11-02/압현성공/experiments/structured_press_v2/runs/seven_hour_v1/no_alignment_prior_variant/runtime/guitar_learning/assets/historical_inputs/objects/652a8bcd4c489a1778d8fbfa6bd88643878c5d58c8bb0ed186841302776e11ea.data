"""Two proximal right supports at fixed guitar pose; static source proposals only."""
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from .initial_pose_noise_v1 import read, save, sha, pose
from .upper_arm_static_geometry_v1 import ROOT, ASSET, calibrated_upper_fk, state_from_fk
from .realistic_guitar_geometry_v1 import source_scene, source_audit
from .om_axilla_source_geometry_v3 import CapsuleBodyDistance
from .environment_contract_v1 import EnvironmentContract

A = ROOT/'stability_adapter_2'
D = ROOT/'docs/2026-10-19/stability_adapter_2'
P = D/'results/right_block_cradle_v1'
CFG = P/'config_v1/static_Thorax40.json'
BASE = P/'native_static_Thorax40/initial_values.json'
PLAN = A/'RIGHT_BLOCK_CRADLE_CLOSE_SOURCE_PLAN_V2.md'


def main():
    contract = EnvironmentContract(CFG); cfg = read(CFG); seed = read(cfg['initial_candidate'])
    base = read(BASE); names, bodies = base['joint_names'], base['human_body_names']
    state = base['native_initial_state']; q0 = contract.q_ref.copy(); gp, gr = pose(state['guitar_body_states'][0])
    fk, parents = calibrated_upper_fk(names, bodies, state, q0); original = fk(q0)
    geometry = read(A/'assets/om_body_geometry_v3/manifest.json')
    analytic = CapsuleBodyDistance(geometry['asset'], ASSET)
    right = np.array([i for i, n in enumerate(names) if n.startswith(('R_Thorax', 'R_Shoulder', 'R_Elbow', 'R_Wrist'))])
    left = np.array([i for i, n in enumerate(names) if n.startswith(('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist'))])
    head = np.array([i for i, n in enumerate(names) if n.startswith(('Neck_', 'Head_'))])
    active = np.r_[contract.body, right]; lo = np.maximum(contract.lower[active]+1e-6, q0[active]-np.r_[np.full(9, .1), np.full(12, .15)])
    hi = np.minimum(contract.upper[active]-1e-6, q0[active]+np.r_[np.full(9, .1), np.full(12, .15)])
    elbow_index = names.index('R_Elbow_y'); j = list(active).index(elbow_index)
    lo[j] = max(lo[j],contract.lower[elbow_index]+np.deg2rad(5)+1e-6)
    hi[j] = min(hi[j],contract.upper[elbow_index]-np.deg2rad(5)-1e-6)
    right_axis = original['R_Shoulder'][0]-original['L_Shoulder'][0]; right_axis[2] = 0; right_axis /= np.linalg.norm(right_axis)
    left_goal, left_rotation = original['L_Wrist']; hand_goal, hand_rotation = original['RH:palm']
    paths = [Path(__file__).resolve(), PLAN, BASE, CFG, ASSET, A/'assets/om_body_geometry_v3/manifest.json', Path(geometry['asset'])]
    paths += list(A.glob('*.py'))+[Path(m['path']) for m in geometry['meshes']]
    inputs = {str(p): sha(p) for p in paths}; inputs.update(contract.inputs)
    out = P/'search_v7'; out.mkdir(exist_ok=False); save(out/'inputs_before.json', inputs)
    rows, selected = [], []
    for number, bend in enumerate((0., .04, -.04)):
        start = q0.copy(); start[contract.body[0::3]] += bend
        def residual(v):
            q = q0.copy(); q[active] = v; poses = fk(q)
            thorax, full, forearm, chest = [analytic.measure(poses, n, gp, gr)['gap_m'] for n in ('R_Thorax', 'R_Shoulder', 'R_Elbow', 'Chest')]
            proximal = analytic.measure(poses, 'R_Shoulder', gp, gr, .3)['gap_m']
            delta = poses['R_Elbow'][0]-poses['R_Shoulder'][0]
            wrist = poses['R_Elbow'][0]-poses['R_Wrist'][0]
            return np.r_[6000*(thorax-.0003), 6000*(proximal-.002), 20000*min(full-.0002, 0),
                20000*min(thorax-.0002, 0), 6000*min(forearm-.014, 0), 10000*min(chest-.001, 0),
                20000*max(.020+delta[2], 0), 1000*max(.12-delta@right_axis, 0), 1000*max(.025-wrist@right_axis, 0),
                50*(poses['RH:palm'][0]-hand_goal), 8*(hand_rotation.inv()*poses['RH:palm'][1]).as_rotvec(),
                2*(v-q0[active])]
        fit = least_squares(residual, np.clip(start[active], lo+1e-8, hi-1e-8), bounds=(lo, hi), max_nfev=60, diff_step=1e-4, ftol=1e-10, xtol=1e-10, gtol=1e-8)
        q = q0.copy(); q[active] = fit.x
        # Keep the previous left near-neck placement in world space while the torso turns.
        llo, lhi = np.maximum(contract.lower[left]+1e-6, q0[left]-.4), np.minimum(contract.upper[left]-1e-6, q0[left]+.4)
        def left_res(v):
            z = q.copy(); z[left] = v; p, r = fk(z)['L_Wrist']
            return np.r_[1000*(p-left_goal), 80*(left_rotation.inv()*r).as_rotvec(), .1*(v-q0[left])]
        left_fit = least_squares(left_res, np.clip(q[left], llo+1e-8, lhi-1e-8), bounds=(llo, lhi), max_nfev=80)
        q[left] = left_fit.x
        hlo, hhi = np.maximum(contract.lower[head]+1e-6, q0[head]-.3), np.minimum(contract.upper[head]-1e-6, q0[head]+.3)
        def head_res(v):
            z = q.copy(); z[head] = v
            return np.r_[100*(original['Head'][1].inv()*fk(z)['Head'][1]).as_rotvec(), .1*(v-q0[head])]
        head_fit = least_squares(head_res, np.clip(q[head], hlo+1e-8, hhi-1e-8), bounds=(hlo, hhi), max_nfev=60)
        q[head] = head_fit.x; q = q.astype(np.float32).astype(float); poses = fk(q)
        caps = {n: analytic.measure(poses, n, gp, gr) for n in ('R_Thorax', 'R_Shoulder', 'R_Elbow', 'R_Hip', 'Chest')}
        proximal = analytic.measure(poses, 'R_Shoulder', gp, gr, .3)
        predicted = state_from_fk(state, bodies, q, fk); audit = source_audit(source_scene(predicted, bodies, geometry['asset']), parents)
        frozen = np.ones(81, dtype=bool); frozen[np.r_[active, left, head]] = False
        lerror = float(np.linalg.norm(poses['L_Wrist'][0]-left_goal))
        delta = poses['R_Elbow'][0]-poses['R_Shoulder'][0]
        wrist = poses['R_Elbow'][0]-poses['R_Wrist'][0]
        natural = {'elbow_below_m': float(-delta[2]), 'elbow_outward_m': float(delta@right_axis), 'wrist_inward_m': float(wrist@right_axis),
                   'head_error_deg': float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude())),
                   'left_wrist_rotation_error_deg': float(np.rad2deg((left_rotation.inv()*poses['L_Wrist'][1]).magnitude()))}
        natural_ok = natural['elbow_below_m'] >= .0199 and natural['elbow_outward_m'] >= .1199 and natural['wrist_inward_m'] >= .0249 and natural['head_error_deg'] <= 1 and natural['left_wrist_rotation_error_deg'] <= 1
        eligible = bool(all(c['gap_m'] >= .00005 for c in caps.values()) and natural_ok and audit['source_clear'] and .00005 <= caps['R_Thorax']['gap_m'] <= .006 and
                        .00005 <= proximal['gap_m'] <= .004 and caps['R_Shoulder']['gap_m'] >= .00005 and
                        caps['R_Elbow']['gap_m'] >= .012 and lerror < .015 and np.array_equal(q[frozen], q0[frozen]) and
                        np.all(q >= contract.lower) and np.all(q <= contract.upper))
        label = 'seed%d'%number
        row = {'label': label, 'accepted_for_native': eligible, 'natural_geometry': natural, 'natural_geometry_ok': natural_ok, 'joint_angles_rad': q.tolist(), 'capsule_body': caps,
            'proximal_upper_arm30_witness': proximal, 'proximal_upper_arm65_witness': proximal, 'proximal_fraction_limit': .3,
            'legacy_key_note': '65 compatibility key, actual source fraction0..30%', 'source_audit': audit,
            'left_wrist_world_error_m': lerror, 'fingers42_exact': bool(np.array_equal(q[frozen], q0[frozen])),
            'body_scalar_delta_rad': {names[i]: float(q[i]-q0[i]) for i in contract.body},
            'chest_relative_rotation_delta_rad': (original['Chest'][1].inv()*poses['Chest'][1]).as_rotvec().tolist(),
            'head_world_rotation_error_deg': float(np.rad2deg((original['Head'][1].inv()*poses['Head'][1]).magnitude())),
            'right_hand_world_error_m': float(np.linalg.norm(poses['RH:palm'][0]-hand_goal)), 'fit_nfev': int(fit.nfev)}
        rows.append(row); save(out/(label+'_audit.json'), row)
        print(label, 'accepted', eligible, 'thorax/prox/full/forearm mm', [caps['R_Thorax']['gap_m']*1000,
              proximal['gap_m']*1000, caps['R_Shoulder']['gap_m']*1000, caps['R_Elbow']['gap_m']*1000], 'clear', audit['source_clear'], flush=True)
        if eligible:
            folder = out/label; folder.mkdir()
            candidate = {**seed, 'joint_angles_rad': q.tolist(), 'position_W_m': seed['position_W_m'], 'quaternion_xyzw': seed['quaternion_xyzw'],
                'predicted_human_poses': {n: {'p': p.tolist(), 'q': r.as_quat().tolist()} for n, (p, r) in poses.items()},
                'body_side_lean_axilla': row, 'right_block_cradle': row,
                'no_strap_upper_arm_proposal': {'proximal_support': caps['R_Elbow']}}
            save(folder/'candidate.json', candidate); save(folder/'config.json', {**cfg, 'initial_candidate': str(folder/'candidate.json'),
                'initial_candidate_sha256': sha(folder/'candidate.json'), 'elbow_motion_amplitude_rad': 0.0})
            selected.append({'label': label, 'config': str(folder/'config.json')})
            break
    assert all(sha(p) == h for p, h in inputs.items())
    save(out/'search.json', {'input_sha256': inputs, 'rows': rows, 'selected': selected, 'native_runs': 0,
                            'scope': 'static source proposal then analytic capsule/full mesh LP audit; cooked contacts pending'})


if __name__ == '__main__': main()
