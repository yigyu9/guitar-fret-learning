"""CPU measurements of actual ring/pinky pulses; no automatic jam diagnosis."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io
import numpy as np


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def load_npz(path):
    with np.load(str(path), allow_pickle=False) as data:
        return {k: data[k] for k in data.files}


def force_summary(raw, row, names, prefix, finger):
    result = {}
    windows = dict(push=(0,240), hold=(240,360), return_original=(360,600), posthold=(600,720))
    if prefix:
        windows['prefix_last_half_s'] = (-120,0)
    for part in (1,2,3):
        name = 'human/LH:'+finger+str(part)
        body = names.index(name)
        result[name] = {}
        for label, (a,b) in windows.items():
            values = raw['contact_force_norm'][prefix*4+a:prefix*4+b,row,body]
            assert len(values) == b-a
            result[name][label] = dict(peak_N=float(values.max()), mean_N=float(values.mean()),
                loaded_s=float(np.count_nonzero(values >= .01)/240.))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    run = args.run.resolve()
    outer = json.loads((run/'report.json').read_text())
    assert outer['completed'] is True
    pins = {str(Path(__file__).resolve()): sha(__file__)}
    variants = []
    for variant in ('prepared','learned10'):
        folder = run/variant
        report = json.loads((folder/'report.json').read_text())
        meta = json.loads((folder/'capture_metadata.json').read_text())
        assert report['completed'] and report['schedule_completed'] and report['probe_started']
        assert report['gpu_scene']['closed'] and report['PPO_updates'] == 0
        assert report['model_and_curriculum_unchanged'] and not report['first_ended_episodes']
        for path in (run/'report.json', folder/'report.json', folder/'capture_metadata.json'):
            pins[str(path)] = sha(path)
        for path, expected in json.loads((folder/'inputs_before.json').read_text()).items():
            assert path not in pins or pins[path] == expected
            pins[path] = expected
        raw_path = folder/meta['native_capture']['path']
        assert sha(raw_path) == meta['native_capture']['sha256']
        pins[str(raw_path)] = sha(raw_path)
        raw = load_npz(raw_path)
        assert all(np.isfinite(a).all() for a in raw.values())
        captures = []
        for case in meta['cases']:
            path = folder/case['path']
            assert sha(path) == case['sha256']
            pins[str(path)] = case['sha256']
            captures.append(load_npz(path))
        p = meta['probe_start_frame']
        assert p == meta['prefix_ticks'] and len(captures) == 18
        assert raw['q'].shape == ((p+180)*4,18,105)
        assert np.array_equal(raw['global_physics_step'], np.arange(1,(p+180)*4+1))
        rows = []
        for case, trace in zip(meta['cases'], captures):
            row = case['env_id']
            assert len(trace['q']) == p+181
            for key in ('q','qd','target'):
                assert np.array_equal(trace[key][1:], raw[key][3::4,row])
            assert np.array_equal(trace['clock'], np.arange(p+181)*4)
            assert all(np.isfinite(a).all() for a in trace.values())
            result = dict(env_id=row,kind=case['kind'],joint=case['joint'],direction=case['direction'],
                force={finger:force_summary(raw,row,meta['native_body_names'],p,finger)
                       for finger in ('ring','pinky')})
            if case['kind'] == 'pulse':
                axis = case['axis_index']; j = meta['tested_native_indices'][axis]
                t = trace['target'][:,j]; q = trace['q'][:,j]
                expected = case['expected_clipped_pulse_delta_rad']
                actual_target = float(t[p+60]-t[p])
                assert abs(actual_target-expected) < 5e-6
                assert abs(float(t[p+90]-t[p+60])) < 5e-6
                assert abs(float(t[p+150]-t[p])) < 5e-6
                pulse_q = float(q[p+90]-q[p])
                baseline = captures[16]['q'][:,j]
                baseline_delta = float(baseline[p+90]-baseline[p])
                return_q = float(q[p+180]-q[p])
                result.update(target_start_rad=float(t[p]),q_start_rad=float(q[p]),
                    allowed_target_delta_rad=actual_target,meaningful_target_excursion=abs(actual_target)>=.05,
                    settled_q_delta_rad=pulse_q,hold_row_q_delta_rad=baseline_delta,
                    baseline_corrected_q_delta_rad=pulse_q-baseline_delta,
                    signed_follow_fraction=pulse_q/actual_target if abs(actual_target)>=1e-5 else None,
                    settled_target_error_rad=float(q[p+90]-t[p+90]),
                    max_q_range_during_probe_rad=float(np.ptp(q[p:])),
                    return_target_error_rad=float(t[p+180]-t[p]),
                    return_q_delta_from_start_rad=return_q,
                    return_baseline_corrected_q_delta_rad=return_q-float(baseline[p+180]-baseline[p]),
                    posthold_last_0p1s_qd_rms_rad_s=float(np.sqrt(np.mean(raw['qd'][-24:,row,j]**2))),
                    body_for_axis=meta['axes'][axis]['native_body_name'])
            else:
                ids = meta['tested_native_indices']
                result.update(target_delta8_rad=(trace['target'][-1,ids]-trace['target'][p,ids]).astype(float).tolist(),
                    q_delta8_rad=(trace['q'][-1,ids]-trace['q'][p,ids]).astype(float).tolist(),
                    end_error_to_prepared_target8_rad=(trace['target'][-1,ids]-np.asarray(meta['prepared_reference8'])).tolist())
            rows.append(result)
        variants.append(dict(variant=variant,probe_start_frame=p,
            probe_start_between_row_difference=meta['probe_start_between_row_difference'],
            non_tested_target_hold_max_error_rad=meta['non_tested_active_target_hold_max_error_rad'],
            cases=rows))
    assert all(Path(path).is_file() and sha(path)==expected for path,expected in pins.items())
    result = dict(completed=True,variants=variants,inputs_sha256=pins,
        limitations=['Movement is local to tested poses, speed and1s pulses; not all-pose freedom.',
            'Signed follow fractions use clipped target movement; small/zero native room is not jamming.',
            'Force is a native net body norm, not pair/witness/pressure; a zero net norm does not exclude cancelling contacts.',
            'Fixed case IDs and evolving closed-loop physics; hold-row subtraction is descriptive.',
            'Coordinated return lasts3s and may not reach the prepared targets. No learning or successful-song claim.'])
    with args.out.open('x') as stream:
        json_io.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json_io.dumps(dict(completed=True,variants=len(variants),cases_per_variant=18)))


if __name__ == '__main__':
    main()
