"""0.5초 휴지 구간의 해제·다음 목표 접촉과 음 전체 유지를 별도 판정한다."""
import gzip
import json
from pathlib import Path
from build_analysis import episodes,sha

HERE=Path(__file__).resolve().parents[1]
ONSETS=(3.,5.,7.,9.)
ENDS=(4.5,6.5,8.5,10.5)


def main():
    out=HERE/'timing_seed7_E4_u300'
    report=json.loads((out/'report.json').read_text())
    assert report['completed'] and report['lifecycle_verified'] and report['episodes']==32
    assert not any(report.get(k) for k in ('failure','changed_inputs','missing_import_pins','cleanup_errors'))
    trace=HERE/'timing_seed7_E4_u300_all_env_contacts.jsonl.gz'
    with gzip.open(trace,'rt') as f:raw=[json.loads(line) for line in f]
    episodes_by_env={row['env_id']:row for row in episodes(out)}
    result=[]
    for env in range(32):
        identity=raw[0]['episode_ids'][env]
        rows=[r for r in raw if r['episode_ids'][env]==identity]
        episode=episodes_by_env[env]
        assert identity==episode['finger_control_diagnostics']['episode_id']
        assert rows[-1]['time_s'][env]+1/240+1e-8>=episode['task_time_s']
        safe=not episode['termination']['physical_failure'] and not episode['termination']['wrist_failure']
        clean=episode['left_note_ledger']['values']['clean']
        def candidate(row,index):return row['candidate'][env][index] and not row['wrong'][env][index]
        for old,new in ((0,1),(1,2),(2,3)):
            end,onset=ENDS[old],ONSETS[new]
            tail=[r for r in rows if end-.05-1e-8<=r['time_s'][env]<end-1e-8]
            onset_row=next((r for r in rows if r['time_s'][env]>=onset-1e-8),None)
            observed=onset_row is not None and onset_row['time_s'][env]-onset<=1/240+1e-8
            old_tail_clean=len(tail)>=11 and all(candidate(r,old) for r in tail)
            gap=[r for r in rows if end-1e-8<=r['time_s'][env]<=onset+1e-8]
            new_times=[r['time_s'][env] for r in gap if candidate(r,new)]
            # wrong 발생으로 clean이 사라진 것을 접촉 후보 소멸로 오인하지 않는다.
            last_old=max((r['time_s'][env] for r in rows if r['time_s'][env]<=onset+1e-8 and r['candidate'][env][old]),default=None)
            release=next((r['time_s'][env] for r in gap if last_old is not None and r['time_s'][env]>last_old+1e-8 and not r['candidate'][env][old]),None)
            on_time=bool(observed and old_tail_clean and release is not None and candidate(onset_row,new) and not onset_row['candidate'][env][old])
            full_previous=clean[old]>=1.5-1e-8
            full_next=clean[new]>=1.5-1e-8
            result.append(dict(env_id=env,previous_note=old+1,next_note=new+1,gap_s=[end,onset],
                previous_last50ms_clean=old_tail_clean,old_final_release_s=release,
                first_next_candidate_in_gap_s=min(new_times) if new_times else None,
                next_candidate_at_onset=bool(observed and candidate(onset_row,new)),
                on_time_transition=on_time and safe,previous_clean_s=clean[old],next_clean_s=clean[new],
                previous_full_1_5s=full_previous,next_full_1_5s=full_next,
                strict_pair_full_and_on_time=on_time and safe and full_previous and full_next,safe=safe))
    summary=[]
    for i in range(3):
        group=[r for r in result if r['previous_note']==i+1]
        summary.append(dict(previous_note=i+1,next_note=i+2,denominator=32,
            on_time_count=sum(r['on_time_transition'] for r in group),
            full_pair_on_time_count=sum(r['strict_pair_full_and_on_time'] for r in group),
            full_pair_example_env_ids=[r['env_id'] for r in group if r['strict_pair_full_and_on_time']]))
    all_four_full=[e for e,row in episodes_by_env.items() if all(v>=1.5-1e-8 for v in row['left_note_ledger']['values']['clean'])
        and not row['termination']['physical_failure'] and not row['termination']['wrist_failure']]
    data=dict(schema='virtual_transition.timing_feasibility.v1',summary=summary,transitions=result,
        all_four_full_1_5s_env_ids=all_four_full,
        scope='one fixed checkpoint, stochastic first32 episodes, actual GPU240Hz geometry/load candidates; not native contact-point or acoustic measurement',
        definition='diagnostic detach-and-move: previous last50ms clean, final previous rawcandidate disappearance in0.5s gap, previous rawcandidate off and next clean candidate at onset; full-pair additionally both ledgers clean1.5s; proxy disappearance is not measured native contact release; this is not a universal musical requirement',
        input_sha256={str(p):sha(p) for p in (trace,out/'report.json',out/'episodes.jsonl',out/'episode_metadata.json',Path(__file__).resolve())})
    (HERE/'timing_feasibility.json').write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps(dict(summary=summary,all_four_full_1_5s_env_ids=all_four_full),ensure_ascii=False,indent=2))


if __name__=='__main__':main()
