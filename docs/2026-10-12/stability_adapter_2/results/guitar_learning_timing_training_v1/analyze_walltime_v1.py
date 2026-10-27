"""Aggregate immutable update timing fields, without running any experiment."""
import hashlib
import json
from pathlib import Path
from statistics import mean, median

PHASE=Path(__file__).resolve().parent
INPUTS={}


def read(path):
    data=path.read_bytes()
    INPUTS[str(path)]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    return json.loads(data)


def main():
    output=PHASE/'collection_update_walltime_v1.json'
    markdown=PHASE/'collection_update_walltime_v1.md'
    if output.exists() or markdown.exists():
        raise FileExistsError('preserve previous analysis')
    runs={}
    for stage,required in ((0,24),(1,12)):
        for role in ('left','right'):
            name='%s_stage%d_v1'%(role,stage)
            folder=PHASE/name
            updates=[read(p) for p in sorted(folder.glob('update_*.json'))]
            report=read(folder/'report.json')
            assert report['completed'] and not report['failure'] and len(updates)==required
            assert [u['update_index'] for u in updates]==list(range(required))
            assert all(u['collection_s']>=0 and u['update_s']>=0 for u in updates)
            collection=sum(u['collection_s'] for u in updates)
            update=sum(u['update_s'] for u in updates)
            runs[name]=dict(role=role,stage=stage,completed_updates=len(updates),
                transitions=sum(u['transitions'] for u in updates),
                collection_sum_s=collection,update_sum_s=update,
                collection_fraction_of_recorded_collection_plus_update=collection/(collection+update),
                collection_mean_s=mean(u['collection_s'] for u in updates),
                collection_median_s=median(u['collection_s'] for u in updates),
                update_mean_s=mean(u['update_s'] for u in updates),
                transition_per_recorded_collection_second=sum(u['transitions'] for u in updates)/collection,
                updates=[{key:u[key] for key in ('update_index','collection_s','update_s','transitions')} for u in updates])
    data=Path(__file__).read_bytes()
    INPUTS[str(Path(__file__))]=dict(sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    result=dict(schema='guitar_learning.collection_update_walltime.v1',runs=runs,
        total_transitions=sum(r['transitions'] for r in runs.values()),
        scope='collection includes native simulation, policy inference and IPC. Fractions use collection_s+update_s only; startup/reset/checkpoint/other overhead is not separately profiled. Concurrent hand-run durations must not be added as elapsed wall time.',
        input_snapshots=INPUTS)
    with output.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
    lines=['# 수집과 PPO update 시간', '',
        '수집 시간은 시뮬레이션·정책 추론·통신을 포함한다. 아래 비율의 분모는 로그의 collection_s+update_s이며 전체 실행시간이나 순수 물리 계산 비율이 아니다. 양손 병렬 실행의 시간을 합산해 실제 경과시간으로 해석하지 않는다.', '',
        '| 실행 | update | 전이 | 수집 합계(s) | update 합계(s) | 수집 비율 | 수집 평균(s/update) |',
        '|---|---:|---:|---:|---:|---:|---:|']
    for name,r in runs.items():
        lines.append('| %s | %d | %d | %.3f | %.3f | %.4f%% | %.3f |'%(name,r['completed_updates'],r['transitions'],r['collection_sum_s'],r['update_sum_s'],r['collection_fraction_of_recorded_collection_plus_update']*100,r['collection_mean_s']))
    lines+=['', '학습 전이 합계: %d. 수집/통신/추론의 구체적인 병목 분해는 별도 프로파일이 필요하다.'%result['total_transitions'], '', '[원수치와 입력 SHA](%s)'%output]
    with markdown.open('x') as stream:stream.write('\n'.join(lines)+'\n')
    print(json.dumps({name:{k:r[k] for k in ('transitions','collection_sum_s','update_sum_s','collection_fraction_of_recorded_collection_plus_update')} for name,r in runs.items()}))


if __name__=='__main__':main()
