"""기존 6→8 참조를 실제 정책 행동 범위·직접 위치 제어와 CPU에서 대조한다.

GPU 장면이나 native 상태를 만들지 않는다. 원래 성공 재생의 입력·SHA를 검증하고,
현재 BatchedController.targets 자체를 CPU tensor로 호출한다. 발 IK는 이 검사에서
생략하며, 그 영향이 없는 팔·손가락16축만 비교한다. 물리 성공은 별도 기존 증거다.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

import numpy as np
import torch

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'scripts/tab2body.py').is_file())
sys.path.insert(0, str(ROOT))
from guitar_learning.gpu.control import BatchedController
from guitar_learning.tool.experiments.natural_press import normalized_action
from guitar_learning.tool.validation.press_acquisition import trajectory_actions

OLD = ROOT/'docs/2026-11-02/압현실험/중지6에서8프렛_환경수비교_20261101'
OUT = Path(__file__).resolve().parents[1]/'validation/action_space'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def mapper(contract, initial, dtype=torch.float32):
    """실제 targets 메서드에 필요한 상태만 만든다. 발 보정은 검사 범위 밖이다."""
    t = lambda value: torch.tensor(value, dtype=dtype)
    names = contract['joint_names']
    active = torch.tensor([names.index(n) for n in contract['action_order']])
    reference = t(contract['reference105_rad'])
    # 비행동 축은 아래 시험의 판정 대상이 아니다. 실제 zero 축은 그대로 둔다.
    lower = torch.full((105,), -100., dtype=dtype)
    upper = torch.full((105,), 100., dtype=dtype)
    lower[active] = t(contract['action_lower_rad'])
    upper[active] = t(contract['action_upper_rad'])
    return SimpleNamespace(num_envs=1, device=torch.device('cpu'), active=active,
        reference=reference, target=t(initial)[None].clone(), lower=lower, upper=upper,
        action_low=t(contract['action_lower_rad']), action_high=t(contract['action_upper_rad']),
        rate=t(contract['rate_rad_s']), alpha=t(contract['smoothing_alpha']),
        zero=torch.tensor(contract['zero_indices']), _foot_targets=lambda target: target)


def decode(action, reference, low, high):
    return reference+torch.where(action >= 0, high-reference, reference-low)*action


def step(model, action):
    return BatchedController.targets(model, action, {})


def audit():
    paths = dict(catalog=OLD/'geometry/initial_catalog.json',
        provenance=OLD/'geometry/initial_provenance.json',
        candidates=OLD/'geometry/reference_v1/reference_candidates.json',
        native_report=OLD/'validation/reference_native_v3/report.json',
        native_settings=OLD/'validation/reference_native_v3/settings.json',
        native_inputs=OLD/'validation/reference_native_v3/inputs_before.json',
        native_trace=OLD/'validation/reference_native_v3/trace240.npz',
        motion=OLD/'tools/reference_motion_settle030.py',
        replay=OLD/'tools/reference_native_settle030.py',
        runtime=OLD/'tools/runtime.py',
        training_contract=OLD/'learning_v1/jobs/s7_t2097152_train/J/training_contract.json',
        controller=ROOT/'guitar_learning/gpu/control.py',
        natural=ROOT/'guitar_learning/tool/experiments/natural_press.py',
        inverse=ROOT/'guitar_learning/tool/validation/press_acquisition.py')
    data = {k: read(p) for k, p in paths.items() if p.suffix == '.json'}
    catalog = data['catalog']; candidates = data['candidates']; native = data['native_report']
    contract = native['controller_contract']; goal = catalog['goals'][0]
    assert sha(paths['catalog']) == data['provenance']['catalog_sha256']
    changed = [p for p, digest in data['native_inputs'].items() if not Path(p).is_file() or sha(p) != digest]
    assert not changed, '기존 native 봉인 입력 변경: '+str(changed)
    assert contract == data['training_contract']['action']['target_contract'], '학습/참조 제어 계약 차이'
    assert np.allclose(catalog['reference105'], contract['reference105_rad'], atol=2e-7, rtol=0)
    assert np.allclose(catalog['action_lower'], contract['action_lower_rad'], atol=2e-7, rtol=0)
    assert np.allclose(catalog['action_upper'], contract['action_upper_rad'], atol=2e-7, rtol=0)
    model = mapper(contract, goal['hold_target105'])
    learned = np.array(list(range(12))+list(range(21,25)))
    assert np.array_equal(learned, candidates['active_channels'])
    ix = np.asarray(catalog['action_indices']); native_ix = ix[learned]
    assert np.array_equal(ix, model.active.numpy())
    fixed = np.array([i for i in range(39) if i not in learned])
    initial = torch.tensor(goal['hold_target105'], dtype=torch.float32)[model.active][None]
    reference = model.reference[model.active]
    rows = {}
    for name, item in candidates['candidates'].items():
        # 실제 native 재생도 비활성 축은 초기 유지 명령을 쓰고, 활성16축만 q105에서 꺼낸다.
        q = np.array(item['q105'])
        desired = initial.clone(); desired[:, learned] = torch.tensor(q[native_ix], dtype=torch.float32)
        actions = trajectory_actions(desired, reference, model.action_low, model.action_high)
        recovered = decode(actions, reference, model.action_low, model.action_high)
        normal = normalized_action(desired, reference, model.action_low, model.action_high)
        a = actions[0].numpy()
        margins = np.minimum(q[native_ix]-np.array(catalog['action_lower'])[learned],
                             np.array(catalog['action_upper'])[learned]-q[native_ix])
        fixed_q = np.max(np.abs(q[ix[fixed]]-np.array(goal['q105'])[ix[fixed]]))
        rows[name] = dict(inside_bounds=bool(np.all(margins >= -1e-7)),
            minimum_bound_margin_rad=float(margins.min()),
            roundtrip_max_rad=float((recovered-desired).abs().max()),
            inverse_implementations_max_action_difference=float((normal-actions).abs().max()),
            nonlearned_action_commands_held_initial=True,
            nonlearned_reference_q_matches_initial_actual=bool(fixed_q < 1e-8),
            channels=[dict(channel=int(ch), name=catalog['active_names'][ch],
                requested_rad=float(q[ix[ch]]), normalized_action=float(a[ch]),
                margin_rad=float(margin), near_saturation=bool(abs(a[ch]) >= .999))
                for ch, margin in zip(learned, margins)])
    # 옛 trajectory_gap JSON은 v1이다. native v3의 실제 .30초 정착 keyframe 생성기를 쓴다.
    spec = importlib.util.spec_from_file_location('audited_settle030_motion', paths['motion'])
    motion = importlib.util.module_from_spec(spec); spec.loader.exec_module(motion)
    times, qs, frames = motion.trajectory(candidates['candidates'], .75)
    requests = []; applied = []; controls = []
    model = mapper(contract, goal['hold_target105'])
    for q in qs[1:]:
        desired = initial.clone(); desired[:, learned] = torch.tensor(q[native_ix], dtype=torch.float32)
        action = trajectory_actions(desired, reference, model.action_low, model.action_high)
        controls.append(action[0].numpy()); requests.append(desired[0].numpy())
        applied.append(step(model, action)[0, model.active].numpy().copy())
    requests, applied, controls = map(np.asarray, (requests, applied, controls))
    trace = np.load(paths['native_trace'])
    # native trace의 requested_target은105축이 아닌action39, applied_target은105축이다.
    native_requested = trace['requested_target'][3::4]
    native_applied = trace['applied_target'][3::4][:, ix]
    request_error = float(np.max(abs(requests-native_requested)))
    applied_error = float(np.max(abs(applied[:, learned]-native_applied[:, learned])))
    assert len(requests) == len(native_requested)
    assert request_error < 2e-6 and applied_error < 2e-6, (request_error, applied_error)
    endpoint_lag = {}
    for time, name in frames:
        if time > 0:
            i = min(len(applied)-1, round(time*60)-1)
            endpoint_lag[str(time)+' '+name] = float(np.max(abs(applied[i, learned]-requests[i, learned])))
    delta = np.diff(np.vstack((initial.numpy(), applied)), axis=0)*60
    actual_rate = np.asarray(contract['rate_rad_s'])[native_ix]
    assert (np.max(abs(delta[:, learned]), axis=0) <= actual_rate+2e-5).all()
    initial_action = trajectory_actions(initial, reference, model.action_low, model.action_high)[0]
    initial_latent = torch.atanh(initial_action.clamp(-.999999,.999999))
    bias_comparison = []
    for row in rows['B_press']['channels']:
        ch = row['channel']
        b_action = torch.tensor(row['normalized_action'], dtype=torch.float32)
        b_latent = torch.atanh(b_action.clamp(-.999999,.999999))
        bias_comparison.append(dict(channel=ch, name=row['name'],
            initial_action=float(initial_action[ch]), initial_latent=float(initial_latent[ch]),
            reference_B_action=float(b_action), reference_B_latent=float(b_latent),
            reference_B_minus_initial_latent=float(b_latent-initial_latent[ch]),
            initial_tanh_derivative=float(1-initial_latent[ch].tanh().square()),
            initial_bias_only_action=float(initial_latent[ch].tanh()),
            initial_support_std=float(np.exp(-3)) if ch < 12 else None,
            reference_latent_delta_over_initial_support_std=(float(abs(b_latent-initial_latent[ch])/np.exp(-3)) if ch < 12 else None)))
    passes = all(v['inside_bounds'] and v['roundtrip_max_rad'] < 2e-6 and
                 v['inverse_implementations_max_action_difference'] < 2e-6 for v in rows.values())
    result = dict(schema='middle_f6_f8.action_space_audit.v1', completed=True, passed=passes,
        inputs={str(p):sha(p) for p in paths.values()}, original_native_inputs_unchanged=not changed,
        identical_training_native_controller_contract=True,
        cpu_only=True, gpu_executed=False, policy_trained=False,
        active_channels=learned.tolist(), active_native_indices=native_ix.tolist(),
        candidates=rows, v3_settle_s=motion.SETTLE_S, keyframes=frames,
        native_replay_requested_max_difference_rad=request_error,
        native_replay_applied_16axis_max_difference_rad=applied_error,
        initial_policy_bias=dict(action=initial_action.numpy().tolist(), latent=initial_latent.numpy().tolist(),
            implementation='NaturalPolicy.__init__: inverse hold_target → atanh(clamp ±.999999); network residual is subsequently added'),
        reference_B_bias_comparison=bias_comparison,
        bias_comparison_scope='Distance to this one known successful reference, not an impossibility proof or the actual network mean. Learned encoder residuals can change the bias.',
        sampled_requested_peak_rate_rad_s=np.max(abs(np.diff(requests[:,learned],axis=0))*60,axis=0).tolist(),
        actual_applied_peak_rate_rad_s=np.max(abs(delta[:,learned]),axis=0).tolist(),
        control_rate_rad_s=actual_rate.tolist(), endpoint_applied_request_lag_rad=endpoint_lag,
        native_evidence=dict(accepted=native['accepted'], source_unchanged=native['source_unchanged'],
            no_intermediate_reset=native['no_intermediate_reset'], notes=native['notes']),
        conclusion='B is reachable inside the same learned action16 bounds; actual original native replay used identical inverse codec and finite target controller. This does not prove the policy can learn the trajectory.',
        limitations=['CPU controller check excludes foot IK; only arm12+middle4 are compared. Original native replay includes foot IK, PD and free-guitar physics.',
            'Native body q may differ from requested q due to PD and contacts; no state teleport and no guarantee for trained policies.',
            'B_press and B_hover are near L_Thorax_z upper bound; this identifies a tight solution, not general infeasibility or a reason to widen all axes.'])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'report.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    text = ['# 정책 행동 범위 검증', '', '**통과: 8프렛 참조는 현재 정책의 팔12+중지4 행동 범위 안에서 실행 가능합니다.**', '',
        '- 기존 학습과 native v3의 제어 계약이 완전히 같습니다.',
        '- A/B의 압현·hover 4개 참조를 실제 inverse codec으로 역변환하고 되돌렸습니다.',
        '- 현재 `BatchedController.targets`를 CPU에서 호출한 16축 결과가 기존 native v3 trace와 최대 '+format(applied_error,'.3g')+' rad 차이로 일치합니다.',
        '- 초기 상태는 기존 initial_catalog를 그대로 사용했습니다. 매 프레임 상태를 덮어쓰지 않았습니다.',
        '- 기존 성공 증거는 자유 기타 GPU 물리·PD를 통과한 native v3이며, 이번 작업에서는 GPU를 실행하지 않았습니다.', '',
        '| 참조 | 최소 범위 여유(rad) | 역변환 오차(rad) | 포화 근접 축 |', '|---|---:|---:|---|']
    for name, row in rows.items():
        near = ', '.join(c['name'] for c in row['channels'] if c['near_saturation']) or '없음'
        text.append('| '+name+' | '+format(row['minimum_bound_margin_rad'],'.6g')+' | '+format(row['roundtrip_max_rad'],'.3g')+' | '+near+' |')
    text += ['', '## 초기 tanh 포화와 탐색 좌표', '',
        '| 축 | 초기 행동 | B 참조 행동 | 초기 latent | B 참조 latent | latent 차이 |',
        '|---|---:|---:|---:|---:|---:|']
    for row in bias_comparison:
        if abs(row['reference_B_minus_initial_latent']) > 1:
            text.append('| '+row['name']+' | '+format(row['initial_action'],'.6f')+' | '+format(row['reference_B_action'],'.6f')+' | '+format(row['initial_latent'],'.3f')+' | '+format(row['reference_B_latent'],'.3f')+' | '+format(row['reference_B_minus_initial_latent'],'.3f')+' |')
    text += ['',
        '초기 유지각을 그대로 역변환해 policy bias에 넣으므로 L_Thorax_y가 +1 끝에 포화됩니다. B의 한 성공 참조는 이 축의 latent를 약 7.3 낮추어야 합니다. 초기 팔 탐색 std=exp(-3)=0.0498과 비교하면 약147배의 좌표 차이입니다. 한 번의 표본으로 반드시 이동해야 한다는 뜻도, 그 참조만 정답이라는 뜻도 아닙니다. 정책의 학습 잔차가 평균을 바꿀 수 있지만 작은 latent 탐색이 포화 부근에서 각도 변화로 잘 전달되지 않는 구조임을 보여줍니다.', '',
        '따라서 단독 8프렛 학습도 실패한다면 범위를 일괄 확대하기보다 초기 bias 포화와 탐색 좌표를 별도 조건으로 점검하는 것이 타당합니다. 기존 frozen 실험·제어·보상은 이번 검증에서 바꾸지 않았습니다. 이것은 가능한 원인에 대한 정량 근거이며, 실패의 인과 확정은 아닙니다.', '',
        '## 해석', '',
        'B는 행동 범위 밖의 불가능한 명령이 아닙니다. 범위를 넓히는 수정은 우선하지 않고, 같은 초기 자세에서 8프렛 단독 학습으로 이동 성공 경험을 만들 수 있는지 확인합니다.', '',
        '다만 B의 흉곽 z축은 상한에 매우 가깝습니다. tanh 출력은 ±1에 정확히 도달하지 않으므로 해 주변의 여유가 작을 수 있습니다. 기존 native 성공은 float32 경계 요청을 실행한 결과이며, 실제 정책이 같은 근방을 탐색·학습한다는 보장은 아닙니다. 실패 시 이 축 포화와 셀 도달 여유를 함께 확인해야 합니다.', '',
        '초기 정책은 초기 hold 명령을 역변환한 latent bias를 사용합니다. 손가락·팔을 A 근처에서 출발시키는 설계이므로, B가 범위 안에 있다는 사실만으로 PPO가 이동 경로를 찾는 것은 아닙니다.', '',
        '## 검증 범위', '',
        'CPU 비교에서는 발 IK를 생략하고 그 보정 대상이 아닌 팔·중지16축만 판정했습니다. PD와 접촉은 새 CPU 계산으로 재현하지 않고, 입력 SHA가 유지된 기존 native v3의 실제 240Hz trace를 근거로 확인했습니다. 과거 v1 trajectory JSON과 v3의 정착 시간을 혼합하지 않았습니다.', '',
        '세부 수치·입력 SHA·포화 행동값·60Hz 제한 및 정착 오차는 report.json에 있습니다.']
    (OUT/'분석.md').write_text('\n'.join(text)+'\n')
    return result


class CodecTests(unittest.TestCase):
    def setUp(self):
        self.reference = torch.linspace(-.2,.2,39)
        self.low = self.reference-.3
        self.high = self.reference+.5

    def test_asymmetric_roundtrip(self):
        action = torch.linspace(-1,1,39)[None]
        desired = decode(action,self.reference,self.low,self.high)
        recovered = trajectory_actions(desired,self.reference,self.low,self.high)
        self.assertTrue(torch.allclose(action,recovered,atol=1e-6))

    def test_zero_returns_reference(self):
        value = decode(torch.zeros(1,39),self.reference,self.low,self.high)
        self.assertTrue(torch.equal(value[0],self.reference))

    def test_outside_is_rejected(self):
        with self.assertRaises(ValueError):
            trajectory_actions((self.high+.01)[None],self.reference,self.low,self.high)

    def test_nonfinite_is_rejected(self):
        value = self.reference[None].clone();value[0,0] = float('nan')
        with self.assertRaises(ValueError):
            trajectory_actions(value,self.reference,self.low,self.high)

    def test_wrong_shape_is_rejected(self):
        with self.assertRaises(ValueError):
            trajectory_actions(self.reference,self.reference,self.low,self.high)

    def test_saturated_bias_blocks_small_latent_changes(self):
        start = torch.atanh(torch.tensor(.999999))
        after = torch.tanh(start-torch.tensor(float(np.exp(-3))))
        self.assertLess(float(abs(after-.999999)), 2e-7)
        self.assertGreater(float(abs(start-torch.atanh(torch.tensor(-.05483)))), 7.)

    def test_real_controller_smoothing_and_rate(self):
        contract = read(OLD/'validation/reference_native_v3/report.json')['controller_contract']
        model = mapper(contract,contract['reference105_rad'])
        old = model.target[0,model.active].clone()
        action = torch.ones(1,39)
        target = step(model,action)[0,model.active]
        expected = old+torch.minimum(model.alpha*(model.action_high-old),model.rate[model.active]/60)
        self.assertTrue(torch.allclose(target,expected,atol=1e-6))
        self.assertTrue(torch.equal(model.alpha[21:25],torch.ones(4)))
        self.assertTrue(torch.allclose(model.alpha[:12],torch.full((12,),.2)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--self-test',action='store_true')
    args = parser.parse_args()
    if args.self_test:
        result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(CodecTests))
        OUT.mkdir(parents=True,exist_ok=True)
        (OUT/'tests.json').write_text(json.dumps(dict(run=result.testsRun,successful=result.wasSuccessful(),
            failures=len(result.failures),errors=len(result.errors)),indent=2)+'\n')
        if not result.wasSuccessful():raise SystemExit(1)
    else:
        result = audit();print(json.dumps(dict(passed=result['passed'],cpu_only=True),indent=2))
        if not result['passed']:raise SystemExit(1)


if __name__ == '__main__':
    main()
