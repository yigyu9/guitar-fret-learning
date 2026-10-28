"""New index112 fresh4 audit, with explicitly reused reviewed middle114 records; CPU only."""
import argparse
import csv
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
spec=importlib.util.spec_from_file_location('fresh112_analysis_probe',BASE/'probe.py')
probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
grid=probe.grid;CAP=probe.acquisition.CAP_ROOT


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed',action='store_true');args=parser.parse_args()
    if not args.root_completed:
        print('Prepared only; no actual result read. Wait for root v2 exit.');return
    sys.path.insert(0,str(grid.ROOT))
    out=HERE/'results_v1';probe.cap.reject_existing(out)
    inputs,verified={},{}
    def track(p):
        p=Path(p);inputs[str(p)]=grid.sha(p);return p
    def read(p):return grid.read(track(p))
    def pins(values):
        for p,h in values.items():
            if p not in verified:verified[p]=grid.sha(p)
            assert verified[p]==h,p
    paths,selected=probe.grid_gate()
    assert selected==dict(index=112,middle=114)
    for p in paths:track(p)
    for root in (probe.BASE/'analysis/results_v1',CAP/'analysis/results_v1'):
        review=read(root/'review.json');assert review['verdict']=='PASS' and not review['findings'];pins(review['reviewed_sha256'])
        verification=read(root/'verification.json')
        for key in ('input_sha256','verified_input_sha256'):pins(verification[key])
    seal=read(BASE/'preparation_seal.json');assert seal['independent_review']=='passed_no_findings' and seal['selected_grid_indices']==selected
    pins(seal['input_pins']);prep=read(BASE/'review.json');assert prep['verdict']=='PASS' and not prep['findings'];pins(prep['reviewed_sha256'])
    launcher=read(BASE/'01_launcher.json');assert launcher['completed'] and launcher['returncode']==0
    assert len(launcher['children'])==1 and launcher['children'][0]['finger']=='index' and launcher['children'][0]['returncode']==0
    assert read(BASE/'01_index_launcher.json')['returncode']==0
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    torch.set_num_threads(1)
    folder=BASE/'runs/index';old=CAP/'runs/index'
    doc=read(BASE/'cpu_inputs/index_targets.json');decl=read(grid.HERE/'cpu_inputs/index_grid.json')
    assert doc['selected_grid_index']==112 and doc['selected_offset_deg']==[0,0,0,0]
    assert doc['selected_target_rad']==decl['rows'][112]['target_rad']==doc['original_reference_target_rad']
    assert len(doc['rows'])==4 and all(r['target_rad']==doc['selected_target_rad'] and r['grid_index']==112 for r in doc['rows'])
    config=read(folder/'settings.json');assert config==read(BASE/'cpu_inputs/index_settings.json')==grid.settings('index',4)
    assert config==read(old/'settings.json')
    report,scene=read(folder/'report.json'),read(folder/'gpu_scene_final.json')
    assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored','no_NN_checkpoint'))
    assert report['failure'] is None and report['close_failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
    assert report['selected_grid_index']==112 and report['assigned_first_attempts']==4
    aliases=read(folder/'selected_input_aliases.json');assert aliases['restored'] and aliases['selected_grid_indices']==selected
    provenance=read(folder/'selection_provenance.json');assert provenance['selected_grid_index']==112 and provenance['original_acceptance_unchanged']
    assert scene['closed'] and scene['environment_count']==4 and scene['hand_collision']['enabled_distinct_finger_pairs']==90
    assert scene['hand_collision_native_readback_environments']==4 and scene['physics_steps']==report['resources']['physics_steps']==4*report['resources']['control_ticks']
    assert scene['diagnostic_guitar_mode']=='fixed' and scene['physx_use_gpu'] and scene['use_gpu_pipeline']
    native=read(folder/'native_effort_readback.json');assert native==read(old/'native_effort_readback.json')
    before,after=read(folder/'inputs_before.json'),read(folder/'inputs_after.json');pins(before)
    assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
    contract=read(folder/'training_contract.json');assert contract==read(old/'training_contract.json')
    control=contract['action']['target_contract']
    evaluation=read(folder/'evaluation.json');statistics=read(folder/'statistics.json');episodes=evaluation['episodes'];rows=statistics['rows']
    assert grid.complete(episodes,4) and evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False
    assert evaluation['acceptance']==probe.cap.repro.acceptance(episodes) and evaluation['summary']==summary(episodes)
    for e,s in zip(episodes,rows):
        r=doc['rows'][e['env_id']];assert e['env_id']==s['env_id'] and e['attempt_id']==s['attempt_id']==r['attempt_id'] and e['grid_index']==s['grid_index']==112
        assert e['selected_target_count']==1 and e['target_id']==doc['source_target_id'] and len(e['reward_components'])==9
        assert sum(p['samples'] for p in s['phases'].values())==e['steps']
    metadata,_=fixture(1);meta=read(folder/'trace_metadata.json');assert meta['env_id']==0 and meta['grid_index']==112
    assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
    t=dict(np.load(track(folder/meta['file'])));assert len(t['time_s'])==episodes[0]['steps'] and np.all(np.diff(np.rint(t['time_s']*240))==4)
    assert all(np.isfinite(a).all() for a in t.values())
    qids=[meta['joint_names'].index(n) for n in doc['joint_names']];assert meta['selected_native_qd_names']==doc['joint_names'] and t['selected_native_qd'].shape==(len(t['time_s']),4)
    bids=[meta['body_names'].index('human/LH:index'+str(i)) for i in (1,2,3)];wrist,guitar=[meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
    rg=Rotation.from_quat(t['body_state'][:,guitar,3:7]);pos=t['body_state'][:,guitar,:3]+rg.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
    rot=(rg*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
    data=np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),np.linalg.norm(t['net_body_force_n'][:,bids],axis=-1),t['surface_distance_m']*1000,t['surface_height_m']*1000,np.zeros(len(t['time_s'])),np.linalg.norm(pos,axis=-1)*1000,np.rad2deg(rot)]
    env=ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
    def snapshot(k):return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
    env.reset([0],snapshot(0));gates=[];height=[]
    for k,now in enumerate(t['time_s']):
        env.clock[0]=round(now*240);env._snapshot(snapshot(k));j=env.selected_index
        assert bool(env.candidate[0,j])==bool(t['candidate'][k]) and bool(env.wrong[0,j])==bool(t['wrong'][k])
        assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][k])<1e-6
        height.append(float(env.surface_height[0,j])-float(t['surface_height_m'][k]));data[k,17]=float(env.surface_alignment[0,j])
        gates.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
    source=config['song']['short_learning']['view']['source_target'];masks=grid.phase_masks(t['source_time_s'],source['onset_s'],source['end_s']);cosine={};phases={}
    for phase,mask in zip(statistics['phase_order'],masks):
        p=rows[0]['phases'][phase];assert int(mask.sum())==p['samples'] and np.array_equal(np.asarray(gates)[mask].sum(0),p['gate_counts'])
        if not p['samples']:continue
        for key,value in [('mean',data[mask].mean(0)),('min',data[mask].min(0)),('max',data[mask].max(0)),('rms',np.sqrt((data[mask]**2).mean(0)))]:
            ix=[i for i in range(20) if i!=17];np.testing.assert_allclose(value[ix],np.asarray(p[key])[ix],rtol=5e-6,atol=5e-5)
            cosine[phase+'_'+key]=dict(CPU=float(value[17]),saved=p[key][17],residual=float(value[17]-p[key][17]))
        phases[phase]=dict(saved_statistics=p,native_qd_mean_rad_s=t['selected_native_qd'][mask].mean(0).tolist(),native_qd_max_abs_rad_s=abs(t['selected_native_qd'][mask]).max(0).tolist())
    armnames=[g+'_'+a for g in ('L_Thorax','L_Shoulder','L_Elbow','L_Wrist') for a in 'xyz'];armids=[meta['joint_names'].index(n) for n in armnames];actionids=[control['action_order'].index(n) for n in armnames]
    low=np.asarray(control['action_lower_rad'])[actionids];high=np.asarray(control['action_upper_rad'])[actionids];audible=masks[1];arm={}
    for kind,values in [('requested',t['wrist_requested_arm_rad']),('native_target',t['target'][:,armids]),('actual',t['q'][:,armids])]:
        values=values[audible];arm[kind]=dict(mean_deg=np.rad2deg(values).mean(0).tolist(),lower_within_or_beyond_1urad_counts=(values<=low+1e-6).sum(0).tolist(),upper_within_or_beyond_1urad_counts=(values>=high-1e-6).sum(0).tolist()) if len(values) else None
    arm['order']=armnames;arm['target_minus_actual_mean_deg']=np.rad2deg((t['target']-t['q'])[audible][:,armids]).mean(0).tolist() if audible.any() else None
    arm['target_minus_actual_max_abs_deg']=np.rad2deg(abs((t['target']-t['q'])[audible][:,armids])).max(0).tolist() if audible.any() else None
    lh=[]
    for b,name in enumerate(meta['body_names']):
        if name.startswith('human/LH:'):
            force=t['net_body_force_n'][audible,b];norm=np.linalg.norm(force,axis=-1);lh.append(dict(body=name,samples=int(audible.sum()),mean_N=float(norm.mean()) if len(norm) else None,max_N=float(norm.max()) if len(norm) else None,mean_world_xyz_N=force.mean(0).tolist() if len(norm) else None,mean_guitar_xyz_N=rg[audible].inv().apply(force).mean(0).tolist() if len(norm) else None))
    gm=read(probe.BASE/'runs/index/trace_metadata.json');gt=dict(np.load(track(probe.BASE/'runs/index/trace_grid000112.npz')))
    docrow=decl['rows'][112];assert docrow['env_id']!=0 and 112 in gm['grid_indices']
    common,a,b=np.intersect1d(np.rint(t['time_s']*240).astype(int),np.rint(gt['time_s']*240).astype(int),return_indices=True)
    assert np.array_equal(t['target'][a][:,qids],gt['target'][b][:,qids])
    # Reuse the reviewed middle data; no new middle scene or perendpoint replay.
    middlefolder=CAP/'runs/middle';middle=read(middlefolder/'evaluation.json');middle_doc=read(CAP/'cpu_inputs/middle_targets.json')
    assert middle_doc['selected_grid_index']==114 and middle['acceptance']==probe.cap.repro.acceptance(middle['episodes']) and middle['acceptance']['passed']
    assert middle_doc['selected_target_rad']==read(grid.HERE/'cpu_inputs/middle_grid.json')['rows'][114]['target_rad']
    assert read(middlefolder/'settings.json')==read(CAP/'cpu_inputs/middle_settings.json')==grid.settings('middle',4)
    assert native['actual_native_PD105']==read(middlefolder/'native_effort_readback.json')['actual_native_PD105']
    reused=read(CAP/'analysis/results_v1/comparison.json')['trace_audits']['middle_cap025']
    arm_middle=read(CAP/'analysis/results_v1/arm_bounds.json')['cases']['middle_cap025']
    with track(CAP/'analysis/results_v1/LH_body_forces.csv').open() as f:middle_lh=[r for r in csv.DictReader(f) if r['finger']=='middle' and r['condition']=='cap025' and r['phase']=='audible']
    assert len(lh)==len(middle_lh)==22 and not (BASE/'runs/middle').exists() and not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve());track(HERE/'PLAN.md');out.mkdir()
    grid.write(out/'comparison.json',dict(index_new=dict(source=str(folder),acceptance=evaluation['acceptance'],episodes=episodes,statistics=statistics,env0_phases=phases,env0_arm=arm,env0_LH=lh),
        middle_reused=dict(source=str(middlefolder),review=str(CAP/'analysis/results_v1/review.json'),acceptance=middle['acceptance'],episodes=middle['episodes'],env0_audit=reused,env0_arm=arm_middle,env0_LH=middle_lh),
        grid112_comparison=dict(source=str(probe.BASE/'runs/index'),grid_env_id=docrow['env_id'],new_env_id=0,common_clock_count=len(common),selected_target_exact=True,selected_actual_max_abs_difference_deg=float(np.rad2deg(abs(t['q'][a][:,qids]-gt['q'][b][:,qids])).max()))))
    grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,new_index_first_attempts=4,reused_middle_first_attempts=4,
        native105_cap_and90pairs=True,aliases_restored=True,candidate_wrong_each_endpoint_match=True,six_phase_gate_counts_match=True,non_cosine19statistics_match=True,
        height_residuals_over_1um=[dict(endpoint=k,CPU_minus_saved_m=v) for k,v in enumerate(height) if abs(v)>1e-6],normal_cos_statistics=cosine,
        known_limits=['newindex4 vs explicitly reused middle4; not8new scenes','same seed7 fourenvs, notfourseeds; gridenvID differs','60Hz env0 detailed only; no240Hz maxima','native qd isvelocity coordinate, no MCP2 qposderivative','native argmin/normalcos endpoint unrecorded; residual is not pressure witness','body resultant isnot contactpair/pressure/isolated motor torque; armfeedback andnonselected12 interact']))
    lines=['# 새 검지112 네첫시도 재현','', '| 출처 | 달성/전체첫시도 | 평균clean/wrong | 물리/손목실패 | 원acceptance |','|---|---:|---:|---:|---|']
    for label,ev in [('새v2 index112',evaluation),('기존cap middle114 재사용',middle)]:
        z=ev['acceptance'];lines.append('| %s | %d/4 | %.4f/%.4f | %d/%d | %s |'%(label,z['achieved'],z['mean_clean'],z['mean_wrong'],z['physical_failures'],z['wrist_failures'],z['passed']))
    lines+=['','검지는 새4첫시도 모두(실패포함), 중지는 기존검수4/4를 출처분리해 재사용했다. 중지새GPU는없다. v1 import-order 실패는 보존된별도실행이며 이음악분모가아니다. 같은seed7의4환경이지4seed가아니다. 원음원장/9보상·전체4환경 경량통계는 comparison.json에 보존한다.','',
        '| 새index env0 phase | samples | body1/2/3 평균 N | actual4 ° | target4 ° | wrist mm/° | gate counts |','|---|---:|---|---|---|---|---|']
    for phase,value in phases.items():
        z=value['saved_statistics'];m=z['mean'];fmt=lambda x:', '.join('%.5f'%a for a in x);lines.append('| %s | %d | %s | %s | %s | %s | %s |'%(phase,z['samples'],fmt(m[12:15]),fmt(m[:4]),fmt(m[4:8]),fmt(m[18:20]),'/'.join(map(str,z['gate_counts']))))
    lines+=['','LH 전체22body의 음중mean/max와실제guitar기준평균벡터, 팔12요청/native target/actual 경계·오차는comparison.json에있다. 미노출시도는힘0으로대체하지않는다. 경계목록1µrad는진단표기이며원판정을바꾸지않는다. request는해당tick물리이전·actual/target은끝점이다. native qd는속도좌표이며 MCP2 qpos미분이아니다.','',
        '원capgrid112(env%d)와새env0는동일실행/bitexact상태를가정하지않는다. 공통%dclock의선택target은exact이며 actual4 최대차이는%.6f°다. 상세자료는60Hz끝점이며 nearest sample/normalcos native perendpoint미저장·원tie한계는그대로다. 몸체순힘은접촉쌍·현압력이나motor torque상한인증이아니며고정teacher/고정기타의성과를자유손production으로확대하지않는다.'%(docrow['env_id'],len(common),float(np.rad2deg(abs(t['q'][a][:,qids]-gt['q'][b][:,qids])).max()))]
    (out/'RESULTS.md').write_text('\n'.join(lines)+'\n');print('Actual CPU audit written:',out)


if __name__=='__main__':main()
