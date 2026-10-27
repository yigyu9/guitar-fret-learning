# 바디 중심 기준 사용자·팀원 위치 범위 나란히 비교

각 그림의 좌우 패널은 같은 저장 native 수평 배치·기타 pose·카메라·원본 프레임을 사용한다. 왼쪽에는 하늘색 사용자 범위만, 오른쪽에는 노란 팀원 RFU 후보만 표시한다. 두 패널의 분홍 점은 동일한 실제 기타 바디 중심이다. 바디 중심은 `c=[0, −0.4, −0.0217] m`로 정의한 표시용 기준점이며 실제 질량중심(CoM)이 아니다.

## 정면 비교

![같은 native 수평 기타와 정면 카메라에서 사용자 위치 범위(왼쪽)와 팀원 후보(오른쪽)를 바디 중심 기준으로 나란히 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/analysis/front.png)

왼쪽 하늘색 범위의 Pelvis RFU는 오른쪽 `−10…25 cm`, 앞 `0.830…30.830 cm`, 위 `5.800…29.174 cm`다. 폭은 각각 `35`, `30`, `23.373839855 cm`다. 오른쪽 노란 팀원 후보는 오른쪽 `17…23 cm`, 앞 `24.5…34.5 cm`, 위 `8…10 cm`이며 폭은 `6`, `10`, `2 cm`다. 양쪽 분홍 점은 같은 중심 `(16.95845, 24.50124, 10.89730) cm`를 나타낸다.

## 측면 비교

![같은 native 수평 기타와 측면 카메라에서 사용자 위치 범위(왼쪽)와 팀원 후보(오른쪽)를 바디 중심 기준으로 나란히 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/analysis/side.png)

측면은 box와 기타를 같은 확대율로 보기 위해 동일한 ROI를 양쪽에 적용했다. 그 crop 때문에 두 패널 모두 사람 머리 위쪽 일부가 화면 밖으로 잘린다. 측면의 표시 목적은 각 범위의 투영 크기와 상대 위치 비교이며, 전신 전체를 담는 장면이 아니다.

## 해석 범위

두 범위는 현재 수평 기타의 동일 q에서 Pelvis 기준 바디 중심 좌표로 비교한다. 왼쪽 사용자 box는 기존 actor-root 위치 범위를 현재 기타 회전으로 고정 변환한 조건부 범위이고, 오른쪽 팀원 box는 보고된 Pelvis RFU 후보다. 두 범위는 같은 좌표에서 비교 가능하지만 단순 포함 관계는 아니다. 왼쪽 범위는 이 회전에서만 유효하며 전체 회전에 공통인 box, 6축 조합의 허용영역 또는 안전 부피가 아니다. 기존 actor-root 및 회전 bounds와 제어는 바꾸지 않았다.

이번 산출은 이전 native t=0 raw frame과 depth/camera 자료의 저장 후처리다. 새 native 초기화·물리 step·학습은 0이다. 패널의 box는 설명용 선이고 접촉 형상이나 접촉 시험 결과가 아니다. 보고에는 입력 SHA 15개와 이전 body-center phase 파일 24개의 보존 확인이 기록되어 있다. 변환식·검사 결과와 원자료 경로는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/FILE_INDEX.md:1)을 참조한다. [review 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/review.md:1)과 [root 보존 검증](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/final_verification.json:1)을 함께 기록한다. 최종 SHA inventory 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body_center_side_by_side_v1/artifact_inventory.json`.
