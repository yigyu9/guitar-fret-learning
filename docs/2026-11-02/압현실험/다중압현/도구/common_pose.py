"""CPU-only common-arm search and actual-arrival finger re-fit. No simulation."""
import os
for _key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[_key] = '1'
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import argparse
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace

from inputs import ROOT, STUDY, SINGLE, FINGERS, imported_pins, merge_pins, sha, verify, write
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation
from guitar_learning.runtime.prepared_reset_v1 import load_gpu_prepared_reset_contract
from guitar_learning.native.lower_body_release_v1.controller_horizontal_v4 import full_fk
from guitar_learning.gpu.contact import load_fingertip_pad
from guitar_learning.tool.validation.press_acquisition import action_bounds, source_geometry


def validate_case(case):
    rows = case['targets']
    if len(rows) != 2 or len({r['finger_id'] for r in rows}) != 2 or len({r['string'] for r in rows}) != 2:
        raise ValueError('Two distinct fingers and strings required; no barre')
    for row in rows:
        if (row['finger'] not in FINGERS or FINGERS.index(row['finger'])+1 != row['finger_id'] or
                not 0 <= row['string'] < 6 or row['string_standard_1based'] != row['string']+1 or
                not 1 <= row['fret'] <= 14):
            raise ValueError('Invalid target identity')


def validate_arrival(arrival, case, contract):
    """Verify ordered snapshot identity before calibrating FK to body poses."""
    initial = contract['initial']
    if (arrival.get('schema') != 'multi_press.arrival.v1' or
            arrival.get('case_id') != case['case_id'] or
            arrival.get('target_ids') != [r['target_id'] for r in case['targets']] or
            arrival.get('joint_names') != initial['joint_names'] or
            arrival.get('human_body_names') != initial['human_body_names'] or
            type(arrival.get('physics_step')) is not int or arrival['physics_step'] < 0 or
            not isinstance(arrival.get('scene_id'), str) or not arrival['scene_id'] or
            arrival.get('evidence_kind') not in ('synthetic', 'native_declared')):
        raise ValueError('Arrival case/names/scene/step identity mismatch')
    verify(arrival['source_sha256'])
    q = np.asarray(arrival['q105'], dtype=float)
    state = arrival['state']
    if q.shape != (105,) or not np.isfinite(q).all():
        raise ValueError('Finite arrival q105 required')
    ordered_q = state['human_dof_states']
    if len(ordered_q) != 105 or not np.array_equal(q, [r['pos'] for r in ordered_q]):
        raise ValueError('Arrival q/state identity mismatch')
    for kind in ('human', 'guitar', 'chair'):
        rows = state[kind+'_body_states']
        if len(rows) != len(contract['state'][kind+'_body_states']):
            raise ValueError('Every ordered actual body required')
        body_names = initial['human_body_names'] if kind == 'human' else initial['guitar_body_names'] if kind == 'guitar' else ['box']
        if arrival['body_names'][kind] != body_names:
            raise ValueError('Ordered body identity mismatch')
        for row in rows:
            position = [row['pose']['p'][a] for a in 'xyz']
            quat = np.array([row['pose']['r'][a] for a in 'xyzw'])
            velocity = [row['vel'][field][a] for field in ('linear', 'angular') for a in 'xyz']
            if not np.isfinite(np.r_[position, quat, velocity]).all() or abs(np.linalg.norm(quat)-1) > 1e-5:
                raise ValueError('Finite poses/velocities and unit quaternion required')
    # Rows carry their own labels, preventing accidental reordered arrays with stale top-level names.
    if [r.get('body_name') for r in state['human_body_states']] != arrival['human_body_names']:
        raise ValueError('Each actual human row requires its ordered body_name')


class CommonPose:
    def __init__(self, case, arrival=None):
        validate_case(case)
        self.rows = case['targets']
        contract = load_gpu_prepared_reset_contract('left')
        self.names = contract['initial']['joint_names']
        bodies = contract['initial']['human_body_names']
        if arrival is not None:
            validate_arrival(arrival, case, contract)
        state = contract['state'] if arrival is None else arrival['state']
        self.q0 = np.array([r['pos'] for r in state['human_dof_states']], dtype=float)
        if self.q0.shape != (105,) or not np.isfinite(self.q0).all():
            raise ValueError('Finite actual q105 required')
        if arrival is not None and not np.allclose(arrival['q105'], self.q0, rtol=0, atol=1e-10):
            raise ValueError('Arrival q/state identity mismatch')
        if len(state['human_body_states']) != len(bodies):
            raise ValueError('Actual arrival requires every human body')
        self.fk = full_fk(SimpleNamespace(names=self.names, human_bodies=bodies, q_ref=self.q0), state)
        initial_poses = self.fk(self.q0)
        self.reproduction = max(np.linalg.norm(initial_poses[name][0]-np.array([row['pose']['p'][a] for a in 'xyz']))
                                for name, row in zip(bodies, state['human_body_states']))
        gp = state['guitar_body_states'][0]['pose']
        self.gp = np.array([gp['p'][a] for a in 'xyz'])
        self.gr = Rotation.from_quat([gp['r'][a] for a in 'xyzw'])
        active, lo, hi = action_bounds(contract)
        self.arm = [int(i) for i in active if self.names[i].startswith('L_')]
        self.finger = [int(i) for r in self.rows for i in active if self.names[i].startswith('LH:'+r['finger'])]
        if len(self.arm) != 12 or len(self.finger) != 8:
            raise ValueError('Common arm12 and assigned finger8 required')
        self.active = active
        self.lower = dict(zip(active, lo)); self.upper = dict(zip(active, hi))
        self.pad = load_fingertip_pad()
        self.starts, ends, low, high, plane, surface = source_geometry(contract, self.rows)
        self.lines = ends-self.starts
        length = np.linalg.norm(plane[:3]); self.normal = plane[:3]/length; self.d = plane[3]/length
        self.low, self.high = low+.002, high-.002
        self.centers = [self.starts[r['string']]+((low[k]+high[k])/2-self.starts[r['string'], 1])/
                        self.lines[r['string'], 1]*self.lines[r['string']] for k, r in enumerate(self.rows)]
        self.pins = dict(contract['source_sha256'])
        merge_pins(self.pins, self.pad['contract']['source_sha256'])
        merge_pins(self.pins, surface['source_sha256'])
        if arrival is not None:
            merge_pins(self.pins, arrival['source_sha256'])

    def samples(self, q, poses=None):
        poses = self.fk(q) if poses is None else poses
        result = []
        for row in self.rows:
            finger = row['finger_id']-1; valid = self.pad['valid'][finger]
            p, rot = poses['LH:'+row['finger']+'3']
            points = self.gr.inv().apply(p+rot.apply(self.pad['points_local'][finger][valid])-self.gp)
            facing = -self.gr.inv().apply(rot.apply(self.pad['normals_local'][finger][valid]))@self.normal
            result.append((points, facing))
        return result

    def measure(self, q, height):
        rows = []
        for k, ((points, facing), row) in enumerate(zip(self.samples(q), self.rows)):
            signed = points@self.normal+self.d
            projected = points-signed[:, None]*self.normal
            delta = projected[:, None]-self.starts[None]
            fraction = (delta*self.lines[None]).sum(-1)/(self.lines*self.lines).sum(-1)
            distances = np.linalg.norm(delta-fraction[..., None]*self.lines[None], axis=-1)
            string = row['string']; lateral = distances[:, string]
            nearest = distances.argmin(-1)
            unique = (distances <= distances.min(-1, keepdims=True)+1e-12).sum(-1) == 1
            cell = (points[:, 1] >= self.low[k]) & (points[:, 1] <= self.high[k])
            inside = (fraction[:, string] >= 0) & (fraction[:, string] <= 1)
            if height > 0:
                band = (signed >= .005) & (signed <= .015); tolerance = .005
            else:
                band = (signed >= -.001) & (signed <= .003); tolerance = .003
            passing = cell & inside & band & (lateral <= tolerance) & (facing >= .1) & unique & (nearest == string)
            j = int(np.linalg.norm(points-(self.centers[k]+height*self.normal), axis=-1).argmin())
            rows.append(dict(target_id=row['target_id'], geometry_candidate=bool(passing.any()),
                passing_samples=np.flatnonzero(passing).tolist(), selected_sample=j,
                signed_height_m=float(signed[j]), lateral_m=float(lateral[j]), facing=float(facing[j]),
                target_error_m=float(np.linalg.norm(points[j]-self.centers[k]-height*self.normal))))
        return rows

    def fit(self, base, indices, height, max_nfev):
        # Both target residuals are evaluated at exactly the same q105.
        lower = np.array([self.lower[i] for i in indices]); upper = np.array([self.upper[i] for i in indices])
        seed = np.clip(base[indices], lower+1e-10, upper-1e-10)
        def residual(values):
            q = base.copy(); q[indices] = values
            terms = []
            for k, (points, facing) in enumerate(self.samples(q)):
                desired = self.centers[k]+height*self.normal
                j = int(np.linalg.norm(points-desired, axis=-1).argmin())
                terms.extend(1000*(points[j]-desired))
                terms.append(10*max(.2-facing[j], 0.))
            return np.r_[terms, .02*(values-seed)]
        fit = least_squares(residual, seed, bounds=(lower, upper), max_nfev=max_nfev)
        q = base.copy(); q[indices] = fit.x
        active_q = q[self.active]
        lo = np.array([self.lower[i] for i in self.active]); hi = np.array([self.upper[i] for i in self.active])
        if not np.isfinite(q).all() or ((active_q < lo-1e-7) | (active_q > hi+1e-7)).any():
            raise ValueError('Candidate violates current action bounds')
        metrics = self.measure(q, height)
        return q, dict(q105=q.tolist(), targets=metrics, both_geometry=all(r['geometry_candidate'] for r in metrics),
                       optimizer_converged=bool(fit.success), nfev=int(fit.nfev), native_verified=False)

    def finger_motion(self, start, end):
        rows = []
        for row, (a, _), (b, _) in zip(self.rows, self.samples(start), self.samples(end)):
            rows.append(dict(target_id=row['target_id'],
                             maximum_same_sample_displacement_m=float(np.linalg.norm(b-a, axis=-1).max())))
        return dict(assigned_joint_max_change_rad=float(np.abs(end[self.finger]-start[self.finger]).max()),
                    arm_max_change_rad=float(np.abs(end[self.arm]-start[self.arm]).max()),
                    targets=rows, scope='Fixed common-arm source FK; not measured native force contribution')


def run(args):
    started = time.monotonic()
    cases_path = STUDY/'설계/cases.json'
    cases = json.loads(cases_path.read_text())['cases']
    if args.case:
        cases = [c for c in cases if c['case_id'] == args.case]
        if len(cases) != 1:
            raise ValueError('Unknown case')
    if args.arrival and len(cases) != 1:
        raise ValueError('Actual arrival requires exactly one case')
    out = Path(args.out).resolve(); out.relative_to(STUDY)
    out.mkdir(parents=True, exist_ok=False)
    protected = json.loads((STUDY/'입력/protected_sha256.json').read_text()); verify(protected)
    pins = imported_pins()
    merge_pins(pins, {str(cases_path): sha(cases_path)})
    frozen_path = SINGLE/'로그/sweep_v1/geometry_frozen.json'
    frozen = json.loads(frozen_path.read_text())
    pins[str(frozen_path)] = sha(frozen_path)
    arrival = None
    if args.arrival:
        path = Path(args.arrival).resolve()
        arrival = json.loads(path.read_text()); pins[str(path)] = sha(path)
    results = []
    for case in cases:
        planner = CommonPose(case, arrival)
        merge_pins(pins, planner.pins); merge_pins(pins, imported_pins()); verify(pins)
        write(out/'inputs_before.json', pins) if not results else None
        if arrival:
            # Re-calibrated actual arrival FK; arm and every nonassigned joint fixed.
            q, press = planner.fit(planner.q0, planner.finger, -.0005, args.max_nfev)
            attempts = [dict(seed='actual_arrival', press=press,
                             finger_motion=planner.finger_motion(planner.q0, q))]
            found = press['both_geometry']
        else:
            first = next(r for r in frozen['rows'] if r['case_id'] == case['targets'][0]['target_id'])
            seed = planner.q0.copy()
            seed[planner.arm] = np.asarray(first['transport_waypoints'][-1]['q105'])[planner.arm]
            attempts = []
            for label, initial in [('common_v9', planner.q0), ('single_arm_seed_jointly_refit', seed)]:
                hover_q, hover = planner.fit(initial, planner.arm+planner.finger, .010, args.max_nfev)
                press_q, press = planner.fit(hover_q, planner.finger, -.0005, args.max_nfev)
                # The common arm is identical throughout hover -> press.
                assert np.array_equal(hover_q[planner.arm], press_q[planner.arm])
                attempts.append(dict(seed=label, preparation=hover, press=press,
                    finger_motion=planner.finger_motion(hover_q, press_q),
                    arm_change_hover_to_press_rad=float(np.max(np.abs(hover_q[planner.arm]-press_q[planner.arm])))))
            found = any(a['preparation']['both_geometry'] and a['press']['both_geometry'] for a in attempts)
        row = dict(case_id=case['case_id'], geometry_pair_found=found, attempts=attempts,
                   fk_reproduction_position_error_m=float(planner.reproduction),
                   assigned_indices=planner.finger, common_arm_indices=planner.arm,
                   native_verified=False, outcome='geometry_only' if found else 'finite_search_unresolved')
        results.append(row); write(out/(case['case_id']+'.json'), row)
        print(case['case_id'], row['outcome'], flush=True)
    merge_pins(pins, imported_pins()); verify(pins); verify(protected)
    write(out/'inputs_after.json', pins)
    report = dict(schema='multi_press.cpu_common_pose.v1', completed=True, physical_tests=0,
        recalibrated_actual_arrival=bool(arrival), rows=results, elapsed_s=time.monotonic()-started,
        source_sha256=pins, protected_inputs_unchanged=True, max_nfev=args.max_nfev,
        limitation='Finite source FK only. No collision, dynamics, load, wrong-contact or sound certification. '
                   'No route or native runner is supplied by this CPU search. Unresolved is not impossible.')
    write(out/'report.json', report)
    print(json.dumps(dict(completed=True, geometry_pairs=sum(r['geometry_pair_found'] for r in results),
                          cases=len(results), elapsed_s=report['elapsed_s'])))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    parser.add_argument('--case')
    parser.add_argument('--arrival', help='Read-only actual-state JSON with state and q105; never injected')
    parser.add_argument('--max-nfev', type=int, default=40)
    args = parser.parse_args()
    if not 1 <= args.max_nfev <= 100:
        parser.error('max-nfev must be 1..100')
    run(args)
