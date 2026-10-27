# 새 유지 제어 후보의 압현 준비 기하 — 사전 추가 범위

현재 요구조건은 `paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/REQUIREMENTS_v2.md`이다. 이 문서는 향후 평가 설계이며 새 후보의 압현 성공 결과가 아니다. 기존 `diagnose_fretting_prepare_v1/audit_v1.py`와 baseline8의7항목 통과, 원2.7mm 단일 고정점 실패는 그대로 보존한다.

## 변경 이유

기존11–16초 정지의 지정3번 줄·5프렛 기하 준비만으로16초 이후 몸통·왼손 유지 보정이나 재접촉 후 복귀를 인증할 수 없다. 새 후보가 채택되면 실제 동작 뒤의 같은 지정 목표를 추가 확인한다. 엄지 보정이 검지 목표를 직접 변경하지 않는다는 사실과 실제 검지의 접근 성공은 구분한다.

## 그대로 유지하는 검사

원본 검지 말단의 삼각형 표면과 현재 기타 좌표의3번 줄 표식/5프렛을 사용한다. nut측 bar 모서리에서0.5–5mm 영역의 하부 피부 교차, 선택 재료점–활성 기타89형상별 분리 평면0.25mm, 다른5개 줄 표식과 최소0.1mm 간격 및 교차0, 선택 검지의 원 관절 범위와 목표 범위, 전체 검지 말단–기타89형상1mm source 상한을 원 조건대로 유지한다. 손가락 전체 FK 절대 pose나 새 피부점을 고정 WORLD 목표로 치환하지 않는다.

현재 string 표식에는 source/native 충돌 형상이 없으므로 선택 현 압현력은null이고 실제 선택 현 압현 성공은false다. 일반 neck/fret5의 양성 접촉과 selected-string force를 구분한다.

## 추가 실행 구간

- [ ] 새 baseline의 기존11–16초와 보정 후17–22초를 각각 연속5초로 검사한다. 각source301개/native접촉1201개와 전체raw sequence를 확인한다.
- [ ] 새 regrasp의 원 지정 dwell38–43초를 같은 기하 조건으로 검사한다. 원43초 일정이나 준비·이탈·접근 시간을 바꾸지 않는다. 단독 regrasp 성공으로 최종 연속77초 성공을 상속하지 않는다.
- [ ] 향후 새77초의 재접촉 dwell50–55초에도 적용한다. 마지막 재해제62–77초와 해제 타현은 별도 물리 gate다.77초 제어와 실행은 현재0이다.
- [ ] 새코드에서 실제 새 core/source/설정/Root before-after/코드 SHA와 exact gate 집합을 연결하고 누락된 전체 human–G 감사도 종합 guard에서 요구한다. 기존 V1의 baseline8 특정 경로나 oldMotion metadata를 새 후보 성과로 전용하지 않는다.
- [ ] 실제 schema CPU와 부정 fixture, 독립 검수·Root ACK 뒤 새 output에만 실행한다. 계산 실패·원 actual105 엄격 EPS0 잔차·available force 한계·source certificate 한계를 보존한다.

새 보정 후보가 먼저 정적 선정/생산 구현 검수와 baseline 동적·source 필수 조건을 통과해야 한다. 이 설계만으로 새 native/압현/안정화 성공을 주장하지 않는다. 새 PPO는 시작하지 않는다.
