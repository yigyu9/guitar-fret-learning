# v3 실행 전 검수 보완 — 분석기 수정 확인

요약 판정: **문제없음**. [review_pre_v3.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/review_pre_v3.md:1)의3개 Warning이 수정됐음을 확인했다. 기존 검수 문서와 trial 기록은 보존했다. producer·trial을 검수자가 실행하지 않았다.

## 해결 확인

- [analyze_palm_thumb_support_v1.py:27](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:27): 직접 읽는 각run `inputs_after.json`을 실행 전 SHA 입력 목록에 포함한다.
- [analyze_palm_thumb_support_v1.py:99](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:99): 접촉 시각을 `[a,z)`로 분기해 t0을 포함하고 `stairs(fraction,bins)`가 실제0.25초 경계에 맞춰 비율을 표시한다.
- [analyze_palm_thumb_support_v1.py:38](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_thumb_support_v1.py:38): native 입력 보존 실패 run을 분석 시작 시 제외하며 마지막 체크에도 입력 불변성을 포함한다(118).
- extrema 범위를30Hz pose/60Hz contact 표본으로 명시한다(86).

## baseline_v3 사용 제한

[baseline_v3/data/report.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline_v3/data/report.json:1)은 물리1200step·151frame·5초와 native 검사 통과를 기록한다. 그러나 [baseline_v3/inputs_after.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/palm_thumb_support_v1/baseline_v3/inputs_after.json:1)은 input_count1260, `inputs_unchanged=false`, 변경1개(`analyze_palm_thumb_support_v1.py`)를 기록한다. 따라서 물리/영상 완료와 입력 보존 통과를 구별해야 한다. 실제 runner에서 실행하지 않은 analyzer의 보수적 전체A SHA 변경도 그 실행의 guard 실패 기록을 없애지 않는다.

현재 분석기는 `baseline_v4/candidate_off/candidate_on`만 비교하도록 변경됐으며 guard 실패 baseline_v3은 정식 비교/Fret gate 입력에 포함하지 않는다. 재실행 결과의 완료·입력 SHA 통과는 최종 검수에서 별도 확인한다.

Critical/Warning/Suggestion: 현재 확인된 항목 없음.
