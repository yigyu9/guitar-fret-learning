# 스트랩 없는 상완 지지 후보 최종 독립 검수

판정: **문제없음 — 완료된 동일 조건5초 진단 범위 승인**. Critical 0 / Warning 1 / Suggestion 0. 새로운 native 실행·학습이나 다른 담당 파일 수정은 하지 않았다.

## 확인한 결과와 구현

[실행용 v16](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v16.py:45)·[source v9](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v9.py:19)·V17/V18과 기존 사전 검수 결과를 대조했다. 오른12 EFFORT·제한된 human actuator window/cap, 다른69 POSITION 목표, root/하체 고정, strapOFF와 자유 기타를 유지한다. 기타 직접 force/attachment·runtime pose 덮어쓰기를 추가하지 않았다.

[analyzer v10](/home/ajou/yigyu/3/stability_adapter_2/analyze_om_no_strap_upper_arm_v10.py:19)은 v9의 계산/검사를 유지하고 helper·asset·mesh·기준 초기값 입력 pin을 보완한다. [반복 비교 producer](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/summarize_support_repeat_v1.py:13)와 canonical JSON을 읽고, native11/12 원자료에서 핵심 수치를 독립 재계산했다.

| 검증 항목 | 확인 결과 |
|---|---:|
| 초기 q·PD·mass·native state / 전체 trace | 두 실행 exact 동일 |
| 바디63 source hull bounding-box 중심 종료 이동 | 40.206627mm |
| actor-root 종료 이동 / 초기 대비 SO(3) 회전 | 53.017170mm / 11.070532° |
| 2→5초 중심 추가 이동 / 회전 | .073932mm / .028843° |
| 상완 접촉 presence / 양의 raw lambda 끝점 | 1187 / 1181 of1200 |
| 왼팔·왼손 / Head 접촉 끝점 | 각각0 of1200 |
| 각 실행 물리 / POSITION 검증 / effort | 1200step·5.0초 / 300회 / 1200회 |
| 후보 전신·손 영상 | 두 실행 view별 SHA exact 동일 |

바디 중심은 실제 source collision hull bounding-box 중심이며 COM/actor-root와 다르다. 60Hz query는 step4..1196의299개로 상완296·Chest290·R_Hip293·L_Hip5회 presence가 있었다. 오른 손가락 접촉은 이 표본에서 관측되지 않았으며 전기간 무접촉을 인증하지 않는다. raw lambda와 횟수는 N 단위 힘·지지 비중이 아니다.

## 설명·시각 자료·보존

최종 candidate v2 PNG2장을 실제로 열고 native 초기 전신 프레임과 대조했다. footer 문장들이 배경 안에 들어오며 초기/후기 장면과 두 위치 지표를 구분한다. diagnostic v2의 native10 실패 패널도 실제로 확인했다. candidate v1/v2·diagnostic v2의 producer/입력 전후/출력 SHA를 확인했고, 영상 manifest1/2/3의 모든 원본·복사본 SHA가 일치했다. 물리5.0초와151frame/30fps MP4의5.033333초를 구분한다.

기존 README의 접촉 원인 표현은 [RESULT_SUMMARY_V2](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/RESULT_SUMMARY_V2.md:3)가 **유지와 접촉의 동시 관측이며 각 힘/모멘트 기여는 미측정**으로 한정했다. 보완을 확인했다. 최초 effort 실패는 readback 또는 state 불변의 결합 assertion에서 physics0·effort0으로 종료한 기록이며 원인을 분리 확정하지 않는다. 완료11회/13200step과 실패1회0step, 재료 읽기1회0step, source V15/V16 거절을 구분한다.

main4의 두 append 단계에서 원문 prefix와 기록 SHA 연결을 독립 확인했다. 핵심 문서 절대링크98개와 지정 행 존재를 확인했다. [봉인 v3](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/seal_phase_v3.py:11)의 입력/provenance·영상·이전 inventory·append-chain·실패/완료 분리·배타 출력·최종 SHA 검증 논리와 AST 문법에 중요한 누락을 발견하지 않았다. 실제 봉인 실행 및 source_final/inventory/final_verification 생성은 root 후속 작업이다. 이전 단계 전량/43553 입력의 중복 재검사는 수행하지 않았다.

## 남은 주의

Warning 1 — [최신 요약](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/RESULT_SUMMARY_V2.md:7): 초기 약40mm/11° 정착 변화, 큰 오른팔 초기각과 R_Wrist_y 한계 접근은 남는다. 같은 초기조건2회 재현은 외란·팔 운동·fret/strike 강건성이나 학습 성공이 아니다. source 양수 간격, 한 점 Jacobian 속도 대응, torque 명령은 cooked 관통·전체 인체 Jacobian/중력 보정·측정 접촉력 인증으로 확대하지 않아야 한다. 이 한계는 최종 문서에 명시돼 있다.

핵심 검수 SHA-256:

| 파일 | SHA-256 |
|---|---|
| run_om_no_strap_upper_arm_v16.py | 4fa00f1f2db3ce1f454faa4d4a75df7a6bdb6eef5cb463f75ba4fe17d9670e49 |
| analyze_om_no_strap_upper_arm_v10.py | c23d0f6ea0274d7085a68febd30bb7a69092a57e9e5a3fbc330e6e2429cda4c5 |
| effort_verification_v10_cases4.json | 5b440dcd3480e6b5481c9fc9dd6b19aaa09cf77e93df4ceb06e87a66f9710f83 |
| support_candidate_comparison_v1.json | ca736088cdef38d8f1e72fbb470c79e8e84fd9113f6a2797dcf9a3b8b672f733 |
| RESULT_SUMMARY_V2.md | 60009df08a8bfc3f150fea5cac64b1e56a49844c28c466b899bc335f20709d6f |
| seal_phase_v3.py | 9560951245a781e2e9a59c71c0e0d12fe1e348c038503999204415f510ab3650 |

최종 봉인을 막는 Critical은 발견하지 않았다. 지정한 이 새 리뷰 파일만 작성했다.
