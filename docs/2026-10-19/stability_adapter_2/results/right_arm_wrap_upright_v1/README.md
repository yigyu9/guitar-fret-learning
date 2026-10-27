# 곧은 상체·오른 상완으로 감싸는 초기 자세

가슴을 기대는 방향에서 오른 상완의 팔꿈치 가까운 끝부분으로 기타 위쪽을 감싸는 방향으로 바꿨다. 실제 정지·작은 팔꿈치 운동 모두5초를 완료했다. 기존 안정 초기값·원본 모델·실패 결과는 보존한다.

## 초기 비교와 실제 영상

왼쪽은 이전, 오른쪽은 새 초기 자세다. 실제 Isaac Gym 전신 카메라 행렬이 같다.

![초기 전신 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/initial_whole_comparison_v1.png)

![초기 측면 비교: 기타 상대 카메라 위치가 달라 동일 world 카메라 비교는 아님](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/initial_side_comparison_v1.png)

초기 Torso/Spine/Chest의 전방 local-Z 기울기 proxy는29.529/28.403/53.412°→16.529/11.403/33.412°다. 기타는 몸 쪽25mm·위약1.03mm로 이동했고 넥 방향·회전은 유지했다. 이 proxy는 임상적 척추각이나 scalar 관절각 합이 아니다.

![팔꿈치 운동 전체5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/native_wrap55_elbow_wave_whole_body.mp4)

## 검증 결과와 한계

정지 최대 기타 BB중심34.001mm/SO3 16.503°, 최종26.012mm/11.981°였다. 이전 더숙인 기준의 최대12.882mm/7.543°보다 초기정착 흔들림이 커졌고 2→5초에도7.342mm/3.344° 변했다. 팔꿈치 실제10.102° 왕복의 같은시점 추가변화 최대0.458126mm/0.200994°는 작았다. 최초2.5초의 초기값·trace는 exact다.

두 조건 모두 가슴/몸통/오른Thorax/오른전완·손/머리 접촉0 of1200. 전체R_Shoulder 강체1196/후기120, 오른허벅지 waist1198/후기120, 왼팔손1189/후기120이었다. 상완 raw축projection0~1 부분집합181step과 끝점clamp/fullbody1196step을 구분한다. source 최근접축98.289%로 상완 끝 cap 근처이며 근위30/45% 또는 겨드랑이 두블록 지속지지가 아니다. rawlambda는힘N로 변환하지 않았다.

스트랩OFF·기타자유·root/하체고정·selfcollisionON·81목표(33EFFORT+48POSITION)를 유지했다. 유한human점요청은Thorax10N4mm/상완20N8mm이며 직접 기타힘·부착·state쓰기·checkpoint·학습은 없다. 왼손 없이 유지하거나 연주를 완주한 시험은 아니다.

## 전체 실행 기록

source7batch21후보: 수락4/거절17. native7회:5초완료2/보호중단5,3512physics/878control. 원영상은 중단까지 실제 길이로 보관했다.

| 실행 | 물리 시간(s) | 완료 | 최대 BB중심(mm) | 최대 SO3(°) |
|---|---:|:---:|---:|---:|
| native_relief12_static | 1.766667 | 부분 | 104.880 | 36.886 |
| native_relief20_static | 0.533333 | 부분 | 116.299 | 36.011 |
| native_upper20_static | 0.616667 | 부분 | 108.690 | 32.229 |
| native_upper40_static | 0.966667 | 부분 | 107.458 | 31.494 |
| native_wrap40_static | 0.750000 | 부분 | 100.710 | 33.980 |
| native_wrap55_static | 5.000000 | 5초 | 34.001 | 16.503 |
| native_wrap55_elbow_wave | 5.000000 | 5초 | 34.001 | 16.503 |

## 자료와 다음 확인

- [구현·상세 조건](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_UPRIGHT_COMPLETION_V1.md:1) · [초기81각·기타p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/search_v7/relief20_fraction55/candidate.json:1)
- [이미지 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/artifacts_v1/README_V2.md:1) · [16개 영상 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_upright_v1/INDEX.md:1)
- [명령·시계 감사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/timelines_final_v1.json:1) · [실제 자세·접촉분율](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/posture_final_v1.json:1) · [waist 접촉](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/waist_final_v1.json:1)
- [변경 파일·실제 줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_upright_v1/CHANGED_FILES_v1.md:1)

새 자세를 시각적 검토 기준으로 두고, 다음에는 왼손 접촉 기여 분리와 상완 지지점 미세조정으로 초기 정착 오차를 줄인다. 기존 안정 후보는 학습기본으로 보존한다. 반복 재현성·타현 전체동작·압현/연주 연결은 별도 검증한다.
