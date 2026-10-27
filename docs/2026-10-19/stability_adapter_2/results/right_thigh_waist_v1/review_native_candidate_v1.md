# 오른 허벅지 waist 수락 후보 연결 검수

판정: **문제없음 — 선택 후보의 제한된 native 정지5초 실행 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건. 실제 native 결과·걸침 성공을 선인증하지 않는다.

선택은 source4의 [shift95_front30mm candidate](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/search_v4/shift95_front30mm/candidate.json:1)다. `EnvironmentContract`로 candidate/reference SHA·native 순서81·전체 초기각 한계를 확인했다. R_Elbow_y 초기2.029893398285rad에서 ±5° 요청은 모델 한계 안이며 추가 하한/상한 여유는2.117159870709/0.675367099488rad이다. fingers42는 이전 B 기준과 exact다.

config는 이전 B 정지 설정에서 candidate 경로/SHA만 변경됐다. 정지 amplitude0·Thorax40N/16mm·Shoulder10N/4mm·body150/1·native reference와 나머지 제어/물성 설정은 동일하다. 기존 helper가 읽는30% witness·legacy 호환 키와 genuine human predicted poses66개가 존재한다. [runner2 사전 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_thigh_waist_v1/review_native_preflight_v1.md:1)의 코드 SHA도 그대로다.

source whole LP clear와6caps 양수, waist flank gate를 확인했다. RHip0.299978mm/LHip1.460013mm, Thorax2.231318mm/Shoulder0.098443mm/forearm29.650887mm/Chest0.934723mm다. 왼 analytic clearance는3.000004/6.367997mm이며, 왼 wrist/Head 방향과 자연 팔 gate를 통과했다. 이 간격들은 source 형상 측정이다.

기타 회전은 seed 원본값과 exact이고 전체 predicted guitar body state39개가 존재한다. 모든 body가 동일 root delta로 이동하고 회전이 보존됨을 독립 재계산했다(위치/회전 잔차 최대1.11e−16). 예측 기타 속도는 모두0이다. metadata 요청 delta와 float32 기타 p의 실제 delta 차이는3.04e−8m로, source 요청값과 native 실제 이동량은 따로 기록한다.

## Warning

- 후보 waist witness G_y−0.363487530m는 확대된 **+15mm flank 구간** [−0.365562980,−0.278240536]m 안이다. 좁은+5mm core 충족이나 cooked 접촉·실제 걸침·힘 분담을 뜻하지 않는다. native의 실제 초기 상태/접촉점·기타 변화·왼손/기존 두 block 기여를 별도로 판단한다.
- [runner2 초기 검사](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v2.py:52)는 전체 G pose 배열의 허용오차 검사이며 실제 초기 전체 JSON exact 판정과 다르다. 사용자 허용에 따른 G 초기 p 변경이며, 원래 G0 위치 invariant를 재사용하지 않는다. source 예측 상태와 실제 native 상태·PD/질량/source LP/입력 SHA 통과를 실행 후 확인해야 한다. 임의 움직임·연주·반복 강건성은 범위 밖이다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| candidate.json | a6b833164432fbd732b8120949926875153383e333f7a635586dcf6629124876 |
| config.json | 0da6b6267f059cfe1590130fb4fd327e95a053eeb9a49adeec2ea184ed6fb062 |
| shift95_front30mm_audit.json | 9560b3d84530d16fe3949414031906a5ef9ac4c6a0c48dfbf0053759c18e9a1a |
| run_right_thigh_waist_v2.py | 416a642eac68d14e3ebe2e162a9417f45b01cc7a2e6c10988cf16e234dc0b87e |

읽기 전용 후보·설정·기존 제어 연결 및 순수 산술 검수다. 새 fitting/native/정책 추론·학습을 실행하지 않았고 다른 소스·원자료·기존 리뷰는 수정하지 않았다.
