# 그래픽 격리 CP242 후속 확인

> 정정본: 기존 README는 보존하며, 렌더 API 조회 횟수·probe 순서·기타 바디 중심 표현과 장기 재개 시간 표현만 명확히 했습니다. 데이터와 판정은 바꾸지 않았습니다.

이 문서는 CP241 완료 체크포인트를 채택한 뒤 CP242에서 실제 CUDA 갱신 한 번(256 transition)을 수행한 단일 후속 비교를 기록합니다. 모델/Adam/RMS/RNG/카운터 채택은 정확히 확인됐고, 실제 policy KL은 0.01990470476448536으로 0.02 이하였으며 RMS는 고정됐습니다. 학습 중 graphics는 −1이었고 렌더 API 조회는 0회였으며, 평가는 graphics 0으로 분리했습니다.

두 결정론 평가 모두 16.3667초 전체 구간(3,928 physics step, 982 control step, 492 frame, 전신·손 영상 각 1개)을 완료했습니다. 두 평가 모두 음악 성공은 0/42였고 safety violation과 accepted crossing은 없었습니다. 이 한 쌍의 평가는 성능 개선이나 학습 성공 판정이 아닙니다.

## 관측값

| 평가 | 상자 밖 시간 비율 | 최대 위치 이탈 | 평균 위치 이탈 | 초기 기타 orientation 대비 최대 SO(3) |
|---|---:|---:|---:|---:|
| CP241 초기 | 47.04684% | 43.11752 cm | 8.63902 cm | 90.20247° |
| CP242 1회 갱신 | 46.63951% | 47.11197 cm | 9.44758 cm | 95.66406° |

CP242의 상자 밖 비율은 약간 낮았지만 최대·평균 위치 이탈과 회전 최대값은 더 컸습니다. 따라서 단일 측정에서 일관된 개선을 확인하지 못했습니다. 상자 밖 값은 actor-root world 위치의 box 진단이며, 기타 바디 중심의 자연스러움 척도는 아닙니다. 회전값은 초기 quaternion 대비 SO(3) 거리이며 scalar 관절각이 아닙니다.

## 실제 Isaac Gym 캡처

아래는 CP241과 CP242의 실제 캡처에서 0초, 2초, 마지막 16.3667초의 전신 및 손 프레임입니다. 주황색 선은 원래 strap route 표시입니다.

![CP241과 CP242의 전신 및 손 native 캡처 프레임 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v2/cp241_cp242_native_frames_v2.png)

## 보관 영상

10개 완료 영상은 원본 SHA-256을 확인하여 별도 V4 보관본으로 복사했습니다. 출처별 중복도 그대로 포함되어 있어 파일 수가 서로 다른 실험 수를 뜻하지 않습니다.

![CP241 초기 평가 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/graphics_initial_cp241_whole_body.mp4)

![CP241 초기 평가 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/graphics_initial_cp241_hands.mp4)

![CP242 갱신 평가 전신 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/graphics_update_cp242_whole_body.mp4)

![CP242 갱신 평가 손 native 영상](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/graphics_update_cp242_hands.mp4)

[V4 영상 전체 색인](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/README.md)

## 진단 probe와 진행 한계

첫 reset probe는 60회 reset을 통과했지만, audit 진단 JSON을 learning source ABI에 추가한 뒤 physics rollout/PPO 전에 거부됐습니다. probe v2에서는 별도로 60회 reset을 다시 통과하고 전체 trajectory가 정확히 일치했습니다. 원본은 보존했고 v2에서는 학습 ABI와 audit 입력을 분리했습니다. 이 probe는 CP242 평가와 다른 절차입니다.

별도 장기 재개 결과는 이 문서 범위에 포함하지 않습니다. 재개 성공이나 그 결과의 성능을 여기서 주장하지 않습니다.

## 근거 파일

- [검증 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/verification_v1.json)
- [세 평가 요약 및 입력 무변경 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/progress_analysis_v1.json)
- [10개 영상 보관 매니페스트](/home/ajou/yigyu/3/docs/2026-10-12/video/archive_v4/manifest.json)
- [산출물 provenance](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/graphics_isolation_v1/artifacts_v2/provenance_v2.json)

