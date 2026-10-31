"""Saved env0 pose audit only. No simulator, state setters, learning, or GPU."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
import numpy as np
from scipy.spatial.transform import Rotation
from guitar_learning.runtime.prepared_reset_v1 import load_prepared_reset_contract
from guitar_learning.native.lower_body_release_v1 import controller_horizontal_v4 as source
from guitar_learning.native.initial_pose_noise_v1 import pose
from guitar_learning.native.paths import original_input_path

HERE = Path(__file__).resolve().parent
INPUT = HERE.parent / 'index_release_clearance_v1' / 'runs'
MODES = ('reference', 'noisy_reference')
BODIES = ('L_Wrist', 'LH:palm', 'LH:index1', 'LH:index2', 'LH:index3')
# Declared before reading native results; numerical agreement, not contact/success gates.
POSITION_TOL_MM = .01
ROTATION_TOL_RAD = 1e-4
SOURCE_SHA = 'c52b9628f71700275d56ddbf064760c3ce37400dd96332c895bcef964383754d'
CAS = ROOT / 'guitar_learning/assets/historical_inputs/objects' / (SOURCE_SHA + '.data')


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def read(path): return json.loads(Path(path).read_text())


def stats(values):
    a = np.asarray(values, dtype=float)
    assert a.size and np.isfinite(a).all()
    return dict(min=float(a.min()), median=float(np.median(a)), p95=float(np.percentile(a, 95)),
                max=float(a.max()), rms=float(np.sqrt(np.mean(a*a))))


def transforms(poses):
    a = np.asarray(poses, dtype=float)
    assert a.shape[-1] == 7 and np.isfinite(a).all()
    return a[..., :3], Rotation.from_quat(a[..., 3:7])


def relative(parent, child):
    pp, pr = parent; cp, cr = child
    return pr.inv().apply(cp-pp), pr.inv()*cr


def errors(a, b):
    return np.linalg.norm(a[0]-b[0], axis=-1)*1000, (a[1].inv()*b[1]).magnitude()


def points(body, local):
    p, r = body
    return np.einsum('nij,pj->npi', r.as_matrix(), local) + p[:, None, :]


def guitar_points(world, guitar):
    p, r = guitar
    return np.einsum('nji,npj->npi', r.as_matrix(), world-p[:, None, :])


def align(clock, clearance):
    take = np.flatnonzero(clearance['env_id'] == 0)
    wanted = clearance['clock'][take]
    np.testing.assert_array_equal(wanted, np.arange(692, 921, 4))
    assert len(np.unique(clock)) == len(clock)
    rows = np.searchsorted(clock, wanted)
    assert (rows < len(clock)).all()
    np.testing.assert_array_equal(clock[rows], wanted)
    assert clearance['valid_snapshot'][take].all()
    assert not clearance['reset_body_snapshot'][take].any()
    assert clearance['first_attempt'][take].all()
    return rows, take


def self_check():
    # Known rigid transformations, antipodal quaternions, and wrong clock rejection.
    r = Rotation.from_rotvec([.2, -.3, .4]); p = np.array([1., 2., 3.])
    c = (p + r.apply([.01, .02, .03]), r*Rotation.from_rotvec([.1, 0, 0]))
    t = relative((p, r), c)
    np.testing.assert_allclose(t[0], [.01, .02, .03], atol=1e-15)
    np.testing.assert_allclose(t[1].as_rotvec(), [.1, 0, 0], atol=1e-15)
    a = (p, r); b = (p, Rotation.from_quat(-r.as_quat()))
    assert errors(a, b)[0] == 0 and errors(a, b)[1] < 1e-15
    shifted = (p + [.005, 0, 0], r*Rotation.from_rotvec([.01, 0, 0]))
    np.testing.assert_allclose(errors(a, shifted), [5., .01], atol=1e-12)
    assert errors(a, shifted)[0] > POSITION_TOL_MM and errors(a, shifted)[1] > ROTATION_TOL_RAD
    n = 58; fixture = dict(env_id=np.zeros(n, int), clock=np.arange(692, 921, 4),
        valid_snapshot=np.ones(n, bool), reset_body_snapshot=np.zeros(n, bool), first_attempt=np.ones(n, bool))
    align(np.arange(4, 1417, 4), fixture)
    bad = dict(fixture, clock=fixture['clock'].copy()); bad['clock'][3] += 1
    try: align(np.arange(4, 1417, 4), bad)
    except AssertionError: pass
    else: raise AssertionError('Foreign tick accepted')
    assert 'isaacgym' not in sys.modules and 'torch' not in sys.modules
    return dict(known_transform=True, antipodal_quaternion=True, millimeter_radian_error_detected=True, foreign_tick_rejected=True,
                no_isaacgym_or_torch_import=True)


def provenance(contract):
    module_path = Path(source.__file__).resolve()
    assert sha(CAS) == SOURCE_SHA
    def fk_ast(path):
        return ast.dump(next(n for n in ast.parse(path.read_text()).body
                             if isinstance(n, ast.FunctionDef) and n.name == 'full_fk'), include_attributes=False)
    assert fk_ast(CAS) == fk_ast(module_path)
    human_sha = sha(source.HUMAN)
    mcp = ET.parse(source.HUMAN).find(".//body[@name='LH:index1']")
    assert [j.get('name') for j in mcp.findall('joint')] == ['LH:index1_x','LH:index1_z']
    np.testing.assert_array_equal([np.fromstring(j.get('axis'),sep=' ') for j in mcp.findall('joint')], [[1,0,0],[0,0,1]])
    pins = {}
    for mode in MODES:
        old = read(INPUT / mode / 'inputs_before.json')
        assert old[str(module_path)] == SOURCE_SHA
        human_keys = [k for k in old if k in (str(source.HUMAN), str(original_input_path(source.HUMAN)))]
        assert human_keys and all(old[k] == human_sha for k in human_keys)
        pins[mode] = dict(controller_pin=old[str(module_path)], human_pins={k: old[k] for k in human_keys})
    paths = set(Path(p) for p in contract['source_sha256']) | {module_path, CAS, Path(source.HUMAN), Path(__file__).resolve()}
    for mode in MODES:
        paths.update(INPUT / mode / name for name in ('trace_env0_episode0.npz', 'release_clearance4.npz',
                     'surface_static.npz', 'trace_metadata.json', 'inputs_before.json', 'diagnostic_inputs_after.json'))
    before = {str(p): sha(p) for p in sorted(paths)}
    for p, digest in contract['source_sha256'].items(): assert before[p] == digest
    return before, dict(original_controller_sha256=SOURCE_SHA, current_controller_sha256=sha(module_path),
        original_CAS_path=str(CAS), original_CAS_bytes_verified=True, full_fk_AST_identical=True,
        whole_controller_file_identical=sha(module_path) == SOURCE_SHA, human_xml_sha256=human_sha, run_pins=pins,
        MCP_XML=dict(body_attributes=mcp.attrib, exposed_joint_axes=['x','z'], unexposed_axis='y'),
        limitation='Current controller import consolidation differs from old whole-file pin. Only full_fk AST and XML byte identity are asserted; unrelated changed sources are not forced against old pins.')


def audit_mode(mode, scene, fk, contract):
    base = INPUT / mode
    with np.load(base / 'trace_env0_episode0.npz') as f: trace = {k:f[k] for k in f.files}
    with np.load(base / 'release_clearance4.npz') as f: clear = {k:f[k] for k in f.files}
    with np.load(base / 'surface_static.npz') as f: static = {k:f[k] for k in f.files}
    assert static['local_points'].shape == (128,3) and np.isfinite(static['local_points']).all()
    assert abs(static['local_points']).max() < .1  # source patch in meters, not millimeters
    assert static['source_valid'].shape == (4,128) and static['source_valid'].all()
    np.testing.assert_allclose(np.linalg.norm(static['local_normals'],axis=-1),1,rtol=0,atol=1e-6)
    meta = read(base / 'trace_metadata.json')
    assert meta['joint_names'] == scene.names
    expected = ['human/'+n for n in scene.human_bodies] + ['guitar/'+n for n in contract['initial']['guitar_body_names']] + ['chair/box']
    assert meta['body_names'] == expected and len(expected) == 106
    assert trace['q'].shape == trace['target'].shape == (354, 105)
    assert trace['body_state'].shape == (354, 106, 13)
    assert np.isfinite(trace['q']).all() and np.isfinite(trace['target']).all() and np.isfinite(trace['body_state']).all()
    norms = np.linalg.norm(trace['body_state'][..., 3:7].astype(float), axis=-1)
    assert abs(norms-1).max() < 1e-6
    clock = np.rint(trace['time_s']*240).astype(int)
    np.testing.assert_array_equal(clock, np.arange(4, 1417, 4))
    np.testing.assert_allclose(trace['time_s'], clock/240, rtol=0, atol=1e-12)
    rows, take = align(clock, clear)
    np.testing.assert_array_equal(trace['time_s'][rows], clear['time_s'][take])
    np.testing.assert_array_equal(trace['source_time_s'][rows], clear['source_time_s'][take])
    ix = {n:meta['body_names'].index('human/'+n) for n in BODIES}
    gi = meta['body_names'].index('guitar/guitar')
    np.testing.assert_array_equal(trace['body_state'][rows, ix['LH:index3'], :7], clear['distal_pose'][take])
    np.testing.assert_array_equal(trace['body_state'][rows, gi, :7], clear['guitar_pose'][take])
    native = {n:transforms(trace['body_state'][:, ix[n], :7]) for n in BODIES}
    guitar = transforms(trace['body_state'][:, gi, :7])
    predicted_rows = [fk(q.astype(float)) for q in trace['q']]
    target_rows = [fk(q.astype(float)) for q in trace['target']]
    def pack(results, name):
        return np.stack([v[name][0] for v in results]), Rotation.from_quat(np.stack([v[name][1].as_quat() for v in results]))
    predicted = {n:pack(predicted_rows,n) for n in BODIES}
    targets = {n:pack(target_rows,n) for n in BODIES}
    native_points = points(native['LH:index3'], static['local_points'])
    fk_points = points(predicted['LH:index3'], static['local_points'])
    target_points = points(targets['LH:index3'], static['local_points'])
    native_G, fk_G = guitar_points(native_points,guitar), guitar_points(fk_points,guitar)
    np.testing.assert_allclose(native_G[rows], clear['points_G'][take], rtol=0, atol=3e-7)
    point_mm = np.linalg.norm(fk_points-native_points,axis=-1)*1000
    point_G_mm = np.linalg.norm(fk_G-native_G,axis=-1)*1000
    np.testing.assert_allclose(point_mm,point_G_mm,rtol=0,atol=1e-10)
    target_mm = np.linalg.norm(target_points-fk_points,axis=-1)*1000
    world = {n:errors(native[n],predicted[n]) for n in BODIES}
    palm = {n:errors(relative(native['LH:palm'],native[n]), relative(predicted['LH:palm'],predicted[n])) for n in BODIES[2:]}
    parent = {}
    for child, par in zip(BODIES[2:], ('LH:palm','LH:index1','LH:index2')):
        parent[child] = errors(relative(native[par],native[child]), relative(predicted[par],predicted[child]))
    # Expose what two actual MCP coordinates do and do not describe; do not fit a new FK.
    mcp_log = relative(native['LH:palm'],native['LH:index1'])[1].as_rotvec()
    mcp_ix = [scene.names.index('LH:index1_'+axis) for axis in ('x','z')]
    mcp_xz_error = mcp_log[:,[0,2]]-trace['q'][:,mcp_ix]
    windows = {}
    for label, ids in (('full_354',np.arange(354)), ('release_58',rows)):
        summarize = lambda values:{n:dict(position_mm=stats(e[0][ids]), rotation_rad=stats(e[1][ids])) for n,e in values.items()}
        windows[label] = dict(rows=len(ids), clock_range=[int(clock[ids[0]]),int(clock[ids[-1]])],
            world=summarize(world), palm_relative=summarize(palm), parent_relative=summarize(parent),
            source128_point_error_world_mm=stats(point_mm[ids]), source128_point_error_guitar_mm=stats(point_G_mm[ids]),
            actual_to_target_FK_source128_change_mm=stats(target_mm[ids]),
            actual_to_target_q_abs_rad=stats(abs(trace['target'][ids]-trace['q'][ids])),
            native_MCP_log_xz_minus_actual_q_abs_rad=stats(abs(mcp_xz_error[ids])),
            native_MCP_unexposed_log_y_rad=stats(mcp_log[ids,1]),
            fk_accuracy_gate=bool(all(e[0][ids].max()<=POSITION_TOL_MM and e[1][ids].max()<=ROTATION_TOL_RAD for e in palm.values())))
    # Compare to measured geometric margins; no recomputation or relaxation of contact predicates.
    distance = clear['aggregate_distance'][take]*1000
    nearest = clear['aggregate_sample_index'][take]
    nearest_err = point_mm[rows,np.asarray(nearest)]
    summary = dict(metadata_order_verified=True, actual_q_used=True, prepared_fk_recalibrations=0,
        exact_clock_and_distal_guitar_pose_alignment=True, quaternion_norm_abs_error_max=float(abs(norms-1).max()),
        saved_points_reconstruction_max_abs_mm=float(abs(native_G[rows]-clear['points_G'][take]).max()*1000),
        windows=windows, measured_release=dict(native_nearest_distance_mm=stats(distance),
            native_nearest_point_FK_error_mm=stats(nearest_err),
            fk_error_exceeds_native_distance_rows=int((nearest_err>distance).sum()),
            cached_positive_rows=int(clear['cached_positive'][take].sum()), candidate_rows=int(clear['candidate'][take].sum()),
            scope='Actual env0 saved geometric nearest distance only; not a signed release guarantee or whole-skin/cooked-contact certification.'),
        endpoint_scope='All354 include original first-attempt terminal endpoint; no additional native integration.')
    series = dict(clock=clock.tolist(), point_error_max_mm=point_mm.max(axis=1).tolist(),
                  native_release_distance_mm=distance.tolist(), release_clock=clock[rows].tolist())
    for n in BODIES:
        series[n+'_world_position_mm']=world[n][0].tolist(); series[n+'_world_rotation_rad']=world[n][1].tolist()
    for n in BODIES[2:]:
        series[n+'_palm_position_mm']=palm[n][0].tolist(); series[n+'_palm_rotation_rad']=palm[n][1].tolist()
    series['native_MCP_log_y_rad']=mcp_log[:,1].tolist()
    series['native_MCP_log_xz_minus_q_max_abs_rad']=abs(mcp_xz_error).max(axis=1).tolist()
    return summary, series


def main():
    checks = self_check()
    contract = load_prepared_reset_contract()
    q = np.array([v['pos'] for v in contract['state']['human_dof_states']])
    scene = SimpleNamespace(names=contract['initial']['joint_names'], human_bodies=contract['initial']['human_body_names'], q_ref=q)
    before, prov = provenance(contract)
    fk = source.full_fk(scene, contract['state'])  # exactly one calibration using actual prepared q
    baseline = fk(q)
    initial = {n:pose(s) for n,s in zip(scene.human_bodies, contract['state']['human_body_states'])}
    baseline_errors = [errors(initial[n],baseline[n]) for n in scene.human_bodies]
    assert max(v[0] for v in baseline_errors) < 1e-8 and max(v[1] for v in baseline_errors) < 1e-12
    # Deliberately wrong q_ref demonstrates why baseline self-consistency alone is insufficient.
    target_baseline = fk(contract['target105'])
    wrong = errors(initial['LH:index3'],target_baseline['LH:index3'])
    results = dict(schema='index_release_fk_native_audit.v1', program_completed=True, gpu_runs=0, ppo_updates=0,
        tolerances=dict(position_mm=POSITION_TOL_MM, rotation_rad=ROTATION_TOL_RAD,
            scope='Numerical FK/native agreement only, declared in source before native results. Existing physical/music/contact gates unchanged.'),
        provenance=prov, prepared=dict(actual105_calibration_count=1,
            self_consistency_position_max_mm=max(v[0] for v in baseline_errors),
            self_consistency_rotation_max_rad=max(v[1] for v in baseline_errors),
            actual_target_abs_q_max_rad=float(abs(q-contract['target105']).max()),
            actual_target_index3_position_mm=float(wrong[0]), actual_target_index3_rotation_rad=float(wrong[1]),
            native_MCP_log_xyz_rad=relative(initial['LH:palm'],initial['LH:index1'])[1].as_rotvec().tolist(),
            scope='Calibration self-consistency is an arithmetic check, not independent native motion evidence.'), modes={})
    series = {}
    for mode in MODES: results['modes'][mode],series[mode] = audit_mode(mode,scene,fk,contract)
    after = {p:sha(p) for p in before}; assert before == after
    results['input_sha256_before']=before; results['input_sha256_after']=after
    results['inputs_unchanged']=True; results['self_checks']=checks
    results['fk_accuracy_gate']=all(m['windows']['release_58']['fk_accuracy_gate'] for m in results['modes'].values())
    (HERE/'results.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    (HERE/'series.json').write_text(json.dumps(series,ensure_ascii=False,indent=2)+'\n')
    plot(series)
    print(json.dumps(dict(program_completed=True, fk_accuracy_gate=results['fk_accuracy_gate'], inputs_unchanged=True,
        output=str(HERE/'results.json')),ensure_ascii=False))


def plot(series):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(4,2,figsize=(12,12),sharex='col',constrained_layout=True)
    for col,mode in enumerate(MODES):
        s=series[mode]; t=np.array(s['clock'])/240
        for n in BODIES:
            axes[0,col].plot(t,s[n+'_world_position_mm'],label=n)
        for n in BODIES[2:]: axes[1,col].plot(t,s[n+'_palm_rotation_rad'],label=n)
        axes[2,col].plot(t,s['point_error_max_mm'],label='128-point maximum FK error')
        axes[2,col].plot(np.array(s['release_clock'])/240,s['native_release_distance_mm'],label='Native nearest distance')
        axes[3,col].plot(t,np.rad2deg(s['native_MCP_log_y_rad']),label='Native MCP log y (unexposed)')
        axes[3,col].plot(t,np.rad2deg(s['native_MCP_log_xz_minus_q_max_abs_rad']),label='Max |native log xz - actual qxz|')
        axes[0,col].set_title(mode)
        for ax in axes[:,col]:
            ax.axvspan(692/240,920/240,color='grey',alpha=.12);ax.grid(alpha=.25);ax.legend(fontsize=7)
        axes[3,col].set_xlabel('Local time (s); grey = saved release window')
    axes[0,0].set_ylabel('World body origin error (mm)')
    axes[1,0].set_ylabel('Palm-relative rotation error (rad)')
    axes[2,0].set_ylabel('Source patch distance/error (mm)')
    axes[3,0].set_ylabel('MCP native coordinate diagnostic (deg)')
    fig.savefig(HERE/'fk_native_comparison.png',dpi=160);plt.close(fig)


if __name__ == '__main__': main()
