# 실행 상태와 이어받기

2026-10-18 사용자 요청으로 손별 실제 학습·분석을 진행한다. 이전 specialist 구조 구현은 완료됐으며 이번에는 새 초기화에서 단독 학습한다. 근거 계획은 `docs/plans/guitar_learning_specialist_training_20261018.md`이고 실행 전 사본·SHA를 `source_run_v1/manifest.json`에 보존했다. 원 계획·소비 소스·설정·실행 원자료는 수정하지 않는다.

## 실행 종료

- `left_run_v1`, `right_run_v1`: 각각4환경/H128/GPU medium, seed7, 최대64update/soft1800초. 전체 native worker8개. 실행기 `guitar_learning.train_specialists`.
- 현재 예산은 각 약30분이며 배치 경계에서 정상 종료한다. code/model/pose/gain/reward 정의·2초 준비·240Hz 안정성 검사 변경 없음.
- `inspect_live_v1.py`는 열려 있는 gzip의 읽을 수 있는 prefix만 요약한다. 미완료 rollout을 포함하므로 committed 통계로 쓰지 않는다. 실제 committed 수는 `update_*.json`의 합이다.
- 최종 LH28update/14336전이/160완료episode, RH29update/14848전이/168완료episode. 둘 다 wall_budget 정상 종료·final.pt·persistent 감사 통과. 단계 성공·목표 접촉 획득/유지·유효 기하 타현·물리 실패 모두0. 전이 폐기0.
- LH onset 직전 거리20.938949→19.841487mm, RH sweep55.169923→55.325716mm. 두 값 모두 기하 대리 지표다. LH의 작은 접근 개선이 실제 압현 성공으로 이어지지 않았다.
- run별4worker RSS는 약2.448GiB에서 안정적이었다. 전체 host 최소여유23.411205GiB. 총336준비 상태/8worker lifecycle·종료 검사 통과.
- 최종 해석·모델·원자료·권장 그림은 [결과 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_specialist_training_v1/README.md)를 따른다. 원 leaf 계획과 실행 전 SHA70개는 보존하고 이 파일에서 체크리스트를 갱신한다.

## 파일 소유권

- root: 실행·실시간 점검·초기 상태 진단·도표·README·최종 감사/봉인·main 문서.
- specialist_learning_analysis: `analyze_learning_v*.py`, `learning_analysis_v1.json`, `learning_verification_v1.json`, `learning_progress.md`.
- specialist_runtime_analysis: `analyze_runtime_v1.py`, `runtime_analysis_v1.json`, `runtime_verification_v1.json`, `runtime_progress.md`.
- change-reviewer: 검수 때 `review.md`만 작성.

## 남은 순서

- [x] 입력·소스·계획 보존과 두 학습 시작.
- [x] 두 학습 정상 종료·final checkpoint·canonical report·persistent audit 확인.
- [x] 학습/자원/준비 상태 분석. 완료 episode·부분 rollout·초반/후반 수치를 구분한다.
- [x] 원자료 도표와 한국어 결과·다음 권고 정리.
- [x] 별도 검수·source_final·artifact_inventory·final_verification. 독립 원자료 재계산·문서/그림 대조에서 미해결 지적 없음. 최종 봉인 파일을 기준으로 입력·소스·산출물 보존을 확인한다.

최종 봉인 실행기는 `seal_results_v2.py`다. v1은 자원 검증 JSON에도 학습 검증과 같은 `completed` 필드가 있다고 가정해 KeyError로 출력 생성 전에 중단했다. 원본 v1을 보존하고 v2에서 자원 보고서의 실제 입력보존·분석무결성·분리PID·양쪽 finalization 필드를 명시적으로 검사한다. 학습·분석 원자료는 변경하지 않았다.

성공 전문가가 확인되기 전 결합 학습은 시작하지 않는다. 목표거리 감소·native 접촉 후보·기하 타현·통합 음악·실제 음향을 구분한다. `validate.py`는 새 specialist checkpoint 영상 평가를 지원하지 않는다.
