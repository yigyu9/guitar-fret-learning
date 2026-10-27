# 사용자 선호 자세 기반, 왼손 없이 자유 기타 유지

주신 바디 중심 좌표와 관절각을 선호값으로 사용해 초기 상태를 찾았다. **스트랩 없이 왼손 접촉 0으로 정지·작은 오른 팔꿈치 운동 각각 5초를 완료했다.** 기존 관절 자세 유지 제어는 켜져 있으며, 이번 결과는 연주/학습 성공 판정이 아니다.

## 선택 초기값

바디 중심 world `(0.099992, 0.009666, 0.704884)m`. 주신 값보다 휴머노이드 기준 왼쪽 약 7.5cm·앞 약 6cm·위 약 4cm다. 상완과 오른 허벅지에서 접촉이 유지되도록 바디 배치를 재맞췄으며 몸통 각도는 주신 값과 가깝게 유지했다.

| scalar 관절 | x (°) | y (°) | z (°) |
|---|---:|---:|---:|
| Torso | 8.49 | −1.07 | −8.29 |
| Spine | 19.00 | −1.05 | 0.61 |
| Chest | −0.58 | 18.85 | 0.28 |
| R_Thorax | −0.01 | −9.92 | 9.62 |
| R_Shoulder | 5.30 | 36.36 | −1.50 |

전체 81관절 및 기타 actor 초기 상태의 원값은 [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/native_upper50_v13_static/initial_values.json:1), 사용자 대비 표와 전체 질량중심은 [selected_summary_v1.json](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/selected_summary_v1.json:1)에 있다. 표는 반올림 값이고 suffix는 world 회전축이 아니다.

## 실제 Isaac Gym 영상

정지 시험: 초기부터 5초 물리 경과까지 원본 전신 영상이다. 기타 바디 중심 최대 변화 15.856mm·SO3 최대 회전 5.557°, 최종 10.214mm·3.494°였다. 왼팔·손·손가락 접촉은 1200step 중 0이다.

![왼손 없이 정지 유지 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/native_upper50_v13_static/media/whole_body.mp4)

팔꿈치 운동 시험: 2.5~4.5초에 목표 ±5°를 주었고 실제 R_Elbow_y scalar 운동 범위는 9.983°였다. 정지 시험과 같은 시각에서의 추가 기타 변화는 최대 0.014142mm·0.008542°다. 오른 전완은 일부 step에 닿지만 오른 손목·손·손가락은 두 시험 모두 접촉 0이었다.

![왼손 없이 팔꿈치 운동 5초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/native_upper50_v14_elbow5/media/whole_body.mp4)

아래는 정지 시험의 실제 초기 전신 프레임이다. 분홍색은 오른손, 초록색은 왼손이다. 화면에서 넥과 겹쳐 보여도 왼손이 지지한다고 판단하지 않으며 실제 접촉 로그와 대조했다.

![선택 초기 상태](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/native_upper50_v13_static/media/frames/whole_body/00000.png)

## 판정 범위와 기록

Root·하체 고정, 내부 충돌 ON, 기타 자유, 스트랩 OFF. 인간 유한 PD·중력 보상·오른 팔/몸통 point 제어는 유지했다. 기타 고정·손 부착·외부 기타 힘·지속 pose 덮어쓰기는 사용하지 않았다. 마지막 0.5초 상완·오른 허벅지 접촉은 각120/120, Thorax·Chest·trunk 접촉은 전체0이다. L_Hip 접촉은 기록하지 않아 두 곳에만 지지가 있다고 단정하지 않는다.

5초 동안 실제 1200step을 적분했다. 영상은 초기 프레임 포함151프레임/30fps로 약5.033초이며 실패 시험은 짧은 실제 경과 그대로 남겼다. 정지 시험 4→5초의 추가 변화는 0.000381mm·0.000803°로 작지만 무제어 평형을 뜻하지 않는다.

geometry 21후보 중7수락/14거절, native9시도 중2완료5초/7미완료, 총2780physics/694완료control이다. constructor 실패0step, 두 조기 실패각2physics/0완료control을 포함한다. V9 SyntaxError 및 실패 분석 로그도 보존했다.

- [구현·제어·제약·다음 단계](/home/ajou/yigyu/3/stability_adapter_2/USER_GUIDED_NO_LEFT_COMPLETION_V1.md:1).
- [모든 native 사례의 240Hz 움직임·접촉 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/analysis_final_v2.json:1).
- [실제 적용 명령·관절 움직임·동시각 비교 감사](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/timelines_final_v1.json:1).
- [선택 source 독립 검수](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/review_source_v13.md:1).
- [초기·2초·5초 전신/손 이미지와 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/user_guided_no_left_v1/artifacts_v1/README.md:1).
- [성공·실패 원본 영상 16개 모음](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/user_guided_no_left_v1/INDEX.md:1).

다음은 받침을 유지한 채 왼손을 현재 기타 기준 압현 준비 위치로 접근시키는 시험이다. 실제 fret·strike 체크포인트는 이번 검사에서 연결하지 않았다.
