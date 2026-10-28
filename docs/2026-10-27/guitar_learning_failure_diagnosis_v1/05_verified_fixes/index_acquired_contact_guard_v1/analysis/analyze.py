"""CPU audit of completed paired acquired-contact evaluations; raw is immutable."""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
MODES=('current_goal','acquired_contact')
INDICES=(4,7,8)


def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m


def preflight():
    paths=[BASE/'01_launcher.json'];launcher=json.loads(paths[0].read_text())
    if launcher.get('completed') is not True or launcher.get('returncode')!=0 or [c.get('condition') for c in launcher.get('children',[])]!=list(MODES) or any(c.get('returncode')!=0 for c in launcher.get('children',[])):raise ValueError('Both actual child exits required')
    for mode in MODES:
        folder=BASE/'runs'/mode
        for name in ('evaluation.json','diagnostic_report.json','acquired_guard_report.json'):
            p=folder/name;v=json.loads(p.read_text());paths.append(p)
            if name=='evaluation.json':
                rows=v['episodes']
                if v['assigned_quotas']!=[1]*128 or len(rows)!=128 or sorted(r['env_id'] for r in rows)!=list(range(128)):raise ValueError('All128 first attempts required')
            elif not v['completed'] or v['failure'] is not None or (not v['closed'] if name=='diagnostic_report.json' else not all(v['checks'].values())):raise ValueError('Closed/override audit required')
    return launcher,paths


def memory_audit(g,rows,view,mode):
    import numpy as np
    first=g['first_attempt'];shape=first.shape;assert first.dtype==bool and len(shape)==2 and shape[1]==128 and shape[0]<=354
    lengths=np.array([next(r['steps'] for r in rows if r['env_id']==j) for j in range(128)])
    np.testing.assert_array_equal(first,np.arange(shape[0])[:,None]<lengths[None])
    clocks=np.broadcast_to(4*np.arange(shape[0])[:,None],shape)
    np.testing.assert_array_equal(g['start_clock'][first],clocks[first]);np.testing.assert_array_equal(g['clock'][first],clocks[first]+4)
    available=(g['start_clock']/240+view['score_offset_s'])[...,None]<np.array([t['end_s'] for t in view['source_targets']])
    goal=np.where(available.any(-1),np.array(INDICES)[available.argmax(-1)],-1);np.testing.assert_array_equal(g['current_goal'][first],goal[first])
    get=lambda label:np.stack([g[label+'_'+str(j)] for j in INDICES],axis=-1)
    candidate,wrong,before,after=[get(k) for k in ('selected_candidate','selected_wrong','memory_before','memory_after')]
    chosen=goal[...,None]==np.array(INDICES);current_candidate=(candidate&chosen).any(-1);current_wrong=(wrong&chosen).any(-1)
    for k,v in (('input_current_candidate',current_candidate),('input_current_wrong',current_wrong)):np.testing.assert_array_equal(g[k][first],v[first])
    safe=g['finite']&~g['prior_failure']&~g['reset'];expected=safe[...,None]&candidate&~wrong&(before|chosen)
    np.testing.assert_array_equal(after[first],expected[first]);np.testing.assert_array_equal(before[0],np.zeros((128,3),bool))
    for k in range(1,shape[0]):np.testing.assert_array_equal(before[k,first[k]],after[k-1,first[k]])
    for k,v in (('memory_acquired',after&~before),('memory_lost',before&~after)):np.testing.assert_array_equal(get(k)[first],v[first])
    effective=current_candidate if mode==MODES[0] else after.any(-1)
    np.testing.assert_array_equal(g['effective_candidate'][first],effective[first])
    if mode==MODES[0]:np.testing.assert_array_equal(g['effective_wrong'][first&(goal!=-1)],current_wrong[first&(goal!=-1)])
    else:assert not g['effective_wrong'][first].any()
    eligible=safe&effective&(~current_wrong if mode==MODES[0] else True);blocked=eligible&(g['raw_target_rad']>g['old_target_rad'])
    np.testing.assert_array_equal(g['effective_eligible'][first],eligible[first]);np.testing.assert_array_equal(g['effective_blocked'][first],blocked[first])
    base=safe&current_candidate&~current_wrong&(g['raw_target_rad']>g['old_target_rad']);extra=blocked&~base
    np.testing.assert_array_equal(g['baseline_would_block'][first],base[first]);np.testing.assert_array_equal(g['memory_extended_block'][first],extra[first])
    np.testing.assert_array_equal(g['final_target_rad'][first],np.where(blocked,g['old_target_rad'],g['raw_target_rad'])[first])
    valid=first&g['finite']
    for k in ('other104_error_rad','memory_error_rad','submit_error_rad','observation_error'):assert (g[k][valid]==0).all(),k
    assert (g['box_rate_excess_rad'][valid]<=g['numerical_tolerance_rad'][valid]).all()
    np.testing.assert_array_equal(g['old_target_rad'][1:][first[1:]],g['final_target_rad'][:-1][first[1:]])
    first_extra=[]
    for j in range(128):
        ids=np.flatnonzero(first[:,j]&extra[:,j]);first_extra.append(dict(env_id=j,index=int(ids[0]) if len(ids) else None,start_clock=int(clocks[ids[0],j]) if len(ids) else None))
    return dict(first_controls=int(first.sum()),blocked=int((first&blocked).sum()),memory_extended_block=int((first&extra).sum()),
        acquired_by_note=(get('memory_acquired')&first[...,None]).sum((0,1)).tolist(),lost_by_note=(get('memory_lost')&first[...,None]).sum((0,1)).tolist(),
        none_retained_controls=int((first&(goal==-1)&after.any(-1)).sum()),first_extra=first_extra,prior_failure_controls=int((first&g['prior_failure']).sum()),post_failure_controls=int((first&g['post_failure']).sum()),
        scope='60Hz first-attempt precontrol cache; no240Hz continuouscontact certification; effective predicate is mode specific')


def array_diff(a,b,mask=None):
    import numpy as np
    if a.shape!=b.shape:return dict(shape_equal=False,old=list(a.shape),new=list(b.shape))
    if mask is not None:a=a[mask];b=b[mask]
    if not a.size:return dict(samples=0,exact=True,max_abs=None)
    result=dict(samples=int(a.size),exact=bool(np.array_equal(a,b,equal_nan=True)))
    if a.dtype.kind in 'biuf':
        finite=np.isfinite(a)&np.isfinite(b);result['max_abs']=float(np.abs(a[finite].astype(float)-b[finite].astype(float)).max()) if finite.any() else None
        result['nonfinite_pattern_exact']=bool(np.array_equal(np.isfinite(a),np.isfinite(b)))
    return result


def self_check():
    old=Path.read_text;seen=[]
    def incomplete(p,*a,**kw):seen.append(p);assert p==BASE/'01_launcher.json';return '{"completed":false}'
    Path.read_text=incomplete
    try:
        try:preflight()
        except ValueError:pass
        else:raise AssertionError('Incomplete run admitted')
    finally:Path.read_text=old
    assert len(seen)==1 and not any(k in sys.modules for k in ('numpy','torch','isaacgym'))
    import numpy as np
    shape=(2,128);g={k:np.zeros(shape,bool) for k in ('first_attempt','finite','prior_failure','reset','effective_wrong','post_failure')};g['first_attempt'][:]=True;g['finite'][:]=True
    g['start_clock']=np.broadcast_to(np.arange(2)[:,None]*4,shape).copy();g['clock']=g['start_clock']+4;g['current_goal']=np.full(shape,4)
    for label in ('selected_candidate','selected_wrong','memory_before','memory_after','memory_acquired','memory_lost'):
        for j in INDICES:g[label+'_'+str(j)]=np.zeros(shape,bool)
    g['selected_candidate_4'][:]=True;g['memory_after_4'][:]=True;g['memory_before_4'][1]=True;g['memory_acquired_4'][0]=True
    for k in ('input_current_candidate','effective_candidate','effective_eligible','effective_blocked','baseline_would_block'):g[k]=np.ones(shape,bool)
    g['input_current_wrong']=g['memory_extended_block']=np.zeros(shape,bool)
    for k in ('old_target_rad','final_target_rad','other104_error_rad','memory_error_rad','submit_error_rad','observation_error','box_rate_excess_rad','numerical_tolerance_rad'):g[k]=np.zeros(shape)
    g['raw_target_rad']=np.full(shape,.01);rows=[dict(env_id=j,steps=2) for j in range(128)];view=dict(score_offset_s=0.,source_targets=[dict(end_s=t) for t in (3,4,5)])
    assert memory_audit(g,rows,view,MODES[1])['blocked']==256
    for key in ('memory_after_4','effective_candidate','effective_blocked','memory_extended_block'):
        bad={k:v.copy() for k,v in g.items()};bad[key][1,0]=not bad[key][1,0]
        try:memory_audit(bad,rows,view,MODES[1])
        except AssertionError:pass
        else:raise AssertionError('Invalid '+key+' admitted')
    assert not array_diff(np.array([1.]),np.array([1.+1e-7]))['exact']
    print('자가검증 PASS: 완료전읽기차단·3bit/effective 별도검증·오류거부·미세차이보존; raw0/GPU0')


def actual_main():
    launcher,early=preflight();out=HERE/'results_v1';assert not out.exists() and not out.is_symlink()
    probe=module('acquired_actual_probe',BASE/'probe.py');grid=probe.grid;sys.path.insert(0,str(grid.ROOT));inputs={};verified={}
    def track(p):p=Path(p).resolve();inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():assert grid.sha(p)==h,p;verified[p]=h
    for p in early:track(p)
    seal,paths=probe.gate();pins(seal['input_pins'])
    for p in paths:track(p)
    review=read(BASE/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
    pre=module('acquired_prefix_trace_helpers',track(probe.parent.HERE/'precheck_analysis/analyze.py'))
    learned=module('acquired_prefix_phase_helpers',track(probe.parent.HERE/'learning_analysis/analyze.py'))
    arm=module('acquired_existing_arm_helpers',track(probe.parent.HERE.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1);assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    config=probe.parent.settings();track(probe.parent.HERE/'cpu_inputs/settings.json');view=config['song']['short_learning']['view'];extra=probe.parent.support();metadata,_=fixture(1)
    original=probe.parent.output('evaluate',update=300);frozen=read(original/'evaluation.json');original_contract=read(original/'training_contract.json')
    with np.load(track(original/'trace_env0_episode0.npz')) as z:frozen_trace=dict(z)
    with np.load(track(original/'current_goal_DIP60.npz')) as z:frozen_guard=dict(z)
    payload=torch.load(track(probe.parent.checkpoint(300)),map_location='cpu',weights_only=False);h=hashlib.sha256()
    for k,v in sorted(payload['model'].items()):h.update(k.encode());h.update(v.detach().cpu().contiguous().numpy().tobytes())
    model_sha=h.hexdigest();assert payload['updates']==300 and payload['identity']['architecture']['contract']==original_contract;del payload
    cases={};traces={};guards={};attempts=[];notes=[];all_rows={}
    for mode,child in zip(MODES,launcher['children']):
        folder=BASE/'runs'/mode;assert child['argv']==read(BASE/'cpu_inputs/commands.json')[mode]
        assert read(folder/'settings.json')==config and read(folder/'training_contract.json')==original_contract
        report=read(folder/'report.json');diag=read(folder/'diagnostic_report.json');audit=read(folder/'acquired_guard_report.json');scene=read(folder/'gpu_scene_final.json');override=read(folder/'execution_override.json')
        assert report['completed'] and report['closed'] and report['failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert all(diag[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and diag['failure'] is None and not any(diag[k] for k in ('cleanup_errors','changed_inputs','unpinned_project_sources'))
        assert audit['completed'] and not audit['cleanup_errors'] and all(audit['checks'].values()) and audit['policy_before']==audit['policy_after'] and audit['policy_before']['model_sha256']==model_sha and audit['policy_before']['updates']==300
        assert override['mode']==mode and override['original_training_contract_preserved'] and override['model_checkpoint_sha256']==grid.sha(probe.parent.checkpoint(300))
        assert all(override[k]==v for k,v in probe.descriptor(mode).items() if k!='scope')
        assert scene['closed'] and scene['environment_count']==128 and scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
        assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['hand_collision_native_readback_environments']==128 and scene['physics_steps']==diag['physics_steps']<=1416 and scene['physics_steps']%4==0
        assert read(folder/'native_effort_readback.json')==read(probe.parent.HERE/'cpu_inputs/effort_declaration128.json')
        before=read(folder/'inputs_before.json');pins(before)
        for name in ('inputs_after.json','diagnostic_inputs_after.json'):
            after=read(folder/name);assert after['verified'] and after['input_pins']==before and not after['changed_paths'] and not after['unpinned_project_sources']
        evaluation=read(folder/'evaluation.json');rows=evaluation['episodes'];all_rows[mode]=rows;assert grid.complete(rows,128) and evaluation['summary']==summary(rows) and evaluation['condition']=='policy'
        accept=probe.parent.acceptance(rows);assert all(accept[k]==v for k,v in pre.acceptance(rows).items()) and accept==read(folder/'prefix_acceptance.json')
        for r in rows:
            assert set(r['reward_components'])==set(REWARD_TERMS) and np.isfinite([r['reward'],*r['reward_components'].values()]).all()
            attempts.append(dict(condition=mode,env_id=r['env_id'],achieved=r['achieved'],steps=r['steps'],reward=r['reward'],cost=r['cost'],physical_failure=r['termination']['physical_failure'],wrist_failure=r['termination']['wrist_failure'],reward_sum_residual=r['reward']-sum(r['reward_components'].values()),**r['reward_components']))
            for n in r['notes']:notes.append(dict(condition=mode,env_id=r['env_id'],source_index=n['source_index'],achieved=n['achieved'],clean=n['clean_fraction'],wrong=n['audible_wrong_fraction'],released=n['released'],release_s=n['release_s']))
        meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names'] and meta['source_indices']==list(INDICES);metadata['action_contract']=original_contract['action']['target_contract']
        with np.load(track(folder/'trace_env0_episode0.npz')) as z:t=dict(z)
        with np.load(track(folder/'acquired_control60.npz')) as z:g=dict(z)
        traces[mode]=t;guards[mode]=g;mg=memory_audit(g,rows,view,mode)
        if mode==MODES[0]:
            normalized=dict(g)
            for k in ('candidate','wrong','eligible','blocked'):normalized[k]=g['effective_'+k]
            pre.guard_audit(normalized,rows,view)  # Baseline only. Never claim acquired fits this predicate.
        detail=pre.trace_audit(t,metadata,config,rows,original_contract['action']['target_contract'],extra,arm,'policy')
        cases[mode]=dict(acceptance=accept,summary=evaluation['summary'],guard=mg,env0=detail)
        if 'unavailable' not in detail:cases[mode]['env0_motion']=learned.phase_audit(t,g,config,original_contract['action']['target_contract'],metadata)
    baseline_trace={k:array_diff(frozen_trace[k],traces[MODES[0]][k]) for k in frozen_trace}
    baseline_guard={k:array_diff(frozen_guard[k],guards[MODES[0]]['effective_'+k] if k in ('candidate','wrong','eligible','blocked') else guards[MODES[0]][k]) for k in frozen_guard}
    old={r['env_id']:r for r in frozen['episodes']};new={r['env_id']:r for r in all_rows[MODES[0]]};baseline_episodes=dict(full_episode_exact=all(old[j]==new[j] for j in old),
        core_difference_envs=[j for j in old if any(old[j][k]!=new[j][k] for k in ('achieved','clean_fraction','audible_wrong_fraction','reason','steps','termination','notes'))],
        reward_max_abs_diff=max(abs(old[j]['reward']-new[j]['reward']) for j in old),reward_component_max_abs_diff={k:max(abs(old[j]['reward_components'][k]-new[j]['reward_components'][k]) for j in old) for k in REWARD_TERMS})
    pair={};ga,gb=[guards[m] for m in MODES];first_extra=cases[MODES[1]]['guard']['first_extra'];length=min(len(ga['first_attempt']),len(gb['first_attempt']));prefix=np.zeros((length,128),bool)
    for e in first_extra:prefix[:,e['env_id']]=np.arange(length)<(e['index'] if e['index'] is not None else length)
    prefix &= ga['first_attempt'][:length]&gb['first_attempt'][:length]
    pair['all128_scalar_before_extra']={k:array_diff(ga[k][:length],gb[k][:length],prefix) for k in ('start_clock','clock','current_goal','old_target_rad','raw_target_rad','final_target_rad','input_current_candidate','input_current_wrong','finite','reset','prior_failure')}
    e0=first_extra[0]['index'];n=min(len(traces[MODES[0]]['time_s']),len(traces[MODES[1]]['time_s']),e0 if e0 is not None else 354)
    pair['env0_full_before_extra']={k:array_diff(traces[MODES[0]][k][:n],traces[MODES[1]][k][:n]) for k in traces[MODES[0]]}
    assert len(attempts)==256 and len(notes)==768 and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__));track(HERE/'PLAN.md');out.mkdir();grid.write(out/'comparison.json',dict(cases=cases,baseline_frozen300=dict(episodes=baseline_episodes,env0=baseline_trace,whole128_scalar=baseline_guard),paired_prefix=pair,source_model_sha256=model_sha))
    for name,table in (('attempts.csv',attempts),('notes.csv',notes)):
        with (out/name).open('x',newline='') as f:w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,attempts=256,note_opportunities=768,model_RNG_updates_frozen=True,all_native128x105_cap90pairs=True,all_scenes_closed=True,reward_component_sum_max_abs_residual=max(abs(r['reward_sum_residual']) for r in attempts),limits=['bodyresultant not pairpressure; env0 detail60Hz only','memory is precontrol cache not240continuouscontact; other127 fullstate unavailable','baseline/prefix residuals reported exactly without new force equivalence gate','original currentgoal verifier used baseline only; new effective predicate separately checked']))
    lines=['# 정상획득 접촉 기억 guard 실제 비교','', '| 조건 | A4/B7/B8 달성률 | all3 | A release | 음악/해제/AND | 물리/손목실패 | 추가억제control |','|---|---|---:|---:|---|---|---:|']
    for m,c in cases.items():
        a=c['acceptance'];lines.append('| %s | %s | %.6f | %.6f | %s/%s/%s | %d/%d | %d |'%(m,', '.join('%.6f'%n['achieved_fraction'] for n in a['per_note']),a['all3_achieved_fraction'],a['A_released_fraction'],a['music_passed'],a['release_passed'],a['stage_ready'],a['physical_failures'],a['wrist_failures'],c['guard']['memory_extended_block']))
    lines+=['','256첫시도/768음·실패를 포함하며 원9보상은재지급하지않았다. A미압현의release0은압현후해제능력의독립실패로해석하지않는다. baseline원300 재현 및 추가개입전scalar/env0 차이는comparison에exact/max차이로보존했고미세힘차이를새문턱으로없애지않았다.','', 'current 원값과effective 기억 gate는구분했고기존currentgoal verifier는baseline에만썼다. 원strict model identity·새execution_override/RNG동결·nativecap/90쌍/입력후/close를대조했다. 참고N주입/full4freeze·보상/손목/물리변경은없다.','', 'env0원6gate·wrong원인/PIPDIP·관절4변화·음수명령/하한체류·손목/3마디순힘은comparison에보존했다. fullstate/상세힘은env0의60Hz만이며240연속·피부전체분리·pair압력·다른127힘은추정하지않는다. 개입이후actor/팔feedback도달라질수있어고정tape또는단일원인/일반제어·자연성해결로확대하지않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('CPU 실제 분석 완료:',out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);g=p.add_mutually_exclusive_group();g.add_argument('--self-check',action='store_true');g.add_argument('--root-completed',action='store_true');a=p.parse_args()
    if a.self_check:self_check()
    elif a.root_completed:actual_main()
    else:print('준비만 완료: root두장면종료전 actual읽기/결과0')
