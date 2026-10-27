# 왼손: 넥 아래·뒤·줄 면에 맞춘 초기 준비 자세

손바닥은 아래, 엄지는 뒤, 네 손가락은 줄이 있는 앞면 가까이에 놓도록 왼쪽33 초기각을 조정했다. 실제 Isaac Gym 초기6면 검증과5초 실행을 완료했다. 기타는 자유·스트랩 없음·하체 고정·self collision ON이다. 오른쪽 기존 Elbow/Wrist6 타현 제어를 유지했다.

초기 면 간격은 손바닥12.83/엄지15.46/검지4.83/중지14.19/약지13.76/새끼9.10mm. 5초에는 엄지17.99mm로 엄격한 초기2~16mm gate를 벗어난다. 그 때문에2초 이후 전체gate통과율0%이며 **모든 부위가 접촉하는 grip 성공으로 판단하지 않는다**. 손바닥·엄지 실제 접촉0, 검지109/새끼1183 physics step에서 접촉query가 있었다.

기타 최대 바디중심 변화10.02mm/회전3.32°. 가상 피크1회 down6→1/up1→6 검출을 확인했으나 checkpoint·압현학습·노래 성공은 아니다.

- [완료 내용과 다음 단계](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_COMPLETION_V1.md:1)
- [새 파일 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/CHANGED_FILES_v1.md:1)
- [현재 config](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/search_v5/station20mm/config.json:1)
- [실제 초기 상태](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/initial_values.json:1)
- [실제 면 재구성 감사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/face_audit_v1.json:1)
- [타현 검출](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/strike_analysis_v1.json:1)
- [명령·줄 marker 검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/command_audit_v1.json:1)

초기실제 앞시점:

![네 손가락은 줄 면, 손바닥은 아래](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/media/frames/hands/00000.png)

초기실제 뒤시점:

![엄지는 넥 뒷면 가까이](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/media/frames/thumb_back/00000.png)

![5초 전신 영상](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/left_neck_three_face_v1/native_off_v1/media/whole_body.mp4)

V1setup실패0후보, V2/V3/V4 각2후보 기각, V5 1후보 수락, native 1회. source는CPU 형상 제안이고 위 이미지는실제 Isaac Gym 카메라다. 선택facet 면간격은 해부학pad·최단거리·접촉력 인증이 아니다. 최종 독립검토와 보존감사 파일은후속에 별도로 기록한다.
