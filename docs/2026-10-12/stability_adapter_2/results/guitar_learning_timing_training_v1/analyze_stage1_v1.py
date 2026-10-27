"""Read-only stage1 preflight/training analysis; never starts physics.

Uses the sealed stage0 v5 readers and numerical checks. Stage1 training starts
fresh PPO counters; migration source24 is not stage1 update24.
"""
import argparse
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path
import re

PHASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('stage0_analysis_v5', PHASE/'analyze_stage0_v5.py')
A = importlib.util.module_from_spec(spec)
spec.loader.exec_module(A)


def compare(current, previous):
    return dict(
        first_target_down_abs_error_s=None if current['first_target_down_abs_error_s'] is None else
            current['first_target_down_abs_error_s']-previous['first_target_down_abs_error_s'],
        audible_hold_fraction=current['audible_hold_fraction']-previous['audible_hold_fraction'],
        unnecessary_crossings=current['unnecessary_crossings']-previous['unnecessary_crossings'],
        target_direction_crossings=current['target_direction_crossings']-previous['target_direction_crossings'],
        guitar_displacement_max_m=current['safety240']['guitar_displacement_max_m']-previous['safety240']['guitar_displacement_max_m'],
        cost=current['cost']-previous['cost'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--name', required=True)
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args()
    if args.preflight and args.final:
        raise ValueError('preflight is actor migration evidence, not completed stage1 PPO')
    if not re.fullmatch(r'[a-z0-9_]+', args.name):
        raise ValueError('simple new artifact basename required')
    output, markdown, png = [PHASE/(args.name+suffix) for suffix in ('.json', '.md', '.png')]
    if any(path.exists() for path in (output, markdown, png)):
        raise FileExistsError('preserve previous analysis; choose a new name')
    baseline = A.read_json(A.BASELINE)
    stage0 = A.read_json(PHASE/'stage0_final_analysis_v1.json')
    preflight = None if args.preflight else A.read_json(PHASE/'stage1_preflight_analysis_v1.json')
    roles = {}
    for role in ('left', 'right'):
        folder = PHASE/(role+('_stage1_preflight_eval_v1' if args.preflight else '_stage1_final_eval_v1'))
        ev = A.native_evaluation(folder, baseline['roles'][role]['bc_eval_v1'], role)
        train = None if args.preflight else A.training(PHASE/(role+'_stage1_v1'), role)
        reset_checks = []
        initialization = None
        if ev and ev['completed']:
            for episode in ev['episodes']:
                reset = A.read_json(folder/('reset_%02d.json'%episode['episode']))
                cfg = reset['timing']['config']
                reset_checks.append(dict(stage1=cfg['stage_index']==1,
                    window_half_second=reset['timing']['window_s']==.5,
                    pre_roll_one_second=cfg['pre_roll_s']==1.,
                    horizon_five_seconds=reset['training_contract']['task']['specialist']['config']['horizon_s']==5.))
                episode['descriptive_change_vs_same_index_stage0_final'] = compare(
                    episode, stage0['roles'][role]['native_evaluation']['episodes'][episode['episode']])
                if preflight is not None:
                    episode['descriptive_change_vs_same_index_stage1_preflight'] = compare(
                        episode, preflight['roles'][role]['native_evaluation']['episodes'][episode['episode']])
            if (folder/'timing_initialization.json').is_file():
                initial = A.read_json(folder/'timing_initialization.json')
                initialization = {key:initial.get(key) for key in (
                    'schema','kind','role','path','sha256','source_updates','copied_keys',
                    'critic_copied','optimizer_copied','updates_copied')}
        roles[role] = dict(training=train, native_evaluation=ev, migration=initialization,
            reset_checks=reset_checks, stage0_final=stage0['roles'][role]['native_evaluation'],
            initial_BC=baseline['roles'][role]['bc_eval_v1'],
            stage1_preflight=None if preflight is None else preflight['roles'][role]['native_evaluation'])
    checks = {}
    for role, record in roles.items():
        ev = record['native_evaluation']; train = record['training']
        valid = bool(ev and ev['completed'])
        es = ev['episodes'] if valid else []
        checks[role] = dict(
            two_evaluations=valid and len(es)==2,
            safe_stage_success=valid and all(e['stage_success'] and e['reason']=='timeline_complete' and
                not e['safety240']['failure_reasons'] and all(e['checks'].values()) for e in es),
            source_unchanged=valid and ev['source_unchanged'],
            stage1_contract=bool(record['reset_checks']) and all(all(c.values()) for c in record['reset_checks']),
            actual_task_quality=valid and (all(e['audible_hold_fraction']>=.95 for e in es) if role=='left' else
                all(e['first_target_down_abs_error_s'] is not None and e['first_target_down_abs_error_s']<=.5 for e in es)))
        if args.preflight:
            checks[role]['source_counter_matches_stage0_final'] = valid and ev['checkpoint_metadata']['updates']==stage0['roles'][role]['native_evaluation']['checkpoint_metadata']['updates']
        else:
            checks[role].update(completed_training=train['report_completed'],
                closed_gzip=train['transition_stream']['gzip_complete'],
                training_integrity=all(train['checks'].values()),
                training_source_unchanged=bool(train['report'] and not train['report']['changed_inputs']),
                final_counter_matches=bool(valid and ev['checkpoint_metadata']['updates']==train['committed_updates']==train['settings']['updates']))
    ready = all(all(value.values()) for value in checks.values())
    if args.final and not ready:
        raise RuntimeError('final stage1 analysis requires completed matching-counter training and safe native evaluations')
    A.read_bytes(Path(__file__))
    A.read_bytes(PHASE/'analyze_stage0_v5.py')
    analysis = dict(schema='guitar_learning.stage1_training_analysis.v1',
        created_utc=datetime.now(timezone.utc).isoformat(),
        mode='actor_migration_preflight' if args.preflight else 'trained_policy_evaluation',
        final_requested=args.final, validation_passed=ready, checks=checks, roles=roles,
        scope='Stage1 only; no automatic stage2 promotion. Original joint music stays separate.',
        input_snapshots=A.INPUTS,
        limitations=['Two repeated fixed-start episodes do not establish generalization.',
            'Stage0 source update24 is separate from new stage1 PPO counter.',
            'Stage1 preflight vs stage1 final is the direct PPO comparison; stage0 to preflight includes changed stage observation.',
            'Window0.5 changes both observable criteria and reward support; raw rewards are not comparable across stages.',
            'LH audible coverage and RH first target/down error are compared independently of window success.',
            'Chest and triple contact are diagnostic, not required continuous support.',
            'Training safety endpoints are60Hz; native safety checks all1200physics samples.'])
    A.write_new(output, analysis)
    lines = ['# Stage1 '+('Actor 이전 사전평가' if args.preflight else '학습·실제 평가 분석'), '',
        '검증 조건 충족: **%s**. stage1 범위의 판단이며 다음 단계 승격을 뜻하지 않는다.'%ready, '',
        'stage0의24회 학습 source와 새 stage1의 학습 횟수를 구분한다. 시간창은 ±0.5초이며 정책 pre-roll1초·전체5초·native 정착2초는 유지한다.', '',
        '| 손 | 회차 | 단계 성공 | audible 유지율 | 최초 down 절대오차(ms) | 추가 목표 down | 반대 up | 기타 최대 이동(mm) |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for role, record in roles.items():
        ev = record['native_evaluation']
        if not ev or not ev['completed']:
            lines += ['', role+': native 평가 자료 미완료.']; continue
        for e in ev['episodes']:
            first = e['first_target_down_abs_error_s']
            lines.append('| %s | %d | %s | %.6f | %s | %d | %d | %.6f |'%(role,e['episode']+1,e['stage_success'],
                e['audible_hold_fraction'],None if first is None else '%.6f'%(first*1000),
                max(0,e['target_direction_crossings']-1),e['up_crossings'],e['safety240']['guitar_displacement_max_m']*1000))
        changes = [e['descriptive_change_vs_same_index_stage0_final'] for e in ev['episodes']]
        delta = A.mean([c['first_target_down_abs_error_s'] for c in changes])
        lines += ['', '%s: stage0 최종 대비 audible 유지율 평균 변화 %.6f, 최초 down 절대오차 평균 변화 %s ms. 동일 시작 조건의 기술적 비교다.'%(role,
            A.mean([c['audible_hold_fraction'] for c in changes]),None if delta is None else '%.6f'%(delta*1000))]
        if record['training']:
            direct=[e['descriptive_change_vs_same_index_stage1_preflight'] for e in ev['episodes']]
            delta=A.mean([c['first_target_down_abs_error_s'] for c in direct])
            lines += ['', '%s: 같은 stage1 계약의 이전 사전평가 대비 audible 유지율 평균 변화 %.6f, 최초 down 절대오차 평균 변화 %s ms. 이 비교를 stage1 PPO 변화의 근거로 사용한다.'%(role,
                A.mean([c['audible_hold_fraction'] for c in direct]),None if delta is None else '%.6f'%(delta*1000))]
            s=record['training']['training_summary']
            fractions=[e['hold_reward_outside_audible_fraction'] for e in record['training']['episodes']
                if e['committed'] and e['hold_reward_outside_audible_fraction'] is not None]
            lines += ['', '%s 학습: %d updates / %d전이, timing 성공%d/%d, 물리실패%d. 실제 LR %s~%s, KL retry%d.'%(role,
                record['training']['committed_updates'],record['training']['committed_transitions'],s['successes'],s['committed_episodes'],
                s['physical_failures'],s['actual_actor_lr']['minimum'],s['actual_actor_lr']['maximum'],s['retries_total'])]
            if role=='left' and fractions:
                lines += ['', '왼손 hold 보상 중 audible 밖 성분 비율 평균 %.3f%%. 시간창 변경으로 보상 적분 구간이 바뀌므로 stage0 총보상과 직접 비교하지 않는다.'%(A.mean(fractions)*100)]
    lines += ['', '240Hz 비용 적분·시계·실제 crossing 깊이/속도·inactive 행동0·원 joint music·입력 SHA는 JSON에 보존했다.',
        '', '[전체 수치와 SHA](%s)'%output]
    if not args.preflight:
        A.plots(png, roles)
        lines += ['', '![KL·실제 LR·critic](%s)'%png]
    A.write_new(markdown, '\n'.join(lines)+'\n')
    print(json.dumps(dict(output=str(output), validation_passed=ready, checks=checks)))


if __name__=='__main__':
    main()
