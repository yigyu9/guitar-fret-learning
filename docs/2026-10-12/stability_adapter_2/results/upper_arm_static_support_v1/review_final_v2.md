# 연주 없는 초기 자세 유지 시험 최종 독립 검수

요약 판정: **문제없음 — 완료된 네 조건의 5초 고정 PD 진단과 결과 해석 범위.** 미결 Critical은 없습니다. 초기 기타 자세 유지·지속 상완 지지 성공은 달성되지 않았습니다.

## 코드·원자료 대조

- [v2 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/review_preflight_v2.md:1)의 시간 분모 정정과 source 간격 선택을 유지했습니다. 새 batch는 순차 child 실행·timeout·개별 종료 기록을 보존합니다. source7+batch 추가 SHA와 네 native 입력 closure를 현재 파일에 대조해 모두 일치했습니다. 미실행 runner 준비본의 보존 및 초기 기타 p/q·속도 검사 추가도 확인했습니다.
- [실행 검증32개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/verification_v2.json:1)와 [동일 조건 검증8개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/same_conditions_verification_v1.json:1)의 입력 SHA를 대조했습니다. 모두 1200물리 step/300제어/301상태를 마쳤으며 초기 q_ref 고정 PD 목표·기타 초기 상태·PD·원본 strap법칙·finger/head scalar 초기각이 일치합니다. 초기 Chest 전경은0°/0°/3°/5°이며 실제 관절·몸체는 물리에 따라 움직입니다. preload·체크포인트·Actor·음악·학습·노이즈 실행은 없습니다.
- 저장된 기타 위치/quaternion에서 초기→5초 및2→5초 이동·SO(3)를 직접 재계산했고 검증 JSON과 일치했습니다. 접촉 원자료300표본에서 R_Shoulder/R_Elbow/Chest/Torso/Spine의 관측 횟수도 직접 대조했습니다.

| 조건 | 초기→5초 이동(mm) / SO(3)(°) | 2→5초 이동(mm) / SO(3)(°) |
|---|---|---|
| 기준 | 112.759698 / 19.628224 | 1.174610 / 0.228258 |
| 상완 접근·전경0° | 100.493723 / 15.960138 | 0.304823 / 0.124557 |
| 상완 접근·전경3° | 105.906231 / 17.405710 | 0.062397 / 0.016754 |
| 상완 접근·전경5° | 107.830700 / 18.337570 | 0.465878 / 0.167869 |

3°는 후기 움직임이 가장 작지만 초기에서 약10.6cm·17.4° 이탈했습니다. 기준도 후기 움직임이 작으므로 후기 정지를 새 자세의 효과나 초기 자세 유지 성공으로 단정할 수 없습니다. 물리는5초까지 계속 적분했습니다.

R_Elbow 전완 capsule은 기준/0°/3°/5°에서282/289/288/287표본에 접촉했습니다. R_Shoulder 상완 접촉은5°에서만55표본(0.4333–1.3333초)이고 나머지는0, Chest/Torso/Spine은모두0입니다. 이는 전완·허벅지·왼손 접촉을 동반한 후기 상태이며 지속 겨드랑이 지지의 증거가 아닙니다. 접촉 query는60Hz 제어 직전이고 raw λ는 뉴턴 힘·압력으로 환산하지 않았습니다.

## 문서·산출물·보존

- [최종 결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/README.md:3)과 [상세 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/README.md:7)은 초기 이탈·후기 정지·접촉 부위를 구분합니다. 후보0°/3°/5°의 source signed-gap은1.32916649/0.50359291/0.50350287mm이며 cooked 형상의 실제 최단 간격으로 설명하지 않습니다. 위치는 actor-root world 이동거리, 회전은 자체 초기 quaternion 대비 SO(3)입니다.
- 실제 PNG3개를 열어 전신/손0·2·5초 프레임 및 전체/후기 곡선의 범례·단위·표본을 원자료와 대조했습니다. [provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/artifacts_v1/provenance_v1.json:1)의39입력 전후 SHA와9출력 SHA가 일치했습니다. [영상 manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/manifest.json:1)의8개 원본/복사 SHA를 확인했고151프레임/30fps/MP4 5.033333초와 물리5초를 구분했습니다.
- [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/CHANGED_FILES_V2.md:1), [영상 색인V11](/home/ajou/yigyu/3/docs/2026-10-12/video/README_ABSOLUTE_V11.md:17)의 절대 링크·실제 줄 및 main4 완료 append의 원문 prefix/전후 SHA를 확인했습니다. [봉인 구현](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/upper_arm_static_support_v1/seal_phase_v2.py:26)은 읽기 전용으로 검토했고 요청한 감사 범위의 큰 누락은 발견하지 않았습니다. 이전4099파일 전체·전체2416이미지·최종 snapshot/inventory의 실행 결과는 root의 후속 봉인 범위입니다.

## Warning

[영상 설명:8](/home/ajou/yigyu/3/docs/2026-10-12/video/upper_arm_static_support_v1/README.md:8)과 색인의 ‘상완 고정3°/5°’는 조건명 축약입니다. 실제 각도는 초기 Chest 전경 차이이고, 고정하는 것은 PD 목표이며 상완 pose 자체가 아닙니다. root 결과·상세 설명의 정의를 함께 읽어야 하며 향후 색인은 ‘상완 접근·Chest 전경’으로 풀어 쓰는 것을 권장합니다. 이미 소비된 설명·그림은 보존합니다.

검증 JSON SHA256: `313d6f650c4c9b05613ae4a141e6e6b9f05569f20091c0b2888204033e7b93af`. 이 검수는 추가 native/물리/정책/학습을 실행하지 않았으며 검수자 소유의 새 리뷰 파일만 작성했습니다. 다음 지지 위치 변경 제안은 미실행 계획입니다.
