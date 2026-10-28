"""Completed v2/v3 fixed-teacher comparison; CPU evidence only, never launches native."""
import argparse
import ast
import copy
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
FIX = HERE.parent
DIAG = FIX.parents[1]
ROOT = DIAG.parents[2]
ARCHIVE = ROOT/'guitar_learning/archive/20261027_before_wrist_position_candidate_v3'
BASES = dict(v2_index=DIAG/'05_verified_fixes/wrist_position_jacobian_v2/native_precheck',
    v2_middle=DIAG/'05_verified_fixes/wrist_position_jacobian_v2/other_finger_regression',
    v3=FIX/'native_precheck')
CONTROLS = ('reference','zero','random')


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preserved_input(path, expected, archived):
    source = Path(path)
    if source.is_file() and sha(source) == expected:
        return dict(path=path, sha256=expected, verified_at=str(source), source='unchanged')
    row = archived.get(path)
    if row and row['sha256'] == expected:
        saved = ARCHIVE/row['path']
        if saved.is_file() and saved.stat().st_size == row['bytes'] and sha(saved) == expected:
            return dict(path=path, sha256=expected, verified_at=str(saved), source='before_candidate_v3 archive')
    raise ValueError('Input differs from both actual pin and named archive: '+path)


def v3_recurrence(trace, meta, contract, short):
    """Independent NumPy reconstruction from recorded candidate; no J reconstruction."""
    import numpy as np
    from guitar_learning.core.control import LEFT_ARM_NAMES
    control = contract['action']['target_contract']
    arm = [meta['joint_names'].index(n) for n in LEFT_ARM_NAMES]
    action_ids = [control['action_order'].index(n) for n in LEFT_ARM_NAMES]
    reference = np.asarray(control['reference105_rad'])[arm]
    low, high = [np.asarray(control[k])[action_ids] for k in ('action_lower_rad','action_upper_rad')]
    rate = np.asarray(control['rate_rad_s'])[arm]/60
    alpha = np.asarray(control['smoothing_alpha'])[action_ids]
    assert np.allclose(alpha,.2,atol=1e-8,rtol=0) and short['wrist_control']['schema'].endswith('.v3')
    goal = np.array([short['teacher']['arm_targets_rad'][n] for n in LEFT_ARM_NAMES])
    fraction = np.minimum(trace['time_s']/short['teacher']['ramp_s'],1)
    base = reference+fraction[:,None]*(goal-reference)
    request = trace['wrist_requested_arm_rad']
    previous = np.concatenate((reference[None],request[:-1]))
    memory = np.concatenate((np.zeros((1,12)),request[:-1]-base[:-1]))
    proposal = base+memory
    candidate = trace['wrist_candidate_arm_rad']
    active = trace['wrist_feedback_active'].astype(bool)
    assert not active[0] and active[1:].all()
    step = short['wrist_control']['correction_step_rad']
    delta = np.where(active[:,None],np.clip(candidate-proposal,-step,step),0)
    predicted_request = np.clip(np.clip(proposal+delta,previous-rate,previous+rate),low,high)
    target = trace['target'][:,arm]
    previous_target = np.concatenate((reference[None],target[:-1]))
    action = np.clip(trace['executed_action'][:,action_ids],-1,1)
    decoded = reference+np.where(action >= 0,high-reference,reference-low)*action
    predicted_target = np.clip(np.clip(previous_target+alpha*(decoded-previous_target),
        previous_target-rate,previous_target+rate),low,high)
    return dict(base=base, proposal=proposal, candidate=candidate,
        precontrol_actual_arm_k_ge_1=trace['q'][:-1,arm], raw_dq_k_ge_1=candidate[1:]-trace['q'][:-1,arm],
        requested_delta_residual=delta-trace['wrist_requested_delta_rad'], request_residual=predicted_request-request,
        native_target_residual=predicted_target-target, inverse_codec_residual=decoded-request,
        inactive_candidate_proposal_residual=candidate[~active]-proposal[~active],
        scope='env0 60Hz; k>=1 precontrol q is prior endpoint; candidate is virtual/unclipped, not native reachability; no v2 recurrence claim')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed',action='store_true')
    args = parser.parse_args()
    if not args.root_completed:
        print('No result inputs read. Root actual8stage completion required.')
        return
    sys.path.insert(0,str(ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.core.control import LEFT_ARM_NAMES
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.gpu.wrong_press import WRONG_PRESS_CONTRACT
    torch.set_num_threads(1)
    out = HERE/'results_v1'
    if out.exists() or out.is_symlink(): raise FileExistsError(str(out))
    hashes, verified, stage_checks, initial_models, settings0, contracts0 = {}, {}, [], {}, {}, {}
    def remember(path):
        hashes[str(path)] = sha(path)
        return read(path)
    manifest = remember(ARCHIVE/'manifest.json')
    assert len(manifest['files']) == manifest['files_count'] == 521
    archived = {str(ROOT/r['path']):r for r in manifest['files']}
    for row in manifest['files']:
        path = ARCHIVE/row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256']
    def verify(pins):
        for path, expected in pins.items():
            key = (path,expected)
            if key not in verified: verified[key] = preserved_input(path,expected,archived)
    module_spec = importlib.util.spec_from_file_location('candidate_v3_actual_precheck',BASES['v3']/'run_precheck.py')
    current = importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(current)
    seal3 = remember(BASES['v3']/'preparation_seal.json')
    assert len(seal3['input_pins']) == 700 and seal3['independent_review'] == 'passed_no_findings'
    current.verify_seal(seal3)
    native_current = {j['name']:current.validate(j,seal3) for j in current.jobs()}
    for label,base in BASES.items():
        launcher, report = remember(base/'01_launcher.json'),remember(base/'runs/report.json')
        assert launcher['returncode'] == 0 and report['completed']
        stages = report['stages']; assert len(stages) == dict(v2_index=4,v2_middle=12,v3=8)[label]
        seal = remember(base/'preparation_seal.json')
        assert seal['independent_review'] == 'passed_no_findings'
        verify(seal['input_pins'])
        for stage in stages:
            assert stage['launcher_returncode'] == 0
            folder = base/'runs'/stage['name']
            child, scene = remember(folder/'report.json'),remember(folder/'gpu_scene_final.json')
            before, after = remember(folder/'inputs_before.json'),remember(folder/'inputs_after.json')
            assert child['completed'] and child['closed'] and child['failure'] is None
            assert not child['changed_inputs'] and not child['unpinned_project_sources']
            assert after['verified'] and before == after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
            assert scene['closed'] and scene['environment_count'] == 4 and scene['diagnostic_guitar_mode'] == 'fixed'
            assert scene['physx_use_gpu'] and scene['use_gpu_pipeline']
            verify(before)
            stage_checks.append(dict(case=label,stage=stage['name'],closed=True,pins=len(before)))
        for finger in (('index','middle') if label == 'v3' else (label[3:],)):
            folder = base/'runs'/(finger+'_initial')
            checkpoint = folder/'initial.pt'; hashes[str(checkpoint)] = sha(checkpoint)
            model = torch.load(checkpoint,map_location='cpu',weights_only=False)
            assert model['updates'] == 0 and len(model['model']) == 73
            setting, contract = remember(folder/'settings.json'),remember(folder/'training_contract.json')
            assert setting == model['metadata']['settings'] and setting['seed'] == 7 and setting['updates'] == 1 and setting['num_envs'] == 4
            assert setting['song']['short_learning']['wrist_control']['schema'].endswith('.v3' if label == 'v3' else '.v2')
            initial_models[label+'_'+finger] = model['model']
            settings0[label+'_'+finger], contracts0[label+'_'+finger] = setting,contract
    model_equality = {}
    for finger in ('index','middle'):
        old,new = initial_models['v2_'+finger+'_'+finger],initial_models['v3_'+finger]
        model_equality[finger] = {key: key in new and torch.equal(value,new[key]) for key,value in old.items()}
        assert set(old) == set(new) and len(old) == 73 and all(model_equality[finger].values())
        prior = settings0['v2_'+finger+'_'+finger]
        normalized = copy.deepcopy(settings0['v3_'+finger])
        normalized['song']['short_learning']['wrist_control'] = prior['song']['short_learning']['wrist_control']
        assert normalized == prior
        prior_contract = contracts0['v2_'+finger+'_'+finger]
        normalized_contract = copy.deepcopy(contracts0['v3_'+finger])
        normalized_contract['task']['short_learning']['wrist_control'] = prior_contract['task']['short_learning']['wrist_control']
        normalized_contract['task']['song']['short_learning']['wrist_control'] = prior_contract['task']['song']['short_learning']['wrist_control']
        assert normalized_contract == prior_contract
    # Runtime module changed only its control pool; the CPU contact environment class is byte-equivalent in AST.
    runtime_rel = 'guitar_learning/tool/experiments/short_finger_learning/runtime.py'
    oldtree,newtree = [ast.parse(p.read_text()) for p in (ARCHIVE/runtime_rel,ROOT/runtime_rel)]
    oldclass,newclass = [next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name == 'ShortEnvironment') for tree in (oldtree,newtree)]
    assert ast.dump(oldclass,include_attributes=False) == ast.dump(newclass,include_attributes=False)
    metadata,_ = fixture(1)
    rows,traces,recurrences,curves = [],{},{},{}
    def stat(value):
        value = np.asarray(value)
        return dict(min=value.min(axis=0).tolist(),median=np.median(value,axis=0).tolist(),max=value.max(axis=0).tolist())
    for version in ('v2','v3'):
        for finger in ('index','middle'):
            label = version if version == 'v3' else version+'_'+finger
            base = BASES[label]
            for control in CONTROLS:
                name = version+'_'+finger+'_'+control
                folder = base/'runs'/(finger+'_'+control)
                settings,contract,meta,evaluation = [remember(folder/p) for p in ('settings.json','training_contract.json','trace_metadata.json','evaluation.json')]
                assert settings == settings0[label+'_'+finger] and contract == contracts0[label+'_'+finger]
                initial = base/'runs'/(finger+'_initial')/'initial.pt'
                before = read(folder/'inputs_before.json'); assert before[str(initial)] == sha(initial)
                assert str(initial.with_name('final.pt')) not in before
                assert evaluation['condition'] == control and evaluation['policy_performance'] is False
                episodes = evaluation['episodes']
                assert evaluation['assigned_quotas'] == [1]*4 and len(episodes) == 4 and sorted(e['env_id'] for e in episodes) == list(range(4))
                assert all(e['selected_target_count'] == 1 for e in episodes) and evaluation['summary'] == summary(episodes)
                rows.append(dict(version=version,finger=finger,control=control,achieved=sum(e['achieved'] for e in episodes),**evaluation['summary']))
                short = settings['song']['short_learning']; view = short['view']
                assert all(e['target_id'] == short['teacher']['source_target_id'] for e in episodes)
                assert meta['joint_names'] == metadata['joint_names'] and meta['body_names'] == metadata['body_names']
                assert meta['wrist_control'] == short['wrist_control']
                path = folder/'trace_env0_episode0.npz'; hashes[str(path)] = sha(path); t = np.load(path)
                local = t['time_s']; assert abs(local[0]-1/60) < 1e-6 and np.allclose(np.diff(local),1/60,atol=5e-7)
                assert np.max(abs(t['source_time_s']-local-view['score_offset_s'])) < 1e-9
                arm = [meta['joint_names'].index(n) for n in LEFT_ARM_NAMES]
                selected = [meta['joint_names'].index(n) for n in short['learned_action_names']]
                wrist,guitar,distal,thumb = [meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar','human/LH:'+finger+'3','human/LH:thumb3')]
                instrument = Rotation.from_quat(t['body_state'][:,guitar,3:7])
                actual_G = instrument.inv().apply(t['body_state'][:,wrist,:3]-t['body_state'][:,guitar,:3])
                actual_R = instrument.inv()*Rotation.from_quat(t['body_state'][:,wrist,3:7])
                data = dict(wrist_position_error_mm=np.linalg.norm(t['wrist_goal_G_m']-actual_G,axis=1)*1000,
                    wrist_rotation_error_deg=np.rad2deg((Rotation.from_quat(t['wrist_goal_G_xyzw']).inv()*actual_R).magnitude()),
                    nearest_pad_distance_mm=1000*t['surface_distance_m'],nearest_signed_height_mm=1000*t['surface_height_m'],
                    distal_body_resultant_N=np.linalg.norm(t['net_body_force_n'][:,distal],axis=1),
                    thumb_distal_resultant_N=np.linalg.norm(t['net_body_force_n'][:,thumb],axis=1),
                    actual_selected_deg=np.rad2deg(t['q'][:,selected]),target_selected_deg=np.rad2deg(t['target'][:,selected]),
                    selected_target_actual_deg=np.rad2deg((t['target']-t['q'])[:,selected]),
                    arm_request_target_max_deg=np.rad2deg(abs(t['wrist_requested_arm_rad']-t['target'][:,arm])).max(1),
                    arm_target_actual_max_deg=np.rad2deg(abs(t['target'][:,arm]-t['q'][:,arm])).max(1))
                env = ShortEnvironment(metadata,bundle=settings['song_training']['bundle'],song=settings['song'],skill=settings['finger_skill'],device='cpu')
                def snapshot(i):
                    return dict(q=torch.tensor(t['q'][i:i+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][i:i+1]),
                        body_state=torch.tensor(t['body_state'][i:i+1]),contact_force=torch.tensor(t['net_body_force_n'][i:i+1]))
                env.reset([0],snapshot(0)); gates=[]
                for i,now in enumerate(local):
                    env.clock[0] = round(now*240); env._snapshot(snapshot(i)); j=env.selected_index
                    assert bool(env.candidate[0,j]) == bool(t['candidate'][i]) and bool(env.wrong[0,j]) == bool(t['wrong'][i])
                    assert abs(float(env.surface_distance[0,j])-t['surface_distance_m'][i]) < 1e-6
                    assert abs(float(env.surface_height[0,j])-t['surface_height_m'][i]) < 1e-6
                    gates.append(dict(time_s=float(now),loaded=bool(env.surface_body_loaded[0,j]),position=bool(env.contact_geometry[0,j]),
                        position_facing=bool(env.contact_facing[0,j]),positive=bool(env.contact_loaded_target[0,j]),candidate=bool(env.candidate[0,j]),
                        wrong=bool(env.wrong[0,j]),nearest_normal_cos=float(env.surface_alignment[0,j]),
                        wrong_source_flags=env.wrong_source_flags[0,j].tolist(),wrong_source_fret_min=env.wrong_source_fret_min[0,j].tolist(),
                        wrong_source_fret_max=env.wrong_source_fret_max[0,j].tolist()))
                data['nearest_normal_cos'] = np.array([g['nearest_normal_cos'] for g in gates])
                phases = dict(before=local < view['local_onset_s']-1e-9,
                    audible=(local >= view['local_onset_s']-1e-9)&(local <= view['local_end_s']+1e-9),after=local > view['local_end_s']+1e-9,
                    post_ramp=local >= 2-1e-9)
                phase_stats={}
                for phase,mask in phases.items():
                    ids=np.flatnonzero(mask)
                    phase_stats[phase] = dict(endpoints=len(ids),statistics={k:stat(v[mask]) for k,v in data.items()} if len(ids) else {},
                        gate_counts={key:sum(gates[i][key] for i in ids) for key in ('loaded','position','position_facing','positive','candidate','wrong')},
                        wrong_source_counts_10body_3cause=np.asarray([g['wrong_source_flags'] for g in gates],dtype=int)[mask].sum(0).tolist())
                traces[name] = dict(view=view,phases=phase_stats,gates=gates,selected_names=short['learned_action_names'],
                    physical_string_1_based=view['source_target']['string']+1,note_ledgers=episodes,stored_endpoints=len(local),
                    wrong_source_body_order=[meta['body_names'][int(i)] for i in env.finger_indices],
                    wrong_source_cause_order=WRONG_PRESS_CONTRACT['causes'])
                if control == 'zero':
                    assert np.count_nonzero(t['policy_action'][:,short['learned_action_indices']]) == 0
                    assert np.max(np.ptp(t['target'][:,selected],axis=0)) == 0
                if version == 'v3':
                    assert meta['wrist_candidate_arm_scope'] == short['wrist_control']['candidate_arm_scope']
                    assert meta['wrist_requested_delta_scope'] == short['wrist_control']['requested_delta_scope']
                    recurrence = v3_recurrence(t,meta,contract,short)
                    residuals = {k:float(abs(v).max()) if v.size else 0. for k,v in recurrence.items() if k.endswith('_residual')}
                    assert max(residuals.values()) < 2e-6,(name,residuals)
                    pre_guitar = Rotation.from_quat(t['body_state'][:-1,guitar,3:7])
                    goal_W = t['body_state'][:-1,guitar,:3]+pre_guitar.apply(t['wrist_goal_G_m'][1:])
                    goal_R = pre_guitar*Rotation.from_quat(t['wrist_goal_G_xyzw'][1:])
                    pre_error = np.c_[goal_W-t['body_state'][:-1,wrist,:3],.1*(goal_R*Rotation.from_quat(t['body_state'][:-1,wrist,3:7]).inv()).as_rotvec()]
                    feedback_residual = float(abs(pre_error-t['wrist_pose_error_world'][1:]).max())
                    assert feedback_residual < 2e-6
                    recurrences[name] = dict(max_abs_residual_rad=residuals,precontrol_pose_error_residual=feedback_residual,
                        inactive_endpoints=local[~t['wrist_feedback_active'].astype(bool)].tolist(),
                        active_candidate_minus_precontrol_actual_deg=stat(np.rad2deg(recurrence['raw_dq_k_ge_1'])),
                        phases={p:dict(proposal_candidate_max_gap_deg=stat(np.rad2deg(abs(recurrence['candidate']-recurrence['proposal'])).max(1)[m]),
                            requested_delta_max_deg=stat(np.rad2deg(abs(t['wrist_requested_delta_rad'])).max(1)[m])) for p,m in phases.items() if m.any()},
                        scope=recurrence['scope'])
                if control == 'reference': curves[name]=dict(time=local,**data)
    assert len(rows)==12 and sum(r['episodes'] for r in rows)==48 and not torch.cuda.is_initialized()
    all_timeline = all(e['reason']=='timeline_complete' for t in traces.values() for e in t['note_ledgers'])
    assert all_timeline and all(row['achieved']==0 for row in rows)
    index_audible = traces['v3_index_reference']['phases']['audible']
    middle_audible = traces['v3_middle_reference']['phases']['audible']
    assert index_audible['endpoints']==11 and index_audible['gate_counts']==dict(loaded=0,position=11,position_facing=11,positive=0,candidate=0,wrong=0)
    assert index_audible['statistics']['distal_body_resultant_N']['max']==0
    assert middle_audible['endpoints']==8 and middle_audible['gate_counts']==dict(loaded=8,position=0,position_facing=0,positive=0,candidate=0,wrong=8)
    wrong_counts=np.asarray(middle_audible['wrong_source_counts_10body_3cause'])
    assert wrong_counts[5,2]==8 and wrong_counts.sum()==8
    assert traces['v3_middle_reference']['wrong_source_body_order'][5]=='human/LH:middle3'
    helper_rels=('gpu/environment.py','gpu/simplified_finger_environment.py','gpu/fingertip_pad.py','gpu/wrong_press.py','tests/test_gpu_environment.py')
    helpers={str(ROOT/'guitar_learning'/r):sha(ROOT/'guitar_learning'/r) for r in helper_rels}
    for path,digest in helpers.items():
        assert all(row['sha256']==digest for row in verified.values() if row['path']==path)
    hashes[str(Path(__file__).resolve())]=sha(Path(__file__).resolve()); hashes[str(HERE/'PLAN.md')]=sha(HERE/'PLAN.md')
    out.mkdir()
    def write(name,value):
        with (out/name).open('x') as stream: json.dump(value,stream,indent=2,ensure_ascii=False,allow_nan=False); stream.write('\n')
    write('comparison.json',dict(summary=rows,env0=traces,v3_recurrence=recurrences,
        scope='12controls/48all first attempts; trace/gates/forces env0 60Hz only; no learned-policy or native-candidate attainability claim'))
    write('verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,CUDA_initialized=False,
        new_launcher_wall_s=read(BASES['v3']/'01_launcher.json')['wall_s'],current_preparation_pins=700,archive_entries_verified=521,
        stage_checks=stage_checks,new_native_current_validations=native_current,initial73_tensor_equality=model_equality,
        only_settings_and_training_contract_change='wrist_control',source_verification=list(verified.values()),
        unchanged_predicate_helper_SHA256=helpers,ShortEnvironment_AST_same_as_archived_v2=True,
        archive_manifest=str(ARCHIVE/'manifest.json'),input_sha256=hashes,historical_strict_checkpoint_reload=False,
        stored_env0_endpoints=sum(t['stored_endpoints'] for t in traces.values()),all_saved_predicates_reproduced=True,
        all48_timeline_complete=all_timeline))
    with (out/'conditions.csv').open('x',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(12,6),sharex='row')
    for i,finger in enumerate(('index','middle')):
        for version in ('v2','v3'):
            curve=curves[version+'_'+finger+'_reference']
            for ax,key in zip(axes[i],('wrist_position_error_mm','nearest_pad_distance_mm','distal_body_resultant_N')):
                ax.plot(curve['time'],curve[key],label=version,lw=1)
                ax.set_title(finger+' / '+key); ax.grid(alpha=.2)
        for ax in axes[i]: ax.axvspan(3,traces['v3_'+finger+'_reference']['view']['local_end_s'],color='green',alpha=.12)
    axes[0,0].legend(); [ax.set_xlabel('local time (s)') for ax in axes[1]]
    fig.tight_layout(); fig.savefig(out/'comparison.png',dpi=140); plt.close(fig)
    text=['# 실제각 후보 v3와 직전 손목 Jacobian v2 비교','',
        '**v3는 검지 reference의 손목 추종을 크게 개선했지만, 검지·중지의 reference/zero/random은 모두0/4다. 손목 기준 도달과 압현 판정은 여전히 분리된다. 중지 reference의 전체4시도 wrong은100%다.**','',
        '같은 seed7·teacher/reference·4환경 첫 시도의 비교다. settings와 training contract 차이는 wrist_control뿐이며 실제 초기73 tensor는 손가락별로 전부 일치한다. scripted/zero/initial random 대조이며 학습성과가 아니다.','',
        '| 버전 | 손가락 | 조건 | 달성/4 | clean | wrong | 물리/손목 실패 |','|---|---|---|---:|---:|---:|---:|']
    for row in rows:
        text.append('| %s | %s | %s | %d | %.2f%% | %.2f%% | %d/%d |'%(row['version'],row['finger'],row['control'],row['achieved'],
            row['mean_clean_fraction']*100,row['mean_audible_wrong_fraction']*100,round(4*row['physical_failure_fraction']),round(4*row['wrist_failure_fraction'])))
    text += ['', '![reference env0 손목·패드·distal 합력](comparison.png)','',
        '아래는 reference의 음 중 env0 저장60Hz 끝점 통계다. 손목·거리·힘·cosine은 중앙값이며 전체4환경의 대표값이나240Hz 극값이 아니다.','',
        '| 버전/손가락 | 끝점 | 손목 mm/도 | postramp 위치max mm | nearest mm | nearest cosine | distal N | loaded/위치/위치+facing/positive/candidate/wrong |',
        '|---|---:|---:|---:|---:|---:|---:|---|']
    for version in ('v2','v3'):
        for finger in ('index','middle'):
            tr=traces[version+'_'+finger+'_reference']; p=tr['phases']['audible']; s=p['statistics']; g=p['gate_counts']
            text.append('| %s/%s | %d | %.4f/%.4f | %.4f | %.4f | %.4f | %.4f | %s |'%(version,finger,p['endpoints'],
                s['wrist_position_error_mm']['median'],s['wrist_rotation_error_deg']['median'],tr['phases']['post_ramp']['statistics']['wrist_position_error_mm']['max'],
                s['nearest_pad_distance_mm']['median'],s['nearest_normal_cos']['median'],s['distal_body_resultant_N']['median'],
                '/'.join(str(g[k]) for k in ('loaded','position','position_facing','positive','candidate','wrong'))))
    text += ['', 'v3 reference의 선택4축(1_x·1_z·2·3) 음 중 env0 중앙값은 다음과 같다.','',
        '| 손가락 | actual q (도) | native target (도) |','|---|---|---|']
    for finger in ('index','middle'):
        s=traces['v3_'+finger+'_reference']['phases']['audible']['statistics']
        text.append('| %s | %s | %s |'%(finger,', '.join('%.3f'%x for x in s['actual_selected_deg']['median']),', '.join('%.3f'%x for x in s['target_selected_deg']['median'])))
    index = traces['v3_index_reference']['phases']['audible']['statistics']
    middle = traces['v3_middle_reference']['phases']['audible']['statistics']
    text += ['',
        '검지 reference env0 음 중11끝점은 위치11/11·위치+facing11/11이지만 loaded0/11이고 distal 합력 min/median/max가 모두0N이다. 이 저장 범위에서는 facing보다 하중 gate 부재로 positive0을 분리할 수 있다. 선택1_x·1_z의 target−actual 중앙값은 각각 %.4f°·%.4f°로 손가락 추종 오차도 남는다. 손목 도달만으로 손가락 압현이 해결됐다고 할 수 없으며, 이 각도 오차를 하중 부재의 단독 원인으로 확정하지 않는다.'%(index['selected_target_actual_deg']['median'][0],index['selected_target_actual_deg']['median'][1]),'',
        '중지 reference env0 음 중8끝점은 loaded8/8이지만 목표 any-sample 위치0/8·positive0/8·wrong8/8이다. 원 wrong source helper는 middle3의 own_wrong_string을8/8, source fret 범위7..7로 기록했고 other_higher·own_wrong_fret는0이었다. 이 flag는 기하·하중 후보 분류이며 실제 접촉상대나 잘못 누른 현 번호를 인증하지 않는다. nearest 높이 중앙값 %.4fmm와 cosine %.4f는 참고값이며 독립 최근접 표본 하나를 any-sample 위치 실패의 단독 원인으로 사용하지 않는다.'%(middle['nearest_signed_height_mm']['median'],middle['nearest_normal_cos']['median'])]
    max_recurrence=max(max(r['max_abs_residual_rad'].values()) for r in recurrences.values())
    text += ['', 'v3의 기록 후보→clip(candidate−proposal)→원 request rate/bounds→executed action decode→native alpha.2/rate/bounds를6trace에서 재구성했다. 최대절대 잔차는 %.3g rad다. k>=1 precontrol q/body는 직전 끝점이며 첫 inactive reset은 candidate=proposal·delta0으로 따로 확인했다. v2 delta에는 이 recurrence를 적용하지 않았다. 후보는 unclipped 가상 관절 위치이며 새 J 캡처나 실제 후보 도달을 주장하지 않는다.'%max_recurrence,'',
        '전체48시도는 모두 timeline_complete였고 음악 수치는 원래240Hz 음 원장이다. 조기 실패가 발생해도4분모에 포함하는 원래 할당을 유지했다. 같은 seed7의 병렬4환경이므로 독립4seed로 해석하지 않는다. gate는 각 env0 저장60Hz 끝점만 현재 ShortEnvironment._snapshot→원 contact helper로 재생했다. 위치 gate와 위치+facing을 구분하며 nearest cosine/거리 표본을 any-sample witness로 쓰지 않았다. JSON은 음 전·중·후/postramp 선택각·target/actual gap·표면·합력과 원 wrong source flags/fret 범위를 포함한다.','',
        '몸체 합력은 현별힘·압력·접촉상대·음향·인과 인증이 아니다. joint qd는 저장되지 않아 CPU 기하 재생에서만0이며 body velocity는 보존했다. 손목 도달 오차 감소를 압현 성공이나 단독 원인 해결로 확대하지 않는다. teacher·목표·문턱·관측·보상·범위는 바꾸지 않았다. 중지 과거128이나 다른 손가락 성과는 비교하지 않는다.','',
        'verification.json은 새700핀·원 archive521 byte/SHA·과거 pin별 verified_at 매핑·24scene 종료·초기73 tensor·settings/contract 차이·원자료 SHA를 기록한다. 과거 checkpoint는 CPU tensor 비교로만 읽었고 현 strict loader를 우회해 재개/평가하지 않았다. GPU/native 추가 실행은0이다.']
    with (out/'RESULTS.md').open('x') as stream: stream.write('\n'.join(text)+'\n')
    print(json.dumps(dict(completed=True,conditions=12,attempts=48,stored_env0_endpoints=sum(t['stored_endpoints'] for t in traces.values()),max_recurrence_rad=max_recurrence)))


if __name__ == '__main__':
    main()
