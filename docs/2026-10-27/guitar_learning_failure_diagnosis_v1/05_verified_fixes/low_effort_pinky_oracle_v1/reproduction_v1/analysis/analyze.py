"""CPU analysis of fresh pinky121 four attempts; no result before root handoff."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root-completed',action='store_true')
    if not parser.parse_args().root_completed:
        print('분석 준비만: root의 소지 fresh4 실제 종료 통보를 기다립니다.');return
    probe=module('pinky_fresh_analysis_probe',BASE/'probe.py');grid=probe.grid;out=HERE/'results_v1'
    probe.cap.reject_existing(out);sys.path.insert(0,str(grid.ROOT));inputs,verified={},{}
    def track(p):
        p=Path(p);inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(mapping):
        for p,h in mapping.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    seal,paths=probe.gate()
    for p in paths:track(p)
    pins(seal['input_pins']);read(BASE/'preparation_seal.json')
    review=read(BASE/'review.json');pins(review['reviewed_sha256'])
    launcher=read(BASE/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode']==0 and len(launcher['children'])==1
    assert launcher['children'][0]['finger']=='pinky' and launcher['children'][0]['returncode']==0
    import numpy as np
    import torch
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.tool.experiments.short_finger_learning.spec import read_reference
    torch.set_num_threads(1);metadata,_=fixture(1);folder=BASE/'runs/pinky'
    config=read(folder/'settings.json');assert config==read(BASE/'cpu_inputs/pinky_settings.json')==probe.prior.settings('pinky')
    short=config['song']['short_learning'];reference=read(probe.REFERENCE)
    assert reference==read_reference(probe.REFERENCE,short)
    row=read(probe.BASE/'cpu_inputs/pinky_grid.json')['rows'][121]
    assert reference['selected_targets_rad']==dict(zip(short['learned_action_names'],row['target_rad']))
    report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
    assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored','no_NN_checkpoint_training'))
    assert report['failure'] is None and not report['close_errors'] and not report['changed_inputs'] and not report['unpinned_project_sources']
    assert report['assigned_first_attempts']==4 and report['cap_Nm']==.25
    assert scene['closed'] and scene['environment_count']==scene['hand_collision_native_readback_environments']==4
    assert scene['hand_collision']['enabled_distinct_finger_pairs']==90 and scene['physx_use_gpu'] and scene['use_gpu_pipeline'] and scene['diagnostic_guitar_mode']=='fixed'
    assert report['resources']['physics_steps']==scene['physics_steps']==4*report['resources']['control_ticks']
    assert report['resources']['control_ticks']<=short['view']['duration_ticks'] and not list(folder.glob('*.pt'))
    before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
    assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    aliases=read(folder/'selected_input_aliases.json');assert aliases['restored'] and aliases['selected_grid_index']==121 and aliases['reference']==str(probe.REFERENCE)
    native=read(folder/'native_effort_readback.json')
    assert native==read(probe.acquisition.PRELEARNING/'runs/pinky_reference/native_effort_readback.json')
    contract=read(folder/'training_contract.json');assert contract['native_backend']['diagnostic_native_effort']==native
    evaluation=read(folder/'evaluation.json');episodes=evaluation['episodes']
    assert evaluation['assigned_quotas']==[1]*4 and grid.complete(episodes,4) and evaluation['policy_performance'] is False
    assert evaluation['summary']==summary(episodes) and all(len(e['reward_components'])==9 for e in episodes)
    acceptance=probe.cap.repro.acceptance(episodes)
    assert read(folder/'reproduction_acceptance.json')['acceptance']==acceptance
    provider=read(folder/'action_provider.json');assert provider['control']=='reference' and provider['NN'] is False and provider['training_updates']==0
    meta=read(folder/'trace_metadata.json');assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
    with np.load(track(folder/'trace_env0_episode0.npz')) as saved:t=dict(saved)
    helper=module('pinky_fresh_trace_helper',probe.acquisition.PRELEARNING/'analysis/analyze.py');track(Path(helper.__file__))
    trace=helper.trace_audit(t,metadata,config,episodes,'reference',contract['action']['target_contract'])
    qids=[metadata['joint_names'].index(n) for n in short['learned_action_names']]
    targets=t['target'][:,qids];lower=np.array(native['actual_native_PD105']['lower'])[qids];upper=np.array(native['actual_native_PD105']['upper'])[qids]
    assert np.isfinite(targets).all() and ((targets>=lower-2e-6)&(targets<=upper+2e-6)).all()
    rate=float(abs(np.diff(targets,axis=0)).max()) if len(targets)>1 else 0.
    assert rate<=4/60+2e-6
    hold=t['time_s']>=reference['ramp_s'];np.testing.assert_allclose(targets[hold],np.broadcast_to(row['target_rad'],targets[hold].shape),rtol=0,atol=2e-6)
    source=short['view']['source_target'];audible=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])[1]
    lh=[]
    for i,name in enumerate(metadata['body_names']):
        if name.startswith('human/LH:'):
            force=np.linalg.norm(t['net_body_force_n'][audible,i],axis=-1)
            usable=bool(len(force)) and bool(np.isfinite(force).all())
            lh.append(dict(body=name,samples=len(force),mean_N=float(force.mean()) if usable else None,p95_N=float(np.percentile(force,95)) if usable else None,max_N=float(force.max()) if usable else None,
                unavailable_reason=None if usable else '음중미노출 또는 비유한 native force; 추정하지않음'))
    original=read(probe.REVIEW.parent/'comparison.json')
    prior=read(probe.acquisition.REVIEW.parent/'comparison.json')['cases']
    reused=dict(grid_selected121=original['focus']['121'],grid_baseline112=original['focus']['112'],
        original_reference4=prior['pinky_reference'],original_zero4=prior['pinky_zero'])
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    grid.write(out/'comparison.json',dict(new_first_attempts=4,episodes=episodes,summary=evaluation['summary'],acceptance=acceptance,
        env0_trace=trace,env0_audible_LH_body_resultants=lh,selected_target_max_delta_rad=rate,
        target_rate_scope='stored endpoint-to-endpoint only; t0 target not saved',reused_comparisons=reused,
        scope='출처별 별도 실행;grid121env62!=freshenv0;4환경seed7!=4seed;원zero에서새reference사용안함'))
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,
        original_acceptance_unchanged=True,all4_first_attempts_including_failures=True,native105_cap90pairs=True,all_scenes_closed=True,
        known_limits=['env0/60Hz상세만;nativeqd/다른3환경상세힘추정없음','nearest!=anycandidate동일점;sample/normalcos미저장·tie한계유지','몸체순힘!=접촉쌍압력/모터토크','고정기타scripted/noNN;손목/팔feedback변화로인과단정불가']))
    fmt=lambda a:', '.join('%.4f'%x for x in a)
    p=trace.get('phases',{}).get('audible',{});m=p.get('metric_mean')
    lines=['# 소지121 새4시도 재현','', '기존grid의1시도와분리한새4첫시도(실패포함)이다. 원acceptance는 **%s** 이다.'%('PASS' if acceptance['passed'] else '미달'),'',
        '| 달성/4 | 평균 clean/wrong | 물리/손목실패 |','|---:|---:|---:|',
        '| %d/4 | %.6f/%.6f | %d/%d |'%(acceptance['achieved'],acceptance['mean_clean'],acceptance['mean_wrong'],acceptance['physical_failures'],acceptance['wrist_failures']),'',
        'env0 음중 actual4°: %s; target4°: %s; 세마디순힘평균N: %s; 손목mm/°: %s.'%(fmt(m[:4]) if m else '미노출',fmt(m[4:8]) if m else '미노출',fmt(m[12:15]) if m else '미노출',fmt(m[15:17]) if m else '미노출'),'',
        'candidate/wrong·CPU6gate/오현·오프렛·arm actionbound 요약은 comparison.json에기록했다. 다른3환경상세힘/nativeqd는없으며추정하지않았다. 원240Hz음원장/9보상을60Hz기하로재지급하지않았다.','',
        '| env0 LH body | 음중표본 | 평균/p95/최대 N |','|---|---:|---:|']
    for body in lh:lines.append('| %s | %d | %s |'%(body['body'],body['samples'],fmt([body['mean_N'],body['p95_N'],body['max_N']]) if body['mean_N'] is not None else '미노출/미확인'))
    lines+=['','기존소지reference4/zero4·gridbaseline112·gridselected121은별도출처로보존했다. 같은seed7의4환경이지4seed가아니다. 새reference는sourceactual이아닌선정유한목표이며zero명령에서는사용하지않는다. body순힘은접촉쌍/현압력/모터토크가아니며고정기타/noNN재현을정책학습·자유기타·생산채택성과로확대하지않는다.']
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print(json.dumps(dict(completed=True,acceptance=acceptance)))


if __name__=='__main__':main()
