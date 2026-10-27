# 하체 초기각 제한 탐색·native 비교 검수

2026-10-06, 별도 change-reviewer 검수. 요약 판정: **문제없음**.

현재 남은 Critical / Warning / Suggestion은 없다. 승인된 설정 범위·진단 구현·
원자료와 산출물의 정확성에 대한 판정이며 안정 자세 채택 또는 연주 성공 판정은 아니다.

## 검수 범위

- [하체 초기 입력](/home/ajou/yigyu/3/stability_adapter_2/trial_settings.py:32)은 유효 Hip/Knee/Ankle/Toe 초기각에 native 한계와 기준각 ±0.05rad를 함께 적용하고, 고정 폭 축과 범위 밖 입력을 거부한다. 주 제어 66관절 범위는 확장하지 않는다.
- [ground probe](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:48)는 선택 옵션으로 source z=0 plane을 추가한다. [거리 query](/home/ajou/yigyu/3/stability_adapter_2/initial_overlap.py:83)는 signed gap·cutoff 한계를 명시하며 native cooked clearance로 사용하지 않는다. 기본 옵션은 false로 과거 query를 보존한다.
- [탐색](/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:41)은 매 후보를 새로운 native 환경의 t=0에서 평가하고 physics step을 실행하지 않는다. 5레벨·최대 2회 좌표 탐색, 기타–사람 음수 pair 증가 거부, 기준보다 나은 후보 최대 3개 선정 계약과 일치한다.
- [native 비교](/home/ajou/yigyu/3/stability_adapter_2/compare_lower_initial_pose.py:61)는 +5mm 기타 초기 상태/목표·root·상체 초기 상태·gain/cap/solver·절대 스트랩 길이를 대조한다. [body 방향 편차](/home/ajou/yigyu/3/stability_adapter_2/compare_lower_initial_pose.py:54)는 정규화된 native body quaternion의 상대 geodesic이며 scalar DOF 편차와 별개다.
- [실행 계획](/home/ajou/yigyu/3/stability_adapter_2/LOWER_INITIAL_POSE.md:3), PLAN 20절, 선정 입력 세 파일, 추가 단위/native 테스트, plot 코드, 결과 README와 VISUAL_REPORT 12절을 검수했다. 구현·원자료·기존 결과는 수정하지 않았다.

## 독립 검증

1. 프로젝트 rl38/native Gym 환경에서 전체 unittest 20개를 직접 실행해 통과했다. plane–box +/0/− gap, 제한 입력 및 native 상체/root/기타/PD 보존 검사를 포함한다. GPU와 renderer는 이 CPU 진단에서 검증하지 않는다.
2. 101개 저장 평가의 승인 범위·공통 +5mm/절대 L_A·검사 flag와 순위를 재계산했다. 선정 ID [45, 58, 66]이 정확히 일치했다. 기준선과 세 선정 후보를 새 native scene t=0에서 재구성해 initial-state SHA, 기타–사람 query와 ground query를 정확히 재현했다. physics steps는 0이었다.
3. 자기 SHA 감사 추가 전후 search/search_verified의 101개 평가 행 및 선정 ID가 정확히 일치했다. 검증된 search의 자기 모듈 SHA가 현재 코드와 일치하고 모든 최종 검사 flag가 true임을 확인했다. ground 기본 옵션을 끈 과거 +5mm 초기 geometry query도 그대로 재현됐다.
4. baseline/c01/c02/c03를 각각 24 physics steps로 파일 저장 없이 독립 재현했다. 각 run의 25개 상태·trace, 24개 contact 기록과 leg_torques 전체가 원자료와 정확히 일치했다. 기타 candidate/source 위치와 회전 최대 오차, 하체 raw 편차, scalar 한계 위반 및 body quaternion geodesic 최대값도 독립 계산해 일치했다.
5. [비교 그림](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:12)과 [c02 자세 그림](/home/ajou/yigyu/3/stability_adapter_2/plot_lower_initial_pose.py:81)을 직접 확인하고 임시 경로에서 재생성했다. 각각 2193×1436, 1812×1036 PNG가 픽셀까지 동일했다. 기존 JSON/PNG SHA256과 mtime은 검증 전후 불변이었다.
6. [결과 표·설명](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md:9), [누적 그림 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:498)을 원자료와 대조했다. case 29의 source floor +4.607mm와 R_Hip/G:body −9.071mm tradeoff 설명도 정확하다.

## 수정 후 해소된 지적

- 탐색 runtime hash 목록에서 자기 모듈이 빠졌던 Warning은 [search_hashes](/home/ajou/yigyu/3/stability_adapter_2/search_lower_initial_pose.py:12)의 시작·끝 감사와 새 search_verified 기록으로 해소됐다. 첫 실행 결과와 source는 보존했다.
- c02 endpoint 그림과 전체 구간 peak를 혼동할 수 있던 문구는 [README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/lower_initial_pose_v1/README.md:26)와 VISUAL_REPORT에서 분리했다. 최대 116.688773°는 step15·0.0625초 L_Knee에서 발생하며, 그림의 step24 최대는 L_Ankle 90.608272°다.

## 결과 해석·기록 한계

최선 초기 source-ground gap은 −9.690869→−9.443120mm로 약 0.248mm만 개선됐고,
음수 pair 2개가 남았다. 1mm 탐색 목표는 미달이며 국소 탐색이 전 공간의 해 부재를 증명하지 않는다.
C02는 기타 오차 7.173984mm/1.591075°와 0.1초 내 L_Knee–넥 접촉 없음이 확인됐지만,
하체 raw/한계 위반 90.754896°와 실제 body 방향 최대 편차 116.688773°가 남았다.
이는 초기각 민감도 진단 사례이며 안정 자세 후보로 채택하지 않은 설명이 타당하다.
네 run의 전체 24step 적용 장력은 0N이며 feedback은 없다. source gap과 실제 native
접촉·상태를 구분하고 초기 배치 개선으로 관절 표현/제어 문제 해결을 주장하지 않는다.

원본 보호 파일과 최종 source snapshot/manifest 수집은 부모가 관리하는 마무리 증거다.
리뷰어는 이전 보호 기준 스냅샷을 새로 만들지 않았으며, 이번 승인 소단계의 실제 결과와
독립 재현을 검수했다. 리뷰어가 새로 작성한 파일은 요청된 이 review.md 하나다.
