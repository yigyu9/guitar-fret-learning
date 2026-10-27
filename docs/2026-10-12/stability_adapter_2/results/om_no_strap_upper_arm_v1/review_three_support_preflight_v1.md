# 세 지지점 초기 배치 사전 검수

판정: **문제없음**. Critical 0 / Warning 1 / Suggestion 0. V10 계획·source search v5·실행 wrapper v9·저장 후보와 사전 SHA를 읽기 전용으로 검토했다. 지정 리뷰 외 파일 수정이나 추가 native 실행·학습은 하지 않았다.

- [source 탐색:27](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v5.py:27): 몸통 전경 증분을 분산하고 머리 world 방향·왼palm world 위치/방향을 보정한다. 기타는 회전·world x를 유지하며 y/z만 조정한다. 초기 오른 Thorax3은 low3 reference±.05rad, 나머지 오른팔은 직전 초기값±.8rad∩native 한계를 사용한다. 통과 후보의 81D 계약 생성, 손가락 각 불변, 초기 body/head/left/Thorax 한계를 확인했다.
- [수락 조건:53](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v5.py:53): 전체 source 검사, capsule 간격, 근위 상완·Chest·최소Hip 간격, 왼palm·머리·몸통 오차를 함께 요구한다. lean4는 거절되고 lean8/12만 저장됐다. source 입력758개와 별도 사전 입력8개의 SHA가 현재 파일과 일치한다.
- [실행 wrapper:12](/home/ajou/yigyu/3/stability_adapter_2/run_om_no_strap_upper_arm_v9.py:12): 기존 v7 construction PD와 v6의 고정 초기 motor preload·PI를 그대로 사용한다. v8의 현재 기타 상대 IK를 사용하는 단계는 아니다. AST로 저장 체인을 연결한 모의 검사에서 저장1회·재귀 없음·최신 초기 계획·source SHA·기존 PI/PD 설명 보존을 확인했다. strapOFF와 단일 목표 제출 경로도 유지한다.

lean12 원자료를 대조하고 저장 FK 및 선택한 source 거리 5개를 독립 재계산했다. 기타 이동은 world Y −23.441789mm / Z +2.834434mm, body scalar 최대 변화는 4.480198°이다. source 간격은 Chest 3.000002mm, L_Hip 3.000000mm, R_Hip 13.128139mm, 전체/근위 오른 상완 약1.000015mm이다. root·양Hip pose·기타 회전과 x는 유지되며 저장 predicted pose도 같은 FK 결과와 일치한다.

Warning 1 — [수락 범위:53](/home/ajou/yigyu/3/stability_adapter_2/search_om_no_strap_upper_arm_v5.py:53): lean8은 Chest 4.586444mm / 최소Hip 4.568373mm로 6mm 미만 수락 범위를 통과했다. 이를 3mm에 정확히 맞춘 후보로 표현하지 않아야 한다. 먼저 계획한 lean12 시험에는 영향을 주지 않는다.

[사전 입력 SHA 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/om_no_strap_upper_arm_v1/three_support_preflight_inputs_v1.json)을 확인했다. 핵심 검수 SHA-256은 다음과 같다.

| 파일 | SHA-256 |
|---|---|
| search_om_no_strap_upper_arm_v5.py | 816e9819c8786acc90631ea8974dab65ebddd9a2bd4033d3dc1b08706b85b157 |
| run_om_no_strap_upper_arm_v9.py | a7398088d899d6032a71b5ace7e48ecaf471af5ef351a8fa21a3c57eaa9dc1ee |
| OM_NO_STRAP_UPPER_ARM_PLAN_V10.md | c56c7d1926186649437e39970f0b4dbe7071dbebb31b28de3d2340fcdf340802 |
| search_v5/search.json | 278490a8b7138e53bd338daa8420b21cb275565aa8ac1ee28ec48643b9880b09 |
| lean12 candidate.json | 445d1e4f53bcf8e2beb6d44daebb2c02610cf41215605519b279f72942dc7c56 |
| lean12 config.json | 50e14eebd49c0e8e5372f86b3684c9b83865164d34bacd039bf5e9a1a220a976 |

실행 차단 사항은 발견하지 않았다. 전체 source 충돌 결과는 저장된 audit와 gate를 검토한 범위이며, 새 native cooked clearance나 움직이는 동안의 접촉·힘 기여·왼팔 비접촉·기타 유지 성공은 인증하지 않는다. 초기 접근 배치와 실제 세 부위 지지는 다음 시험에서 구분해 판단해야 한다.
