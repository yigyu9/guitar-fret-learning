# 넥 쪽 상완 seed IK 사전 검수

판정: **문제없음**. Critical 0 / Warning 2 / Suggestion 0. 실행용 v16/V17·search v9·수락 후보/config·7개 사전 SHA와 실행 배치 기록을 읽기 전용으로 검토했다. 지정 리뷰 외 파일 수정·추가 native 실행·학습은 하지 않았다.

선행 V16/search_v8은 source clear·gap .163321mm·world normal Z .768960을 통과했지만 witness Gy −.453810m가 Gy>−.34m 조건에 미달해 거절됐다. native 실행 후보가 없었으며 이번 검수는 그 결과와 새 seed 후보를 구분한다.

- [seed 및 최종 검사:19](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v9.py:19): 상완 capsule의 local 축을 지정한 G 점 방향으로 향하게 하는 source IK를 같은 오른12 범위 안에서 수행한다. 그 결과는 최종 기존 최적화의 시작점으로만 사용된다. 최종 목적함수와 수락 gate의 AST가 V16과 동일하며, seed 성공만으로 후보를 수락하지 않는다. 물리 강제·접촉 추가가 아니다.
- [수락 gate:25](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v9.py:25): 완료 결과는 source clear이며 full 상완 gap **.088442798mm**, witness Gy **−.230889630m**, world normal Z **.771140007**로 조건을 통과했다. 저장 초기 상태와 새 q로 gap/normal을 독립 재계산해 일치를 확인했다. 전체 source 충돌 검사는 저장 audit와 gate를 대조한 범위다.
- [제어 재사용:45](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v16.py:45): right_indices·effort guard·construction·factory/혼합 mode step·EffortRecording의 AST가 v15와 동일하다. 기존 currentG 8mm/요청40N·gravity/posture·native effort cap·POSITION69/state guard·latch/endpoint 경로를 유지한다. PLAN/search metadata만 바뀌며 기타 직접 외력이나 state 쓰기 권한은 추가하지 않는다.

수락 후보의 81D 계약이 통과했다. 다른69 초기 q, reference PD, 기타 p/회전은 기준 저장자료와 동일하다. source 입력558개와 [사전 입력7개](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/neck_side_seed_preflight_inputs_v1.json)의 SHA가 현재 파일과 일치한다. [배치 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/native_batch_v12.json)은 이 수락 config와 새 native_v11/upper_arm_neck_side 경로를 선택한다.

Warning 1 — [초기 범위:15](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v9.py:15): 최대 초기 변화는 R_Elbow_x **1.200000017881rad**로 ±1.2rad 대비 float32 반올림 차이 약1.8×10⁻⁸rad가 있다. 실제 native 모델 한계는 모두 만족한다. 오른팔 최소 한계 여유는 R_Wrist_y **.000121593475rad**로 작다. 큰 초기 각도와 경계 접근을 자연스러운 자세·운동 여유 인증으로 해석하지 말고 실제 초기/진행 영상과 q를 확인해야 한다.

Warning 2 — [계획 가설](/home/ajou/yigyu/3/stability_adapter_2/OM_NO_STRAP_UPPER_ARM_PLAN_V17.md:7): 양수 source 미세 간격·넥 쪽 witness 수락은 cooked 초기 관통 부재나 실제 상완 지지를 인증하지 않는다. 지지점 이동의 실제 모멘트/안정 효과도 측정된 wrench 없이 인과로 단정할 수 없다. 왼팔·Head·상완 접촉, 기타 최대/종료 변화는 다음 native 진단의 별도 검증 대상이다.

핵심 SHA-256:

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v16.py | 4fa00f1f2db3ce1f454faa4d4a75df7a6bdb6eef5cb463f75ba4fe17d9670e49 |
| search_om_no_strap_upper_arm_v9.py | f667df93cdef69a9b48714ee8832f16017ca38463c0fb85269c8134837b804a3 |
| OM_NO_STRAP_UPPER_ARM_PLAN_V17.md | 0e34d7de2be353f23c176abf1f0266b82fdbe23d9e8c47c0f8b26e5dc116f541 |
| search_v9/search.json | bad21fce3574bcfccada0a56be30a3f3d3f6d8d2780bf28c9789c172cd30c296 |
| 수락 candidate.json | 2fb7b088e97762c33ec35ed7303a55c57223780b446cdf0ae578e5b23c5ead02 |
| 수락 config.json | 47b1fc0ebdb4d6782a90b6a27df04e0cb3794a1cfbf7230f8c58ec701ca47f0a |

실행 차단 사항은 발견하지 않았다. source 수락 후보 한 개에 대한 제한된 native 진단을 진행할 수 있으며, 실제 기타 유지·자연스러움·연주 성공 승인은 아니다. 지정한 새 리뷰 파일만 작성했다.
