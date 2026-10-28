"""CPU-only comparison of reviewed20Nm and completed0.25Nm native diagnostics."""
import argparse
import csv
import importlib.util
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
spec = importlib.util.spec_from_file_location('cap_analysis_probe', BASE/'probe.py')
probe = importlib.util.module_from_spec(spec); spec.loader.exec_module(probe)
parent = probe.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root-completed', action='store_true'); args = parser.parse_args()
    if not args.root_completed:
        print('Prepared only; actual result read requires root completion handoff.'); return
    sys.path.insert(0, str(probe.ROOT))
    import numpy as np
    import torch
    from scipy.spatial.transform import Rotation
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning.runtime import ShortEnvironment
    from guitar_learning.tool.experiments.short_finger_learning.runner import summary
    from guitar_learning.tool.experiments.short_finger_learning.spec import selected_actions
    torch.set_num_threads(1)
    out = HERE/'results_v1'; probe.reject_existing(out)
    inputs, verified = {}, {}

    def track(path):
        path = Path(path); inputs[str(path)] = parent.sha(path); return path

    def read(path):
        return parent.read(track(path))

    def pins(values):
        for p, h in values.items():
            if p not in verified: verified[p] = parent.sha(p)
            assert verified[p] == h, p

    def stats_of(values):
        values = np.asarray(values)
        return dict(mean=values.mean(0).tolist(), p50=np.percentile(values,50,axis=0).tolist(),
            p95=np.percentile(values,95,axis=0).tolist(), max=values.max(0).tolist()) if len(values) else None

    # Reuse the reviewed baseline; no old grid re-analysis or native execution.
    for path in probe.baseline_actual_gate(): track(path)
    baseline_review = read(probe.BASELINE_REVIEW)
    baseline_verification = read(probe.BASELINE_REVIEW.parent/'verification.json')
    pins(baseline_review['reviewed_sha256'])
    for key in ('input_sha256', 'verified_input_sha256'): pins(baseline_verification[key])
    baseline_comparison = read(probe.BASELINE_REVIEW.parent/'comparison.json')
    seal = read(BASE/'preparation_seal.json'); pins(seal['input_pins'])
    assert seal['independent_review'] == 'passed_no_findings' and len(seal['input_pins']) == 752
    launcher = read(BASE/'01_launcher.json')
    assert launcher['completed'] and launcher['returncode'] == 0
    assert [r['finger'] for r in launcher['jobs']] == ['index','middle'] and all(r['returncode']==0 for r in launcher['jobs'])
    metadata, _ = fixture(1)
    cases, audits, force_rows, attempt_rows, plots = {}, {}, [], [], {}
    for finger, grid in probe.repro.SELECTED.items():
        folder = BASE/'runs'/finger; oldfolder = probe.REPRO/'runs'/finger
        assert read(BASE/('01_'+finger+'_launcher.json'))['returncode'] == 0
        config = read(folder/'settings.json'); assert config == read(oldfolder/'settings.json') == read(BASE/'cpu_inputs'/(finger+'_settings.json'))
        document = read(BASE/'cpu_inputs'/(finger+'_targets.json'))
        assert document == read(probe.REPRO/'cpu_inputs'/(finger+'_targets.json'))
        report, scene = read(folder/'report.json'), read(folder/'gpu_scene_final.json')
        assert all(report[k] for k in ('completed','closed','scene_valid','loader_restored','no_NN_checkpoint'))
        assert report['failure'] is None and report['close_failure'] is None and not report['changed_inputs'] and not report['unpinned_project_sources']
        assert report['assigned_first_attempts']==4 and report['selected_grid_index']==grid and report['cap_Nm']==.25
        oldscene = read(oldfolder/'gpu_scene_final.json')
        assert all(scene[k]==oldscene[k] for k in scene if k not in ('physics_steps','rigid_property_readback_max_abs_error'))
        assert scene['closed'] and scene['environment_count']==4 and scene['hand_collision']['enabled_distinct_finger_pairs']==90
        assert scene['hand_collision_native_readback_environments']==4 and scene['physics_steps']==4*report['resources']['control_ticks']
        assert report['resources']['physics_steps']==scene['physics_steps']
        assert report['resources']['control_ticks']<=config['song']['short_learning']['view']['duration_ticks']
        before, after = read(folder/'inputs_before.json'), read(folder/'inputs_after.json'); pins(before)
        assert after['verified'] and before==after['input_pins'] and not after['changed_paths'] and not after['unpinned_project_sources']
        native = read(folder/'native_effort_readback.json')
        contract = read(folder/'training_contract.json'); oldcontract = read(oldfolder/'training_contract.json')
        assert contract['native_backend'].pop('diagnostic_native_effort') == native
        assert contract==oldcontract
        actual, original = native['actual_native_PD105'], native['original_profile_native_PD105']
        assert set(actual)==set(original) and all(len(v)==105 for v in actual.values())
        delta = {k: np.flatnonzero(np.asarray(actual[k])!=original[k]).tolist() for k in actual}
        ids = [i for i,n in enumerate(metadata['joint_names']) if n.startswith('LH:') and not n.startswith('LH:thumb')]
        assert len(ids)==16 and delta==native['changed_native_field_indices'] and delta['effort']==ids
        assert all(not v for k,v in delta.items() if k!='effort')
        assert all(actual['effort'][i]==.25 and original['effort'][i]==20 for i in ids)
        assert native['expected_readback_exact'] and native['source_contract_except_16_effort_exact']
        evaluation = read(folder/'evaluation.json'); statistics = read(folder/'statistics.json')
        oldeval = read(oldfolder/'evaluation.json'); oldstats = read(oldfolder/'statistics.json')
        assert all(statistics[k]==oldstats[k] for k in ('phase_order','phase_scope','gate_order','metric_order','scope'))
        episodes, rows = evaluation['episodes'], statistics['rows']
        assert evaluation['assigned_quotas']==[1]*4 and evaluation['policy_performance'] is False
        assert parent.complete(episodes,4) and sorted(r['env_id'] for r in rows)==list(range(4))
        assert evaluation['summary']==summary(episodes) and evaluation['acceptance']==probe.repro.acceptance(episodes)
        assert oldeval['acceptance']==baseline_comparison['cases'][finger]['acceptance']
        for e,s in zip(episodes, rows):
            expected = document['rows'][e['env_id']]
            assert e['env_id']==s['env_id'] and e['grid_index']==s['grid_index']==grid
            assert e['attempt_id']==s['attempt_id']==expected['attempt_id'] and e['selected_target_count']==1 and e['target_id']==document['source_target_id']
            assert sum(p['samples'] for p in s['phases'].values())==e['steps']
            assert len(e['reward_components'])==9 and np.isfinite(list(e['reward_components'].values())).all()
        cases[finger] = dict(baseline=dict(acceptance=oldeval['acceptance'],episodes=oldeval['episodes'],statistics=oldstats['rows']),
            cap=dict(acceptance=evaluation['acceptance'],episodes=episodes,statistics=rows), native_changed_fields=delta)
        pair_traces = {}; pair_data = {}
        for label, directory, ev, stat in [('baseline20',oldfolder,oldeval,oldstats),('cap025',folder,evaluation,statistics)]:
            for e,s in zip(ev['episodes'],stat['rows']):
                attempt_rows.append(dict(condition=label,finger=finger,env_id=e['env_id'],achieved=e['achieved'],
                    clean=e['clean_fraction'],wrong=e['audible_wrong_fraction'],missing=e['missing_fraction'],
                    physical_failure=e['termination']['physical_failure'],wrist_failure=e['termination']['wrist_failure'],
                    reward=e['reward'],reward_component_sum=sum(e['reward_components'].values()),
                    reward_components=e['reward_components'],note=e['note'],phases=s['phases']))
            meta = read(directory/'trace_metadata.json')
            assert meta['joint_names']==metadata['joint_names'] and meta['body_names']==metadata['body_names']
            assert meta['env_id']==0 and meta['grid_index']==grid and meta['attempt_id']==document['rows'][0]['attempt_id']
            t = dict(np.load(track(directory/meta['file'])))
            assert len(t['time_s'])==ev['episodes'][0]['steps'] and np.all(np.diff(np.rint(t['time_s']*240))==4)
            assert all(np.isfinite(v).all() for v in t.values())
            qids = [meta['joint_names'].index(n) for n in document['joint_names']]
            bodies = [meta['body_names'].index('human/LH:'+finger+str(i)) for i in (1,2,3)]
            wrist,guitar = [meta['body_names'].index(n) for n in ('human/L_Wrist','guitar/guitar')]
            rg = Rotation.from_quat(t['body_state'][:,guitar,3:7])
            pos = t['body_state'][:,guitar,:3]+rg.apply(t['wrist_goal_G_m'])-t['body_state'][:,wrist,:3]
            rot = (rg*Rotation.from_quat(t['wrist_goal_G_xyzw'])*Rotation.from_quat(t['body_state'][:,wrist,3:7]).inv()).magnitude()
            data = np.c_[np.rad2deg(t['q'][:,qids]),np.rad2deg(t['target'][:,qids]),np.rad2deg((t['target']-t['q'])[:,qids]),
                np.linalg.norm(t['net_body_force_n'][:,bodies],axis=-1),t['surface_distance_m']*1000,t['surface_height_m']*1000,
                np.zeros(len(t['time_s'])),np.linalg.norm(pos,axis=-1)*1000,np.rad2deg(rot)]
            source = config['song']['short_learning']['view']['source_target']
            masks = parent.phase_masks(t['source_time_s'],source['onset_s'],source['end_s'])
            gate_counts, residual_height, residual_distance, causes = [], [], [], []
            if label=='cap025':
                assert meta['selected_native_qd_names']==document['joint_names'] and t['selected_native_qd'].shape==(len(data),4)
                env = ShortEnvironment(metadata,bundle=config['song_training']['bundle'],song=config['song'],skill=config['finger_skill'],device='cpu')
                def snapshot(k):
                    return dict(q=torch.tensor(t['q'][k:k+1]),qd=torch.zeros(1,105),target=torch.tensor(t['target'][k:k+1]),
                        body_state=torch.tensor(t['body_state'][k:k+1]),contact_force=torch.tensor(t['net_body_force_n'][k:k+1]))
                env.reset([0],snapshot(0))
                for k, now in enumerate(t['time_s']):
                    env.clock[0]=round(now*240); env._snapshot(snapshot(k)); j=env.selected_index
                    assert bool(env.candidate[0,j])==bool(t['candidate'][k]) and bool(env.wrong[0,j])==bool(t['wrong'][k])
                    residual_distance.append(float(env.surface_distance[0,j])-float(t['surface_distance_m'][k]))
                    residual_height.append(float(env.surface_height[0,j])-float(t['surface_height_m'][k]))
                    assert abs(residual_distance[-1])<1e-6
                    data[k,17]=float(env.surface_alignment[0,j])
                    gate_counts.append([bool(v[0,j]) for v in (env.surface_body_loaded,env.contact_geometry,env.contact_facing,env.contact_loaded_target,env.candidate,env.wrong)])
                    causes.append(env.wrong_source_flags[0,j].tolist())
            checks = {}; cosine = {}; phases = {}
            for phase, mask in zip(stat['phase_order'],masks):
                p=stat['rows'][0]['phases'][phase]; assert int(mask.sum())==p['samples']
                if not p['samples']: continue
                for key,value in [('mean',data[mask].mean(0)),('min',data[mask].min(0)),('max',data[mask].max(0)),('rms',np.sqrt((data[mask]**2).mean(0)))]:
                    np.testing.assert_allclose(value[[i for i in range(20) if i!=17]],np.asarray(p[key])[[i for i in range(20) if i!=17]],rtol=5e-6,atol=5e-5)
                    if label=='cap025': cosine[phase+'_'+key]=dict(CPU=float(value[17]),saved=p[key][17],residual=float(value[17]-p[key][17]))
                if label=='cap025':
                    assert np.array_equal(np.asarray(gate_counts)[mask].sum(0),p['gate_counts'])
                phases[phase]=dict(actual_q_deg=stats_of(data[mask,:4]),target_q_deg=stats_of(data[mask,4:8]),
                    target_minus_actual_deg=stats_of(data[mask,8:12]),selected_resultant_N=stats_of(data[mask,12:15]),
                    wrist_mm_deg=stats_of(data[mask,18:20]),saved_nearest_mm=stats_of(data[mask,15:17]),gate_counts=p['gate_counts'],samples=p['samples'],
                    selected_native_qd_rad_s=stats_of(t['selected_native_qd'][mask]) if label=='cap025' else None,
                    CPU_wrong_source_counts=np.asarray(causes)[mask].sum(0).tolist() if label=='cap025' else None)
                for b,name in enumerate(meta['body_names']):
                    if not name.startswith('human/LH:'): continue
                    force=t['net_body_force_n'][mask,b]; norm=np.linalg.norm(force,axis=-1)
                    force_rows.append(dict(finger=finger,condition=label,phase=phase,body=name,samples=int(mask.sum()),
                        **stats_of(norm),mean_world_xyz_N=force.mean(0).tolist(),mean_guitar_xyz_N=rg[mask].inv().apply(force).mean(0).tolist()))
            checks.update(endpoints=len(data),non_cosine20statistics_match=True,phases=phases)
            if label=='cap025':
                checks.update(candidate_wrong_each_endpoint_match=True,six_phase_gate_counts_match=True,
                    nearest_distance_max_abs_residual_m=max(map(abs,residual_distance)),
                    nearest_height_max_abs_residual_m=max(map(abs,residual_height)),
                    nearest_height_residuals_over_1um=[dict(endpoint=k,time_s=float(t['time_s'][k]),saved_m=float(t['surface_height_m'][k]),CPU_minus_saved_m=v) for k,v in enumerate(residual_height) if abs(v)>1e-6],
                    nearest_normal_cos_statistics=cosine,CPU_wrong_source_body_order=['thumb2','thumb3','index2','index3','middle2','middle3','ring2','ring3','pinky2','pinky3'],
                    CPU_wrong_source_cause_order=['other_higher','own_wrong_fret','own_wrong_string'])
            audits[finger+'_'+label]=checks; pair_traces[label]=t; pair_data[label]=data
        old,new = pair_traces['baseline20'],pair_traces['cap025']
        assert np.array_equal(old['time_s'],new['time_s']) and np.array_equal(old['source_time_s'],new['source_time_s'])
        action_ids=list(selected_actions(['index','middle','ring','pinky'].index(finger)+1))
        # Native selected q ids and active-action ids are different index spaces.
        assert np.array_equal(old['target'][:,qids],new['target'][:,qids])
        assert np.array_equal(old['scripted_action'][:,action_ids],new['scripted_action'][:,action_ids])
        assert np.array_equal(old['executed_action'][:,action_ids],new['executed_action'][:,action_ids])
        target_change=np.diff(new['target'][:,qids],axis=0)
        assert abs(target_change).max()<=4/60+1e-6
        assert (new['target'][:,qids]>=np.asarray(actual['lower'])[qids]-1e-6).all() and (new['target'][:,qids]<=np.asarray(actual['upper'])[qids]+1e-6).all()
        armids=[i for i,n in enumerate(metadata['joint_names']) if n.startswith(('L_Thorax_','L_Shoulder_','L_Elbow_','L_Wrist_'))]
        cases[finger]['trace_comparison']=dict(selected4_target_and_action_tape_exact=True,identical_time_grid=True,
            selected4_actual_max_abs_difference_deg=float(np.rad2deg(abs(new['q'][:,qids]-old['q'][:,qids])).max()),
            arm12_target_max_abs_difference_deg=float(np.rad2deg(abs(new['target'][:,armids]-old['target'][:,armids])).max()),
            selected4_target_max_step_rad=float(abs(target_change).max()),native_rate_rad_s=4.,selected_target_bounds_pass=True)
        plots[finger]=(pair_traces,pair_data,masks[1])
    assert len(attempt_rows)==16 and len(force_rows)==2*2*3*22
    assert not torch.cuda.is_initialized() and 'isaacgym' not in sys.modules
    track(Path(__file__).resolve()); track(HERE/'PLAN.md')
    out.mkdir()
    parent.write(out/'comparison.json',dict(cases=cases,trace_audits=audits,scope='16 first attempts:8 reviewed baseline+8 newcap; env0 detailed60Hz only'))
    parent.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,total_cap_first_attempts=8,total_comparison_first_attempts=16,
        input_sha256=inputs,verified_input_sha256=verified,scene_checks_pass=True,native105_exact_except16_effort=True,original90pairs_preserved=True,
        same_selected4_target_action_tapes=True,statistics_rtol=5e-6,statistics_atol=5e-5,
        baseline_validation_reused=str(probe.BASELINE_REVIEW),baseline_nearest_limits=baseline_verification['trace_checks'],
        known_limits=['60Hz endpoints/env0 full raw only; not240Hz maxima','native sample index/normalcos perendpoint not stored; CPU argmin/provenance not native witness certification',
            'native qd caponly velocity coordinate; no baseline qd or MCP2 qpos derivative claim','0.25Nm native cap readback is not body force/pressure or isolated motor torque measurement',
            'same selected finger commands, but arm wrist feedback changes with physical trajectory; no specific contactpair or production causal guarantee']))
    for name,rows in [('attempts',attempt_rows),('LH_body_forces',force_rows)]:
        with (out/(name+'.csv')).open('x',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(12,6.5))
    for r,(finger,(traces,data,audible)) in enumerate(plots.items()):
        for label,style in [('baseline20','--'),('cap025','-')]:
            t=traces[label]['time_s']; d=data[label]
            for i in range(3): axes[r,0].plot(t,d[:,12+i],style,label=label+' body'+str(i+1))
            for i in (1,): axes[r,1].plot(t,d[:,i],style,label=label+' actual1_z')
            axes[r,1].plot(t,d[:,5],style,label=label+' target1_z',alpha=.5)
            axes[r,2].plot(t,d[:,18],style,label=label+' wrist mm')
            axes[r,2].plot(t,d[:,15],style,label=label+' nearest mm')
        for ax in axes[r]:
            ax.axvspan(t[audible][0],t[audible][-1],color='gray',alpha=.15); ax.grid(alpha=.2); ax.legend(fontsize=6); ax.set_xlabel('local seconds')
        axes[r,0].set_ylabel(finger+' resultant N'); axes[r,1].set_ylabel('selected1_z degrees'); axes[r,2].set_ylabel('mm')
    fig.suptitle('Env0 first-attempt60Hz endpoints; shaded audible; body resultant is not pair pressure')
    fig.tight_layout(); fig.savefig(out/'comparison.png',dpi=145); plt.close(fig)
    print('CPU comparison written:',out)


if __name__=='__main__': main()
