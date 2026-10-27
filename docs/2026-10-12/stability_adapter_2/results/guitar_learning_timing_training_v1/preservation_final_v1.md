# Timing 학습 최종 보존 감사

**통과했습니다.**

4개 학습 실행과 8개 결정적 평가의 소비 입력, 이전 phase의 봉인 자료, native 종료 및 모델 실제 counter를 확인했습니다. 시뮬레이터 실행·학습·기존 source/결과 수정은 수행하지 않았습니다.

| 검사 | 수 | 결과 |
|---|---:|---|
| previous seal manifest anchors | 6 | 일치 |
| previous consumed inputs | 1658 | 일치 |
| previous original source bytes | 125 | 일치 |
| previous immutable artifacts | 348 | 일치 |
| previous source snapshot copies | 125 | 일치 |
| previous archived bytes | 112 | 일치 |
| consumed inputs left_stage0_final_eval_v1 | 1602 | 일치 |
| consumed inputs left_stage0_update12_eval_v1 | 1602 | 일치 |
| consumed inputs left_stage0_v1 | 1634 | 일치 |
| consumed inputs left_stage1_final_eval_v1 | 1602 | 일치 |
| consumed inputs left_stage1_preflight_eval_v1 | 1602 | 일치 |
| consumed inputs left_stage1_v1 | 1634 | 일치 |
| consumed inputs right_stage0_final_eval_v1 | 1602 | 일치 |
| consumed inputs right_stage0_update12_eval_v1 | 1602 | 일치 |
| consumed inputs right_stage0_v1 | 1634 | 일치 |
| consumed inputs right_stage1_final_eval_v1 | 1602 | 일치 |
| consumed inputs right_stage1_preflight_eval_v1 | 1602 | 일치 |
| consumed inputs right_stage1_v1 | 1634 | 일치 |

소비 입력 manifest 12개, 입력 참조 19352개, 보존 경로를 반영한 합집합 1650개를 확인했습니다. SHA 충돌 0개, 읽는 동안 변한 고정 파일 0개입니다.

## 문서 갱신과 이전 bytes 보존

승인된 living Markdown 6개는 기존 문서와 새 문서를 구분했습니다. 각각의 before SHA가 보관본과 일치하고 현재 SHA가 documentation_update의 after SHA와 일치합니다. 과거 입력 pin에서 이 문서들을 참조하는 경우 before bytes 보관 경로로 해석했으며, 기타 source·기존 결과의 변경을 허용하지 않았습니다.

- [PLAN.md](/home/ajou/yigyu/3/stability_adapter_2/PLAN.md) → [before 보관본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/main_documents_before/stability_adapter_2/PLAN.md)
- [README.md](/home/ajou/yigyu/3/stability_adapter_2/README.md) → [before 보관본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/main_documents_before/stability_adapter_2/README.md)
- [README.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/README.md) → [before 보관본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/main_documents_before/docs/2026-10-12/stability_adapter_2/README.md)
- [VISUAL_REPORT.md](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md) → [before 보관본](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/main_documents_before/docs/2026-10-12/stability_adapter_2/VISUAL_REPORT.md)
- [README.md](/home/ajou/yigyu/3/guitar_learning/README.md) → [before 보관본](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_timing_training/README.md)
- [TIMING_TRAINING.md](/home/ajou/yigyu/3/guitar_learning/TIMING_TRAINING.md) → [before 보관본](/home/ajou/yigyu/3/guitar_learning/archive/20261018_before_timing_training/TIMING_TRAINING.md)

## Native 종료와 단계별 counter

Native scene 16개가 각각 한 번 생성·종료됐고, 에피소드 reset 168회의 동일 scene/controller/FK 재사용·물성 보존·상태 readback을 확인했습니다. 금지 호출은 0회이며 실제 simulator 시각 합으로 확인한 물리 step은 272,640개입니다. 이는 숨겨진 PhysX solver cache 복원이나 접촉·음향 성공의 추가 인증을 뜻하지 않습니다.

| 손 | stage0 final 실제 update | stage1 initial 실제 update | stage1 final 실제 update | 설명용 계보 update |
|---|---:|---:|---:|---:|
| 왼손 | 24 | 0 | 12 | 36 |
| 오른손 | 24 | 0 | 12 | 36 |

모델 index 10개의 SHA·손·536차원·stage·실제 checkpoint counter를 확인했습니다. stage1은 stage0 최종 actor/std를 정확히 가져오고, critic은 같은 seed의 신규 초기값과 같으며 optimizer state는 비어 있었습니다. 계보 36은 이번 phase의 stage0 24＋stage1 12 합계이며, BC fit step이나 이전 실험 전체의 학습 계보를 합산한 값이 아닙니다. stage1 checkpoint 자체의 counter는 12입니다.

## 현재 source snapshot

Source·현재 문서·분석 producer/configuration 143개를 원경로 구조와 SHA로 복사했습니다. Root가 마지막 감사 링크와 완료 체크를 추가할 이번 phase README 및 새 작업 계획은 snapshot에서 제외했습니다. 해당 두 문서의 최종 bytes와 전체 artifact inventory/seal은 root가 마지막으로 기록합니다.

[상세 보존 감사 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/preservation_final_v1.json) · [Source manifest](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/source_final_v1.json)
