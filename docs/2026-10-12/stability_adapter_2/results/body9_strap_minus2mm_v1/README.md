# 같은 초기 자세·손목 움직임에서 스트랩 -2mm

절대LA만2mm줄인한actual5초에서최대초기이동·회전오차와2~5초변화가모두줄었다. 원본LA의같은움직임보다나은후속비교기준으로유지한다. 전체연주·초기p/q복원보정·손바닥옆면grip완료는아직아니다.

## 초기값과 변경 범위

실제native humanoid/기타t0상태·초기81/기존81target·PD·physics·초기route길이·기타목표p/q·cablelaw·최종66명단·파형을11field로exact비교했다.1200개의제출target/갱신step/파형도기준small_wrist_motion_v1과exact였다. Body9PD×2/목표유지,root하체물리고정,자유G·selfcollision정책도같다.

Trial물리입력변경은 initial_settings.strap_rest_length_m 한필드다.1.1018469719600776→1.0998469719600776m이고길이는5초내내상수다. 각도/기타초기translation/mainoffset/PDscale은같다. 새trialpath/SHA·선언LA/closure를새proposal에명시했고원본소스/입력/계획은수정하지않았다. Freshnative초기형상admission을다시통과했다.

[새trial](/home/ajou/yigyu/3/stability_adapter_2/trials/body9_strap_fine_v1/la_minus2mm.json:1), [초기값·실제81/G p/q·PD](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/initial_values.json:1), [선언](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/proposal.json:1), [실행계획](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_FINE_COMPARISON_PLAN.md:1), [전체실측](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/analysis.json:1)을따른다.

## 실제 Isaac Gym 영상·초기/종료

![스트랩−2mm의실제손·기타·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/hands.mp4)

![동일실행의전신·스트랩0~5초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/whole_body.mp4)

한actual1200step/5초,카메라두개각151frame/30fps·인코딩5.033333초다. 원nativePNG와actual13routeoverlay를모두보존했다. 주황실선/가려진옅은점선은passive cable경로이며clothmesh가아니다. 기존과동일한CPU PhysX/CUDA/context/visualgeom경고를원로그에남겼다.

![실제initial 손·기타·스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/frames/hands/00000.png)

![실제5초종료 손·기타·스트랩](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/native/frames/hands/00150.png)

초기geometry는같고표시restlength만1.099847m다. Native actual p/q를고정/덮어쓰지않았다. Palm–G 양의rawλ step은이번도0이므로손바닥옆면지지를만들었다고설명하지않는다.

## 비교 수치와 그림

| 항목 | 원본LA/같은동작 | LA−2mm/같은동작 |
|---|---:|---:|
| 최대초기위치오차(mm) | 14.132608 | 14.010556 |
| 최대초기회전오차(°) | 2.894328 | 2.607665 |
| 종료초기위치오차(mm) | 13.817898 | 13.735694 |
| 종료초기회전오차(°) | 2.894219 | 2.607149 |
| 2초기준2~5초최대위치차이(mm) | 0.481766 | 0.363488 |
| 2초기준2~5초최대회전차이(°) | 0.091929 | 0.070089 |
| 실제손목좌표1Hz진폭(°) | 0.146929 | 0.147836 |
| 초기slack(mm) | 16.013697 | 14.013697 |
| 첫양의법칙T step | 39.000000 | 37.000000 |
| 최대법칙T(N) | 24.129230 | 28.152161 |
| 종료법칙T(N) | 1.888452 | 1.807247 |


![동일손목움직임의기타오차와법칙장력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/body9_strap_minus2mm_v1/artifacts/guitar_errors_and_strap_tension.png)

위/중간패널은원 world초기p/q에대한실측trace오차다. 아래는저장state직전제출된cable법칙T이며실제contactλ를N으로변환한값이아니다. 두길이의route position/velocity로이전state→다음step법칙T를재구성한최대오차는모두0N이다. K6000N/m·damping120Ns/m·cap300N을그대로썼고두초기법칙T는0이다.

최대위치오차는0.122052mm(약0.86%),회전은0.286663°(약9.90%)줄었다.2~5초pose범위도위치0.118278mm·회전0.021840°줄었다. 초기·종료·후반지표를혼동하지않는다. 초기에장력이생기는step은39→37로앞당겨지고peakT는24.129230→28.152161N으로늘었다. 이러한관측을단일원인/인과인증이나최종성공상한으로확대하지않는다.

실제L_Wrist_x의2~5초 qminus원본정지기준을constant/trend/sin/cos1Hz로fit한진폭은0.147836°다. 이전같은파형0.146929°와비슷하여손목동작이없어진결과가아니다. Scalar q진폭은뼈회전으로동일시하지않는다. 실제palm–기타양의rawλ/selfSDKcontact step은둘다0이고native충돌mask정책은그대로다. 다른finger/허벅지지지를palm지지로치환하지않는다.

## 검증과 다음 단위

입력생성4검사·native보고서검사·offline분석10검사,604native/overlayPNG SHA와원자료closure가통과했다. 실제그래프와native초기/종료PNG를열어대조했다. Native는1회/1200step이고입력생성/그래프는native0이다. Luna/change-reviewer는agent thread limit reached로실패해root가작성/검증했고독립승인으로표시하지않는다.

[영상모음124개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v3.md:1)에두복사본을추가했다. 이전영상/모음/목록은같은바이트로보존했다. [다음original대비−4mm계획](/home/ajou/yigyu/3/stability_adapter_2/BODY9_STRAP_MINUS4MM_PLAN.md:1)은미실행이다. 현재−2mm를유망한동작비교기준으로두되해당길이의별도무동작정지µm범위는측정하지않았다. 초기이탈추가감소와이후실제관절로p/q오차복원·연주target+안정화보정권한설계는계속진행한다.
