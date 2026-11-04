# Framework 근거 색인

확인 기준: **2026-11-04 작업 트리**. 이 색인은 [Overview](01_overview.md), [Model](02_model.md), [Method](03_method.md)의 설명을 직접 구현과 연결한다. 코드 근거는 구현의 존재·계산 의미를 뒷받침하며 학습 성과나 물리 수행 성공을 증명하지 않는다.

## 1. 설계와 구현을 읽는 우선순위

사용자가 작성한 [정리.txt](정리.txt)는 세 정책의 역할과 정보 구성을 정한 원안이다. 해당 파일을 수정하지 않고, 현행 코드에서 확장된 차원과 아직 구현되지 않은 부분을 새 문서에 명시했다. 기본 왼손 실행과 compact 압현 v5, compact 타현은 각각의 실제 진입점과 계약을 기준으로 읽는다.

실행에 적용되는 수치가 공용 클래스 기본값과 다르면 실행기의 덮어쓰기 설정을 따른다. 보상 프로필을 상속하는 환경에서는 해당 실행이 선택한 프로필과 최종 보상 합성식을 함께 확인한다. 과거 TXT·Markdown·그림은 설계 또는 역사 자료로 식별하고 현행 실행값의 직접 근거로 대체하지 않는다.

## 2. 주장별 직접 근거

| ID | 설명 | 직접 구현·설계 근거 | 적용 범위 |
| --- | --- | --- | --- |
| E01 | 세 정책, 전신 목표 입력 생략, 480상태/37행동 원안 | [정리.txt](정리.txt) | 사용자 설계. 전신 학습 구현 증거 아님 |
| E02 | 105축·영범위 8축, 왼팔/손과 오른팔/손의 이름 | [core/control.py](../../guitar_learning/core/control.py) | 축 이름·소유 집합. GPU 실행 제어 수치는 E04 우선 |
| E03 | 인간 Root 고정, 자유 기타, 중력, 의자, 240Hz, 강체·합력 표현 | [gpu/scene.py](../../guitar_learning/gpu/scene.py), [기타 manifest](../../guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json) | 현재 GPU 물리 모델. 자유 Root 균형·현 음향 아님 |
| E04 | GPU 48/57 혼합 구동, LH21 직접 목표각·4rad/s·alpha1, 발 IK·지지·힘 상한 | [gpu/control.py](../../guitar_learning/gpu/control.py) | 실행 제어. core의 과거 프로필 수치와 구분 |
| E05 | 오른손 27축과 39칸 운반 형식, RH21 직접 위치 제어 | [right27/control.py](../../guitar_learning/tool/experiments/right27/control.py), [right27/policy.py](../../guitar_learning/tool/experiments/right27/policy.py) | 타현 단독 정책의 실제 축 배치 |
| E06 | 준비 상태와 손별 초기 스냅샷 | [prepared_reset_v1.py](../../guitar_learning/runtime/prepared_reset_v1.py), [scene.py](../../guitar_learning/gpu/scene.py) | 왼손 v9, 오른손 035/v14. 세 정책 공통 초기화는 미확정 |
| E07 | 압현 원안에서 이어진 상대 좌표·굽힘·기반 관측 블록 | [gpu/compact_press_v5.py](../../guitar_learning/gpu/compact_press_v5.py) | 이전 compact 기반을 단일 V5로 통합한 관측 |
| E08 | 추가 9상태·10목표 필드, 26×8, 동시 유지 보상과 엄격한 유지 | [gpu/compact_press_v5.py](../../guitar_learning/gpu/compact_press_v5.py), [press_coordination.py](../../guitar_learning/gpu/press_coordination.py) | 활성 목표 집합별 all-clean 및 음 전체 유지 |
| E09 | 이전 v4 combined에서 이어진 접근·줄 정렬·대기 가중치·자세 품질 | [gpu/compact_press_v5.py](../../guitar_learning/gpu/compact_press_v5.py) | 상속 사슬을 제거하고 단일 V5 안에 통합한 보상 기반 |
| E10 | 압현 v5 464/473, 준비 맥락12, 네 개선 조건, 해제 완료 | [gpu/compact_press_v5.py](../../guitar_learning/gpu/compact_press_v5.py) | 학습 달성 문턱과 strict 유지·release 평가 분리 |
| E11 | 압현 상태/목표 인코더, 결합768, actor33, 별도 reward/cost 가치망 | [training/policy.py](../../guitar_learning/training/policy.py), [compact_press_v5.py](../../guitar_learning/training/compact_press_v5.py) | 목표 인코더는 슬롯 간 공유, actor/critic은 분리 |
| E12 | 손가락별 tracking/next, 최초 준비·대기·연속 접촉 예산 | [gpu/finger_reward.py](../../guitar_learning/gpu/finger_reward.py), [finger_skill_environment.py](../../guitar_learning/gpu/finger_skill_environment.py) | 현재 또는 준비 목표의 선택과 예산 |
| E13 | 압현 기하 후보·오압현 v3 | [gpu/contact.py](../../guitar_learning/gpu/contact.py) | 패드 표면과 몸체 합력. 개별 현 압력 아님 |
| E14 | 음별 접촉/clean 기록, 해제 필요성, 공통 물리 실패·비용 | [gpu/environment.py](../../guitar_learning/gpu/environment.py) | 압현 종료 비용 대체는 E15 확인 |
| E15 | 압현 9개 보상 합성·균형 가중치·손목 종료·남은 비용 정산 | [gpu/finger_skill_environment.py](../../guitar_learning/gpu/finger_skill_environment.py) | 현재 단일 V5의 override와 함께 읽음 |
| E16 | 원음·누름·타현 계획의 정본과 실행 시간표 | [score/canonical.py](../../guitar_learning/score/canonical.py), [song/task.py](../../guitar_learning/song/task.py) | 일반 곡 입력. 합성 압현 동시 시각은 E17 적용 |
| E17 | C1~C6 등록·검사, 원시 onset 보존, v5 실행 연결 | [prepare_press_targets.py](../../guitar_learning/tool/prepare_press_targets.py), [press_sequence.py](../../guitar_learning/tool/experiments/press_sequence.py) | 실행마다 한 조합. 자동 여섯 목표 혼합 아님 |
| E18 | 겹침 그룹을 보존하는 부분 구간과 손가락 균형 선택 | [song/finger_phrases.py](../../guitar_learning/song/finger_phrases.py) | 압현 구간 학습. P 번호를 직접 읽는 선택기 아님 |
| E19 | 타현 목표 검증, 원음 대응, 단일·스트럼 시계 | [song/strike_task.py](../../guitar_learning/song/strike_task.py) | 타현 단독 과제, 왼손 성공과 별개 |
| E20 | 타현 상태450·목표79×2, 피크·줄 교차·재무장·완료 | [gpu/compact_strike.py](../../guitar_learning/gpu/compact_strike.py) | 자유 기타의 기하·시각·방향 판정 |
| E21 | 스트럼 순서, 오류·준비 자격·회복·중복 지급 방지 | [gpu/strike_events.py](../../guitar_learning/gpu/strike_events.py) | 이벤트 원장. 최초 준비 자격의 에피소드 상속 |
| E22 | 타현 S3 항별 계산과 실패 tick 보상 대체 | [gpu/strike_reward.py](../../guitar_learning/gpu/strike_reward.py) | 과거 계수 계승, 모든 식이 과거와 같지는 않음 |
| E23 | 타현 상태450→256, 목표79→64, 결합384, actor27 | [training/compact_strike.py](../../guitar_learning/training/compact_strike.py) | size 옵션과 무관한 고정 폭 |
| E24 | 정책/물리 주기, H32 수집, 부분 reset | [training/rollout.py](../../guitar_learning/training/rollout.py) | 60Hz 제어 안의 네 물리 계산, 환경 상태 연속 |
| E25 | GAE, clipped PPO, 비용 우위, 별도 가치 갱신, KL 복구 | [training/ppo.py](../../guitar_learning/training/ppo.py), [training/launch.py](../../guitar_learning/training/launch.py) | GPU 실행의 λ0.98·minibatch4096, 엔트로피 보너스 없음 |
| E26 | 최초 예산25% 후 다음 reset부터 전체, 운영·평가·재개 | [training/finger_skill_runner.py](../../guitar_learning/training/finger_skill_runner.py) | 성공률 기반 일정이 아님. 물리 중간 상태 재개 아님 |
| E27 | v5 개선 조건·초기std·엄격한 저장 계약 | [experiments/compact_press_v5.py](../../guitar_learning/tool/experiments/compact_press_v5.py) | 초기 잠재std .15/.35, 목표·보상 변경의 암묵 재개 금지 |
| E28 | 타현 단독 학습·평가·영상과 설정 | [experiments/compact_strike.py](../../guitar_learning/tool/experiments/compact_strike.py) | 고정 S3, 별도 압현 커리큘럼 없음 |
| E29 | 기본 학습 진입점의 V5 연결과 공용 MLP·인코더 | [training/policy.py](../../guitar_learning/training/policy.py), [training/launch.py](../../guitar_learning/training/launch.py) | 이전 557상태 기본 경로는 [과거 이력](../../docs/history/press_before_v5.md)으로 구분 |
| E30 | CPU의 전신 목표·유지 계약 | [core/whole_body_control.py](../../guitar_learning/core/whole_body_control.py) | 37축 학습 전신 정책의 존재를 뜻하지 않음 |

## 3. 문서에서 주장하지 않는 것

37축 독립 정책·480상태 조립·전신 보상·세 정책 동시 PPO·97축 통합 행동 배치는 설계 항목이다. 이름에 whole body가 포함된 기존 제어 코드만으로 이 구현이 완료됐다고 판단하지 않았다. 전신 보상식의 가중치는 제안 변수이며 적용값을 만들어 넣지 않았다.

압현의 물리 후보, 타현의 기하 통과, 준비 자세의 유지, 입력 규칙 검사, 학습 업데이트, 전체 목표의 실제 성공은 서로 다른 근거를 필요로 한다. 본문에는 새 성공률·성능 개선 수치를 추가하지 않았다. 기존 그림은 [그림 안내](images/README.md)의 당시 범위로 보존한다.

## 4. 문서 검증 기록

이번 변경은 문서만 작성하며 학습 소스와 실행 입력을 수정하지 않는다. [작업 전 목록·SHA](../../docs/plans/framework_rewrite_20261104_before.json)로 TXT 3개와 기존 매체·JSON의 보존을 대조한다. 참조 파일 SHA와 링크·수치 점검, 독립 검수의 결과는 [이번 코드 snapshot](code_snapshot_20261104.json)에 기록한다.

[source_snapshot.json](source_snapshot.json)은 이전 2026-11-02 기록이므로 이번 근거 SHA와 혼합하지 않는다. 문서 snapshot은 확인 시점의 코드 식별용이며, 실행 중인 실험의 봉인·체크포인트 identity 검증을 대체하거나 완화하지 않는다.
