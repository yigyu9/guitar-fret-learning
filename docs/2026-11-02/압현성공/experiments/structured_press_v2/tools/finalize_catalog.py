"""실제 GPU 초기화 검사 결과를 후보별로 붙이고 학습용 자산을 봉인한다."""
import argparse
import hashlib
import json
import struct
from pathlib import Path


def pose_sha(q, hold):
    return hashlib.sha256(struct.pack('<210f', *(list(q)+list(hold)))).hexdigest()


def safe_rows(report, variant=None, expected_pose_sha256=None):
    indices = [r['env'] for r in report['initial'] if r['variant'] == variant]
    episodes = {row['env_id']: row for row in report['episodes']}
    flags = report.get('pretarget_press_240hz', report['pretarget_press'])
    reasons = []
    if not indices:
        reasons.append('variant not physically sampled')
    for index in indices:
        first = report['initial'][index]
        if expected_pose_sha256 is None or first.get('pose_sha256') != expected_pose_sha256:
            reasons.append('missing or changed native initial pose env '+str(index))
        native = report['first_physics'][index]
        episode = episodes.get(index)
        if first['candidate'] or first['wrong'] or native['candidate'] or native['wrong']:
            reasons.append('initial loaded press env '+str(index))
        if flags[index]:
            reasons.append('pretarget loaded press env '+str(index))
        if not episode or episode['reason'] != 'timeline_complete':
            reasons.append('physical/wrist/unfinished env '+str(index))
    return dict(verified=bool(indices) and not reasons, sampled_envs=indices,
        failures=reasons, contact_check_hz=240 if 'pretarget_press_240hz' in report else 60)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--catalog', type=Path, required=True)
    parser.add_argument('--a', type=Path, action='append', default=[])
    parser.add_argument('--b', type=Path, action='append', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    value = json.loads(args.catalog.read_text())
    a = {}
    for path in args.a:
        for row in json.loads(path.read_text())['goals']:
            a[row['song']] = (row, path)
    b = {}
    for path in args.b:
        for row in json.loads(path.read_text())['goals']:
            b[row['song']] = (row, path)
    result = dict(scope='finite-PD 6s hold; no PPO; physical candidate evidence only', goals=[])
    for goal in value['goals']:
        row, path = a.get(goal['song'], b[goal['song']])
        audit_path = path.parent/goal['song']/'gpu_scene_final.json'
        audit = json.loads(audit_path.read_text())
        if not (audit['physx_use_gpu'] and audit['use_gpu_pipeline'] and audit['closed']
                and audit['simulator_count'] == 1):
            raise ValueError('native GPU lifecycle missing: '+goal['song'])
        if not row.get('v9_reference_unchanged', False):
            raise ValueError('v9 action reference verification missing: '+goal['song'])
        center = row.get('center_variant')
        expected = pose_sha(goal['q105'], goal['hold_target105'])
        if row.get('center_pose_sha256') != expected:
            raise ValueError('native center source mismatch: '+goal['song'])
        validation = safe_rows(row, center, expected)
        if not validation['verified']:
            raise ValueError('A initial preparation failed: '+goal['song']+' '+str(validation))
        # A 패드 기하는 reset과 첫 실제 물리 tick 양쪽에서 확인한다.
        for index in validation['sampled_envs']:
            initial, physical = row['initial'][index], row['first_physics'][index]
            for sample in (initial, physical):
                tangent = max(0., sample['distance_m']**2-sample['height_m']**2)**.5
                if not (.005 <= sample['height_m'] <= .015 and tangent <= .005 and sample['normal_cos'] >= .1):
                    raise ValueError('A pad geometry failed: '+goal['song'])
        goal['native_verified'] = True
        goal['native_validation'] = dict(report=str(path.resolve()), **validation)
        perturbations = []
        for index, perturbation in enumerate(goal['perturbations']):
            hold = list(goal['hold_target105'])
            for axis in value['action_indices'][:12]:
                hold[axis] = perturbation['q105'][axis]
            check = safe_rows(b[goal['song']][0], index, pose_sha(perturbation['q105'], hold))
            perturbation['native_verified'] = check['verified']
            perturbation['native_validation'] = check
            perturbations.append(check)
        result['goals'].append(dict(song=goal['song'], A=validation,
            B_verified=sum(p['verified'] for p in perturbations), B_total=len(perturbations), B=perturbations))
    value['native_verified'] = True
    paths = [args.catalog]+args.a+args.b
    paths += [b[g['song']][1].parent/g['song']/'gpu_scene_final.json' for g in value['goals']]
    result['source_sha256'] = {str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')
    result['catalog_sha256'] = hashlib.sha256(args.out.read_bytes()).hexdigest()
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
