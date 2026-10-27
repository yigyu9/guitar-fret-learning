# 오른쪽 두 블록 cradle · 정지 기준과 elbow 주기 진단

이 기록은 실제 native 5초 시험 11개와 guard에서 중단된 1회(총 12 native 시도)를 구분해 보관합니다. 본 산출물 생성에서는 추가 물리 실행·학습을 하지 않았습니다. 분석 수치는 `native_analysis_final_v1.json`을 따릅니다.

## 선택된 close 조건: native 프레임

![선택 elbow5_close 전신 실제 native 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_whole_body_0_3_5_v1.png)

![선택 elbow5_close 손 실제 native 프레임: 0, 3, 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_hands_0_3_5_v1.png)

패널은 원본 Isaac Gym native 캡처를 같은 카메라·같은 시점으로 배치했으며 캡션은 이미지 밖에 뒀습니다. 아래 초기 측면 이미지도 원본 native 캡처를 그대로 복사한 별도 2-block 보기입니다. 추가 카메라 투영, 힘 표시, 접촉 overlay는 넣지 않았습니다.

![elbow5_close 실제 native 초기 support-side 2-block 보기](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/native_elbow5_close_initial_support_side.png)

## 모든 완료 시도의 최종 기록

| native 조건 | 상태 | 최종 기타 BB 중심 변위 (mm) | 최종 기타 전체 SO(3) 변화 (°) |
|---|---|---:|---:|
| `native_static_OFF0` | 완료 5초 | 6.1182752340338995 | 4.419458384396346 |
| `native_static_ON10` | 완료 5초 | 6.554302873170103 | 4.398171602467899 |
| `native_static_body4_ON10` | 완료 5초 | 8.313591199313134 | 2.995145532483108 |
| `native_static_body9_low` | 완료 5초 | 8.305272325244381 | 3.9217585676991757 |
| `native_static_currentG_body4` | 완료 5초 | 8.566303228376361 | 2.814562548494293 |
| `native_static_Thorax20` | 완료 5초 | 6.8338121905966736 | 3.965936471683041 |
| `native_static_Thorax30` | 완료 5초 | 7.46177275081792 | 5.08273116996101 |
| `native_static_Thorax40` | 완료 5초 | 3.6035952603413026 | 3.9330570893445596 |
| `native_static_close` | 완료 5초 | 4.093496441417328 | 3.995343013535303 |
| `native_elbow5_Thorax40` | 완료 5초 | 4.454501703404399 | 4.240770789733003 |
| `native_elbow5_close` | 완료 5초 | 4.102108673620094 | 3.997035619161813 |

별도 abort인 `native_static_body9_effort`는 guard에서 물리 step 5, 즉 0.020833초에 중단됐고 전신·손 영상은 각각 2프레임입니다(재생 0.066667초). 5초 완료 실행이나 분석 최종표에 포함하지 않습니다.

## 정지 기준과 팔꿈치 주기의 trace 비교

![native_static_close와 native_elbow5_close 전체 trace 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/static_vs_elbow5_close_trace_v1.png)

그래프는 두 raw `trace.json`의 모든 저장 표본(각각 301개)을 사용했습니다. 시간은 `physics_step/240`초입니다. 바디 중심은 canonical `body_centre_G_m`을 xyzw quaternion으로 world 회전한 뒤 `position_W_m`에 더하고 초기 위치에서의 이동량을 계산했습니다. SO(3)는 초기와 현재 xyzw quaternion의 상대 각도이며, 팔꿈치는 실제 `R_Elbow_y` scalar `q − q_ref`입니다. 음영은 elbow wave 2.5–4.5초 구간입니다.

선택된 정지 기준 대비 주기 조건은 2.5–4.5초 `R_Elbow_y` 실제 이동 range 10.114130°였습니다. 정지 trace 대비 기타 추가 변화는 최대 중심 0.071023 mm / SO(3) 0.031521°였고, wave 종료 시점의 초기 대비 변화는 중심 4.102109 mm / SO(3) 3.997036°였습니다. 실행 중 최대 중심 변위 5.328657 mm, 최대 SO(3) 변화 4.494762°는 종료값과 구분합니다.

![선택된 elbow5_close 전체 native 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/elbow5_close/whole_body.mp4)

## 접촉과 제어의 범위

선택 조건에서 Thorax와 상완 contact presence는 elbow wave 480/480 step, positive raw lambda는 223/480 step이었습니다. 마지막 120 step에서는 각각 presence 120/120, positive 56/120입니다. 왼쪽 `LH:thumb3`와 오른쪽 허벅지 contact가 계속 남아 있으므로 오른쪽만의 지지로 분리된 결과가 아닙니다. raw lambda는 뉴턴 단위 힘이나 지지력 분담이 아닙니다.

이 조건은 현재 기타 G 기준으로 finite/bounded한 사람 관절 토크 제어를 사용합니다. passive hold로 설명하지 않습니다. source face-wrap 4·5는 실패해 실행하지 않았습니다. 이번 조건은 한 축·한 주기만 확인했으며 반복성, 모든 움직임, 연주 안정성 또는 음악 성공을 인증하지 않습니다. 기타를 고정·부착·직접 가압하거나 자세를 덮어쓰지 않았습니다.

## 원자료와 보관 파일

- [12개 실행 전신·손 영상 목록](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/INDEX_V1.md)
- [24개 원본/사본 hash·ffprobe manifest](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_block_cradle_v1/manifest_v1.json)
- [canonical analysis](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/native_analysis_final_v1.json)
- [승인된 artifact brief](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifact_brief_v1.json)
- [failure audit v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/failure_audit_v2.json)

**보관 산출물:** 위 세 이미지, byte-exact 24개 MP4, 한국어 README/색인, manifest 및 [provenance](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_block_cradle_v1/artifacts_v1/provenance_v1.json).
