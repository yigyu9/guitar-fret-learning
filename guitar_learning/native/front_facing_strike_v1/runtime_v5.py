"""동작 중 오른말단6축 feedback의 오차 좌표만 child SO(3)로 교정한다."""
import xml.etree.ElementTree as ET
import numpy as np
from scipy.spatial.transform import Rotation
from ..initial_pose_noise_v1 import pose
from guitar_learning.native.paths import HUMAN
from ..lower_body_release_v1.control_math_v1 import rotation_error
from .runtime_v4 import Controller as PreviousController, Scene, PROTOCOL

MODE = 'finite_distal6_SO3_child_PD_v1'


class Controller(PreviousController):
    def __init__(self, scene):
        super().__init__(scene)
        assert scene.cfg['distal_rotational_feedback_mode'] == MODE
        assert scene.cfg['distal_rotational_feedback_start_s'] == 10.
        xml = ET.parse(HUMAN)
        self.rotational_groups = []
        for body, parent, K, D, cap in (('R_Elbow','R_Shoulder',60.,3.,100.),('R_Wrist','R_Elbow',20.,1.,60.)):
            joints = xml.find(".//body[@name='"+body+"']").findall('joint')
            ix = np.array([scene.names.index(j.get('name')) for j in joints])
            basis = np.column_stack([np.fromstring(j.get('axis'),sep=' ') for j in joints])
            assert [scene.names[j] for j in ix] == [body+'_'+a for a in 'xyz']
            assert np.array_equal(basis.T@basis,np.eye(3))
            assert np.array_equal(scene.control_kp[ix],np.full(3,K)) and np.array_equal(scene.control_kd[ix],np.full(3,D))
            assert np.array_equal(scene.pd_properties['effort'][ix],np.full(3,cap))
            assert set(ix)<=set(scene.upper_effort_indices) and not set(ix)&set(scene.zero_indices)
            self.rotational_groups.append((body,parent,ix,basis))

    def effort(self):
        effort, row = super().effort()
        s = self.s
        if s.steps < 2400:
            return effort, row
        state = s.native()
        q = np.array([v['pos'] for v in state['human_dof_states']])
        qd = np.array([v['vel'] for v in state['human_dof_states']])
        target = s.target.astype(float).copy()
        delta = np.zeros(105)
        groups = []
        for body,parent,ix,basis in self.rotational_groups:
            child_state = state['human_body_states'][s.human_bodies.index(body)]
            parent_state = state['human_body_states'][s.human_bodies.index(parent)]
            _, child_r = pose(child_state)
            _, parent_r = pose(parent_state)
            relative = parent_r.inv()*child_r
            coordinate_error = float((Rotation.from_rotvec(basis@q[ix]).inv()*relative).magnitude())
            omega = np.array([child_state['vel']['angular'][a]-parent_state['vel']['angular'][a] for a in 'xyz'])
            predicted = child_r.apply(basis@qd[ix])
            velocity_error = float(np.linalg.norm(omega-predicted))
            assert coordinate_error < 1e-5 and velocity_error < .01
            scalar_error = target[ix]-q[ix]
            error = rotation_error(q[ix],target[ix],basis)
            scalar_pd = s.control_kp[ix]*scalar_error-s.control_kd[ix]*qd[ix]
            rotational_pd = s.control_kp[ix]*error-s.control_kd[ix]*qd[ix]
            assert np.max(abs(scalar_pd-np.array(row['scalar_PD105_Nm'])[ix])) < 1e-12
            delta[ix] = s.control_kp[ix]*(error-scalar_error)
            groups.append(dict(body=body,parent=parent,indices105=ix.tolist(),joint_names=[s.names[j] for j in ix],
                basis3x3=basis.tolist(),q3_rad=q[ix].tolist(),target3_rad=target[ix].tolist(),native_qd3_rad_s=qd[ix].tolist(),
                K3_Nm_rad=s.control_kp[ix].tolist(),D3_Nms_rad=s.control_kd[ix].tolist(),caps3_Nm=s.pd_properties['effort'][ix].astype(float).tolist(),
                scalar_error3_rad=scalar_error.tolist(),SO3_error3_child_axes_rad=error.tolist(),scalar_PD3_Nm=scalar_pd.tolist(),
                rotational_PD3_Nm=rotational_pd.tolist(),delta3_Nm=delta[ix].tolist(),actual_relative_xyzw=relative.as_quat().tolist(),
                coordinate_residual_rad=coordinate_error,actual_relative_angular_W_rad_s=omega.tolist(),
                predicted_relative_angular_W_rad_s=predicted.tolist(),velocity_residual_rad_s=velocity_error))
        ix = np.concatenate([g[2] for g in self.rotational_groups])
        assert len(ix)==6 and len(set(ix))==6
        old_raw = np.array(row['raw_requested105_Nm'])
        old_submitted = effort.copy()
        old_scalar = np.array(row['scalar_PD105_Nm'])
        old_task = np.array(row['support_task105_Nm'])
        request = old_raw+delta
        effort[ix] = np.clip(request[ix],-s.pd_properties['effort'][ix],s.pd_properties['effort'][ix]).astype(np.float32)
        outside = np.setdiff1d(np.arange(105),ix)
        assert np.array_equal(effort[outside],old_submitted[outside])
        assert np.array_equal(effort[s.lower_indices],old_submitted[s.lower_indices])
        assert np.array_equal(effort[s.position_indices],old_submitted[s.position_indices])
        assert np.array_equal(effort[s.zero_indices],old_submitted[s.zero_indices])
        row['distal_rotational_feedback'] = dict(mode=MODE,start_s=10.,indices105=ix.tolist(),joint_names=[s.names[j] for j in ix],
            groups=groups,delta105_Nm=delta.tolist(),previous_raw_requested105_Nm=old_raw.tolist(),
            previous_submitted105_Nm=old_submitted.astype(float).tolist(),previous_scalar_PD105_Nm=old_scalar.tolist(),
            previous_support_task105_Nm=old_task.tolist(),outside6_unchanged=True,lower_unchanged=True,
            position48_unchanged=True,zero8_unchanged=True,state_preserved=True,target_preserved=True,
            scope='Controller4의 Chest0.5mm 이후 distal6 feedback 오차만 SO3 child축으로 교체. scalar_PD105는 원진단으로 보존, 실제raw=gravity+scalarPD+supporttask+이delta. 원K/D/cap·nativeqd·관절목표·materialtask 불변. Mass predictor/gain/G힘/상태주입 없음.')
        row.update(raw_requested105_Nm=request.tolist(),submitted105_Nm=effort.astype(float).tolist())
        assert np.isfinite(effort).all() and np.array_equal(s.target.astype(float),target) and s.native()==state
        return effort,row
