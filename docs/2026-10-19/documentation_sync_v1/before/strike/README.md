# strike — 오른손 타현 연구 안내서

> **최종 갱신 — 2026-09-11:** 현재 기본은 30 action/303 observation Strike-v2,
> `strike_plan.v4`, checkpoint/environment state v14, curriculum state v16이다.
> 완료 이후 품질 감시와 고정 사례 반복 평가를 추가했다(세부 내용은 학습 안내서 참고).
> 기존 실패 환경은 복원하지 않고 `[time, frame, string]`
> pick-only source, phrase 방향 계획, A0→A4→S0→S3 성능 curriculum으로 새로 구현했다.
> 입력 provenance 감사, traversal-edge 원속도 가능성 검사와 방향 반전 clearance recovery를
> 추가했다. 과거 smoke 산출물은 현재 계약과의 혼동을 막기 위해 제거했으며, 배관 검증은 현재 코드의
> `python -m tab2body.train --task strike --smoke`로 재실행한다. 장시간 학습 성능과 사람다운
> 동작 여부는 별도 재검증 대상이다.

이 디렉터리는 tablature의 onset을 전신 휴머노이드 오른손의 실행 가능한 타현으로 바꾸기 위한 규칙,
학습 순서, 검증 기준을 모은 문서 허브다. 삭제 전 구현과 실패 실험은 설계 근거로만 보존한다.
현재 실행 정본은 `tab2body/strike_cfg.py`, `env/tasks/task_strike.py`,
`env/strike_{goals,detector}.py`, `learning/strike_{curriculum,evaluation}.py`다.

## 연구를 한 문장으로

곡의 sound-onset 후보를 실제 오른손 공격 여부와 phrase-level 주법 계획으로 변환하고, 피크 또는 지정
손가락이 준비·접근·release·회복을 거쳐 올바른 줄만 자연스럽게 타현하도록 오른쪽 어깨
띠·팔·손목·손을 물리 제어한다.

## 전체 흐름

```text
notes.t_on (sound-onset candidate)
  ↓
① 입력 근거·품질 감사
   fingering/raw/JAMS 차이, 묶음 경계와 원속도 traversal-edge 가능성을 검사
  ↓
② StrikeIntent
   이 onset에 실제 오른손 공격이 필요한지 true/false/unknown 해결
  ↓
③ phrase-level StrikePlan
   hand setup, agent, 방향, 주법, microtiming, strike lane과 다음 동작 관계를 결정
  ↓
④ 물리 타현
   goal-independent detector가 유효 swept crossing에서 RELEASE를 내고 matcher가 목표에 일대일 배정
  ↓
⑤ 곡별 반복 학습과 검증
   단현에서 전환·스트럼·전체곡으로 확장하고 정확도·안전·자연스러움 분포를 각각 평가
```

## 읽는 순서

1. [사람이 먼저 읽는 짧은 규칙](QUICK_RULES.md)
2. [현재 오른손 구현 규칙 정본](RIGHT_HAND_RULES.md)
3. [과거 Strum·양손 동기화 확장안](archive/RIGHT_HAND_EXTENSIONS.md)
4. [제공 규칙 R1~R28 반영표](archive/RULE_TRACEABILITY.md)
5. [goal과 이벤트 계약](01_goal_contract/README.md)
6. [SourceNote → StrikeIntent → StrikePlan 입력 아키텍처](01_goal_contract/GOAL_ARCHITECTURE.md)
7. [구절 단위 StrikeMapper 결정 규칙 C1~C48](01_goal_contract/MAPPER_RULES.md)
8. [물리 타현 규칙](02_physical_control/README.md)
9. [사람다운 상세 운동 규칙 N1~N90](02_physical_control/NATURAL_MOTION_RULES.md)
10. [Strike 영역 정의와 시각화](02_physical_control/strike-zone.md)
11. [하위 상세 규칙 S1~S60](02_physical_control/rules.md)
12. [규칙별 구현·통합·진단·보류 판정표](IMPLEMENTATION_CHECKLIST.md)
13. [2026-08-03 코드 정리·검증 보고서](archive/CODE_AUDIT_2026-08-03.md)
14. [기존 guitar 연구의 pick 구현 분석](90_references/LEGACY_GUITAR_PICK_ANALYSIS.md)
15. [학습·평가 계획](03_training/README.md)
16. [학습 개선 이력과 중복 방지표](03_training/EXPERIMENT_HISTORY.md)
17. [보류 항목](04_deferred/README.md)

## 현재 상태

| 항목 | 상태 | 의미 |
|---|---|---|
| 규칙·연구 문서 | 갱신 | 현재 Strike-v2와 역사적 확장을 구분 |
| 실행 환경 | Strike-v2 CPU·GPU PASS | 30 action, v2 303 observation, path-aware clearance recovery |
| 학습 진입점 | 구현 | `python -m tab2body.train --task strike` |
| checkpoint | 새 schema 구현 | 과거 checkpoint와 호환하지 않음 |
| 과거 결과 | 로그·영상만 보존 | 500회 pilot 실패 원인 비교용 |
| 새 입력 계약 | 구현·CPU PASS | raw v3 provenance/검수 → single/strum/direction/microtiming/edge-feasible StrikePlan |
| detector | CPU PASS·과거 CUDA PASS | 유한 crossing, RELEASE, re-arm, zone |
| A0~S3 runtime | CPU 계약 PASS·A0 smoke/A1 학습 PASS | 방향 반전 lift/transfer, recovery/music 방향 분리 관측 |
| 학습·복원·산출물 배관 | historical PASS | 현재 코드는 smoke로 재검증 |
| 장시간 PPO | 재검증 필요 | 과거 5,000회 기록은 비교용 historical record |

## 현재 설계 범위

- **현재 타현 주체**: `pick`만 실행한다. `thumb/index/middle/ring/pinky`는 후속 schema 확장이다.
- **타현 면**: 피크, 손톱, 손가락 살(`pick/nail/flesh`). 현재 손 에셋은 손톱을 별도 geometry로
  구분하지 않으므로 손가락 identity까지 물리 감독하고 nail/flesh는 annotation·후속 확장으로 보존한다.
- **현재 이벤트 종류**: pick `single`과 연속 줄 `strum`. 같은 줄 alternate restrike와
  여러 손가락 `multi_pluck`은 보류한다.
- **조합**: pick+middle/ring 같은 hybrid picking도 한 event의 여러 target-agent 쌍으로 표현한다.
- **후속**: palm mute, slap/tap, rasgueado, 줄의 탄성·진동·음향 합성. 새 detector/라벨이 필요한
  주법이며 일반 pluck/strum으로 억지 환원하지 않는다.
- 데이터에 타현 주체가 없으면 임의로 손가락을 발명하지 않는다. 곡/실험 설정에서 기본 주체를 명시해
  resolve한 뒤 학습하며, 미해결 `unspecified` goal은 물리 학습 입력으로 거부한다.
- `notes.t_on`은 새 음향 onset 후보이지 항상 오른손 strike가 아니다. legato 여부가 불명확하면
  `requires_rh_attack=unknown`으로 남겼다가 명시 profile/annotation으로 해결한다.
- `presses[].strikes`는 개방현이 빠지는 왼손 press projection이므로 오른손 source로 사용하지 않는다.

## 고정 규약

- 기타 로컬축: `+x_g=6번줄(low-E)→1번줄(high-e)`, `+y_g=브리지→너트`,
  `+z_g=기타 앞/줄 바깥쪽`.
- Isaac 줄 index: `0=G:string1=high-e`, `5=G:string6=low-E`. CSV의 `0=low-E`와 반대다.
- `down`은 연주자 기준 6번줄→1번줄, 즉 Isaac index `5→0`과 기타 로컬 `+x_g` 방향이다.
  `up`은 그 반대인 `0→5`, `-x_g`다.
- 제어는 `R_Shoulder/R_Elbow/R_Wrist` 9 DOF와 `RH:*` 21 DOF, 합계 30 action을 기준으로 한다.
  `R_Thorax`는 정책 action에서 제외하고 seated init PD로 유지한다. 실제 런타임 열거 결과가 다르면
  조용히 맞추지 말고 계약 오류로 중단한다.
- 줄은 비충돌 marker다. 타현 성공은 접촉력이 아니라 피크 점 또는 지정 손가락 fingertip pad의
  두 프레임 사이 swept geometry로 판정한다.
- 타현은 지속 상태가 아닌 **소모되는 이벤트**다. 한 교차는 최대 한 목표에만 배정되고, 한 목표는
  최대 한 번만 성공한다.
- 현재 공개 운동 phase는 `READY→APPROACH→RELEASE_RECOVER` 세 개다. detector 내부 중복 방지는
  별도의 `ARMED→RELEASE pulse→WAIT_REARM→ARMED` 상태로 관리한다. CONTACT/LOAD는 pick S0의 필수
  phase가 아니며 fingerstyle 또는 물리 pick의 후속 진단으로만 남긴다.
- 정상 곡 종료와 실패 종료를 구분한다. 현재 `−10`은 안전·비유한·미완료 회복 실패에만 적용한다.

## 구현 산출물

- 원본 입력과 실행 계획:
  `data/song_bundles/<song_id>/training/strike_training.json`, `strike_plan.json`
- 곡별 입력 구조와 `--song` 선택:
  [`data/song_bundles/README.md`](../data/song_bundles/README.md)
- grip 정본: [`pick-grip-reference.json`](02_physical_control/pick-grip-reference.json)
- GPU runtime audit JSON은 역사 산출물로 정리했다. 현재 검증은 공용 `--smoke` 실행 폴더의
  `run_manifest.json`·로그·평가 JSON을 기준으로 한다.
- CPU/CUDA 검사: `tab2body/tests/test_strike_*.py`
- 전 단계 GPU 진단: `tab2body/tools/audit_strike_runtime.py`
- 학습 정책 운동·안전 진단: `tab2body/tools/audit_strike_motion.py`
- 학습 진입점: `tab2body/train.py --task strike`
- 태스크 실행기: `tab2body/train_fret.py`, `tab2body/train_strike.py`
  (동일 `build_parser()`·`main()` 인터페이스)
- 종료 영상: `tab2body/tools/record_strike_rollout.py`
- 영역·가상 피크 표시 영상: `tab2body/tools/record_strike_visualized_rollout.py`
- 학습곡선: `tab2body/tools/plot_strike_training.py`
- clean-recovery와 후속 변경 근거: [`03_training/EXPERIMENT_HISTORY.md`](03_training/EXPERIMENT_HISTORY.md)

## 문서 판단 우선순위

충돌 시 `master_plan → 실제 구현·자동 검사 → RIGHT_HAND_RULES.md → status.md →
하위 S/N 규칙 → 과거 설계 초안` 순서로 판단한다. `RIGHT_HAND_EXTENSIONS.md`는 strum 도입 전
확장안의 역사 기록이다. 접촉력·물리 pick 항목은 명시적으로 승격되기 전까지
현재 실행 계약이 아니다.
