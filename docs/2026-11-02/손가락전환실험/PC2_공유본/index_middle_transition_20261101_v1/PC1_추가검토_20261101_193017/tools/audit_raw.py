"""공유 원시 파일만 읽어 검산한다. 학습 코드·GPU·Torch를 불러오지 않는다."""
from pathlib import Path
import collections
import gzip
import hashlib
import json
import math
import numpy as np

OUT = Path(__file__).resolve().parents[1]
ROOT = OUT.parent
used = {}


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def read(path):
    used[str(path.relative_to(ROOT))] = sha(path)
    return json.loads(path.read_text())


def episodes(folder):
    meta = read(folder / 'episode_metadata.json')['fields']
    path = folder / 'episodes.jsonl'
    used[str(path.relative_to(ROOT))] = sha(path)
    rows = []
    for line in path.read_text().splitlines():
        outer = json.loads(line)
        row = outer['episode']
        for field in meta:
            target = row
            for key in field['path'][:-1]:
                target = target.setdefault(key, {})
            target[field['path'][-1]] = field['value']
        rows.append(row)
    rows.sort(key=lambda e: e['env_id'])
    return rows


def evaluate(folder):
    report = read(folder / 'report.json')
    assert report['completed'] and report['lifecycle_verified']
    assert report['first_episode_per_env_per_batch'] and report['failed_episodes_in_denominator']
    assert not any(report[k] for k in ['failure', 'changed_inputs', 'missing_import_pins', 'cleanup_errors'])
    eps = episodes(folder)
    n = report['episodes']
    assert len(eps) == n and [e['env_id'] for e in eps] == list(range(n))
    identity = [e['finger_control_diagnostics']['episode_id'] for e in eps]
    rows = [e['left_note_ledger']['values'] for e in eps]
    safe = [not (e['termination']['physical_failure'] or e['termination']['wrist_failure']) for e in eps]
    ids = [e['env_id'] for e, v, s in zip(eps, rows, safe) if s and all(v['left'])]
    ckpt = (folder / report['portable_checkpoint_ref']['path']).resolve()
    assert ROOT in ckpt.parents
    ckpt_sha = sha(ckpt)
    assert ckpt_sha == report['checkpoint_sha256']
    used[str(ckpt.relative_to(ROOT))] = ckpt_sha
    sources = collections.defaultdict(lambda: {'env_ids': [], 'sum_seconds': 0.0, 'body_all_causes_frets': []})
    for e in eps:
        w = e['left_note_ledger']['wrong_press_sources']
        for j in range(2):
            for bi, body in enumerate(w['body_names']):
                for ci, cause in enumerate(w['contract']['causes']):
                    duration = w['values']['wrong_source_time'][j][bi][ci]
                    if duration > 0:
                        rec = sources[f'{"AB"[j]}:{body}:{cause}']
                        rec['env_ids'].append(e['env_id'])
                        rec['sum_seconds'] += duration
                        rec['body_all_causes_frets'].append([w['values']['wrong_source_fret_min'][j][bi], w['values']['wrong_source_fret_max'][j][bi]])
    for rec in sources.values():
        rec['mean_seconds_all_envs'] = rec['sum_seconds'] / n
    return dict(n=n, AB=len(ids), AB_ids=ids, front32_AB=sum(i < 32 for i in ids),
                whole_AB=sum(s and all(c >= 1.5 - 1e-8 for c in v['clean']) for s, v in zip(safe, rows)),
                A=sum(bool(v['left'][0]) for v in rows), B=sum(bool(v['left'][1]) for v in rows),
                clean_mean=[sum(v['clean'][j] for v in rows)/n for j in range(2)],
                physical=sum(e['termination']['physical_failure'] for e in eps),
                wrist=sum(e['termination']['wrist_failure'] for e in eps),
                first_episode_ids=identity, checkpoint_sha=ckpt_sha,
                settings_sha=hashlib.sha256(json.dumps(report['settings'],sort_keys=True).encode()).hexdigest(),
                action_mode=read(folder/'action_mode.json'), wrong_sources=dict(sources)), eps


def trace_rows(folder):
    path = folder / 'finger_control_trace.jsonl.gz'
    used[str(path.relative_to(ROOT))] = sha(path)
    with gzip.open(path, 'rt') as stream:
        for line in stream:
            yield json.loads(line)


def geometry(folder, eps):
    counts=collections.Counter()
    values=collections.defaultdict(list)
    ids=[e['finger_control_diagnostics']['episode_id'] for e in eps]
    last_A_gap=None
    for row in trace_rows(folder):
        ex=row['natural_preparation']['transition']
        for i,t in enumerate(ex['all_env_episode_time_s']):
            if ex['all_env_episode_ids'][i] != ids[i] or not (5.25-1e-8 <= t < 6.75-1e-8):
                continue
            counts['B_env_endpoints']+=1
            for key in ['position_geometry','facing_geometry','assigned_loaded','raw_candidate','candidate','wrong']:
                counts[key]+=int(ex['all_env_'+key][i][1])
            counts['effective']+=int(ex['all_env_candidate'][i][1] and not ex['all_env_wrong'][i][1])
            counts['A_raw_in_B']+=int(ex['all_env_raw_candidate'][i][0])
        if row['env_id']!=0 or row['episode_id']!=ids[0]:
            continue
        t=row['episode_time_s']
        if 4.5 <= t < 5.25 and ex['all_env_raw_candidate'][0][0]:
            last_A_gap=t
        if 5.25-1e-8 <= t < 6.75-1e-8:
            f=row['natural_preparation']['fingers'][1]
            for key in ['height_m','lateral_error_m','along_cell_excess_m','normal_cos','standby_rate_per_s']:
                values[key].append(f[key])
            for ji,name in enumerate(row['joint_names']):
                if name.startswith('LH:middle'):
                    values[name+':requested_actual_deg'].append(math.degrees(row['requested_target_rad'][ji]-row['actual_rad'][ji]))
                    values[name+':requested_applied_deg'].append(math.degrees(row['requested_target_rad'][ji]-row['applied_target_rad'][ji]))
    return {'all_env_B_endpoint_counts':dict(counts),'env0_B_stats':{k:{'n':len(v),'mean':float(np.mean(v)),'min':min(v),'max':max(v),'rms':float(np.sqrt(np.mean(np.asarray(v)**2)))} for k,v in values.items()},'env0_last_A_raw_gap_s':last_A_gap}


def first_distance_difference(a,b):
    result=None
    count=0
    for left,right in zip(trace_rows(a),trace_rows(b)):
        count+=1
        ex=left['natural_preparation']['transition']; ey=right['natural_preparation']['transition']
        assert left['episode_time_s']==right['episode_time_s']
        x=np.asarray(ex['all_env_distance_m']);y=np.asarray(ey['all_env_distance_m'])
        delta=np.abs(x-y)
        if result is None and np.max(delta)>1e-9:
            index=np.unravel_index(np.argmax(delta),delta.shape)
            result=dict(time_s=left['episode_time_s'],env_id=int(index[0]),goal_index=int(index[1]),max_difference_m=float(delta[index]),left=float(x[index]),right=float(y[index]),left_episode_id=ex['all_env_episode_ids'][index[0]],right_episode_id=ey['all_env_episode_ids'][index[0]])
    return {'aligned_rows':count,'first_over_1e_9_m':result}


def main():
    assert read(ROOT/'공유상태.json')['ready'] is True
    paths=sorted((ROOT/'진단').glob('base_seed*_u*_mean'))+sorted((ROOT/'진단').glob('base_seed*_u*_sampled'))
    paths += [ROOT/'진단'/x for x in ['final128_seed7_mean','final128_seed17_mean','context_repeat_seed17_mean_128']]
    paths += sorted(p for p in (ROOT/'로그분석/runs').glob('s17_u200_mean_N*') if p.is_dir())
    result={}; eps={}
    for folder in paths:
        result[folder.name],eps[folder.name]=evaluate(folder)
        print('ledger',folder.name,result[folder.name]['AB'],flush=True)
    geom={}
    for name in ['base_seed7_u300_mean','base_seed17_u300_mean']:
        geom[name]=geometry(ROOT/'진단'/name,eps[name])
        print('geometry',name,flush=True)
    first=first_distance_difference(ROOT/'진단/final128_seed17_mean',ROOT/'진단/context_repeat_seed17_mean_128')
    compare_paths=[ROOT/'진단/final128_seed17_mean',ROOT/'진단/context_repeat_seed17_mean_128']+[p for p in paths if p.parent.name=='runs']
    anchor_settings=read(compare_paths[0]/'report.json')['settings']
    anchor_pins={k:v for k,v in read(compare_paths[0]/'inputs_before.json').items() if not k.endswith('/settings.json')}
    identity=[]
    for folder in compare_paths:
        settings=read(folder/'report.json')['settings']
        pins={k:v for k,v in read(folder/'inputs_before.json').items() if not k.endswith('/settings.json')}
        left=dict(anchor_settings);right=dict(settings)
        left.pop('num_envs');right.pop('num_envs')
        identity.append({'name':folder.name,'settings_equal_except_num_envs':left==right,'non_settings_input_pins_equal':pins==anchor_pins,'checkpoint_sha':result[folder.name]['checkpoint_sha'],'num_envs':settings['num_envs']})
    original=read(ROOT/'로그분석/summary.json')['evaluations']
    mismatches=[]
    for name,values in result.items():
        orig=original[name]
        for key in ['n','AB','whole_AB','A','B']:
            if values[key]!=orig[key]:mismatches.append([name,key,values[key],orig[key]])
        for j,key in enumerate(['mean_A_clean_s','mean_B_clean_s']):
            if abs(values['clean_mean'][j]-orig[key])>1e-10:mismatches.append([name,key,values['clean_mean'][j],orig[key]])
    (OUT/'raw_audit.json').write_text(json.dumps({'scope':'CPU JSON/gzip/hash only; no training imports, no checkpoint deserialization, no GPU','evaluations':result,'geometry':geom,'original128_distance_comparison':first,'repeat_identity_comparison':identity,'reported_summary_mismatches':mismatches,'source_sha256':used},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
