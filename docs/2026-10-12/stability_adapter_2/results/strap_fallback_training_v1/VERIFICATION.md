# 완료된 소단계의 검증 범위

[검증 기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/final_verification_v1.json)의 완료 범위 검사를 통과했다. 검증 생산자는 [verify_completed_phase_v1.py](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/verify_completed_phase_v1.py:1)이다.

- 두 조건 합계 실제 PPO 갱신 24회·학습 전이 6144개, 추가 최적화 없는 reset 진단 전이 300개.
- 완료 범위의 실제 물리 적분 46508회·장면 초기화 16회. 로드가 거절된 최초 probe v1의 장면 1개는 별도이며 물리 적분 0회다.
- 실제 실행 소스·모드별 입력 closure·reset 입력·초기 비교 입력·시각화 입력·6회 평가 영상 SHA-256을 대조했다. 메인 문서 기존 내용의 prefix 보존과 새 설명의 절대 링크·줄 번호를 확인했다.
- 실행 소스 6개를 `source_final_v1/`에 추가 복사했다. 실행 중인 원본 A 파일은 수정하지 않았다.
- [정적 결과 설명 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/review_v4.md)는 별도다. 이전 실행·산출물 검수 v1~v3도 보존한다.

이 검증은 **진행 중인 long_on_v1·long_off_v1, 이후 30분 평가, 정오 마감 결과를 포함하지 않는다.** 완료 범위 검사 통과는 안정화·연주 학습 성공을 의미하지 않으며 현재 음악 성공은 0회다.
