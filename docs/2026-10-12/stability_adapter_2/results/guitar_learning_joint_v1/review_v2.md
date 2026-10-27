# 독립 변경 검수 기록

change-reviewer가 joint 신규 코드와 관련 검사를 읽고 CPU 검사를 독립 실행했다. 최초 검수에서 협응 집계와 전체 episode 재적재 문제가 보고되어 `coordination.stage_success` 집계 및 streaming counter 요약으로 반영했다. 이후32개 CPU 검사는 통과했다.

첫 native 실행은 persistent 환경에 일반 HeadlessPreparedSession을 공급해 reset 전에 실패했다. 최초 mock 검사는 공급받은 factory를 실제로 사용하지 않아 이 계약 오류를 잡지 못했다. 실패 원자료는 fixed_experts_evaluation_v1에 보존했다.

수정 검수에서는 evaluate/worker의 PersistentHeadlessPreparedSession 공급, 실제 `reset_episode(config,out)` API, 원 scene/target/integrate/close 및 nativeprep0 호환, episode 경계 reset와 안전/속성 검사를 확인했다. 해당 factory identity/callable 회귀 검사도 추가했다. 최종 검수 판정: 추가 Critical/Warning 없음, native 재시도 가능. 파일 변경은 root와 담당 worker만 수행했다.

이 문서는 코드 검수 기록이며 실제 native 성공이나 학습 수렴의 증거는 아니다. 실행 결과는 각 실행 result/report 원자료에서 별도 확인한다.
