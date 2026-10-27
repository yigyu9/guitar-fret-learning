# 기존 학습 코드 이식 경로 감사

사용자 요청에 따라 현재 권장 학습 진입점에서 기존 고정 기타·선행 자유 기타 구현까지 실제 호출, 복사 기록, 판정·보상·관측·모델·가중치 연결을 읽기 전용으로 점검했다. 생산 코드·기존 실행 원자료는 변경하지 않았으며 새 물리 실험/학습은0회다.

| 문서 | 내용 |
|---|---|
| [통합 문서](/home/ajou/yigyu/3/guitar_learning/CODE_LINEAGE.md) | 실제 학습/환경 경로, 부품별 계보, 미이식 기능, 최종 보상, 네트워크·PPO·모델 이전, 우선 읽을 코드 |
| [기존 fret/strike·음악 코드 비교](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/legacy_music_v1.md) | compiler 직접 재사용, detector 변경 구현, 기존 보상과 누락, 목표 projection·타현 준비·뮤팅의 차이 |
| [native·초기화·제어 계보](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/native_provenance_v1.md) | origin manifest15쌍·상속/우회·기존 생성자/자산 의존성·035/snapshot·하체/파지 제어 범위 |
| [코드 위치·모델 집계](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/code_map_v1.json) | AST 정의/import 줄번호·SHA, 최신 reset536 계약의 실제 CPU 모델 파라미터 수 |
| [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/review_v1.md) | 호출·보상·재사용 분류·파일/줄 링크·SHA·모델 집계 검수 |

직접 import, manifest로 확인한 복사, 소스상 adaptation, 동작 비교와 미이식을 구분했다. 코드 유사성만으로 정확한 작성·복사 이력을 단정하지 않았다. 문서/소스의 존재를 해당 기능의 실제 활성화나 물리·음향 성공으로 확대하지 않았다.
