"""C1 장기 학습의 확정 로그만 읽어 분모를 나눈다. 학습 설정은 바꾸지 않는다."""
import argparse
import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path
import sys

ROOT = Path(os.environ.get('C1_RUNTIME_ROOT', Path(__file__).resolve().parents[4])).resolve()
sys.path.insert(0, str(ROOT))
import numpy as np
from guitar_learning.training.training_log_io import iter_episode_rows

STUDY = Path(__file__).resolve().parents[1]
SOURCE = ROOT/'data/song_bundles/press_sequence_c1_v1/source/original/C1.fingering.json'
SCORE = 'completion_rate, full_hold_rate, achieved_per_episode, clean_fraction, safe_timeline_rate; tie: later optimizer_updates'


def ranking(row):
    """전체20음 분모의 성과를 우선하고 안전 완주율을 함께 비교한다."""
    return tuple(row[key] for key in ('completion_rate', 'full_hold_rate',
        'achieved_per_episode', 'clean_fraction', 'safe_timeline_rate', 'optimizer_updates'))


def json_rows(path):
    """미완성 마지막 행은 실행 중일 때만 제외하고, 중간 손상은 실패시킨다."""
    with Path(path).open() as stream:
        for line in stream:
            if not line.endswith('\n'):
                break
            yield json.loads(line)


def metric_selection(runs):
    """복구 실행 순서를 따라 같은 전역 업데이트를 한 번만 센다."""
    chosen = {}
    for run in runs:
        for row in json_rows(Path(run)/'learning_metrics.jsonl'):
            chosen[int(row['optimizer_updates'])] = (Path(run), row)
    return chosen


def mean(values):
    values = [float(value) for value in values if value is not None and np.isfinite(value)]
    return float(np.mean(values)) if values else None


def contract_digest(contract):
    from guitar_learning.portability import portable
    return hashlib.sha256(json.dumps(portable(contract), sort_keys=True).encode()).hexdigest()


def episode_notes(episode, schedule):
    """목표 ID로 조인한다. 무노출 surface_min=0을 도달로 오인하지 않는다."""
    ledger = episode['left_note_ledger']
    values = ledger['values']
    indices = {target_id: i for i, target_id in enumerate(ledger['target_ids'])}
    hold = {row['target_id']: row for row in episode['press_coordination']['notes']}
    releases = {row['target_id']: row for row in episode['press_completion']['notes']}
    result = {}
    for target in schedule:
        target_id = target['target_id']
        i = indices[target_id]
        if not ledger['focus_mask'][i]:
            continue
        value = {key: items[i] for key, items in values.items()}
        duration = target['end_s']-target['onset_s']
        exposed = float(value['exposure_time']) > 0
        acquired = float(value['loaded_target_time']) > 0
        release = releases[target_id]
        strict = bool(hold[target_id]['strict_success'])
        if not exposed:
            cause = 'not_exposed'
        elif not acquired:
            cause = 'no_loaded_pad_candidate'
        elif float(value['wrong']) > 0 and not strict:
            cause = 'wrong_with_insufficient_hold'
        elif not strict:
            cause = 'insufficient_continuous_hold'
        elif release['release_status'] not in ('released', 'not_required'):
            cause = 'release_'+release['release_status']
        else:
            cause = 'completed'
        result[target['mapping_note_index']] = dict(
            target_id=target_id, source_note_index=target['mapping_note_index'],
            source_string=target['source_string'], runtime_string=target['string'],
            fret=target['fret'], finger=target['finger'], duration_s=duration,
            exposed=exposed, achieved=bool(value['left']), first_contact=bool(value['contact_done']),
            loaded_candidate=acquired, clean_s=float(value['clean']),
            clean_fraction=min(1., float(value['clean'])/duration),
            best_clean_streak_s=float(value['best_clean_streak']), strict_hold=strict,
            wrong_s=float(value['wrong']), missing_s=float(value['missing']),
            surface_min_m=float(value['surface_min']) if exposed else None,
            release_required=release['release_required'], release_status=release['release_status'],
            release_exercised=acquired, completion=strict and release['release_status'] in ('released', 'not_required'),
            failure_evidence=cause,
            geometry_time_s=float(value['geometry_time']), loaded_target_time_s=float(value['loaded_target_time']),
            facing_time_s=float(value['facing_time']), rejected_target_time_s=float(value['rejected_target_time']),
            own_wrong_fret_time_s=float(value['own_wrong_fret_time']),
            own_wrong_string_time_s=float(value['own_wrong_string_time']),
            other_higher_time_s=float(value['other_higher_time']))
    return result


def section_results(episode, notes, sections):
    """P7은 두 동시 구간까지, P9는 앞 음 해제와 뒤 음 재획득까지 요구한다."""
    groups = episode['press_coordination']['groups']
    safe = bool(episode['press_completion']['safe'])
    result = []
    for section in sections:
        members = [notes.get(i) for i in section['note_indices']]
        covered = all(member is not None and member['exposed'] for member in members)
        ids = {member['target_id'] for member in members if member is not None}
        applicable = [group for group in groups if set(group['target_ids']).issubset(ids)]
        holds = covered and all(member['strict_hold'] for member in members)
        simultaneous = all(group['strict_success'] for group in applicable)
        release = covered and all(member['release_status'] in ('released', 'not_required') for member in members)
        result.append(dict(section=section['case_id'], title=section['title'],
            source_note_indices=section['note_indices'], covered=covered,
            strict_hold=bool(holds), overlap_group_count=len(applicable),
            simultaneous=bool(simultaneous) if applicable else None, release=bool(release),
            completion=bool(safe and holds and simultaneous and release)))
    return result


class Aggregate:
    def __init__(self, schedule, sections):
        self.schedule, self.sections = schedule, sections
        self.count = 0
        self.totals = Counter()
        self.notes = {}
        self.section = defaultdict(Counter)
        self.rewards = defaultdict(lambda: [0., 0])
        self.motion = {}
        self.posture = {}
        self.reasons = Counter()

    def add(self, episode):
        self.count += 1
        completion = episode['press_completion']
        self.reasons[str(episode.get('reason'))] += 1
        for key in ('completion_success', 'full_hold_success'):
            self.totals[key] += bool(completion[key])
        self.totals['safe_timeline'] += bool(completion['safe'] and completion['timeline_complete'])
        self.totals['timeline'] += bool(completion['timeline_complete'])
        self.totals['safe'] += bool(completion['safe'])
        for key in ('physical_failure', 'wrist_failure'):
            self.totals[key] += bool(episode.get('termination', {}).get(key))
        self.totals['achieved'] += episode['song']['left_success_count']
        self.totals['reward'] += float(episode['reward'])
        self.totals['cost'] += float(episode['cost'])
        notes = episode_notes(episode, self.schedule)
        self.totals['selected_opportunities'] += len(notes)
        self.totals['exposed_opportunities'] += sum(note['exposed'] for note in notes.values())
        for index, row in notes.items():
            bucket = self.notes.setdefault(index, dict(opportunities=0, sums=Counter(), counts=Counter(),
                labels={}, failure_evidence=Counter(), release_status=Counter()))
            bucket['opportunities'] += 1
            for key, value in row.items():
                if key in ('failure_evidence', 'release_status'):
                    bucket[key][value] += 1
                elif key in ('target_id', 'source_note_index', 'source_string', 'runtime_string', 'fret', 'finger', 'duration_s'):
                    bucket['labels'][key] = value
                elif value is not None:
                    bucket['sums'][key] += float(value)
                    bucket['counts'][key] += 1
        for row in section_results(episode, notes, self.sections):
            counts = self.section[row['section']]
            counts['episodes'] += 1
            for key in ('covered', 'strict_hold', 'simultaneous', 'release', 'completion'):
                counts[key] += bool(row[key])
            counts['overlap_opportunities'] += row['overlap_group_count'] > 0
        for key, value in episode.get('reward_components', {}).items():
            if isinstance(value, (int, float)):
                self.rewards[key][0] += value
                self.rewards[key][1] += 1
        for key in ('action_mean_abs_change', 'limit_outward_command_fraction',
                    'actual_native_limit_fraction', 'target_native_limit_fraction', 'tracking_error_rms_rad',
                    'actual_min_rad', 'actual_max_rad', 'actual_range_rad', 'target_range_rad', 'action_mean_abs'):
            values = episode.get('left_finger_motion', {}).get('values', {}).get(key)
            if values is not None:
                self._motion(key, values)
        for key, values in episode.get('finger_control_diagnostics', {}).get('values', {}).items():
            self._motion('native_'+key, values)
        diagnostic = episode.get('compact_press_v4', {})
        for key in ('observed_s', 'actual_gate_s', 'quality_integral', 'raw_standby_reward',
                    'target_exposed_s', 'aligned_s', 'candidate_s'):
            if key in diagnostic.get('values', {}):
                self.posture.setdefault(key, np.zeros(4))[:] += diagnostic['values'][key]
        for key in ('phase_valid_s', 'shape_seconds', 'actual_paid_standby'):
            if key in diagnostic:
                values = np.asarray(diagnostic[key])
                if key not in self.posture: self.posture[key] = np.zeros_like(values)
                self.posture[key] += values

    def _motion(self, key, values):
        value = np.asarray(values, dtype=float)
        if key not in self.motion:
            self.motion[key] = [np.zeros_like(value), 0]
        self.motion[key][0] += value
        self.motion[key][1] += 1

    def report(self):
        n = self.count
        notes = []
        for index, row in sorted(self.notes.items()):
            result = dict(row['labels'], opportunities=row['opportunities'],
                failure_evidence=dict(row['failure_evidence']), release_status=dict(row['release_status']))
            result.update({key: value/row['counts'][key] for key, value in row['sums'].items()})
            notes.append(result)
        clean_sum = sum(row['sums']['clean_fraction'] for row in self.notes.values())
        clean_count = sum(row['counts']['clean_fraction'] for row in self.notes.values())
        return dict(episodes=n, reasons=dict(self.reasons),
            safe_timeline_rate=self.totals['safe_timeline']/n if n else None,
            completion_rate=self.totals['completion_success']/n if n else None,
            full_hold_rate=self.totals['full_hold_success']/n if n else None,
            achieved_per_episode=self.totals['achieved']/n if n else None,
            clean_fraction=clean_sum/clean_count if clean_count else None, mean_reward=self.totals['reward']/n if n else None,
            mean_cost=self.totals['cost']/n if n else None,
            physical_failures=self.totals['physical_failure'], wrist_failures=self.totals['wrist_failure'],
            selected_opportunities=self.totals['selected_opportunities'],
            exposed_opportunities=self.totals['exposed_opportunities'], notes=notes,
            sections=[dict(section=key, **counts) for key, counts in sorted(self.section.items())],
            reward_components={key: value/count for key, (value, count) in self.rewards.items()},
            posture_diagnostic_sums={key: value.tolist() for key, value in self.posture.items()},
            joint_diagnostics={key: (value/count).tolist() for key, (value, count) in self.motion.items()})


def evaluation(path, sections):
    report = json.loads((path/'report.json').read_text())
    if report.get('scope') != 'full_song':
        raise ValueError('고정 평가 full_song 필요: '+str(path))
    if (report.get('completed') is not True or report.get('failure') or report.get('changed_inputs') or
            report.get('missing_import_pins') or not report.get('lifecycle_verified')):
        raise ValueError('미완료/입력 불일치 평가: '+str(path))
    schedule = report['training_contract']['task']['provenance']['song']['schedule']
    if len(schedule) != 20:
        raise ValueError('C1 20목표 계약 필요')
    agg = Aggregate(schedule, sections)
    for row in iter_episode_rows(path):
        if row['episode']['finger_skill']['scope'] != 'full_song':
            raise ValueError('전곡 평가에 구간 episode 혼입')
        if len(row['episode']['left_note_ledger']['selected_target_ids']) != 20:
            raise ValueError('전곡 평가의 선택 목표는20개여야 합니다')
        agg.add(row['episode'])
    result = agg.report()
    if not result['episodes'] or result['episodes'] != report['summary']['count']:
        raise ValueError('평가 report/episode 분모 불일치')
    result.update(path=str(path.resolve()), checkpoint=str(report['checkpoint']),
        checkpoint_sha256=report['checkpoint_sha256'], num_envs=report['settings']['num_envs'],
        contract_sha256=contract_digest(report['training_contract']),
        seed=report['settings']['seed'],
        profile=report['settings']['compact_press']['improvement_profile'])
    return result


def checkpoint_std(path, expected_sha=None):
    """출처·입력·정책 identity·명세 SHA를 모두 확인한 저장 std만 반환한다."""
    from guitar_learning.tool.experiments.compact_press_v5 import read_checkpoint
    from guitar_learning.tool.experiments.press_sequence import checked_target, verify_checkpoint_clock
    import torch
    path = Path(path)
    entries = [row for row in json_rows(path.parent/'checkpoint_manifest.jsonl') if row['path'] == path.name]
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if not entries or entries[-1]['sha256'] != digest or (expected_sha and digest != expected_sha):
        raise ValueError('checkpoint manifest SHA 불일치: '+str(path))
    read_checkpoint(path)
    verify_checkpoint_clock(path, checked_target('C1'))
    payload = torch.load(path, map_location='cpu', weights_only=False)
    values = payload['model']['log_std'].clamp(-5, 2).exp().numpy()
    if values.shape != (33,) or not np.isfinite(values).all():
        raise ValueError('33축 Gaussian std 필요')
    return dict(path=str(path.resolve()), sha256=digest, optimizer_updates=int(payload['updates']),
        contract_sha256=contract_digest(payload['identity']['architecture']['contract']),
        latent_std33=values.tolist(), support17_mean=float(values[:17].mean()),
        finger16_mean=float(values[17:].mean()), scope='pre-tanh latent Gaussian; action delta degrees 아님')


def write_csv(path, rows):
    if not rows:
        return
    keys = list(dict.fromkeys(key for row in rows for key in row))
    with path.open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=keys)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value
                for key, value in row.items()})


def discover(study):
    manifest = study/'analysis_inputs.json'
    if manifest.exists():
        value = json.loads(manifest.read_text())
        return ([study/Path(p) for p in value['training_runs']],
                [study/Path(p) for p in value['evaluation_runs']])
    exclude = ('처리량', 'pilot', 'dry', '테스트')
    train = sorted(path.parent for path in study.rglob('learning_metrics.jsonl')
        if not any(word in str(path.relative_to(study)) for word in exclude))
    evaluations = []
    for path in sorted(study.rglob('report.json')):
        if any(word in str(path.relative_to(study)) for word in exclude):
            continue
        value = json.loads(path.read_text())
        if value.get('scope') == 'full_song' and 'checkpoint' in value:
            evaluations.append(path.parent)
    return train, evaluations


def plots(out, rows, evaluations, stds):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    if rows:
        fig, axes = plt.subplots(4, 1, figsize=(11, 12), sharex=True)
        x = [row['optimizer_updates'] for row in rows]
        keys = sorted({key for row in rows for key in row if key.startswith('reward:')})
        for key in keys:
            axes[0].plot(x, [row.get(key, np.nan) for row in rows], label=key[7:], alpha=.75)
        axes[0].legend(fontsize=7, ncol=2); axes[0].set_ylabel('reward / physical transition')
        axes[1].plot(x, [row['actor_lr'] for row in rows], label='actor_lr'); axes[1].legend()
        axes[2].plot(x, [row['analytic_kl'] for row in rows], label='KL')
        axes[2].plot(x, [row.get('clip_fraction', np.nan) for row in rows], label='clip fraction')
        axes[2].legend()
        axes[3].plot(x, [row['mean_cost'] for row in rows], label='decision mean cost')
        axes[3].legend(); axes[3].set_xlabel('optimizer updates')
        fig.tight_layout()
        for ext in ('png', 'svg'): fig.savefig(out/('learning.'+ext))
        plt.close(fig)
    if evaluations:
        fig, ax = plt.subplots(figsize=(12, max(2, len(evaluations)*.65)))
        data = [[note['clean_fraction'] for note in row['notes']] for row in evaluations]
        image = ax.imshow(data, vmin=0, vmax=1, aspect='auto')
        ax.set_xticks(range(20)); ax.set_xticklabels(range(1,21)); ax.set_xlabel('source note (1-based)')
        ax.set_yticks(range(len(evaluations))); ax.set_yticklabels([str(row['optimizer_updates']) for row in evaluations])
        ax.set_ylabel('checkpoint update'); fig.colorbar(image, ax=ax, label='audible clean fraction')
        fig.tight_layout()
        for ext in ('png', 'svg'): fig.savefig(out/('notes.'+ext))
        plt.close(fig)
    if stds:
        ordered = sorted(stds, key=lambda row: row['optimizer_updates'])
        fig, ax = plt.subplots(figsize=(9, 4))
        for key in ('support17_mean', 'finger16_mean'):
            ax.plot([row['optimizer_updates'] for row in ordered], [row[key] for row in ordered], 'o-', label=key)
        ax.set_xlabel('checkpoint optimizer updates'); ax.set_ylabel('latent Gaussian std'); ax.legend()
        fig.tight_layout()
        for ext in ('png', 'svg'): fig.savefig(out/('std.'+ext))
        plt.close(fig)


def analyze(study=STUDY, output=None):
    study = Path(study).resolve(); out = Path(output) if output else study/'분석'
    out.mkdir(parents=True, exist_ok=True)
    sections = json.loads(SOURCE.read_text())['metadata']['sections']
    train, eval_paths = discover(study)
    chosen = metric_selection(train)
    rows, scopes, windows = [], {}, {}
    last_update = max(chosen, default=0)
    window_width = min(200, max(10, len(chosen)//4))
    for update, (run, row) in sorted(chosen.items()):
        values = dict(optimizer_updates=update, run=str(run), transitions=row['transitions'],
            mean_cost=row['mean_cost'], actor_lr=row['actor_lr'], analytic_kl=row['analytic_kl'],
            max_attempted_kl=row['max_attempted_kl'], kl_retries=row['kl_retries'],
            clip_fraction=row.get('diagnostics', {}).get('post_update', {}).get('clip_fraction'),
            entropy=row.get('diagnostics', {}).get('post_update', {}).get('latent_gaussian_entropy', {}).get('mean'),
            **{'reward:'+key: value for key, value in row['reward_component_means'].items()})
        rows.append(values)
    base_contract = None
    for run in train:
        contract = json.loads((run/'training_contract.json').read_text())
        digest = contract_digest(contract)
        if base_contract is not None and digest != base_contract:
            raise ValueError('서로 다른 환경 계약의 학습을 합산할 수 없습니다')
        base_contract = digest
        schedule = contract['task']['provenance']['song']['schedule']
        accepted = {row['update_index']: number for number, (source, row) in chosen.items() if source == run}
        for row in iter_episode_rows(run):
            if row['update_index'] not in accepted:
                continue
            episode = row['episode']; scope = episode['finger_skill']['scope']
            if scope not in scopes: scopes[scope] = Aggregate(schedule, sections)
            scopes[scope].add(episode)
            # 구간 훈련에서 전곡으로 바뀐 효과를 마지막 추세로 오인하지 않는다.
            if scope == 'full_song':
                update = accepted[row['update_index']]
                bucket = 'last' if update is not None and update > last_update-window_width else (
                    'previous' if update is not None and update > last_update-2*window_width else None)
                if bucket:
                    if bucket not in windows: windows[bucket] = Aggregate(schedule, sections)
                    windows[bucket].add(episode)
    stds, evaluations, warnings = {}, [], []
    for path in eval_paths:
        result = evaluation(path, sections)
        checkpoint = Path(result['checkpoint'])
        if not checkpoint.is_absolute(): checkpoint = ROOT/checkpoint
        std = checkpoint_std(checkpoint, result['checkpoint_sha256'])
        if result['contract_sha256'] != std['contract_sha256']:
            raise ValueError('평가와 checkpoint의 환경 계약 불일치')
        if base_contract is not None and base_contract != result['contract_sha256']:
            raise ValueError('학습과 고정 평가의 환경 계약 불일치')
        stds[str(checkpoint)] = std
        result['optimizer_updates'] = std['optimizer_updates']
        result['checkpoint'] = str(checkpoint.resolve()); evaluations.append(result)
    evaluations.sort(key=lambda row: row['optimizer_updates'])
    if len({(row['num_envs'], row['profile'], row['seed']) for row in evaluations}) > 1:
        raise ValueError('고정 평가 환경 수/프로필/seed가 다릅니다')
    selected = max(evaluations, key=ranking) if evaluations else None
    if not evaluations: warnings.append('완료된 고정 전곡 평가가 없어 모델을 선정하지 않았습니다.')
    if not (study/'analysis_inputs.json').exists():
        warnings.append('자동 경로 발견 사용: 복구 순서는 analysis_inputs.json 명시 순서가 우선입니다.')
    trend = None
    if len(rows) >= 40:
        half = max(10, min(100, len(rows)//4)); before, after = rows[-2*half:-half], rows[-half:]
        trend = {key: dict(before=mean(row[key] for row in before), after=mean(row[key] for row in after))
                 for key in ('mean_cost','actor_lr','analytic_kl')}
    summary = dict(schema='press_v5_c1_analysis.v1', study=str(study),
        training_runs=[str(p) for p in train], evaluation_runs=[str(p) for p in eval_paths],
        training=dict(unique_updates=len(rows), physical_transitions=sum(row['transitions'] for row in rows),
            scopes={key: value.report() for key, value in scopes.items()}, last_window=trend),
        evaluations=evaluations, std_snapshots=list(stds.values()), selection_score=SCORE,
        selected_checkpoint=selected['checkpoint'] if selected else None, warnings=warnings,
        extra1000_recommendation='자동 연장하지 않음. 고정 평가 향상과 마지막 전곡 노출 추세를 함께 검토해야 함.')
    write_csv(out/'learning.csv', rows)
    write_csv(out/'notes.csv', [dict(update=e['optimizer_updates'], **note) for e in evaluations for note in e['notes']])
    write_csv(out/'sections.csv', [dict(update=e['optimizer_updates'], **s) for e in evaluations for s in e['sections']])
    summary['training']['last_full_song_windows'] = {key: value.report() for key, value in windows.items()}
    if set(windows) == {'last', 'previous'}:
        before, after = windows['previous'].report(), windows['last'].report()
        growing = after['achieved_per_episode'] > before['achieved_per_episode']+.05 or after['clean_fraction'] > before['clean_fraction']+.01
        summary['extra1000_recommendation'] = (
            '마지막 전곡 학습 창에서 증가 신호가 있습니다. 고정 평가도 개선되었는지 검토 후 동일 조건 추가1000회를 고려합니다.'
            if growing else '마지막 전곡 학습 창에서 뚜렷한 증가 기준(+0.05음 또는 clean+0.01)을 넘지 않았습니다. 추가1000회를 자동 권고하지 않습니다.')
    plots(out, rows, evaluations, list(stds.values()))
    (out/'분석.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    lines = ['# C1 장기 학습 결과', '', '학습과 고정 전곡 평가를 분리했습니다. 이전 단기 검증은 합산하지 않습니다.', '',
        f'중복 제거 후 {len(rows)}업데이트, {summary["training"]["physical_transitions"]:,} 물리 전이입니다.',
        '', '|모델 업데이트|완결 평가 episode|안전 전곡|물리실패|손목종료|전체20음 압현·해제 완성|전체20음 유지|평균 달성/20|clean 비율|',
        '|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for e in evaluations:
        lines.append('|%d|%d|%.3f|%d|%d|%.3f|%.3f|%.3f|%.3f|' % (e['optimizer_updates'],e['episodes'],
            e['safe_timeline_rate'],e['physical_failures'],e['wrist_failures'],e['completion_rate'],
            e['full_hold_rate'],e['achieved_per_episode'],e['clean_fraction']))
    lines += ['', '선정 기준: '+SCORE, '', '평가한%d개 중 선정 모델: '%len(evaluations)+str(summary['selected_checkpoint']), '',
        '## 해석과 한계', '',
        '- 20음 표와 P1~P9 표는 같은 전곡 평가 안에서의 수행입니다. 각 과제만 별도 초기화한 독립 실험은 아닙니다.',
        '- 학습의 구간/전곡 분모는 scopes로 분리했습니다. 노출되지 않은 목표는 실패 원인을 not_exposed로 기록합니다.',
        '- 달성은 configured hold 기준(현재 corrected 40%)입니다. 전체20음 유지와 압현·해제 완성은 개별 음의 성공 비율이 아니라 전체 task의 bool을 episode 수로 나눈 값이며, 안전 완주·모든 음의 연속 유지·모든 동시 구간을 요구합니다.',
        '- 해제는 하중이 있는 목표 패드 후보 소실입니다. 실제 줄 압력·소리·완전 분리는 측정하지 않습니다. 한 번도 후보가 없었던 음의 missed 해제는 해제를 시도한 증거가 아닙니다.',
        '- geometry·facing·loaded 및 wrong 원인 시간은 겹칠 수 있으므로 합산해 원인 비율로 쓰지 않습니다.',
        '- 탐색은 SHA·입력·identity 검증을 통과한 체크포인트의 pre-tanh Gaussian std입니다. 설정 초기값 또는 entropy로 대체하지 않습니다.',
        '- 관절 한계 비율은 실제 native limit의 1e-6 근방이며 자연스러운 자세 판정이 아닙니다. 위치제어 submitted effort=0은 모터 힘이 없다는 뜻이 아닙니다.',
        '- 상세 trace는 env0 최초 10초만 저장하므로 후반 P7/P9의 순간 원인은 완결 ledger 이상으로 확정하지 않습니다.',
        '- 접근 보상은 potential 차이이므로 음수 평균만으로 탐색 실패를 단정할 수 없습니다. 보상 항은 물리 전이 평균, mean_reward는 decision 합의 평균으로 분모가 다릅니다.',
        '', '추가1000회: '+summary['extra1000_recommendation'], '', '확인되지 않은 가설: 실패 원인 분류는 누적 후보/오압현/유지의 증거 우선순위이며 물리 인과관계를 증명하지 않습니다.']
    if selected:
        lines += ['', '## 선정 모델의 과제별 수행', '', '|과제|노출/평가|완성/평가|연속 유지|필요 해제|', '|---|---:|---:|---:|---:|']
        for section in selected['sections']:
            lines.append('|%s|%d/%d|%d/%d|%d|%d|' % (section['section'], section['covered'],
                section['episodes'], section['completion'], section['episodes'], section['strict_hold'], section['release']))
        lines += ['', '음별 원시 기하 진단과 실패 증거 분류는 notes.csv, 관절21축 진단 및 탐색33축은 분석.json에 있습니다.']
    lines += ['\n주의: '+warning for warning in warnings]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study', type=Path, default=STUDY)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    result = analyze(args.study, args.out)
    print(json.dumps(dict(selected_checkpoint=result['selected_checkpoint'],
        unique_updates=result['training']['unique_updates']), ensure_ascii=False))
