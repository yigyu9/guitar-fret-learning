# 00_SS1-68-E_comp 35.28초 strike 입력 승인 기록

> **상태: IMMUTABLE INPUT-REVIEW RECORD.** 승인 당시 source와 plan hash에 대한 기록이며
> 다른 곡이나 재생성된 plan에 자동 적용하지 않는다.

## 승인 결과

35.26~35.34초의 low-E, high-e, B onset은 하나의 down strum/chord로 병합했다.

- decision: `merge_as_single_down_strum`
- status: `approved_user_delegated`
- authority: `user_delegated_to_codex`
- source event IDs: `147, 148, 149`
- manual audio review: `not_performed`

사용자가 판단을 위임했으며, source JAMS와 symbolic mapping의 일치 및 기존 분리 plan의 물리적
불가능성을 근거로 승인했다. 사람이 오디오를 직접 청취했다는 뜻은 아니다.

## 승인 근거

| 입력 | 세 onset (s) | span |
|---|---|---:|
| derived fingering | 35.2595, 35.2943, 35.3408 | 81.3 ms |
| source JAMS | 35.277968, 35.280145, 35.283048 | 5.08 ms |
| symbolic notes | 35.294118의 한 chord | 동시 |

승격 전 canonical plan은 앞 down strum이 high-e에서 끝난 지 `46.5 ms` 뒤 B현 up-pick을 요구했다.
최소 물리 계약은 `50 ms`였으며, 기존 전체곡 report에서 앞 strum이 성공한 22회 모두 다음 up-pick
전에 high-e를 재통과해 blocked가 발생했다. 이 경계는 별도 attack이 아니라 source annotation의
한 chord를 파생 fingering이 시간상 분리하면서 만들어진 것으로 판정했다.

## canonical 승격

후보를 2026-08-30 19:09:57 KST에 canonical로 원자 승격했다.

| canonical 파일 | schema / profile | SHA-256 |
|---|---|---|
| `training/strike_training.json` | raw v3 | `4fa5659f5220eb28ade714842d98fa4a81d90d242e42c2a99acdb93f87cac096` |
| `training/strike_plan.json` | plan v4, direction v3 / transition v2 | `efab30028c60e1d2e9c412a6cb36ad1cd84154996b1d1a39c4fe5483bb9ee85f` |
| `training/strike_review.json` | approved review v1 | `67fe86945199c63cd5135d38ba24631ea02ffff531c6b7aebf82fc20992dcc5f` |

승격 전 정본·후보·promotion record는
`data/song_bundles/00_SS1-68-E_comp/training/history/20260830_user_delegated_strum_merge/`에
보존했다. 현재 plan은 실행 event `104`, single `61`, strum `43`, 최소 실제 edge gap `51.0 ms`,
`INFEASIBLE=0`이다.

## 승격 후 검증

- 전체 strict audit: exit `0`
- 전체 8개 bundle: `PASS 2 / AMBIGUOUS 6 / INFEASIBLE 0`
- `00_SS1-68-E_comp`: 승인 override가 적용됐고 물리적 infeasible 경계는 제거됨
- 남은 상태: 다른 source 정렬·grouping·provenance 경고 때문에 곡 단위 결과는 `AMBIGUOUS`
- original-tempo full-song preflight: 통과
- manifest의 canonical strike 입력: ready

따라서 이 곡은 현재 canonical 입력으로 fresh A0 학습을 시작할 수 있다. 다만 observation이 327D로
변경된 새 계약이므로 v12 이하 checkpoint는 resume이나 `--initialize-from` actor 전이에 사용하지
않는다. 남은 `AMBIGUOUS` 항목은 학습 금지 사유는 아니지만 이후 데이터 검수 대상으로 유지한다.
