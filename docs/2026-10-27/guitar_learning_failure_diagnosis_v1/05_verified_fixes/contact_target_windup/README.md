# 고정 tape target 진단 실행 준비

root가 승인한 [PLAN.md](PLAN.md)의 세 조건만 구현한다. 기존 `contact_load_probe/probe.py`와 protocol/평가기/strict loader/240Hz 관찰을 변경 없이 감싼다. 첫120 control은 target을 쓰지 않고 원래 결과 그대로 통과한다. 이후 고정 material point에서 기존0.01N 문턱의 signed normal gate를 만족한 행만 선택4 target memory를 바꾼다. snapshot actual q/body에는 쓰지 않는다.

`projection.py`는 float64/maxabs-g 정규화와 유한8 clip breakpoint의 구간별 affine root로 box+halfspace의 Euclidean 최소 변경을 구한다. B는 기존 오차 중 한 tick box에서 가능한 양까지만 완화한다. 최종 float32 target의 box/rate/halfspace는 dtype epsilon·4축 dot·원래 target scale에 따른 numerical tolerance로 검사하며 미세 잔차를 그대로 남긴다. nextafter·추가 force/J 문턱·force cap·보상 변경은 없다. 자세한 수학·gate·미달 처리와 해석 범위는 PLAN을 따른다.

새 `target_control60.npz`만 추가한다. 원래 action과 tape, old/raw/filtered target, 고정점 J와 normal, 실제/예측 점속도, gate/skip(비유한 q/qd/state는 계산 전 제외, actual4 진단 기록만0+invalid_state로 표시), β/가용량/남은 선형오차, normal/tangent 변경, memory/제출 오차와 팔12/손목오차를 저장한다. 원래 previous_action은 override 역산 행동이 아니며, 이후 손목 feedback 혼입과 Cartesian 접선 변경은 남는다. 기존 nearest/any-sample 관찰도 고정점 접촉 인증으로 바꾸지 않는다.

CPU는 `CUDA_VISIBLE_DEVICES='' PYTHONPATH=. python .../self_test.py` 뒤 `prepare.py`다. source final의 action tape 전체와 clock480 source sample을 `fixed_inputs.npz`로 내보내고 original checkpoint input checker를 그대로 통과시킨다. 전체 CUDA topology/architecture strict load는 원래 runtime에서 수행한다. 새 입력을 원래 `_pins` extras에 추가한다. 기존 out은 native import 전에 거부하고 원래 exclusive mkdir 후 dev/inode를 확인한 새 out에만 추가 기록한다. 기존 producer report/raw는 덮어쓰지 않는다.

root GPU 인계 뒤 기존 rl38/Isaac 환경에서 아래처럼 실행한다. mode는 `tape_original`, `tape_no_new_inward`, `tape_no_new_inward_and_relax` 순서다. 각각 새 out을 지정한다. 여기서 GPU 인계는 내부 자원 조정이며 추가 사용자 승인 요청이 아니다.

```bash
PYTHONPATH=. taskset -c 0-13 /home/ajou/miniconda3/envs/rl38/bin/python docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_windup/run_probe.py --mode tape_original --out docs/2026-10-27/guitar_learning_failure_diagnosis_v1/05_verified_fixes/contact_target_windup/run_original
```

다음 두 out은 `run_no_new_inward`, `run_no_new_inward_and_relax`를 권장한다. `target_windup_report.json`은 세 조건의 source-prefix 실제 동일성·tape 전체 동일성·memory/scene 제출·원래 관찰 완료를 검사한다. original 조건은 source의 전체 q/target/pose/force와 evaluation JSON도 실제 exact 비교한다. 불일치나 큰 numerical 위반은 raw를 보존하고 진단 실패로 보고한다. 이를 새 정책 성과·접촉쌍 압력·정책 단독 인과 효과·힘 상한 해결로 주장하지 않는다.
