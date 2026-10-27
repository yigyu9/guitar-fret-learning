# 사용자 기타 위치 범위의 바디 중심 좌표 보기

이 기록은 기존 actor-root 위치 범위를 유지하면서 같은 저장 기타 자세의 표시 기준점을 바디 중심으로 바꾸어, 사용자 범위와 팀원 Pelvis 상대 후보를 같은 좌표에서 비교한다. `body center`는 기존 local offset `[0, −0.4, −0.0217] m`로 정의한 **표시용 기준점**이며 실제 질량중심(CoM)이 아니다. 세 조건의 여섯 그림은 이전 phase가 저장한 native Isaac Gym t=0 raw frame와 depth/camera 정보를 사용한 후처리다. 이번 단계의 신규 native 초기화·물리 step·학습은 모두 0이다.

## 현재 수평 배치

분홍 표식과 값은 실제 기타 바디 중심이다. 하늘색 box는 현재 실제 기타 회전 q를 고정하고 기존 사용자 world actor-root 위치 box의 8개 꼭짓점을 바디 중심 좌표로 옮긴 범위다. 노란 box는 Pelvis 기준 팀원 후보다. 초록 선은 실제 넥 방향을 바디 중심에서 표시하며 접촉이나 넥 표면을 나타내지 않는다. 표시선은 저장 raw camera image와 depth 위에 투영한 설명 overlay다.

![현재 수평 배치의 바디 중심 marker와 두 위치 범위, 실제 넥 방향을 표시한 정면 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/current_control/front.png)

![현재 수평 배치의 동일 body-center 범위를 측면에서 본 native frame](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/current_control/side.png)

## 현재 수평 q에서 두 위치 범위

아래 두 box는 현재 수평 배치의 동일 world/Pelvis 기준 body-center 좌표로 표현해 비교한다. 사용자의 기존 actor-root box를 이 q에서 변환한 각 축 폭과 팀원 RFU 후보 폭을 함께 적었다.

| 기준 | 오른쪽 (cm) | 앞 (cm) | 위 (cm) | 폭 (cm) |
|---|---:|---:|---:|---:|
| 사용자 범위, 현재 수평 q | −10.000…25.000 | 0.830…30.830 | 5.800…29.174 | 35.000 / 30.000 / 23.373839855 |
| 팀원 Pelvis RFU 후보 | 17…23 | 24.5…34.5 | 8…10 | 6 / 10 / 2 |

두 box는 같은 좌표에서 위치 비교가 가능하지만 어느 한쪽이 다른 쪽을 포함하지는 않는다. 이 비교는 위치 box의 단순 containment나 공통 6축 허용영역을 뜻하지 않는다.

## 세 저장 자세의 실제 중심과 q별 사용자 범위

각 행의 사용자 범위는 해당 저장 자세의 q로 actor-root box를 body-center 좌표에 변환한 결과다. 실제 중심은 같은 q와 저장 Pelvis 자세로 RFU를 계산했다. 열의 RFU 순서는 오른쪽/앞/위이고 단위는 cm다. 팀원 보고 후보는 각 행마다 동일한 `(17…23, 24.5…34.5, 8…10)` cm다.

| case | 실제 넥 고도 | 실제 중심 RFU | q별 사용자 최소 RFU | q별 사용자 최대 RFU | 사용자 범위 폭 RFU |
|---|---:|---:|---:|---:|---:|
| 현재 수평 배치 (`current_control`) | 0° | (16.958, 24.501, 10.897) | (−10.000, 0.830, 5.800) | (25.000, 30.830, 29.174) | (35.000, 30.000, 23.373839855) |
| 팀원 보고 기준 재구성 (`reported_reference`) | 22° | (17.000, 24.500, 8.000) | (−12.913, 0.830, −9.184) | (22.087, 30.830, 14.190) | (35.000, 30.000, 23.373839855) |
| 팀원 중앙 후보 재구성 (`reported_center`) | 19.5° | (20.000, 29.500, 9.000) | (−12.169, 0.863, −7.197) | (22.831, 30.863, 16.177) | (35.000, 30.000, 23.373839855) |

ref/center q에서 사용자 box의 Pelvis 상대 위쪽 최솟값이 음수인 것은 변환된 위치 범위의 RFU 좌표다. 이를 지면 관통, 기타/인체 충돌 또는 안전성 판정으로 읽을 수 없다. 사용자 bounds는 기존 actor-root/회전 bounds를 대체하지 않으며, 각 q에서 변환한 box도 해당 자세에 조건부다. 보고 기준 q의 넥 고도는 22°, 중앙 q는 19.5°다. 세 q의 표를 전 q 공통 box나 전체 6축 조합 검증으로 일반화하지 않는다.

### 다른 두 자세의 그림

팀원 보고 기준 재구성: [정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_reference/front.png), [측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_reference/side.png)

팀원 중앙 후보 재구성: [정면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_center/front.png), [측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/analysis/reported_center/side.png)

## 좌표 변환과 범위

world quaternion은 `xyzw` 순서다. 표시용 중심 변환은 `p_center = p_root + R(q)c`, 역변환은 `p_root = p_center − R(q)c`이고 `c=[0,−0.4,−0.0217] m`다. Pelvis RFU는 local right=−X, forward=−Y, up=+Z를 사용한다. 이 helper는 표시·좌표계 변환용이며 기존 runner에 연결하거나 제어를 교체하지 않았다.

기존 사용자 actor-root world bounds는 `X=[−0.50,−0.15] m`, `Y=[−0.15,0.15] m`, `Z=[0.65 m, 현재 Chest 높이]` 그대로 두고 각 자세의 q를 고정해 body-center box를 만든다. 따라서 box 폭은 세 q에서 유지되지만 Pelvis에 대한 min/max 위치는 달라진다. 팀원 RFU 후보는 현재 Pelvis 기준으로 별도 변환되어 함께 그려진다. 기존 회전 bounds 역시 유지된다. summary 검사는 identity와 z=90° 해석, 256개 무작위 quaternion의 변환 왕복 및 `q`/`−q` 부호 동치, native 저장 중심·box 꼭짓점 정합, 입력 SHA 불변을 통과했다. 이는 수치 좌표 검사이지 물리나 접촉 검사가 아니다.

이 단계는 세 개 native 장면의 재초기화 없이 저장 frame을 처리했고, 추가 물리/학습을 수행하지 않았다. 이전 `envelope_native_comparison_v1`에서 보호된 파일 44개를 유지했으며 이번 입력 SHA 검사 대상 30개가 보존됐다. 기존 `prior_inventory_note.json`에는 선행 phase의 review가 inventory 작성 뒤 갱신되어 생긴 기존 불일치가 기록되어 있다. 해당 이전 파일은 변경하지 않았다.

수치 원자료와 변경 위치는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/FILE_INDEX.md:1)에 정리했다. [review 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/review.md:1)과 [root 최종 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/final_verification.json:1)을 참조한다. 최종 SHA inventory 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_view_v1/artifact_inventory.json`.
