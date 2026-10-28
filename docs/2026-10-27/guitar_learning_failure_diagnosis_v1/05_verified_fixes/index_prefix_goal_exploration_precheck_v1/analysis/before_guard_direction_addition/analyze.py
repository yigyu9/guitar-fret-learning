"""Stdlib-only preparation; native reports/models remain unread until root completion."""
import argparse
import copy
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
MODES = ('deterministic', 'stochastic')


def read(path): return json.loads(Path(path).read_text())


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path); value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value; spec.loader.exec_module(value); return value


def complete(parent, commands):
    assert parent['completed'] is True and parent['returncode'] == 0
    assert len(parent['children']) == 2 and set(commands) == set(MODES)
    for child, mode in zip(parent['children'], MODES):
        assert child['job'] == mode and child['returncode'] == 0 and child['argv'] == commands[mode]


def execution(value, mode):
    """Runtime sampled-action/logp assertions are evidence, not CPU invented samples."""
    assert mode in MODES and value['mode'] == mode
    assert value['completed'] is True and value['failure'] is None and value['secondary_failure'] is None
    assert value['checks'] and all(v is True for v in value['checks'].values())
    assert value['seed_after_full_strict_load'] == 7 and value['PPO_updates'] == 0
    assert value['supervised_steps'] == 1000 and value['metadata_rewritten'] is False
    assert value['old_model_RNG_frozen_callback_used'] is False
    assert value['legacy_goal_codec_report_written'] is False
    before, after = value['policy_before'], value['policy_after']
    assert all(before[k] == after[k] for k in ('model_sha256', 'updates', 'cost_weight'))
    sampling = value['sampling']; n = sampling['calls']; assert 0 < n <= 354
    assert sampling['requested_deterministic_true'] == n and value['conversion_calls'] == n
    deterministic = mode == 'deterministic'
    assert sampling['actual_deterministic_true'] == (n if deterministic else 0)
    assert sampling['actor_RNG_advances'] == (0 if deterministic else n)
    # Overall fingerprint is reported separately; per-act RNG assertions certify sampling.
    override = value['std_override']
    assert override['changed_state_names'] == ['finger_log_std'] and override['other_state_tensors_exact'] == 72
    assert override['changed_parameter'] == 'finger_log_std[0:4]'
    assert all(override[k] is True for k in ('other12_finger_std_exact', 'other35_effective_std_exact', 'mean_and_critics_exact'))


def self_check():
    commands = {mode: ['python', 'probe.py', '--execute', mode] for mode in MODES}
    p = dict(completed=True, returncode=0, children=[dict(job=m, argv=commands[m], returncode=0) for m in MODES])
    complete(p, commands)
    bad = [dict(p, completed=False), dict(p, returncode=1), dict(p, children=p['children'][:1]), dict(p, children=p['children'][::-1])]
    for key, val in (('job', 'reference'), ('returncode', 1), ('argv', ['other'])):
        v = copy.deepcopy(p); v['children'][0][key] = val; bad.append(v)
    for v in bad:
        try: complete(v, commands)
        except AssertionError: pass
        else: raise AssertionError('Incomplete/foreign jobs admitted')
    for mode in MODES:
        det = mode == 'deterministic'; policy = dict(model_sha256='fixed', updates=0, cost_weight=0.)
        v = dict(completed=True, failure=None, secondary_failure=None, checks=dict(all=True), mode=mode,
            seed_after_full_strict_load=7, PPO_updates=0, supervised_steps=1000, metadata_rewritten=False,
            old_model_RNG_frozen_callback_used=False, legacy_goal_codec_report_written=False,
            policy_before=policy, policy_after=dict(policy), conversion_calls=354,
            sampling=dict(calls=354, requested_deterministic_true=354, actual_deterministic_true=354 if det else 0, actor_RNG_advances=0 if det else 354),
            std_override=dict(changed_state_names=['finger_log_std'], other_state_tensors_exact=72, changed_parameter='finger_log_std[0:4]', other12_finger_std_exact=True, other35_effective_std_exact=True, mean_and_critics_exact=True))
        execution(v, mode)
        mutations = []
        for key, val in (('mode', 'wrong'), ('conversion_calls', 353), ('metadata_rewritten', True), ('PPO_updates', 1), ('completed', False)):
            a = copy.deepcopy(v); a[key] = val; mutations.append(a)
        a = copy.deepcopy(v); a['sampling']['actor_RNG_advances'] = 354 if det else 0; mutations.append(a)
        a = copy.deepcopy(v); a['policy_after']['model_sha256'] = 'changed'; mutations.append(a)
        for a in mutations:
            try: execution(a, mode)
            except AssertionError: pass
            else: raise AssertionError('Wrong execution semantics admitted')
    assert not any(k in sys.modules for k in ('numpy', 'torch', 'isaacgym'))
    print('자가검증 PASS: 두job 완료/실제mode·RNG/모델고정·변환1회; raw/model 읽기0·결과생성0')


def actual():
    complete(read(BASE/'01_launcher.json'), read(BASE/'cpu_inputs/commands.json'))
    out = HERE/'results_v1'; assert not out.exists() and not out.is_symlink()
    probe = module('exploration_actual_producer', BASE/'probe.py'); sys.path.insert(0, str(probe.grid.ROOT))
    codec = probe.source.support(); inputs = {}; verified = {}; native_pin_counts = []
    def track(path):
        p = Path(path).resolve(); inputs[str(p)] = probe.grid.sha(p); return p
    def load(path): return read(track(path))
    for p in (Path(__file__), HERE/'PLAN.md', BASE/'probe.py', BASE/'review.json', BASE/'preparation_seal.json', BASE/'01_launcher.json', BASE/'cpu_inputs/commands.json', probe.source.HERE/'codec.py'):
        track(p)
    import numpy as np
    import torch
    from types import SimpleNamespace
    from guitar_learning.tests.test_gpu_environment import fixture
    from guitar_learning.tool.experiments.short_finger_learning import runner
    from guitar_learning.gpu.simplified_finger_environment import REWARD_TERMS
    torch.set_num_threads(1); assert not torch.cuda.is_available() and 'isaacgym' not in sys.modules
    old = probe.parent.HERE
    pre = module('exploration_actual_precheck', track(old/'precheck_analysis/analyze.py'))
    arm = module('exploration_actual_arm', track(old.parent/'low_effort_index_learning_v1/precheck_analysis/analyze.py'))
    original_folder = probe.recovery.output('evaluate')
    original = load(probe.source.HERE/'analysis/results_recovery_v1/comparison.json')
    original_rows = load(original_folder/'evaluation.json')['episodes']
    original_trace = dict(np.load(track(original_folder/'trace_env0_episode0.npz'), allow_pickle=False))
    original_contract = load(probe.source.output('reference')/'training_contract.json')
    payload = torch.load(track(probe.CHECKPOINT), map_location='cpu', weights_only=False)
    assert inputs[str(probe.CHECKPOINT)] == probe.recovery.MODEL_SHA
    cases = {}; maps = []; baseline = None
    for mode in MODES:
        folder = probe.output(mode); assert load(BASE/('01_%s_launcher.json'%mode)) == read(BASE/'01_launcher.json')['children'][MODES.index(mode)]
        report = load(folder/'execution_override.json'); execution(report, mode)
        assert report['checkpoint_sha256'] == probe.recovery.MODEL_SHA and report['checkpoint'] == str(probe.CHECKPOINT)
        native = load(folder/'diagnostic_report.json')
        assert all(native[k] for k in ('completed','closed','scene_valid','aliases_restored','loader_restored')) and native['failure'] is None
        assert not any(native[k] for k in ('changed_inputs','unpinned_project_sources','cleanup_errors'))
        after = load(folder/'diagnostic_inputs_after.json'); before = load(folder/'inputs_before.json'); maps.append(before)
        assert after['verified'] and not after['changed_paths'] and not after['unpinned_project_sources'] and before == after['input_pins']
        native_pin_counts.append(len(before))
        config = load(folder/'settings.json'); assert config == probe.parent.settings()
        scene = load(folder/'gpu_scene_final.json')
        assert scene['closed'] and scene['environment_count'] == 128 and scene['diagnostic_guitar_mode'] == 'fixed'
        assert scene['hand_collision']['enabled_distinct_finger_pairs'] == 90 and scene['hand_collision_native_readback_environments'] == 128
        assert load(folder/'native_effort_readback.json') == load(old/'cpu_inputs/effort_declaration128.json')
        ev = load(folder/'evaluation.json'); rows = ev['episodes']
        assert ev['assigned_quotas'] == [1]*128 and probe.grid.complete(rows,128) and ev['policy_performance'] and ev['summary'] == runner.summary(rows)
        acceptance = probe.parent.acceptance(rows); assert load(folder/'prefix_acceptance.json') == acceptance
        residual = []
        for row in rows:
            c = row['reward_components']; assert set(c) == set(REWARD_TERMS) and np.isfinite([row['reward'],*c.values()]).all()
            residual.append(row['reward']-sum(c.values()))
        contract = load(folder/'training_contract.json'); assert contract == original_contract
        target = contract['action']['target_contract']; short = config['song']['short_learning']; ids = short['learned_action_indices']
        meta,_ = fixture(1); meta['action_contract'] = target; tm = load(folder/'trace_metadata.json')
        assert tm['joint_names'] == meta['joint_names'] and tm['body_names'] == meta['body_names']
        t = dict(np.load(track(folder/'trace_env0_episode0.npz'),allow_pickle=False))
        g = dict(np.load(track(folder/'current_goal_DIP60.npz'),allow_pickle=False))
        d = dict(np.load(track(folder/'observations4.npz'),allow_pickle=False)); side = dict(np.load(track(folder/'goal_codec_env0.npz'),allow_pickle=False))
        assert (d['source_control'] == 1).all() and d['first_attempt'].all(); np.testing.assert_array_equal(d['requested_NN_action'],d['executed_action'])
        qids = [meta['joint_names'].index(n) for n in short['learned_action_names']]
        for i in range(4):
            m = d['env_id'] == i; episode = next(r for r in rows if r['env_id'] == i); steps = episode['steps']
            np.testing.assert_array_equal(d['start_clock'][m],np.arange(steps)*4); np.testing.assert_array_equal(d['clock'][m],np.arange(1,steps+1)*4)
            assert not d['prior_failure'][m].any() and not d['post_failure'][m][:-1].any()
            assert bool(d['post_failure'][m][-1]) == bool(episode['termination']['physical_failure'] or episode['termination']['wrist_failure'])
            np.testing.assert_array_equal(d['current_goal'][m],g['current_goal'][:steps,i])
        m = d['env_id'] == 0
        for k in side: np.testing.assert_array_equal(side[k],d[k][m])
        np.testing.assert_array_equal(d['requested_NN_action'][m],t['policy_action'][:,ids]); np.testing.assert_array_equal(d['old_target_rad'][m][1:],t['target'][:-1,qids]); np.testing.assert_array_equal(d['final_target_rad'][m],t['target'][:,qids])
        active = torch.tensor([target['joint_names'].index(n) for n in target['action_order']]); ref = torch.tensor(target['reference105_rad'],dtype=torch.float32)
        oldtarget = ref[None].repeat(len(d['clock']),1); oldtarget[:,active[ids]] = torch.from_numpy(d['old_target_rad'])
        mask = torch.zeros(39,dtype=torch.bool); mask[17:33] = True
        fake = SimpleNamespace(spec=short,teacher_reference=ref[active],incremental_mask=mask,controller=SimpleNamespace(reference=ref,target=oldtarget,active=active,action_low=torch.tensor(target['action_lower_rad']),action_high=torch.tensor(target['action_upper_rad'])),environment=SimpleNamespace(_local_time=lambda:torch.from_numpy(d['start_clock']).to(torch.float64)/240.))
        raw = torch.zeros(len(d['clock']),39); raw[:,ids] = torch.from_numpy(d['raw_goal_normalized']); physical,decoded = codec.convert(fake,raw)
        np.testing.assert_array_equal(decoded.numpy(),d['decoded_goal_rad']); np.testing.assert_array_equal(physical[:,ids].numpy(),d['requested_NN_action'])
        policy = codec.policy_type(probe.source)(contract=contract,size='large',fresh=False); policy.load_state_dict(payload['model'],strict=True)
        assert len(policy.state_dict()) == 73 and policy.architecture == payload['identity']['architecture']
        with torch.no_grad():
            policy.finger_log_std[:4].copy_(torch.tensor(report['std_override']['new_log_std4']))
            pred = policy(*(torch.as_tensor(d[k]) for k in runner.FIELDS))['mean'][:,ids].tanh()
        raw_difference = pred.numpy()-d['raw_goal_normalized']
        if mode == 'deterministic': np.testing.assert_allclose(pred.numpy(),d['raw_goal_normalized'],rtol=0,atol=2e-6)
        reference = runner.read_reference(track(probe.parent.base.pre.INPUTS['index'][1]),short)
        desired = codec.desired_reference(probe.source,fake,reference)[:,ids].numpy(); phases = []
        for j in range(6):
            p = d['phase'] == j; phases.append(dict(phase=j,samples=int(p.sum()),decoded_minus_planned_RMS_deg=np.rad2deg(np.sqrt(np.mean((d['decoded_goal_rad'][p]-desired[p])**2,0))).tolist(),raw_minus_CPU_mean_RMS4=np.sqrt(np.mean(raw_difference[p]**2,0)).tolist(),physical_negative_requests4=(d['requested_NN_action'][p]<0).sum(0).tolist()))
        cross = {str(a):{str(r):sum(bool(v['notes'][0]['achieved']) == a and bool(v['notes'][0]['released']) == r for v in rows) for r in (False,True)} for a in (False,True)}
        cases[mode] = dict(acceptance=acceptance,A_achieved_release_cross=cross,execution=report,phase_comparison=phases,
            raw_minus_CPU_mean_max_abs=float(abs(raw_difference).max()),raw_CPU_mean_equality_required=mode=='deterministic',decoded_replay_max_abs_rad=0.,physical_replay_max_abs=0.,
            trace=pre.trace_audit(t,meta,config,rows,target,probe.parent.support(),arm,'policy'),guard=pre.guard_audit(g,rows,short['view']),reward9_mean={k:float(np.mean([r['reward_components'][k] for r in rows])) for k in REWARD_TERMS},reward9_sum_max_abs_residual=float(max(map(abs,residual))))
        if mode == 'deterministic':
            baseline = dict(acceptance_exact=acceptance==original['acceptance'],episodes_exact=rows==original_rows,common_env0_trace_max_abs={k:float(np.max(abs(t[k].astype(float)-original_trace[k].astype(float)))) for k in t if k in original_trace and t[k].shape==original_trace[k].shape})
    assert cases['deterministic']['execution']['policy_before']['model_sha256'] == cases['stochastic']['execution']['policy_before']['model_sha256']
    for mapping in maps:
        for p,h in inputs.items():
            if p in mapping: assert mapping[p] == h; verified[p] = h
    out.mkdir(); probe.grid.write(out/'comparison.json',dict(cases=cases,original_goal_acceptance=original['acceptance'],deterministic_original_reproduction=baseline,
        scope='256 new attempts/768 notes; runtime sampling assertions/RNG audit reused; sampled stochastic raw goals replayed without claiming equality to mean; no PPO/fit/native added'))
    probe.grid.write(out/'acceptance.json',{mode:cases[mode]['acceptance'] for mode in MODES})
    probe.grid.write(out/'verification.json',dict(completed=True,CPU_only=True,GPU_executed=False,input_sha256=inputs,verified_input_sha256=verified,native_verified_execution_pin_counts=native_pin_counts,attempts=256,note_opportunities=768,CPU_rehash_scope='direct inputs only; full native before/after audits kept separately'))
    print(json.dumps({mode:dict(acceptance=cases[mode]['acceptance'],A_cross=cases[mode]['A_achieved_release_cross']) for mode in MODES},ensure_ascii=False))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('--self-check', action='store_true'); p.add_argument('--root-completed',action='store_true'); a = p.parse_args()
    if a.self_check: self_check()
    elif a.root_completed: actual()
    else: print('CPU 준비만. root 두job 종료 통보 전 실제 raw/model 읽기·결과 생성0.')
