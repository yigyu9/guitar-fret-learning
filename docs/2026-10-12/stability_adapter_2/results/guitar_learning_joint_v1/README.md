# 양손 공동 모드 구현과 실제 실행 검증

현재 코드: `/home/ajou/yigyu/3/guitar_learning/joint/`. 기존 single-hand 코드·모델·성공/실패 기록은 수정하지 않았다. `source_pins_v2.json`과 `source_snapshot_v2/`가 이번 실제 성공 실행에 사용한 신규 코드20개를 보존한다. v1은 최초 실패 실행용 코드다.

## 구현한 것

1. 하나의 자유 기타 환경에 왼손33+오른손6 목표를 동시에 제출한다. 60Hz 한 tick에 물리는240Hz 네 번 진행하고 같은 표본으로 양손 ledger를 갱신한다.
2. 각 손의 기존563 관측·토큰·스케일·계약·품질 이력을 보존한다. 공동 이력6을 추가해 Actor 입력569씩, 중앙 reward/cost Critic 입력1132, 출력39로 구성했다. 총3,113,808 파라미터(actor1,982,798/value1,131,010)다.
3. 검증된 BC Actor와 해당 std만 명시적으로 이전한다. 새6열은0이고 공동 Critic/Adam/PPO update는 새로 시작한다. 별도 출력 합성망은 없으며 두 Actor를 공동 PPO로 업데이트한다.
4. 원 손별 품질·완화 timing·엄격 MusicLedger50/100ms·물리 안전과 공동 성공을 구분한다. 타현 순간 목표현/방향/시간창/note종료 이전 및 압현 양끝 clean을 검증한다. 공유 비용과 action-change는 한 번만 적용하고 실패tick의 양성 보상은 억제한다.
5. 고정 전문가 실행, strict PPO 평가, fresh PPO와 strict resume, streaming240Hz 측정/60Hz native pose 원자료, 자원 감시, persistent reset/종료 감사, 체크포인트와 요약을 연결했다.

물리 조건은 Root 고정·하체 유한 제어·105/97/8·자유 기타·중력ON·스트랩OFF다. 하체는 기존 유지 제어를 사용하며 정책의 학습 출력은39개 손/팔 채널이다. 별도의 Root 자유 균형·보행이나 실제 현 압력·진동·음향을 검증한 것이 아니다. 가슴 접촉 지속은 필수 성공조건이 아니다.

## 검증

- CPU34개 통과: `cpu_tests_v2.log`. 실제 factory/reset API 회귀 검사 포함.
- 독립 코드 검수: `review_v2.md`. 추가 blocking 사항 없음.
- 원169/6/15/11개 source/evidence 묶음은 `prior_inputs_audit_v1.json`에서 변경0으로 확인했다. 최종 감사는 `final_inputs_audit_v1.json`을 확인한다.

| 실제 실행 | 안전7초 완주 | LH 품질 | RH 품질 | 협응 | 전체 공동 |
|---|---:|---:|---:|---:|---:|
| 고정 두 전문가, deterministic |1/1|1/1|0/1|0/1|0/1|
| PPO 첫 rollout, stochastic |2/2|2/2|0/2|0/2|0/2|
| 저장된 PPO strict 평가, deterministic |1/1|1/1|0/1|0/1|0/1|

고정 실행은 `fixed_experts_evaluation_v2/result.json`과 `preflight_gate.json`에 있다. 물리 실패0, 금지 API0, 원gain·속성 유지, 소비 입력 불변, cleanup 오류0, 70.743초 wall이었다. LH clean audible은 목표 구간 전체를 유지했다. RH는 준비와 타현 후 복귀는 달성했지만 accepted crossing이 약6.47653초에 발생해 목표4.12초보다2.35653초 늦었다. 이때 clean 압현도 없어 협응 보상이 지급되지 않았다. 목표현 accepted1개와 다른현 native-eligible2개가 기록됐고 원 MusicLedger50/100ms는 모두0/1이다. 개별4/4 전문가 성공을 공동 성공으로 상속하지 않는다.

공동 PPO는 `ppo_smoke_v1/report.json`, `joint_report.json`, `episodes.jsonl`에 있다. 2환경×420전이=840개를 sampled/logged/durable/committed 모두 일치하게 기록했고 discarded0, 실제 optimizer update1회, 정상 종료했다. checkpoint는 `ppo_smoke_v1/final.pt`다. 두 episode 모두7초완주했고 물리 실패0, guard/physical flag/input 오류0, persistent 감사도 통과했다. 원50/100ms는0/2다. 두 episode는 업데이트 전 수집분이다. 이 시험은 학습 연결 검증이며 성공률 향상이나 수렴을 입증하지 않는다.

저장된 모델을 strict PPO 방식으로 다시 읽은 `ppo_evaluation_v1`도7초를 안전하게 완주했다. 소비 입력 불변·원물리조건·금지API0·cleanup 오류0을 확인했다. LH1/RH0/협응0/공동0으로 이번 업데이트 뒤에도 공동 성공은 없었다. 별도 검수에서 initial→final의 양손 Actor, 양쪽 log_std, Critic 및 Adam 상태의 실제 변경을 확인했다. 학습·저장·불러오기 경로가 작동한다는 근거이며 실력 향상의 근거는 아니다.

PPO 최초 actor_lr1e-5는 KL guard에서 두 번 재시도한 뒤6.25e-7에서 수락됐다. accepted analyticKL은0.0118585였고 max attemptedKL은0.405391이었다. 실패 시 Actor/Adam을 복원하는 기존 guard가 동작했다. 긴 fresh 실행 설정에는 관찰된 수락 학습률6.25e-7을 사용했다. 이 값의 장기 성능은 아직 검증하지 않았다.

## 실행 설정과 기록

- `fixed_experts_settings_v1.json`: 두 기존 BC의 설정·원4회 native 평가·dataset/교사·모든 소비 입력 SHA를 검증한다.
- `ppo_smoke_settings_v1.json`: 실제 검증한2환경/horizon420/update1/maxwall900초. safe preflight1회 근거를 명시한다.
- `joint_training_settings_v1.json`: fresh 장기 실행용16환경/horizon120/update256/maxwall7200초/actor_lr6.25e-7. 환경 수는 이전 single-hand 설정을 이어받았으며 이번 공동 모드에서16환경 처리량·장기 성능을 따로 비교한 결과는 아니다. 이번에 긴 실행은 시작하지 않았다.

프로젝트 루트에서 새 출력 경로로 실행한다.

```bash
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:$LD_LIBRARY_PATH
/home/ajou/miniconda3/envs/rl38/bin/python -m guitar_learning.joint.train \
  --settings docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/joint_training_settings_v1.json \
  --out docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/joint_long_v1
```

기존 checkpoint 재개는 원 PPO config와 계약이 정확히 같은 설정으로 `--resume /절대경로/final.pt`를 지정한다. 이번 smoke checkpoint를 재개할 때는 `ppo_smoke_settings_v1.json`을 복사해 updates/시간 등 실행 길이만 조절한다. Actor 학습률을 바꾼 장기 fresh 설정을 smoke의 strict resume에 사용하면 거부되는 것이 정상이다. 원 checkpoint Adam에는 KL guard로 조절된 학습률도 저장된다.

학습은10초 주기 터미널 heartbeat와 `status.json`, `resources.jsonl`, `events.jsonl`, `learning_metrics.jsonl`, `training_summary.json`, `episodes.jsonl`, `transitions.jsonl.gz`, update JSON, `report.json`, `joint_report.json`, `persistent_audit.json`, `initial.pt`, `final.pt`를 남긴다. sampled/logged/durable/committed를 구분한다. 전체 nested 손별/협응 증거는 `episodes.jsonl`에 보존하고 요약에는 원 파일 경로·SHA를 기록한다.

평가는 `python -m guitar_learning.joint.evaluate --settings ... --out 새경로 --episodes 1`이며 joint PPO 모델이면 `--run 학습디렉토리`를 추가한다. 평가 원자료는 `transitions.jsonl.gz`의 한 줄당60Hz 전이,240Hz 네 측정 표본, 마지막 실제 native body pose다. 평가에서 교사/후처리/보조 힘은 사용하지 않는다. 시작8GiB/실행중6GiB 메모리 보호, case600초/전체3000초 제한이다.

## 실패 보존과 남은 과제

`fixed_experts_evaluation_v1`은 일반 HeadlessPreparedSession을 persistent 환경에 잘못 공급해 reset에서 실패한 기록이다. 음악/물리 성공 표본에 포함하지 않는다. 이전 구현·검사는 `guitar_learning/archive/20261019_before_joint_persistent_session_fix/` 및 source_snapshot_v1에 보존하고 두 진입점을 PersistentHeadlessPreparedSession으로 수정했다. 회귀 검사는 실제 공급 factory의 identity와 reset_episode 존재를 확인한다.

구현 및 짧은 실제 학습 검증과 공동 연주 숙련은 별개다. 다음 연구 과제는 먼저 이 한 음에서 RH 타이밍·다른현 오류를 줄이고 LH clean 압현과 타현을 겹치게 만드는 것이다. 이후 반복 평가로 공동 성공을 확인한 뒤 음/시간창/곡 범위를 넓힌다. 현재 여러 음·전곡 일반화·장기 수렴을 확인하지 않았다.
