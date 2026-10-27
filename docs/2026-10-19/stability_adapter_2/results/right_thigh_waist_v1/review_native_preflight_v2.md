# 넥 축 회전 후보용 runner3 사전 검수

판정: **코드 준비는 문제없음. 실제 후보·정확cfg 통과 후 조건부 실행.** Critical 0건, Warning 2건, Suggestion 0건. 새 후보는 아직 확정하지 않은 검수다.

runner2→3 diff는 [초기 neck direction 검사](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v3.py:58) 한 곳이다. 기존 전체 G회전 보존 대신 원래 world 넥축 방향 차이<1e−6을 요구한다. 전체39 predicted G pose 길이·위치<3µm/회전<1e−5rad 비교와 실제 delta 기록은 유지하므로 source5에서 새로 허용한 local G_Y 회전을 검사하면서 엉뚱한 초기 회전을 허용하지 않는다.

root/하체·finger42·q_ref/model·PD/mass/FK·actual source LP/state 보존·human37 mesh/SHA pin은 동일하다. 현재33 EFFORT/48 POSITION, body150/1·Thorax40/16mm·Shoulder10/4mm·왼 wrist30N과 단일81 effort/4physics owner·금지 상태쓰기/기타 힘·속도/기타 변위 가드는 바뀌지 않는다. 원 prototype/실패 출력은 보존한다. AST 검사를 통과했다.

## Warning

- [runner3:58](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v3.py:58): 넥축 방향 보존은 front/back 판의 회전이나 기타 위치 보존과 다르다. 새 source 회전·p와 실제 초기 상태의 허용오차 검사를 통과했는지 확인하고, 전체 초기 JSON exact라고 설명하지 않는다. 수락 candidate/config SHA·81q와 추가 ±5° 여유를 확인하기 전에는 실행 후보를 승인하지 않는다.
- [runner3:95](/home/ajou/yigyu/3/stability_adapter_2/run_right_thigh_waist_v3.py:95): 위치 보호는 actor-root 초기 대비 norm20cm이며 바디 BB 중심 이동·높이·SO3와 다른 양이다. 직전 중단을35° 또는50rad/s 실패로 바꾸지 않는다. 새5초 완료 여부·접촉·기타 변화·왼손/허벅지 기여는 실행 후 별도로 판단한다.

검수 SHA-256: run_right_thigh_waist_v3.py `69e75bbe8ea30aa26e52e75b7227e1f9dde3d9d92ab7f0571bda1d46aaf06a18`.

새 native·source fitting·정책 추론/학습 및 다른 소스·원자료·기존 리뷰 수정은 하지 않았다. 실제 후보/결과·최종 보존 봉인을 선인증하지 않는다.
