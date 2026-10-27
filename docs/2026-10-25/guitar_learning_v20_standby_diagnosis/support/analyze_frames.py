"""Read-only saved-pose analysis. Never run physics or alter learning inputs."""
import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
import numpy as np
import torch
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from guitar_learning.gpu.finger_reward import (
    B_PREPARATION_ANGLES_DEGREES, finger_posture_reward,
    finger_preparation_gate)
from guitar_learning.gpu.fingertip_pad import load_fingertip_pad, pad_target_geometry
from guitar_learning.gpu.geometry import apply, conjugate
from guitar_learning.gpu.press_surface import load_press_surface, project_press_strings
from guitar_learning.core.control import ACTIVE_NAMES

PHASE = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'docs/2026-10-25/guitar_learning_v20_A500'
FINGERS = ['index', 'middle', 'ring', 'pinky']
REFERENCE = np.asarray(B_PREPARATION_ANGLES_DEGREES)
torch.set_num_threads(1)


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def intervals(mask, times):
    """Half-open endpoint-index ranges, with no assumed sub-frame behavior."""
    starts = np.flatnonzero(mask & ~np.r_[False, mask[:-1]])
    stops = np.flatnonzero(mask & ~np.r_[mask[1:], False])
    return [dict(start_s=float(times[a]), last_endpoint_s=float(times[b]),
                 endpoint_count=int(b-a+1), completed_endpoint_count=int(b-max(a, 1)+1),
                 sampled_s=float((b-max(a, 1)+1)/60),
                 index_start=int(a), index_end=int(b)) for a, b in zip(starts, stops)]


def windows(targets, duration, preparation):
    result = []
    for f in range(1, 5):
        busy = sorted((max(0., t['press_s']-preparation), min(duration, t['end_s']))
                      for t in targets if t['finger'] == f)
        merged = []
        for lo, hi in busy:
            if merged and lo <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], hi)
            else:
                merged.append([lo, hi])
        cursor = 0.
        for lo, hi in merged+[[duration, duration]]:
            if lo > cursor:
                result.append(dict(finger=f, start_s=cursor, end_s=lo,
                                   duration_s=lo-cursor))
            cursor = max(cursor, hi)
    return result


def mul_np(a, b):
    return np.concatenate((a[..., 3:]*b[..., :3]+b[..., 3:]*a[..., :3]+
                           np.cross(a[..., :3], b[..., :3]),
                           a[..., 3:]*b[..., 3:]-(a[..., :3]*b[..., :3]).sum(-1, keepdims=True)), -1)


def rot_np(q, v):
    q = q/np.maximum(np.linalg.norm(q, axis=-1, keepdims=True), 1e-12)
    u = np.cross(q[..., :3], v)
    return v+2*(q[..., 3:]*u+np.cross(q[..., :3], u))


def conjugate_np(q):
    return q*np.asarray([-1., -1., -1., 1.])


def geometry(pose, meta):
    body = pose['body_state'].astype(np.float64)
    idx = {name: i for i, name in enumerate(meta['body_names'])}
    palm = body[:, idx['human/LH:palm'], 3:7]
    segidx = np.array([[idx['human/LH:'+f+str(j)] for j in (1, 2, 3)] for f in FINGERS])
    segment = body[:, segidx, 3:7]
    parent = np.concatenate((np.broadcast_to(palm[:, None, None], (len(palm), 4, 1, 4)), segment[:, :, :2]), 2)
    direction = rot_np(mul_np(conjugate_np(parent), segment), np.array([0., -1., 0.]))
    valid = np.isfinite(parent).all(-1) & np.isfinite(segment).all(-1)
    valid &= (np.linalg.norm(parent, axis=-1) > 1e-12) & (np.linalg.norm(segment, axis=-1) > 1e-12)
    valid &= np.linalg.norm(direction[..., 1:], axis=-1) >= 1e-6
    angles = np.where(valid, np.arctan2(-direction[..., 2], -direction[..., 1]), 0.)*180/np.pi
    outside = np.maximum(np.abs(angles-REFERENCE)-15., 0.)
    inside = valid.all(-1) & (outside == 0).all(-1)
    quality = np.where(valid.all(-1), 1/(1+np.square(outside/30).sum(-1)), 0.)
    # Native q1_x/z are recorded separately and never called geometric MCP.
    jidx = {name: i for i, name in enumerate(meta['joint_names'])}
    joints = np.array([[jidx['LH:'+f+s] for s in ('1_x', '1_z', '2', '3')] for f in FINGERS])
    native = pose['q'][:, joints]*180/np.pi
    target = pose['target'][:, joints]*180/np.pi
    topidx = [idx['human/LH:'+f+'_top'] for f in FINGERS]
    tops_local = rot_np(conjugate_np(palm[:, None]), body[:, topidx, :3]-body[:, idx['human/LH:palm'], None, :3])
    bases_local = rot_np(conjugate_np(palm[:, None]), body[:, segidx[:, 0], :3]-body[:, idx['human/LH:palm'], None, :3])
    base_sign = np.sign(bases_local[0, 1:, 0]-bases_local[0, :-1, 0])
    reversed_order = (tops_local[:, 1:, 0]-tops_local[:, :-1, 0])*base_sign < 0
    # Distal skeletal centerline samples: finger2 -> finger3 -> top, 17 per segment.
    chain = np.concatenate((body[:, segidx[:, 1:], :3], body[:, topidx, None, :3]), 2)
    frac = np.linspace(0, 1, 17)
    samples = (chain[:, :, :-1, None]*(1-frac[None, None, None, :, None])+
               chain[:, :, 1:, None]*frac[None, None, None, :, None]).reshape(len(body), 4, -1, 3)
    separation = np.stack([np.linalg.norm(samples[:, f, :, None]-samples[:, f+1, None], axis=-1).min((1, 2))
                           for f in range(3)], -1)
    return dict(angles=angles, valid=valid, inside=inside, quality=quality,
                native=native, target=target, top_local=tops_local,
                reversed_order=reversed_order, centerline_separation=separation)


def temporal(times, targets):
    press, end = np.array([t['press_s'] for t in targets]), np.array([t['end_s'] for t in targets])
    finger = np.array([t['finger'] for t in targets])
    assigned = finger[None] == np.arange(1, 5)[:, None]
    relevant = (times[:, None] >= press-2) & (times[:, None] <= end)
    busy = np.minimum(np.clip((times[:, None]-(press-.5))/.15, 0, 1),
                      np.clip((end+.15-times[:, None])/.15, 0, 1))
    busy = np.where((times[:, None] >= press-.35) & (times[:, None] <= end), 1., busy)
    idle = 1-(busy[:, None]*assigned[None]).max(-1)
    own_relevant = relevant[:, None] & assigned[None]
    pressing = (((times[:, None] >= press) & (times[:, None] <= end))[:, None] & assigned[None]).any(-1)
    return dict(idle=idle, own_relevant=own_relevant, pressing=pressing,
                far_idle=~own_relevant.any(-1))


def pad_distances(pose, meta, targets, pad, press_surface):
    idx = {name: i for i, name in enumerate(meta['body_names'])}
    strings = torch.tensor([t['string'] for t in targets])
    frets = torch.tensor([t['fret'] for t in targets])
    fingers = torch.tensor([t['finger'] for t in targets])
    plane = torch.tensor(press_surface['plane_G'], dtype=torch.float64)
    starts_idx = [idx['guitar/G:string%d'%i] for i in range(1, 7)]
    ends_idx = [idx['guitar/G:string%d_end'%i] for i in range(1, 7)]
    frets_idx = [idx['guitar/G:nut']]+[idx['guitar/G:fret%d'%i] for i in range(1, 23)]
    pad_idx = [idx['human/LH:'+f+'3'] for f in FINGERS]
    result = []
    validation = []
    for lo in range(0, len(pose['clock']), 64):
        b = torch.tensor(pose['body_state'][lo:lo+64], dtype=torch.float64)
        g = b[:, idx['guitar/guitar']]
        local = apply(conjugate(g[:, None, 3:7]), b[..., :3]-g[:, None, :3])
        starts, ends = project_press_strings(local[:, starts_idx], local[:, ends_idx], plane)
        fret_y = local[:, frets_idx, 1]
        lower = torch.minimum(fret_y[:, frets-1], fret_y[:, frets])
        upper = torch.maximum(fret_y[:, frets-1], fret_y[:, frets])
        p = b[:, pad_idx]
        world = p[:, :, None, :3]+apply(p[:, :, None, 3:7], torch.tensor(pad['points_local'], dtype=torch.float64)[None])
        points = apply(conjugate(g[:, None, None, 3:7]), world-g[:, None, None, :3])
        normals = apply(conjugate(g[:, None, None, 3:7]), apply(p[:, :, None, 3:7], torch.tensor(pad['normals_local'], dtype=torch.float64)[None]))
        out = pad_target_geometry(points, normals, torch.zeros_like(points), torch.tensor(pad['valid']),
            starts, ends, lower, upper, strings, fingers, torch.zeros(len(b), 4, dtype=torch.bool), plane)
        result.append(out['distance'].numpy())
        if lo == 0:
            # Independently compute all67 finite-segment distances at the reset frame.
            pn, sn, en = points[0].numpy(), starts[0].numpy(), ends[0].numpy()
            npdist = []
            for ti, target in enumerate(targets):
                start, line = sn[target['string']], en[target['string']]-sn[target['string']]
                bounds = sorted(((float(lower[0, ti])+.002-start[1])/line[1],
                                 (float(upper[0, ti])-.002-start[1])/line[1]))
                v = pn[target['finger']-1]
                a = np.clip(((v-start)*line).sum(-1)/(line*line).sum(), max(0, bounds[0]), min(1, bounds[1]))
                npdist.append(np.linalg.norm(start+a[:, None]*line-v, axis=-1).min())
            validation.append(float(np.max(np.abs(np.asarray(npdist)-result[-1][0]))))
    return np.concatenate(result), max(validation)


def summary_array(a):
    return dict(min=np.min(a, axis=0).tolist(), mean=np.mean(a, axis=0).tolist(),
                max=np.max(a, axis=0).tolist())


def write_csv(path, rows):
    if not rows:
        return
    with path.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def plot_selected(times, g, state, targets, far_windows):
    fig, axes = plt.subplots(4, 1, figsize=(16, 11), sharex=True)
    colors = ['#cf4141', '#2c8b5f', '#3264b8']
    for f, ax in enumerate(axes):
        for j, (name, color) in enumerate(zip(('MCP', 'PIP', 'DIP'), colors)):
            ax.fill_between(times, REFERENCE[f,j]-15, REFERENCE[f,j]+15, color=color, alpha=.07)
            ax.plot(times, g['angles'][:, f, j], color=color, lw=1.1, label=name)
        for w in far_windows:
            if w['finger'] == f+1:
                ax.axvspan(w['start_s'], w['end_s'], color='#39a5a5', alpha=.13)
        for target in targets:
            if target['finger'] == f+1:
                ax.axvspan(target['press_s'], target['end_s'], color='#ffb047', alpha=.2)
        ax.set(ylabel=FINGERS[f]+' (deg)', ylim=(-105, 130)); ax.grid(alpha=.2)
    axes[0].legend(loc='upper left', ncol=3)
    axes[-1].set_xlabel('Physical clock / rendered caption (s); video PTS = clock - 1/60s; teal: score-only far idle; orange: own press..end; pale bands: B +/-15deg')
    fig.suptitle('v20 A500, repeat1 env0: actual geometric flexion (60 Hz endpoints)')
    fig.tight_layout(); fig.savefig(PHASE/'plots/selected_geometric_angles.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(4, 1, figsize=(16, 11), sharex=True)
    for f, ax in enumerate(axes):
        for j, label in enumerate(('native MCP1_x', 'native MCP1_z (spread)', 'native PIP', 'native DIP')):
            ax.plot(times, g['native'][:, f, j], lw=1, label=label)
        ax.set(ylabel=FINGERS[f]+' (deg)'); ax.grid(alpha=.2)
    axes[0].legend(ncol=4); axes[-1].set_xlabel('Physical clock / rendered caption (s); video PTS = clock - 1/60s')
    fig.suptitle('Recorded native joint positions; not the source-body geometric MCP definition')
    fig.tight_layout(); fig.savefig(PHASE/'plots/selected_native_angles.png', dpi=150); plt.close(fig)
    fig, axes = plt.subplots(5, 1, figsize=(16, 11), sharex=True, gridspec_kw={'height_ratios':[1,1,1,1,1.4]})
    for f, ax in enumerate(axes[:4]):
        ax.plot(times, state['idle'][:,f], color='#777', label='Temporal idle upper bound')
        ax.scatter(times[state['known_full'][:,f]], np.ones(state['known_full'][:,f].sum())*.85, s=2, color='#009d77', label='Gate=1 certain at saved endpoint')
        ax.scatter(times[state['unknown'][:,f]], np.ones(state['unknown'][:,f].sum())*.45, s=2, color='#d98a00', label='Contact veto unknown')
        ax.scatter(times[state['known_off'][:,f]], np.ones(state['known_off'][:,f].sum())*.05, s=2, color='#bd4444', label='Gate=0 certain at saved endpoint')
        ax.set(ylabel=FINGERS[f], ylim=(-.1,1.15)); ax.grid(alpha=.2)
    axes[0].legend(ncol=4, loc='upper center', fontsize=8)
    for pair in range(3):
        axes[4].plot(times, g['centerline_separation'][:,pair]*1000, label=FINGERS[pair]+'/'+FINGERS[pair+1])
    axes[4].axhline(5, color='gray', ls=':'); axes[4].legend(ncol=3)
    axes[4].set(ylabel='Sampled distal skeletal\ncenterline distance (mm)', xlabel='Physical clock / rendered caption (s); video PTS = clock - 1/60s')
    fig.suptitle('Saved-endpoint gate classification; no exact 240Hz transition or mesh penetration claim')
    fig.tight_layout(); fig.savefig(PHASE/'plots/selected_gate_and_proximity.png', dpi=150); plt.close(fig)


def main():
    result = dict(schema='guitar_learning.v20_saved_pose_standby_diagnosis.v1',
        scope='60Hz saved endpoints plus existing exact 240Hz episode aggregates; no physics rerun',
        time_basis='All time_s/start_s/end_s and plot axes are physical clock/240 seconds, equal to the rendered caption. Existing video PTS = physical clock - 1/60s for capture frames1..end. Reset frame0 has no video frame.',
        limitations=['Candidate/wrong per finger and four physics substeps are not saved; exact contact veto transition times cannot be reconstructed.',
                    'Reversed fingertip lateral order and sampled skeletal centerline proximity are geometric proxies, not mesh collision or pressure.',
                    'Captured env0..7 are predeclared low IDs, not an unbiased whole1024 population sample.'],
        geometric_B_reference_degrees=REFERENCE.tolist(), fingerprints={}, traces=[], selected={})
    pad = load_fingertip_pad()
    all_rows, metrics = [], []
    max_angle_error = 0.
    max_distance_error = 0.
    for cohort in ('evaluation', 'baseline'):
        for repeat in range(1, 4):
            directory = SOURCE/(cohort+'_repeat'+str(repeat))
            meta = json.loads((directory/'capture_metadata.json').read_text())
            targets = json.loads((directory/'targets.json').read_text())
            duration = max(c['duration_s'] for c in meta['captures'])
            far_windows = windows(targets, duration, 2.)
            if cohort == 'evaluation' and repeat == 1:
                dump(PHASE/'raw/score_far_idle_windows.json', far_windows)
                write_csv(PHASE/'raw/score_far_idle_windows.csv', far_windows)
            press_surface = load_press_surface([t['string'] for t in targets], [t['fret'] for t in targets])
            episodes = {e['env_id']: e for e in map(json.loads, (directory/'first_episodes.jsonl').read_text().splitlines())}
            for env in range(8):
                path = directory/('poses_env%04d.npz'%env)
                result['fingerprints'][str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
                with np.load(path) as source:
                    pose = {k: source[k] for k in source.files}
                times = pose['clock']/240
                g = geometry(pose, meta)
                temp = temporal(times, targets)
                # Independently validate signed source-body geometry against production Torch.
                q = torch.tensor(pose['body_state'][::97,:,3:7], dtype=torch.float64)
                indices = meta['posture_reconstruction']['segment_body_indices']
                palm = meta['posture_reconstruction']['palm_body_index']
                checked = finger_posture_reward(torch.tensor(times[::97]),
                    *[torch.tensor([t[key] for t in targets], dtype=torch.float64) for key in ('onset_s','end_s','press_s')],
                    torch.tensor([t['finger'] for t in targets]), q[:,palm], q[:,indices])
                error = np.max(np.abs(checked['angles'].numpy()*180/np.pi-g['angles'][::97]))
                max_angle_error = max(max_angle_error, float(error))
                trace = dict(cohort=cohort, repeat=repeat, env_id=env, reason=episodes[env]['reason'],
                    duration_s=float(times[-1]), endpoint_count=len(times), fingers=[])
                for f in range(4):
                    idle = temp['far_idle'][1:,f]
                    press = temp['pressing'][1:,f]
                    row = dict(finger=FINGERS[f], initial_angles=g['angles'][0,f].tolist(),
                        initial_quality=float(g['quality'][0,f]), initial_native=g['native'][0,f].tolist(),
                        final_angles=g['angles'][-1,f].tolist(), final_native=g['native'][-1,f].tolist(),
                        far_idle_sampled_s=float(idle.sum()/60),
                        far_idle_in_B_fraction=float(g['inside'][1:,f][idle].mean()) if idle.any() else None,
                        far_idle_angles=summary_array(g['angles'][1:,f][idle]) if idle.any() else None,
                        press_angles=summary_array(g['angles'][1:,f][press]) if press.any() else None,
                        native_angles=summary_array(g['native'][1:,f]),
                        native_target_actual_rms_deg=np.sqrt(np.square(g['target'][1:,f]-g['native'][1:,f]).mean(0)).tolist())
                    trace['fingers'].append(row)
                    metrics.append(dict(cohort=cohort, repeat=repeat, env_id=env, finger=FINGERS[f],
                        far_idle_sampled_s=row['far_idle_sampled_s'], far_idle_in_B_fraction=row['far_idle_in_B_fraction'],
                        mean_MCP_deg=float(g['angles'][1:,f,0].mean()),mean_PIP_deg=float(g['angles'][1:,f,1].mean()),
                        mean_DIP_deg=float(g['angles'][1:,f,2].mean()), mean_spread_deg=float(g['native'][1:,f,1].mean())))
                trace['adjacent_pairs'] = [dict(pair=FINGERS[f]+'/'+FINGERS[f+1],
                    reversed_fingertip_lateral_order_s=float(g['reversed_order'][1:,f].sum()/60),
                    distal_centerline_min_mm=float(g['centerline_separation'][1:,f].min()*1000),
                    distal_centerline_below5mm_s=float((g['centerline_separation'][1:,f]<.005).sum()/60)) for f in range(3)]
                result['traces'].append(trace)
                if cohort != 'evaluation' or repeat != 1 or env != 0:
                    continue
                expected_windows = episodes[0]['left_episode_diagnostics']['recovery']['windows']
                assert len(far_windows) == len(expected_windows)
                for actual, expected in zip(far_windows, expected_windows):
                    assert actual['finger'] == expected['finger']
                    assert abs(actual['start_s']-expected['start_s']) < 1e-12
                    assert abs(actual['end_s']-expected['end_s']) < 1e-12
                distance, error = pad_distances(pose, meta, targets, pad, press_surface)
                max_distance_error = max(max_distance_error, error)
                near = ((distance<=.04)[:,None] & temp['own_relevant']).any(-1)
                invalid = ((~np.isfinite(distance))[:,None] & temp['own_relevant']).any(-1)
                known_off = (temp['idle']==0) | near | invalid
                known_full = (temp['idle']==1) & ~temp['own_relevant'].any(-1)
                known_partial = (temp['idle']>0) & (temp['idle']<1) & ~temp['own_relevant'].any(-1)
                unknown = ~(known_off|known_full|known_partial)
                state = dict(**temp, near=near, known_off=known_off, known_full=known_full,
                             known_partial=known_partial, unknown=unknown)
                # Helper parity with all missing contact vetoes deliberately false: upper bound only.
                gate = finger_preparation_gate(torch.tensor(times),
                    *[torch.tensor([t[key] for t in targets], dtype=torch.float64) for key in ('onset_s','end_s','press_s')],
                    torch.tensor([t['finger'] for t in targets]), torch.zeros(len(times),4,dtype=torch.bool), torch.tensor(distance))
                expected_upper = temp['idle']*~(near|invalid)
                assert np.max(np.abs(gate['gate'].numpy()-expected_upper)) < 1e-12
                selected_intervals = []
                for f in range(4):
                    for label in ('known_off','known_full','known_partial','unknown'):
                        for entry in intervals(state[label][:,f],times):
                            selected_intervals.append(dict(finger=FINGERS[f],classification=label,**entry))
                write_csv(PHASE/'raw/selected_gate_endpoint_intervals.csv', selected_intervals)
                for k,t in enumerate(times):
                    for f in range(4):
                        all_rows.append(dict(time_s=float(t),finger=FINGERS[f],MCP_deg=float(g['angles'][k,f,0]),
                            PIP_deg=float(g['angles'][k,f,1]),DIP_deg=float(g['angles'][k,f,2]),
                            native_MCP1_x_deg=float(g['native'][k,f,0]),native_MCP1_z_deg=float(g['native'][k,f,1]),
                            native_PIP_deg=float(g['native'][k,f,2]),native_DIP_deg=float(g['native'][k,f,3]),
                            B_quality=float(g['quality'][k,f]),B_inside=bool(g['inside'][k,f]),
                            temporal_idle_upper=float(temp['idle'][k,f]),far_idle=bool(temp['far_idle'][k,f]),
                            near_veto=bool(near[k,f]),known_gate_full=bool(known_full[k,f]),
                            known_gate_off=bool(known_off[k,f]),contact_gate_unknown=bool(unknown[k,f])))
                result['selected'] = dict(trace=trace, exact_episode_diagnostics=episodes[0]['left_episode_diagnostics'],
                    endpoint_gate_intervals=selected_intervals,
                    time_mapping='All time_s values and plot axes use physical clock/240 seconds, equal to the rendered caption. Existing videos emit capture frames1..end: video PTS0 is physical clock1/60s, so seek PTS=physical time-1/60s for emitted frames. Reset capture frame0 is retained only in NPZ and has no video frame.',
                    B_band_entry_endpoint_counts=g['inside'][1:].sum(0).tolist())
                action_idx = np.array([[ACTIVE_NAMES.index('LH:'+f+s) for s in ('1_x','1_z','2','3')] for f in FINGERS])
                actions = pose['action'][:,action_idx]
                result['selected']['far_idle_action_mean'] = [actions[1:,f][temp['far_idle'][1:,f]].mean(0).tolist() for f in range(4)]
                result['selected']['known_full_action_mean'] = [actions[1:,f][known_full[1:,f]].mean(0).tolist() for f in range(4)]
                result['selected']['native_action_order'] = ['MCP1_x','MCP1_z','PIP','DIP']
                keyframes = []
                for desired in [0.,1.5,5.75,7.083333333333333,11.583333333333334,23.3,28.4,32.8]:
                    k = int(np.argmin(np.abs(times-desired)))
                    for f in range(4):
                        keyframes.append(dict(time_s=float(times[k]),frame_index=k,finger=FINGERS[f],
                            MCP_deg=float(g['angles'][k,f,0]),PIP_deg=float(g['angles'][k,f,1]),
                            DIP_deg=float(g['angles'][k,f,2]),native_spread_deg=float(g['native'][k,f,1]),
                            B_quality=float(g['quality'][k,f]),B_inside=bool(g['inside'][k,f]),
                            known_gate_full=bool(known_full[k,f]),known_gate_off=bool(known_off[k,f]),
                            contact_unknown=bool(unknown[k,f])))
                write_csv(PHASE/'raw/selected_keyframes.csv', keyframes)
                plot_selected(times, g, state, targets, far_windows)
                np.savez_compressed(PHASE/'raw/selected_reconstructed.npz', times_s=times, angles_degrees=g['angles'],
                    native_degrees=g['native'],target_native_degrees=g['target'],quality=g['quality'],B_inside=g['inside'],
                    idle_upper=temp['idle'],near=near,known_full=known_full,known_off=known_off,contact_unknown=unknown,
                    pad_distance_m=distance,centerline_distance_m=g['centerline_separation'],
                    reversed_tip_order=g['reversed_order'],tip_local=g['top_local'])
    assert max_angle_error < 1e-10 and max_distance_error < 1e-10
    result['validation'] = dict(numpy_torch_max_geometric_angle_error_deg=max_angle_error,
        numpy_torch_reset67_pad_distance_max_error_m=max_distance_error,
        gate_with_no_contact_upper_bound_parity=True,
        score_far_idle_windows_match_existing_episode_diagnostics=True,
        trace_count=len(result['traces']), physics_rerun=False)
    write_csv(PHASE/'raw/selected_endpoints.csv', all_rows)
    write_csv(PHASE/'raw/all48_pose_metrics.csv', metrics)
    dump(PHASE/'frame_analysis.json', result)
    dump(PHASE/'support/frame_validation.json', result['validation'])
    print(json.dumps(result['validation']))


if __name__ == '__main__':
    main()
