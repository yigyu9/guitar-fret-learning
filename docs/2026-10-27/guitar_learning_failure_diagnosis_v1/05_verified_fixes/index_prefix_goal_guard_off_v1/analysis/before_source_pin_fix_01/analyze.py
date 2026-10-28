"""Guard-off audit preparation; no actual files read before root completion."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
ON=BASE.parent/'index_prefix_goal_exploration_precheck_v1/analysis'
s=importlib.util.spec_from_file_location('off_original_on_analysis',ON/'analyze.py');on=importlib.util.module_from_spec(s);s.loader.exec_module(on)
complete=on.complete
execution=on.execution
guard_direction=on.guard_direction


def off_guard(g,rows,view):
    """Actual bypass semantics; this is not the original guard-on verifier."""
    import numpy as np
    first=np.asarray(g['first_attempt'],bool);assert first.ndim==2 and first.shape[1]==128 and len(first)<=354
    lengths=np.array([next(r['steps'] for r in rows if r['env_id']==i) for i in range(128)])
    np.testing.assert_array_equal(first,np.arange(len(first))[:,None]<lengths)
    clock=np.broadcast_to(np.arange(len(first))[:,None]*4,first.shape)
    np.testing.assert_array_equal(g['start_clock'][first],clock[first]);np.testing.assert_array_equal(g['clock'][first],clock[first]+4)
    available=(clock/240+view['score_offset_s'])[...,None]<np.array([r['end_s'] for r in view['source_targets']])
    goals=np.where(available.any(-1),np.array([4,7,8])[available.argmax(-1)],-1)
    np.testing.assert_array_equal(g['current_goal'][first],goals[first])
    eligible=first & g['candidate'] & ~g['wrong'] & ~g['prior_failure'] & ~g['reset'] & g['finite']
    would=eligible & (g['raw_target_rad']>g['old_target_rad'])
    np.testing.assert_array_equal(g['eligible'][first],eligible[first]);np.testing.assert_array_equal(g['would_block'][first],would[first])
    assert not g['actual_blocked'][first].any() and not g['blocked'][first].any()
    np.testing.assert_array_equal(g['actual_blocked'],g['blocked'])
    np.testing.assert_array_equal(g['raw_target_rad'][first],g['final_target_rad'][first])
    valid=first & g['finite']
    for k in ('other104_error_rad','memory_error_rad','submit_error_rad','observation_error'):assert (g[k][valid]==0).all(),k
    assert (g['box_rate_excess_rad'][valid]<=g['numerical_tolerance_rad'][valid]).all()
    return dict(first_attempt_controls=int(first.sum()),would_block_controls=int((would&first).sum()),actual_blocked_controls=0,
        by_goal={str(j):dict(controls=int((first&(goals==j)).sum()),would_block=int((would&(goals==j)).sum()),actual_blocked=0) for j in (4,7,8,-1)},
        prior_failure_controls=int((first&g['prior_failure']).sum()),same_endpoint_failure_controls=int((first&g['post_failure']).sum()),scope='guard-off actual passthrough; would_block is counterfactual only; failure endpoint retained')


def self_check():
    on.self_check()  # stdlib completion/mode/RNG guards; no producer/raw/model imports.
    import numpy as np
    shape=(3,128);flags=('first_attempt','candidate','wrong','prior_failure','reset','finite','eligible','blocked','post_failure','would_block','actual_blocked')
    g={k:np.zeros(shape,bool) for k in flags};g['first_attempt'][:]=True;g['finite'][:]=True
    g['start_clock']=np.broadcast_to(np.arange(3)[:,None]*4,shape).copy();g['clock']=g['start_clock']+4;g['current_goal']=np.full(shape,4)
    for k in ('old_target_rad','raw_target_rad','final_target_rad','other104_error_rad','memory_error_rad','submit_error_rad','observation_error','box_rate_excess_rad','numerical_tolerance_rad'):g[k]=np.zeros(shape)
    for k in ('candidate','eligible','would_block'):g[k][0,0]=True
    g['raw_target_rad'][0,0]=g['final_target_rad'][0,0]=.01
    rows=[dict(env_id=i,steps=3) for i in range(128)];view=dict(score_offset_s=0.,source_targets=[dict(end_s=t) for t in (3.1,4.7,5.7)])
    assert off_guard(g,rows,view)['would_block_controls']==1
    for k in ('would_block','actual_blocked','blocked','final_target_rad','other104_error_rad','current_goal','first_attempt'):
        v={n:a.copy() for n,a in g.items()};v[k][0,0]=False if k in ('would_block','first_attempt') else True if k in ('blocked','actual_blocked') else 9
        try:off_guard(v,rows,view)
        except AssertionError:pass
        else:raise AssertionError('Invalid off semantics admitted: '+k)
    assert not any(n in sys.modules for n in ('torch','isaacgym'))
    print('off 자가검증 PASS: raw=final/actualblocked0/wouldblock·범위/원분모; actual 읽기·결과생성0')


def actual():
    complete(on.read(BASE/'01_launcher.json'),on.read(BASE/'cpu_inputs/commands.json'))
    spec=importlib.util.spec_from_file_location('off_actual_producer',BASE/'probe.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
    # Reuse the frozen on audit; only the producer facade, paths and actual-off guard verifier differ.
    facade=SimpleNamespace(**vars(probe.on));facade.output=probe.output
    prior=(on.BASE,on.HERE,on.module)
    def module(name,path):
        if name=='exploration_actual_producer':return facade
        value=prior[2](name,path)
        if name=='exploration_actual_precheck':return SimpleNamespace(trace_audit=value.trace_audit,guard_audit=off_guard)
        return value
    try:
        on.BASE=BASE;on.HERE=HERE;on.module=module;on.actual()
    finally:on.BASE,on.HERE,on.module=prior
    assert (on.BASE,on.HERE,on.module)==prior
    out=HERE/'results_v1';result=on.read(out/'comparison.json');verification=on.read(out/'verification.json')
    def load(path):
        p=Path(path).resolve();h=probe.grid.sha(p);verification['input_sha256'][str(p)]=h;return on.read(p)
    load(Path(__file__));old=load(ON/'results_v1/comparison.json');review=load(ON/'results_v1/review.json')
    assert review['verdict']=='PASS' and not review['findings']
    paired={}
    for mode in on.MODES:
        report=load(probe.output(mode)/'guard_execution_override.json');case=result['cases'][mode]
        assert report['completed'] and report['failure'] is None and all(report['checks'].values()) and report['mode']==mode
        assert report['schema']==probe.SCHEMA and report['guard_enabled'] is False and report['checkpoint_metadata_rewritten'] is False and report['original_control_contract_preserved'] is True
        assert report['checkpoint_sha256']==probe.on.recovery.MODEL_SHA and report['checkpoint']==str(probe.on.CHECKPOINT)
        assert report['first_attempt_counts']=={k:case['guard'][k] for k in ('first_attempt_controls','would_block_controls','actual_blocked_controls')}
        case['guard_execution_override']=report
        before=old['cases'][mode];paired[mode]={k:before[k] for k in ('acceptance','A_achieved_release_cross','guard','reward9_mean')}
        paired[mode]['guard_direction']={k:v for k,v in before['guard_direction'].items() if k!='segments'}
        paired[mode]['env0_trace']=before['trace']
    result['paired_on']=paired
    result['scope']='256 new off attempts/768 notes vs separately reviewed on256/768; closed-loop execution override, not identical-action physics; original guard-on contract retained and actual bypass separately declared'
    result['analysis_aliases_restored']=True
    # Direct new inputs only; native full maps remain the original execution audits.
    for mode in on.MODES:
        mapping=on.read(probe.output(mode)/'inputs_before.json')
        for p,h in verification['input_sha256'].items():
            if p in mapping:assert mapping[p]==h;verification['verified_input_sha256'][p]=h
    probe.grid.write(out/'comparison.json',result);probe.grid.write(out/'verification.json',verification)
    print(json.dumps({m:dict(acceptance=result['cases'][m]['acceptance'],cross=result['cases'][m]['A_achieved_release_cross'],off_counts=result['cases'][m]['guard']) for m in on.MODES},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--self-check',action='store_true');p.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual()
    else:print('CPU 분석 준비만: root off 두child 종료 통보 전 실제자료 읽기/결과생성0')
