# 자유 기타 연주 자세·현재 목표 오차 진단

이번 산출물은 `fret_fingers_strap_v1/native_v2/data`에 저장된 실제 Isaac Gym 스트랩 ON 실행을 후처리한 기록이다. 새 물리 실행은 0회, 학습 갱신은 0회다. 원본 실행은 113개 native 표본을 남겼고, source의 `finger_back` 실패로 실제 종료 시각 3.716667초에 끝났다. 압현 성공률은 기존 실행 기록과 같은 0%다. 이 문서는 원본 성능의 성공이나 새 물리 검증을 뜻하지 않는다.

## 관측 요약

| 시각 | 기타 넥 고도 | 앞판 대 몸통 전방 각도 | 앞판 법선 world Z | 위치 box | 활성 목표 marker 오차 |
|---|---:|---:|---:|---|---|
| 초기 0초 | 0° | 0° | 0 | 내부 | 정책 목표 미저장 |
| 2초 | −5.4722° | 3.6829° | −0.05424 | 내부 | ring 86.2840 mm |
| 3초 | −5.7972° | 5.7793° | −0.04519 | 내부 | index 87.4655 mm |
| 실제 종료 3.716667초 | +11.3339° | 51.4889° | +0.62274 | 내부 | index 106.8809 mm, ring 78.7405 mm |

시각별 활성 손가락과 할당 목표가 달라지므로 marker 오차를 같은 음의 연속 추이로 해석할 수 없다. 종료 시 actor-root 위치는 위치 box 안이었지만 기타 앞판은 크게 기울었고 손끝은 할당된 프렛 목표에서 멀었다. 전체 회전 허용 집합 포함 여부는 평가하지 않았다.

113개 표본 중 69개에서 위치 box를 벗어났으며, 가장 큰 초과는 2.6초의 world Z 방향 9.7475 mm였다. 이는 초기점 복귀 판정이 아니며 이 분석에서 즉시 실패 문턱을 추가하지 않았다. 사용자가 허용한 넓은 범위는 그대로 둔다.

손끝 marker와 native 손끝 위치의 최대 정합 오차는 7.7970×10⁻⁸ m(0.07797 µm)였고, 요약의 관측 정합 상태 수는 53개다. capture/trace step, 선택 이미지 SHA, 마지막 terminal observation 정합과 전후 입력 SHA 대조는 기록상 통과했다. 의미 검증 6개도 통과했다.

## 측정 정의와 한계

- 넥 고도는 기타 local +Y의 world 수평면 기준 각도다. 앞판 각도는 기타 local +Z와 고정 Pelvis local −Y 전방 사이의 각도이며, 법선 world Z도 별도로 기록했다.
- 몸통 상대 배치는 기타 actor-root에서 현재 Chest 원점을 뺀 값을 고정 Pelvis 기준축(right=local −X, forward=local −Y, up=local +Z)으로 나타낸 m 단위 값이다. 바디 중심 간 거리, 신체 표면 간격 또는 접촉 보증이 아니다.
- 팔 한계 여유는 양쪽 Thorax·Shoulder·Elbow·Wrist 12관절 각각에 대해 native와 source 한계를 구분해 계산했다. 이번 선택 표본에서는 양쪽 결과가 같았다. 전체 최소는 R_Thorax_x의 +0.0000544861 rad, 0.23333초였다. 한계 여유와 비율은 모델 한계에 대한 지표이며 인간 생리학적 자연스러움·도달성·충돌을 보증하지 않는다. root는 이 관절의 제어 목표를 바꾸지 않았다.
- 손끝 목표는 저장된 420D ABI에서 관측된 손끝 위치와 활성 목표 marker 사이의 거리다. 함께 저장된 `signed_press_depth_mm`도 정책 관측의 목표 field이지 실제 접촉력·접촉 상태·기하 관통 측정이 아니며, 이번 결과는 접촉이나 관통을 인증하지 않는다. 2초 이미지는 trace상 PREPARE로 표기되지만, 그 목표 관측은 첫 PLAY의 적분 전 관측과 같은 물리 상태다. source_info 평가는 4 step 뒤에 이루어져 화면 목표 산출에 섞지 않았다. 마지막 화면은 `terminal_observation`을 사용했다.
- 색상 안내는 노랑=넥 local +Y, 청록=앞판 법선 local +Z, 흰색=활성 손끝, 분홍=현재 할당 목표다. 저장 depth가 없으므로 새 참고선은 가림·접촉을 인증하지 않는다. 오렌지 스트랩 경로와 원래 native 이미지의 표시를 유지했다. PLAY 장력 0 N은 기존 실행 기록이며 이번에 힘을 새로 검증한 값이 아니다.
- 추세 그림에는 자연스러움 문턱, 새 경보, 보상 가중치를 설정하지 않았다. 위치 box는 위치 조건이며 회전 집합 검증을 대신하지 않는다.

## 이미지 기록

각 프레임의 전신·손 확대 이미지는 저장된 native Isaac Gym 이미지에 진단 표식을 덧붙인 결과다. 장면별 지표와 표식은 보이기 위한 참고 정보이며, 원본의 물리·접촉 검증 범위를 넓히지 않는다.

### 초기 — frame 000

전신: 기타와 몸통의 초기 상대 배치. 손 확대: 초기 손 위치. 아직 활성 Fret 목표는 표시되지 않는다.

![초기 전신 frame 000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_000_whole_body.png)

![초기 손 확대 frame 000](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_000_hands.png)

### 2초 — frame 060

trace phase 표기는 PREPARE다. 표식의 활성 목표 관측은 첫 PLAY의 적분 전 상태에 맞췄으며, ring marker 오차는 86.2840 mm다.

![2초 전신 frame 060](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_060_whole_body.png)

![2초 손 확대 frame 060](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_060_hands.png)

### 3초 — frame 090

기타 위치는 box 내부다. 넥 고도 −5.7972°, 앞판 대 몸통 전방 각도 5.7793°이며, 활성 index 목표 오차는 87.4655 mm다.

![3초 전신 frame 090](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_090_whole_body.png)

![3초 손 확대 frame 090](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_090_hands.png)

### 실제 종료 — frame 112

3.716667초 `TERMINATED` 표본이다. 위치 box 내부지만 앞판 대 몸통 전방 각도는 51.4889°이고, index/ring 목표 marker 오차는 각각 106.8809/78.7405 mm다.

![실제 종료 전신 frame 112](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_112_whole_body.png)

![실제 종료 손 확대 frame 112](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/frame_112_hands.png)

### 시각별 비교와 113개 표본 추세

아래 비교는 2초와 실제 종료 화면을 나란히 보여준다. 추세 그림의 세로 점선은 2초이며 마지막 표본은 실제 종료다. 목표 오차 선은 활성 손가락·할당 목표가 달라지는 구간을 연결하므로 같은 음에 대한 단조 추세가 아니다.

![2초와 실제 종료 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/comparison.png)

![기타 자세·관절 여유·몸통 상대 배치·활성 목표 오차의 표본 추세](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/analysis/trends.png)

## 다음 검증 단계

승인된 다음 단계는 현재 기타 기준의 제한된 왼팔 9관절 접근 보정과 Fret 21개 목표를 하나의 PD 목표로 합성해 단일 음 압현·유지를 확인하는 것이다. 이는 이번 분석에서 구현되거나 실행된 내용이 아니다. 보정 한계·변화율·목표 소유권과 원본 음악 성능 보존을 별도로 검증해야 한다.

독립 검수 기록 [review.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/review.md:1), 보존 소스 [source_final/](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/source_final/), root 보존 검증 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/final_verification.json:1)을 참조한다. 최종 산출물 SHA 기록 경로: `/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/artifact_inventory.json`.

세부 근거 파일과 실제 코드·계획·검증 참조는 [파일 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playing_posture_diagnostic_v1/FILE_INDEX.md:1)을 참조한다.
