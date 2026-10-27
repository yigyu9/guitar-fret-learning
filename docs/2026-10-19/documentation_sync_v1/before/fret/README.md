# fret — 왼손 운지 연구 안내서

> 최종 갱신: 2026-09-07 — Fret-v2 기본 계약 반영

이 디렉터리는 왼손 운지 연구의 결정, 학습 방식, 현재 결과를 정리한 문서 허브다.

## 연구를 한 문장으로

탭에 적힌 줄·프렛을 사람이 연주할 법한 손가락에 배정하고, 그 운지대로 전신 휴머노이드의 왼손이 실제 기타를 누르게 학습한다.

## 전체 흐름

```text
탭의 음표
  ↓
① 운지 결정
   어느 손가락으로 누를지, 손을 어디에 둘지, 언제 미리 누르고 뗄지 결정
  ↓ presses
② 물리 압현
   지정 손가락이 목표 줄·프렛을 누르도록 Isaac Gym 환경에서 제어
  ↓ reward / observation
③ 곡별 반복 학습과 검증
   한 곡 전용 정책을 PPO로 반복 최적화하고 정확도·관통·관절 안전·자연스러움을 평가
```

## 읽는 순서

fret 학습이 처음이라면 이 문서와 [현재 학습·실행 계약](03_training/README.md)을 먼저 읽는다.
`archive/FRET_LEARNING_GUIDE.md`는 Fret-v1 당시의 상세 학습 설명을 보존한 역사 문서다.

그 뒤 연구의 세 영역을 아래 순서로 보면 된다.

1. [운지 결정 이해하기](01_finger_mapping/README.md)
2. [물리 압현 이해하기](02_physical_control/README.md)
3. [학습과 현재 결과 이해하기](03_training/README.md)

결정을 미룬 항목은 [보류 항목](04_deferred/README.md)에 따로 모아 두었다.

각 현재 디렉터리의 `README.md`가 안내와 계약의 진입점이다. 과거 설계·실험 문서는 `archive/`에 보관하며 현재 계약으로 사용하지 않는다.

## 현재 상태

| 단계 | 상태 | 의미 |
|---|---|---|
| 운지 결정 | v0 구현 완료 | 교본 운지·앵커·바레·선행 계획을 처리하며 rock3에서 생체역학 위반 0 |
| Fret-v2 물리 학습 | 진행 중 | 30-action/420-observation 환경 구현, 곡별 커리큘럼 checkpoint 생성 |
| 물리 안전 검증 | 핵심 조건 구현 | checkpoint contract와 안전 진단을 사용하며, 구 smoke·구 checkpoint는 제거함 |
| 곡별 반복 커리큘럼 | 구현 완료 | 같은 곡 내부 coverage → integration → 전체곡 연주 |
| 화음·바레 | 후속 단계 | 현재 S0는 암묵 바레와 동일 손가락 다중 줄 목표를 로딩 단계에서 거부하며, 명시적 바레 확장 흔적만 보존 |

현재 기본 인터페이스는 `Fret-v2: 30 action / 420 observation / 6 reward-value`다. 관측은
`O_proprio60 + O_arm_anchor18 + O_hand_geometry60 + O_current_event45 + O_target_geometry24 +
O_finger_transition52 + O_lookahead72 + O_readiness_contact45 + O_phase12 + O_synchronizer2 +
O_history30`의 named block으로 봉인한다. Fret-v1 425D는 명시적 호환 baseline일 뿐 새 주 학습의
기본값이 아니다. 정책은 block encoder actor-critic, bounded action과 EMA를 사용한다.
체크포인트는 제어 순서, 관측 manifest, 보상, 안전 설정, 곡 데이터와 코드 지문이 모두 맞아야 로드된다.
R22 손가락 capsule 겹침은 아직 진단 전용이다.

2026-09-01부터 `L_Thorax` 3DOF는 정책 행동에서 제외하고 초기 자세의 PD target으로 유지한다.
따라서 기존 33-action checkpoint는 호환하지 않으며 새 정책을 처음부터 학습한다.

`fret/training/runs/20260803_*`는 이전 33-action 배관의 역사 기록으로만 보존한다. Fret-v2에서는
재개·평가하지 않는다. 새 30-action 학습은 별도 run으로 생성한다. 다른 곡은 같은 규칙으로
별도 정책을 반복 학습한다. 새 곡의 즉시 일반화는 목표가 아니다.

## 디렉터리 구조

```text
fret/
├── README.md                    이 문서: 전체 안내
├── 01_finger_mapping/           탭 → 손가락·포지션·presses
├── 02_physical_control/         presses → 실제 왼손 압현
├── 03_training/                 PPO 학습·평가·현재 결과
├── 04_deferred/                 학습 결과를 기다리는 보류 항목
├── training/                    실제 곡별 학습 실행 산출물과 보관 규칙
├── archive/                      Fret-v1 과거 설계·실험 기록
└── renders/                     프렛 작업에서 생성한 이미지·영상
```

## 자주 헷갈리는 규약

- 손가락 번호: 1=검지, 2=중지, 3=약지, 4=소지. 엄지는 압현 손가락이 아니다.
- CSV에서는 `string 0=low-E`, Isaac frame goal에서는 `index 5=low-E`다.
- 현재 기타 에셋의 왼손 목표 fret은 정수 `−1`, `0`, `1..22`만 허용한다. 각각 NO_PRESS,
  DONT_CARE, PRESS이며 23프렛 이상이나 암묵 바레 goal은 로딩 즉시 오류다.
- `fret=0` DONT_CARE는 음향 판정만 자유이며 관통·관절·과압 등 물리 안전은 면제하지 않는다.
- 기타 로컬축은 `+x=6번줄→1번줄`, `+y=브리지→너트`, `+z=지판 바깥쪽`이다.
- 음의 시작 시각과 손가락을 누르는 시각은 다르다. 기본적으로 타현 0.12초 전에 누르기 시작한다.
- 운지 알고리즘이 생체역학적으로 가능한 goal을 만들었다고 해서 물리 모델이 안전하게 수행했다는 뜻은 아니다.

## 상세 참고

- [Fret 압현 학습: 처음부터 끝까지](archive/FRET_LEARNING_GUIDE.md)
- [Fret 학습 실험 이력과 중복 방지표](../docs/archive/dated/2026-08-24/FRET_EXPERIMENT_HISTORY.md)
- [프로젝트 결정과 현재 상태](../PROJECT_CONTEXT.md)
- [간단 작업 보고서](archive/WORK_REPORT.md)
- [기타 연주 기초](../docs/guitar-basics-notes.md)
- [코드 구조](../tab2body/STRUCTURE.md)
- [학습 실행 폴더와 산출물 관리](training/README.md)
- 과거 `fret/renders/` 진단 이미지는 현재 저장소에 없으므로 현재 성능 근거로 링크하지 않는다.

문서가 충돌하면 `master_plan → 현재 코드·자동 계약 검사 → 03_training → 역사 문서` 순서로 판단한다.

학습 실행 명령은 [Fret 학습 문서](03_training/README.md)와
[`tab2body/TRAINING.md`](../tab2body/TRAINING.md)를 따른다.
