"""Read-only analysis of the additional actual240Hz A500 observation run."""
import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

PHASE = Path(__file__).resolve().parents[1]
SOURCE = PHASE/'gpu_trace'
FINGERS = ('index', 'middle', 'ring', 'pinky')
HZ = 240.


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def intervals(mask, time):
    """Completed endpoint runs; duration=count/240, not last minus first."""
    mask = np.asarray(mask, dtype=bool)
    starts = np.flatnonzero(mask & ~np.r_[False, mask[:-1]])
    ends = np.flatnonzero(mask & ~np.r_[mask[1:], False])
    return [dict(first_endpoint_s=float(time[a]), last_endpoint_s=float(time[b]),
                 endpoint_count=int(b-a+1), sampled_s=float((b-a+1)/HZ),
                 first_index=int(a), last_index=int(b)) for a, b in zip(starts, ends)]


def summarize(values, mask=None):
    v = np.asarray(values)[mask] if mask is not None else np.asarray(values)
    return dict(count=int(v.size), mean=float(v.mean()) if v.size else None,
                rms=float(np.sqrt(np.square(v).mean())) if v.size else None,
                min=float(v.min()) if v.size else None, max=float(v.max()) if v.size else None)


def correlation(a, b):
    return float(np.corrcoef(a, b)[0, 1]) if np.std(a) > 1e-12 and np.std(b) > 1e-12 else None


def first_stable(mask, times, minimum_s=.1):
    eligible = [row for row in intervals(mask, times) if row['sampled_s'] >= minimum_s-1e-12]
    return eligible[0] if eligible else None


def write_csv(path, rows):
    with path.open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def plot_trace(trace, reference):
    t, angles = trace['time_s'], np.rad2deg(trace['angles'])
    fig, axes = plt.subplots(4, 2, figsize=(16, 12), sharex=True)
    colors = ('#1572b8', '#e57c1d', '#4b963f')
    for f, name in enumerate(FINGERS):
        left, right = axes[f]
        left.plot(t, trace['idle_weight'][:, f], color='.6', ls='--', label='temporal idle')
        left.plot(t, trace['gate'][:, f], color='#1572b8', lw=1.1, label='actual standby gate')
        left.fill_between(t, 0, .24, where=trace['near_veto'][:, f], color='#d85555', alpha=.6, label='near veto')
        left.fill_between(t, .27, .51, where=trace['contact_veto'][:, f], color='#f4a340', alpha=.65, label='candidate/wrong veto')
        left.set_ylim(-.04, 1.08)
        left.set_ylabel(name+' gate')
        for j, joint in enumerate(('MCP', 'PIP', 'DIP')):
            right.axhspan(reference[f, j]-15, reference[f, j]+15, color=colors[j], alpha=.085)
            right.plot(t, angles[:, f, j], color=colors[j], lw=1., label=joint)
        right.fill_between(t, -65, 110, where=trace['pressing'][:, f], color='#ef8686', alpha=.11,
                           label='own press..end')
        right.set_ylim(-65, 110)
        right.set_ylabel(name+' geometric flexion (deg)')
        for ax in (left, right):
            ax.grid(alpha=.2)
            for stamp in (7.083, 23.3, 28.4):
                ax.axvline(stamp, color='.55', lw=.65, ls=':')
        if f == 0:
            left.legend(loc='lower right', fontsize=8)
            right.legend(loc='lower right', fontsize=8)
    axes[-1, 0].set_xlabel('Prepared-song time (s); actual 240 Hz endpoints')
    axes[-1, 1].set_xlabel('Prepared-song time (s); bands are B reference ±15 deg')
    fig.suptitle('Additional A500 evaluation, env0: exact reward gate and actual geometric angles\n'
                 'A new GPU trajectory; separate from the previously rendered videos', fontsize=13)
    fig.tight_layout(rect=(0, 0, 1, .95))
    fig.savefig(PHASE/'plots/exact_gate_and_angles.png', dpi=170)
    plt.close(fig)


def main():
    trace_report = SOURCE/'trace_report.json'
    if not trace_report.exists():
        raise ValueError('Wait for completed native evaluation and trace_report.json before analysis')
    capture = json.loads(trace_report.read_text())
    if not capture['completed'] or not capture['inputs_unchanged']:
        raise ValueError('Completed immutable observation run required')
    oldpath = PHASE/'frame_analysis.json'
    old = json.loads(oldpath.read_text())
    reference = np.asarray(old['geometric_B_reference_degrees'])
    names = capture['finger_joint_names']
    paths = [SOURCE/'physics'/row['path'] for row in capture['captures']]
    if len(paths) != 8:
        raise ValueError('Exactly eight predeclared observed environments required')
    fingerprints = {str(p): sha(p) for p in paths+[trace_report, SOURCE/'first_episodes.jsonl',
        SOURCE/'targets.json', oldpath, Path(__file__).resolve()]}
    if any(sha(path) != row['sha256'] for path, row in zip(paths, capture['captures'])):
        raise ValueError('Native trace capture checksum differs')
    episodes = {row['env_id']: row for row in map(json.loads,
                (SOURCE/'first_episodes.jsonl').read_text().splitlines())}
    rawdir = PHASE/'raw'
    rawdir.mkdir(exist_ok=True)
    (PHASE/'plots').mkdir(exist_ok=True)
    reports, interval_rows, snapshot_rows, sequence_rows, spread_rows = [], [], [], [], []
    for capture_row, path in zip(capture['captures'], paths):
        index = capture_row['env_id']
        with np.load(path) as loaded:
            a = {k: loaded[k] for k in loaded.files}
        t, angles = a['time_s'], np.rad2deg(a['angles'])
        if len(t) != episodes[index]['steps']*4:
            raise ValueError('Trace/native first episode endpoint count differs')
        fingers = []
        for f, finger in enumerate(FINGERS):
            gates = {}
            for mode, mask in (('gate_positive', a['gate'][:, f] > 0),
                               ('gate_full', a['gate'][:, f] == 1)):
                runs = intervals(mask, t)
                gates[mode] = dict(total_s=float(mask.sum()/HZ), count=len(runs),
                    max_s=max((r['sampled_s'] for r in runs), default=0.), intervals=runs,
                    in_B_s=float((mask & a['band_inside'][:, f]).sum()/HZ))
                for run in runs:
                    interval_rows.append(dict(env_id=index, finger=finger, mode=mode, **run))
                native = episodes[index]['left_episode_diagnostics']['standby'][
                    'actual_gate_runs' if mode == 'gate_positive' else 'full_gate_runs']
                # The native run counters divide int tensors in Torch's
                # default float32. Recover their integer endpoint count;
                # requiring float64 seconds equality would reject valid data.
                if (int(mask.sum()) != round(native['total_s'][f]*HZ) or
                        len(runs) != native['count'][f]):
                    raise ValueError('Trace gate intervals differ from native episode counters')
                if mode == 'gate_positive':
                    eligible = episodes[index]['left_episode_diagnostics']['standby']['eligible_s'][f]
                    if abs(gates[mode]['total_s']-eligible) > 1e-8:
                        raise ValueError('Trace eligible time differs from native float64 integral')
            band = a['band_inside'][:, f] & a['valid'][:, f].all(-1)
            band_runs = intervals(band, t)
            returning = [r for r in band_runs if r['first_index'] > 0]
            full_band = intervals(band & (a['gate'][:, f] == 1), t)
            state_snapshots = []
            for stamp in (0., 7.083, 23.3, 28.4, float(t[-1])):
                if stamp > t[-1]+1e-9:
                    continue
                k = int(np.argmin(np.abs(t-stamp)))
                row = dict(env_id=index, finger=finger, requested_time_s=stamp,
                    actual_endpoint_s=float(t[k]), gate=float(a['gate'][k, f]),
                    idle_weight=float(a['idle_weight'][k, f]), quality=float(a['quality'][k, f]),
                    in_B=bool(band[k]), pressing=bool(a['pressing'][k, f]),
                    near_veto=bool(a['near_veto'][k, f]), contact_veto=bool(a['contact_veto'][k, f]),
                    MCP_deg=float(angles[k, f, 0]), PIP_deg=float(angles[k, f, 1]), DIP_deg=float(angles[k, f, 2]))
                snapshot_rows.append(row)
                state_snapshots.append(row)
            native_indices = [names.index('LH:'+finger+s) for s in ('1_x', '1_z', '2', '3')]
            residual = np.rad2deg(a['target'][:, native_indices]-a['q'][:, native_indices])
            spread = residual[:, 1]
            force = np.linalg.norm(a['segment_contact_force'][:, f], axis=-1)
            loaded = (force >= .01).any(-1)
            association = dict(env_id=index, finger=finger,
                spread_residual_rms_deg=float(np.sqrt(np.square(spread).mean())),
                spread_residual_abs_max_deg=float(np.abs(spread).max()),
                loaded_fraction=float(loaded.mean()),
                spread_abs_residual_mean_loaded_deg=float(np.abs(spread[loaded]).mean()) if loaded.any() else None,
                spread_abs_residual_mean_unloaded_deg=float(np.abs(spread[~loaded]).mean()) if (~loaded).any() else None,
                spread_abs_residual_vs_sum_netload_correlation=correlation(np.abs(spread), force.sum(-1)),
                sum_segment_netload_mean_N=float(force.sum(-1).mean()),
                sum_segment_netload_max_N=float(force.sum(-1).max()))
            spread_rows.append(association)
            association['first_stable_spread_residual_over5deg'] = first_stable(np.abs(spread) > 5., t)
            association['first_stable_netload_ge0p01N'] = first_stable(loaded, t)
            row = dict(finger=finger, actual_gate=gates,
                geometric_B=dict(sampled_s=float(band.sum()/HZ), starts_inside=bool(band[0]),
                    entry_count=len(returning), stable_ge0p2s_return_count=sum(r['sampled_s'] >= .2 for r in returning),
                    entry_intervals=returning, fullgate_in_B_runs=full_band),
                geometric_angle_statistics_deg=[summarize(angles[:, f, j]) for j in range(3)],
                geometric_angle_mean_during_actual_gate_deg=[summarize(angles[:, f, j], a['gate'][:, f] > 0) for j in range(3)],
                native_target_actual_residual_deg=[summarize(residual[:, j]) for j in range(4)],
                spread_load_association=association, snapshots=state_snapshots)
            fingers.append(row)
            if index == 0:
                for k in np.flatnonzero((t >= 6.5) & (t <= 7.6)):
                    sequence_rows.append(dict(time_s=float(t[k]), finger=finger,
                        gate=float(a['gate'][k, f]), idle_weight=float(a['idle_weight'][k, f]),
                        near_veto=bool(a['near_veto'][k, f]), contact_veto=bool(a['contact_veto'][k, f]),
                        pressing=bool(a['pressing'][k, f]), in_B=bool(band[k]),
                        MCP_deg=float(angles[k, f, 0]), PIP_deg=float(angles[k, f, 1]), DIP_deg=float(angles[k, f, 2]),
                        native_spread_q_deg=float(np.rad2deg(a['q'][k, native_indices[1]])),
                        native_spread_target_deg=float(np.rad2deg(a['target'][k, native_indices[1]])),
                        spread_action=float(a['action'][k, native_indices[1]]),
                        spread_residual_deg=float(spread[k]), sum_segment_netload_N=float(force[k].sum())))
        reports.append(dict(env_id=index, duration_s=float(t[-1]), endpoint_count=len(t),
            reason=episodes[index]['reason'], left_success_count=episodes[index]['song']['left_success_count'], fingers=fingers))
        if index == 0:
            plot_trace(a, reference)
    write_csv(rawdir/'exact_gate_intervals.csv', interval_rows)
    write_csv(rawdir/'exact_snapshots.csv', snapshot_rows)
    write_csv(rawdir/'exact_env0_phase_6p5_to7p6.csv', sequence_rows)
    write_csv(rawdir/'exact_spread_association.csv', [{k: v for k, v in r.items()
        if not k.startswith('first_stable_')} for r in spread_rows])
    result = dict(schema='guitar_learning.v20_actual240_standby_diagnosis.v1',
        scope='Additional deterministic A500 evaluation, actual240Hz reward helper copies and native human net contact resultants; no learning.',
        time_alignment='q and angles are completed physics endpoints; target and action are the held command applied over that control tick. There is no t0 in physics arrays; requested initial snapshot is the first endpoint1/240s.',
        limitations=['This is a new GPU trajectory, not the trajectory of any previous rendered video.',
            'The predeclared env0..7 are not an unbiased1024-environment sample.',
            'Net force resultants do not identify body pairs, pressure, torque, penetration, or the causal reason for tracking residuals.',
            'Band entry and gate runs use completed endpoint counts; sub-endpoint transitions are not inferred.',
            'Gate veto flags overlap; their durations must not be summed as disjoint states.'],
        geometric_B_reference_degrees=reference.tolist(), fingerprints=fingerprints,
        original_rendered_env0_summary=old['selected']['trace'],
        original_comparison='Original summary is saved60Hz geometry from evaluation_repeat1 env0. The reports below are a separate new240Hz GPU run; never combine their event times.',
        traces=reports)
    output = PHASE/'exact_trace_analysis.json'
    output.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    if any(sha(path) != h for path, h in fingerprints.items()):
        raise ValueError('Read-only analysis input changed')
    print(json.dumps(dict(completed=True, traces=len(reports), output=str(output))))


if __name__ == '__main__':
    main()
