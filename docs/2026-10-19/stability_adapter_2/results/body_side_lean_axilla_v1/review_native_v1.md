# 바디 쪽 기울임 두 native 시험 독립 검수

요약 판정: **문제없음.** Critical 0 / Warning 1 / Suggestion 0. 실제 저장 상태·명령·접촉·분석식을 대조한 기록이며 **초기 기타 자세 유지 성공의 승인이 아니다.** 새 물리 실행·학습은 하지 않았다.

두 실행은1200 physics/300 control·5초를 완료했고 초기 JSON 전체가 exact였다. source1~4의 거절을 보존한 뒤 source5의 임시5mm 근접 gate로 같은 초기 후보를 사용했다. source5는 실제 접촉/안전 문턱이나 최종 자세 채택이 아니다. 이번 확정 방향은 player-right=정면 화면 왼쪽=기타 바디 쪽이다.

| 조건 | 바디 BB 중심 / root 이동 | 초기 대비 SO3 | 최종 G+Y 넥 고도 | 상완 / 전완 / left / Head 존재 |
|---|---:|---:|---:|---:|
| 전완 | 48.051 / 373.073mm | 52.174° | −15.921° | 968 / 1191 / 0 / 0 of1200 |
| 전완+상완 | 47.501 / 345.241mm | 47.662° | −10.019° | 256 / 1149 / 0 / 0 of1200 |

trace에서 body bbox 중심·root 이동·SO3를 재계산하고 endpoint 접촉을 직접 집계해 [첫 조건 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v2/verification.json:1), [두 점 분석](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/analysis_v3/verification.json:1), [요약](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/result_summary_v1.json:1)과 일치함을 확인했다. 넥 고도는 `asin((R*[0,1,0]).z)`의 world 수평 기준 부호 각도로 SO3 전체 회전과 다르다. 2→5초 변화는 각각0.310mm/0.317°,0.316mm/0.494°지만 이미 회전된 뒤 정착한 것이며 초기 방향 유지 성공이 아니다.

각1200행의 전완 점 위치/속도·posture·요청 합산·model clip을 재계산했다. 최대 요청 차이는8.88e−16/1.78e−15Nm였고 실제 actor effort1200회/other69 effort0/owner window 종료 기록을 확인했다. 새 상완 항은 기존 전완+gravity+posture 미clip 요청에 더해 한 번 제출한다. 각 점30N은 합계30N이나 측정 접촉력 cap이 아니다. POSITION69 목표/상태 불변·Jacobian gate를 유지하며 직접 기타 힘·부착·pose 쓰기를 추가하지 않는다. 전체 gravity/Jacobian·접촉별 힘 기여는 이 검증으로 인증하지 않는다.

[요약 producer](/home/ajou/yigyu/3/docs/2026-10-19/stability_adapter_2/results/body_side_lean_axilla_v1/summarize_trials_v1.py:17)의60Hz 제어 직전 표본0..1196도 직접 대조했다. R_Hip 존재는297/300씩, 양lambda는297/296이고 L_Hip 존재는3/5표본이다. 240Hz endpoint1..1200과 다른 표본계열이며 합산하지 않는다. raw lambda·접촉 존재는 N 힘·지지 비중이 아니다. 원source Hip 표기 오류는 source_scope_note에서 L0.131/R1.782mm로 구분했다.

## Warning

1. [analyze_body_side_lean_axilla_v2.py:19](/home/ajou/yigyu/3/stability_adapter_2/analyze_body_side_lean_axilla_v2.py:19): 상대 config 경로의 절대키 lookup 문제가 남아 있다. 성공 분석은 절대 CLI 경로로 수행했으며 기존 상대 경로 실패 analysis_v1을 보존한다. 현 결과에는 영향이 없지만 재사용 시 case/config/out은 절대 경로로 사용하거나 향후 새 버전에서 정규화해야 한다.

검수 SHA256:

- summary: `c8c848354518a53e1a6eb905a60a2efcc0e14a334bb0fa9bb18f49cfe6064a7b`
- summary producer: `023de384bee8abcbc17eae95c861d16ffe0a68510520b27db6e8a6e2cd5f7df6`
- analysis_v2: `cadc03f1b743df6effaf659dd5ba8a60a3f1d02051933725bb112a928c100cb0`
- analysis_v3: `515b6777041caa61367a0fad2f436b1583ffdc821d6a680586c64442f97f0226`

실제 문서·그림·보존감사의 최종 범위는 별도 final 리뷰에서 기록한다. 이 새 리뷰 외 기존 파일을 수정하지 않았다.
