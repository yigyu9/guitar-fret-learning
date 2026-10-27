# Skill curriculum 실험 보조 코드 독립 검수 v1

요약 판정: **문제없음 — 현재 첫 단음·4초의 제한 실험 범위**. 검토한 코드에서 실제 성공 판정·checkpoint 로드·현재 비용 비교 통계를 훼손하는 Critical 또는 수정이 필요한 Warning을 발견하지 못했다. 아래에서 입력 보존과 지표의 인증 범위를 한정한다. 정책 학습 효과와 scripted 성공 궤적은 구별한다.

## 검수 범위

읽기 전용 대상은 결과 phase의 `probe_v1.py`~`probe_v6.py`, `right_grid_v1.py`/`right_grid_v2.py`, `evaluate_v1.py`, `check_setup_v1.py`, `analyze_runs_v1.py` 및 `guitar_learning/SKILL_CURRICULUM.md`와 README 상단 신규 안내다. probe 버전 간 변경도 대조했다. 소스·시험·실험·분석 producer를 실행하거나 수정하지 않았으며, 이미 생성된 JSON/압축 trace와 SHA를 독립적으로 읽었다. 소유한 이 보고서만 작성했다.

추가 생성된 `evaluate_v2.py`, demonstration capture 및 advantage diagnostic producer는 이번 요청 범위 밖이며 여기서 검수 완료로 표시하지 않는다. 비용 학습·결정적 평가가 진행 중이므로 그 최종 수치는 이 보고서에서 확정하지 않는다.

## Critical / Warning

없음.

## 계산·평가 계약

- **`probe_v1.py:22`, `:79` 및 후속 버전의 동일 경로:** 후보 joint target을 원래 active39의 실제 비대칭 유효 범위로 정규화하고 clip한 뒤 기존 환경 step을 통과시킨다. 반대 손은 정확히0으로 만든다. IK나 과거 replay는 후보 생성 방법이며 별도 기타 힘·부착·native state 쓰기나 성공 flag 주입을 하지 않는다. 실제 성취는 원래 240Hz contact/crossing ledger와 안전한 전체 horizon에서 판정한다.
- **`probe_v2.py:48` 이후 / v3~v4:** 과거 native 양성 접촉의 local feature 평균을 IK marker로 재사용하나, 새 contact 후보를 해당 과거 데이터만으로 인증하지 않는다. v3의 프렛선 쪽 후보와 v4의 다른 FK/절대 command 탐색도 각 새 버전·결과로 보존한다. 이 FK fitting을 해부학적·물리적 도달성의 일반 증명으로 해석하지 않는다.
- **`right_grid_v1.py:13`, `:20` 및 v2:** 한 recorded native 자세에 고정한 FK로 범위 내 두 endpoint를 찾는다. grid v2의 차이는 ±4mm에서 ±8mm로 확장한 후보 stroke다. 이 offline residual은 native 성공 지표가 아니다. probe v5/v6가 각각 별도 grid JSON을 읽어 원래 codec·속도·평활화와 실제 detector를 거친다.
- **`evaluate_v1.py:31–38`:** 새 v2 환경의 실제505 입력으로 SpecialistPolicy를 생성하고 `PPOTrainer.load`의 전체 identity 검사로 final checkpoint를 로드한다. `parallel.FIELDS`의 state/events/mask/priority_events/priority_mask 순서로 전달하며 deterministic action을 사용한다. 이후 reset에서도 환경 계약을 대조한다. 학습에 포함된 transition과 분리된 현재 목표 재평가다.
- 이 evaluator는 현재 기본 목표·tempo·4초 horizon과 CUDA에 한정돼 있다. 다른 event/tempo 설정을 자동 재현하는 범용 평가기로 설명하면 안 된다. 그런 task 차이는 기존 strict contract가 거부한다. 반복된 동일 prepared start 두 회는 새로운 곡이나 독립 초기 분포의 일반화 표본이 아니다.
- **`check_setup_v1.py:24–32`:** cost weight를 제외한 설정, initial model tensor 전체와 Torch CPU/CUDA·NumPy·Python RNG, training contract를 비교한다. 생성된 `setup_comparison_v1.json`에서 두 손 모두 이 동등성 검사가 참이고 cost는 `[1.0,0.1]`, 전체 모델 parameter 수는2,920,528이다. `reset_initial.json`은 pin하지만 실제 native reset 값의 쌍별 동일성을 비교하지 않는다. 따라서 이 산출물 자체의 증명 범위는 모델/RNG/설정/계약 동등성이다.
- **`analyze_runs_v1.py:16–28`:** 완료·persistent 감사가 성립한 실행만 읽고 전체 transition 수를 committed report와 대조한다. 현재 N2/H240 설정에서 JSONL 한 줄은 동시 control tick이며, 줄 번호를 H로 나누어 update를 구분하는 계산이 맞다. 성공·실패는 완료 episode에서 집계하고 비용 가중치·업데이트 수·원래 음악 매칭을 별도로 기록한다.
- **`analyze_runs_v1.py:26`, `:37`:** 행동 지표는 선택 손의33/6채널에서 각 tick RMS를 계산한 뒤 그 값을 평균한 `mean_action_rms`다. 비활성 손의0으로 희석하지 않는다. 전체 시간·채널을 한 번에 제곱 평균한 pooled RMS와는 다르므로 문서에서도 **활성 손의 tick RMS 평균**으로 읽어야 한다.
- **`analyze_runs_v1.py:25`, `:35–36`, `:44`:** 기타·발의 최대/평균 변위와 지지 비율은60Hz control endpoint 표본이다. 240Hz 전체 표본의 최대나 실패 gate의 평가 주기를 뜻하지 않는다. `all_support_presence60`은 지지 세 곳 중 **하나 이상 존재한 비율**, `triple_support_presence60`은 세 곳 모두 존재한 비율이며 양발은 별도다. probe의 `minimum_marker_m`도 각 tick 마지막 표본의 최소다.

## 실제 궤적 확인

| 기록 | 독립 확인한 표본과 성취 | 해석 |
| --- | --- | --- |
| `left_servo_v3` / `left_servo_v3_repeat1` | 각각240 ticks·960물리 표본·4초, 물리 실패 없음, 올바른 약지 contact/hold 성취, 최장 연속 후보2.870833333초, reach 집합 비어 있음 | 같은 초기 조건의 scripted 접촉 후보 재현. 원래 음악 matched50/100은0, 최종 release 미측정 |
| `right_grid_native_v1` | target2 후보3개가 모두 speed 사유로 무효. down 속도 약0.04226/0.04257m/s, up 약−0.04262m/s | 원래 최소속도0.05m/s를 완화하지 않고 실패로 남긴 기록 |
| `right_grid_native_v2` | 240 ticks·960물리 표본·4초, 물리 실패 없음, target2의 down/up/down 후보가 모두 유효. 속도+0.084857862/−0.085783307/+0.085190083m/s, down2회. cross 단계 성취 참 | 기존 조건 안의 scripted 기하 타현 성공. timed50 매칭 및 원래 공동 음악 매칭은0 |

LH 두 trace의 최대 정규화 행동 절댓값은1.0이며 반대 손은0이다. RH grid v2는 최대0.717510768, 반대 손0이다. 모두 기존 환경 step을 통과한 동작이다. 이 수치는 탐색기/servo가 현재 정책 행동권 안에서 실제 성취 동작을 만들었다는 근거이며, 학습된 policy의 능력이나 두 손을 결합한 음악 성공을 뜻하지 않는다.

위 네 기록의 각 `inputs.json`에는31개 경로가 있으며 검수 시 재계산한 SHA 변화는 모두0이었다. 이는 그 목록에 대해서만 성립한다.

## 입력 보존과 문서의 범위

`probe_v1.py:34–38` 및 후속 버전, `evaluate_v1.py:25–26`의 `project_source_paths`는 reset 이전에 이미 import된 프로젝트 Python과 명시된 파일을 pin한다. 각 `source_unchanged=true`는 **그 inputs 목록**의 종료 전후 불변을 뜻한다. 뒤늦은 동적 import, 모든 asset·mesh·compiler 입력과 원래 실험 전체의 parity까지 이 flag 하나로 인증하지 않는다. 최종 보존 감사는 원래 native input union SHA와 실제 학습 runner의 imported-source/asset 감사를 별도로 연결해야 한다. 원문 report를 고쳐 인증 범위를 확대해서는 안 된다.

문서의 parameter 수는 비활성 branch까지 포함한 **전체 모델** 수로 고쳐졌고,15mm reach는 실제 hold 성공의 필수 승격 gate가 아닌 선택 진단이라고 명시됐다. RH 성공 경로의 y≈−0.36m/depth≈4mm/앞뒤≈8mm와 기존 학습 기본 guide의 차이도 구분한다. 같은 native 목표/영역 안의 다른 후보 경로를 찾았다는 사실을 실험 도중 학습 guide를 바꾼 것처럼 설명하지 않는다. 학습 reward 증가·checkpoint 생성·scripted 성공을 전문가의 학습 수렴이나 양손 결합 성과로 바꾸지 않는다.
