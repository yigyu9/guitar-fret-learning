# 스트랩 없는 초기 자세 후보 · v2

이 v2는 접촉 표본의 주파수 설명을 분리합니다. 이전 문서 v1의 한 문장은 모든 표본을 60 Hz로 읽을 여지가 있어, 표의 1200 physics endpoint와 RHfinger 전용 299-query 한계를 명시합니다. 기존 v1 문서는 보존했습니다.


## 무엇을 확인했나

native 11(`upper_arm_neck_side`)과 native 12(`upper_arm_neck_side_repeat`)는 같은 초기 상태에서 각각 5초 동안 수행한 반복 평가입니다. 두 결과의 주요 궤적·영상 SHA가 같지만, 이는 해당 초기 조건의 반복 자료이며 움직이는 연주 강건성이나 학습 성공을 뜻하지 않습니다.

- native 11: [초기 문자열 포함 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_initial_strings.png), [측면 초기 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_initial_support_side.png)
- native 12: [초기 문자열 포함 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native12_initial_strings.png), [측면 초기 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native12_initial_support_side.png)
- [초기 자세와 0·0.5·2·5초 전체 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_initial_and_timeline_v2.png)
- [0초와 5초 native 장면 비교](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_zero_to_five_comparison_v2.png)

![native 11 초기 자세 및 0, 0.5, 2, 5초 전체 장면](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/images/native11_initial_and_timeline_v2.png)

## 보고된 변화와 조건

| 항목 | native 11/12 결과 |
|---|---:|
| 초기 대비 기타 body bounding-box 중심 이동 | 40.206627 mm |
| 초기 대비 actor-root 위치 이동 | 53.017170 mm |
| 초기 대비 SO(3) 회전 | 11.070532° |
| 2→5초 body 중심 변화 / 회전 변화 | 0.073932 mm / 0.028843° |
| 오른상완 접촉 관측 / 양의 raw lambda 표본 | 1187/1200 / 1181/1200 |
| 왼팔·왼손 / Head 접촉 관측 | 0/1200 / 0/1200 |
| 물리 구간 / MP4 재생 길이 | 5.000초 / 5.033333초 |

여기서 `R_Hip`은 오른 허벅지에 해당하는 모델의 Pelvis–R_Knee 사이 상부 다리 capsule이며, 접촉 횟수는 접촉 위치나 관절 중심을 뜻하지 않습니다. 각 접촉의 힘·모멘트 기여는 분리 측정하지 않았습니다. raw lambda는 N 단위 힘이 아닙니다. 표의 1200개 접촉 표본은 240 Hz physics endpoint k=1…1200에서 센 값입니다. 별도의 RHfinger 접촉 query는 60 Hz에서 299개 표본(k=4…1196)만 확인했습니다. 이 60 Hz RHfinger query를 다른 240 Hz step까지의 전기간 무접촉 인증으로 확대하지 않습니다. 40 N은 제어 계산에서 요청하는 점 힘 크기 상한이지 측정된 접촉력은 아닙니다.

스트랩은 OFF이며 strap force 호출 0회, 외부 기타 힘·부착·policy는 없습니다. root와 하체는 고정했고 기타는 자유 상태입니다. 오른팔 12 DOF는 EFFORT, 나머지 69 DOF는 POSITION PD 제어였습니다. 오른팔의 큰 초기 각도 보정(최대 약 1.2 rad)과 손목 한계 근접이 남으며, 초기 정착 이동도 있습니다. 따라서 정지 초기 조건의 5초 유지 후보로만 설명합니다.

## 원자료와 실패 진단

- [검증 요약 JSON 복사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/effort_verification_v10_cases4.json)
- [후보 비교 JSON 복사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/support_candidate_comparison_v1.json)
- [native 11 초기값 및 제어 설정](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/native11_initial_values.json), [native 11 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/native11_report.json)
- [native 12 초기값 및 report](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/native12_initial_values.json), [native 12 속성](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/native12_native_properties.json)
- [후보 검색 설정 복사본](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/data/posture/search_v9_upper_arm_neck_side_config.json)

이전 시험들은 후보 반복과 별도인 실패/진단 기록입니다. 첫 두 시험은 왼팔 접촉이 각각 295/300, 291/300 표본에서 관측되어 오른상완 독립 지지로 볼 수 없습니다. 다음 두 시험은 왼팔 및 오른상완 접촉이 0/1200이었지만 기타가 넘어졌습니다. 시험 5·6은 상완 접촉이 없었고, 시험 7은 Head 접촉이 다수 관측됐습니다. 시험 9는 Head 접촉 1086/1200, 시험 10은 오른상완 53/1200·Head 60/1200이면서 큰 root 변위와 회전이 있어 유지 성공으로 보지 않습니다. 시험별 영상은 [진단 영상 색인](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md#과거-진단-시험)에서 확인합니다.

미완료 native 8은 첫 step assertion에서 physics 0으로 끝났고 원본 두 파일은 각각 1 frame/약0.034초입니다. 정상 5초 영상과 분리된 원자료이며 이번 완성 영상 22개에 포함하지 않았습니다. [native 8 원본 whole_body](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/whole_body.mp4), [hands](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_v8/three_support_right_effort/media/hands.mp4).

원본 조건·해석은 [결과 요약 원문](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/RESULT_SUMMARY_V2.md:1) 및 [분석 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/README.md:1)에 있습니다. 10-19 자료는 이 파일들을 수정하지 않고 복사·정리했습니다.


영상 destination 대조 오류 보완은 [영상 INDEX v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/INDEX_v2.md)와 [manifest v2](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/video/manifest_v2.json)를 참조합니다.
