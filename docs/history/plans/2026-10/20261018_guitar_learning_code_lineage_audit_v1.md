# 기존 학습 코드 이식 경로 감사

요청: 기존 학습 코드를 현재 자유 기타 학습에 어떻게 가져왔는지 문서와 코드 위치로 정리한다.
전제: '기존'은 tab2body 고정 기타 구현과 stability_adapter_2의 이전 자유 기타/음악 초안을 함께 포함한다. 직접 import, 기록상 복사, 변경 이식, 현재 전용 구현, 미이식 기능을 구분한다. 코드 유사성만으로 역사적 출처를 단정하지 않는다. 환경·보상·모델·학습·기존 봉인 자료는 변경하지 않는다.

- [x] 현재 권장 실행부터 실제 환경·보상·정책·PPO·reset까지 호출 경로를 확인한다.
- [x] 기존 fret/strike·음악 코드와 현재 구현의 재사용·변경·누락을 대조한다.
- [x] 초기 자유 기타 복사 manifest와 native 장면/초기화/제어 의존성을 확인한다.
- [x] 코드 위치·판정 기준·보상 합·모델 이전을 통합 문서로 정리한다.
- [x] 별도 검수 및 근거 링크/SHA를 확인한다.

분담: legacy_music_v1.*는 skill_environment, native_provenance_v1.*는 persistent_reset_design. 메인 호출·망·PPO와 통합 문서는 root. 최종 검수는 change-reviewer.
산출물: guitar_learning/CODE_LINEAGE.md 및 docs/2026-10-12/stability_adapter_2/results/guitar_learning_code_lineage_audit_v1/.

완료: 통합 CODE_LINEAGE.md·음악/native 상세문서·코드AST/SHA·최신536 모델CPU집계·독립검수(미해결0). 환경/보상/모델/학습/기존결과 변경 없음.
