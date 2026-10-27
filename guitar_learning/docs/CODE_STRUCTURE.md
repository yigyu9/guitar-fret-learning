# 메인 코드와 도구의 배치

기본 학습은 GPU 왼손 `finger-skill` v2다. `python -m guitar_learning.train --out NEW`에서 시작하며 family 옵션을 생략할 수 있다. 실행 환경·명령·재개는 [README](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다.

## 기본 실행 흐름

```text
train.py
  → training/start.py                    기본 왼손 GPU CLI, v2만 허용
  → training/launch_settings.py          공용 곡·설정 생성과 검증
  → training/finger_skill_runner.py      J 공동 학습, 저장·엄격 재개·평가
      → training/gpu_pool.py            GPU 장면·환경 구성
          → gpu/simplified_finger_environment.py  9개 보상·종료·561상태
          → gpu/finger_skill_environment.py      구간 선택·공통 finger-skill 환경
          → gpu/environment.py · scene.py        배치 물리·측정·공용 원장
      → skills/finger_skill_policy.py    지지17/손가락16 분기, J33 활성 축
      → training/finger_decisions.py    독립 K1 결정·H32 수집
      → training/decision_ppo.py         PPO 갱신
      → training/finger_skill_curriculum.py      구간→전곡 노출 일정
      → training/gpu_log_records.py     에피소드·checkpoint 기록
```

기본 실행은 구형 song runner나 `tool/` 실행기를 거치지 않는다. `finger_skill_runner.py`와 기반 환경·정책은 v24 도구도 사용하므로 활성 라이브러리로 유지한다. 새 기본 경로에는 R/F 단계 통과·전문가 모델·BC가 필요하지 않다. 구간 학습 중에도 원곡 음 식별자를 보존하고, 원래 전이 예산의 25% 이후 다음 reset부터 전곡으로 전환한다.

## 공용 라이브러리

| 위치 | 역할 |
| --- | --- |
| `training/` | 현행 시작·설정·수집·PPO·노출 일정·저장·재개; CPU/전문 경로가 사용하는 공용 runner도 유지 |
| `gpu/` | GPU 장면·제어·측정·환경·충돌 필터·진단 |
| `skills/` | finger-skill 정책과 기존 전문 정책·행동 분배 |
| `song/` | 검수된 곡 일정·음별 원장·보상/종료에 필요한 공용 측정 |
| `core/` · `runtime/` | 공통 제어·안전·초기 자세 복원·native 기반 |
| `native/` · `assets/` | 실제 장면·모델·제어·준비 상태·출처 |
| `score/` · `music_task.py` | 곡 입력 읽기·정본화·목표 자료형 |
| `historical_inputs.py` | 과거 입력 원문·경로·SHA·CAS 검증 |
| `timing/` · `quality/` · `imitation/` | 현재 공유 의존성과 전문 학습 기반 |
| `tests/` | 설정·제어·보상·종료·저장·경로 회귀 검사 |
| `docs/` | 현행 안내와 전문 단계별 계약 문서 |
| `archive/` | 변경 전 원문과 manifest; 활성 코드의 import 대상이 아님 |

이름에 이전 버전이 있어도 현행 상속·호출·계약에서 필요한 모듈은 남긴다. `music_task.py`, `song/task.py`, `song/__init__.py`는 기존 checkpoint의 원문 검증 대상이므로 그대로 보존한다.

## 별도 실행 도구

| 위치 | 역할 |
| --- | --- |
| `tool/training/train_legacy.py` | 기존 song·CPU/오른손·finger-skill-v24 CLI |
| `tool/training/legacy_gpu_runner.py` | 기존 song 전용 GPU 학습 실행기 |
| `tool/evaluation/evaluate_finger_skill.py` | v2/v24 저장 계약에 따른 구간·전곡 평가 |
| `tool/demonstration/render_finger_skill.py` | 저장 계약의 실제 물리 평가·손/전신 영상 |
| 기타 `tool/training/` · `tool/evaluation/` · `tool/demonstration/` | 기존 단계별 학습·평가·시연 |
| `tool/validation/` | 압현 도달·접촉·제어 진단 |
| `tool/experiments/` | 전문 양손·전곡·전환·정밀화·회복 실험 |
| `tool/`의 입력·운영 도구 | 곡 등록·전처리·검수·타임라인·로그 점검 |

[도구 안내](/home/ajou/yigyu/3/guitar_learning/tool/README.md)를 따른다. 기존 `training/gpu_runner.py`의 song 실행 코드는 `tool/training/legacy_gpu_runner.py`로 이동했고, 기본 `training/start.py`는 v2만 실행한다. 구형 재현을 위해 archive를 import하거나 strict checkpoint 검증을 우회하지 않는다.

## 보관과 문서

[변경 전 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/manifest.json)에 원래 경로와 SHA를 기록했다. [이전 코드 배치 문서](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/guitar_learning/docs/CODE_STRUCTURE.md)는 과거 실행 흐름의 설명으로 보존한다.

[LOGGING](/home/ajou/yigyu/3/guitar_learning/docs/LOGGING.md)은 공용 기록 해석, [CODE_LINEAGE](/home/ajou/yigyu/3/guitar_learning/docs/CODE_LINEAGE.md)는 원구현 계보를 설명한다. TRAINING·SPECIALIST_TRAINING·SKILL_CURRICULUM·IMITATION_TRAINING·TIMING_TRAINING·ACTIONABLE_PREPARATION·MUSICAL_QUALITY 문서는 각 전문 단계의 계약이며 새 기본 학습의 선행조건이 아니다.
