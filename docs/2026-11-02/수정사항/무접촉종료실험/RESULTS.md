# 무접촉 종료 실험 결과

단계: complete

신규 무접촉 종료를 해제한 전곡128환경 평가. 원래 물리·손목 종료는 유지한다.

| 조건 | seed | 달성 음/67 | 물리 종료 | 손목 종료 | 학습 무접촉 종료 비율 |
| --- | ---: | ---: | ---: | ---: | ---: |
| baseline_s7 | 7 | 6.547 | 0 | 0 | 0.0% |
| no_contact5_s7 | 7 | 2.742 | 0 | 79 | 75.6% |
| no_contact3_s7 | 7 | 9.758 | 0 | 0 | 93.6% |
| baseline_s17 | 17 | 6.086 | 0 | 0 | 0.0% |
| no_contact3_s17 | 17 | 6.547 | 1 | 3 | 93.7% |

선별/재현 결과: {"threshold": 3, "confirmed": false, "reason": "not reproduced on second seed"}

기본 학습 설정은 변경하지 않는다. 두 seed의 단기 초기 선별이며 장기 수렴을 보장하지 않는다.


## 2026-10-31 저장 기록 정리

완료된 구형 비교 학습의 `train/J/episodes.jsonl`, `decisions.jsonl.gz`, `transitions.jsonl.gz` 15개(5.03GiB)를 정리했다. 최종·초기 모델, 중간 체크포인트, 평가 에피소드, `learning_metrics.jsonl`, 손가락 진단, 설정·계약, 기존 분석·그래프·영상은 보존했다. 실패 실행의 원시 로그도 보존했다. 삭제한 학습 원시 시점에 대한 새로운 상세 재분석은 불가능하며, 기존 요약과 체크포인트 평가는 가능하다. 정확한 삭제 목록·검증은 [정리 기록](/home/ajou/yigyu/3/docs/maintenance/project_cleanup_20261031/REPORT.md)을 따른다.
