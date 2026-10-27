# 기타 비율 변경 native 비교

## 범위와 재생자료

원본 기타와 새 비율 기타의 완료된 5초 native 장면을 비교합니다. 두 결과는 각각 1,200 physics step, 300 control step, 151개 프레임(30 fps)입니다. 영상은 재인코딩 없이 원본 MP4 바이트를 그대로 복사했으며, 네 파일 모두 원본·보관본 SHA-256이 일치하고 ffprobe에서 1280×720, 30 fps, 151 frames, 5.033333초로 확인됐습니다. 물리 구간은 5.0초입니다.

| 구분 | 전신 영상 | 손 영상 |
|---|---|---|
| 기존 기타 | [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/old_whole_body.mp4) | [손 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/old_hands.mp4) |
| 현실 비율 기타 | [전신 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/new_whole_body.mp4) | [손 MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/new_hands.mp4) |

영상에서 old는 기존 파란 몸체, new는 새 갈색 몸체입니다. 아래 그림은 native Isaac Gym에서 직접 캡처한 각 조건의 초기·2초·5초 프레임입니다.

![원본과 현실 비율 기타의 native 전신 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/native_whole_body_panel.png)

![원본과 현실 비율 기타의 native 손 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/native_hands_panel.png)

![초기 native 시각화와 충돌 메쉬 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/native_visual_collision_t0.png)

## 형상과 기준

새 몸체는 사람 중립 소스 형상 높이 172.05 cm를 기준으로 기존 현 마커 평균 스케일 비율 0.981682로 치수를 조정했습니다. 172.05 cm는 입력 중립 모델의 형상 높이이며 실제 사람의 측정 키가 아닙니다. 비교 기준 Yamaha FS800 공개 치수는 497×380 mm, 두께 90–110 mm, 전체 길이 1,021 mm입니다. 생성 윤곽은 제품 스캔이나 정밀 복제가 아니라 두 볼록 몸체와 waist를 갖는 근사 형상입니다.

- 기존 몸체 경계: 길이 34.00 cm, 폭 30.00 cm, 두께 4.00 cm.
- 새 몸체: 길이 48.7896 cm, 최대 폭 37.3039 cm, 두께 8.8351–10.7985 cm; 전체 길이 100.2298 cm.
- 기존 목·프렛·현과 body frame/name/order는 보존했습니다. 상·하 convex mesh와 연장된 headstock를 사용했고 render와 collision은 같은 형상입니다.
- 모든 기타 body 질량과 총 native mass(4.6487157 kg)는 기존값을 유지했습니다. 새 imported COM/inertia를 해당 질량에 맞춰 초기 설정하고 runtime guard와 cache를 확인했습니다. 이는 속이 빈 목재 악기의 실제 질량·COM을 인증하지 않습니다.
- 기존 strap의 L0/k/c/cap은 유지했지만 새 몸체에 맞춰 strap anchor와 route를 바꿨습니다. 기타 앞쪽 3.5 cm·위쪽 8 cm의 시작 배치와 팔 24개 IK 목표도 적용했습니다.

![몸체 길이와 폭 치수 비교 도식](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/dimensions_comparison.png)

![몸체 평면 윤곽 비교 도식](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/outline_comparison.png)

![몸체 두께 범위 비교 도식](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/thickness_comparison.png)

세 치수 그림은 확인된 build 수치를 그린 설계 도식입니다. 새 윤곽은 build의 `half_width_profile_t_m`을 표시하며 원본은 기존 34×30 cm bounds를 표시합니다. 실제 기하의 정밀 스캔 렌더로 해석하면 안 됩니다.

## 관측값과 해석 한계

| 요약 지표 | 기존 기타 | 현실 비율 기타 |
|---|---:|---:|
| actor-root 초기 대비 최종 위치 변화 | 108.434 mm | 131.920 mm |
| actor-root 초기 대비 최종 SO(3) 회전 변화 | 18.974° | 10.013° |
| 실제 몸체 envelope 중심 초기 대비 이동 | 41.077 mm | 102.077 mm |
| 끝부분 2–5초 actor-root 순이동 | — | 0.017267 mm |
| 끝부분 2–5초 actor-root 순회전 | — | 0.003439° |
| LH 손가락 / R_Hip 접촉 query | 여러 접촉(300회 중) | LH 여러 손가락 최대 298/300, R_Hip 290/300 |
| R_Shoulder / R_Elbow / Chest 접촉 query | R_Shoulder 284/300, R_Elbow 15/300 | 보고된 접촉 없음 |

여기서 envelope 중심 이동은 `body_center_audit_v2.json`의 **실제 bounding-envelope 중심** `[0, −0.4, −0.05569252] m`를 사용한 값입니다. frozen manifest의 `body_envelope_center_G_m`은 평균 깊이에 놓인 중간 길이 참조점 `[0, −0.4, −0.05078411] m`으로 실제 envelope 중심이 아닙니다. native G:body COM `[약 0, −0.41630393, −0.05111216] m` 및 legacy origin `[0, −0.4, −0.0217] m`와도 서로 다른 기준점입니다. verification_v3의 center companion 검사는 통과했습니다. audit 문서에 상속된 “verification_v2” 표현은 현재 권위 검증 파일인 `verification_v3.json`을 뜻하는 것으로 정정해 읽습니다.

두 실험은 각각 자기 초기상태 대비 움직임을 기록했습니다. 몸체 형상 외에 시작 배치와 strap anchor/route도 달라졌으므로 차이를 형상 하나의 인과 효과로 볼 수 없습니다. 기타 자세의 안정화나 연주 성공을 판정한 실험도 아닙니다. 왼손 손가락과 오른쪽 엉덩이 접촉은 관측됐지만 R_Shoulder/R_Elbow/Chest 접촉은 새 장면에서 관측되지 않아 겨드랑이 지지 성공으로 해석하지 않습니다. 접촉은 60 Hz의 300 query이며 240 Hz 모든 하위 물리 step의 비접촉/접촉 인증이 아닙니다. raw contact lambda는 뉴턴 단위 힘이 아닙니다.

두 장면 모두 고정 q_ref PD 조건이며 policy/checkpoint/music actor는 0, 초기화 뒤 관절·강체 상태 재기록은 없습니다. 안정화 학습이나 음악 생성의 결과로 읽으면 안 됩니다. 이전 v1 OBJ 반올림 검증의 1.73e−9 차이가 엄격한 1e−9 기준을 넘어 거절됐고, 이전 analyzer 입력 누락 실패도 보존돼 있습니다. 현재 v2 audit의 완화된 1e−7 기준 및 verification_v3 분석으로 확인했으며, 이 문서화를 위해 물리 실험을 다시 실행하지 않았습니다.

원자료의 전체 SHA-256 입력/출력 기록은 [provenance.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/provenance.json)에 있고, 네 영상의 source/destination hash와 ffprobe 요약은 [video manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/realistic_guitar_proportions_v1/manifest.json)에 있습니다. 작업 스크립트는 [make_artifacts_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v1/make_artifacts_v1.py)입니다.
