# 변경 파일

- 한국어 수치 요약, 한계, 재사용 native frame 및 향후 접촉 영역 설계 링크: [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/README.md:1).
- 분석 결과 JSON: [analysis.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/analysis.json:1).
- 저장 관절/접촉 요약을 만든 함수: [analyze_finger_curl.py의 main()](/home/ajou/yigyu/3/stability_adapter_2/analyze_finger_curl.py:7). 저장된 21개 scalar joint row 및 5개 distal body 접촉 row를 원자료에서 집계한다.
- 조사 범위와 미구현 접촉 영역 시각화 계획: [FINGER_CONTACT_REGION_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/FINGER_CONTACT_REGION_PLAN.md:1).
- 재사용한 직전 plus008 native 초기값: [initial_values.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/initial_values.json:1).
- 재사용 native hands frame: [시작 00000.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00000.png), [종료 00150.png](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/fixed_strap_shoulder_response_v1/plus008/frames/hands/00150.png).
- 분석 실행 기록: [analysis_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/analysis_execution.json:1), [analysis.log](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/finger_curl_diagnosis_v1/analysis.log:1).
- 메인 실험 기록: [stability_adapter_2/README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md:1023), [stability_adapter_2/PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1821), [누적 시각 보고서 §103](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1904).

## 확인

- 분석은 exit 0이며 4개 검사와 21개 일정 target, 5개 distal body 접촉 집계를 기록했다.
- 입력 SHA-256 before/after가 일치한다.
- 산출물 담당 작업은 문서 두 개를 추가했으며, root의 저장 자료 분석과 구분한다. 새 plot/native/actor/학습 실행은 없다.
