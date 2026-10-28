"""Reuse frozen prefix analysis, then audit only the added schedules and counters."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
PREFIX=BASE.parent/'index_prefix_4_7_8_v1'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec)
    sys.modules[name]=value;spec.loader.exec_module(value);return value


def check_launcher(value):
    assert value['completed'] and value['returncode']==0 and len(value['children'])==1
    child=value['children'][0];assert child['finger']=='index' and child['control']=='reference' and child['returncode']==0


def check_masks(steps,masks):
    assert len(steps)==4 and len(masks)>=max(steps)
    assert all(row==[k<n for n in steps] for k,row in enumerate(masks))


def selfcheck():
    good=dict(completed=True,returncode=0,children=[dict(finger='index',control='reference',returncode=0)])
    check_launcher(good)
    for key,value in (('completed',False),('returncode',1),('children',[])):
        bad=copy.deepcopy(good);bad[key]=value
        try:check_launcher(bad)
        except AssertionError:pass
        else:raise AssertionError('bad launcher accepted')
    masks=[[k<n for n in [1,2,3,4]] for k in range(4)];check_masks([1,2,3,4],masks)
    masks[2][0]=True
    try:check_masks([1,2,3,4],masks)
    except AssertionError:pass
    else:raise AssertionError('retry mask accepted')
    assert not any(n in sys.modules for n in ('torch','numpy','isaacgym'))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true');parser.add_argument('--self-check',action='store_true');args=parser.parse_args()
    if args.self_check:selfcheck();print('stdlib synthetic launcher/mask checks PASS');return
    if not args.root_completed:
        print('준비만 완료: root 종료 통보 전 실제 raw를 읽지 않습니다.');return
    probe=module('release_actual_probe',BASE/'probe.py');grid=probe.grid
    sys.path.insert(0,str(grid.ROOT));out=HERE/'results_v1';probe.cap.reject_existing(out)
    launch=grid.read(BASE/'01_launcher.json');check_launcher(launch)
    parent=module('release_frozen_prefix_analysis',PREFIX/'analysis/analyze.py');load=parent.module
    aliases={BASE/'runs/index/prefix_scope_report.json':BASE/'runs/index/release_transfer_scope_report.json',BASE/'runs/index/prefix_acceptance.json':BASE/'runs/index/release_transfer_acceptance.json'}
    resolve=lambda path:aliases.get(Path(path),Path(path))
    facade=SimpleNamespace(ROOT=grid.ROOT,read=lambda p:grid.read(resolve(p)),sha=lambda p:grid.sha(resolve(p)),complete=grid.complete,phase_masks=grid.phase_masks,write=grid.write)
    adapter=SimpleNamespace(grid=facade,cap=probe.cap,gate=probe.gate,postcheck=probe.postcheck,base=probe.prefix.base,support=probe.prefix.support)
    def child(name,path):return adapter if name=='prefix_analysis_probe' else load(name,path)
    # Original geometry/ledger/force analysis executes unchanged; only2 report names adapt.
    with patch.object(parent,'HERE',HERE),patch.object(parent,'BASE',BASE),patch.object(parent,'module',child):parent.main()
    import numpy as np
    import torch
    comparison=grid.read(out/'comparison.json');verification=grid.read(out/'verification.json')
    inputs={str(resolve(p)):h for p,h in verification['input_sha256'].items()}
    def read(path):inputs[str(path)]=grid.sha(path);return grid.read(path)
    def track(path):inputs[str(path)]=grid.sha(path);return path
    config=read(BASE/'cpu_inputs/index_settings.json');short=config['song']['short_learning'];view=short['view'];episodes=comparison['episodes']
    scope=read(BASE/'runs/index/release_transfer_scope_report.json');assert scope['schedule_aliases_restored'] and scope['observer_hooks_restored']
    with np.load(track(BASE/'runs/index/schedule_requests.npz')) as saved:requests=dict(saved)
    with np.load(track(BASE/'runs/index/trace_env0_episode0.npz')) as saved:t=dict(saved)
    steps=[next(e['steps'] for e in episodes if e['env_id']==i) for i in range(4)]
    check_masks(steps,requests['first_attempt'].tolist());assert len(requests['first_attempt'])<=354
    np.testing.assert_array_equal(requests['endpoint_clock'],requests['submit_clock']+4)
    request_audits=[]
    for env_id in range(4):
        first=requests['first_attempt'][:,env_id]
        np.testing.assert_array_equal(requests['submit_clock'][first,env_id],np.arange(steps[env_id])*4)
        time=requests['endpoint_clock'][:,env_id]/240.;weight=probe.timing.negative_weight(torch.tensor(time),view).numpy()
        # Before2s the frozen035→reference ramp is retained; after2s the3phase is explicit.
        hold=first&(time>=2);positive=np.array(short['release_transfer']['reference_selected_rad']);negative=np.array(short['release_transfer']['negative_selected_rad'])
        goal=positive+weight[:,None]*(negative-positive)
        np.testing.assert_allclose(requests['selected_goal_rad'][hold,env_id],goal[hold],rtol=0,atol=2e-6)
        np.testing.assert_allclose(requests['actual_native_target_rad'][hold,env_id],goal[hold],rtol=0,atol=2e-6)
        delta=abs(requests['actual_native_target_rad'][first,env_id]-requests['old_target_rad'][first,env_id]);assert np.isfinite(delta).all() and delta.max()<=4/60+2e-6
        assert requests['phase'][:,env_id].tolist()==[probe.timing.phase(float(v),view) for v in time]
        phases={}
        for phase_id,name in enumerate(('before','release','move','close','after')):
            mask=first&(requests['phase'][:,env_id]==phase_id);actual=requests['actual_selected_q_rad'][mask,env_id];target=requests['actual_native_target_rad'][mask,env_id]
            phases[name]=dict(control_samples=int(mask.sum()),actual4_mean_deg=np.rad2deg(actual).mean(0).tolist() if len(actual) else None,target4_mean_deg=np.rad2deg(target).mean(0).tolist() if len(target) else None)
        request_audits.append(dict(env_id=env_id,first_attempt_controls=steps[env_id],max_control_target_delta_rad=float(delta.max()),phases=phases))
    events=read(BASE/'runs/index/native_gate_events.json');assert len(events['envs'])==4 and events['clock_hz']==240 and not any(events['first_attempt_active'])
    for i,row in enumerate(events['envs']):
        assert row['env_id']==i and row['last_clock']==4*steps[i] and sum(v['samples'] for v in row['phases'].values())==row['last_clock']
        first_censored=row['first_censored_clock'];assert sum(v['censored_samples'] for v in row['phases'].values())==(row['last_clock']-first_censored+1 if first_censored is not None else 0)
        for name,item in row['phases'].items():
            assert 0<=item['valid_samples']<=item['samples']-item['censored_samples'] and 0<=item['nonfinite_force_samples']<=item['samples']
            assert all(0<=n<=item['samples'] for key in ('candidate_counts','loaded_counts','wrong_counts') for n in item[key])
            for key in ('first_valid_A_candidateoff_loadedoff','first_valid_B_candidateoff_loadedoff'):
                event=item[key]
                if event is None:continue
                assert not event['censored'] and (first_censored is None or event['clock']<first_censored)
                assert probe.timing.Observer.names[probe.timing.phase(event['clock']/240.,view)]==name
                cols=[0] if key.startswith('first_valid_A') else [1,2]
                assert all(not event['candidate'][j] and not event['assigned_loaded'][j] for j in cols)
        event=row['first_valid_post_A_candidate_fall']
        if event:assert not event['censored'] and not event['candidate'][0] and (first_censored is None or event['clock']<first_censored)
    old=read(PREFIX/'analysis/results_v1/comparison.json');baseline_review=read(PREFIX/'analysis/results_v1/review.json');assert baseline_review['verdict']=='PASS' and not baseline_review['findings']
    supplemental=dict(request_audits=request_audits,native_gate_events=events,baseline_closed_move_prefix=old['prefix'],baseline_source=str(PREFIX/'analysis/results_v1'),
        scope='actual targets and4env first masks/rate; bounded240 aggregate internal clock/censor checks only, no unavailable240-sample replay; N off/loadedoff not full skin separation; changedfinger+Cartesian-speed bundle')
    track(Path(__file__).resolve());track(HERE/'PLAN.md');track(PREFIX/'analysis/analyze.py')
    comparison['release_transfer_audit']=supplemental
    verification.update(input_sha256=inputs,release_transfer_first_masks_and_goal_target_rate=True,native_gate_aggregate_clock_censor_consistent=True,
        native_gate_limit='No240raw samples saved: aggregates are producer-pinned observations checked for internal consistency, not independent candidate240 replay',bundle_limit='finger release schedule andCartesiangoal speed66.8405vs44.6176mm/s jointlychanged; no isolatedreleasecausality')
    grid.write(out/'comparison.json',comparison);grid.write(out/'verification.json',verification)
    lines=['# staged release→이동→재압현 실제 결과','',f"각음 원acceptance3개 AND: **{comparison['prefix']['prefix_passed']}**,3음모두달성 {comparison['prefix']['all3_achieved_attempts']}/4. 원4episode/12note·9보상·354tick상한을보존했다.",'', '| source | 닫힌이동 달성/4 | staged 달성/4 | staged clean/wrong | env0 distal 평균N | wrist mm/° |','|---|---:|---:|---|---:|---|']
    for key,entry in comparison['notes'].items():
        a=entry['acceptance'];b=old['notes'][key]['acceptance'];phase=entry['phases'].get('audible',{});m=phase.get('metric_mean')
        lines.append('| %s | %d/4 | %d/4 | %.6f/%.6f | %s | %s |'%(key,b['achieved'],a['achieved'],a['mean_clean'],a['mean_wrong'],'%.6f'%m[14] if m else '미확인','%.6f/%.6f'%(m[15],m[16]) if m else '미확인'))
    lines+=['','| env | A release 원latch/time(score) | release중 A off/loadedoff 최초clock | move중 B off/loadedoff 최초clock | 최초censor |','|---|---|---|---|---|']
    for i,row in enumerate(events['envs']):
        episode=next(e for e in episodes if e['env_id']==i);note=episode['notes'][0]
        a=row['phases'].get('release',{}).get('first_valid_A_candidateoff_loadedoff');b=row['phases'].get('move',{}).get('first_valid_B_candidateoff_loadedoff')
        lines.append('| %d | %s / %.9f | %s | %s | %s |'%(i,note['released'],note['release_s'],a['clock'] if a else '없음',b['clock'] if b else '없음',row['first_censored_clock']))
    lines+=['','원native released/release_s는240Hz판정그대로이며candidate/assigned-loaded off사건과별도이다. 중간사건없음도분모/음악성과에서제외하지않는다. N은A-reset사례의distal-negative목표로, proximal하중/geometry가남을수있고피부전체분리나현압력을증명하지않는다. 원release창/음시계·성공기준은늘리지않았다.','',
        '목표일정은.10s손가락N/A손목유지→.4417s N유지/wristAtoB→.12s원reference/B손목유지이다. Cartesian목표속도44.6176→66.8405mm/s와손가락일정을함께바꿨으므로효과를해제하나의인과로확정할수없다. joint4rad/s·wrist .5도cap/gain/range/원105PD·90쌍은유지한다. 실제60Hz 요청/target/q·firstmask/rate및240집계의내부clock/censor를대조했다. 저장하지않은240sample을재생했다고주장하지않는다.','',
        '원6gate/10body×3wrong원인·각도/PIPDIP·force·팔경계·원A candidate잔존은comparison.json에기록했다. 본문힘/손목상세는env0 60Hz,4환경selectedq는추가bounded60Hz자료이다. bodyforce는pair압력이아니며NN학습/자유기타/J33/전곡/자연성/생산채택으로확대하지않는다. source/raw/원1215producer를수정하거나새GPU를실행하지않았다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n')
    print('staged4/12 audit complete; independent source+actual review pending')


if __name__=='__main__':main()
