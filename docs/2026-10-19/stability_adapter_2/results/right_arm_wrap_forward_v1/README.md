# 오른 상완 받침을 보존하고 전완·손을 조금 앞으로

현재 곧은 상체·기타 배치를 유지하고 R_Elbow3 초기각만 바꿨다. 오른손 손바닥을 기타 앞판의 수평 전방으로 약1cm 내민 자세를 실제 Isaac Gym 5초로 검증했다. 나머지78 scalar초기각·기타39초기fullstate·R_Thorax/R_Shoulder fullstate·원지지점제어configuration은 기준과exact다.

## 실제 초기 비교와 전체 5초

왼쪽은이전wrap55,오른쪽은새초기배치다. 전신 카메라행렬이같은native원프레임이다.

![초기 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/initial_whole_comparison_v3.png)

![현재 자세 실제 전신5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/native_elbow10_static_whole_body_v3.mp4)

![오른팔 초기 확대: 왼쪽 이전, 오른쪽 새 자세](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/right_arm_initial_comparison_v1.png)

## 측정 결과

- 손바닥전방이동: 초기9.941820mm,같은시각기준5초8.562639mm. 손목초기8.531274mm. 전방축은초기기타front normal의world수평투영으로,+Y에가깝다. 움직이는기타에대한손의상대오차가아니다.
- 팔꿈치원점은기구학적으로유지했고nativefloat32에서59.605nm차이를측정했다. 허용치1µm와실제비영차이를분리하며exact위치로표현하지않는다.
- 기타최대BB중심34.011512mm/SO3 16.513982°(기준34.001197mm/16.502623°). 동시각추가최대1.323156mm/0.555192°다. 초기정착의흔들림은여전히남는다.
- 실제접촉:가슴/몸통/오른Thorax/전완·손/머리0 of1200,full상완1196·waist1198·왼팔손1189,상완/waist/왼손후기각120/120. 축projection0~1부분집합181과전체body1196을구분하며상완끝cap지지다. 왼손없는유지나두블록지속끼움이아니다.

초기Shoulder3탐색은손후퇴로채택하지않았다. Shoulder+Elbow6전방시도는0.633333초/152physics에안전중단됐고원자료와영상을보존했다. Elbow3 방식은5초를완료했다. 이번native2회/1352physics/338control이며추가학습/체크포인트연결은없다.

## 자료·검증 범위

스트랩OFF·기타자유·root/하체고정·selfcollisionON·full81(33EFFORT+48POSITION)과유한human제어10N4mm/20N8mm·기존gain을유지했다. 기타힘/부착/상태덮어쓰기는없다. 새자세는다음검토기준이며학습기본값과원본/이전실험은보존한다.

- [자세 구현·상세 조건](/home/ajou/yigyu/3/stability_adapter_2/RIGHT_ARM_WRAP_FORWARD_COMPLETION_V1.md:1) · [현재81초기각·기타p/q](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/search_v4/forward10mm/candidate.json:1)
- [이미지·설명 보완본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/artifacts_v1/README_V3.md:1) · [6개 영상 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/right_arm_wrap_forward_v1/INDEX_V3.md:1)
- [실제 팔 변위](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/arm_final_v2.json:1) · [유한명령·실제시계](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/timelines_final_v1.json:1) · [동시각 기타 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/guitar_comparison_v1.json:1) · [waist 접촉영역](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/waist_final_v1.json:1)
- [변경 파일·실제 줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/CHANGED_FILES_v1.md:1)

- [그림 후처리 실패 이력의 보존 범위](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/right_arm_wrap_forward_v1/ARTIFACT_HISTORY_LIMITATION_V1.md:1): 첫 실패 producer 한 버전의 사전 스냅샷 누락을 명시했다. 물리 원자료와 정상 완료 산출물의 검증은 구분한다.
