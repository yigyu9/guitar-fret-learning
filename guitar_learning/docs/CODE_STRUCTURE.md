# 압현 V5 코드 지도

새 압현은 V5를 기준으로 읽는다. 실제 명령은 [README](../README.md), 필드·수식·함수 흐름의 상세는 [V5 코드 해설](../../docs/2026-11-02/코드해설/V5_학습코드해설.md)에 모았다.

## 먼저 읽을 순서

| 순서 | 파일 | 역할 |
| --- | --- | --- |
| 1 | [train.py](../train.py) · [training/launch.py](../training/launch.py) | 기본 명령을 V5 설정·실행으로 연결 |
| 2 | [tool/experiments/compact_press_v5.py](../tool/experiments/compact_press_v5.py) | V5 설정, 정책·환경 연결, 입력·checkpoint 엄격 검증 |
| 3 | [gpu/compact_press_v5.py](../gpu/compact_press_v5.py) | 상태464/473·목표26×8, 접근·대기·유지 프로필, 완료 평가 |
| 4 | [training/compact_press_v5.py](../training/compact_press_v5.py) | 상태·목표 인코더, Actor33, 독립 보상·비용 Critic |
| 5 | [training/finger_skill_runner.py](../training/finger_skill_runner.py) · [training/rollout.py](../training/rollout.py) | 구간/전체 노출, 경험 수집, 학습·저장·재개·평가 |
| 6 | [training/ppo.py](../training/ppo.py) · [training/training_log_io.py](../training/training_log_io.py) | GAE·PPO 갱신, 저널·로그·SHA·저장본 |

```text
train → launch → compact_press_v5 실행 연결
                   ├─ finger_skill_runner → rollout
                   │                         ├─ scene · control
                   │                         └─ CompactPressV5Environment
                   ├─ CompactPressV5Policy
                   ├─ PPO
                   └─ training_log_io · portability
C1~C6: press_sequence → 같은 V5 연결 + 원본 압현 시각 검증
```

## 함께 사용하는 기반

| 영역 | 파일 |
| --- | --- |
| 물리 생성·reset·native tensor | [gpu/scene.py](../gpu/scene.py) |
| 직접 목표각·속도 제한·PD·지지 제어·좌표 변환 | [gpu/control.py](../gpu/control.py) · [core/control.py](../core/control.py) |
| 곡 측정·음별 원장·안전·구간 | [gpu/environment.py](../gpu/environment.py) · [gpu/finger_skill_environment.py](../gpu/finger_skill_environment.py) |
| 패드·엄지·오압현·손목 영역 | [gpu/contact.py](../gpu/contact.py) |
| 손가락 목표 선택·실제 기하각·대기 gate | [gpu/finger_reward.py](../gpu/finger_reward.py) |
| 동시 압현 구간 | [gpu/press_coordination.py](../gpu/press_coordination.py) |
| 제어·접촉·팔/손가락 움직임 진단 | [gpu/episode_diagnostics.py](../gpu/episode_diagnostics.py) |
| 곡·악구·입력 컴파일 | [song/task.py](../song/task.py) · [song/finger_phrases.py](../song/finger_phrases.py) · [score/canonical.py](../score/canonical.py) |
| 초기 자세와 입력 경로·SHA | [runtime/prepared_reset_v1.py](../runtime/prepared_reset_v1.py) · [native/paths.py](../native/paths.py) · [portability.py](../portability.py) |

부모 환경은 공용 물리·접촉·음별 상태를 계산하는 기반이다. 부모 내부의 넓은 관측을 V5가 선택·재조립하며 실제 정책 입력은464/473과26×8이다. 부모의 내부 차원을 별도 선택 가능한 구형 학습 구조로 해석하지 않는다. 메타데이터의 이전 버전 표시는 기존 로그 필드 호환용이며 V5의 최종 계약이 우선한다.

## 별도 영역

타현·전신·CPU 공용 측정과 전처리는 각 목적의 구현을 유지한다. 공용 MLP·목표 결합은 `training/policy.py`에 모으고, V5 이전 이름의 정책 모듈은 제거했다. `train_legacy`의 학습 CLI는 오른손만 허용하며, 남은 왼손 설정·CPU 측정 API를 구형 왼손 학습 실행기로 사용하지 않는다. [타현27](../tool/experiments/right27/README.md), [전신37](WHOLE_BODY_TRAINING.md), [도구](../tool/README.md), [전처리](../../tab2fingermapping/README.md)를 따른다.

전체 Python 수·정적 연결 수·실제 실행 파일 수·checkpoint 입력 SHA 대상은 서로 다른 기준이다. 이번 정리의 수량은 [최종 정리 기록](../../docs/maintenance/v5_project_cleanup_20261104/)에서 확인한다. 이전 코드 해설의 소스 SHA와 검증 원문은 [역사 근거](../../docs/2026-11-02/코드해설/역사근거_20261031/)로 이동해 보존했다.
