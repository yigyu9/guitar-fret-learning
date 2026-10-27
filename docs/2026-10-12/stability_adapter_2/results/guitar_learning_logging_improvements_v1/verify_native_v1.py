"""Read-only independent accounting/raw-substep checks of new logging runs."""
import gzip
import hashlib
import json
import math
from pathlib import Path

PHASE=Path(__file__).resolve().parent
ROOT=PHASE.parents[4]


def read(path):return json.loads(Path(path).read_text())
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(4*1024*1024),b''):h.update(block)
    return h.hexdigest()
def norm(value):return math.sqrt(sum(x*x for x in value))


def verify_run(name):
    folder=PHASE/name
    report=read(folder/'report.json');summary=read(folder/'training_summary.json')
    assert report['completed'],report.get('failure')
    accounting=report['accounting']
    assert accounting['sampled_transitions']==accounting['logged_transitions']==accounting['durable_transitions']==accounting['committed_transitions']
    assert accounting['discarded_transitions']==0
    transitions=raw_count=0;reward_error=0.;totals={};last={}
    with gzip.open(folder/'transitions.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line)
            for worker,info in enumerate(row['infos']):
                transitions+=1
                assert info['worker_id']==worker
                assert info['safety240']['sample_count']==4
                reward_error=max(reward_error,abs(row['reward'][worker]-sum(info['reward_terms'].values())))
                for key,value in info['reward_terms'].items():totals[key]=totals.get(key,0.)+value
                last[worker]=info
                if 'raw_sample_path' not in info:continue
                raw_count+=1
                with gzip.open(info['raw_sample_path'],'rt') as rawstream:raw=json.load(rawstream)
                rows=raw['info']['physics_measurements'];safety=[r['stability'] for r in rows]
                expected=dict(guitar_displacement_m=max(norm(r['guitar_delta_m']) for r in safety),
                    guitar_rotation_rad=max(norm(r['guitar_rotation_vector_rad']) for r in safety),
                    left_foot_displacement_m=max(norm(r['foot_delta_m'][0]) for r in safety),
                    right_foot_displacement_m=max(norm(r['foot_delta_m'][1]) for r in safety),
                    joint_speed_rad_s=max(r['max_joint_speed_rad_s'] for r in safety))
                for key,value in expected.items():assert abs(value-info['safety240']['maxima'][key])<1e-12
    assert transitions==accounting['committed_transitions']==summary['transitions']
    assert reward_error<1e-6
    for key,value in totals.items():assert abs(value-summary['reward_terms'][key])<1e-10
    episode_count=0;qualities=[];safety_samples=0
    with (folder/'episodes.jsonl').open() as stream:
        for line in stream:
            record=json.loads(line);metrics=record['metrics']
            assert metrics['safety240_complete']
            safety_samples+=metrics['safety240']['sample_count']
            if record['episode'] is None:continue
            episode_count+=1
            episode=record['episode'];q=episode['musical_quality']
            assert metrics['quality_stage_success']==q['stage_success']
            assert metrics['timing_only_success']==episode['timing']['timing_only_stage_success']
            assert not metrics['physical_failure']
            qualities.append(dict(worker=record['worker_id'],quality=q['stage_success'],
                timing_only=metrics['timing_only_success'],left=metrics['left'],right=metrics['right']))
    assert safety_samples==transitions*4
    assert episode_count==summary['completed_episodes']
    quality_report=read(folder/'musical_quality_report.json')
    assert quality_report['episodes']==[]
    assert quality_report['completed_episodes']==episode_count
    assert quality_report['successful_episodes']==summary['quality_successful_episodes']
    assert quality_report['episode_records']['sha256']==sha(folder/'episodes.jsonl')
    assert not (folder/'rollout_first.pt').exists()
    assert not (folder/('checkpoint_%06d.pt'%(report['settings']['updates']-1))).exists()
    assert not report['changed_inputs'] and not report['guard_violations'] and not report['physical_flags_errors']
    return dict(path=str(folder),completed=True,transitions=transitions,physics_samples=transitions*4,
        completed_episodes=episode_count,quality_successes=quality_report['successful_episodes'],
        raw_substep_checks=raw_count,max_float32_reward_error=reward_error,
        accounting=accounting,optimizer_updates=report['optimizer_updates'],
        final_checkpoint_mode=report['final_checkpoint']['mode'],episodes=qualities,
        transition_compressed_bytes=(folder/'transitions.jsonl.gz').stat().st_size)


if __name__=='__main__':
    output=PHASE/'native_verification_v1.json'
    if output.exists():raise FileExistsError(str(output))
    source=read(PHASE/'sources_before_native_v1.json')
    old=read(PHASE/'preserved_results_before_v1.json')
    changed_source=[p for p,h in source.items() if sha(p)!=h]
    changed_old=[p for p,h in old.items() if sha(p)!=h]
    archive=read(ROOT/'guitar_learning/archive/20261019_before_logging_improvements/manifest.json')['files']
    changed_archive=[r['snapshot'] for r in archive if sha(r['snapshot'])!=r['sha256']]
    assert not changed_source and not changed_old and not changed_archive
    runs={name:verify_run(name) for name in ('left_native_train_v1','right_native_train_v1','left_native_resume_v1')}
    evaluation=read(PHASE/'right_native_eval_v1/evaluation_metrics.json')
    assert evaluation['mode']=='deterministic_evaluation' and evaluation['optimizer_updates']==1
    assert evaluation['completed_episodes']==1
    result=dict(completed=True,runs=runs,evaluation=evaluation,source_files=len(source),
        preserved_artifact_files=len(old),archived_files=len(archive),
        changed_source=changed_source,changed_old_results=changed_old,changed_archive=changed_archive,
        scope='logging integration and preservation only; no learning convergence claim')
    output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(dict(completed=True,training_transitions=sum(r['transitions'] for r in runs.values()),
        evaluation_episodes=evaluation['completed_episodes'])))
