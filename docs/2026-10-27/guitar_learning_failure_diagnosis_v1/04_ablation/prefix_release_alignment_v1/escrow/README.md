# A 달성 보너스 유보: 지정 시간표의 CPU 산술

원 production ledger와 지정 candidate/wrong 시간표를 재사용한 산술이다. 실제 물리·학습 결과가 아니다. 기존 A의 달성 지급 .25b만 유보해 유효 release를 관측한 control이 실패하지 않았을 때 한 번 지급한다. 이 표의 b=1이다. 보너스를 새로 추가하지 않고 기존 song_left_success 안의 지급 시점·조건만 비교한다.

| 지정 시간표 | 원 A 지급 | 유보 후 A 지급 | B7/B8 지급(원=새) | 원 핵심5항 합 | 새 합 |
|---|---:|---:|---|---:|---:|
| 세 음 clean·A 적시해제 |.25|.25|.25/.25|4.5000038743|4.5000038743|
| 같은 clean/wrong·A candidate 유지 |.25|0|.25/.25|4.5000038743|4.2500038743|
| A clean·B wrong·A 미해제 |.25|0|0/0|1.0008109087|.7508109087|
| A wrong·B clean |0|0|.25/.25|2.7515993938|2.7515993938|

첫 두 시간표의 원5항은 **매 control exact 동일**하지만 유보 조건에서는 적시해제만 .25를 받는다. 원 A 달성 지급은 control185(3.083333s), 적시해제 시간표의 새 지급은 control191(3.183333s)이다. 원 A source end=5.62s, offset=2.4497s라 local end=3.1703s이고 원 release 마감은 local3.2703s다. 적시해제 행은 control185~190 동안 pending, 미해제 행은185~196 동안 pending 후197에 expired가 된다. 원base 지급·새pending/paid/forfeited를 [results.json](results.json)에 별도로 남겼으며 원ledger는 수정하지 않았다.

나머지4항과 B7/B8의 지급은 tick-exact다. B7/B8 공유press 사이 해제를 새로 요구하지 않는다. 새 총예산은 원예산을 넘지 않고 A를 건너뛰면 A 지급도0이다. 원 achieved/music/release 판정 및90% 음악·해제 기준은 바뀌지 않았다. 유효 release가 있더라도 그 control에 실패가 있으면 미지급 소멸하며, 이미 paid인 뒤의 미래 실패는 취소하지 않는다. 안전종료까지 지급을 더 미루는 조건은 없다.

CPU 경계 검사는 미달성, end 전/포함 경계/마감 포함/마감 뒤, 미래 timestamp, 같은 control 달성·해제 및 실패, failure latch, 종료, 반복 지급, 부분reset의 행별 소멸, 60Hz H32 경계의 상태 유지, .25b 예산을 포함한다. reset은 pending을 새 episode로 넘기지 않는다. 같은 native falling-edge 규칙의 짧은 이탈을 사용하므로 안정된 무접촉·피부 전체 분리를 인증하지 않는다. release가 학습으로 개선될지, 간접 다음음 보상보다 유리할지, 보상만이 병목인지 이번 산술로 결정하지 않는다.

원 audit.main은 원문 그대로 실행했고 결과 파일 쓰기만 메모리로 받았다. 원 결과의 모든 산술은 exact이며, 입력 SHA map은 같은 audit.py의 상대/절대 경로 표기만 정규화해 exact 비교했다. 직접 입력 SHA만 검증했고 과거 전체 재귀 감사는 하지 않았다. 처음 import 경로 오류와 SHA 경로 표기 비교 중단 기록은 failed_cpu_*.log에 남겼다. H32 검사의 시간 간격을 실제60Hz/32control 경계로 고친 전후 source/첫 결과도 별도 보존했다. 원 source/raw/결과·GPU/native/fit/PPO 변경은0이다.

## 후속 구현 시 최소 연결 지점: 제안만

현재 `05_verified_fixes/low_effort_index_prefix_learning_v1/learning.py:PrefixLearningEnvironment`의 작은 새 subclass를 `LearningPool.environment_class_override`로 연결하는 경로가 가장 작다. 실제 보상 변경 지점은 `guitar_learning/gpu/simplified_finger_environment.py:SimplifiedFingerEnvironment._reward_components`다. 여기는 원 `TensorSongEnvironment.end_control`이 같은 control의 positive 실패차단을 적용한 뒤 호출하고, 이후 이9항으로 step.reward·episode_reward_terms·reward_window·total_reward를 함께 누적한다. 따라서 원9항 객체에서 **song_left_success 한 항만** base_A_due를 빼고 escrow_paid를 더하면 별도 step.reward 사후수정이나 compact 원장 보정이 필요하지 않다. Pool.step 이후 reward만 바꾸는 방식은 원장과 어긋난다.

원 `begin_control`에서 A의 이전 left latch를 보존하고, `_reward_components`에서 이번 A달성/유효 release_s/원 control failure를 읽어 계산하는 작은 수명주기 연결이 필요하다. A base due는 해당 control의 새 달성에 원 .25×finger_weight를 적용한 뒤 원 실패차단과 일치시켜야 한다. `note['left']`는 달성 원장으로 그대로 두며 actual payment가 아니다. base_success_paid·escrow pending/paid/expired/failed를 별도로 기록하고 실제9항에는 escrow paid만 넣어 의미를 구분한다. 원 `reset(indices,snapshot)`과 같은 선택행만 초기화하며 H32 수집 경계에서는 초기화하지 않는다. B7/B8 지급과 다른8항은 원문을 유지한다. 이는 위치 제안일 뿐 구현하지 않았다. 새 reward/procedure 계약을 policy 생성 전에 명시해야 하며 기존 strict 모델을 다른 보상 계약으로 재개하는 안은 사용하지 않는다.

실행: `CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B .../escrow/audit.py` — 기존 results.json이 있으면 거부한다.
