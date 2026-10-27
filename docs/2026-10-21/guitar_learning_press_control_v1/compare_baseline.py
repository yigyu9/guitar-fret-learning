"""CPU-only equal100-budget comparison; run after training and both evaluations close."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[3]
PHASE = Path(__file__).resolve().parent
OLD = PHASE.parent/'guitar_learning_incremental_fingers_v1'
OLD_SEAL = '1f743895bd7685e9885ed4264477d581113c3b1ac4c653d6c62f5279c7906f52'
TRANSITIONS = 100*32*1024
sys.path.insert(0, str(ROOT))
from guitar_learning.training import json_io


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def mean(values):
    return statistics.mean(values) if values else None


def finite(value):
    if isinstance(value, float):
        require(math.isfinite(value), 'Nonfinite numeric evidence')
    elif isinstance(value, dict):
        for item in value.values(): finite(item)
    elif isinstance(value, list):
        for item in value: finite(item)


def check_pins(pins, phase, historical):
    """Historical package Python resolves only to the sealed source copy."""
    for name, expected in pins.items():
        path = Path(name)
        if historical and path.suffix == '.py' and str(path).startswith(str(ROOT/'guitar_learning')+'/'):
            path = phase/'source_training'/path.relative_to(ROOT)
        require(path.is_file() and sha(path) == expected, 'Input SHA mismatch: '+str(path))
    return len(pins)


def closed_gpu(report):
    scene = report['gpu_scene']
    require(report['completed'] and scene['closed'] and scene['physx_use_gpu'] and
            scene['use_gpu_pipeline'] and scene['environment_count'] == 1024,
            'Completed, closed native GPU1024 evidence required')


def training_complete(report):
    closed_gpu(report)
    require(report['optimizer_updates'] == 100 and report['transitions'] == TRANSITIONS and
            len(report['updates']) == 100 and report['lifecycle_verified'] and
            report['gpu_scene']['physics_steps'] == 12800 and not report['failure'] and
            not report['cleanup_errors'] and not report['changed_inputs'] and not report['missing_import_pins'],
            'Actual complete100-update training required')
    journal = report['journal']
    require(all(journal[k] == TRANSITIONS for k in ('sampled', 'logged', 'durable', 'committed')) and
            journal['discarded'] == 0 and journal['pending_transitions'] == 0 and
            journal['closed'] and not journal['failed'], 'No discarded or incomplete journal allowed')


def validate_episodes(episodes, targets):
    for e in episodes:
        ledger = e['left_note_ledger']
        require(e['valid'] and 0 <= e['env_id'] < 1024 and
                ledger['target_ids'] == [t['target_id'] for t in targets] and
                all(len(v) == len(targets) for v in ledger['values'].values()) and
                sum(ledger['values']['left']) == e['song']['left_success_count'], 'Invalid raw note ledger')
        require((e['reason'] == 'timeline_complete' and e['left_curriculum']['full_safe']) or
                (e['reason'] == 'terminal_failure' and not e['left_curriculum']['full_safe']), 'Unexpected ended-song safety/reason')


def group(episodes, targets):
    """Equal episode means; failed songs retain partial exposure, not fake full songs."""
    fingers = []
    for finger in range(1, 5):
        indices = [i for i, target in enumerate(targets) if target['finger'] == finger]
        left = sum(sum(e['left_note_ledger']['values']['left'][i] for i in indices) for e in episodes)
        contact = sum(sum(e['left_note_ledger']['values']['contact_done'][i] for i in indices) for e in episodes)
        denominator = len(episodes)*len(indices)
        fingers.append(dict(finger=finger, assigned_notes=len(indices), achieved_total=left,
            success_fraction=left/denominator if denominator else None,
            contact_fraction=contact/denominator if denominator else None))
    failure = [e for e in episodes if not e['left_curriculum']['full_safe']]
    result = dict(episodes=len(episodes), safe=len(episodes)-len(failure), physical_failures=len(failure),
        mean_achieved_notes=mean([e['song']['left_success_count'] for e in episodes]),
        mean_clean_seconds=mean([math.fsum(e['left_note_ledger']['values']['clean']) for e in episodes]),
        mean_contact_fraction=mean([sum(e['left_note_ledger']['values']['contact_done'])/len(targets) for e in episodes]),
        full_task_successes=sum(e['song']['stage_success'] for e in episodes), fingers=fingers,
        mean_duration_s=mean([e['task_time_s'] for e in episodes]),
        failure_reason_occurrences=dict(Counter(r for e in failure for r in e['failure_reasons'])),
        failure_mean_duration_s=mean([e['task_time_s'] for e in failure]),
        failed_below1s=sum(e['task_time_s'] < 1 for e in failure),
        failed_at_most1s=sum(e['task_time_s'] <= 1 for e in failure))
    motions = [e['left_finger_motion'] for e in episodes if 'left_finger_motion' in e]
    result['motion_episodes'] = len(motions)
    if motions:
        names = motions[0]['joint_names']
        require(len(names) == 21 and all(m['joint_names'] == names for m in motions), 'LH21 diagnostic order changed')
        fields = ('actual_range_rad', 'target_range_rad', 'tracking_error_rms_rad',
                  'limit_outward_command_fraction', 'action_zero_fraction')
        result['motion'] = dict(joint_names=names,
            equal_episode_axis_means={k:[mean([m['values'][k][j] for m in motions]) for j in range(21)] for k in fields},
            all_one_sign_episode_fraction=[mean([max(m['values']['action_positive_fraction'][j],
                m['values']['action_negative_fraction'][j]) == 1. for m in motions]) for j in range(21)],
            scope='60Hz endpoint ranges include t0; equal episodes, not equal time; failed songs can be shorter. Requested target is not actual q or240Hz extrema.')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--new-run', type=Path, default=PHASE/'smoke100')
    parser.add_argument('--tag', default='smoke')
    args = parser.parse_args()
    inputs = {}
    def read(path):
        inputs[str(path)] = sha(path)
        value = json.loads(path.read_text()); finite(value)
        return value
    # Fail before writing any output while actual training/evaluation is absent.
    new_report = read(args.new_run/'report.json'); training_complete(new_report)
    require(sha(OLD/'result_manifest.json') == OLD_SEAL, 'Historical seal SHA differs')
    seal = read(OLD/'result_manifest.json')
    for name, record in seal['files'].items():
        require(sha(OLD/name) == record['sha256'] and (OLD/name).stat().st_size == record['bytes'], 'Historical sealed file changed: '+name)
    sources = {name:read(phase/'training_source_manifest.json')['source'] for name, phase in [('old', OLD), ('new', PHASE)]}
    require(len(sources['old']) == 430 and len(sources['new']) == 435, 'Expected430/435 frozen Python sources')
    for name, phase in [('old', OLD), ('new', PHASE)]:
        check_pins(sources[name], phase, name == 'old')
        for file, expected in sources[name].items():
            require(sha(phase/'source_training'/Path(file).relative_to(ROOT)) == expected, 'Frozen source copy mismatch')
    unchanged = {}
    for relative in ('gpu/control.py', 'gpu/scene.py', 'gpu/geometry.py', 'gpu/rigid_guitar.py',
                     'training/ppo.py', 'training/policy.py', 'skills/specialist_policy.py', 'core/finger_control.py'):
        name = str(ROOT/'guitar_learning'/relative)
        require(sources['old'][name] == sources['new'][name], 'Expected unchanged source: '+relative)
        unchanged[relative] = sources['new'][name]
    collection, fixed, target_sets, contracts, settings = {}, {}, {}, {}, {}
    for label, phase, run in [('old', OLD, OLD/'smoke100'), ('new', PHASE, args.new_run)]:
        report = read(run/'report.json'); training_complete(report)
        pins = read(run/'inputs_before.json'); check_pins(pins, phase, label == 'old')
        config = read(run/'settings.json'); settings[label] = config
        require((config['size'], config['num_envs'], config['horizon'], config['updates'], config['seed'], config['specialist']['role']) ==
                ('large', 1024, 32, 100, 7, 'left'), 'Expected same large1024/H32/seed7/fresh100 settings')
        require(report['settings'] == config, 'Training report settings differ')
        contract = read(run/'training_contract.json'); contracts[label] = contract
        targets = contract['task']['provenance']['song']['schedule']; require(len(targets) == 67, 'Expected67 song targets')
        episodes, curve, first = [], [], {}
        for index in range(100):
            row = read(run/('update_%06d.json' % index))
            require(row['update_index'] == index and row['optimizer_updates'] == index+1 and row['transitions'] == 32768 and
                    row['journal']['committed'] == (index+1)*32768, 'Invalid committed100-update prefix')
            episodes.extend(row['completed_episodes'])
            curve.append({k:row[k] for k in ('actor_lr', 'analytic_kl', 'kl_retries', 'mean_reward', 'mean_cost')})
            curve[-1]['std_mean'] = row['diagnostics']['post_update']['active_distribution']['std']['mean']
            for e in row['completed_episodes']: first.setdefault(e['env_id'], e)
        require(len(first) == 1024, 'Complete first1024 collection episodes required')
        validate_episodes(episodes, targets)
        # Independent ended stream must exactly match committed update payloads.
        stream = run/'episodes.jsonl'; inputs[str(stream)] = sha(stream)
        require([json.loads(s)['episode'] for s in stream.read_text().splitlines()] == episodes, 'Committed/ended episode stream differs')
        collection[label] = dict(committed_updates=100, committed_transitions=TRANSITIONS,
            all_ended=group(episodes, targets), safe_ended=group([e for e in episodes if e['left_curriculum']['full_safe']], targets),
            failed_ended=group([e for e in episodes if not e['left_curriculum']['full_safe']], targets),
            first1024=group(list(first.values()), targets), latest_curriculum=read(run/'update_000099.json')['left_curriculum'],
            ppo_update_means={k:mean([r[k] for r in curve]) for k in ('actor_lr', 'analytic_kl', 'kl_retries', 'std_mean')},
            ppo_first_and_last=[curve[0], curve[-1]],
            reward_means_different_objectives={k:mean([r[k] for r in curve]) for k in ('mean_reward', 'mean_cost')},
            scope='Changing stochastic policies, repeated cycles and open songs excluded from ended means; never a fixed-policy score.')
        prefix = 'smoke_' if label == 'old' else args.tag+'_' if args.tag else ''
        combined = read(phase/(prefix+'checkpoint_evaluation.json'))
        require(combined['completed'] and len(combined['results']) == 2, 'Actual completed paired evaluation required')
        fixed[label], target_sets[label] = {}, targets
        for checkpoint, updates in [('initial', 0), ('final', 100)]:
            folder = phase/('evaluation_'+prefix+checkpoint+'_1024')
            evaluation = read(folder/'report.json'); closed_gpu(evaluation)
            require(evaluation == combined['results'][updates != 0] and evaluation['deterministic'] and
                    evaluation['source_optimizer_updates'] == updates and evaluation['ticks'] == 1969 and
                    evaluation['gpu_scene']['physics_steps'] == 7876, 'Invalid fixed0/100 evaluation evidence')
            check_pins(read(folder/'inputs_before.json'), phase, label == 'old')
            note_targets = read(folder/'targets.json')
            require(len(note_targets) == 67 and all(all(a[k] == b[k] for k in
                ('target_id', 'finger', 'string', 'fret', 'onset_s', 'end_s', 'press_s')) for a,b in zip(note_targets, targets)), 'Target mapping differs')
            path = folder/'first_episodes.jsonl'; inputs[str(path)] = sha(path)
            rows = sorted([json.loads(s) for s in path.read_text().splitlines()], key=lambda e:e['env_id']); finite(rows)
            require(len(rows) == 1024 and [e['env_id'] for e in rows] == list(range(1024)), 'Unique1024 first episodes required')
            require([{k:v for k,v in e.items() if k != 'left_note_ledger'} for e in rows] == evaluation['episodes'], 'Raw/report first episodes differ')
            validate_episodes(rows, targets)
            require(len(evaluation['per_note']) == 67, 'Complete67 per-note report required')
            for j, note in enumerate(evaluation['per_note']):
                require(all(note[k] == note_targets[j][k] for k in ('target_id', 'finger', 'string', 'fret', 'required_clean_s')), 'Per-note mapping mismatch')
                for name, selected in [('all_first', rows), ('full_safe_first', [e for e in rows if e['left_curriculum']['full_safe']])]:
                    require(note[name]['episodes'] == len(selected) and note[name]['left_success_count'] ==
                            sum(e['left_note_ledger']['values']['left'][j] for e in selected), 'Per-note/report mismatch')
                    for field, output in [('contact_done', 'contact_done_fraction'), ('clean', 'mean_clean_s')]:
                        expected = mean([e['left_note_ledger']['values'][field][j] for e in selected])
                        actual = note[name][output]
                        require(actual is None if expected is None else actual is not None and math.isclose(actual, expected, abs_tol=1e-10), 'Contact/clean report mismatch')
            fixed[label][checkpoint] = dict(rows=rows, all_first=group(rows, targets),
                safe_first=group([e for e in rows if e['left_curriculum']['full_safe']], targets),
                curriculum_progress=evaluation['curriculum_progress'])
    require(target_sets['old'] == target_sets['new'], 'Song target mapping changed')
    for key in ('ppo', 'initial_std', 'physics_backend', 'song', 'song_training'):
        require(settings['old'][key] == settings['new'][key], 'Expected same setting: '+key)
    for key in ('action', 'task', 'termination', 'native_backend'):
        require(contracts['old'][key] == contracts['new'][key], 'Expected unchanged measurement/control/safety contract: '+key)
    matched = {}
    for checkpoint in ('initial', 'final'):
        ids = [i for i in range(1024) if all(fixed[label][checkpoint]['rows'][i]['left_curriculum']['full_safe'] for label in ('old', 'new'))]
        matched[checkpoint] = dict(count=len(ids), **{label:group([fixed[label][checkpoint]['rows'][i] for i in ids], targets) for label in ('old', 'new')})
    within = {}
    for label in ('old', 'new'):
        ids = [i for i in range(1024) if all(fixed[label][c]['rows'][i]['left_curriculum']['full_safe'] for c in ('initial', 'final'))]
        within[label] = dict(count=len(ids), **{c:group([fixed[label][c]['rows'][i] for i in ids], targets) for c in ('initial', 'final')})
    for values in fixed.values():
        for v in values.values(): v.pop('rows')
    result = dict(schema='guitar_learning.press_control_baseline_comparison.v1', completed=True,
        old_seal_sha256=OLD_SEAL, unchanged_source_sha256=unchanged, collection=collection,
        fixed=fixed, matched_cross_baseline_safe_ids=matched, matched_within_phase_safe_ids=within,
        limitations=['Old and new near/surface_min use wire versus physical press-plane targets: no comparable improvement delta.',
            'Reward adds tracking and changes geometry: do not rank average rewards as equivalent objectives.',
            'Curriculum progress is recorded state; its near gate now uses a different physical target, not an equivalent achievement scale.',
            'Existing contact/clean/success and safety contracts agree; candidate success is not pressure or audible sound.',
            'Same seed/song/prepared pose, correlated IDs, different safe cohorts; matched IDs are descriptive, not randomized causal proof.',
            'PPO collections contain changing stochastic policies; fixed evaluations use deterministic0/100 checkpoints. No absolute-control2000 score8.301 comparison.',
            'Equal-episode motion ranges differ with episode duration, include t0 and sample60Hz; no240Hz extrema claim.'], inputs_sha256=inputs)
    finite(result)
    require(all(sha(Path(name)) == expected for name, expected in inputs.items()), 'Evidence changed during analysis')
    lines = ['# 동일100회 예산 비교', '', '이전 누적 제어와 새 압현면·감속 보상의 실제100회 학습 수집 및 고정0/100 평가다. 근접/거리 목표와 보상은 달라 평균 우열로 비교하지 않는다.', '',
             '| 고정 정책 | 이전 안전/1024 | 새 안전/1024 | 이전 전체 달성/67 | 새 전체 달성/67 | 공통 안전 ID 수 |', '| --- | ---: | ---: | ---: | ---: | ---: |']
    for c in ('initial', 'final'):
        a,b = fixed['old'][c],fixed['new'][c]
        lines.append(f'| {c} | {a["all_first"]["safe"]} | {b["all_first"]["safe"]} | {a["all_first"]["mean_achieved_notes"]:.6f} | {b["all_first"]["mean_achieved_notes"]:.6f} | {matched[c]["count"]} |')
    lines += ['', '안전 전곡·공통 안전ID의 별도 분모, 손가락별 달성 합계/접촉, clean 시간, 물리실패 사유·길이, 단계와 LH21 움직임 원자료 요약은 JSON을 따른다. 같은 안전ID도 독립 seed나 같은 궤적은 아니다.', '',
        '| 학습 수집100회 | 이전 | 새 |', '| --- | ---: | ---: |']
    for title,key in [('종료 곡','episodes'),('안전 완주','safe'),('물리실패','physical_failures'),('종료곡 평균 달성','mean_achieved_notes')]:
        lines.append(f'| {title} | {collection["old"]["all_ended"][key]} | {collection["new"]["all_ended"][key]} |')
    lines += ['', '수집은 각3,276,800전이이며 계속 변하는 확률 정책이다. 반복 곡과 실패 후 재시작을 포함하고 진행 중 곡은 종료 분모에서 제외한다. 고정 정책 결과를 수집 평균으로 대체하지 않는다.', '',
        '옛 활성 경로의 소스가 현재와 다른 것은 예상된 변경이다. 이전 결과는 지정 SHA의 봉인 manifest와 source_training 사본으로 검증했으며 옛 소스는 실행하지 않았다. 새 입력과 동결435소스는 실제 SHA를 검증했다. 제어·scene·기하·PPO·policy·native gain 소스가 동일하다.', '']
    lines += ['- '+x for x in result['limitations']]
    (PHASE/'compare_baseline.json').write_text(json_io.dumps(result, indent=2, allow_nan=False)+'\n')
    (PHASE/'compare_baseline.md').write_text('\n'.join(lines)+'\n')
    print(json_io.dumps(dict(completed=True)))


if __name__ == '__main__':
    main()
