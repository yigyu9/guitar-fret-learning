# DOF force 관측·저장 분석 통합 검수

검수일: 2026-10-07. 범위는 이번 두 native attempt의 저장 기록, 새 `analyze_dof_force_observation.py`·`plot_dof_force_observation.py`, 현재 계획·결과·누적 보고서 및 승인 전 어깨 PD 제안이다. 기존 코드 검수 두 파일과 원자료를 수정하지 않았으며 reviewer native 실행은 없다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 성공한 force 관측은 기존 움직임을 재현하지만 기타 유지·물리 지지 성공이나 PD 부족의 원인을 입증하지 않는다.

## 실행·자료 보존

- 첫 native attempt는 지원 true 후 `std::bad_alloc`으로 0step에서 실패했고 sensors는 빈 배열이다. 참조 보존 수정 후 별도 attempt_v2가 120step을 완료했다. 각 실행 메타의 producer SHA와 v1/v2 보관본, 실패 분석 producer·로그의 대응을 확인했다. 성공만으로 wrapper 수명이 단독 원인이었다고 확정할 수 없다.
- 성공 실행의 sensor 6개·native 13개 계약은 모두 통과했다. states/trace/controls/contacts/hands/queries/leg_torques 7개 배열을 기존 PALM_RATE 0.5초 원자료와 직접 대조해 전체 exact를 확인했다. 기존 PI·rate·box·목표·물리를 바꾼 실행이 아니다.
- force report의 명시 입력 SHA 167건과 summary 입력 170건을 현재 파일과 대조했다. 첫 실패와 성공, 기존 동결 코드 검수와 분석 실패 자료를 구별하여 보존한다.

## 시점·수치 독립 대조

- finite 센서 행렬은 120×105이며 native type 1/회전형, 단위 Nm다. 완료 step `n=1…120`의 sensors[n−1]·states[n]와 직전 제출 목표 controls[n−1] 대응 및 시간 `n/240`을 확인했다. Step0은 미측정 null이며 120개 nonzero 표본은 관측이다.
- 분석 :36–44의 control step 범위는 1…120으로 수정되어 저장 raw와 일치한다. 최초 0…119 guard로 실패한 분석 소스·실행을 보존했고 현재 변경은 이 범위 한 줄이다.
- 두 선택 관절의 전체 force 곡선·post-step scalar gap 및 min/max/절댓값 peak step/최대·최종 gap을 재계산했다. L_Shoulder_x는 −14.536088943…+0.112701349 Nm, peak step1, gap 최대·최종 21.619761704°다. R_Shoulder_z는 −1.187056422…+5.564083576 Nm, peak step1, gap 최대·최종 17.266791646°다.

## 최종 그림·문서

실제 지원 plot CLI를 새 `/tmp` 출력 경로에서 실행하여 canonical 2355×1029 PNG의 byte/RGBA 일치와 summary/report/producer/output 및 embedded 170/167 SHA를 확인했다. 직접 시각 QA에서 완료-step 시간, t0 미측정, Nm 부호와 도 단위 scalar gap, 범례가 맞았다. 센서값이 nonzero이어야 한다는 plot gate는 없다.

README:22의 Z +5mm 위치와 기존 회전 분리 표현을 확인했다. README:9·13·18–22, CHANGED_FILES:4–8, VISUAL_REPORT:862·868·870, main PLAN:956·README:436의 수치·링크·실행 범위가 맞는다. 기타 최대 오차 36.091149 mm/4.761921°와 LH source-center 최대 이탈 90.540508 mm는 이전 그대로다.

총 DOF force는 actuator 전용 토크·접촉력·effort 포화나 PD 원인으로 분리할 수 없고, scalar 좌표 차이는 실제 상대 회전각이 아니다. 어깨 stiffness 200→300 제안은 Shoulder6만 변경하고 damping50/effort150 및 다른 조건을 유지하는 승인 전 계획이다. 0.1→계약 통과 시 0.5초 범위이며 1초는 포함하지 않는다. 아직 구현·실행되지 않았고 관측만으로 gain 부족을 전제하지 않는다. 현재 소단계 검수를 완료하며 이 리뷰를 동결한다.
