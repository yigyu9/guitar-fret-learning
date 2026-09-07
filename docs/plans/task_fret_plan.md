# task_fret — 왼손 Fret 압현 학습 환경 설계·구현 계획 (2026-07-16)

> **상태: HISTORICAL.** 최초 Fret 구현 계획과 결정 근거를 보존한다. 현재 정본은 [`master_plan/03_fret.md`](../../master_plan/03_fret.md)다.

> 상태: **역사적 구현 계획**. 현재 정본은 `task_fret_design.md`, 실행 상태는 `PROJECT_CONTEXT.md`와
> `fret/WORK_REPORT.md`를 따른다. 아래 내용은 초기 결정 근거를 보존한다.
>
> 사용자 결정 2건 반영(2026-07-16),
> S0 학습 JSON 파일럿 1곡 생성(2026-07-19):
> ① 운지 감독 = **처음부터 명시(explicit)** — 우리 fingermapping의 finger id를 goal로 감독.
> ② 이 문서는 계획서로 저장, 구현은 별도 지시 후 착수.
> 근거 표기: **[G]**=`related_work/guitar/env.py`(Xu SA'24, 이식원본) · **[GPS]**=`related_work/GPS/`(CGF'24) ·
> **[D]**=과거 DIGIT 실패 분석(안티패턴) · **[P]**=PROJECT_CONTEXT/README(정본·함정) · **[M]**=본 프로젝트 실측.
> 승계: 이 계획이 착수되면 PROJECT_CONTEXT §2 "다음 작업(T2)"의 구체화다. base.py는 완성·검증됨(env/README.md).
>
> **2026-07-21 방향 갱신**: 아래의 20곡 일괄 학습·난이도 자동 승급 서술은 초기 계획 기록이다.
> 현재 정본은 **곡 하나마다 정책 하나를 여러 epoch 반복 최적화**하는 방식이다. 곡 안에 포함된 단음·코드
> 형태는 모두 같은 고정 goal에 남기며, 시작점만 coverage→integration→full-song으로 바꾼다.

---

## 0. 한 줄

좌식 전신의 왼팔·왼손 33DOF가 운지 goal을 받아 지정 손가락으로 줄·프렛을 누르도록 학습한다.

## 1. 목표·범위·성공 게이트

- **범위**: 왼손 압현만(태스크 A). 우손 strike(B)·결합(A+B)·기타 자유화(G1/G2)는 별도 계획.
- **기타 스테이징**: G0(월드고정)에서만. 압현 보상은 순수 기하라 접촉힘 불필요.
- **1차 게이트**: S0 단음곡에서 **좌손 F1 ≥ 0.9**(accuracy_l/precision_l/recall_l, [G] 1580-1606 이식 지표).
- **커리큘럼**: 같은 곡의 부분구간 coverage → 구간·전체 통합 → frame 0 전체곡 반복.

## 2. 선행연구 대조 (핵심만)

| 축 | Xu [G] = 베이스 | GPS | **우리 채택(명시)** |
|---|---|---|---|
| 운지 | 암묵(순서형 손가락-윈도 마스크) | 명시(arrangeFinger 그리디) | **명시 — 우리 fingermapping(빔서치·그립·앵커)** |
| 거리 보상 | 듀얼스케일 가우시안 | 축분해 거리 | **Xu 듀얼스케일 유지 + 지정 손가락으로 min 제한** |
| 압점·판정 | 단일점 거리 | 칸 정중앙+힘 | **우리: 30% 접근(x=20%) + 50% signed-depth press + 20% 위치품질(x=10~30% 만점)** |
| press 검출 | 순수 기하 | 접촉힘 | **Xu 기하** (G0 접촉 불필요) |
| 보상 구조 | per-string 6채널 멀티크리틱 | 0.5f+0.5k+E | **per-string 6채널 유지, rew_dim=6** |
| 데이터 | 노트 윈도 10~20 | 곡별 | **20곡 note JSON → fingermapping → finger 라벨** |

명시 채택 이유: Xu·GPS 공통 한계 = "선행적 운지 계획 부재"(Xu Fig13). 우리 fingermapping이 앵커핑거·바레·선행준비를 이미 해결 → 이를 감독 신호로 쓰면 그 한계가 우리 노벨티가 됨(결정 #10 정합).

## 3. 데이터 소스 — 명시 운지의 새 의존성 ⚠️

**문제**: 학습 주 데이터인 20곡(`related_work/guitar/assets/notes/*.json`, 결정 #7)은 (줄,프렛)만 있고 **손가락 라벨이 없다**. 명시 운지는 손가락 라벨이 필요.

**해법**: 20곡 note JSON을 우리 fingermapping에 **오프라인 1회 통과**시켜 finger-annotated goal 생성.
- `fingermapping`의 `press_events` 출력 = `{finger∈{1,2,3,4}, string, fret, barre, t_press, t_release, strikes}` = 왼손 goal 그 자체([P] §2 "fingering.json=왼손 goal", Stage1 next-task ①).
- finger: 1=검지,2=중지,3=약지,4=소지 → `LH:{index,middle,ring,pinky}` 세그먼트. 0(개방)=압현 아님 → goal −1 처리.
- 산출물 = `tab2body/_gen/notes_fingered/*.json` (재생성물, 위생규칙 [P]#8).

**전제 검증(구현 전 스모크)**: fingermapping이 20곡 note JSON 입력을 받는지(CSV 전용이면 note JSON→CSV 어댑터 필요), 20곡 전곡에서 `finger=None`/`t_cut` 진단율 확인. 진단율 높으면 해당 구간은 암묵 폴백(§10).

### 3.1 S0 파일럿 데이터 (2026-07-19 완료)

첫 학습은 20곡 전체 변환보다 먼저 오디오와 직접 매핑된 GuitarSet JAMS 정답 annotation에서
`02_Jazz1-200-B_solo`를 선정했다. 후보 전수 통계 중 이 곡은 42음·최대 동시발음 1·4~7프렛·
사용 줄 3개로, 한 음/한 프렛 고정은 피하면서 바레·화음 없이 시작하기 적합하다.

- 생성 도구: `tab2body/tools/build_fret_training_data.py`
- 산출물: `data/song_bundles/02_Jazz1-200-B_solo/training/fret_training.json`
- 검수 번들: 현재 정본은 `data/song_bundles/02_Jazz1-200-B_solo/`이며 오디오, JAMS annotation,
  원본 fingering JSON, 학습 입력 JSON을 `source/`, `mapping/`, `training/`으로 분리해 보존한다.
- 명시 운지 결과: press event 24개, 진단 0, 생체역학 위반 0.
- 학습 표현: 60Hz 861프레임, 줄별 `fret_goal[6]`·`finger_goal[6]`·`barre_goal[6]`.
- hand position: finger mapping의 검지 기준 `P`를 anchor로 쓰되 한 점을 강제하지 않고
  `[P-1, P+4]` 상당의 **6프렛 soft band**를 사용한다. 다음 포지션은 0.25초 전부터 선형 보간한다.
- 3D hand prior(2026-07-19): `fingerviz/visualize_fingering.py --training-json`이 실제 기타 에셋의
  프렛/줄 좌표로 넥 축을 계산하고, 손목 중심+4cm soft workspace를 기타 로컬 좌표로 내보낸다.
  S0 번들의 `*.hand_position_targets.json`(430 frame)과 `*.isaac_hand_position.mp4`로 검수 가능.
  단, 이는 기하 오프셋 prior이므로 T-d 이전에 휴머노이드 손목 IK·관통 검증 후 오프셋을 확정한다.
- 줄 축: event는 0=low-E, frame goal은 Isaac 순서 0=high-e/5=low-E로 변환 완료.

## 4. `goals.py` 스펙 (명시 운지)

[G] 1045-1432 이식 + finger 채널 추가.

**(a) 노트 로딩** — [G] 1045-1234. **goal 인코딩 반전 절대 보존**([G] 1143-1148, 감사 ③):
```
JSON frets: -1=안침, 0=개방침, f≥1=f프렛  →  왼손 goal: 0=don't-care, -1=누르지마, f≥1=눌러
```
연주가능성 위생([G] 1090-1109): 스팬>4 드롭, distinct>4 상위4 → 4손가락 5프렛.
**string 매핑 확정**: `G:string{k}↔frets[k-1]`, **G:string6=low-E**(감사 4단 근거로 §7 "미확정" 닫음). fingerviz `CSV s0→G:string6` 가정과 일치 스모크 1회.

**(b) finger 채널 추가(신규)**: goal_tensor(줄별 프렛, [G] 30=5×6)와 **병렬로 finger_tensor**(줄별 손가락 id, 5×6) 유지. update_goal_tensor가 프렛과 동시 롤링. finger는 fingermapping 출력에서 로드.

**(c) 윈도·타이머** — `reset_goal` [G] 1236-1324. 곡 가중샘플→10~20 노트 윈도→프레임 타이머(min5·max50, 첫=grace5). 피치/BPM 증강 초기 off. ⚠️피치 증강은 finger 라벨과 정합 안 됨(프렛 이동 시 운지 재계산 필요) → **명시 모드에선 피치 증강 보류**.

**(d) 관측** — `observe_goal` [G] 1420-1432. 기본 35차원(5×[줄6 프렛÷12 + 타이머÷20]) + **finger 관측 추가**: [GPS]식 지정손가락 목표 위치(5손가락×3=15) 또는 손가락 id one-hot. → `goal_dim` = 35 + finger관측. task_fret.compute_observations = `cat(super(), observe_goal)`.

## 5. `rewards/fret.py` 스펙 (명시 = Xu 커널 + 지정손가락 감독)

[G] 1471-1687 이식하되 **암묵 윈도 마스크(1614-1651)를 지정손가락 마스크로 교체**.

**압현 기하**([G] 1485-1510 이식 후 2026-07-20 재정의): 목표 와이어 표면→이전 와이어 표면의
나무 구간을 `x=0..1`로 두고, 접근은 목표 줄의 x=20% 지점을 향한다. 실제 성공은 pad가 기타
local -z로 1.0mm 이상 누른 signed depth와 올바른 프렛 칸/최고 프렛 일치로 판정하며, 위치품질은
x=10~30% 만점·30~85% 완만 감점이다. 30/50/20 분해와 signed-depth 판정은 구현 완료됐다.
일반 압현은 끝마디, 바레는 검지 여러 마디를 쓴다.

**보상 채널(per-string, 반환 `(N,6)` → rew_dim=6)**:

| goal | 채널 | 공식 |
|---|---|---|
| f≥1 | 압현 | `0.30·접근 + 0.50·지정손가락 press + 0.20·press·위치품질`; 높은 프렛 NP 위반 시 0 |
| −1 | NO_PRESS | 1~22프렛 중 실제 press 없음=1, 하나라도 press=0 |
| 0 | DONT_CARE | 행동 독립 상수, 정확도·all-correct 검사 제외 |
| — | 정답 보너스 | `0.8·rew_tar+0.2·all_correct`; 요구가 있는 PRESS/NP 줄만 검사 |
| — | 부드러움 | `+0.05·e^(−3000·(Δ손목+0.1·Δ손끝)²)` |

**지정손가락 마스크(신규, 암묵 마스크 대체)**: string s의 goal이 (fret f, finger k)면 dist2fret를 finger k의 세그먼트 외에는 inf. 세로 손가락(>5°) 실격은 [G] 그대로.
- **줄·프렛 요구 마스크**: 양의 목표 f는 `1..f-1=DC / f=PRESS / f+1..22=NP`로 파생한다.
  NP 오압현은 해당 줄 task 점수를 0으로 무효화한다. 추가 음수 페널티와 연속 회피 shaping은
  기본 0인 설정 hook으로만 준비한다.
- **바레 처리**: fingermapping `barre=True`면 검지(finger 1)가 같은 프렛의 여러 줄을 담당 → 그 줄들 모두 finger 1로 감독(finger 1은 복수 줄 허용).
- **폴백**: finger 정보 없는 구간(진단 `finger=None`)은 [G] 암묵 윈도 마스크로 자동 폴백 → 코드에 두 경로 공존(명시 우선).

**press 검출 = 순수 기하**([G] 1550-1576): 세그↔줄<6.3mm AND y 프렛 사이 → 눌림, 최고 프렛 승. 접촉힘 불필요.

**주의(감사 ⑦, 이식 금지 버그)**: [G] 1675 좌손 이동보상 wrist 인덱스 오프셋(13+ 누락) — 부드러움 항 이식 시 수정. 쿼터니언 conjugation 버그는 base.py가 이미 회피.

## 6. `tasks/task_fret.py` 조립

- **control_dofs(2026-07-20 재정의)** = `L_Thorax/L_Shoulder/L_Elbow/L_Wrist + LH:thumb/index/middle/ring/pinky` = 33DOF.
  `Torso/Spine/Chest`·머리·우팔·RH·하체는 비제어 init PD 유지. 몸통 뒤꺾임 권한을 제거하면서 작은 어깨 띠 움직임과 엄지 지지는 허용한다.
- **종료**: 손목 기타로컬 고정 박스 이탈 3프레임 / 비엄지 손가락 샘플 25% 이상이 `z<−0.05m`에 3프레임 / 손바닥 명백한 바닥 반전 → base timeout·NaN·blow와 OR. 엄지 과이탈은 분포 확인 전 보류.
- **멀티크리틱**: 줄별 reward/value 6채널이다. 곡 전체에서 영구 DONT_CARE인 줄은 actor 가중치에서 제외한다.
- **학습루프**: 6 value-head advantage를 활성 줄 가중합한 뒤 scalar advantage를 한 번만 정규화한다. Actor LR은 `1e-5`, Critic LR은 `3e-4`이며 optimizer step 전에 KL `0.03` 초과를 차단한다.

## 7. `base.py` 인터페이스 확장 (감사 ④가 지목, 착수 전 확정)

현재 `FretTask.step`은 `(obs, reward[N,6], done[N], info)`를 반환한다. goal advance, 6채널
reward/value, named termination, terminal observation과 자동 reset 다음 관측이 모두 연결돼 있다.

## 8. 전신 난제 + GPS 튜닝 노브

**난제(선행연구 없음)**: ①팔이 손을 넥까지 이동(reach 34/36 검증됨, 단 35% 고정 기준 — 가변 압점 이식 시 재확인 1회) ②큰 액션공간 손끝 정밀 ③비제어 우팔 자세 유지(P3 미검증).

**GPS 노브(수렴 정체 시)**: reciprocal 커널(가우시안 대비 수렴↑) · γ=0.84(짧은 지평 recall↑) · freedom 완화(Xu는 max-fret로 내장) · idle 에너지 2배.

## 9. DIGIT 안티패턴 회피 체크리스트

- 게이트 없는 접촉보상 → ✅ 기하 press + 지정손가락 마스크
- 좁은 그래디언트 신호소멸 → ✅ 듀얼스케일 넓은 항
- 손 전체 centroid 이동보상 자충수 → ✅ 기타-상대 세그먼트 거리
- 미정규화 보상합 → ✅ 활성 줄 가중합 뒤 scalar advantage 단일 정규화
- 자유기타 불안정 → ✅ G0 월드고정

## 10. 명시 운지의 리스크·완화

- **GT 운지 없음**([finger-mapping-design §14]): fingermapping은 프록시 검증만 됨. 오배정 시 보상↔물리 충돌.
- **완화**: ①`finger=None`/`t_cut` 진단 구간은 암묵 윈도 마스크로 자동 폴백(§5) ②학습 정체 시 해당 곡 운지 시각화(render_timeline)로 오배정 육안 점검 ③암묵 경로를 코드에 상시 공존 → A/B 진단·회귀 안전판.
- **경로 C 피드백**: 압현 보상이 특정 손가락에서 지속적으로 낮으면 = fingermapping 오배정 후보 → 탭·운지 교정 신호([finger-mapping-design §11]).

## 11. 단계별 계획 + 검증 게이트 (체크리스트)

- [x] **T-a 인터페이스**: task 4-tuple step, rew/value=6, goal128+EMA state33 적용 obs=341,
  actions=33. 13D 손가락 mask goal의 전수 검사와 GPU smoke 통과.
- [~] **T-b 데이터**: GuitarSet GT 기반 S0 파일럿 1곡 생성·검증 완료. 후속으로 20곡 note JSON → fingermapping → `_gen/notes_fingered/` 및 전곡 진단율·finger 커버리지 리포트.
- [x] **T-c goals.py**: 60Hz 로딩+finger/barre+hand target+0/6/15-frame lookahead. CPU shape 및 GPU tick smoke PASS. (곡 윈도 방식 대신 현 S0 frame sequence 채택.)
- [~] **T-d rewards/fret.py**: R1/R2 30/50/20, 실제 pad signed-depth+hysteresis, live fret 구간,
  위치품질, 최고 프렛 승과 free/don't-care+hand/smooth 구현. CPU 기하 검사·GPU 실행 PASS.
  **남음**: 정답 IK 자세에서 임계값·관통/reach 실측.
- [~] **T-e task_fret**: 33 actions·종료·6채널 reward/value·episode F1 조립. **남음**: 새 제어 계약 GPU/장기 스모크·몸통/우팔 유지(P3).
- [~] **T-f 첫 학습(S0 단음)**: signed-depth 기준 1,024env·5,000회 학습 완료. F1=0.598,
  압현 성공률=0.432로 최종 gate는 미통과.
- [x] **T-g 선행 커리큘럼**: 접근·분리 압현·통합 압현·goal pair 구현. 화음·바레는 후속.

## 12. 열린 엔지니어링 결정 (착수 시)

1. finger 관측은 S0에서 줄별 id÷4 + 프렛/바레 + 3시점 룩어헤드로 확정. 목표 위치 직접 관측은 후속 A/B.
2. reward 반환은 task의 `step→(obs,reward,done,info)`로 확정(base 코어는 공유 물리 API 유지).
3. 20곡 변환용 fingermapping 입력 어댑터는 여전히 미정. S0는 GuitarSet GT→전용 builder 사용.

## 13. 참조 인덱스

| 무엇 | 어디 |
|---|---|
| 이식 원본 보상 | `related_work/guitar/env.py:1471-1687` |
| 이식 원본 goal | `related_work/guitar/env.py:1045-1432` |
| base 코어·근거 | `tab2body/env/base.py`, `tab2body/env/README.md` |
| 운지 모듈 | `tab2fingermapping/fingermapping/` (ALGORITHM.md), 설계 `docs/finger-mapping-design.md` |
| 도메인 통계 | `docs/guitar-basics-notes.md` (1~12프렛 91.8%) |
| 함정·결정 | `PROJECT_CONTEXT.md` §3·§4·§7 |
| 안티패턴 | 과거 DIGIT 18차 실패 기록의 요약 (소스 디렉터리는 정리됨) |
| GPS 튜닝 | `related_work/GPS/`, `docs/GPS-paper-ko.md` |
