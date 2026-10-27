"""Batched finite human controls; no actor state or guitar force writes.

The source geometry mass law is ported to tensor operations. Foot IK uses a
fixed-iteration damped solver, and Chest proximity uses source triangles rather
than SciPy's convex optimizer. These are a new control contract, not CPU parity.
"""
import itertools
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import torch
from guitar_learning.core.control import ACTIVE_NAMES, LEFT_HAND_NAMES
from guitar_learning.runtime.native_session import target_rates
from guitar_learning.native.paths import A, resolve_input_path
from .geometry import apply, conjugate, multiply, rotvec, origin_velocity


def exp_rotation(value):
    size = torch.linalg.vector_norm(value, dim=-1, keepdim=True)
    scale = .5 * torch.sinc(size / (2 * torch.pi))
    return torch.cat((value * scale, torch.cos(.5 * size)), -1)


def rotation_error(q, target, basis):
    """Original child-axis SO(3) error, with arbitrary leading batch axes."""
    current = exp_rotation(torch.matmul(basis, q.unsqueeze(-1)).squeeze(-1))
    desired = exp_rotation(torch.matmul(basis, target.unsqueeze(-1)).squeeze(-1))
    error = rotvec(multiply(conjugate(current), desired))
    return torch.matmul(basis.transpose(-1, -2), error.unsqueeze(-1)).squeeze(-1)


def stable_pd(mass, error, velocity, kp, kd, gravity, dt=1/240.):
    """Finite backward-Euler feedback with gravity outside the predictor RHS."""
    mass = .5 * (mass + mass.transpose(-1, -2))
    lhs = mass + torch.diag_embed(dt * kd + dt * dt * kp)
    rhs = torch.matmul(mass, velocity.unsqueeze(-1)).squeeze(-1) + dt * kp * error
    predicted = torch.linalg.solve(lhs, rhs.unsqueeze(-1)).squeeze(-1)
    feedback = kp * error - (kd + dt * kp) * predicted
    return gravity + feedback, predicted, feedback


def _point_triangle(point, triangles):
    a, b, c = triangles.unbind(-2)
    normal = torch.cross(b-a, c-a, dim=-1)
    projected = point - (((point-a)*normal).sum(-1, keepdim=True) /
                         (normal*normal).sum(-1, keepdim=True).clamp_min(1e-20))*normal
    edge0, edge1, delta = b-a, c-a, projected-a
    d00, d01 = (edge0*edge0).sum(-1), (edge0*edge1).sum(-1)
    d11 = (edge1*edge1).sum(-1)
    d20, d21 = (delta*edge0).sum(-1), (delta*edge1).sum(-1)
    denom = (d00*d11-d01*d01).clamp_min(1e-20)
    v, w = (d11*d20-d01*d21)/denom, (d00*d21-d01*d20)/denom
    inside = (v >= 0) & (w >= 0) & (v+w <= 1) & ((normal*normal).sum(-1) > 1e-20)
    starts, ends = triangles, triangles.roll(-1, dims=-2)
    edges = ends-starts
    t = (((point.unsqueeze(-2)-starts)*edges).sum(-1) /
         (edges*edges).sum(-1).clamp_min(1e-20)).clamp(0, 1)
    candidates = starts+t.unsqueeze(-1)*edges
    distance = ((candidates-point.unsqueeze(-2))**2).sum(-1)
    closest = candidates.gather(-2, distance.argmin(-1)[..., None, None].expand(*distance.shape[:-1], 1, 3)).squeeze(-2)
    return torch.where(inside[..., None], projected, closest)


def capsule_triangle_witness(a, b, triangles):
    """Closest points of batched segments and a static triangle surface union.

    Endpoints, three edges, and interior plane intersections exhaust the closest
    feature cases. The result is source mesh proximity, not cooked penetration.
    """
    a, b = a[:, None, :], b[:, None, :]
    if triangles.ndim == 3:
        triangles = triangles[None]
    surface_a, surface_b = _point_triangle(a, triangles), _point_triangle(b, triangles)
    starts, ends = triangles, triangles.roll(-1, dims=-2)
    u, v, w = (b-a).unsqueeze(-2), ends-starts, a.unsqueeze(-2)-starts
    aa, bb, cc = (u*u).sum(-1), (u*v).sum(-1), (v*v).sum(-1)
    dd, ee = (u*w).sum(-1), (v*w).sum(-1)
    denom = aa*cc-bb*bb
    s = torch.where(denom > 1e-18, (bb*ee-cc*dd)/denom.clamp_min(1e-18), torch.zeros_like(denom)).clamp(0, 1)
    t = ((bb*s+ee)/cc.clamp_min(1e-20)).clamp(0, 1)
    s = ((bb*t-dd)/aa.clamp_min(1e-20)).clamp(0, 1)
    t = ((bb*s+ee)/cc.clamp_min(1e-20)).clamp(0, 1)
    line_edges, surface_edges = a.unsqueeze(-2)+s[..., None]*u, starts+t[..., None]*v
    normal = torch.cross(triangles[..., 1, :]-triangles[..., 0, :],
                         triangles[..., 2, :]-triangles[..., 0, :], dim=-1)
    dn = ((b-a)*normal).sum(-1)
    fraction = ((triangles[..., 0, :]-a)*normal).sum(-1) / torch.where(dn.abs() > 1e-15, dn, torch.ones_like(dn))
    intersection = a+fraction[..., None]*(b-a)
    projected = _point_triangle(intersection, triangles)
    valid = (dn.abs() > 1e-15) & (fraction >= 0) & (fraction <= 1) & (((intersection-projected)**2).sum(-1) < 1e-16)
    line = torch.cat((a.expand_as(surface_a).unsqueeze(-2), b.expand_as(surface_b).unsqueeze(-2), line_edges, intersection.unsqueeze(-2)), -2)
    surface = torch.cat((surface_a.unsqueeze(-2), surface_b.unsqueeze(-2), surface_edges, projected.unsqueeze(-2)), -2)
    distance = ((line-surface)**2).sum(-1)
    distance[..., -1] = torch.where(valid, distance[..., -1], torch.full_like(distance[..., -1], float('inf')))
    index = distance.flatten(1).argmin(-1)
    gather = index[:, None, None].expand(-1, 1, 3)
    return line.flatten(1, 2).gather(1, gather).squeeze(1), surface.flatten(1, 2).gather(1, gather).squeeze(1)


def source_capsule_witness(a, b, triangles, low, high, candidate_count=512):
    """Certify AABB candidates, then exhaust the surface for uncertified rows.

    Only candidate failure rows use the expensive exact path. Six feature
    cases per triangle are evaluated in chunks of at most16 environments;
    state and geometry stay on the tensor device throughout.
    """
    bound_delta = torch.maximum(torch.maximum(low[None]-torch.maximum(a, b)[:, None],
        torch.minimum(a, b)[:, None]-high[None]), torch.zeros((), device=a.device, dtype=a.dtype))
    bounds = torch.linalg.vector_norm(bound_delta, dim=-1)
    selected_bounds, selected = bounds.topk(min(candidate_count, triangles.shape[0]),
                                           dim=-1, largest=False, sorted=True)
    axis, surface = capsule_triangle_witness(a, b, triangles[selected])
    finite = torch.isfinite(axis).all(-1) & torch.isfinite(surface).all(-1)
    fast_certified = finite & (torch.linalg.vector_norm(axis-surface, dim=-1) <= selected_bounds[:, -1]+1e-7)
    certified = fast_certified.clone()
    fallback = ~fast_certified
    rows = fallback.nonzero().flatten()
    for chunk in rows.split(16):
        # No omitted source triangles remain, so finite global results certify.
        exact_axis, exact_surface = capsule_triangle_witness(a[chunk], b[chunk], triangles)
        axis[chunk], surface[chunk] = exact_axis, exact_surface
        certified[chunk] = torch.isfinite(exact_axis).all(-1) & torch.isfinite(exact_surface).all(-1)
    return axis, surface, certified, fallback, fast_certified


class BatchedController:
    def __init__(self, scene):
        self.scene, self.device = scene, scene.device
        self.dtype = scene.q.dtype
        self.names, self.bodies = tuple(scene.names), tuple(scene.human_bodies)
        self.num_envs = scene.num_envs
        self.reference = scene.reference105.clone()
        self.target = self.reference.expand(self.num_envs, -1).clone()
        self.lower, self.upper = scene.lower, scene.upper
        self.initial = scene.contract['initial']
        self.config = scene.contract['config']
        if len(self.names) != 105 or len(set(self.names)) != 105:
            raise ValueError('Exact named native105 required')
        self.active = self.index([self.names.index(n) for n in ACTIVE_NAMES])
        self.leg = self.index([self.names.index(side+'_'+part+'_'+axis) for side in ('L', 'R') for part in ('Hip', 'Knee', 'Ankle', 'Toe') for axis in 'xyz'])
        self.moving_leg = self.index([self.names.index(side+'_'+part+'_'+axis) for side in ('L', 'R') for part, axes in (('Hip', 'xyz'), ('Knee', 'x'), ('Ankle', 'xyz'), ('Toe', 'x')) for axis in axes])
        self.foot_channels = self.index([self.names.index(side+'_'+name) for side in ('L', 'R') for name in ('Knee_x', 'Ankle_x', 'Ankle_y', 'Ankle_z', 'Toe_x')])
        self.zero = self.index(self.initial['zero_range_indices'])
        self.position = self.index(self.initial['position_indices'])
        self.effort = self.index(self.initial['effort_indices'])
        if (len(self.zero) != 8 or len(self.position) != 48 or len(self.effort) != 57):
            raise ValueError('Pinned 105/97/8 and mixed48/57 control required')
        self.caps = self.tensor(self.initial['native_PD_properties']['effort'])
        self.kp, self.kd = scene.native_control_kp.to(self.dtype), scene.native_control_kd.to(self.dtype)
        half = self.tensor([.5 if n.startswith('LH:') else .35 if n.startswith('L_') else .25 for n in ACTIVE_NAMES])
        self.rate = self.tensor(target_rates(self.names))
        self.alpha = self.tensor([.2]*39)
        if scene.hand == 'left':
            for name in LEFT_HAND_NAMES:
                i, j = self.names.index(name), ACTIVE_NAMES.index(name)
                half[j] = torch.maximum(self.reference[i]-self.lower[i], self.upper[i]-self.reference[i])
                self.rate[i], self.alpha[j] = 4., .45
        self.action_low = torch.maximum(self.lower[self.active], self.reference[self.active]-half)
        self.action_high = torch.minimum(self.upper[self.active], self.reference[self.active]+half)
        self._load_geometry()
        self._load_support()
        # Original initial environment gains; lower native PD fields themselves are zero.
        native_config = json.loads((A/'config.json').read_text())
        gains = json.loads(resolve_input_path(native_config['gain_source']).read_text())
        lower_k, lower_d = [], []
        for i in self.moving_leg.cpu().tolist():
            gain = min(max(gains.get(self.names[i], [50, 5])[0], 30), 600)
            lower_k.append(gain)
            lower_d.append(max(.25*gain, gains.get(self.names[i], [50, 5])[1]))
        self.lower_kp, self.lower_kd = self.tensor(lower_k), self.tensor(lower_d)
        self.contract = dict(schema='guitar_learning.gpu_finite_control.v2', action_dim=39, target_dim=105,
            joint_names=list(self.names), action_order=list(ACTIVE_NAMES), physics_hz=240, control_hz=60,
            position_indices=self.initial['position_indices'], effort_indices=self.initial['effort_indices'],
            zero_indices=self.initial['zero_range_indices'], native_position_count=48, native_effort_count=57,
            reference105_rad=self.reference.cpu().tolist(), action_lower_rad=self.action_low.cpu().tolist(),
            action_upper_rad=self.action_high.cpu().tolist(), smoothing_alpha=self.alpha.cpu().tolist(),
            rate_rad_s=self.rate.cpu().tolist(), flexible_left21=scene.hand == 'left',
            lower_control='source_geometry_COM_inertia_mass_implicit_SO3_PD16_plus_hip_bias',
            foot_IK='eight_fixed_tensor_DLS_steps_ten_channels_four_source_soles',
            upper_control='native_COM_J_gravity_scalar_PD_Chest10mm_right_world_support_distalSO3',
            chest_proximity='source_triangle_capsule_closest_features_not_cooked_contact',
            chest_search='certified_AABB512_then_full_surface_exact_fallback_in_chunks16',
            initial_jacobian='geometry_fallback_until_first_step_after_boundary_reset',
            source_contract='035_v14_prepared22s', native_cpu_parity=False,
            differences=['GPU PhysX solver and native contact backend',
                         'Explicit geometry lower mass; native CUDA mass comparison is recorded separately',
                         'Fixed-step damped foot IK replaces CPU SciPy least_squares',
                         'Triangle source proximity replaces CPU convex optimizer',
                         'Initial/reset upper Jacobian uses source child-axis geometry until GPU refresh'])
        self.metadata = self.contract
        self.diagnostics = {}

    def tensor(self, value):
        return torch.as_tensor(value, dtype=self.dtype, device=self.device)

    def index(self, value):
        return torch.as_tensor(value, dtype=torch.long, device=self.device)

    def _load_geometry(self):
        human_path = resolve_input_path(self.initial['loaded_assets'][0]['path'])
        self.human_xml = ET.parse(human_path)
        elements = {b.get('name'): b for b in self.human_xml.iter('body')}
        parents = {c.get('name'): p.get('name') for p in self.human_xml.iter('body') for c in p.findall('body')}
        ancestor = [[False]*105 for _ in self.bodies]
        joint_bodies, axes = [0]*105, [[0., 0., 0.] for _ in self.names]
        self.groups = {}
        for name, element in elements.items():
            if name not in self.bodies:
                continue
            joints = element.findall('joint')
            if not joints:
                continue
            ix = [self.names.index(j.get('name')) for j in joints]
            basis = self.tensor([[float(x) for x in j.get('axis').split()] for j in joints]).T
            self.groups[name] = (self.index(ix), basis)
            descendants = {n.get('name') for n in element.iter('body')}
            for j, joint in zip(ix, joints):
                joint_bodies[j] = self.bodies.index(name)
                axes[j] = [float(x) for x in joint.get('axis').split()]
                for body_index, body_name in enumerate(self.bodies):
                    ancestor[body_index][j] = body_name in descendants
        self.ancestry, self.joint_bodies, self.axes = self.tensor(ancestor), self.index(joint_bodies), self.tensor(axes)
        initial_state = self.initial['native_state']
        self.initial_bodies = self.tensor([[*[r['pose']['p'][a] for a in 'xyz'], *[r['pose']['r'][a] for a in 'xyzw']] for r in initial_state['human_body_states']])
        self.initial_q = self.tensor([r['pos'] for r in initial_state['human_dof_states']])
        self.lower_bodies = self.index([self.bodies.index(side+'_'+part) for side in ('L', 'R') for part in ('Hip', 'Knee', 'Ankle', 'Toe')])
        self.fk_rows, self.sole_points = [], []
        lower_names = ['Pelvis'] + [side+'_'+part for side in ('L', 'R') for part in ('Hip', 'Knee', 'Ankle', 'Toe')]
        self.lower_name_order = lower_names
        self.foot_fk_joint_ids = self.index([lower_names.index(self.bodies[i]) for i in self.joint_bodies[self.foot_channels].cpu().tolist()])
        self.lower_error_groups = []
        moving_names = {self.names[i] for i in self.moving_leg.cpu().tolist()}
        for side in ('L', 'R'):
            for part in ('Hip', 'Knee', 'Ankle', 'Toe'):
                ix, basis = self.groups[side+'_'+part]
                keep = self.index([j for j, i in enumerate(ix.cpu().tolist()) if self.names[i] in moving_names])
                self.lower_error_groups.append((ix, basis, keep))
        self.human_ids, self.all_joint_ids = self.index(range(len(self.bodies))), self.index(range(105))
        for name in lower_names[1:]:
            body_id, parent_id = self.bodies.index(name), self.bodies.index(parents[name])
            ix, basis = self.groups[name]
            pose, parent = self.initial_bodies[body_id], self.initial_bodies[parent_id]
            local = apply(conjugate(parent[3:7]), pose[:3]-parent[:3])
            relative = multiply(conjugate(parent[3:7]), pose[3:7])
            zero = multiply(conjugate(exp_rotation(basis@self.initial_q[ix])), relative)
            self.fk_rows.append((lower_names.index(parents[name]), ix, basis, local, zero))
            if name.endswith(('Ankle', 'Toe')):
                geom = elements[name].find('geom')
                half = self.tensor([float(x) for x in geom.get('size').split()])
                center = self.tensor([float(x) for x in geom.get('pos').split()])
                wxyz = [float(x) for x in geom.get('quat', '1 0 0 0').split()]
                rotation = self.tensor(wxyz[1:]+wxyz[:1])
                signs = self.tensor(list(itertools.product((-1., 1.), repeat=3)))
                signs = signs[signs[:, 2] == -1]
                self.sole_points.append((lower_names.index(name), self.bodies.index(name), center+apply(rotation, signs*half)))

    def _load_support(self):
        candidate = json.loads(Path(self.config['candidate']).read_text())
        support = json.loads(resolve_input_path(candidate['support_candidate']).read_text())['right_block_cradle']
        witness = support['upper_arm_witness']
        surface, axis = self.tensor(witness['guitar_surface_G_m']), self.tensor(witness['capsule_axis_G_m'])
        normal = (axis-surface)/torch.linalg.vector_norm(axis-surface)
        state = self.initial['native_state']
        guitar = state['guitar_body_states'][0]
        gp = self.tensor([guitar['pose']['p'][a] for a in 'xyz'])
        gr = self.tensor([guitar['pose']['r'][a] for a in 'xyzw'])
        shoulder = self.initial_bodies[self.bodies.index('R_Shoulder')]
        point = gp+apply(gr, surface+normal*witness['gap_m'])
        self.right_local = apply(conjugate(shoulder[3:7]), point-shoulder[:3])
        goal = gp+apply(gr, surface+normal*(witness['gap_m']-.004))
        correction = json.loads(Path(self.config['finite_right_goal_spec']).read_text())
        self.right_goal = apply(self.tensor(correction['R_delta_xyzw']), goal)+self.tensor(correction['translation_W_m'])
        self.right_support_indices = self.index([i for i, n in enumerate(self.names) if n.startswith(('Torso_', 'Spine_', 'Chest_', 'R_Thorax_', 'R_Shoulder_'))])
        self.chest_indices = self.index([i for i, n in enumerate(self.names) if n.startswith(('Torso_', 'Spine_', 'Chest_'))])
        hip = json.loads(Path(self.config['hip_load_bias_spec']).read_text())
        self.hip_indices = self.index(hip['joint_indices105'])
        self.hip_bias = self.tensor(hip['bias_Nm'])
        chest = self.human_xml.find(".//body[@name='Chest']/geom")
        self.chest_segment = self.tensor([float(x) for x in chest.get('fromto').split()]).reshape(2, 3)
        self.chest_radius = float(chest.get('size'))
        asset = resolve_input_path(self.initial['loaded_assets'][1]['path'])
        xml = ET.parse(asset)
        body = xml.find(".//body[@name='G:body']")
        shift = self.tensor([float(x) for x in body.get('pos', '0 0 0').split()])
        assets = {m.get('name'): m for m in xml.findall('./asset/mesh')}
        meshdir = xml.find('compiler')
        meshdir = '' if meshdir is None else meshdir.get('meshdir', '')
        triangles = []
        for geom in body.findall('geom'):
            if geom.get('contype') == '0' or geom.get('conaffinity') == '0':
                continue
            path = asset.parent/meshdir/assets[geom.get('mesh')].get('file')
            vertices = []
            for row in path.read_text().splitlines():
                fields = row.split()
                if fields and fields[0] == 'v':
                    vertices.append([float(v) for v in fields[1:4]])
                elif fields and fields[0] == 'f':
                    face = [int(v.split('/')[0])-1 for v in fields[1:]]
                    for j in range(1, len(face)-1):
                        triangles.append([vertices[face[0]], vertices[face[j]], vertices[face[j+1]]])
        if not triangles:
            raise ValueError('Source convex triangle surfaces required for Chest control')
        triangles = self.tensor(triangles)+shift
        area = torch.cross(triangles[:, 1]-triangles[:, 0], triangles[:, 2]-triangles[:, 0], dim=-1)
        self.chest_triangles = triangles[(area*area).sum(-1) > 1e-20]
        self.triangle_low = self.chest_triangles.amin(1)
        self.triangle_high = self.chest_triangles.amax(1)

    def reset(self, indices, snapshot):
        indices = torch.as_tensor(indices, dtype=torch.long, device=self.device).flatten()
        self.target[indices] = self.reference

    def _lower_fk(self, q):
        count = q.shape[0]
        root = self.initial_bodies[self.bodies.index('Pelvis')]
        positions, rotations = [root[:3].expand(count, -1)], [root[3:7].expand(count, -1)]
        for parent, ix, basis, local, zero in self.fk_rows:
            positions.append(positions[parent]+apply(rotations[parent], local))
            joint = exp_rotation(q[:, ix]@basis.T)
            rotations.append(multiply(rotations[parent], multiply(joint, zero.expand_as(joint))))
        return torch.stack(positions, 1), torch.stack(rotations, 1)

    def _geometry_jacobian(self, body, body_ids, joint_ids, local=None):
        joint_pose = body[:, self.joint_bodies[joint_ids]]
        axes = apply(joint_pose[..., 3:7], self.axes[joint_ids])
        selected = body[:, body_ids]
        point = selected[..., :3]+apply(selected[..., 3:7], self.scene.com[body_ids] if local is None else local)
        delta = point[:, :, None]-joint_pose[:, None, :, :3]
        angular = axes[:, None]*self.ancestry[body_ids][:, joint_ids][None, :, :, None]
        linear = torch.cross(angular.expand_as(delta), delta, dim=-1)
        return linear.transpose(-1, -2), angular.transpose(-1, -2).expand_as(linear.transpose(-1, -2))

    def _foot_targets(self, request):
        q = request.clone()
        lo = torch.maximum(self.lower[self.foot_channels]+1e-7, self.reference[self.foot_channels]-.6)
        hi = torch.minimum(self.upper[self.foot_channels]-1e-7, self.reference[self.foot_channels]+.6)
        q[:, self.foot_channels] = torch.maximum(torch.minimum(self.target[:, self.foot_channels], hi), lo)
        eye = torch.eye(10, device=self.device, dtype=self.dtype)
        for _ in range(8):
            pos, rot = self._lower_fk(q)
            points, jacobians = [], []
            axes = apply(rot[:, self.foot_fk_joint_ids], self.axes[self.foot_channels])
            origin = pos[:, self.foot_fk_joint_ids]
            for fk_id, body_id, local in self.sole_points:
                bottom = pos[:, fk_id, None]+apply(rot[:, fk_id, None], local)
                mask = self.ancestry[body_id, self.foot_channels]
                j = torch.cross(axes[:, None].expand(-1, 4, -1, -1), bottom[:, :, None]-origin[:, None], dim=-1)*mask[None, None, :, None]
                points.append(2000*(bottom[..., 2]+.00025))
                jacobians.append(2000*j[..., 2])
                # Same source foot origin XY anchoring; the z terms dominate.
                reference = self.initial_bodies[body_id, :2]
                origin_j = torch.cross(axes, pos[:, fk_id, None]-origin, dim=-1)*mask[None, :, None]
                points.append(2*(pos[:, fk_id, :2]-reference))
                jacobians.append(2*origin_j.transpose(-1, -2)[:, :2])
            residual = torch.cat(points, -1)
            jacobian = torch.cat(jacobians, 1)
            jt = jacobian.transpose(-1, -2)
            lhs = jt@jacobian + .01*eye
            rhs = -(jt@residual.unsqueeze(-1)).squeeze(-1)-.0004*(q[:, self.foot_channels]-self.reference[self.foot_channels])
            step = torch.linalg.solve(lhs, rhs.unsqueeze(-1)).squeeze(-1).clamp(-.05, .05)
            q[:, self.foot_channels] = torch.maximum(torch.minimum(q[:, self.foot_channels]+step, hi), lo)
        self.diagnostics['foot_residual'] = residual
        return q

    def targets(self, action, snapshot):
        if action.shape != (self.num_envs, 39) or action.device != self.device:
            raise ValueError('Device-aligned action[N,39] required')
        action = action.clamp(-1, 1)
        ref = self.reference[self.active]
        requested = ref+torch.where(action >= 0, self.action_high-ref, ref-self.action_low)*action
        old = self.target[:, self.active]
        smoothed = old+self.alpha*(requested-old)
        active = torch.maximum(torch.minimum(smoothed, old+self.rate[self.active]/60), old-self.rate[self.active]/60)
        target = self.reference.expand(self.num_envs, -1).clone()
        target[:, self.active] = torch.maximum(torch.minimum(active, self.action_high), self.action_low)
        target = self._foot_targets(target)
        target = torch.maximum(torch.minimum(target, self.target+self.rate/60), self.target-self.rate/60)
        target = torch.maximum(torch.minimum(target, self.upper), self.lower)
        target[:, self.zero] = self.reference[self.zero]
        self.target.copy_(target)
        return self.target

    def efforts(self, snapshot):
        body, q, qd = snapshot['body_state'], snapshot['q'], snapshot['qd']
        geo_v, geo_w = self._geometry_jacobian(body, self.human_ids, self.all_joint_ids)
        native = snapshot.get('jacobian', self.scene.jacobian)
        native = torch.cat((torch.zeros_like(native[:, :1]), native), 1)
        reset = snapshot['reset_body_snapshot'][:, None, None, None]
        jv = torch.where(reset, geo_v, native[:, :, :3])
        jw = torch.where(reset, geo_w, native[:, :, 3:])
        gravity = 9.81*(jv[:, :, 2]*self.scene.mass[:len(self.bodies)][None, :, None]).sum(1)
        posture = self.kp*(self.target-q)-self.kd*qd
        for name in ('R_Elbow', 'R_Wrist'):
            ix, basis = self.groups[name]
            posture[:, ix] = self.kp[ix]*rotation_error(q[:, ix], self.target[:, ix], basis)-self.kd[ix]*qd[:, ix]
        task = torch.zeros_like(q)
        shoulder = self.bodies.index('R_Shoulder')
        shoulder_body = body[:, shoulder]
        point = shoulder_body[:, :3]+apply(shoulder_body[:, 3:7], self.right_local)
        velocity = origin_velocity(shoulder_body, self.scene.com[shoulder])+torch.cross(shoulder_body[:, 10:13], point-shoulder_body[:, :3], dim=-1)
        force = 2000*(self.right_goal-point)-30*velocity
        force = force*(20/torch.linalg.vector_norm(force, dim=-1, keepdim=True).clamp_min(20))
        offset = apply(shoulder_body[:, 3:7], self.right_local-self.scene.com[shoulder])
        point_j = jv[:, shoulder]+torch.cross(jw[:, shoulder].transpose(-1, -2), offset[:, None], dim=-1).transpose(-1, -2)
        task[:, self.right_support_indices] += (point_j.transpose(-1, -2)@force.unsqueeze(-1)).squeeze(-1)[:, self.right_support_indices]
        chest = self.bodies.index('Chest')
        chest_body, guitar = body[:, chest], body[:, len(self.bodies)]
        endpoints = chest_body[:, None, :3]+apply(chest_body[:, None, 3:7], self.chest_segment)
        segment = apply(conjugate(guitar[:, None, 3:7]), endpoints-guitar[:, None, :3])
        axis, surface, certified, fallback, fast_certified = source_capsule_witness(
            segment[:, 0], segment[:, 1], self.chest_triangles, self.triangle_low, self.triangle_high)
        delta = axis-surface
        distance = torch.linalg.vector_norm(delta, dim=-1, keepdim=True)
        normal_defined = distance.squeeze(-1) > 1e-9
        normal_g = delta/distance.clamp_min(1e-9)
        normal = apply(guitar[:, 3:7], normal_g)
        point_g = axis-normal_g*self.chest_radius
        point = guitar[:, :3]+apply(guitar[:, 3:7], point_g)
        local = apply(conjugate(chest_body[:, 3:7]), point-chest_body[:, :3])
        goal = guitar[:, :3]+apply(guitar[:, 3:7], surface)
        velocity = origin_velocity(chest_body, self.scene.com[chest])+torch.cross(chest_body[:, 10:13], point-chest_body[:, :3], dim=-1)
        goal_velocity = origin_velocity(guitar, self.scene.com[len(self.bodies)])+torch.cross(guitar[:, 10:13], goal-guitar[:, :3], dim=-1)
        raw = -2000*(distance-self.chest_radius+.010)+30*((goal_velocity-velocity)*normal).sum(-1, keepdim=True)
        force = normal*raw.clamp(-20, 0)
        offset = apply(chest_body[:, 3:7], local-self.scene.com[chest])
        point_j = jv[:, chest]+torch.cross(jw[:, chest].transpose(-1, -2), offset[:, None], dim=-1).transpose(-1, -2)
        task[:, self.chest_indices] += (point_j.transpose(-1, -2)@force.unsqueeze(-1)).squeeze(-1)[:, self.chest_indices]
        request = gravity+posture+task
        # Independent geometric mass, exactly the original lower child-axis law.
        lv, lw = self._geometry_jacobian(body, self.lower_bodies, self.moving_leg)
        rotation = body[:, self.lower_bodies, 3:7]
        unit = torch.eye(3, device=self.device, dtype=self.dtype)
        matrix = apply(rotation[..., None, :], unit).transpose(-1, -2)
        inertia = matrix@self.scene.inertia[self.lower_bodies]@matrix.transpose(-1, -2)
        lower_mass = (self.scene.mass[self.lower_bodies][None, :, None, None]*(lv.transpose(-1, -2)@lv) + lw.transpose(-1, -2)@inertia@lw).sum(1)
        lower_gravity = 9.81*(lv[:, :, 2]*self.scene.mass[self.lower_bodies][None, :, None]).sum(1)
        errors = []
        for ix, basis, keep in self.lower_error_groups:
            error = rotation_error(q[:, ix], self.target[:, ix], basis)
            errors.append(error[:, keep])
        lower_error = torch.cat(errors, -1)
        lower_effort, predicted, feedback = stable_pd(lower_mass, lower_error, qd[:, self.moving_leg], self.lower_kp, self.lower_kd, lower_gravity)
        request[:, self.moving_leg] = lower_effort
        request[:, self.hip_indices] += self.hip_bias
        effort = torch.maximum(torch.minimum(request, self.caps), -self.caps)
        effort[:, self.position] = 0
        effort[:, self.zero] = 0
        self.diagnostics.update(lower_mass=lower_mass, lower_gravity=lower_gravity,
            lower_error=lower_error, lower_predicted_velocity=predicted, lower_feedback=feedback,
            chest_gap=distance.squeeze(-1)-self.chest_radius, chest_force=force, chest_witness_certified=certified,
            chest_fast_certified=fast_certified, chest_exact_fallback_used=fallback,
            chest_normal_defined=normal_defined,
            gravity=gravity, support_task=task, posture=posture,
            finite=torch.isfinite(effort).all(-1), valid=torch.isfinite(effort).all(-1) & certified & normal_defined)
        return effort
