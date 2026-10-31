# 손가락 제어·압현 진단 로그

기본 GPU 왼손 학습에 관절21축·손가락5개 요약과 용량이 제한된 대표환경 상세 로그를 추가했다. 보상·제어·물리·종료 계산은 유지한다.

로그 항목·표본 주기·해석은 [LOGGING.md](/home/ajou/yigyu/3/guitar_learning/docs/LOGGING.md#손가락-제어압현-진단-2026-10-29-추가)를 따른다. 이전281개 Python과 문서2개 원문·SHA는 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261029_before_tracking_diagnostics_v1/manifest.json)에 있다.

## 검증

- 관련 CPU 검사72개 통과. 독립 검수의23개 검사도 통과.
- 실제 GPU large/8환경/H32 새20업데이트와 strict 재개2업데이트 완료.
- 새 실행은640제어 tick을 진행했지만 상세 로그는2400행에서 정확히 종료(약2.03MB). reset 전후 에피소드0/1을 모두 포함하며 gzip CRC와 JSON 복원 통과.
- 새 실행 종료 에피소드8개와 현재 부분 요약8개의 물리 표본 합20480개가 실제 실행량과 일치. 재개도2048개와 일치.
- GPU 검증 동안 활성281개 Python SHA 불변. 보관283개 원문 SHA 일치.

[기계 판독 검증 결과](verification.json) · [CPU 검사](cpu_related.log) · [독립 검수](REVIEW.md)

이 검증은 기록·저장·재개의 정상 작동을 확인하며 학습 성능 향상을 주장하지 않는다. 별도 옵션 없이 다음 새 학습부터 자동 기록한다. 과거 체크포인트의 소스 검증은 완화하지 않는다.
