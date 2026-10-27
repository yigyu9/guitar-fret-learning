# 자유 기타 학습 연결 구현 결과

정본 음악 목표·관측·행동·압현/타현 측정·보상/비용·종료·네트워크·PPO 수집을 현재 자유 기타 환경에 연결했다. **CPU 84개 검사와 실제 native 96단계 수집·PPO 업데이트 1회가 통과했다.** 실제 연주 학습이 수렴한 결과는 아니다.

- [현재 개발 코드](/home/ajou/yigyu/3/guitar_learning/README.md)
- [입출력·상태468·보상식·종료·네트워크·실행법](/home/ajou/yigyu/3/guitar_learning/TRAINING.md)
- [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_training_interface_20261018.md)
- [변경 전24파일 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_training_interface/archive_manifest.json)
- [독립 최종 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/review.md)

## 구현한 것

| 구성 | 현재 구현 |
| --- | --- |
| 관측 | 상태468, 이벤트64×24와mask, 우선2×24와mask; 실제 움직이는 기타 기준 상대 위치/속도, 전체105관절 상태와 제출 목표 포함 |
| 출력 | 왼팔/손33+오른팔꿈치/손목6의39행동, 관절 한계/속도/평활화 적용; 하체는 기존 유한 접지 제어 |
| 음악 | 정본05_BN2-131-B_solo B/C/D 구간, 이벤트 ID/원 시각/SHA 보존, 토큰·현재/준비/마감 우선 목표 |
| 압현 | 지정 손가락·현·프렛 실제 접촉 후보, 열린현 방해 접촉, 구간 양 끝 유효 유지 시간 |
| 타현 | 현재 기타 좌표계의240Hz 유한 현 선분 통과, 깊이/영역/속도/방향/재준비와 구간 내 시각 |
| 평가/보상 | strict50ms·lenient100ms 매칭, 미스/오타현, 유지/목표 접촉 후보 소실, 접근/행동변화 |
| 안정성 | 기타/발 편차와 양성 raw 지지/접지 비용, 접촉 소실 유예, 안전 실패·시간표 완료·시간제한 구분 |
| 망 | 상태256²·이벤트128²·attention·현재/마감 우선토큰·fusion512/512/256, 독립Actor/Value와 reward/cost 두critic |
| PPO/수집 | 단일환경 실제rollout, terminal/truncated/경계bootstrap, KL/실패 rollback, 엄격계약체크포인트 |
| 실행기 | 명시한 예산, 기본 준비2초, 원자료/관측/보상/rollout/체크포인트와 입력 전후SHA 기록 |

Root만 고정하고 자유 기타·중력ON·스트랩OFF·105/97/8을 유지했다. 기존 모델·자세·충돌 정책·의자·gain과 공용 과거 실행은 변경하지 않았다. 기타 직접 보조 힘이나 반복 상태 주입으로 대체하지 않았다. 현재 정책은39축을 학습하며 하체의 비영범위16축은 정책 출력이 아니다.

## CPU 검증

[최종 검사 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/cpu_tests.txt): 84개/5.555초/OK. 기존 환경 검사와 음악/타현/측정17개, 정책/PPO/collector15개, 학습환경 통합4개를 포함한다. 강체 공동 이동의 거짓 타현, rearm·깊이·영역, 실제 기록 재측정, 열린현/해제, 해제창의 토큰 보존, terminal/truncated/수집경계 bootstrap, rollback/체크포인트, 첫 substep만 위험했다가 복귀하는 경우의 실패 누적을 검사했다. 기록 재생/합성 CPU 검사와 아래의 실제 동역학 실행을 구분한다.

## 실제 연결 시험

[원자료 디렉토리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/native_v1) · [실행 보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/native_v1/report.json) · [읽기 전용 재집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/native_audit.json) · [실행 로그](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/native_v1_console.txt).

PhysX CPU, GPU pipeline OFF, 정책 CPU에서 실행했다. medium/state468의 실제 파라미터는 **1,931,600개**다. 시험 행동 반범위는 **0.002rad**이며 기본 학습 범위0.25~0.5rad와 다르다. 96개 정책 전이·384개 학습 물리 표본, reset2회 각각 실제 준비2초, 총 물리5.6초다. 첫88단계에서 시간표를 완료하고 두 번째 reset 이후8단계를 더 수집했다.

| 확인값 | 실제 결과 |
| --- | ---: |
| PPO 업데이트 | 1 |
| analytic KL / 한도 | 0.001617014 / 0.02 |
| KL 재시도 | 0 |
| 전체 파라미터 변화L2 | 0.378099231 |
| actor / reward head / cost head 변화L2 | 0.020118597 / 0.006304790 / 0.005480526 |
| 첫 완료 에피소드 보상 / 비용 | −0.483911216 / 0.000002722 |
| strict / lenient 타현 매칭 | 0 / 0 |
| strict 미스 | 1 |
| 목표 압현 유지 | 0초 |
| 안전 실패 | 0 |
| 삼중 양성 지지 / 양발 접촉 표본 비율 | 100% / 100% |
| 준비 후 기타 최대 이동 / 회전 | 0.0409841mm / 0.000104298rad |
| 발목 최대 이동 | 0.000765237mm |

정본 첫 목표는 **실제 현2·프렛7·약지**, onset1.12초/end1.3522초다. 초기 자세의 현1·프렛5·검지 진단 목표를 정본 목표로 바꾸어 사용하지 않았다. 지정 목표 후보가 없으므로 압현 유지와 타현 매칭도0이다. 실제 목표 시점 후 미스−0.5가 한 번 발생했고, 보상 합산과 에피소드 종료/재시작, 배우와 두 가치 head의 실제 업데이트를 확인했다. 안정성을 유지했다는 사실을 음악 성공으로 집계하지 않았다.

마지막 물리 표본만 검사한 결과가 아니라384개 학습 물리 표본을 재집계했다. 이 작은 행동의 짧은 연결 시험은 기존V3 장시간/하중 분담/완전 비접촉/전체83초 연속 검증이나 Root 자유 균형을 대체하지 않는다.

## 재현 자료와 보존

- `native_v1/arguments.json`, `training_contract.json`: 실제 옵션과 상태/행동/음악/보상/종료 계약.
- `reset_0001/0002.json`, `initial_values.json`, `transition_*.json.gz`, `final_state.json`: 실제 reset과 매 정책 단계의 native 상태/접촉·음악·안정성·보상.
- `rollout_0000.pt`, `initial.pt`, `checkpoint_0000.pt`, `update_0000.json`: 실제 PPO 입력과 전후 정책·optimizer/RNG.
- `inputs_before.json`: **1,564개 입력 SHA**. 실행 후 변경0, 실제 import 누락0, 원 물리/모델 source parity 오류0. Human/guitar XML의 mesh 선언 전부와 실제 compiler·곡 입력을 포함한다.
- [실행 당시 소스 보관](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_training_interface_v1/source_run_v1_manifest.json): 이후 설명 문서 갱신과 구분해 실제 실행 당시 파일을 보존했다.

별도 검수에서 발견한 해제창 토큰 누락과 새 음악 의존성의 원 물리 parity 오분류는 native 실행 전에 수정하고 회귀검사/재확인을 거쳤다. 과거 원자료를 수정하거나 누락을 소급 채우지 않았다. CLI 실행은 정상exit0이었다. 기존 장면 로딩의 visual geom/articulation 경고가 콘솔에 남으므로 이 실행을 시각 형상의 검증 결과로 사용하지 않는다.

## 남은 구현·검증

1. 전체 곡의 `event-000042` 복합 `alternate_restrike` 표현·타현 분리. 현재 선택에 포함하면 명시적으로 거부하며 조용히 제외하지 않는다.
2. 기본 학습 행동 범위에서 실제 도달성·안정성, 보상/비용 크기와 연주 수렴 평가. 이번 작은 행동 시험으로 확정할 수 없다.
3. 단일음→두 이벤트→구간의 자동 단계 승급과 병렬 수집. 현재는 B/C/D를 명시적으로 선택하고 단일 환경으로 수집한다.
4. 하체를 정책 자체가 학습하는 역할 확장. 현재는 전체 관절을 관측하지만 하체 목표는 외부 유한 제어다.
5. 실제 현 압력·진동·음향. 현재 지정 목표 후보 소실은 완전 왼손 비접촉을 뜻하지 않으며 타현은 기하 검사다.

기존 정책 체크포인트는 새 계약에 호환되지 않는다. 새 체크포인트 복원도 PPO/optimizer/RNG에 한정되고 새 물리 에피소드에서 시작한다. 장시간 학습은 이번 작업에서 수행하지 않았다.
