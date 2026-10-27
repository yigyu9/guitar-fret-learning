# 변경 파일과 저장 결과

이 단계는 아래 신규 source/trial로 세 조건을 준비·실행·분석했다. 사용한 실제 줄 위치는 `IMPLEMENTATION_FILES.md`를 참고한다. 기존 locality 단계는 변경 대상이 아니다.

| 경로 | 역할 |
|---|---|
| [prepare_seed2_feedback_trials.py](</home/ajou/yigyu/3/stability_adapter_2/prepare_seed2_feedback_trials.py:19>) | seed2 피드백 단계 준비와 입력 closure 기록 |
| [run_seed2_guitar_feedback.py](</home/ajou/yigyu/3/stability_adapter_2/run_seed2_guitar_feedback.py:18>) | 별도 trial을 실제 native 5초 실행 |
| [analyze_seed2_guitar_feedback.py](</home/ajou/yigyu/3/stability_adapter_2/analyze_seed2_guitar_feedback.py:26>) | 저장된 결과만 분석 |
| `stability_adapter_2/trials/seed2_guitar_feedback_v1/constant_0p008.json` | 상수 −0.008 rad 조건 |
| `stability_adapter_2/trials/seed2_guitar_feedback_v1/constant_0p016.json` | 상수 −0.016 rad 조건 |
| `stability_adapter_2/trials/seed2_guitar_feedback_v1/guitar_feedback.json` | actual guitar error feedback 조건 |
| 이 결과 디렉토리의 `execution.json`, `analysis.json`, `artifact_execution.json` 및 `artifacts/` | native 실행, 사후 분석, 두 PNG 산출물의 기록 |

신규 실행은 3 initialization/3600 physics step이다. 실제 보존 출력과 판정 한계는 [README](README.md), 수치 원자료는 [analysis.json](analysis.json), 생성물 SHA와 입력 closure는 [artifact manifest](artifacts/artifact_manifest.json)를 참조한다. 영상 인코딩·ffprobe 결과는 각 native 조건의 `videos.json`에 저장했다.

이번 시각 자료 단계는 canonical SHA `255da51545e975db05fb99ce91bd71b91d5695291f3ade75d04e5fad8479589c`의 producer를 소비했다. producer를 재실행하지 않았으며 plotting native call은 0이다. artifact 실행 메타데이터는 subprocess 성공 후 wrapper가 `--out-dir`를 producer 경로로 잘못 hash하려다 실패해 실제 elapsed time을 보존하지 못했다. 따라서 plotting 시간은 미측정으로 남겼다.

[메인 계획 § seed2 feedback](</home/ajou/yigyu/3/stability_adapter_2/PLAN.md:1430>)와 [프로젝트 README의 실행 요약](</home/ajou/yigyu/3/stability_adapter_2/README.md:787>)에 단계의 전체 진행이 기록됐다. 다음 미실행 leaf는 [SEED2_SUPPORT_POSE_WARMSTART_PLAN.md](</home/ajou/yigyu/3/stability_adapter_2/SEED2_SUPPORT_POSE_WARMSTART_PLAN.md>)다.

최종 감사 산출물은 작성 후 [final_verification.json](final_verification.json), [artifact_inventory.json](artifact_inventory.json), [source_final_manifest.json](source_final_manifest.json)에서 확인한다. 독립 검수 기록은 [review.md](review.md)에 추가될 예정이다.

`maintenance_attempt_v1/`은 이전 frozen phase 문서에 잘못 적용된 편집 시도와 root가 원본으로 복원했음을 기록하는 provenance다. 복원 시 원본 1005개 파일이 확인됐으며, 이 단계에서 그 보존 기록이나 이전 phase는 수정하지 않았다.
