"""Existing env0/60Hz evidence only; no native import or simulator."""
import ast
import math
from types import SimpleNamespace
import sys

from common import HERE, ROOT, DIAG, VIDEO, CLOCKS, sha, write
sys.path.insert(0, str(ROOT))


def main():
    import json
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation as R
    from guitar_learning.runtime import prepared_reset_v1 as prepared
    from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
    from guitar_learning.native.lower_body_release_v1.common import HUMAN
    from guitar_learning.core.control import LEFT_ARM_NAMES
    assert not torch.cuda.is_available()
    meta_path = DIAG/'02_contact_reward/teacher_fixed_B_export/metadata.json'
    meta = json.loads(meta_path.read_text())
    capture = json.loads((VIDEO/'capture_metadata.json').read_text())
    assert capture['joint_names'] == meta['joint_names'] and capture['body_names'] == meta['body_names']
    state = prepared.load_prepared_reset_contract()['state']
    qref = np.array([row['pos'] for row in state['human_dof_states']])
    fk = full_fk(SimpleNamespace(names=meta['joint_names'], human_bodies=meta['human_bodies'], q_ref=qref), state)
    a = np.load(VIDEO/'poses_env0000.npz')
    wrist, guitar = (meta['body_names'].index(name) for name in ('human/L_Wrist', 'guitar/guitar'))
    arm = [meta['joint_names'].index(name) for name in LEFT_ARM_NAMES]
    com = np.array(meta['body_com'][wrist])
    assert np.array_equal(a['physics_step'], 4*a['control_tick'])
    assert np.allclose(a['time_s'], a['physics_step']/240, atol=1e-12)
    assert a['physics_step'][0] == 4 and np.all(np.diff(a['physics_step']) == 4)

    def jac(q, eps):
        result = np.empty((6, 105))
        for col in range(105):
            plus, minus = q.copy(), q.copy()
            plus[col] += eps; minus[col] -= eps
            pp, rp = fk(plus)['L_Wrist']; pm, rm = fk(minus)['L_Wrist']
            result[:, col] = np.r_[(pp-pm)/(2*eps), (rp*rm.inv()).as_rotvec()/(2*eps)]
        return result

    def velocity(row):
        body = a['body_state'][row, wrist].astype(float)
        return np.r_[body[7:10]+np.cross(body[10:13], R.from_quat(body[3:7]).apply(-com)), body[10:13]]

    rows = []
    for clock in CLOCKS:
        pre = int(np.flatnonzero(a['physics_step'] == clock)[0]); end = pre+1
        # Float64 perturbations avoid perturbation quantization of float32 native qpos.
        q = a['q'][end].astype(float)
        j = jac(q, 1e-5); jhalf = jac(q, 5e-6)
        pos, rot = fk(q)['L_Wrist']; body = a['body_state'][end, wrist]
        qdot = (a['q'][end+1].astype(float)-a['q'][end-1].astype(float))*30
        actual = velocity(end)
        native_error = j@a['qd'][end]-actual
        central_error = j@qdot-actual
        bp, bm = a['body_state'][end+1, wrist], a['body_state'][end-1, wrist]
        central_body = np.r_[(bp[:3].astype(float)-bm[:3].astype(float))*30,
            (R.from_quat(bp[3:7])*R.from_quat(bm[3:7]).inv()).as_rotvec()*30]
        prebody = a['body_state'][pre, wrist].astype(float)
        gp = a['body_state'][pre, guitar].astype(float); gr = R.from_quat(gp[3:7])
        goalp = gp[:3]+gr.apply(a['wrist_goal_G_m'][end])
        goalr = gr*R.from_quat(a['wrist_goal_G_xyzw'][end])
        error = np.r_[goalp-prebody[:3], .1*(goalr*R.from_quat(prebody[3:7]).inv()).as_rotvec()]
        weighted_j = jac(a['q'][pre].astype(float), 1e-5)[:, arm]
        weighted_j[3:] *= .1
        dls = weighted_j.T@np.linalg.solve(weighted_j@weighted_j.T+1e-5*np.eye(6), error)
        dls = np.clip(dls, -math.radians(.5), math.radians(.5))
        stored = a['wrist_requested_delta_rad'][end]
        rows.append(dict(endpoint_time_s=float(a['time_s'][end]), endpoint_row=end,
            precontrol_row=pre, precontrol_clock=clock, endpoint_tick=int(a['control_tick'][end]),
            FK_position_error_m=float(np.linalg.norm(pos-body[:3])),
            FK_rotation_error_rad=float((rot*R.from_quat(body[3:7]).inv()).magnitude()),
            FD_half_epsilon_max_abs=float(abs(j-jhalf).max()),
            native_qd_linear_error_m_s=float(np.linalg.norm(native_error[:3])),
            native_qd_angular_error_rad_s=float(np.linalg.norm(native_error[3:])),
            central_qpos_linear_error_m_s=float(np.linalg.norm(central_error[:3])),
            central_qpos_angular_error_rad_s=float(np.linalg.norm(central_error[3:])),
            central_body_linear_error_m_s=float(np.linalg.norm(central_body[:3]-actual[:3])),
            central_body_angular_error_rad_s=float(np.linalg.norm(central_body[3:]-actual[3:])),
            native_qd_vs_central_qpos_rate_norm_rad_s=float(np.linalg.norm(a['qd'][end]-qdot)),
            precontrol_pose_error_max_abs=float(abs(error-a['wrist_pose_error_world'][end]).max()),
            qpos_DLS_vs_stored_delta_max_deg=float(np.rad2deg(abs(dls-stored)).max()),
            qpos_DLS_delta_deg=np.rad2deg(dls).tolist(), stored_delta_deg=np.rad2deg(stored).tolist()))
    example = ROOT/'isaacgym/python/examples/spherical_joint.py'
    node = next(n for n in ast.parse(example.read_text()).body if isinstance(n, ast.FunctionDef) and n.name == 'quat2expcoord')
    scope = dict(np=np, math=math)
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(example), 'exec'), scope)
    vectors = (np.array([.2, -.7, .1]), np.array([-.8, .4, 1.2]))
    roundtrip = max(np.linalg.norm(scope['quat2expcoord'](R.from_rotvec(v).as_quat())-v) for v in vectors)
    assert roundtrip < 1e-14
    assert max(r['precontrol_pose_error_max_abs'] for r in rows) < 2e-7
    assert max(r['FK_position_error_m'] for r in rows) < 1e-5
    paths = [VIDEO/'poses_env0000.npz', VIDEO/'capture_metadata.json', meta_path, example, __file__,
        ROOT/'guitar_learning/native/lower_body_release_v1/controller_horizontal_v4.py', HUMAN,
        ROOT/'guitar_learning/runtime/prepared_reset_v1.py', *prepared.SOURCE_SHA256]
    write(HERE/'cpu_evidence.json', dict(CPU_only=True, GPU_executed=False, rows=rows,
        local_example_AST_only_nonzero_roundtrip_max_error=float(roundtrip), input_pins={str(p):sha(p) for p in paths},
        limitations=['60Hz central differences are time-averaged approximations, not exact instantaneous qpos rates',
            'local position example does not establish installed native qd velocity coordinates',
            'native simultaneous Jacobian/frame/COM/column comparison still required']))
    print('CPU evidence saved; no native execution')


if __name__ == '__main__':
    main()
