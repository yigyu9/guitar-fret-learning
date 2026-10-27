# 현실 비율 기타 구현 최종 독립 검수

요약 판정: **승인·문제없음 — 별도 자산 구현과 완료된 두5초 native 진단 범위.** 미결 Critical은 없습니다. 실물 기타의 물성·음악 성능·왼손 없는 유지 성공은 인증하지 않습니다.

## 원자료·구현 확인

- [v2 사전 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/review_preflight_v2.md:1)의 construction property guard·전체 mass/COM/I readback·캐시 보완이 실제 두 native 실행에서 통과했습니다. 원본/새 모델의 per-body 질량과 총질량4.64871572775kg이 같고, 새 관성은 importer 관성×질량비와 일치합니다. 초기 setter0/1회·거절0 및 route 양 끝 COM/관측 COM/총질량 캐시 검사를 확인했습니다.
- [권위 검증25개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/verification_v3.json:1)와 [native 좌표/관성 검증4개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/native_geometry_ABI_verification_v1.json:1)의 입력 SHA·source/asset 핀·두 native closure를 대조했습니다. 기존 body 이름/순서 및 모든 기타 상대 frame은 명시된 수치 허용오차 내에서 유지됐습니다. 몸통·머리·손가락 초기 목표와 PD는 같고, 양팔 초기 목표와 기타 위치는 새 배치에 맞게 바뀌었습니다.
- 새 바디는 길이48.7896cm·폭37.3039cm·깊이8.8351–10.7985cm·전체100.2298cm입니다. [Yamaha 공식 사양](https://shop.sg.yamaha.com/fs800.html)의 치수를 기존 현 marker 길이에 대응시킨 source 비율 근사이며 제품 스캔이 아닙니다. 휴머노이드1.7205m는 중립 source 형상 높이입니다. 두 convex bout/연장부 mesh, 기존 frame·음악 geom 보존을 CPU와 XML로 대조했습니다. 공용 자산·학습 기본환경 자동 교체는 없습니다.
- 두 시험은 초기 q_ref 고정 PD로 각각1200물리 step/300제어·물리5초를 완료했습니다. 단일81 목표 제출·초기화 state-write guard·원본 strap ON 법칙을 유지했고 체크포인트·Actor·음악·학습·preload·실시간 IK는 실행하지 않았습니다.

## 움직임·중심 정의

위치/quaternion 원자료로 초기/후기 이동·SO(3)와 실제 바디 envelope 중심 이동을 직접 재계산해 검증 JSON과 일치했습니다.

| 진단 | 원본 | 새 모델 |
|---|---:|---:|
| 초기→5초 actor-root 이동(mm) | 108.433775 | 131.919901 |
| 초기→5초 SO(3)(°) | 18.973592 | 10.013111 |
| 초기→5초 바디 envelope 중심 이동(mm) | 41.076657 | 102.077190 |
| 2→5초 actor-root 이동(mm) | 0.047841 | 0.017267 |
| 2→5초 SO(3)(°) | 0.008496 | 0.003439 |

새 모델의 회전 감소와 이동 증가는 함께 보고해야 합니다. 초기 유지 실패 뒤의 작은 후기 변화이며 안정화 성공이 아닙니다. **왼손 지지 조건**으로 새 모델에서도 왼손 손가락·오른허벅지 접촉이 남고 오른상완/전완/Chest는0/300query입니다. 겨드랑이 지지나 왼손 없는 유지 시험이 아닙니다. 원질량 유지,초기 기타 위치·양팔 각도·버튼/strap route 동시 변경 때문에 형상만의 인과효과를 분리할 수 없습니다.

[중심 audit](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/body_center_audit_v2.json:1)의 실제 OBJ bounds를 직접 재계산해 true envelope 중심G[0,−0.4,−0.05569252]m를 확인했습니다. 소비 manifest의 평균깊이 reference[0,−0.4,−0.05078411]m,legacy body 원점,native G:body COM 및 전체 기타 합성 COM은 서로 다릅니다. 실패한 준비 audit/analyzer와 원 manifest를 보존하고 권위 분석v3로 설명한 방식은 적절합니다.

## 그림·문서·보존

[정정 그림v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/artifacts_v2/README.md:1)의 두 PNG를 실제로 열어 old/new×raw 시각/collision의 네 native 패널과 동일12px/cm 윤곽 축척·표제·단위를 대조했습니다. 그림은 실제 제품 정밀 형상 인증이 아닙니다. v2 provenance10입력/3출력/producer SHA와 보존한 v1 후처리 입력/출력/producer SHA가 일치했습니다. 원본/보관 영상4개의 SHA도 일치했고151프레임/30fps/MP4 5.033333초와 물리5초를 구분했습니다.

[변경 색인v2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/CHANGED_FILES_V2.md:1)의 절대 링크·실제 줄과 main4의 완료/그림 정정 append prefix·SHA를 확인했습니다. [봉인 코드](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/seal_phase_v1.py:35)는 읽기 전용으로 검토했고 중요한 감사 범위 누락은 없습니다. 이전2589개 전체 보존·전체1208프레임·4단계 append chain·최종inventory/verification 실행은 root 후속 봉인 범위입니다.

## Warning

소비 manifest의 중심 필드 이름과 companion 설명의 옛 verification_v2 문자열은 보존된 한계입니다. [결과 설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/realistic_guitar_proportions_v1/README.md:1)대로 body_center_audit_v2/verification_v3를 권위값으로 사용해야 합니다. 원질량4.6487kg 통제와 새 COM/I는 중공 목재 악기의 실제 질량 분포 인증이 아닙니다. 접촉은60Hz query/raw λ이며 전체240Hz substep이나 뉴턴 지지력 인증이 아닙니다. 기존 체크포인트의 음악·기하 이전 성능은 미검증입니다.

검증v3 SHA256: `567bf0701ab74f88d60ba05fbf538a7e749a12412a4a1b40516ba43b548206ad`. 검수자는 이 새 리뷰만 작성했고 추가 native·물리·정책·학습과 기존 파일 수정은 하지 않았습니다.
