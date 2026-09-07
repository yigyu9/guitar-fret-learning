# task_fret 체크리스트 — "왼손이 finger mapping대로 동작하는가"

> **상태: SUPERSEDED.** Fret-v1 계열의 과거 검증 기록이다. 현재 구조는 [`master_plan/03_fret.md`](../../master_plan/03_fret.md)를 따르며, 아래 완료 표시는 Fret-v2의 완료를 의미하지 않는다.

> 최종 갱신: 2026-09-01. 현재 실행 계약은 `30 action / 425 observation / 6 reward-value`다.
> 아래 2026-07-22 측정값과 완료 표시는 당시 `341 observation` 구현에 대한 역사 기록이며,
> 현재 계약 확인에는 [`tab2body/TRAINING.md`](../../tab2body/TRAINING.md)의 공용 smoke를 사용한다.

> 2026-07-22 당시 상태: 33 action / 341 observation / 6 reward-value 구현 완료. 당시 전체곡 평가는
> F1 0.598, 완주율 100%, 안전 종료 0회였으며 정확도와 sustain 게이트는 미통과였다.

> 목적: 왼손이 fingermapping 출력(`presses`)에 맞게 **올바른 (줄·프렛)을 올바른 손가락으로, 올바른 시각에, 관통·역꺾임 없이** 누르도록 만드는 데 필요한 전 항목을 검증 가능 단위로 분해.
> 각 항목 = `[ ] 무엇` + **검증: 어떻게 확인** (실측 없이 완료 선언 금지, PROJECT_CONTEXT 규칙).
> 동반 문서: `docs/plans/task_fret_plan.md`(설계). 근거 태그: [G]=guitar/env.py, [P]=PROJECT_CONTEXT, [M]=실측.

---

## P0. 전제 (대부분 확인됨 — 착수 전 재확인만)

- [ ] base.py 3검증 PASS 유지 — **검증**: `verify_stability`와 공용 `python -m tab2body.train --task fret --smoke` 재실행.
- [ ] seated RSI 자세에서 왼손이 넥 근처, 관통 0 — **검증**: `render_pose.py` 4뷰 + `isaac_contact_audit.py`.
- [ ] 지판 reach: 목표 프렛(1~12)이 굽힌 운지로 도달 — **검증**: 기존 34/36 결과, 단 가변 압점(P4-6) 반영 시 재측정.

## P1. Goal 파이프라인 — fingermapping `presses` → 제어 goal (가장 실수 잦음)

> 2026-07-19 데이터 파일럿: `build_fret_training_data.py`가 GuitarSet GT 한 곡을 60Hz로
> 래스터화했다. 아래 항목 중 파일 변환 수준의 줄 반전·인코딩·시간축은 검증했으며,
> `goals.py`와 Isaac 환경 연결, 60Hz 1-step=1-frame advance, PPO 배관까지 구현·스모크했다.
> `[x]`는 코드/shape/실행 검증 완료, `[~]`는 구현됐지만 물리 정답자세·장기 검증이 남은 항목이다.

- [x] **줄 인덱스 반전**: builder의 `goal_idx=5-s`, reward의 index0→`G:string1`/index5→`G:string6` 계약이 실제 GPU env에서 shape·실행 확인됨.
- [x] **인코딩 정합·fail-fast**: 길이 6 배열, 정수 `1..22=PRESS / 0=DONT_CARE / −1=NO_PRESS`,
  PRESS finger `1..4`를 loader와 reward가 동일하게 처리하며 23프렛·비정수·finger 불일치는 거부.
- [x] **초→프레임 래스터화**: 14.3182초→861프레임, physics 1 step마다 `advance()` 1회. frame index와
  60Hz timestamp는 0부터 연속이어야 하며 불일치 입력은 loader가 거부.
- [x] **룩어헤드**: 현재/0.1s/0.25s(0/6/15 frame)의 줄별 fret·finger·barre·hand target 75D와
  손가락별 next-goal 13D×4, 곡 진행률1을 함께 관측.
- [x] **S0 바레 차단**: 동일 손가락의 다중 줄 목표는 같은 fret이어도 fail-fast이며 현재 번들의 암묵
  다중 줄 frame은 105→0. 6줄 mask와 `allow_barre` 흔적만 후속 명시적 검지 바레 확장용으로 보존.
- [x] **명시 모드 피치 증강 OFF**: frame goal을 그대로 재생하며 pitch 조정 경로 없음.
- [ ] **진단 폴백**: `finger=None`/`t_cut` 구간은 [G] 암묵 윈도 마스크로 자동 폴백 — **검증**: 진단 있는 곡에서 폴백 경로 실행 로그.

## P2. 제어 DOF 구성

- [x] **control_dofs 재정의**: `L_Shoulder/Elbow/Wrist` 9 + 엄지5 + 네 손가락16 = **30 DOF**.
  actuator-state `prev_action30`, thumb geometry 12D와 미래 문맥 75D를 포함한 runtime 계약은
  `actions=30`, `obs=425`이다.
  `L_Thorax`·몸통·머리·우측·하체는 init PD target 고정.
- [~] **엄지 정책 제어·R6 지지 보상**: 엄지 5DOF action, tapered neck-back 기하,
  thumb3 실제 충돌+hysteresis, 접근30/접촉70, 전체 가중치5% 구현. CPU 기하검사·8-env GPU PPO smoke 통과.
  **남음**: 접촉 rollout로 0.5/0.1N 보정 및 지속 과이탈 종료 여부 결정.
- [~] **비제어 관절 유지**: 8환경×5 PPO update 정책의 14.37초 전체 rollout에서 뒤로 꺾이는
  누적 상체 붕괴는 관찰되지 않음. 몸통·머리 비제어 DOF 최대 2.25°/RMS 0.93°,
  우측 비제어 DOF 최대 1.32°/RMS 0.27°, early reset 0. **남음**: 충분히 학습된 정책의 장시간 검증.
- [x] **액션·reset 의미 공유**: Actor는 Jacobian 보정이 포함된 tanh-squashed bounded policy v1이며
  실행 action `[-1,1]`은 scale=1.0으로 hard range에 1:1 대응한다. base/FretTask는 EMA α=0.5를
  공유한다. reset noise 뒤 제어관절은 hard range 안쪽 2%에 clamp하고 `prev_action`은 reset PD
  target의 역변환으로 초기화한다. policy init std=.02.

## P3. 물리 정합 — 안전 (역꺾임·관통 절대 금지)

- [x] **손목 안전 박스 종료(R7)**: 손목 중심이 기타 로컬 고정 박스
  `min=(-.20,-.35,-.30)m`, `max=(.30,.35,.25)m` 밖에 3프레임 연속 있으면 종료.
  경계 자체는 안전 — **검증**: CPU 경계·연속 필터, 강제 GPU `done=True`, 정상 준비 자세 PASS.
- [x] **손바닥 반전 종료(R13)**: 손바닥 안쪽 법선의 world-z<−0.3이 3 제어 프레임 지속되면 종료.
  무효 법선은 streak 초기화, 원인은 info에 기록 — **검증**: CPU 경계·연속 필터 검사와 8-env GPU
  PPO smoke 통과, 초기 world-z=+0.871. **남음**: 학습 정책의 의도적 반전 rollout으로 임계값 보정.
- [ ] **관절 hard/soft range(R21)**: 굽힘 +부호, hard limit 이탈 0. soft range는 단음·코드·바레별
  정상 분포 뒤 설정 — **검증**: 랜덤 액션 및 학습 rollout에서 hard range 이탈 0, 정상 폼 제한 없음.
- [ ] **무효 자세 마스크**: 손끝 세그 수직>5°면 압현 보상=∞([G]:1543) — **검증**: 수직 찍기 자세에 보상≈0.
- [~] **기타 관통 0(R14)**: 필터 humanoid1/guitar2와 contact_offset 1e-4 시작 감사, 테이퍼 넥·바디
  해석 깊이, swept 통과, reset 겹침 진단 구현. 초기 8env×12step 및 reset noise 0.02의
  512env×2step에서 전 항목 0·PPO smoke 통과.
  5mm×3프레임 종료가 활성화되어 있다. 최종 평가는 해석 깊이·swept·초기겹침 proxy도 확인한다.
  **남음**: 학습된 정상 압현 깊이 분포의 오탐 여부와 exact mesh 관통 0 검증.
- [x] **기타 뒤 이탈 종료(R8)**: 엄지를 제외한 네 손가락 마디 중심선을 구간당 5점 샘플링한다.
  한 손가락 샘플의 25% 이상이 기타 로컬 `z<-50mm`에 3프레임 연속 있으면 종료한다.
  단일 끝점 돌출은 오탐으로 제외 — **검증**: CPU 경계·연속 필터, 강제 GPU `done=True`, 정상
  1초 준비 자세 최대 뒤쪽 비율 13.3%로 무종료, 8-env PPO smoke PASS.
- [x] **손가락 상호관통 진단(R22)**: self-collision OFF 상태에서 5손가락 capsule 10쌍의 표면 간격,
  2mm 초과 관통·streak 기록. 초기 8-env×120step 전 쌍 0, 강제는 보류.
- [x] **과압·비정상 지지 진단(R24)**: 손가락 마디·손바닥·손목·팔꿈치 순접촉력, target/inactive
  distal 힘, 30 제어관절 실제 토크·cap 비율을 info와 감사 JSON으로 기록. 보상·종료는 비활성.
- [x] **finite 실패 원인**: action/PD/torque, DOF position/velocity, root/body/contact와 reward/observation의
  NaN/Inf를 이름별 mask로 기록하고 유한값으로 정리한 뒤 실패 종료. reward 뒤 결합한 goal·EMA 파생
  관측도 같은 step에서 `nonfinite_observation`으로 종료한다. velocity blowup은 별도 reason.
- [ ] **앞면 접근**: 손가락이 지판 앞에서 하강(RSI가 대부분 보장) — **검증**: 손목·손끝이 넥 앞
  기타 로컬 `+z`측에서 접근.

## P4. 보상 — 지정 손가락 압현 (명시 운지)

- [x] **R1/R2 구현**: 줄별 `30% 접근거리 + 50% 실제 지정손가락 압현 + 20% 위치품질`.
  접근점은 wire 표면 기준 `x=20%`, 위치 최적은 `x=10~30%`, 뒤쪽은 `x=85%`까지 완만히 감점.
  CPU 단위검사와 8-env GPU PPO smoke 통과.
- [x] **접근 거리**: 끝마디 pad→p20의 평면오차와 one-sided 바깥 gap,
  12/60mm 듀얼스케일 커널 구현·단조성 검사 통과.
- [~] **실제 지정 손가락 press**: guitar local `-z` signed depth on/off=1.0/0.5mm, 올바른 프렛 칸,
  최고 프렛 승, 다른 손가락 대체 불인정, pad 반지름 6.3mm 구현. 기하 단위검사 통과.
  **남음**: 실제 PhysX 정답 자세에서 hover/press/해제 대조 및 임계값 보정.
- [~] **위치 quality**: press에 gate하고 x=10~30% 만점, 30~85% 완만 감점 구현·단위검사 통과.
  **남음**: 실제 같은 프렛 다중 손가락 자세에서 x=20/45/70% 대조.
- [~] **PRESS/NO_PRESS/DONT_CARE 통합**: 매 프레임 6줄×22프렛 요구 마스크와 실제 압현을 비교하고,
  목표보다 높은 프렛 또는 전 프렛 NO_PRESS 위반 시 해당 줄 task 점수 0. DC는 정확도·all-correct 제외.
  CPU 사례검사와 8-env GPU PPO smoke 통과. **남음**: 재학습 rollout의 오압현율 실측.
- [x] **후속 오압현 대응 hook**: `wrong_press_penalty=0`, `wrong_press_avoidance_weight=0` 기본 비활성.
  오압현율이 높을 때만 음수 페널티 또는 press-on 임계 전 연속 회피 shaping을 설정으로 활성화.
- [~] **R5 release goal 정제**: 같은 위치 재타현 PRESS 병합은 유지하고, 다른 다음 press가 있는
  `t_release..next.t_press` 구간을 NO_PRESS, 마지막 release 뒤를 DONT_CARE로 래스터화.
  CPU 전환 검사·재생성 S0 JSON 16 release window·8-env GPU smoke 통과. **남음**: 재학습 release 성공률 실측.
- [~] **press 검출(기하)**: 원통 pad reach + 프렛 칸 + signed-depth hysteresis + **최고 프렛 승** 구현.
  **남음**: 정답 압현 rollout에서 press==goal 실측.
- [x] **유지시간(R27)**: 동일 줄·fret·finger PRESS run을 이벤트로 묶고, 긴 음의 시작·끝 각 3프레임은
  전환 여유로 제외. 이벤트 유지율≥90%이고 연속 이탈≤3프레임이어야 성공하며 전체 이벤트 성공률
  100%를 최종 평가 gate로 사용. reward에는 중복 추가하지 않음. 짧은 음 보존·유지율·이탈 CPU 검사 PASS.
- [x] **HOLD 미끄러짐(R23)**: 실제 PRESS 3프레임 뒤 pad의 기타 로컬 x/y anchor를 설정하고 누적
  2mm 자유구간 초과분만 3mm scale·전체 0.5%로 감점. 목표 변경/접촉 실패/release reset, CPU+GPU PASS.
- [ ] **ChordReady 연속 유지(R25, 보류)**: 현재 단일 압현 S0와 strike timing 없는 60Hz goal에서는
  타현 전 준비를 판정할 수 없음. dyad·코드 단계 전에 strikes 래스터화 후 3프레임 유지 진단부터 추가.
- [~] **전체 보상 조합**: core 77% + wrist 15% + thumb support 5% + R12 proximal priority 2%
  + R18 hover 0.5% + R23 slip 0.5%. R10 smooth는 보류해 0%,
  core 내부 all-correct 20% 구현. **남음**: 새 정책 정답 정지 자세 수치 검증.
- [x] **R12 근위 관절 우선순위**: wrist goal 도달 전 비용 해제, 접근 후 정규화 속도 비용
  finger0.05<wrist0.20<elbow0.50<shoulder1.00. CPU 계층 검사·8-env GPU PPO smoke 통과.
- [x] **멀티크리틱 rew_dim=6**: `(N,6)` reward와 6 value heads를 유지한다. Actor는 곡에서 감독되는
  줄만 가중해 6열 advantage를 먼저 합산하고 scalar를 한 번 정규화한다. S0는 disc 미사용(value_dim=6).
- [x] **이식 금지 버그 회피**: body 이름 직접 조회, base의 정확한 guitar inverse frame 사용.

## P5. 관측

- [x] **기본·actuator 관측**: base 180차원 뒤에 직전 EMA action 30차원을 포함해 같은 자세에서도
  서로 다른 내부 PD 상태를 구분. runtime shape 확인.
- [x] **룩어헤드+손가락 이벤트 관측(R15)**: 시점당 25×3=75D 뒤에 손가락별
  `[string mask(6),fret,timing,valid,current-change,KEEP/MOVE/REST]` 13D×4와 반복 구간을 구분하는
  곡 진행률 1D를 붙여 goal128D를 구성하고, 현재는
  base180+goal128+prev_action30+thumb geometry12+future context75=`obs425D`다.
  합성 CPU 검사, S0 861프레임 전수 검사, GPU PPO smoke 통과. S0는 동일 손가락의 다중 줄과
  다중 프렛 배정을 모두 거부하며 명시적 바레 mask는 후속 `allow_barre=true`에서만 허용한다.
- [x] **정규화**: fret/22, finger/4, anchor·range/21, wrist/0.25 + RunningMeanStd.

## P6. 학습 루프·커리큘럼

- [x] **PPO 이식**: clipped PPO·6열 GAE·활성 줄 가중합 뒤 actor scalar 단일 정규화·RunningMeanStd
  구현. Actor/`log_std` lr=1e-5, Critic lr=3e-4로 분리하고 minibatch KL>0.03은 optimizer step 전에
  차단한다. 역사적 512env·2,500회 checkpoint=40,960,000 samples에서 NaN 없음,
  1,951~2,000회 평균 value loss 0.0525, KL 0.0203. **PopArt는 S0 후속**.
- [x] **strict checkpoint 계약**: ordered 30 DOF, 현재 425/30/6 shape, policy/action/reset,
  reward·safety·PPO, 활성 줄 actor 가중치·scalar advantage 버전, goal/hand SHA, 자산·핵심 구현 지문을
  저장한다. save에는 계약이 필수이고 재개·평가 전에 전체 일치·payload 무결성을 확인하며 legacy를 거부.
- [x] **곡별 RSI + R26 커리큘럼**: 한 곡의 goal/규칙을 고정한 채 coverage 1,000회 random-start 100%
  → integration 1,000회 100→0% → full-song frame 0으로 전환. 단계 상태는 context에 저장하고, 곡을
  포함한 전체 strict contract 불일치는 모델 적재 전에 거부. CPU 스케줄·8-env GPU PPO PASS.
- [x] **R29 reset 준비 clock**: frame0/RSI 시작 frame을 60프레임 고정하고 목표 관측·접근·압현 보상은
  제공하되 F1/R27 집계와 goal 진행은 정지. 이후 마지막 원곡 frame까지 평가하며 rollout 오디오는
  1초 offset. 별도 차원 없이 룩어헤드 dt·13D time-to에 남은 준비 delay를 더해 countdown을 관측하며
  `--preparation-seconds`와 checkpoint context에 길이 기록.
- [x] **종료·auto-reset 계약**: 마지막 goal 완료는 정상 종료이고 M2 `−25`는 조기 timeout·finite·속도
  폭주·hard safety 실패에만 적용. done step의 반환 obs는 다음 episode reset 관측이며 직전 관측·원인은
  `terminal_observation`, `terminal_env_ids`, `episode_*`로 PPO/eval에 보존.
- [ ] **스타일 disc**(선택, LH/wrist·LH/fingers): 자연스러움 — **검증**: disc reward가 자세 자연도 반영(정성).

## P7. 성공 판정 게이트 (이게 "성공적으로 동작"의 정의)

- [ ] **정량 — 독립 정확도 gate**: PRESS F1≥0.90, 적용 가능한 NO_PRESS 정확도≥0.99,
  `wrong_press_rate≤0.01`. 2026-07-22 수치는 역사 기준이며, 현재 425D 계약의 장기 학습 평가로
  다시 측정해야 한다. **남음**: 정확도와 sustain gate 통과.
- [ ] **완주·지속 gate**: 모든 평가 episode가 전체곡을 완료하고 실패 종료 0. 각 episode의 R27 이벤트
  수가 예상값과 같고 유지율≥0.90, 이벤트 성공률100%, 최장 이탈≤3프레임.
- [ ] **물리 proxy gate**: 해석적 관통≤5mm, swept 터널링·초기겹침·R7/R8/R13 종료 0.
  `hard_safety_passed`는 exact mesh 안전이 아닌 alias다. R14 termination은 활성화되어 있다.
  R22 capsule 2mm 초과 겹침 frame·초기겹침은 보정 전 진단값으로 기록하되 최종 gate에는 넣지 않음.
- [~] **정성 — fingermapping 대조**: 선택 모델 close-up `fret_002000_rollout.mp4` 생성·재생 검증 완료. **남음**: 목표 `isaac_fingering.mp4`와 프레임별 대조(앵커·선행준비 재현 확인; S0는 바레 없음).
- [ ] **최종 물리 감사 — exact mesh 관통 0 · 리밋 위반 0** (전체 곡 롤아웃) — proxy gate와 별도로
  `isaac_contact_audit` + 리밋 이탈 카운터와 영상을 확인.
- [ ] **선행 운지 — 앵커·미리누름 창발**: C→Am서 검지·중지 유지, 다음 폼 선행 이동 — **검증**: 데모 곡 롤아웃에서 앵커 손가락 t_press 연속성.
- [ ] **안정 — 비제어 부위 유지**: 우팔·몸통 하체 드리프트 소량 — **검증**: `verify_stability` 학습 정책 하에서.

---

## 의존 순서 (권장 착수 흐름)

```
P0 재확인 → P2 DOF 확정 → P1 goal 변환(단위테스트) → P5 관측 →
P4 보상(정지 자세 스모크) → P3 안전 스모크 → P6 첫 학습(S0) → P7 게이트 → 커리큘럼 진급
```
핵심 관문 3개: **P1 goal 변환 정합**(줄 반전·초→프레임), **P4 지정 손가락 감독**(명시의 정수), **P7 F1≥0.9 + fingermapping 대조**.
