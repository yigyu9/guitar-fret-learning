"""Read-only audit of recorded fretting evidence; never runs physics or changes classifiers."""
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[5]
PHASE=Path(__file__).resolve().parent
RUN=PHASE.parent/'guitar_learning_actionable_preparation_v1/left_ppo_eval_v1'
INPUTS={}


def record(path):
    path=Path(path).resolve();digest=hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda:stream.read(1024*1024),b''):digest.update(part)
    INPUTS[str(path)]=dict(sha256=digest.hexdigest(),bytes=path.stat().st_size)


def read(path):record(path);return json.loads(Path(path).read_text())


def plausible_neck_feature(e,g,contract):
    """Narrow offline diagnostic subset, not an acoustic wrong-press detector."""
    human=e['human_body']
    if not any(human=='human/LH:'+finger+str(n) for finger in ('thumb','index','middle','ring','pinky') for n in (2,3)):
        return None
    if e['guitar_body'] not in {'guitar/guitar',*('guitar/G:fret'+str(n) for n in range(1,23))}:
        return None
    if not e['positive_lambda'] or e['body_pair_witness_gap_m']>contract['witness_max_gap_m']:
        return None
    p=e['guitar_feature_G_m'];near=e['nearest_physical_string']-1
    start,end=g['starts_G_m'][near],g['ends_G_m'][near]
    fraction=(p[1]-start[1])/(end[1]-start[1])
    projected=[a+fraction*(b-a) for a,b in zip(start,end)]
    if not (0<=fraction<=1 and abs(p[0]-projected[0])<=contract['lateral_max_m'] and
            abs(p[2]-projected[2])<=contract['height_abs_max_m']):return None
    markers=g['fret_markers_G_m']
    cells=[i+1 for i in range(22) if min(markers[i][1],markers[i+1][1])<=p[1]<=max(markers[i][1],markers[i+1][1])]
    if not cells:return None
    return dict(nearest_string=near+1,geometric_cells=cells,
        nearest_lateral_m=abs(p[0]-projected[0]),nearest_height_m=p[2]-projected[2])


def main():
    out=PHASE/'fret_audit_v1.json'
    if out.exists():raise FileExistsError('preserve earlier audit')
    result=read(RUN/'result.json');reset=read(RUN/'reset_00.json')
    record(RUN/'transitions.json.gz')
    with gzip.open(RUN/'transitions.json.gz','rt') as stream:rows=json.load(stream)
    target=reset['training_contract']['task']['targets'][0];identity=target['target_id']
    total=valid=none=coexist_broad=coexist_narrow=0
    raw_reasons=Counter();narrow_reasons=Counter();narrow_labels=Counter();raw_bodies=Counter()
    features=0;narrow_features=0;valid_features=0;examples={};first_candidate=None
    timing_rewards=Counter();candidate_reason_counts=Counter();last_music=None
    for row in rows:
        for key,value in row['info']['reward_terms'].items():timing_rewards[key]+=value
        for p,sample in zip(row['physics_measurements'],row['native_physics_samples240']):
            measured=p['music'];m=measured['targets'][identity];evidence=m['evidence'];candidate=m['candidate']
            assert candidate==any(e['valid'] for e in evidence['contact_evidence'])
            assert candidate==bool(evidence['valid_evidence_ids'])
            total+=1;valid+=candidate;last_music=measured['summary']
            if candidate and first_candidate is None:first_candidate=measured['task_time_s']
            candidate_reason_counts.update(evidence['reason_flags'])
            rejected=[e for e in evidence['contact_evidence'] if not e['valid']]
            features+=len(evidence['contact_evidence']);valid_features+=len(evidence['valid_evidence_ids'])
            none+=not evidence['contact_evidence'];coexist_broad+=candidate and bool(rejected)
            narrow=[]
            for e in evidence['contact_evidence']:
                raw_reasons.update(e['reason_flags']);raw_bodies[e['human_body']]+=1
                feature=plausible_neck_feature(e,sample['geometry'],evidence['contract'])
                if feature is not None and not e['valid']:
                    narrow_features+=1;narrow.append((e,feature));narrow_reasons.update(e['reason_flags'])
                    if e['human_body'] not in {'human/LH:ring2','human/LH:ring3'}:narrow_labels['other_finger_body']+=1
                    if feature['nearest_string']!=target['string']+1:narrow_labels['other_string_lane']+=1
                    if target['fret'] not in feature['geometric_cells']:narrow_labels['outside_target_geometric_cell']+=1
                    if feature['nearest_string']==target['string']+1 and all(f>target['fret'] for f in feature['geometric_cells']):
                        narrow_labels['same_string_higher_geometric_cell']+=1
            coexist_narrow+=candidate and bool(narrow)
            if candidate and rejected and 'broad_coexist' not in examples:
                examples['broad_coexist']=dict(physics_step=p['physics_step'],time_s=measured['task_time_s'],candidate=True,
                    valid_evidence_ids=evidence['valid_evidence_ids'],rejected_example=rejected[0])
            if candidate and narrow and 'narrow_coexist' not in examples:
                e,feature=narrow[0]
                examples['narrow_coexist']=dict(physics_step=p['physics_step'],time_s=measured['task_time_s'],candidate=True,
                    valid_evidence_ids=evidence['valid_evidence_ids'],rejected_example=e,offline_geometry=feature)
            if not candidate and narrow and 'target_false_with_narrow_contact' not in examples:
                e,feature=narrow[0]
                examples['target_false_with_narrow_contact']=dict(physics_step=p['physics_step'],time_s=measured['task_time_s'],candidate=False,
                    overall_reason_flags=evidence['reason_flags'],rejected_example=e,offline_geometry=feature)
    source_locations={
        'guitar_learning/fretting_v1.py':dict(contract=[24,30],target_filter=[86,153],open=[82,85]),
        'guitar_learning/task_measurement.py':dict(target_and_open=[62,99],wrong_crossing=[154,159],strict_miss=[166,182]),
        'guitar_learning/training_environment.py':dict(base_reward=[12,23],base_computation=[125,145]),
        'guitar_learning/skill_environment.py':dict(replace_base=[297,306]),
        'guitar_learning/timing_curriculum.py':dict(left_reward=[123,153],right_crossing=[154,188],miss=[192,195]),
        'guitar_learning/timing_environment.py':dict(replace_reward=[131,143]),
        'guitar_learning/actionable_preparation_environment.py':dict(preparation_contact=[53,78]),
        'tab2body/env/rewards/fret.py':dict(old_requirement_masks=[932,963],old_geometric_press=[1920,1943],old_wrong_veto=[2275,2290],old_no_press=[2400,2416],old_penalty=[3002,3029]),
        'tab2body/cfg.py':dict(old_weights=[91,106])}
    for path in source_locations:record(ROOT/path)
    record(Path(__file__))
    summary=dict(total240Hz_samples=total,valid_target_samples=valid,invalid_target_samples=total-valid,
        raw_evidence_records=features,valid_target_evidence_records=valid_features,
        samples_without_any_human_guitar_evidence=none,
        valid_target_with_any_rejected_human_guitar_evidence_samples=coexist_broad,
        valid_target_with_any_rejected_human_guitar_evidence_fraction=coexist_broad/valid if valid else None,
        narrow_rejected_neck_feature_records=narrow_features,
        valid_target_with_narrow_rejected_neck_feature_samples=coexist_narrow,
        valid_target_with_narrow_rejected_neck_feature_fraction=coexist_narrow/valid if valid else None,
        all_evidence_rejection_reason_record_counts=dict(raw_reasons),all_human_body_record_counts=dict(raw_bodies),
        narrow_rejection_reason_record_counts=dict(narrow_reasons),narrow_geometric_diagnostic_label_record_counts=dict(narrow_labels),
        target_overall_reason_sample_counts=dict(candidate_reason_counts),first_target_candidate_s=first_candidate,
        reward_sums=dict(timing_rewards),original_joint_music=last_music,
        native_timing=result['episodes'][0]['timing'],examples=examples,
        denominator_scope='One actual LH final-PPO episode,420ticks/1680physics. Evidence records are per240Hz features, not unique musical mistakes. Broad rejects include chest/arm/thigh support. Narrow subset is offline diagnostic only: positive finger2/3/neck-surface, aligned witness, measured nearest string lane/height and actual neck-cell bounds; not a new runtime classifier or acoustic-error count.')
    assert total==1680 and abs(sum(timing_rewards.values())-result['episodes'][0]['reward'])<1e-8
    audit=dict(schema='guitar_learning.fret_audit.v1',created_utc=datetime.now(timezone.utc).isoformat(),
        native_trace_source=str(RUN),native_completed=result['completed'],source_unchanged=result['source_unchanged'],
        finding='Target-positive detector with rejection diagnostics; not exhaustive mutually exclusive correct/wrong/no-press musical classifier. Legacy fret reward is not reused.',
        native_summary=summary,source_line_locations=source_locations,input_snapshots=INPUTS)
    with out.open('x') as stream:json.dump(audit,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({k:v for k,v in summary.items() if k not in ('all_evidence_rejection_reason_record_counts','all_human_body_record_counts','native_timing','original_joint_music','examples')},ensure_ascii=False))


if __name__=='__main__':main()
