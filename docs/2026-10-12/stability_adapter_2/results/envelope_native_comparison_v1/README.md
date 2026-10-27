# 사용자·팀원 기타 위치 범위의 native 정적 장면 비교

세 조건에서 각각 새 Isaac Gym native `NoPhysicsGym` 환경을 초기화해 t=0 장면을 캡처했다. 환경 3개를 만들고 카메라 렌더 후 설명선을 투영했지만, physics step은 0, 학습 update는 0이다. 동일 humanoid 관절각과 실제 Pelvis·기타 상태를 이전 실행 기록과 exact 대조했고, 각 report에서 9개 검사(관절각·body pose·기타 pose, 두 box 역변환, 렌더 전후 상태, 0 step, 금지된 force/write 없음, 입력 SHA 불변)가 모두 통과했다. strap은 OFF다.

## 현재 수평 장면 — 정면과 측면

파란 선은 사용자 world actor-root 위치 box를 각 장면의 실제 기타 회전으로 고정한 채 기타 바디 중심 좌표로 옮긴 조건부 범위다. 노란 선은 Pelvis 기준 팀원 보고 body-center RFU 후보 box다. 분홍 점은 실제 기타 바디 중심, 회색 점은 actor 원점, 초록 선은 해당 장면의 실제 넥 방향을 나타낸다. 점선은 depth를 기준으로 가려진 구간이다.

![현재 수평 배치의 전체 seated humanoid와 기타, 두 위치 범위 및 실제 중심·넥 방향을 표시한 native 정면 장면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front.png)

![같은 현재 수평 배치를 옆에서 본 native 장면. box 투영과 인체·기타의 깊이 관계를 보조적으로 확인한다.](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side.png)

## 세 조건 정면 비교

| 조건 | 초기 넥 고도 | 실제 회전의 사용자 회전 box 포함 검사 | 정면 그림 |
|---|---:|---|---|
| 현재 수평 배치 | 0° | 안 — 저장된 실제 회전의 quaternion 동치 기준 한 점 검사 | [current_control/front.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front.png) |
| 팀원 보고 기준 재구성 | 22° | 안 — 저장된 실제 회전의 quaternion 동치 기준 한 점 검사 | [reported_reference/front.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front.png) |
| 팀원 중앙 후보 재구성 | 19.5° | 밖 — 비특이 Euler 표현의 두 동치해 모두 box 밖 | [reported_center/front.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front.png) |

현재와 보고 기준은 저장 자세의 사용자 회전 box 안에 witness가 있고 native quaternion 동치 허용오차 `1e−5 rad` 이내여서 안으로 판정했다(보고 기준의 실제 오차 `2.33212e−7 rad`; float32 경계 readback 정밀도). 중앙 후보는 밖이다. 이는 세 저장 자세에 대한 해당 검사 결과만 뜻한다. 전체 회전 집합의 포함 판정이나 안전영역 인증은 구현하지 않았다. 노란 팀원 위치 box와 파란 사용자 위치 box는 모두 같은 world body-center 좌표로 변환했으므로 위치를 비교할 수 있지만, 현재 각 장면에서 두 box가 단순 포함 관계인 것은 아니다. 파란 box는 해당 장면의 기타 회전을 고정한 조건부 위치 변환이므로 모든 회전에서의 6축 범위 포함을 뜻하지 않는다.

### 현재 수평 배치

정면은 위의 큰 그림을 참조한다. [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/front.png), [측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/current_control/side.png)

### 팀원 보고 기준 재구성

정면에서 넥 고도 22°의 실제 native 자세와 두 위치 box를 비교한다. 이는 팀원의 원 장면 재현이 아니다. [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/front.png), [측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_reference/side.png)

### 팀원 중앙 후보 재구성

정면에서 넥 고도 19.5°의 실제 native 자세와 두 위치 box를 비교한다. 저장된 자세는 사용자 회전 box 밖이다. [정면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/front.png), [측면 PNG](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/native/reported_center/side.png)

세 캡처 모두 같은 humanoid DOF와 body pose가 이전 실행의 저장 상태와 일치했다. 장면에서 보고 기준·중앙 후보의 왼손이 넥에서 떨어져 보이지만, 이 정적 캡처는 동적 손 접촉·연주를 시험하지 않는다. 동적 관측은 별도 이전 phase의 범위에 속한다.

## 좌표 가정과 한계

노란 팀원 후보는 현재 Pelvis 기준 오른쪽=local −X, 앞=local −Y, 위=local +Z로 변환한 기타 바디 중심 RFU 범위 `(17–23, 24.5–34.5, 8–10) cm`다. 바디 중심 offset은 기존 가정 `BODY_CENTER_G = [0, −0.4, −0.0217] m`를 사용했다. 팀원 원본의 초기 pose 입력·회전 피벗·정확한 좌표 변환이 없어 보고 범위 재구성이지 원 장면 재현이 아니다. 현재 실제 넥 고도는 0°, 보고 기준 재구성은 22°, 중앙 재구성은 19.5°다.

파란 사용자 위치 box는 world actor-root box `X=[−0.50,−0.15] m`, `Y=[−0.15,0.15] m`, `Z=[0.65 m, 현재 Chest 높이]`를 해당 장면의 기타 회전을 고정해 body-center box로 옮긴 것이다. 노란 팀원 box도 같은 world body-center 좌표에 있으므로 위치 box끼리 비교할 수 있다. 세 장면의 box는 단순 포함 관계가 아니며, 파란 box는 각 장면의 실제 회전에 조건부라 전체 6축 범위 포함 검증이 아니다.

각 조건은 raw native 정면·측면 PNG(1280×720), depth 배열(각 720×1280), view/projection 행렬과 annotated PNG(1280×875)를 보존한다. 선은 camera/depth에 투영한 설명 overlay이며 충돌 형상이나 접촉면이 아니다. Isaac Gym 로그에 `Could not load visual geom` 경고가 있어 실제 자산 형상·재질의 완전한 시각 정확성을 인증하지 않는다. 물리 안정성이나 범위 내 모든 회전 조합을 시험하지 않았고, 이전에 설정한 범위도 변경하지 않았다.

실제 이미지·geometry/report/attempt 자료와 소스 줄 위치는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/FILE_INDEX.md:1)에 정리했다. 관련 검수 기록은 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/review.md:1)에서, root 보존 검증은 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/envelope_native_comparison_v1/final_verification.json:1)에서 확인한다.
