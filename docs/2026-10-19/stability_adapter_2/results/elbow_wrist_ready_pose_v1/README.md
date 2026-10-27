# Elbow·Wrist 타현 준비 자세 결과

**close90 준비 자세 + 실제피크6관절보정으로내려치기/올려치기6줄전체를확인했습니다.** 초기오른어깨위치를타현영역에맞추고타현요청/추가보정은Elbow·Wrist6에만적용합니다. 몸통·어깨는준비목표와finite받침제어를유지하며실제상태를고정하지않습니다.

## 실제5초 최종영상

![Elbow·Wrist 양방향6줄 타현 전신](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/native_pick_feedback_v1_whole_body.mp4)

0~2초정착,2~3.2초준비/진입,3.2~3.55초down,3.75~4.45초up,5초까지복귀입니다. 원detector에서down6→1/up1→6 각각통과,12RELEASE모두defaultlane core입니다. physics5초,151프레임을포함한MP4길이는5.033333초입니다. 기존손확대카메라는넥중심으로오른손이화면끝에있으므로타현전체동작은전신영상을참고합니다.

## 초기 자세

![새 준비 자세 전신0초](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/native_pick_feedback_v1_t00_whole_body.png)

오른상완과오른허벅지받침을유지하며팔꿈치축을타현영역에가깝게두었습니다. 핑크색오른손은가상피크타현,녹색왼손은넥근처지만contact0입니다. 스트랩없음·기타자유/root하체고정/selfcollisionON이며유한human PD/중력보상/currentG상완제어를사용합니다. 기타고정/손부착/기타힘/state덮어쓰기없습니다.

| 준비 관절 | x (°) | y (°) | z (°) |
|---|---:|---:|---:|
| R_Thorax | -1.69 | -10.00 | 20.00 |
| R_Shoulder | 1.83 | 53.96 | -1.62 |
| R_Elbow | -24.07 | 87.13 | -40.26 |
| R_Wrist | -20.77 | -6.47 | -5.12 |

## 비교

| 실제 실행 | 내려치기 | 올려치기 | 완료 | 왼팔·손 접촉 | 오른 손목·손 접촉 |
|---|---|---|---|---:|---:|
| native_static_v1 | [] | [] | 5초 | 0 | 0 |
| native_strike_v1 | [6, 5, 4, 3, 2, 1] | [1] | 5초 | 0 | 0 |
| native_velocity_v1 | [6, 5, 4, 3, 2, 1] | [1, 2, 6] | 5초 | 0 | 0 |
| native_slow_up_v1 | [6, 5, 4, 3, 2, 1] | [1, 3, 5] | 5초 | 0 | 0 |
| native_pick_feedback_v1 | [6, 5, 4, 3, 2, 1] | [1, 2, 3, 4, 5, 6] | 5초 | 0 | 0 |

모든조건기타최대BB이동11.410449mm/회전3.872548°로첫2초정착궤적이exact같습니다. 최종선택조건은최종이동9.917425mm/회전3.358788°입니다. 왼팔·손접촉0,오른전완/손목/손가락0,가슴·몸통·머리0. 상완·오른허벅지후기접촉각120/120step입니다. 무제어수동평형·체크포인트곡완주·학습성공을의미하지않습니다.

## 보관 문서

- [초기81관절값](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/native_pick_feedback_v1/initial_values.json:1)
- [적용config](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/native_configs_v1/strike.json:1)
- [원detector 정량분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/analysis_v4.json:1)
- [6관절 명령·first2s·렌더 marker검증](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/command_audit_v2.json:1)
- [초기3조건 영상·캡션](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v1/README.md:1)
- [최종2조건 이미지·영상 설명](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/artifacts_v2/README_v2.md:1)
- [전체영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/elbow_wrist_ready_pose_v1/INDEX_v2.md:1)
- [제어구현·실험제한·다음작업](/home/ajou/yigyu/3/stability_adapter_2/ELBOW_WRIST_READY_POSE_COMPLETION_V1.md:1)
- [변경파일 절대경로와실제줄](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/elbow_wrist_ready_pose_v1/CHANGED_FILES_v1.md:1)

source6중수락1/기각5,깊이envelope기각1·V4실행0,native5회각5초/총6000physics·1500control입니다. 이전파일과실패도보존합니다. command감사V1에서새stage없는static/strike의maxcommand0은실제명령0이아니며V2에서보완했습니다. 최종검수와봉인기록은완료후생성하며임시성공문서를만들지않습니다.
