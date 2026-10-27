"""Measured hand hierarchy plus verified arm12/scalar-hinge deltas; offline only."""
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

from .build_fixed_lower_asset import pose
from .search_multi_face_grip import left_fk

ROOT = Path(__file__).resolve().parents[1]
HINGES = ('LH:thumb2', 'LH:thumb3', 'LH:index2', 'LH:index3',
          'LH:middle2', 'LH:middle3')
ARM_BODIES = ('L_Thorax', 'L_Shoulder', 'L_Elbow', 'L_Wrist', 'LH:palm')
CONTACT_BODIES = ('LH:palm', 'LH:thumb3', 'LH:index3', 'LH:middle3')


def anchor_catalog(proposal):
    anchors = {}
    for name in CONTACT_BODIES:
        row = proposal['rows'][0]['source_anchors'].get(name)
        anchors[name] = ((np.array(row['source_point_local_m']), np.array(row['source_normal_local']))
                         if row else (np.array(proposal['facets'][name]['point_local_m']),
                                      np.array(proposal['facets'][name]['normal_local'])))
    return anchors


def features(snapshot, delta, anchors):
    poses = snapshot.poses(delta)
    points, normals = [], []
    for name in CONTACT_BODIES:
        p, r = poses[name]; point, normal = anchors[name]
        points.append(p+r.apply(point)); normals.append(r.apply(normal))
    return np.r_[np.array(points).reshape(-1), np.array(normals).reshape(-1)]


class CoupledSnapshot:
    def __init__(self, names, bodies, state0, state):
        self.names, self.bodies = names, bodies
        self.q = np.array([d['pos'] for d in state['human_dof_states']])
        q0 = np.array([d['pos'] for d in state0['human_dof_states']])
        self.arm = [n for n in names if n.startswith(
            ('L_Thorax_', 'L_Shoulder_', 'L_Elbow_', 'L_Wrist_'))]
        self.selected = self.arm + list(HINGES)
        assert len(self.arm) == 12 and len(set(self.selected)) == 18
        self.indices = [names.index(n) for n in self.selected]
        self.fk, _ = left_fk(names, bodies, state0, q0)
        self.actual = {n: (pose(state['human_body_states'][i])[0],
                           Rotation.from_quat(pose(state['human_body_states'][i])[1]))
                       for i, n in enumerate(bodies)}
        p0, r0 = pose(state0['human_body_states'][bodies.index('Chest')])
        self.chest0 = p0
        self.lift = self.actual['Chest'][1] * Rotation.from_quat(r0).inv()
        self.old_arm = self.arm_at(self.q)
        xml = ET.parse(ROOT / 'tab2body/assets/smpl_mpl_hands_body.xml').getroot()
        parents = {c: p for p in xml.iter('body') for c in p.findall('body')}
        tree = next(b for b in xml.iter('body') if b.get('name') == 'LH:palm')
        self.relative = []
        for body in tree.iter('body'):
            name = body.get('name')
            if name == 'LH:palm':
                continue
            parent = parents[body].get('name')
            pp, pr = self.actual[parent]; cp, cr = self.actual[name]
            axis = None
            if name in HINGES:
                joint, = body.findall('joint')
                assert joint.get('name') == name
                assert np.linalg.norm(np.fromstring(joint.get('pos', '0 0 0'), sep=' ')) == 0
                axis = np.fromstring(joint.get('axis'), sep=' ')
                assert abs(np.linalg.norm(axis) - 1) < 1e-12
            self.relative.append((name, parent, pr.inv().apply(cp-pp), pr.inv()*cr, axis))

    def arm_at(self, q):
        pc = self.actual['Chest'][0]
        return {n: (pc+self.lift.apply(p-self.chest0), self.lift*r)
                for n, (p, r) in self.fk(q).items() if n in ARM_BODIES}

    def poses(self, delta):
        delta = np.asarray(delta, dtype=float)
        assert delta.shape == (18,) and np.isfinite(delta).all()
        q = self.q.copy(); q[self.indices] += delta
        predicted = self.arm_at(q)
        output = {}
        for name in ARM_BODIES:
            pa, ra = self.actual[name]; po, ro = self.old_arm[name]; pn, rn = predicted[name]
            output[name] = (pa+pn-po, (rn*ro.inv())*ra)
        for name, parent, relative_p, relative_r, axis in self.relative:
            pp, pr = output[parent]
            dr = (Rotation.from_rotvec(axis*delta[self.selected.index(name)])
                  if axis is not None else Rotation.identity())
            output[name] = (pp+pr.apply(relative_p), pr*dr*relative_r)
        return output

    def meshes(self, source_meshes, moving, delta):
        poses = self.poses(delta); output = dict(source_meshes)
        for shape in moving:
            key, name = shape['geom_id'], shape['body']
            mesh = source_meshes[key].copy()
            if np.any(delta):
                oldp, oldr = self.actual[name]; newp, newr = poses[name]
                mesh.vertices = newp+newr.apply(oldr.inv().apply(mesh.vertices-oldp))
            output[key] = mesh
        return output
