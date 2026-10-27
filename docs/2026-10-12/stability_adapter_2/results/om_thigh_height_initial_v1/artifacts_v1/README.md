# OM 기타 초기 thigh-gap 비교

세 실제 Isaac Gym native 평가의 전신·손 영상과 캡처를 정리했다. 조건은 이전 높은 기준, 양쪽 hip capsule 중 최소 source gap 8 mm, 최소 source gap 3 mm다. 각 낮은 조건은 5초 실행이며 초기 자세부터 내려간 뒤 평가한 결과다.

## 실제 native 캡처

![동일 whole-body camera의 전신 0·2·5초 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/whole_body_0_2_5s_comparison.png)

![세 조건의 초기 여섯 현 표시](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/initial_strings_3conditions.png)

![이전 높은 초기 측면과 8 mm·3 mm 초기 측면](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/initial_side_comparison.png)

전신 패널은 세 조건과 0·2·5초의 실제 `whole_body` capture frame을 배치했다. 해당 시점 모두 세 capture의 whole-body view/projection matrix가 일치한다. 측면 비교는 기준의 기존 ON-side 이미지와 낮은 두 조건의 `initial_thigh_side.png`를 사용한다. 측면 camera는 기타를 따라가므로 화면에서 보이는 픽셀 높이 변화는 world z 하강량을 뜻하지 않는다.

## 단위와 결과

[Verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/verification_v1.json)과 [source search 수치](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/search_v2/search.json)에 따라 기록했다.

| 조건 | source gap 정의 및 좌/우 Hip | 선택 위치의 world z 변화 | 0→5초 actor-root 위치 변화 | 0→5초 회전 변화 | 최대 회전 변화 |
|---|---|---:|---:|---:|---:|
| 이전 높은 기준 | 이전 `R_Hip` source gap 101.803 mm; 낮은 조건의 min-gap 기준과는 별도 | — | 114.259337 mm | 6.512226° | 9.751527° |
| thigh gap 8 mm | min(L_Hip, R_Hip) target 8 mm; 실제 source 거리 L 8.000 mm / R 17.138540 mm | -100.558260 mm | 41.009180 mm | 10.177273° | 10.177737° |
| thigh gap 3 mm | min(L_Hip, R_Hip) target 3 mm; 실제 source 거리 L 3.000 mm / R 11.666880 mm | -107.109548 mm | 29.992751 mm | 7.201794° | 7.333630° |

`8 mm`와 `3 mm`는 좌·우 Hip capsule 중 더 작은 source analytic distance이며 수직 높이나 오른쪽 Hip 단독 gap이 아니다. 이전 높은 기준의 101.803 mm는 기록된 오른쪽 Hip source 거리다. Source 간격은 PhysX cooked 형상의 인증된 clearance가 아니다. 낮은 두 조건에서 전경 목표는 동일했고, 기타 world z는 기준 자세보다 각각 약 100.558 mm와 107.110 mm 낮다.

낮은 두 조건 모두 2→5초는 거의 정지한 수치지만, 그 전에 초기 이동과 회전이 있었다. 8 mm 조건은 2→5초 위치 변화 0.000128 mm·회전 변화 0.0000336°였고, 3 mm 조건은 0.008658 mm·0.0033725°였다. 전체 초기→종료에서는 8 mm 조건이 actor-root 41.009180 mm 이동·최대 10.177737° 회전, 3 mm 조건이 29.992751 mm 이동·최대 7.333630° 회전했다. 따라서 초기 pose 유지나 지속적인 상체 지지·연주 성공으로 판정하지 않는다. 3 mm는 다음 높이 진단 후보로 제안할 수 있는 수준이지 성공 조건이 아니다.

각 낮은 조건의 300 contact-query 표본에서 R_Hip raw lambda는 294회 positive였고, L_Hip는 8 mm에서 289회, 3 mm에서 292회 positive였다. Chest와 R_Shoulder는 두 조건 모두 0/300이었다. 이는 300개 표본의 결과이며 지속적인 contact certification이 아니다. raw lambda는 N 단위 force가 아니다. 낮은 조건에서 LH palm 양의 lambda는 0/300이나 thumb·middle finger의 일부 contact 표본은 기타 비바디 부위에서 기록됐다. 이를 palm grip 또는 연주 판정으로 바꾸지 않는다.

두 낮은 native 실행은 기존 PD, 질량 및 strap 동작 조건에서 평가됐다. Strap route는 켜져 있고 rest length는 1.10184697 m다. 기록된 commanded tension 0 N은 직전 step 계산/명령값이며 측정 힘이 아니다. 기타는 물리적으로 고정하거나 강제 부착하지 않았다.

## 원본 영상과 provenance

| 조건 | 전신 영상 | 손 영상 |
|---|---|---|
| 이전 높은 기준 | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/previous_high_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/previous_high_hands.mp4) |
| thigh gap 8 mm | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/thigh_gap8mm_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/thigh_gap8mm_hands.mp4) |
| thigh gap 3 mm | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/thigh_gap3mm_whole_body.mp4) | [MP4](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/thigh_gap3mm_hands.mp4) |

여섯 MP4는 원본 bytes 그대로 복사했다. 파일별 SHA-256, 크기, 재생 정보는 [manifest](/home/ajou/yigyu/3/docs/2026-10-12/video/om_thigh_height_initial_v1/manifest_v1.json)에서 확인한다. 재생성 producer와 입력·출력 provenance는 [make_archive_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/make_archive_v1.py), [provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/provenance_v1.json), [docs_provenance_v1.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_thigh_height_initial_v1/artifacts_v1/docs_provenance_v1.json)에 있다. 여섯 현 선은 화면 overlay이며 물리 현의 굵기·진동은 아니다.
