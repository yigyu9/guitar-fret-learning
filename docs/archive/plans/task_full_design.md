# task_full (병합: 왼손 fret ∥ 오른손 strike) 설계 — §2 규칙 명세 (rule set)

> **상태: SUPERSEDED.** AdaptNet이 관절 residual을 출력하고 하나의 Full 정책을 학습하던 초기 결합안이다. 현재 Synchronizer는 관절을 제어하지 않는 timing supervisor이며, 정본은 [`master_plan/05_synchronizer.md`](../../../master_plan/05_synchronizer.md)와 [`master_plan/07_full_body_player.md`](../../../master_plan/07_full_body_player.md)다.

> 최종 갱신: 2026-08-03. 이 문서는 결합 태스크의 역사적 설계 초안이다. 현재 운영은 Fret과
> Strike를 각각 검증하며, Full 전용 실행·checkpoint 계약은 아직 공개하지 않는다.

> 백지 재설계의 **작업 정본**. 사전학습된 왼손 압현(fret) 정책과 오른손 타현(strike) 정책을 하나의
> 전신 캐릭터로 **결합**하여, 두 손이 같은 곡 타임라인 위에서 **시간 정합(동기)**되고 **공유 몸통을 절충**하며
> 함께 연주하도록 학습하기 위한 **규칙 명세**. 각 규칙은 실제로 `tasks/task_full.py`·`goals.py`·`base.py`·
> `learning/models.py`(AdaptNet)·`cfg.py` 중 어디서 강제되는지까지 지정한다(= 그 파일들의 사양서).
> 압현·타현의 **개별 보상은 새로 만들지 않고** `rewards/fret.py`·`rewards/strike.py`를 그대로 재사용한다.
> 자매 문서 `task_fret_design.md`(왼손 R1~R29·M1~M3)를 전제로 읽는다. 파일 지도는 `tab2body/STRUCTURE.md`.
> 최종 갱신 2026-07-17. 상태: 규칙 초안(상속 규칙 + 병합 전용 F/T/O/D/S + 결합 메커니즘 A1~A6).

## 0. 관통하는 프레임 — 누가 무엇을 책임지나

- **fingermapping = "규칙 엔진"**: 한 `fingering.json`이 **양손 goal을 동시에** 위반 0으로 생산한다 —
  `presses`(왼손 채널: 줄·프렛·손가락)와 `notes.t_on/strikes`(오른손 채널: 타현할 줄). 선행 압현(타현
  0.12s 앞), 재타현 병합, 조기 릴리즈까지 **오프라인에서 이미 계산**해 넘긴다.
- **두 사전학습 정책 = "손별 모터 제어기"**: `meta_fret`(왼손)·`meta_strike`(오른손)가 각자 자기 손의
  압현/타현을 물리적·사실적으로 달성하도록 이미 학습되어 있다. 병합은 이 둘을 **동결·융합**한다.
- **task_full = "조립자"**: 새 압현/타현 보상을 만들지 않는다. (a) 두 손 보상을 **concat**하고,
  (b) 우손 타현 보상을 좌손 압현 상태로 **게이팅(손 동기)**하며, (c) 종료를 **양손 OR**로 묶고,
  (d) AdaptNet으로 두 정책을 융합하며 **공유 몸통을 해제**한다.
- ⟹ **병합의 고유 규칙은 오직 세 가지 축**만 다룬다: **① 두 손의 시간 정합(동기)** · **② 공유 몸통 절충
  (한 손 모션이 다른 손을 방해하지 않음, 비제어 몸통 안정)** · **③ 양손 안전(종료 OR)**.
  압현 합법성·타현 궤적·손 자세 사실성은 전부 fret/strike 규칙에서 **상속**한다(재검사하지 않음).

## 1. 분류 체계 · 담당 파일

| 분류 | 뜻 | 주 담당 파일 |
|---|---|---|
| **보상** | 잘할수록 오르는 연속 점수(양손을 목표로 유도) | `env/rewards/fret.py` + `env/rewards/strike.py`(재사용), 조립은 `env/tasks/task_full.py` |
| **종료** | 걸리면 에피소드 즉시 종료(−25 벌점) | `env/tasks/task_full.py`(양손 조건 OR) |
| **목표** | 무엇을 향해 보상하나(양손 단일 타임라인) | `env/goals.py` |
| **관측** | 정책이 보는 입력(양손 현재+미래 목표) | `env/goals.py`(observe) |
| **인프라** | 자동 유지·결합 장치(직접 학습 대상 아님) | `env/base.py`, `learning/models.py`(AdaptNet), `learning/ppo.py`, `cfg.py` |

## 2. 규칙 마스터 표

### 상속 규칙 — fret + strike 전부 여전히 적용

병합은 두 손의 개별 규칙을 **하나도 완화하지 않는다**. 아래는 그대로 유효하며, 담당 파일도 그대로다.

| 출처 | 상속되는 규칙 | 담당 파일 |
|---|---|---|
| **왼손 fret** | R1~R29(압현 코어·타이밍·손자세·모션·안전·코드 준비·커리큘럼·지속·MOVE 진단·첫 goal 준비) + M1~M3(all-correct 보너스·종료 −25 broadcast·press 검출) | `rewards/fret.py`, 종료는 `tasks/task_full.py`로 편입 |
| **오른손 strike** | 타현 궤적↔목표 현 교차·타이밍 보상, pick 급가속 벌점·관절속도 벌점·접촉힘 보너스, 픽 이외 부위가 기타 스트럼영역(G:pluck_range) 바디에 접촉 시 벌점(env.py 2034-2035), 우손 종료 | `rewards/strike.py`, 종료는 `tasks/task_full.py`로 편입 |

→ **보상 채널**: 왼손 per-string 6채널 + 오른손 1채널 = **7채널**(§3-1). 두 손의 어떤 종료 조건이든
그대로 살아 있고 §3-4의 S1이 이를 OR로 합친다.

### 병합 전용 규칙 (F·T·O·D·S)

| # | 규칙 | 분류 | 담당 파일 | 강제 방식(스케치) |
|---|---|---|---|---|
| **F1** | 병합 보상 = 좌손 6채널·우손 1채널 concat → (N,7) | 보상 | `tasks/task_full.py` | `cat(rew_fret(N,6), rew_strike(N,1), -1)`. **호출 순서 좌→우 강제**(좌손이 먼저 `info["press"]`를 채워야 F2 게이팅이 성립) |
| **F2** | 우손 타현 보상은 그 줄 좌손이 목표 프렛을 **실제로 눌렀을 때만** 만점(= 손 타이밍 동기) | 보상 | `tasks/task_full.py` | `pressed = (press==goal_fret) OR (goal_fret==0) OR (~goal_right)` → `ready` 신호를 `strike._reward`에 주입. ready 아닌데 타현하면 우손 벌점(strike 내장) |
| **F3** | 좌손이 아직 못 눌러도 온셋 임박·초과면 타현 허용(곡 진행 정지 방지) | 보상 | `tasks/task_full.py` | `timer = (goal_t[:,0] ≤ τ_on) OR (goal_t_ ≥ τ_over)` → `ready = pressed OR timer`. τ 값 §5 미해결 |
| **F4** | all-correct 병합 보너스: 그 순간 좌손 목표 프렛 전부 **AND** 우손 타현 줄 전부 맞으면 보너스 | 보상 | `rewards/fret.py` + `rewards/strike.py` | 좌손 M1(+0.2) + 우손 정답 분기 보너스 — 각 손 보상 내부에서 이미 계산, 병합은 채널만 합침 |
| **T1** | 좌·우 goal이 **하나의 타임라인**(같은 `goal_t`·같은 goal 커서)을 공유해 함께 전진 | 목표 | `goals.py` | `update_goal_tensor`가 좌손 텐서·우손 텐서를 **한 번에** 전진. 두 손이 서로 다른 시점을 보지 않음 |
| **T2** | 왼손 누름이 오른손 타현보다 **먼저 완료**(누름 선행 → 타현) | 목표 | `goals.py` | `presses`의 `t_press`(타현 0.12s 선행)가 좌손 press 목표를 먼저 켜고, `notes.t_on`가 우손 타현 목표를 켬. 선행/병합/조기릴리즈는 fingermapping이 이미 계산 |
| **T3** | 재타현 병합 구간: 좌손 유지(R20)와 우손 재타현이 **정합** | 목표 | `goals.py` | 스티키 핑거(좌손 press 유지 목표)와 우손 재타현 목표를 같은 구간에 함께 세팅 |
| **O1** | 관측 goal = [좌손 per-string fret+시간]×horizon ‖ [우손 per-string bool+시간]×horizon ‖ `pluck_correct`(6) | 관측 | `goals.py`(observe) | Xu 76차원 인코딩 이식. 명시 운지면 finger id 채널 추가 검토(§5) |
| **O2** | 룩어헤드: `goal_horizon` 미래 노트를 **양손 각각** 포함 | 관측 | `goals.py` | 두 손이 미리 자리를 잡도록 미래 목표를 obs에 노출 |
| **O3** | 양손 바디 관측 모두 **기타로컬 좌표** | 관측 | `base.py` + `goals.py` | quat 버그 회피(기타상대 관측). weld→free(G1)를 투명하게 만듦 |
| **D1** | 좌손 사실성·자세 규칙 상속(R6 엄지·R10 부드러움·R12 근위안정·R13 손바닥 바닥방향 종료·R17 idle·R19 손목중립 등) | 사실성 | `rewards/fret.py` | fret 보상 그대로 재사용, 병합에서 완화 없음 |
| **D2** | 우손 사실성 규칙 상속(pick 급가속 억제·관절속도 규제·접촉힘 보너스) | 사실성 | `rewards/strike.py` | strike 보상 그대로 재사용 |
| **D3** | **한 손 모션이 다른 손을 방해하지 않음** + 공유 몸통이 양손 요구를 절충(비제어 몸통이 외란에도 안정) | 사실성 | `tasks/task_full.py` + `learning/models.py`(AdaptNet) | 새 명시 보상 없음 — AdaptNet 잔차가 두 정책의 몸통 요구를 절충하도록 학습. 안정성은 D1·D2 사실성 항의 결합 결과로 창발 |
| **D4** | (선택) 병합 스타일 판별자 | 사실성 | `learning/models.py` | Xu는 좌손 wrist/fingers disc 2개만(우손 disc 주석, cfg/two_demo.py). 판별자는 **옵션** — 태스크 보상만으로 먼저 학습(무disc 기본)한 뒤 좌손/양손 disc를 A/B로 얹는다(채택 판정은 결정 #10 A/B 방식). 채택 시에만 value_dim에 가산 |
| **S1** | 종료 = 좌손 종료 **OR** 우손 종료 | 종료 | `tasks/task_full.py` | `termination = fret._termination OR strike._termination`. 손목박스(R7)·지판뒤(R8)·엄지이탈(R6)·손바닥 world-z<−0.3(R13)·관통(R14) 어느 손이든 걸리면 종료 |
| **S2** | 공유 몸통↔기타 관통 금지 + 전신 자기충돌 금지 | 종료+인프라 | `tasks/task_full.py` + `base.py` | R14(관통)를 전신으로 확장. Xu(손만)엔 없던 전신 자기충돌·몸통 관통 판정 필요 |
| **S3** | 병합은 **기타 G0 유지**(기타 월드 고정) | 인프라 | `base.py` + `cfg.py` | **기타 액터에만** `fix_base_link=True, disable_gravity=True`. humanoid는 중력 ON·root 고정(결정 #5 root 고정 + 함정 #10 중력성 드리프트). guitar env의 전역 disable_gravity는 손-only 시뮬 산물이므로 전신엔 액터별 분리 적용. 기타 안정은 별도 태스크 아님 = 병합 정책의 G1 파인튜닝(§3-5·A6). G0에선 `hold` 보상 미가산 |
| **S4** | 어떤 종료든 7채널 전부에 −25 broadcast | 인프라 | `learning/ppo.py` | 좌손 M2를 7채널로 확장(`terminate_reward=−25`) |

### 결합 메커니즘 (A1~A6, 규칙 실현 장치 — AdaptNet)

병합은 단일 env에서 처음부터 학습하지 않는다(결정 #4). fret·strike를 **개별 학습**한 뒤, 두 정책을
**주입 네트워크 AdaptNet**으로 융합한다. 아래는 그 장치의 사양(참조: `related_work/guitar/models.py:288-378`).

| # | 장치 | 분류 | 담당 파일 | 내용 |
|---|---|---|---|---|
| **A1** | 사전학습 정책 동결 | 인프라 | `learning/models.py` | `meta_fret`·`meta_strike`의 파라미터를 **sigma 제외 전부 `requires_grad=False`**. 두 손의 모터 스킬은 보존 |
| **A2** | zero-init 잔차 시작 | 인프라 | `learning/models.py` | 어댑터 `embed` MLP의 **마지막 Linear를 zero-init** → 학습 시작 순간 잔차 z=0이라 출력 = 두 정책 각각의 출력을 그대로 concat(각 손 액션이 정확히 보존된 상태에서 출발). 융합이 안전한 지점에서 출발 |
| **A3** | disjoint action concat | 인프라 | `learning/models.py` + `cfg.py` | 출력 = `Normal(cat(mu_fret, mu_strike), cat(sigma_fret, sigma_strike))`. **몸통 DOF를 fret(좌)에 귀속**시켜 좌/우 액션이 겹치지 않게 유지(우리 해법 — §4·§5) |
| **A4** | 이중 ob_normalizer | 인프라 | `learning/models.py` | 정규화기 2개: 어댑터용 1개 + 동결 meta용 1개(`ob_normalizer_list` 길이 2). 각 손 정책이 학습 때 본 정규화를 그대로 유지 |
| **A5** | 멀티크리틱 value_dim | 인프라 | `learning/models.py` + `learning/ppo.py` | `value_dim = n_disc + rew_dim(7)`. D4 무disc면 **7**, 좌손 disc 2개 채택 시 **9**. DiagonalPopArt 값 정규화, 열별 GAE·열별 어드밴티지 정규화 |
| **A6** | G0→G1→G2 스테이지 전환 | 인프라 | `tasks/task_full.py` + `cfg.py` + `rewards/hold.py` | `FULL`=G0(기타 고정 병합), `FULL_G1`=기타 풀기+스트랩 spring-damper+`hold` 보상 가산, G2=자유. 같은 정책이 config로 스테이지 승계(기타상대 관측 O3가 weld→free를 투명화) |

## 3. 규칙별 상세 (그룹)

### 3-1. 보상 조립 (F1·F4 + 상속)
- **7채널 concat(F1)**: `rew_fret`는 줄별 자기 채널을 갖는 per-string 6채널(멀티크리틱), `rew_strike`는
  1채널. `cat(rew_fret, rew_strike)` → (N,7). **좌손을 반드시 먼저 계산**해야 한다 — 좌손 보상 계산이
  `info["press"]`(각 줄이 실제로 눌렸는지)를 채우고, F2 게이팅이 그 값을 읽기 때문. 순서를 바꾸면 이전
  스텝의 stale press로 게이팅되어 동기 신호가 어긋난다.
- **all-correct 병합 보너스(F4)**: 좌손 목표 프렛 전부 맞음(M1 +0.2)과 우손 타현 줄 전부 맞음이 함께
  성립하는 순간 각 손 보상 내부의 정답 분기가 켜진다. 병합 계층은 별도 계산 없이 채널만 합친다.

### 3-2. 손 동기 게이팅 (F2·F3) — 병합의 핵심
두 손을 **시간적으로 묶는 유일한 결합 보상 로직**. 우손이 타현할 자격(`ready`)을 좌손 상태로 판정한다.
- **pressed(F2)**: 줄별로 다음 셋 중 하나면 True — ① 그 줄 좌손이 목표 프렛을 실제로 눌렀다
  (`press == goal_fret`), ② 그 줄은 don't-care(`goal_fret == 0`), ③ 그 줄은 타현 대상이 아니다
  (`~goal_right`). 즉 **눌러야 할 줄은 실제로 눌러야만** 우손이 만점을 받는다.
- **timer(F3)**: 좌손이 아직 못 눌렀어도 **온셋 임박**(타이머 `goal_t[:,0]`가 임계 τ_on 이하) 또는
  **초과**(경과 카운터 `goal_t_`가 임계 τ_over 이상)면 타현을 허용. 좌손 실패가 곡 전체를 정지시키는 것을
  막는 안전밸브. τ_on·τ_over 구체값은 §5 미해결(우리 BPM·fps·0.12s 선행과 정합시켜 재튜닝).
- **ready = pressed OR timer** → `strike._reward`에 주입. ready 아닌 줄을 타현하면 우손 pluck 벌점.

### 3-3. 단일 타임라인·룩어헤드·관측 (T1·T2·T3·O1·O2·O3)
- **공유 타임라인(T1)**: 좌·우 goal이 같은 goal 커서·같은 `goal_t`로 함께 롤한다. 두 손이 서로 다른 마디를
  보는 일이 없다.
- **누름 선행(T2)**: `t_press`가 타현보다 앞서 좌손 press 목표를 켠다(타현 0.12s 선행). 이 선행·병합·
  조기릴리즈 타임라인은 fingermapping이 오프라인에서 확정해 `presses`로 넘긴다(env는 재계산하지 않음).
- **재타현 정합(T3)**: 재타현이 병합된 구간에서 좌손은 유지(R20 스티키), 우손은 재타현. 두 채널이 같은
  구간에 정합하도록 goal을 세팅.
- **양손 goal 관측(O1)**: Xu 76차원 인코딩 이식 — 좌손 per-string 목표(fret+남은시간)×horizon, 우손
  per-string 타현여부(bool+남은시간)×horizon, 그리고 `pluck_correct`(6). 명시 운지에서는 손가락 id
  채널 추가를 검토(§5).
- **룩어헤드(O2)**: `goal_horizon` 만큼의 미래 노트를 양손 각각 obs에 담아 두 손이 미리 자세를 잡는다.
- **기타상대 관측(O3)**: 양손 바디 좌표를 모두 기타로컬로 표현(quat 버그 회피). G1에서 기타를 풀어도
  관측이 불변이라 같은 정책이 스테이지를 승계.

### 3-4. 사실성·모션 절충 (D1·D2·D3·D4)
- **좌손 상속(D1)·우손 상속(D2)**: 각 손의 자세·부드러움·에너지 규제는 fret/strike 보상 그대로. 병합에서
  완화·재정의하지 않는다.
- **몸통 절충(D3)**: "한 손 모션이 다른 손을 방해하지 않음"과 "비제어 몸통이 외란에도 안정"은 **명시 보상이
  아니라 AdaptNet 잔차 학습의 목표 상태**다. 우손 타현이 몸통을 흔들면 좌손 압현 보상(D1)이 떨어지고,
  그 반대도 성립 — 두 손 보상이 서로에게 몸통 안정의 압력을 준다. 잔차 z가 이 절충을 흡수한다는 것이
  결합의 핵심 가정(§4·§5의 최대 미해결과 직결).
- **스타일 disc(D4)**: 채택은 선택. 판별자는 옵션이므로 태스크 보상만으로 먼저 학습(무disc 기본), 이후 좌손/
  양손 disc를 A/B로 얹는다(채택 판정은 결정 #10 A/B 방식). 채택 시에만 value_dim(A5)에 가산.

### 3-5. 안전·종료·스테이징 (S1·S2·S3·S4 + A6)
- **양손 종료 OR(S1)**: 좌손·우손 어느 쪽의 종료 조건이든 걸리면 에피소드 종료. 두 손의 안전 규칙이 전부
  살아 있다.
- **전신 관통·자기충돌(S2)**: R14(손↔기타 관통)를 전신으로 확장. Xu는 손 두 개뿐이라 몸통 관통·전신
  자기충돌 판정이 없었다 — 우리는 base의 충돌 필터가 1차 저항, 침투/과대 접촉힘이 2차 종료(metric·임계는
  §5). **정상 접촉(압현·타현)과 관통을 구분**하는 것이 관건(fret R14와 동일 주의).
- **기타 G0 유지(S3)**: 병합 본체(G0)에서 기타 액터만 월드에 고정(`fix_base_link`·`disable_gravity`), humanoid는
  중력 ON·root 고정(결정 #5). 기타 안정성은 독립 태스크가 아니라 병합 정책의 후속 파인튜닝이다.
- **스테이징(A6)**: `FULL`(G0) → `FULL_G1`(기타 풀기+스트랩+`hold` 보상) → G2(자유). 별도 `task_hold.py`
  없이 `task_full.py`가 config로 전환하고, `rewards/hold.py`는 G1 이상에서만 가산.
- 모든 종료는 S4로 7채널 전부에 −25 broadcast.

### 3-6. 결합 메커니즘 (A1~A6)
AdaptNet은 두 동결 정책(A1)을 잔차로 융합한다. zero-init(A2)로 "두 정책 출력의 concat(잔차 0)"에서 출발해 안전하게
파인튜닝하고, 출력은 좌·우 disjoint 액션 concat(A3)이며, 정규화기(A4)와 멀티크리틱(A5)은 각 손의 학습
조건을 보존한다. 스테이지 전환(A6)은 같은 네트워크로 G0→G1→G2를 잇는다.

## 4. 규칙 간 관계 · 잠재 충돌

- **F1(좌→우 순서) ↔ F2(게이팅)**: 순서가 뒤바뀌면 stale `press`로 게이팅되어 손 동기가 무너진다.
  구현에서 **보상 계산 순서를 하드 제약**으로 못박아야 한다.
- **F2(눌러야 타현) ↔ F3(임박/초과 유예)**: F2만 있으면 좌손이 한 번 실패할 때 곡이 영영 멈춘다. F3의
  타이머가 진행을 보장하되, τ가 너무 관대하면 F2의 동기 압력이 약해진다 → τ 튜닝이 두 규칙의 균형점(§5).
- **D3(몸통 절충) ↔ A3(disjoint concat) — 가장 큰 난제**: Xu는 손 두 개가 **분리 액터·DOF 완전 disjoint·
  몸통 없음**이라 concat이 자연히 성립했다. 우리 전신은 몸통 DOF를 좌/우 팔 체인이 공유한다. 우리는 몸통을
  fret(좌)에 귀속시켜 disjoint를 회복하지만, 그러면 **strike는 단독 학습 때 "고정 몸통"을 봤는데 병합에선
  fret이 움직이는 몸통을 본다 = 분포 이동**. 잔차 AdaptNet(A2)이 이를 흡수한다는 것이 가정이며, 검증
  전까지 이 태스크의 핵심 리스크(§5).
- **O1(goal 76) ↔ A3(AdaptNet actor)**: Xu AdaptNet actor는 goal 76 중 앞 70(좌 35+우 35)만 쓰고
  `pluck_correct`(6)는 버린다(크리틱만 사용). 또 우손 goal 차원은 actor/critic 비대칭. 우리 goal 채널을
  설계할 때 이 actor↔critic 비대칭을 그대로 살릴지 확정해야 한다.
- **S1(양손 종료 OR) ↔ 학습 안정**: 종료 조건이 두 배가 되어 초기 종료율이 높아질 수 있다 → 커리큘럼·grace
  period(현 5프레임)와의 정합 확인.
- **좌손 goal vs 우손 goal 처리 비대칭**: 우손 goal은 타현 대상 줄 사이 구멍을 메워 스트럼을 표현하지만
  좌손 goal은 메우지 않는다. `goals.py`에서 두 채널을 서로 다른 규칙으로 생성해야 한다(혼동 주의).

## 5. 구현 시 확정 필요 (기하·임계값·구조 미해결)

- **손 동기 임계 τ_on·τ_over(F3)**: Xu는 `goal_t[:,0] ≤ 3`, `goal_t_ ≥ 5`(프레임 하드코딩). 우리 BPM·
  fps(60)·`t_press` 0.12s 선행과 정합하도록 **재튜닝 필요**. 본문에선 τ로만 표기, 값 미확정.
- **공유 몸통 분포 이동(D3·A3)**: strike 단독학습(고정 몸통) → 병합(움직이는 몸통)의 분포 이동을 잔차
  AdaptNet이 실제로 흡수하는지 **미검증**. 몸통 소유를 fret에 두는 것이 최선인지도 확정 전(대안: 몸통 별도
  잔차 헤드).
- **goal 차원(O1)**: Xu 76 그대로 갈지, 명시 운지의 손가락 id 채널을 추가할지 미확정. `pluck_correct`(6)를
  actor에서 버리는 Xu 비대칭을 따를지도 확정 필요.
- **value_dim·disc 정책(A5·D4)**: 판별자를 쓸지(좌손만? 양손?) 미확정 → value_dim이 7(무disc 기본, =rew_dim)
  또는 9(좌손 disc 2개 채택)로 갈림.
- **strike rew_dim 미정(연쇄 의존)**: full의 7채널(=fret 6 + strike 1)은 **strike rew_dim=1(Xu) 가정**이다. strike가
  6(줄별)로 귀결되면 full=12채널로 바뀌고 value_dim·hold 사이징까지 연쇄 변경 → **base 사이징 인터페이스 착수
  전 strike rew_dim을 먼저 확정**해야 한다.
- **멀티크리틱 채널 가중**: 좌손 6채널 대 우손 1채널의 상대 가중(Xu 적용값: 좌 각 0.15/2=0.075·우 1/2=0.5,
  비 0.15:1 유지, cfg/two_demo.py). 우리 곡·데이터에서 재튜닝 대상.
- **전신 관통 metric(S2)**: 침투 깊이 vs 접촉힘 중 무엇으로, 임계값 얼마. 정상 접촉과의 구분 기준. 전신
  자기충돌 필터 구성.
- **string↔JSON 매핑**: 채택 규약 G:string6=low-E(frets[5]=low-E). goals.py 이식 시 스모크로 1회 검증(우리
  `presses`/`notes` 스키마 ↔ Xu note_tar 반전 규약의 어댑터 필요).
- **press 검출·plucking depth 임계**: fret/strike 문서에서 상속하되 병합 조건에서 재검증(6.3mm·plucking
  depth 등).
- **보상 반환 방식**: `base.step()` 4-튜플 확장 vs `task_full.compute_reward()` 분리 — 미확정(STRUCTURE.md
  공통 이슈). `base.py`의 `rew_dim(7)`/`goal_dim`/`value_dim` 사이징 속성 노출도 착수 전 확정.
- **네트워크 시계열**: Xu AdaptNet은 rnn(GRU)을 deepcopy하는 구조를 전제한다. 우리가 룩어헤드를 goal에
  넣어 단일프레임 MLP로 가면 AdaptNet 프런트엔드 구조가 바뀐다 → GRU 제거 여부 미정.

## 6. 다른 섹션 (예정)

- **§1 학습환경(PPO·AdaptNet 하이퍼)**: PPO + 멀티크리틱 + DiagonalPopArt, Isaac 병렬. AdaptNet actor
  5e-6/critic 1e-4·엔트로피 0·zero-init 잔차 시작. num_envs·horizon·γλ 등 Xu `two_demo`/`main.py` 근거
  정리 예정.
- **§3 입출력(type·shape)**: action = `cat(좌손 DOF, 우손 DOF)`(disjoint 전신) · 보상 `(N,7)` · obs =
  양손 고유수용 + 양손 기타상대 바디 + 양손 goal(O1). 세부 인코딩·몸통 귀속 DOF 분할 확정 예정.
- **§4 스테이징 상세(G0→G1→G2)**: `hold` 보상 항, 스트랩 spring-damper 파라미터, weld→free 전환 절차
  정리 예정.

---

## 부록: 근거 파일(절대경로)

템플릿 `/home/ajou/yigyu/3/docs/archive/plans/task_fret_design.md`, 파일 지도 `/home/ajou/yigyu/3/tab2body/STRUCTURE.md`, 참조구현 `/home/ajou/yigyu/3/related_work/guitar/env.py`(TwoHands reward 2185-2201·termination 2182-2183)와 `/home/ajou/yigyu/3/related_work/guitar/models.py`(AdaptNet 288-378), 대상 스텁 `/home/ajou/yigyu/3/tab2body/env/tasks/task_full.py`·`/home/ajou/yigyu/3/tab2body/learning/models.py`·`/home/ajou/yigyu/3/tab2body/cfg.py`.
