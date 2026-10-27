# 팔 기준 자세와 접촉 지지 결합 — 실행 전 독립 검수

요약 판정: **문제없음**. 새 leaf 계획·controller·runner·보존 wrapper·shell·분석기·저장 상태 수치 검증 producer를 읽었다. 확인된 Critical/Warning은 없다. 검수자는 trial과 producer를 실행하지 않았고 기존 source·결과·검수 문서를 수정하지 않았다.

## 확인 사항

- [palm_thumb_posture_support_v1.py:58](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_support_v1.py:58)의 DLS 관절 오차와 팔 초기각−실제각을0.25 계수로 합쳐 하나의17차원 PI에 입력한다. 엄지5에는 joint-hold 오차를 더하지 않는다. 최종 목표는 초기각+결합 오차+2×적분이다(65).
- 최종 목표의 native limit·초기 기준 팔0.3/엄지0.15rad cap·팔0.8/엄지0.3rad/s slew 교집합을 적용하고 raw−final과 오차 방향으로 적분 포화를 판정한 뒤 다시 계산한다(62–72). 시뮬레이터 상태·기타 외력/effort를 쓰지 않는다.
- [run_palm_thumb_posture_support_v1.py:62](/home/ajou/yigyu/3/stability_adapter_2/run_palm_thumb_posture_support_v1.py:62)에서 기존 외부 왼팔 hold PI를 비활성화하므로 두 적분기가 중첩되지 않는다. 오른팔 기존 PI는 유지하고 단일81 PD 목표만 제출한다. 실제 상태 불변·목표 한계/속도·다른 목표 유지·고정 root/하체·palm-up240Hz 검사를 유지한다.
- normal 종료 기록은1200 physics step·60Hz 접촉300표본·30Hz native COLOR151frame이며, partial/crash journal과 subprocess 입력 보존은 기존 수정 구조를 유지한다. [palm_thumb_posture_preserved_v1.py:48](/home/ajou/yigyu/3/stability_adapter_2/palm_thumb_posture_preserved_v1.py:48)는 새 runner를 실행한다.
- [analyze_palm_thumb_posture_support_v1.py:21](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_posture_support_v1.py:21)은 baseline_v4/candidate_off/candidate_on/posture_on의4조건을 별도 `analysis_posture`에 비교한다. 직접 소비 native guard metadata를 SHA에 포함하고 입력 보존 실패 조건은 제외한다. 0.25초 bin의 t0·경계를 정확히 포함하며 native PNG 비율은 유지한다.
- Fret gate는 기준보다 동시 양의 raw solver 응답 표본이 늘고30Hz 자세 표본의 최대 actor-root 이동·shortest 회전이 모두 감소한 조건만 허용한다. raw lambda는 N·미끄럼 방지 성공으로 환산하지 않는다. 전체 자연 회전 범위 검증이나 연주 성공 판정으로 확대하지 않는다.
- [test_palm_thumb_posture_support_v1.py:24](/home/ajou/yigyu/3/stability_adapter_2/test_palm_thumb_posture_support_v1.py:24)은 저장 native 상태의17관절 분할·FK·상태 읽기전용·속도/범위·frame 변환·불일치 거부·anti-windup을 확인한다. 실제 접촉은 새 native 결과로 별도 판단해야 한다.

## 범위

이번 구현은 checkpoint 없는5초 지지 비교다. 최종 목표는 초기 기준이며 엄지 Fret 정책 요청에 합성하는 구현은 아직 별도 후속이다. Fret을 연결한다면 최종 제출 목표와 실행 history의 소유권을 별도로 검수한다.

실제 결과·문서·이미지·영상 및 최종 입력 불변성은 후속 최종 검수에서 확인한다.
