# 독립 검수 — three_face_arm_initial_target_v1

2026-10-08. 새 준비·분석 코드와 완료된 두 실행, 저장 기준, 최종 그림·문서를 읽기 전용으로 검수했다. 검수 중 native 초기화·물리 실행·생산 코드 실행·원자료 변경은 하지 않았다.

## 요약 판정

문제없음. 미해소 Critical / Warning / Suggestion 없음. 두 조건 모두 저장 기준보다 기타 오차가 악화하므로 채택하지 않는 판정이 측정과 일치한다. 최종 보존 감사는 root의 후속 작업이며 이 검수에서 완료로 주장하지 않는다.

## 코드·원자료

- 새 실행은 2회 초기화 / 2,400 physics step, 각각 5초·exit 0이다. 분석 7계약과 11,319개 명시 입력의 현재 SHA를 확인했다. 저장 reference 실행은 신규 집계에 포함하지 않는다.
- 저장 state0 전체, 초기 81 q·속도·기타 상태·PD·solver·LA가 기준과 같았다. 두 arm12 목표는 실제 초기 q와 같고 첫 finger21은 저장 절대 목표, 둘째는 초기 q이다. 다른48 목표와 최종66 인터페이스를 유지한다.
- 각 1,200 controls의 제출 81목표, 300회 갱신/4step hold, native bounds, 물리 고정 root·하체 구조를 확인했다. 목표 제출은 Python 기록 범위이며 별도의 SDK 목표 getter 인증으로 확대하지 않는다.
- 저장 기타 pose에서 위치 거리와 SO(3) 회전 오차를 독립 재계산했다. 포함 구간 0–24 / 0–1200 / 960–1200의 최대·종료값 및 arm12/finger21/torso9의 실제−목표 scalar 좌표 오차가 분석과 일치했다. t0는 계획된 첫 목표, 이후는 로그로 확인한 상수 제출 목표와 비교한다.
- 이전 state의 route 위치·속도로 두 실행의 1,200구간 수동 cable 법칙을 재계산해 오차 0 N을 확인했다. LA는 일정하며 제출 장력은 전 구간 0 N이었다. 비활성화나 단독 원인이라는 추론은 하지 않는다.
- 기타/body 접촉 집계를 독립 대조했다. Palm 양의 마지막 step 90/99, 전체 행 마지막 96/105; index3 양의 마지막11/11; R_Hip 양의 unique step 1,191/1,190이며 마지막1200이다. RH 손 행은 없다. 1,200개 연속 양의 접촉으로 해석하지 않는다.
- 첫 조건 최대 p/q 159.799114 mm / 25.272466°, 종료 159.795174 / 25.142339; 둘째 최대 157.516483 / 25.623971, 종료 157.510653 / 24.868219이다. 저장 기준 최대25.229274 / 7.770624, 종료21.912505 / 7.091529와 구별했다.

## 최종 미디어·문서

- 각 실행 151×2 실제 camera frame의 시점·뷰·SHA 및 네 MP4의 실제 ffprobe 151 frame / 30 fps / 5.033333 s와 SHA를 확인했다. 물리 관측 시간은 0–5초이다.
- Canonical 그림 두 개를 직접 열어 축·단위·범례·저장 기준 점선·양의 raw-lambda 시점 표시를 확인했다. Hands montage 네 셀은 해당 step0/1200 native 원 PNG의 동일 축소 결과와 pixel exact다.
- Artifact 14입력의 시작/종료/current SHA, 두 출력 SHA, 실제 producer 사본·manifest·로그·실행 연결이 일치했다. 실행 exit0 / 0.7822753069922328 s / native0·physics0이다.
- Phase README/CHANGED, main PLAN:1518·README:846, dated README:512, VISUAL §81:1529 / 그림116:1537·117:1543의 수치·실제 절대 경로/줄을 확인했다. 실제 runner는 변경하지 않은 run_seed2_support_warmstart.py:18이다.
- 다음 THREE_FACE_HALF_STRAP_SLACK_PLAN은 저장된 이전 절대목표로 돌아가 LA만 비교하는 미실행 계획이다. 여유 수식과 다른 자세의 과거 시험 범위가 구별되어 있다. 최종 봉인 스크립트는 읽기 검토만 했다.
- 문서의 runner 링크 정정과 ‘분석 입력 SHA’→‘analysis.json 결과 파일 SHA’ 표기 보완을 확인해 해소했다. 예정된 final_verification 링크는 후속 감사 경로다.

## 확인한 소스와 최종 한계

준비 SHA `98352c2a69955a8291c625c7bbcbb3e02e16115abbfdbb434c8e9f66f2246d2c`, 분석 SHA `4ff7cacf9f1a721b0b573e68a1a3d4ef2d444bf2b3895cd57c5fa7edf2bd8f0f`, 그림 producer SHA `b534d707478f2cb02101fb320ba441fd0d05934edd0057b5cfca2ec51e0fb50f`, analysis.json SHA `7a481c7061935999b9e85aacc52b6f174bf51463888a84b387347b376b059811`을 확인했다.

Source hull 근접과 선택 facet은 cooked clearance·해부학적 접촉면을 인증하지 않는다. Named-body contact와 raw lambda는 Newton 힘·면별 지지·연속 지지 인증이 아니다. Scalar DOF 좌표 오차는 whole-joint SO(3) 오차나 PD/중력 원인의 증명이 아니다. 기타 초기 복원·지속 유지·연주 안정화는 미완료다. 이 검수 기록은 최종 작성 후 동결한다.
