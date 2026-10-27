# 독립 검수 — three_face_half_strap_slack_v1

2026-10-08. 새 준비·분석 코드, 완료 원자료, canonical v2 그림과 최종 문서를 독립 검수했다. 검수 중 native/물리 실행·생산 코드 실행·원자료 변경은 하지 않았으며 이 파일만 작성했다.

## 요약 판정

문제없음. 미해소 Critical / Warning / Suggestion 없음. 최대 회전 감소와 위치·종료 회전 악화의 tradeoff를 구별하며 두 LA를 채택하지 않는 결론이 측정과 일치한다. Root의 최종 보존 감사는 후속 작업으로, 이 검수에서 통과를 주장하지 않는다.

## 코드·완료 원자료

- 신규 2 init / 2,400 physics step, 각각 5초·exit0이다. 분석 7계약·11,321개 current 입력 SHA와 실행 소스를 확인했다. 저장 support-loss 기준은 신규 실행에 포함하지 않는다.
- 두 native state0 전체가 저장 기준과 exact였다. 실제81 q·속도·G·PD·solver·초기 route·절대81 목표를 보존하고 trial 입력에서 고정 LA만 변경했다. LA는 1.0943400885564325 / 1.0868332051527874 m이다. 다른48 목표·최종66 인터페이스·물리 고정 root/하체를 유지한다.
- 각 1,200 controls의 제출81 목표·300회 갱신/4step hold를 확인했다. 목표 기록은 Python 제출 범위이며 별도 SDK 목표 getter 인증으로 확대하지 않는다. Source/FK 초기 admission은 cooked·해부학적 면 접촉 인증이 아니다.
- 실제 G pose로 world 위치 거리와 SO(3) 회전 오차를 독립 재계산했다. 포함 구간 0–24 / 0–1200 / 960–1200의 최대·종료값과 arm12/finger21/torso9의 scalar 실제−목표 좌표 오차가 분석과 일치했다. t0는 계획된 첫 목표, 이후는 로그로 확인한 상수 제출 목표다.
- 두 실행의 1,200구간을 이전 state의 route 위치·속도로 독립 계산해 passive cable 법칙과 적용값 exact, 오차 0 N을 확인했다. 첫 제출은 둘 다0 N; half 양의 첫/마지막 step36/1200·양의1160구간, zero 2/1200·1176구간이다. Cap300 도달은 둘 다0이다. Route 길이·변화율 극값도 일치한다.
- Half 법칙 최대/종료 12.894181676 / 1.063009510 N, zero 5.119047234 / 2.677262806 N이다. 시계열은 힘 구간 시작 0…1199/240초에 표시하며 적용값은 다음 trace1…1200에 기록된다. Native force sensor 또는 body raw lambda의 Newton 환산값이 아니다.
- 접촉 집계 독립 대조: palm 양의 unique1017/1044·마지막1200, thumb3 양의 마지막35/96·전체 행 마지막39/107, R_Hip 양의 unique1200 각각, RH 손 행0이다. 양의 시점/전체 행과 substep 연속 지지를 구별한다.
- Half 최대 p/q 30.696048 mm / 7.727219°, 종료30.695007 / 7.622948; zero 최대32.861798 / 7.103582, 종료32.860232 / 7.103303이다. 저장 기준 최대25.229274 / 7.770624·종료21.912505 / 7.091529와의 최대/종료 비교가 맞다.

## 최종 미디어·문서·보존 경계

- 각 151×2 camera frame 시점·뷰·SHA와 네 MP4의 실제 ffprobe 151frame / 30fps / 5.033333초·파일 SHA를 확인했다. 물리 시간은 0–5초이다. v2 PNG 두 개를 직접 열어 0–5초 축·단위·범례·저장 기준·구간 시작 장력과 완료-step 접촉 표시를 확인했다.
- Hands montage 네 셀은 step0/1200 원 native PNG의 동일 축소 결과와 pixel exact였다. v2 14입력의 pre/post/current SHA·2출력·실행 source 사본·manifest·로그가 연결되며 exit0 / 0.8706656479043886초 / native0·physics0이다.
- v1도 성공(exit0 / 0.8542346449103206초 / native0)했으나 후기 palm 표식과 범례가 겹쳤다. 전체 source/brief/wrapper/log/meta/manifest/2PNG를 exact SHA로 보존했다. v2는 범례 위치와 기본 새 출력 경로 두 줄만 바뀌며 hands PNG는 v1/v2 byte exact다. 물리 재실행은 없다.
- 한국어 README·CHANGED, main PLAN:1533·README:853, dated index:517, VISUAL §82:1551·그림118:1565/119:1571의 수치·실제 함수 줄·절대 이미지/MP4 링크를 확인했다. 분석 파일 SHA·11,321 분석 closure와 별도14 artifact closure, 양의 thumb 기록과 전체 행을 구별했다.
- 다음 THREE_FACE_NATIVE_FEATURE_MAP_PLAN은 저장3조건 offline/native0의 미실행 계획이다. Body/COM·child/fret 변환과 마지막 substep 시점의 불확실성을 먼저 검증하고 확정 면 분류를 보류하며 제어·gain·관절각을 변경하지 않는다. 최종 감사 스크립트는 읽기 검토만 했다.
- 산출물 작업자가 만든 pending review/audit 초안은 실제 결과로 사용하지 않았다. artifact_document_drafts의 두 원문 SHA와 보존 영수증을 확인했다. 새 AGENTS의 담당 외 placeholder 금지·소비 소스 보존 규칙과 CHANGED의 구분 설명이 반영돼 해소됐다. 실제 final_verification은 root가 이후 생성하는 감사 기록이다.

## 확인 소스와 최종 한계

준비 SHA `56d13d08738d9f70af5ad69ef51e0af6064f60422867b1bc57107e4a02e1fbd8`, 분석 SHA `889f7d690df6ea137d06f974487ee4ffb087eb95c0904faf7463184071692e6c`, analysis.json SHA `35e2054f93c863d299437842a79addcadafa40b6ec24f9dfceeaa232c87746e8`, canonical v2 producer SHA `f21ac1201e8b9300f4e5fd5ecb9f4fabafd01823d4310a98f4e039ec02a18a40`을 확인했다.

Source hull/facet 근접은 cooked clearance·해부학적 접촉면 인증이 아니다. Body contact/raw lambda는 면별·연속 지지나 Newton 힘을 인증하지 않는다. Scalar DOF 좌표 오차로 whole-joint SO(3)·PD/중력 원인을 단정하지 않는다. 자유 기타 초기 복원·지속 유지·연주 안정화는 미완료다. 이 실제 독립 검수 기록은 최종 작성 후 동결한다.
