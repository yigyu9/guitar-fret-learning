# 구현·실행·누적 기록 변경 파일 보완 색인

산출물 담당의 [변경 색인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/CHANGED_FILES.md:1)에 이번 phase의 물리 구현/실행 파일을 보완한다. 이전 실험과 소비된 원본 runner는 수정하지 않았다.

| 파일/실제 시작 줄 | 내용 |
|---|---|
| [COUPLED_PALM_WITNESS_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/COUPLED_PALM_WITNESS_PLAN.md:1) | 현재 feasible palm witness 우선 source 탐색 계획 |
| [search_coupled_palm_witness.py](/home/ajou/yigyu/3/stability_adapter_2/search_coupled_palm_witness.py:22) | 저장 실제 상태의18변수 source 검색; 새 physics 없음 |
| [PALM_WITNESS_INITIAL_TRIAL_PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_TRIAL_PLAN.md:1) | source 통과 초기각 한 후보의 실제5초 비교 계획 |
| [prepare_palm_witness_initial_trial.py](/home/ajou/yigyu/3/stability_adapter_2/prepare_palm_witness_initial_trial.py:23) | float32 초기18각/PD shift, held63·한계·source 검사와 입력 closure 준비 |
| [initial_witness.json](/home/ajou/yigyu/3/stability_adapter_2/trials/coupled_palm_witness_v1/initial_witness.json:1) | 새 실제 시험 초기 입력 |
| [run_palm_witness_initial_diagnostic.py](/home/ajou/yigyu/3/stability_adapter_2/run_palm_witness_initial_diagnostic.py:16) | 원본 runner의 초기 audit hook 확장; fresh native self1188쌍 gate |
| [analyze_palm_witness_initial.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_palm_witness_initial.py:15) | 원자료 coverage/목표/영상·기타/strap/접촉 비교16검사 |
| [collect_palm_witness_videos.py](/home/ajou/yigyu/3/stability_adapter_2/collect_palm_witness_videos.py:11) | 새 두 영상 exact 복사와 v5 목록 생성 |
| [PALM_WITNESS_INITIAL_DECISION.md](/home/ajou/yigyu/3/stability_adapter_2/PALM_WITNESS_INITIAL_DECISION.md:27) | 새 초기각 미채택, 기존−2mm 유지;39행 이후 학습 후속 순서 |
| [main README](/home/ajou/yigyu/3/stability_adapter_2/README.md:976) · [main PLAN](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1752) | 이전 내용 보존 후 이번 실제 시험/학습 연결 기록 추가 |
| [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md:1824) | §99의 실제0/5초 이미지·영상과 설명 추가 |
| [VIDEO_INDEX_v5.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VIDEO_INDEX_v5.md:1) | 기존126개 보존+새2개 영상;총128 |
| [ROOT_VERIFICATION_NOTES.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/ROOT_VERIFICATION_NOTES.md:1) | 실제PNG/그림 QA, 단위/제어/원본복구 한계 기록 |

`search/preparation/native/analysis/collection`의 source·wrapper·log·execution JSON은 이 결과 폴더에 보존한다. 최종 SHA 감사와 source_final snapshot은 root가 별도 생성하며 [final_verification.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/coupled_palm_witness_v1/final_verification.json:1)에 통합 결과를 저장한다.

기존 [학습 평가 계획](/home/ajou/yigyu/3/stability_adapter_2/PLAYING_RESIDUAL_EVALUATION.md:17)은 이번 실행에서 수정하지 않았으며 다음 연결 단계의 기준으로 인용한다.
