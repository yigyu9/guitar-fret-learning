# Thorax40 조건 팔꿈치 동작 사전 검수

요약 판정: **문제없음 — 제한된 5초 비교 시험의 실행 차단 없음.** Critical 0건, Warning 2건, Suggestion 0건.

config를 정지 Thorax40 조건과 대조했으며 유일한 차이는 `elbow_motion_amplitude_rad` 0→0.08726646259971647이다. `EnvironmentContract`의 순수 CPU 검증으로 source3 candidate/reference SHA와 81개 초기 q의 모델 한계를 확인했다. source4/5 거절 후보는 투입되지 않는다.

R_Elbow_y(index55)의 초기 q는 2.027669429779rad이고 ±5° 요청 범위는 [1.940402967179, 2.114935892379]rad이다. native 한계 [−0.174532935023, 2.792526960373]rad 안에 있으며, 파형 끝값 기준 하한/상한 여유는 각각 2.114935902203/0.677591067994rad이다.

[parent 제어식](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_effort_v1.py:103)은 매 물리 명령마다 `steps/240`으로 2.5≤t<4.5에서 `A*sin(pi*(t−2.5))`와 목표속도 `A*pi*cos(pi*(t−2.5))`를 오른 posture에 반영한다. 2초 한 주기의 native scalar 명령이다. [two-block 합성](/home/ajou/yigyu/3/stability_adapter_2/right_block_effort_v6.py:57)은 이전 상완점 task를 감산하고 proximal task를 더하며, elbow/wrist child Jacobian 0을 검사한다. [body9 합성](/home/ajou/yigyu/3/stability_adapter_2/right_block_body_effort_v5.py:92)은 body9 성분만 교체하므로 elbow posture 요청은 유지된다. 왼팔 합성도 왼12만 변경한다. [runner의 일정한 논리 목표](/home/ajou/yigyu/3/stability_adapter_2/run_right_block_cradle_v9.py:88)는 EFFORT 오른팔의 물리 직전 posture 파형을 덮어쓰지 않는다. 단일 최종81 effort, 33 EFFORT/48 POSITION 및 기존 가드의 변경은 없다.

## Warning

- [계획:14](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_BLOCK_CRADLE_ELBOW_PLAN_V1.md:14): 기존 정지 조건의 Thorax 후기 접촉 소실이 있으므로 이 시험은 두 블록 지지 성공을 전제로 하지 않는다. 전체/후기 접촉·정지와 같은 시간 기타 차이·몸통 실제각을 별도로 제시하고, 직접 child Jacobian 0을 관성 영향 부재나 안정성 인증으로 확대하지 않는다.
- [parent:104](/home/ajou/yigyu/3/stability_adapter_2/dual_shoulder_effort_v1.py:104): ±5°는 목표각이며 실제 관절 왕복량·world 축 동작이 아니다. 구간 경계에서 목표 위치는 연속이지만 목표속도는 0과 ±Aπ 사이에서 전환된다. 실제 추종·속도 가드·토크 clipping을 기록하고 연주/반복 강건성으로 확대하지 않는다.

## 검수 SHA-256

| 파일 | SHA-256 |
|---|---|
| RIGHT_BLOCK_CRADLE_ELBOW_PLAN_V1.md | 7db0d5c50474755bc9ce915f91eda50b10bc0d44326fde92c4f4a91315d85150 |
| run_right_block_cradle_v9.py | c9111d623b47e8e0f8119ff9cd5349a65ff5360de08bcc0040b13ee223654f10 |
| right_block_body_effort_v5.py | 6e3c9928b11e0bd46d59a7276ecc9158439d24fe22ed1fc3758f2e2649fb7201 |
| right_block_effort_v6.py | 57f36af4f5df535440488097319cf53dbf85c74fd71d82fcb6fb6194e3ec1620 |
| elbow5_Thorax40.json | c90a1b060c8b7f15df50e4fdb5b1affd8da623e262769489a41ca33fa754900e |

검수 범위는 설정·모델 한계 산술·기존 제어 전달 경로다. 새 native 실행이나 과거 원자료 전체 감사는 하지 않았으며 다른 소스·기존 결과·기존 리뷰는 수정하지 않았다.
