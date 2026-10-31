# large 모델 GPU 병렬 학습 실측

사용자 요청: 현재 왼손 학습에서 large 모델의 환경 수를 GPU 기준으로 시험한다. 정책 추론·PPO는 CUDA, 물리는 현재 구현의 CPU PhysX를 유지한다. 앞선 CPU 결과는 별도 원자료로 보존한다.

같은 곡·왼손 512상태·유연한 LH21·large·seed 7·H1969/PPO 1회를 2→4→8환경 순서로 실행한다. 전곡 수집·GPU 갱신·저장·가용 RAM/VRAM·물리/입력 감사를 검증한다. 각 후보가 정상 종료하고 RAM 6GiB·GPU 여유 2GiB 이상을 확보할 때 다음 후보로 늘린다. 검증한 후보의 처리율을 비교한 뒤, 선택한 8환경 저장 모델을 H256/PPO 2회로 재개해 복원과 반복 갱신을 확인한다.

- [x] GPU 접근 제약과 실제 장치 상태 확인, 소스 410개 SHA 보존
- [x] RTX4070Ti에서 실제 CUDA 텐서 연산 검증, `--device cuda:0` 명시
- [x] 2환경 전곡·PPO·저장·입력/물리 감사 통과
- [x] 4환경 전곡·PPO·저장 통과: RAM 최소17.63GiB, GPU 여유 최소9637MiB
- [x] 8환경 전곡·PPO·저장 통과: RAM 최소15.91GiB, GPU 여유 최소7852MiB
- [x] 8환경 strict resume H256/PPO 2회 통과:4096전이·누적1→3갱신·metadata 외 payload 정확 일치
- [x] 결과 문서와 원자료 대조, 독립 change-reviewer 검수 통과
- [x] 소스/경로/실행 예의 실제 CLI 파서/아티팩트 SHA 검증 완료(verification.json)

GPU 전체 메모리는 약2초 `nvidia-smi` 표본, Torch 할당/예약은 부모 프로세스의 실제 peak 통계다. 소스·gain·접촉·물리 안전·PPO 계약은 변경하지 않았다. CPU fallback을 GPU 성공으로 보고하지 않는다. 16환경·100업데이트 장기 안정성·음악 수렴은 측정 범위에 포함하지 않는다.
