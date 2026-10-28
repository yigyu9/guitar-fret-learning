"""CPU-only audit of the one original-note pinky grid; wait for root completion."""
import argparse
import csv
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true')
    if not parser.parse_args().root_completed:
        print('준비만 완료: root 실제 종료 통보 전에는 원자료/결과를 읽지 않습니다.')
        return
    probe = load('pinky_grid_analysis_probe', BASE/'probe.py')
    grid = probe.grid
    sys.path.insert(0, str(grid.ROOT))
    out = HERE/'results_v1'; probe.cap.reject_existing(out)
    inputs, verified = {}, {}

    def track(path):
        path = Path(path); inputs[str(path)] = grid.sha(path)
        return path

    def read(path):
        return grid.read(track(path))

    def pins(values):
        for path, digest in values.items():
            if path not in verified: verified[path] = grid.sha(path)
            assert verified[path] == digest, path

    for path in probe.actual_gate(): track(path)
    seal = read(BASE/'preparation_seal.json')
    assert seal['independent_review'] == 'passed_no_findings' and seal['valid_count'] == 72
    pins(seal['input_pins'])
    review = read(BASE/'review.json')
    assert review['verdict'] == 'PASS' and not review['findings']
    pins(review['reviewed_sha256'])
    assert grid.sha(BASE/'review.json') == seal['review_sha256']
    prior_review = read(probe.REVIEW); pins(prior_review['reviewed_sha256'])
    prior_verification = read(probe.REVIEW.parent/'verification.json')
    for key in ('input_sha256', 'verified_input_sha256'): pins(prior_verification[key])
    launcher = read(BASE/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode'] == 0
    assert len(launcher['children']) == 1 and launcher['children'][0]['finger'] == 'pinky'
    assert launcher['children'][0]['returncode'] == 0
    # CPU imports occur only after the explicit actual-completion guard and strict gates.
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    torch.set_num_threads(1)
    original = load('pinky_original_row_analysis', grid.HERE/'analysis/analyze.py')
    helper = load('pinky_prelearning_trace_analysis', probe.PRELEARNING/'analysis/analyze.py')
    track(Path(original.__file__)); track(Path(helper.__file__))
    metadata, _ = fixture(1)
    folder = BASE/'runs/pinky'
    document = read(BASE/'cpu_inputs/pinky_grid.json')
    config = read(folder/'settings.json')
    with probe.pinky_inputs(): expected = grid.settings('pinky', 72)
    assert config == expected == read(BASE/'cpu_inputs/pinky_settings.json')
    reference = read(document['reference_path'])
    assert grid.sha(document['reference_path']) == document['reference_sha256']
    rebuilt = grid.grid(reference['selected_targets_rad'], document['joint_names'], document['native_lower_rad'], document['native_upper_rad'])
    assert all(document[key] == value for key, value in rebuilt.items())
    assert document['valid_count'] == 72 and len(document['rows']) == 225
    assert document['executed_detail_grid_indices'] == [22,109,112,113,115,130]
    short = config['song']['short_learning']
    report, scene = read(folder/'report.json'), read(folder/'gpu_scene_final.json')
    lifecycle = read(folder/'pinky_grid_lifecycle.json')
    assert report['completed'] and report['closed'] and report['failure'] is None and report['close_failure'] is None
    assert not report['changed_inputs'] and not report['unpinned_project_sources']
    assert report['grid_rows'] == 225 and report['assigned_valid_attempts'] == 72 and report['no_NN_or_checkpoint']
    assert lifecycle['scene_valid'] and lifecycle['input_and_pool_scopes_restored'] and not lifecycle['cleanup_errors']
    assert lifecycle['declared_valid_count'] == scene['environment_count'] == scene['hand_collision_native_readback_environments'] == 72
    assert scene['closed'] and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode'] == 'fixed'
    assert scene['hand_collision']['enabled_distinct_finger_pairs'] == 90
    assert report['resources']['physics_steps'] == scene['physics_steps'] == 4*report['resources']['control_ticks']
    assert report['resources']['control_ticks'] <= short['view']['duration_ticks'] and not list(folder.glob('*.pt'))
    before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json'); pins(before)
    assert after['verified'] and before == after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    native = read(folder/'native_effort_readback.json')
    old_native = read(probe.PRELEARNING/'runs/pinky_reference/native_effort_readback.json')
    assert native['environment_count'] == 72 and native['expected_readback_exact']
    for key in ('actual_native_PD105', 'changed_native_field_indices', 'native_indices', 'source_sha256'):
        assert native[key] == old_native[key]
    assert len(native['native_indices']) == 16 and native['changed_native_field_indices']['effort'] == native['native_indices']
    assert all(not ids for field, ids in native['changed_native_field_indices'].items() if field != 'effort')
    assert len(native['actual_native_PD105']['effort']) == 105
    assert all(native['actual_native_PD105']['effort'][i] == .25 for i in native['native_indices'])
    contract = read(folder/'training_contract.json'); assert contract['native_backend']['diagnostic_native_effort'] == native
    old_contract = read(probe.PRELEARNING/'runs/pinky_reference/training_contract.json')
    for value in (contract, old_contract): value['native_backend'].pop('diagnostic_native_effort')
    assert contract == old_contract
    evaluation = read(folder/'evaluation.json'); assert evaluation['policy_performance'] is False
    selection = original.audit_rows(document, evaluation)
    assert selection == read(folder/'selection.json')
    episodes = evaluation['episodes']; assert evaluation['summary'] == summary(episodes)
    bygrid = {e['grid_index']: e for e in episodes}
    eligible = [e['grid_index'] for e in episodes if e['achieved'] and e['clean_fraction'] >= .7 and e['audible_wrong_fraction'] <= .1
        and not e['termination']['physical_failure'] and not e['termination']['wrist_failure']]
    ranked = sorted(eligible, key=lambda i: (sum(x*x for x in document['rows'][i]['offset_deg']), max(abs(x) for x in document['rows'][i]['offset_deg']), i))
    assert selection['eligible_grid_indices'] == ranked and selection['selected_grid_index'] == (ranked[0] if ranked else None)
    statistics = read(folder/'statistics.json'); stats = {r['grid_index']: r for r in statistics['rows']}
    assert len(statistics['rows']) == len(stats) == 72 and set(stats) == set(bygrid)
    assert statistics['gate_order'] == ['loaded','position','position_facing','positive','candidate','wrong']
    assert statistics['phase_order'] == ['before','audible','after']
    assert statistics['phase_scope'] == 'source_time<source_onset; source_onset<=source_time<source_end; source_time>=source_end'
    table = []
    for row in document['rows']:
        i = row['grid_index']; episode = bygrid.get(i); stat = stats.get(i)
        if episode:
            assert stat['env_id'] == row['env_id'] == episode['env_id'] and len(episode['reward_components']) == 9
            assert sum(p['samples'] for p in stat['phases'].values()) == episode['steps']
            for phase in stat['phases'].values():
                assert len(phase['gate_counts']) == 6 and all(0 <= n <= phase['samples'] for n in phase['gate_counts'])
                if phase['samples']:
                    assert all(len(phase[k]) == 20 and np.isfinite(phase[k]).all() for k in ('mean','min','max','rms'))
        table.append(dict(**row, baseline=i == 112, selected=i == selection['selected_grid_index'], eligible=i in ranked,
            rank=ranked.index(i)+1 if i in ranked else None, episode=episode, statistics=stat))
    meta = read(folder/'trace_metadata.json')
    assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
    assert meta['grid_indices'] == document['executed_detail_grid_indices']
    assert sorted(p.name for p in folder.glob('trace_grid*.npz')) == ['trace_grid%06d.npz'%i for i in sorted(meta['grid_indices'])]
    details = {}; metric_ids = list(range(15))+[18,19]
    source = short['view']['source_target']
    for i in meta['grid_indices']:
        with np.load(track(folder/('trace_grid%06d.npz'%i))) as saved: trace = dict(saved)
        local_episode = dict(bygrid[i], env_id=0)  # Helper single-snapshot row only; real ledger/env_id is unchanged.
        detail = helper.trace_audit(trace, metadata, config, [local_episode], 'reference', contract['action']['target_contract'])
        detail['actual_env_id'] = bygrid[i]['env_id']; residuals = []; gate_mismatch = []
        if 'unavailable_reason' not in detail:
            masks = grid.phase_masks(trace['source_time_s'], source['onset_s'], source['end_s'])
            for phase, mask in zip(('before','audible','after'), masks):
                raw, calculated = stats[i]['phases'][phase], detail['phases'][phase]
                assert raw['samples'] == calculated['samples']
                if raw['gate_counts'] != calculated['CPU_gate_counts']: gate_mismatch.append(dict(phase=phase, native=raw['gate_counts'], CPU=calculated['CPU_gate_counts']))
                if not raw['samples']: continue
                for key in ('mean','max'):
                    a, b = np.asarray(calculated['metric_'+key]), np.asarray(raw[key])[metric_ids]
                    np.testing.assert_allclose(a, b, rtol=5e-6, atol=5e-5)
                    residuals.append(float(abs(a-b).max()))
                for field, column in (('surface_distance_m',15),('surface_height_m',16)):
                    values = trace[field][mask]*1000
                    for key, value in (('mean',values.mean()),('min',values.min()),('max',values.max()),('rms',np.sqrt((values**2).mean()))):
                        np.testing.assert_allclose(value,raw[key][column],rtol=5e-6,atol=5e-5)
        detail.update(native_phase_gate_mismatches=gate_mismatch, max_checked_statistic_abs_residual=max(residuals,default=None),
            statistic_tolerance=dict(rtol=5e-6,atol=5e-5), omitted_statistic='native nearest normalcos endpoint not saved; no tie/sample proof')
        details[str(i)] = detail
    old_case = read(probe.REVIEW.parent/'comparison.json')['cases']['pinky_reference']
    assert old_case['reused'] is False and len(old_case['episodes']) == 4
    focus = {str(i): table[i] for i in dict.fromkeys([112,*ranked[:1]])}
    groups = {}
    for label, rows in (('all72',episodes),('eligible',[e for e in episodes if e['grid_index'] in ranked]),('ineligible',[e for e in episodes if e['grid_index'] not in ranked])):
        exposed = [stats[e['grid_index']]['phases']['audible']['mean'] for e in rows if stats[e['grid_index']]['phases']['audible']['samples']]
        groups[label] = dict(attempts=len(rows),audible_exposed_attempts=len(exposed),
            metric_scope='equal-weight per-attempt audible mean distribution, not pooled240Hz samples',
            mean_metric_p50=np.median(exposed,axis=0).tolist() if exposed else None,
            mean_metric_p95=np.percentile(exposed,95,axis=0).tolist() if exposed else None,
            mean_metric_max=np.max(exposed,axis=0).tolist() if exposed else None)
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__)); track(HERE/'PLAN.md')
    result = dict(declared=225, valid_first_attempts=72, excluded=153, episodes=episodes, summary=evaluation['summary'], selection=selection,
        metric_order=statistics['metric_order'], gate_order=statistics['gate_order'], audible_groups=groups,focus=focus,detailed_traces=details,
        previous_reference4=dict(source=old_case['source'], episodes=old_case['episodes'], summary=old_case['summary'], env0_trace=old_case['env0_trace'],
            scope='기존4환경 별도 실행; 새72batch baseline112와 동일 실행/bitexact 가정 없음'))
    out.mkdir()
    grid.write(out/'comparison.json',result)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        total_declared_rows=225,total_valid_first_attempts=72,excluded_rows=153,detailed_rows=meta['grid_indices'],all_scenes_closed=True,
        candidate_wrong_mismatches=sum(len(d.get('candidate_wrong_mismatches',[])) for d in details.values()),
        native_phase_gate_mismatches=sum(len(d['native_phase_gate_mismatches']) for d in details.values()),
        scope='전체72음원장/저장60Hz통계; 상세6행CPU기하. 미저장nativeqd/sample/normalcos 및 다른행시계열 추정 없음'))
    with (out/'attempts.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(table[0]));writer.writeheader()
        writer.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in table)
    lines=['# 낮은 상한 소지 유한 목표 탐색','', '225개 선언 중 유효72개 첫 시도와 제외153개를 모두 보존했다. 같은seed7의72환경이며 실패도 성과 분모에 포함한다. 원 eligible 조건과 perturbation 순위를 변경하지 않았다.','',
        '| 달성/72 | eligible/72 | 평균 clean/wrong | 물리/손목실패 | 선정 grid |','|---:|---:|---:|---:|---:|',
        '| %d/72 | %d/72 | %.6f/%.6f | %d/%d | %s |'%(sum(e['achieved'] for e in episodes),len(ranked),evaluation['summary']['mean_clean_fraction'],evaluation['summary']['mean_audible_wrong_fraction'],sum(e['termination']['physical_failure'] for e in episodes),sum(e['termination']['wrist_failure'] for e in episodes),selection['selected_grid_index']), '',
        '| 초점 | env | 음중 표본 | actual4 ° | target4 ° | 세 마디 평균/최대 N | 손목 mm/° | native6gate |','|---|---:|---:|---|---|---|---|---|']
    fmt=lambda xs:', '.join('%.4f'%x for x in xs)
    for i,row in focus.items():
        p=row['statistics']['phases']['audible'];m=p['mean']
        lines.append('| %s | %s | %d | %s | %s | %s / %s | %s | %s |'%(i,row['env_id'],p['samples'],fmt(m[:4]) if m else '미노출',fmt(m[4:8]) if m else '미노출',fmt(m[12:15]) if m else '미노출',fmt(p['max'][12:15]) if m else '미노출',fmt(m[18:20]) if m else '미노출',p['gate_counts']))
    lines += ['', '| 전체/원 eligible 분리 | 원 분모/음중 노출 | 시도별 평균 순힘 p50/p95/max N (세 마디) | 시도별 평균 손목오차 p50/p95/max mm |','|---|---:|---|---|']
    for label,g in groups.items():
        v=[g['mean_metric_'+part] for part in ('p50','p95','max')]
        lines.append('| %s | %d/%d | %s | %s |'%(label,g['attempts'],g['audible_exposed_attempts'],' / '.join(fmt(a[12:15]) for a in v) if v[0] else '미노출',' / '.join('%.4f'%a[18] for a in v) if v[0] else '미노출'))
    lines += ['', 'baseline112는 이72환경 batch 안의 새 시도이며 기존4환경 reference와 출처를 분리했다. 기존 reference4의 원장/상세env0은 comparison.json에 별도로 담았다.', '',
        '상세6행은 원 기하 helper로 CPU 재생했다. nearest tie/미저장 sample·normalcos 한계, 거리/높이 잔차와 gate 불일치는 comparison.json에 보존했다. 60Hz 상세 관찰을240Hz 하중 극값으로 확대하지 않으며 실제240Hz음원장/9보상을 재지급하지 않는다. 원자료가 없는66행의 시계열이나 random env3 고정 목표는 추정하지 않았다.', '',
        '선정 후보1개에 대한 fresh4시도 검증이 필요하다.' if ranked else '원 조건을 만족하는 후보가 없어 grid/cap 확장을 멈추고 손목/제약을 분리하는 진단을 검토한다.', '',
        '105 native 속성·16축 effort0.25Nm만 변경·원90 collision pairs·장면종료·입력불변·실제launcher종료0을 확인했다. 비교 계약은 검수된 기존 소지 reference에서 cap 진단 선언을 제거한 파생값이며 새20Nm 실행이 아니다. 몸체 순힘은 특정 접촉쌍·현 압력·모터 토크가 아니며 cap이 몸체힘 상한을 보장하지 않는다. no-NN scripted/fixed-guitar 진단을 정책학습·자유기타 성과나 MCP coupling 원인 확정으로 확대하지 않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(dict(completed=True,attempts=72,eligible=len(ranked),selected=selection['selected_grid_index'])))


if __name__ == '__main__': main()
