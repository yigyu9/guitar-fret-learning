# 단계 2: 현재 접촉 판정과 실제 음별 보상 검증

2026-10-27 구버전 진단 완료. **현행 판정으로 네 손가락 모두 정적 접촉을 만들 수 있었으나, 빠른 준비 뒤 원래 음 길이 안에 달성한 것은 24개 중6개이고 중지는0/6이었다.** 장기 hold의 접촉 가능성과 실제 음악 시점의 수행을 구분해야 한다. 이 단계에서 학습·정책 수정·물리 속성 변경은 하지 않았다.

구버전 GPU 수집은 **12:25:48 KST**에 종료했다. 마지막 실행의647개 입력(활성 Python510개 및 모든 진단 support Python 포함)이 실행 전후 동일했고 simulator를 정상 종료했다. [수집 종료 봉인](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/source_capture_complete.json) 이후에는 다음 단계에서 패키지가 변경될 수 있으므로, 아래 결과는 해당 봉인 버전의 기록이다. 이후 현재 작업 트리와 같다고 주장하지 않는다.

## 판정과 시간의 구분

- **Source FK 후보**: 실제 메시 표본으로 계산한 목표각의 기하 후보다. 충돌·하중·제어 추종을 통과했다는 뜻은 아니다.
- **정적 candidate**: 원래 선택 음의 audible midpoint와 selected mask를 명시적으로 고정해 현재 positive/wrong v2를 검사한다. 실제 physics는240Hz로 진행하지만 곡 원장은 지급하지 않는다.
- **실제 원장**: 원래 음의 press/onset/end/required를 유지하고, 명시적 phrase offset으로 원래 press를 local3초에 맞춘다. 실제 단조 clock에서 `begin_control → 실제 substep4회 → end_control`을 실행한다. 원래 곡 전체 평가와 다르고, 다음 단계의 **audible onset-local3초** 조건과도 다르다.
- **학습 성공**: 이번 단계에는 학습 정책이 없다. 모든 teacher는 실제 자세 오차를 읽어 유한 행동으로 진단하는 도구다.

고정/자유 기타는 같은 현재 강체 자산·충돌 필터·마찰·solver를 사용한다. 고정 여부 외의 속성을 바꾸지 않았다. source 상태는 준비 episode reset 때만 설정했고, 그 뒤에는 기존39차원 행동·native 관절 범위·손가락1rad/s 속도 제한을 통과했다.

## 도달 진단

목표는 탐색 전에 [선정표](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/selection_precommitted.json)로 고정했다. 이전 대조16개와 최종24개(손가락별6개)를 각각 탐색했다. 24개 source 기하 후보가 모두 있었지만, 이를 실제 도달 증거로 사용하지 않았다.

아래 값은 손가락별6개 중 **가장 긴 hold 구간의 현행 candidate 연속시간**이다. 오래 걸리는 진단에서는 손목 종료를 shadow로 계산했으므로 이 표에는 shadow 실패 이후 값이 포함될 수 있다. 이를 살아 있는 학습 episode의 수행으로 해석하면 안 된다.

| 조건 | 검지 | 중지 | 약지 | 소지 |
| --- | ---: | ---: | ---: | ---: |
| source 목표각, fixed/준비 참조 | 0.013초 | 0 | 0 | 0 |
| source 목표각, fixed/다른 손가락 B | 0 | 0 | 0 | 0 |
| source 목표각, free/준비 참조 | 6.000초 | 0 | 0 | 0 |
| source 목표각, free/다른 손가락 B | 0 | 0 | 0 | 0 |
| 실제 pad point DLS, fixed/B | 1.096초 | 4.713초 | 2.033초 | 5.433초 |
| pad+wrist DLS, 2N 이상 전체 보정 정지 | 5.879초 | 4.713초 | 0 | 5.433초 |
| pad+wrist DLS, 고부하 안쪽 법선 보정만 제한 | 5.850초 | 3.683초 | 2.533초 | 3.971초 |
| 같은 보호, B/arm 동시2초 준비 | 5.675초 | 4.250초 | 5.775초 | 5.267초 |

정적 상세 원본과 전체24행 요약은 [비교 JSON](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/support/static_comparison.json), [보호 방식 비교](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/support/normal_guard_comparison.json)에 있다. 마지막 export 재생은 hold4초로 줄인 별도 실행이며, 위의 빠른 준비 hold6초 결과와 구분한다.

실제 source 목표각→controller 목표각은 약1e−5도 수준으로 일치했지만 actual q에는 팔/손가락 추종 오차가 남았다. 대표 중지에서 팔 약1~4도의 오차도 있었다. [축별 추종 기록](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/hold_tracking_axes.json)은 목표 codec의 큰 변형보다 실제 자세 추종과 접촉 궤적이 주요 문제임을 뒷받침한다.

DLS는 실제 패드 표본을 첫 보정 때 고정하고 native Jacobian으로 팔12축과 지정 손가락4축을 함께 보정했다. wrist task는 원래 guide box에19mm를 더한 범위의 최근접점으로 향하며, 원래 guide와30mm 종료 문턱은 유지했다. 고부하 보호를 전체 정지에서 안쪽 법선 보정 제한으로 바꾸자 약지 접촉이 회복됐다. 손목 보정을 함께 정지시킨 조건의 실패를 도달 불가능으로 볼 수는 없다.

### 실제 종료를 적용하면 제외되는 표본

빠른 준비에서도 row12/13 약지는4.496초에 손목 shadow 실패가 먼저 발생했다. 이 두 행의 늦은 candidate는 학습 episode의 수행 근거에서 제외한다. 마지막 전체24행 export의 [live 표본 집계](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/support/static_live_evidence60.json)는 lifetime shadow 실패 이후 표본을 제외한다. 이 집계는60Hz PRE-control 실제 자세 endpoint이며240Hz 전체 접촉 구간의 인증을 대체하지 않는다.

row8/9 중지는 shadow 실패 없이 정적 candidate가 있었고, 이후 teacher 추출도 이 두 행으로 사전 지정했다. row6 중지는 빠른 진단에서 순간 candidate가 약0.058초 있었지만 distal resultant가 최대95.37N으로 매우 커 안정적인 대표 접촉으로 채택하지 않았다.

## 실제 음별 원장 결과

[실제 원장 실행](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/ledger_fixed_B_fast_normal_guard/report.json)은 원래 press를 local3초에 맞춘 one-note phrase24개이며, b=1이다. 준비0.5초+동시2초 ramp 후2.5초부터 동일한 pad+wrist feedback을 사용했다. 선택 음이 끝나면 feedback을 중단하고 유한 해제 명령을 보냈다. 각 행의 첫 episode만 집계했고, 먼저 종료된 행은 정상 API로 reset해 나머지 행을 끝냈다.

| 손가락 | 실제 달성/선택 음 | 달성 row |
| --- | ---: | --- |
| 검지 | 2/6 | 0, 1 |
| 중지 | 0/6 | 없음 |
| 약지 | 2/6 | 15, 16 |
| 소지 | 2/6 | 19, 23 |
| 합계 | **6/24** | 정상 종료24개, 물리/손목 실패0개 |

중지 row8/9는 원래 음 창 안에서 candidate0이었다. 예를 들어 row8의 press~end는0.1387초, audible 길이는0.1174초다. 여러 초 기다린 뒤 성립한 정적 접촉만으로 짧은 음악 시간의 성공을 설명할 수 없다.

[지급 검산](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/ledger_fixed_B_fast_normal_guard/reward_verification.json)에서 다음을 확인했다.

- 최초 접촉0.25×최고 접촉 진행, 유지 clean/D, 달성0.25×달성 여부, 오압현−0.15×wrong/D, 수행부족−0.10×max(missing/D, 연속 미달성률)의 최대 오차 **1.19e−7**.
- PBRS 매 제어 tick `gamma*nextPhi−Phi` 오차 **2.98e−8**, terminal nextPhi=0을 포함한 할인 합산 오차 **9.79e−8**.
- 첫 episode의240Hz clock 연속, 원래 offset을 포함한 score clock의1/240초 진행, 모든 추적 값 유한.
- 실제 보상9항목을 개별 누적 기록했다. 실패 사례가 없는 이 실행만으로 실패 tick의 양수 억제·강한 종료 비용을 모두 검증했다고 보지는 않는다.

실제 단기 수행 실패는 이번 24개 대조에서 보상 지급 누락으로 설명되지 않는다. 지정 손가락까지 움직이는 진단 teacher조차 중지의 짧은 음 창을 놓쳤다는 점이 다음 제어/학습 구조 비교의 출발점이다.

## 물리 하중과 메시의 확인 범위

실제 human shape readback에서 rest_offset=0, thickness=0, contact_offset≈0.1mm, friction=1을 확인했다. 기본 AssetOptions의 thickness2cm가 실제 human에 남았다는 가설은 이 결과와 맞지 않는다. [실제 shape/force readback](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/teacher_fixed_B/human_shape_and_force_readback.json), [native DOF force 요약](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/teacher_fixed_B/dof_sensor_summary.json)을 보존했다. POSITION 관절의 명시적 외부 effort0과 실제 drive 응답은 다르다.

[Source convex hull 검사](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/source_hull_audit_with_thumb.json)에서 네 손가락과 엄지128개 source 표본은 source convex envelope에 거의 놓였고0.1mm를 넘는 깊은 내부 표본은 없었다. 이는 PhysX가 실제 생성한 cooked shape의 직접 readback은 아니다. 엄지 후면 기하와 실제 접촉 하중이 불일치하는 원인까지 해결한 것은 아니다.

**2N은 하중 상한이 아니다.** 고부하 보호는 안쪽 pad 오차를 제거하고, 현재 native point Jacobian과 controller smoothing으로 선형 예측한 다음 target의 안쪽 법선 이동을 막는다. 접선 이동·손목 보정·동역학·다른 패드점의 침투로 actual resultant는 커질 수 있다. 동일 보호의 느린 row6에서는55.18N, 빠른 row6에서는95.37N을 관측했다. 물리 force cap/PD/재료를 바꾸거나 더 깊게 밀어 성공을 만들지 않았다.

## 다음 단계용 팔 teacher

정합된 schema는 다음 **v2 파일**이다. 원래 봉인된 문자열 finger 버전과 source_capture manifest는 보존했다.

- [중지 row8 teacher](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/short_finger_teacher_middle_row8_v2.json): 실제5.45초, candidate·wrong0·lifetime 손목 실패 없음·손목 이탈20mm 이하, distal resultant1.59N.
- [중지 row9 teacher](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/short_finger_teacher_middle_row9_v2.json): 실제5.067초, 같은 조건, distal resultant10.24N.
- [v2 파일 SHA 목록](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/teacher_exports_v2.json).

`schema=short_finger_teacher.v1`, finger=2, finger_name=middle, arm_targets_rad는왼팔12축의 실제 controller target이다. ramp_s=3은 다음 단계에서 사용할 설정이며 source 궤적의2초 ramp와 다르다. source raw trace/metadata/wrapper/report 경로와 SHA, native 축 매핑, 실제 팔각과 지정 손가락의 reference/contact actual/contact target각을 별도 metadata로 담았다. source 접촉은 팔12+지정 손가락4 DLS가 만든 것이므로 **팔만 고정하고 지정4축을 reference 또는 행동0으로 둬도 접촉한다는 검증은 아직 없다.** 다음 단계의 정책은 지정4축만 제어하며 이 경계를 별도로 검증해야 한다.

## 남은 검증과 증거의 한계

- 물리 negative 대조군 전체는 미완료다. 다른 줄/프렛, 타손가락 높은 프렛, 같은/낮은 프렛의 비감점, 잘못된 패드 방향, 하중 없는 근접,50ms 미만, 해제를 한 요인씩 재현하는 원장 대조가 필요하다. 이번 자연 발생 wrong/미달성은 이 대조군 전체를 대체하지 않는다.
- free 기타에서는 source 목표각 재생만 검사했다. 안정 접촉 DLS+실제 원장 결과를 free 조건까지 일반화하지 않는다.
- 중지의 static 도달 이후 빠른 음악 수행, 팔-only teacher와 지정4축0 대조, 실제 정책이 이를 배우는지는 다음 단계의 과제다.
- 초기 정적/teacher 비교의 package 입력은 전후 SHA를 검사했지만 당시 `native_point*_teacher.py`와 detailed adapter는 입력 목록에 빠져 있었다. 종료 시 wrapper SHA만으로 실행 도중 불변까지 입증하지 못한다. 해당 원본은 보존하고 이 한계를 기록한다. **실제 원장과 마지막 teacher export는 실행 전 support 전체 Python도 pin하고 전후 검증했다.**
- 이번 결과는 기하·부하·오압현 판정이며 접촉 상대별 calibrated pressure나 실제 소리를 인증하지 않는다.

## 후속 읽기 분석: 고정 손목 pose 후보

관절 target을 재생해도 실제 접촉 자세가 재현되지 않은 원인과, 지정 손가락4축을 대신 제어하지 않는 팔12축 손목 pose 안내 후보를 [후속 제안](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_failure_diagnosis_v1/02_contact_reward/fixed_wrist_pose_proposal.md)에 정리했다. CPU FK 교차 검산과 별도 JSON export만 수행했으며 이 후보의 GPU 가능성은 아직 검증하지 않았다.
