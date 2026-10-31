# 전곡 보상 개선과 추가 학습

사용자 요청: 확인한 보상 문제를 개선하고 더 길게 학습한다. 기존 source/학습/실패/검증자료는 보존하고 신규 song_reward_v2 경로에서만 구현한다. 입력500/미래4초/전체67음/1969tick/Actor규모/행동39/원물리안전·gain·비용은 유지한다.

- [x] 다음음준비기간의오압현벌점충돌제거: wrong을audible구간에서만부과,현곡의정당한유지와미래준비를충돌시키지않음.
- [x] RH누적거리보상제거: 같은목표에대한60Hz signed discounted preparation-potential progress만작게부여하고실제타현/협응보상과분리. 정지hover/진동farm/목표교체/artificialentry/failuretick회귀검사.
- [x] 원전곡final8 Actor/std명시warmstart+Critic/Adamfresh+입력불변확인; old reward checkpoint의strictresume완화금지. 모델이전은reward metadata만달라질수있고obs/task/action/safety는동일해야함.
- [x] CPU/독립검수/같은실제trajectory에서old/new보상대조(학습성과비교와구분),그후2환경/H256/24업데이트/최대3600초추가학습.
- [x] 로그/모델/음별성공/안전/실행범위/남은문제를문서화.

짧은대조는같은고정Actor·native표본에서V1/V2보상회계를나란히계산해설계수정이적용되는지검증한다. 그자체로학습효과의인과비교라주장하지않는다. 긴실험은원500전곡checkpoint의양Actor만이전하며oldoptimizer/critic/성과는계승하지않는다. 학습중fulltrajectory와최종고정정책평가도구분한다. 업데이트/시간은명시예산으로제한하고메모리8GiB시작/6GiB실행·기존실패종료·checkpoint보존을유지한다.

소유권: ledger담당metrics와해당tests;warmstart담당transfer/settings와tests;rootprogress/environment/worker/train/probe/문서/native실행. 기존파일수정금지,서로의편집보존.

CPU 신규34검사 통과(20.270초), 별도검수 Critical/Warning 없음. 소스·검사19파일 source_snapshot_v1/source_pins_v1로 봉인. 실제6초 보상대조 실행 중. 최종고정정책 evaluate wrapper도 봉인에 포함했다.

추가학습24업데이트/12,288전이전부반영/6fullsafe완주/약53.1분완료. 최종고정평가진행중. 원8update모델의고정전곡평가도별도완료(L1/R0/C0,fullsafeTrue).

최종고정평가완료: 기존/새모델모두L1/R0/C0,strict50/100=0/0,fullsafeTrue. 오타현1→2. 보상수정적용은확인했으나최종음악성과개선없음. 14개기존/신규manifest및snapshot SHA변경0. 결과README/analysis/audit/병목후보문서완료.
