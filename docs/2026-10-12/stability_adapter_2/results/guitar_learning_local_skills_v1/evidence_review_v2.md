# 오른손 완료 결과·최종 문서 증거 검수 v2

요약 판정: **문제없음**. RH finalized 정책 평가·gate·별도 PPO 준비 설정과 최종 README의 주요 사실이 일치한다. v1 기록은 해당 시점의 기록으로 보존했다. 이번에도 native·학습·PPO를 실행하지 않고 파일과 SHA를 읽어 검증했다.

- Critical: 없음.
- Warning: 없음.
- Suggestion: 없음. 검수 중 제안한 wrong 지표의 범위 구분은 README의 별도 문단에 반영된 것을 확인했다.

## RH 완료 결과

`right_policy_evaluation_v1/musical_quality_result.json`·`evaluation_metrics.json`·`local_skill_gate.json`·`right_gate_validation_v1.json`을 대조했다.

- 보조 제어 없는 결정적 정책 4/4가 valid/timeline_complete·420tick·7초이며, stage1 품질 성공·timing-only 성공 4/4, 물리 실패 0, safety_invalidated false다.
- 네 실행 모두 accepted 1, extra/unprepared/blocked 0, 최종 recovered true다. **손별 timing.wrong_crossings는 0이며, 원 music.wrong_crossings는 각 1이다.** 서로 다른 판정 이력이다.
- 인정된 타현의 오차는 첫 실행 +50.178669166ms, 나머지 세 실행 각각 +108.706247566ms다. 따라서 인정 타현 시각만 기준으로 50ms 이내 0/4·100ms 이내 1/4가 맞다.
- 실제 원 MusicLedger matched50/matched100은 네 실행 모두 0이다. stage1±0.5초 성공을 엄격 타이밍이나 양손 음악 성공으로 바꾸어 해석하지 않은 최종 README 설명이 맞다.
- RH 평가 모델 SHA는 `8dcd082a4b574699cbb8ece459487d46f7a438ac4e09e951d52e68509670239a`이며 BC report·실제 BC 파일·평가 지표·gate와 일치한다.
- gate의 세 artifact SHA, 전체 dataset manifest 및 평가 소비 입력 1658개의 현재 SHA가 모두 일치한다. 현재 신규 소스/검사/안내 11개 봉인도 변경 0이다.
- 별도 `right_bc_ppo_ready_settings_v1.json`은 평가 설정과 비교해 통과 gate 경로와 device CPU→CUDA만 추가/변경됐다. 현행 parser 및 `train.validate_gate`를 검수자가 직접 실행해 proof 4개 통과를 확인했다. native/PPO는 시작하지 않았다.

LH의 4/4·clean audible 1.0·해제 완료도 이전 검수와 일치한다. `release_late_s=0.179050`은 grace 이후 지연 적분량이며 0이 아니다. 최종 README는 이 한계와 RH 정밀 타이밍 한계를 구분해 기록한다.

## 기존 장기 실행과 새 PPO 구분

원 장기 실행의 `long_supervisor_v1/result.json`은 2026-10-19 02:48:10 KST 종료·7230.64초·interrupted false·양손 returncode 0이다. 각 hand의 report는 completed true·failure null·stopped wall_budget이다.

| 원 장기 실행 | 완료 episode | timing-only 성공 | 품질 성공 |
| --- | --- | --- | --- |
| LH | 384 | 378 | 0 |
| RH | 384 | 381 | 0 |

이 수치는 최종 README와 일치한다. 기존 확률적 PPO episode와 새 BC 정책의 동일 단음·동일 시작 결정적 4회는 별도 실험이다. gate 검사 통과는 실제 새 PPO를 시작했다는 뜻이 아니며 새 PPO는 미실행이다. 두 음 확장이나 다른 초기 상태 일반화·양손 결합·음향·Root 자유 균형의 성공으로 확대하지 않는다.
