# 관절 유지 관측 독립 검수

검수일: 2026-10-08. 범위는 관측 wrapper·분석·최종 artifacts_v2와 해당 문서다.
원자료·구현·기존 동결 결과를 수정하지 않았고 신규 native 실행은 하지 않았다.

## 요약 판정

**문제없음.** Critical 없음, Warning 없음. Python 제출 목표 검사 범위와 rotational DOF 용어에 관한 Suggestion은 문서에 반영되어 해소됐다.

## 확인한 범위

- baseline/full은 각각 기존 .45 bias/전체 목표 보정이며 둘 다 sensor를 추가했다. 각 조건의 이전 states/trace/tasks/contacts/controls 5배열 exact와 2init/48step을 확인했다. 서로 다른 목표 조건을 sensor OFF/ON 비교로 표현하지 않는다.
- actor 생성 후 prepare 이전 sensor 활성화, 완료 step의 float32 force 사본, 상태·Python target·PD 조회 전후 보존, scene 정리 및 임시 class/argv 복원 경로를 검토했다. 각 6개 관측 계약·393 입력 SHA, 분석 5개 계약·410 입력 SHA가 확인됐다.
- 81개 DOF는 native DOF_ROTATION type 1이며 단위는 Nm다. 각 25개 상태와 step1–24의 24개 힘 샘플을 구분한다. t0 force는 None이고 임의의 0을 넣지 않았다. COM은 body 좌표, inertia는 COM 기준이라는 로컬 SDK 설명과 필드가 일치한다.
- Shoulder_x/Elbow_y의 좌표·속도·힘 최소/최대/종료값과 개별 body 질량 표를 저장 분석과 대조했다. full 종료 좌표 차이 .338013/.208089rad는 제출 목표 대비 native 좌표 성분이며 whole-joint SO(3) 오차가 아니다. native 목표 getter 인증도 아니다.
- canonical PNG를 직접 확인했다. 2×2 곡선의 라벨·rad/Nm·0–.1초 범위·힘 첫 샘플 시점이 올바르며 과학 그래프를 카메라 장면으로 표현하지 않는다. producer의 10입력·출력 SHA가 일치하고 실행 기록 exit0을 확인했다. 라벨 수정 전 producer/PNG는 artifacts_attempt_v1의 manifest SHA와 일치한다.
- phase README/CHANGED, 메인 README·PLAN, dated README·VISUAL §67/그림91과 후속 PD 계획·보완 기록·강성 분리 계획을 대조했다. 관측 2/48, 첫 PD 3/72 및 보완 PD 3/72를 구분하고 다음 stiffness-only 비교를 미실행 계획으로 둔다. PD §68의 최종 미디어 검수는 별도다.

## 검토한 source SHA

- run_palm_hold_observation.py: `9497e1fad2b26db6d35451075c7ea3fb489608712764d330964f7b7f08cfce4c`
- analyze_palm_hold_observation.py: `5cb084d0008b3749e2673e816d9a06800796cbad4ba791e8fb60a9b8cd2b435d`
- plot_palm_hold_observation.py: `626e31a5e884fc15204801629718ea6ac48dac0fd7d3c28b25615c2ec8d8fc4f`

## 남은 한계와 최종 상태

total DOF force는 drive-only torque·접촉힘·effort 포화·중력 또는 PD 부족의 원인을 분리하지 않는다. source gap·raw lambda와 짧은 응답으로 지속 지지나 기타 안정화 성공을 인증하지 않는다. 남은 actionable finding은 없으며 이 검수 기록은 최종 동결한다.
