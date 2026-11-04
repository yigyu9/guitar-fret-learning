"""Read only committed B/P records; GPU work belongs to the native supervisor."""
import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import sys

TOTAL = 16777216
BATCH = 32768
POINTS = (0, 4194304, 8388608, 12582912, TOTAL)
PROFILES = {'B': 'corrected', 'P': 'preparation'}


def read(path):
    return json.loads(Path(path).read_text())


def json_rows(path):
    """A live final partial line is not a committed record; interior damage fails."""
    if not Path(path).exists():
        return
    with Path(path).open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break
            yield json.loads(line)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def metric_selection(runs, committed_prefix):
    """Recovery order supersedes earlier rows only inside the restored prefix."""
    chosen = {}
    for run in runs:
        key = str(Path(run).resolve())
        if key not in committed_prefix:
            raise ValueError('committed_prefix missing: ' + key)
        limit = int(committed_prefix[key])
        for row in json_rows(Path(run)/'learning_metrics.jsonl'):
            update = int(row['optimizer_updates'])
            if update <= limit:
                chosen[update] = (Path(run), row)
    updates = sorted(chosen)
    if updates and updates != list(range(1, updates[-1]+1)):
        raise ValueError('committed updates contain a gap')
    for update, (_, row) in chosen.items():
        if (int(row['transitions']) != BATCH or
                int(row['curriculum']['committed_transitions']) != update*BATCH):
            raise ValueError('global update/committed transition mismatch')
    return chosen


def section_for(note, sections, pre_roll):
    """Use the original source onset and end; runtime IDs are not section labels."""
    onset = note['onset_s']-pre_roll
    matches = [s['case_id'] for s in sections
               if s['first_note']-1e-8 <= onset <= s['last_note']+1e-8
               and note['end_s'] <= s['end']+pre_roll+1e-8]
    if len(matches) != 1:
        raise ValueError('note does not map uniquely to source section')
    return matches[0]


def episode_notes(episode, schedule, sections, pre_roll):
    ledger = episode['left_note_ledger']
    ids = ledger['target_ids']
    selected = set(ledger['selected_target_ids'])
    expected = {n['target_id'] for n in schedule}
    if len(ids) != 20 or len(set(ids)) != 20 or set(ids) != expected or selected != expected:
        raise ValueError('full-song evaluation requires all 20 scheduled targets')
    held = {n['target_id']: n for n in episode['press_coordination']['notes']}
    releases = {n['target_id']: n for n in episode['press_completion']['notes']}
    if set(held) != expected or set(releases) != expected:
        raise ValueError('hold/release target identity mismatch')
    source_end = float(episode['finger_skill']['source_task_time_s'])
    result = []
    for target in schedule:
        tid = target['target_id']; i = ids.index(tid)
        value = {key: values[i] for key, values in ledger['values'].items()}
        note, release = held[tid], releases[tid]
        for key in ('onset_s', 'end_s'):
            if abs(note[key]-target[key]) > 1e-8:
                raise ValueError('ledger/source clock mismatch')
        ended = source_end+1e-9 >= note['end_s']
        strict = bool(note['strict_success'])
        streak_ok = note['best_clean_streak_s']+1e-9 >= note['duration_s']
        if strict != streak_ok:
            raise ValueError('strict hold disagrees with full continuous duration')
        released = release['release_status'] in ('released', 'not_required')
        if (not release['release_required']) != (release['release_status'] == 'not_required'):
            raise ValueError('release requirement/status mismatch')
        result.append(dict(env_id=episode['env_id'], target_id=tid,
            section=section_for(note, sections, pre_roll),
            preparation_goal_observation_exposed=None,
            surface_window_exposed=float(value['exposure_time']) > 0,
            audible_started=source_end > note['onset_s']+1e-12,
            audible_ended=ended, strict_hold=strict,
            release_required=release['release_required'], release_status=release['release_status'],
            hold_release=bool(strict and ended and released),
            safe_hold_release=bool(strict and ended and released and episode['press_completion']['safe']),
            legacy_40pct=bool(value['left']), first_contact=bool(value['contact_done']),
            loaded_candidate=float(value['loaded_target_time']) > 0,
            first_candidate_s=None, first_clean_s=None, early_release=None,
            clean_s=float(value['clean']), wrong_s=float(value['wrong']), missing_s=float(value['missing']),
            best_clean_streak_s=float(note['best_clean_streak_s']),
            surface_min_m=float(value['surface_min']) if value['exposure_time'] > 0 else None))
    return result


def aggregate(episodes, schedule, sections, pre_roll):
    rows = []
    boundaries = sorted({n[k] for n in schedule for k in ('onset_s', 'end_s')})
    expected_groups = []
    for start, end in zip(boundaries, boundaries[1:]):
        active = tuple(n['target_id'] for n in schedule if n['onset_s'] <= start and n['end_s'] >= end)
        if len(active) >= 2 and end > start:
            expected_groups.append((active, start, end))
    for episode in episodes:
        if episode['finger_skill']['scope'] != 'full_song':
            raise ValueError('phrase episode in fixed full-song evaluation')
        groups = episode['press_coordination']['groups']
        observed_groups = [(tuple(g['target_ids']), g['start_s'], g['end_s']) for g in groups]
        if observed_groups != expected_groups:
            raise ValueError('coordination groups differ from source overlap schedule')
        for group in groups:
            valid = (group['observed_s']+1e-9 >= group['duration_s'] and
                     group['longest_clean_s']+1e-9 >= group['duration_s'])
            if bool(group['strict_success']) != valid:
                raise ValueError('coordination strict hold duration mismatch')
            labels = {section_for(n, sections, pre_roll) for n in schedule if n['target_id'] in group['target_ids']}
            if len(labels) != 1:
                raise ValueError('coordination group spans source sections')
        rows.extend(episode_notes(episode, schedule, sections, pre_roll))
    n = len(episodes)
    if n != 32 or {e['env_id'] for e in episodes} != set(range(32)):
        raise ValueError('exactly 32 first episodes, one per env, required')
    failure = sum(bool(e['termination']['physical_failure'] or e['termination']['wrist_failure']) for e in episodes)
    result = dict(episodes=n, note_denominator=20*n,
        hold_release_notes=sum(r['hold_release'] for r in rows),
        strict_hold_notes=sum(r['strict_hold'] for r in rows),
        safe_hold_release_notes=sum(r['safe_hold_release'] for r in rows),
        legacy_40pct_notes=sum(r['legacy_40pct'] for r in rows),
        contact_notes=sum(r['first_contact'] for r in rows),
        candidate_notes=sum(r['loaded_candidate'] for r in rows),
        surface_window_exposed_notes=sum(r['surface_window_exposed'] for r in rows),
        audible_started_notes=sum(r['audible_started'] for r in rows),
        audible_ended_notes=sum(r['audible_ended'] for r in rows),
        unstarted_notes=sum(not r['audible_started'] for r in rows),
        exposed_failed_notes=sum(r['audible_started'] and not r['hold_release'] for r in rows),
        failure_episodes=failure, failure_rate=failure/n,
        physical_failure_episodes=sum(bool(e['termination']['physical_failure']) for e in episodes),
        wrist_failure_episodes=sum(bool(e['termination']['wrist_failure']) for e in episodes),
        episode_completion=sum(bool(e['press_completion']['completion_success']) for e in episodes),
        clean_s=sum(r['clean_s'] for r in rows), wrong_s=sum(r['wrong_s'] for r in rows),
        missing_s=sum(r['missing_s'] for r in rows))
    result['hold_release_rate'] = result['hold_release_notes']/result['note_denominator']
    result['exposed_hold_release_rate'] = (result['hold_release_notes']/result['audible_started_notes']
        if result['audible_started_notes'] else None)
    section_rows = []
    for section in sections:
        sid = section['case_id']; sr = [r for r in rows if r['section'] == sid]
        if len(sr) != len(section['note_indices'])*n:
            raise ValueError('source section denominator mismatch')
        completed = 0
        for episode in episodes:
            er = [r for r in sr if r['env_id'] == episode['env_id']]
            tids = {r['target_id'] for r in er}
            groups = [g for g in episode['press_coordination']['groups'] if set(g['target_ids']) <= tids]
            completed += all(r['hold_release'] for r in er) and all(g['strict_success'] for g in groups)
        section_rows.append(dict(section=sid, episodes=n, section_completed=completed,
            note_denominator=len(sr), hold_release_notes=sum(r['hold_release'] for r in sr),
            clean_s=sum(r['clean_s'] for r in sr), wrong_s=sum(r['wrong_s'] for r in sr)))
    result['section_denominator'] = len(sections)*n
    result['section_completed'] = sum(r['section_completed'] for r in section_rows)
    result['section_completion_rate'] = result['section_completed']/result['section_denominator']
    return result, rows, section_rows


def load_runtime(runtime):
    runtime = Path(runtime).resolve()
    for key in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[key] = '1'
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(runtime))
    import torch
    torch.set_num_threads(1)
    from guitar_learning.training import training_log_io
    from guitar_learning.tool.experiments import compact_press_v5, press_sequence
    from guitar_learning.portability import portable
    for module in (training_log_io, compact_press_v5, press_sequence):
        if runtime not in Path(module.__file__).resolve().parents:
            raise ValueError('refusing an imported runtime outside analysis_inputs runtime')
    return torch, training_log_io.iter_episode_rows, compact_press_v5.read_checkpoint, press_sequence, portable


def checkpoint_info(path, expected_sha, api):
    torch, _, strict_reader, clock, portable = api
    path = Path(path).resolve()
    entries = [r for r in json_rows(path.parent/'checkpoint_manifest.jsonl') if r['path'] == path.name]
    digest = sha(path)
    if not entries or entries[-1]['sha256'] != digest or digest != expected_sha:
        raise ValueError('evaluation/checkpoint manifest SHA mismatch')
    settings = strict_reader(path)
    clock.verify_checkpoint_clock(path, clock.checked_target('C1'))
    payload = torch.load(path, map_location='cpu', weights_only=False)
    if int(entries[-1]['optimizer_updates']) != int(payload['updates']):
        raise ValueError('manifest/checkpoint optimizer update mismatch')
    values = payload['model']['log_std'].clamp(-5, 2).exp().tolist()
    if len(values) != 33 or not all(math.isfinite(v) for v in values):
        raise ValueError('finite 33-axis latent std required')
    contract = portable(payload['identity']['architecture']['contract'])
    initial_digest = None
    if int(payload['updates']) == 0:
        h = hashlib.sha256()
        for key, tensor in sorted(payload['model'].items()):
            h.update(key.encode()); h.update(tensor.detach().cpu().contiguous().numpy().tobytes())
        initial_digest = h.hexdigest()
    return dict(checkpoint=str(path), checkpoint_sha256=digest,
        optimizer_updates=int(payload['updates']), transitions=int(payload['updates'])*BATCH,
        latent_std33=values, support17_mean=sum(values[:17])/17,
        finger16_mean=sum(values[17:])/16, initial_tensor_sha256=initial_digest,
        strict_reader_passed=True), settings, contract


def validate_evaluation(report, info, settings, contract, portable, condition):
    if (report.get('completed') is not True or report.get('failure') or report.get('changed_inputs')
            or report.get('missing_import_pins') or report.get('cleanup_errors')
            or report.get('lifecycle_verified') is not True):
        raise ValueError('evaluation not complete/source-verified/scene-closed')
    if (report.get('scope') != 'full_song' or report.get('episodes') != 32
            or report.get('settings', {}).get('num_envs') != 32
            or report.get('first_episode_per_env_per_batch') is not True
            or report.get('failed_episodes_in_denominator') is not True):
        raise ValueError('fixed 32-env full-song denominator contract required')
    if report['checkpoint_sha256'] != info['checkpoint_sha256']:
        raise ValueError('evaluation used a different model')
    if portable(report['training_contract']) != contract:
        raise ValueError('evaluation contract differs from its own checkpoint')
    if (settings['compact_press']['improvement_profile'] != PROFILES[condition]
            or report['settings']['compact_press']['improvement_profile'] != PROFILES[condition]
            or report['settings']['simple_start']['initial_pose'] != 'left_standby_v9'):
        raise ValueError('profile/original initial pose mismatch')
    if info['transitions'] not in POINTS:
        raise ValueError('evaluation outside prescribed transition boundary')


def validate_evaluation_inputs(path, runtime):
    from guitar_learning.portability import localize
    from guitar_learning.native import paths
    if runtime not in Path(paths.__file__).resolve().parents:
        raise ValueError('input verifier is outside the selected runtime')
    pins = localize(read(path/'inputs_before.json'))
    if not pins:
        raise ValueError('evaluation input pins are empty')
    # Official verifier resolves registered historical (path, SHA) versions to
    # preserved bytes; resolving a historical label directly changes its meaning.
    if not paths.verify(pins):
        raise ValueError('evaluation input pins differ from preserved/live bytes')


def write_csv(path, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(k for row in rows for k in row))
    with Path(path).open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys); writer.writeheader()
        writer.writerows({k: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
                         for k, v in row.items()} for row in rows)


def diagnostic_row(condition, run, row, elapsed):
    post = row.get('diagnostics', {}).get('post_update', {})
    critics = post.get('critics', {})
    result = dict(condition=condition, run=str(run), optimizer_updates=row['optimizer_updates'],
        transitions=row['curriculum']['committed_transitions'], collect_opt_elapsed_s=elapsed,
        actor_lr=row.get('actor_lr'), analytic_kl=row.get('analytic_kl'),
        max_attempted_kl=row.get('max_attempted_kl'), kl_retries=row.get('kl_retries'),
        clip_fraction=post.get('clip_fraction'),
        reward_EV=critics.get('reward', {}).get('explained_variance'),
        cost_EV=critics.get('cost', {}).get('explained_variance'),
        reward_value_loss=row.get('reward_value_loss'), cost_value_loss=row.get('cost_value_loss'),
        latent_entropy=post.get('latent_gaussian_entropy', {}).get('mean'))
    result.update({'reward:'+k: v for k, v in row.get('reward_component_means', {}).items()})
    return result


def plots(out, comparisons, learning):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    for xkey, xlabel, tag in [('transitions', 'Committed transitions', '전이'),
                             ('training_wall_elapsed_s', 'Measured training process seconds', '시간')]:
        fig, axes = plt.subplots(1, 2, figsize=(11, 4))
        for condition in PROFILES:
            rr = [r for r in comparisons if r['condition'] == condition and r.get(xkey) is not None]
            for ax, key in zip(axes, ('hold_release_rate', 'failure_rate')):
                ax.plot([r[xkey] for r in rr], [r[key] for r in rr], 'o-', label=condition)
                ax.set_xlabel(xlabel); ax.set_ylabel(key); ax.set_ylim(-.01, 1.01); ax.grid(alpha=.2)
        for ax in axes: ax.legend()
        fig.tight_layout(); fig.savefig(out/(tag+'_비교.png'), dpi=150); plt.close(fig)
    if learning:
        keys = ['actor_lr', 'analytic_kl', 'clip_fraction', 'reward_EV', 'cost_EV', 'latent_entropy']
        keys += sorted({k for r in learning for k in r if k.startswith('reward:')})
        fig, axes = plt.subplots(math.ceil(len(keys)/3), 3, figsize=(13, math.ceil(len(keys)/3)*2.6))
        for ax, key in zip(axes.flat, keys):
            for condition in PROFILES:
                rr = [r for r in learning if r['condition'] == condition]
                ax.plot([r['transitions'] for r in rr],
                        [r.get(key) if r.get(key) is not None else float('nan') for r in rr], label=condition)
            ax.set_title(key); ax.grid(alpha=.2); ax.legend(fontsize=7)
        for ax in list(axes.flat)[len(keys):]: ax.set_visible(False)
        fig.tight_layout(); fig.savefig(out/'학습진단.png', dpi=130); plt.close(fig)


def analyze(study=None):
    study = Path(study or Path(__file__).resolve().parents[1]).resolve()
    inputs = read(study/'analysis_inputs.json')
    runtime = Path(inputs['runtime']).resolve()
    api = load_runtime(runtime)
    _, episode_reader, _, _, portable = api
    sections = read(runtime/'data/song_bundles/press_sequence_c1_v1/mapping/fingering.json')['metadata']['sections']
    if [s['case_id'] for s in sections] != ['P'+str(i) for i in range(1, 10)]:
        raise ValueError('original C1 P1-P9 metadata required')
    comparisons, notes, section_rows, learning, stds = [], [], [], [], []
    training, initial_hashes, selections = {}, {}, {}
    for condition in PROFILES:
        runs = [(study/Path(p)).resolve() for p in inputs['training_runs'].get(condition, [])]
        chosen = metric_selection(runs, inputs['committed_prefix'])
        elapsed = 0.; elapsed_by_update = {0: 0.}; wall_by_update = {0: 0.}
        training_episodes = 0
        for update, (run, row) in sorted(chosen.items()):
            elapsed += row['collection_s']+row['update_s']; elapsed_by_update[update] = elapsed
            learning.append(diagnostic_row(condition, run, row, elapsed))
        previous_wall = 0.; native_completed = False
        for run in runs:
            accepted = {r['update_index'] for source, r in chosen.values() if source == run}
            training_episodes += sum(r['update_index'] in accepted for r in episode_reader(run))
            limit = int(inputs['committed_prefix'][str(run)])
            boundaries = {int(r['update_index']): r['elapsed_s'] for r in json_rows(run/'events.jsonl')
                          if r.get('event') == 'phase' and r.get('phase') == 'collecting'}
            for u, seconds in boundaries.items():
                if u <= limit and (u == 0 or chosen.get(u, (None,))[0] == run):
                    wall_by_update[u] = previous_wall+seconds
            report_path = run/'report.json'
            report = read(report_path) if report_path.exists() else {}
            # A completed final has no subsequent collecting event.
            if report.get('completed') and report.get('lifecycle_verified') and not report.get('failure'):
                last = max((u for u, (source, _) in chosen.items() if source == run), default=0)
                if last == limit and report.get('optimizer_updates') == limit:
                    wall_by_update[last] = previous_wall+report['wall_s']
                native_completed = (report.get('optimizer_updates') == TOTAL//BATCH
                    and not report.get('changed_inputs') and not report.get('missing_import_pins')
                    and not report.get('cleanup_errors'))
            previous_wall = wall_by_update.get(limit, previous_wall)
        training[condition] = dict(unique_committed_updates=len(chosen), committed_transitions=len(chosen)*BATCH,
            collect_opt_elapsed_s=elapsed, committed_episode_rows=training_episodes,
            native_final_completed=native_completed, runs=[str(p) for p in runs])
        for value in inputs['evaluation_runs'].get(condition, []):
            path = (study/Path(value)).resolve(); report = read(path/'report.json')
            checkpoint = Path(report['checkpoint'])
            if not checkpoint.is_absolute(): checkpoint = runtime/checkpoint
            info, settings, contract = checkpoint_info(checkpoint, report['checkpoint_sha256'], api)
            validate_evaluation(report, info, settings, contract, portable, condition)
            validate_evaluation_inputs(path, runtime)
            if info['optimizer_updates'] > len(chosen):
                raise ValueError('evaluation beyond committed training prefix')
            schedule = contract['task']['provenance']['song']['schedule']
            if len(schedule) != 20: raise ValueError('C1 source schedule requires 20 notes')
            episodes = [r['episode'] for r in episode_reader(path)]
            result, nr, sr = aggregate(episodes, schedule, sections, settings['song']['pre_roll_s'])
            if report['summary']['count'] != result['episodes']:
                raise ValueError('report/episode denominator mismatch')
            label = dict(condition=condition, transitions=info['transitions'])
            result.update(label, checkpoint=info['checkpoint'], checkpoint_sha256=info['checkpoint_sha256'],
                collect_opt_elapsed_s=elapsed_by_update[info['optimizer_updates']],
                training_wall_elapsed_s=wall_by_update.get(info['optimizer_updates']),
                evaluation_wall_s=report['wall_s'])
            comparisons.append(result); notes.extend(dict(label, **r) for r in nr)
            section_rows.extend(dict(label, **r) for r in sr); stds.append(dict(info, condition=condition))
            if info['transitions'] == 0: initial_hashes[condition] = info['initial_tensor_sha256']
        rr = [r for r in comparisons if r['condition'] == condition]
        if len({r['transitions'] for r in rr}) != len(rr):
            raise ValueError('duplicate evaluation transition boundary')
        if rr:
            final = max(rr, key=lambda r: r['transitions'])
            selections[condition] = dict(checkpoint=final['checkpoint'], sha256=final['checkpoint_sha256'],
                transitions=final['transitions'], selection_reason='prescribed final checkpoint' if final['transitions'] == TOTAL
                else 'latest strictly verified checkpoint; partial run, not a final model',
                evaluation_used_for_selection=False, independent_test=False)
    if len(initial_hashes) == 2 and len(set(initial_hashes.values())) != 1:
        raise ValueError('B/P fresh initial tensor digests differ')
    comparisons.sort(key=lambda r: (r['condition'], r['transitions']))
    common = sorted(set(r['transitions'] for r in comparisons if r['condition'] == 'B') &
                    set(r['transitions'] for r in comparisons if r['condition'] == 'P'))
    pairs = []
    for t in common:
        b, p = [next(r for r in comparisons if r['condition'] == c and r['transitions'] == t) for c in PROFILES]
        pairs.append(dict(transitions=t, success_diff_pp=100*(p['hold_release_rate']-b['hold_release_rate']),
                          failure_diff_pp=100*(p['failure_rate']-b['failure_rate']),
                          wrong_diff_s=p['wrong_s']-b['wrong_s'], clean_diff_s=p['clean_s']-b['clean_s']))
    full = bool(common == list(POINTS) and len(initial_hashes) == 2 and
        all(training[c]['committed_transitions'] == TOTAL and training[c]['native_final_completed'] for c in PROFILES))
    screen = (pairs[-1]['success_diff_pp'] >= 5-1e-9 and pairs[-1]['failure_diff_pp'] <= 2+1e-9) if full else None
    unavailable = ['per-note preparation observation exposure', 'first candidate timestamp',
                   'first clean timestamp', 'early release timestamp/rate']
    summary = dict(schema='pc1_preparation_analysis.v1', status=inputs.get('status'),
        complete_comparison=full, training=training, comparison=comparisons, common_transition_pairs=pairs,
        initial_model_tensor_sha256=initial_hashes, selections=selections,
        final_screen_passed=screen, unavailable=unavailable,
        limitations='One training seed7; 32 parallel evaluation environments are not independent training seeds. '
                    'Same C1 evaluation is not an independent test. Surface diagnostics are not preparation observation exposure. '
                    'Full continuous hold AND required release is separate from legacy40% and acoustic success.')
    out = study/'분석'; out.mkdir(exist_ok=True)
    video_report = out/'영상검증.json'
    videos = read(video_report) if video_report.exists() else {}
    verified_videos = []
    if videos.get('completed'):
        for video in videos.get('videos', []):
            file = Path(video['file']).resolve()
            selection = selections.get(video['condition'])
            if (study/'동영상' != file.parent or not selection or sha(file) != video['sha256']
                    or video['checkpoint_sha256'] != selection['sha256']):
                raise ValueError('representative video/model SHA mismatch')
            verified_videos.append(video)
    summary['representative_videos'] = verified_videos
    for name, value in [('요약.json', summary), ('선정모델.json', selections)]:
        (out/name).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    for name, values in [('비교표.csv', comparisons), ('구간별비교.csv', section_rows), ('음별원장.csv', notes),
                         ('학습지표.csv', learning), ('탐색표준편차.csv', stds), ('동일전이차이.csv', pairs)]:
        write_csv(out/name, values)
    plots(out, comparisons, learning)
    report_lines = ['# PC1 준비 접근 비교', '', '완전한 동일예산 비교: '+str(full),
                    '최종 seed7 선별 기준 통과: '+str(screen)+' (성공 +5pp 이상, 실패 증가 +2pp 이하)', '',
                    '|전이|P−B 유지+해제 pp|P−B 실패 pp|P−B clean 초|P−B 오압현 초|',
                    '|---:|---:|---:|---:|---:|']
    report_lines += ['|{transitions}|{success_diff_pp:.3f}|{failure_diff_pp:.3f}|{clean_diff_s:.3f}|{wrong_diff_s:.3f}|'.format(**p) for p in pairs]
    report_lines += ['', '전체20음×32episode 분모에 조기 종료·미도달 음을 포함했다. 실제 발음 창 시작/끝 도달 및 surface 노출 분모는 별도다.',
        'P1~P9는 원래 source clock으로 매핑하고 동시압현 그룹의 strict 유지와 필요한 해제를 함께 요구했다.',
        '학습진단에는 로그의 보상 항목·LR·KL·clip·보상/비용 EV·가치 손실·엔트로피를 기록했다. std는 manifest SHA와 공식 strict reader 및 clock 검증 뒤 checkpoint에서 읽었다.',
        '시간 그래프는 native events의 elapsed_s와 완료 report.wall_s를 사용하며 없는 경계 시각은 생략했다. collect+opt 시간은 별도 열이다.',
        '첫 후보/clean의 정확한 시각과 조기 해제, 목표 관측 노출은 원장에 없으므로 추정하지 않았다. 누적 candidate/contact/clean을 대체 시각으로 해석하지 않는다.',
        '총보상은 보상 정의가 다른 B/P 순위로 사용하지 않았다. 최종 모델을 기본 선정하고 미완료는 마지막 검증 저장본으로 명시했다.',
        '', '한 학습 seed7의 선별 결과이며32환경은32독립 학습seed가 아니다. 같은 C1 평가로 얻은 결과는 독립 테스트 성과가 아니다.',
        '다음 단독 실험: 동일 설정의 추가 학습 seed에서 B/P 재현을 먼저 확인한다.']
    if pairs:
        latest = pairs[-1]
        report_lines += ['', '가장 큰 공통 평가 예산은 '+str(latest['transitions'])+'전이다. '
            + ('완전한 두 조건의 seed7 선별 기준 '+('통과' if screen else '미통과')+'다.' if full
               else '현재는 부분 비교이며 완전한 B/P 비교 결론은 보류한다.')]
    report_lines += ['', '## 선정 모델', '', '|조건|전이|모델 SHA256|저장본|', '|---|---:|---|---|']
    for condition, item in selections.items():
        report_lines.append('|'+condition+'|'+str(item['transitions'])+'|'+item['sha256']+'|['
            +Path(item['checkpoint']).name+']('+item['checkpoint']+')|')
    report_lines += ['', '## 실제 탐색 std', '', 'pre-tanh latent Gaussian std이며 action 각도 표준편차가 아니다.', '',
        '|조건|전이|support17 평균|finger16 평균|', '|---|---:|---:|---:|']
    for item in sorted(stds, key=lambda r: (r['condition'], r['transitions'])):
        report_lines.append('|{condition}|{transitions}|{support17_mean:.6f}|{finger16_mean:.6f}|'.format(**item))
    report_lines += ['', '## 대표 영상', '']
    if verified_videos:
        report_lines.extend('- '+v['condition']+' ['+Path(v['file']).name+']('+v['file']+') · 모델 SHA '+v['checkpoint_sha256']
                            for v in verified_videos)
    else:
        report_lines.append('검증 완료된 대표 영상은 아직 없다.')
    (out/'REPORT.md').write_text('\n'.join(report_lines)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path)
    print(json.dumps(analyze(parser.parse_args().study), ensure_ascii=False, allow_nan=False))
