# 검지→중지 원시 로그 분석

[보고서](REPORT.md)에서 원인별 수치와 다음 단독 실험3개를 읽는다. [사실/가설 구분](FINDINGS.md), [영상 시점 안내](VIDEO_GUIDE.md), [독립 검수](REVIEW_FINAL.md), [재현 명령](REPRODUCE.md)을 함께 남겼다.

이번 결론은 평균 B의 잘못된 위치 정착, 지원 한 축의 요청 탐색 압축, 128환경 반복 민감도다. 지원 축과 실패의 인과는 미검증이다. 새 학습이나 보상·제어 변경은 수행하지 않았고 기존/공유 코드는 그대로다.

- `runs/`: 같은 seed17/200회 모델의 mean32/128 각각3회 원문. 보상60Hz 원문은 각 실행 디렉토리의 sibling gz다.
- `tools/`, `tests/`, `logs/`: 관찰·분석 도구, 검사, 원문 실행/실패 기록. 파생 분석 초안의 오류 로그도 보존했다. 최종 성공 기록은 v4/final 접미 로그를 확인한다.
- `tables/`, `figures/`: 조건/축/보상/업데이트 표와 시간축 그래프9개.
- `analysis_ledger.json`, `learning_ledger.json`, `summary.json`: 소스 SHA와 비교 원장.
- `identity_integrity.json`: 원래13,943봉인 파일과756기존 artifact의 무변경 확인.
- `environment.json`: Python/Torch/Gym 설치 메타데이터와 실제 native cache launch SHA를 구분한 환경 기록.
- `trajectory_comparison.json`, `snapshots.json`, `saturation.json`, `potential_check.json`: 최초 차이·시점별 관절/기하·초기 포화·할인 정산 검산.
- `output_manifest.json`: 이번 분석 산출물 SHA. 원본 연구의 봉인 파일을 대신하거나 고치지 않는다.
