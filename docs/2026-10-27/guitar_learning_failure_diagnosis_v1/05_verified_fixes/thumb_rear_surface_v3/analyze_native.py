"""Recheck both production captures from saved poses, without native execution."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

import numpy as np
from scipy.spatial.transform import Rotation


BASE = Path(__file__).resolve().parent
ORACLE = BASE.parents[1]/'04_ablation/thumb_geometry_audit/native_comparison/analysis_v1/analyze.py'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    spec = importlib.util.spec_from_file_location('independent_thumb_oracle', ORACLE)
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    fixture_path = BASE/'precommitted_native_face_geometry.npz'
    fixture = dict(np.load(fixture_path))
    pins = {str(p): sha(p) for p in (Path(__file__), ORACLE, fixture_path)}
    results = {}
    for mode, name in (('fixed', 'native_regression_01'), ('free', 'native_free_regression_01')):
        folder = BASE/name
        report = json.loads((folder/'report.json').read_text())
        launcher = json.loads((BASE/(name+'_launcher.json')).read_text())
        declared = json.loads((folder/'inputs_before.json').read_text())
        assert all(sha(p) == h for p, h in declared.items())
        pins.update(declared)
        for p in (folder/'report.json', folder/'inputs_before.json', folder/'physics_env0000.npz',
                  folder/'native_thumb_oblique.mp4', BASE/(name+'_launcher.json')):
            pins[str(p)] = sha(p)
        a = np.load(folder/'physics_env0000.npz')
        assert len(a['time_s']) == 3600 and report['completed'] and launcher['returncode'] == 0
        assert report['scene']['closed'] and report['scene']['physx_use_gpu'] and report['scene']['use_gpu_pipeline']
        assert report['scene']['reset_calls'] == 1 and report['scene']['physics_steps'] == 3600
        if mode == 'fixed':
            assert report['scene']['diagnostic_guitar_asset']['requested_fix_base_link']
        else:
            assert report['scene']['diagnostic_guitar_mode'] is None
        measured = oracle.geometry(a['thumb_selected_point'], a['thumb_selected_normal'],
            a['thumb_force_G'], a['thumb_valid'], report['fixed_work_center_y_m'], fixture)
        errors = {}
        for key, value in measured.items():
            observed = a['thumb_'+key]
            errors[key] = int(np.count_nonzero(value != observed)) if key == 'contact_candidate' else float(np.max(np.abs(value-observed)))
            assert errors[key] == 0 if key == 'contact_candidate' else errors[key] < 3e-6
        events, stages = oracle.transitions(measured['contact_candidate'])
        assert np.array_equal(stages, a['stage'])
        assert [(e['time_s'], e['next']) for e in events] == [(e['time_s'], e['next']) for e in report['transitions']]
        ids = a['thumb_sample_index'].astype(int)
        thumb = a['body_state'][:, report['body_names'].index('human/LH:thumb3')]
        guitar = a['body_state'][:, report['body_names'].index('guitar/guitar')]
        rt, rg = Rotation.from_quat(thumb[:, 3:7]), Rotation.from_quat(guitar[:, 3:7])
        reconstructed = rg.inv().apply(thumb[:, :3]+rt.apply(fixture['points_local'][ids])-guitar[:, :3])
        pose_error = float(np.max(np.abs(reconstructed-a['thumb_selected_point'])))
        assert pose_error < 1e-6
        phase = {}
        for stage in dict.fromkeys(stages):
            mask = stages == stage
            load = measured['normal_load'][mask]
            phase[stage] = dict(endpoints=int(mask.sum()), seconds=float(mask.sum()/240),
                candidate_fraction=float(measured['contact_candidate'][mask].mean()),
                normal_load_mean_N=float(load.mean()), normal_load_max_N=float(load.max()),
                final_gap_mm=float(measured['signed_gap'][mask][-1]*1000))
            for key in ('seconds', 'candidate_fraction', 'normal_load_mean_N', 'normal_load_max_N'):
                assert abs(phase[stage][key]-report['measured_stages'][stage][key]) < 3e-6
        video = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames',
            '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,nb_read_frames',
            '-show_entries', 'format=duration', '-of', 'json', str(folder/'native_thumb_oblique.mp4')]))
        assert video['streams'][0] == dict(width=1280, height=720, r_frame_rate='30/1', nb_read_frames='450')
        assert abs(float(video['format']['duration'])-15.) < .001
        results[mode] = dict(execution_passed=True, protocol=report['protocol_passed'],
            all_protocol_passed=all(report['protocol_passed'].values()),
            fixed_witness_release_2mm_passed=report['fixed_witness_release_2mm_passed'],
            candidate_endpoints=int(measured['contact_candidate'].sum()), phases=phase,
            independent_geometry_errors=errors, selected_point_pose_max_error_m=pose_error,
            guitar_translation_max_m=float(a['guitar_translation'].max()),
            guitar_rotation_max_rad=float(a['guitar_rotation'].max()), video=video)
    assert all(sha(p) == h for p, h in pins.items())
    result = dict(verification_passed=True, results=results, input_pins=pins,
        limitation='One first-attempt native scene per mode; body resultant and source geometry, not pair pressure or learned/full-song performance. Free protocol failure is retained.')
    (BASE/'native_analysis.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: dict(all_protocol_passed=v['all_protocol_passed'],
        candidate_endpoints=v['candidate_endpoints']) for k, v in results.items()}))


if __name__ == '__main__':
    main()
