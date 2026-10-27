# 사진 기준 오른팔·전완 제어 사전 검수

판정: **문제없음(거절 처리 정상)**. Critical 0 / Warning 1 / Suggestion 0. **source v2 수락 후보가 없어 현재 native를 진행할 수 없다.** V1/V2 계획·source v2·실행용 v2·완료 source 결과를 읽기 전용으로 검토했다. 추가 물리/학습 실행·다른 담당 파일 수정은 하지 않았다.

## source 결과

[수락 gate:39](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v2.py:39)는 전체 source clear·capsule 간격≥.1mm·전완 간격<30mm·자연 방향/손 위치·관절box·다른69 불변을 함께 요구한다. [search 결과](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/natural_right_arm_v1/search_v2/search.json:1)는 `selected=[]`, 두 후보 모두 `accepted_for_native=false`, `native_runs=0`이다. candidate/config 디렉터리는 생성되지 않았다.

| 손바닥 목표 조건 | 전완 gap | 상완 gap | source clear | 결과 |
|---|---:|---:|---|---|
| front120mm | 70.646679mm | .492653mm | true | 전완30mm 조건 미달 |
| front160mm | 79.647118mm | .490113mm | true | 전완30mm 조건 미달 |

팔꿈치 바깥/아래·손목 안쪽 방향과 손 목표 오차·다른69 불변은 통과했다. 두 후보 source overlap은0이며 관절box는 명시된1e−7rad 허용범위 내다. 상완 .5mm는 강한 선호항이고 실제 hard gate는 capsule≥.1mm이다. 이번 거절은 전완 거리가 원인이며 자연 방향이나 source 교차 실패와 구분한다. source 입력564개 SHA와 원사진/reference.jpeg 복사 SHA가 일치한다.

## 실행 코드의 변경 범위

- [전완 기준점:80](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v2.py:80): body-local motor point, COM, fixed-root Jacobian의 link index−1을 모두 R_Elbow로 선택한다. config에 `support_body=R_Elbow`를 저장한다. legacy `proximal_support` 필드는 이번 source 전완 witness이며 상완 접촉점으로 해석하지 않는다.
- [접촉 callback:106](/home/ajou/yigyu/3/stability_adapter_2/run_natural_right_arm_v2.py:106): 기존 상완/왼팔 endpoint와 Head callback을 유지하고 전완–바디 접촉 및 전완·손목·palm·Chest 실제 body state를 덧붙인다. 이전 callback의 행 추가 뒤 실행하며 read-state 불변 검사가 유지된다.
- right_indices·ArmEffortGuard·construction·factory/혼합69 step·control 함수의 AST가 보존된 run_om_no_strap_upper_arm_v16과 동일하다. 현재G8mm/요청40N·gravity/posture·effort cap·owner/window·속도오차10mm/s guard·latch를 유지한다. 기타 직접 force/attachment·runtime state 쓰기 권한은 추가하지 않는다. 실행 metadata는 새 phase/search/V2 계획·사진 SHA와 전완 설명을 기록한다.

Warning 1 — [정성 자세 기준:37](/home/ajou/yigyu/3/stability_adapter_2/search_natural_right_arm_v2.py:37): 단일 사진과 팔 segment 방향·관절box·palm 위치만으로 사진의3D 관절각, 손바닥 방향, 자연스러움 또는 실제 전완 지지를 인증하지 않는다. 이번 source 거절이 모든 자연스러운 자세의 불가능성을 뜻하지도 않는다. 현재 결과로 native/유지 성공을 주장할 수 없다.

핵심 검수 SHA-256:

| 파일 | SHA-256 |
|---|---|
| NATURAL_RIGHT_ARM_REFERENCE_PLAN_V2.md | 3b0fba937c994cfe9e815383cff1c709b706b5b0b2c584439e04d2adf596ea97 |
| search_natural_right_arm_v2.py | 0d907378c8c83d501e70dde9bf0ba761eeb702c64e65662d18fb017b64725720 |
| run_natural_right_arm_v2.py | a8aff3ac93785d041570218fa80815fa359847669705a3c85c3967c2a3b7756a |
| search_v2/search.json | f9a186b3c57a2a73e9447676683ebf079871dc177f2ce27bdbf8bf04819156a9 |
| reference.jpeg | 4f25ef42a0c1a507c9d03a363c773650687543bebfa93c7e898f53cfdbffbcb6 |

추가 실행 차단 코드 오류는 발견하지 않았으나 source 수락 gate가 두 후보를 거절했다. 새 native readback·Jacobian 관계·실제 초기 관통/접촉·자연스러움·기타 유지는 검증하지 않았다. 지정한 이 새 리뷰 파일만 작성했다.
