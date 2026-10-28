# 기본 학습 코드 추가 통합

기본 GPU 왼손 finger-skill v2의 구현을31개에서24개로 줄였다. 이름만 연결하는 facade를 남기지 않고 실제 구현을 옮겼다. 기존 파일을 오가며 읽던 자료형·일정·기하·입력·저장을 역할별 파일 안의 구역으로 모았다.

| 기준 | 직전 | 현재 |
| --- | ---: | ---: |
| 기본 경로 구현 | 31 | 24 |
| 연결된 패키지 초기화 | 9 | 8 |
| 기본 정적 연결 전체 | 40 | 32 |
| 활성 Python 전체(archive 제외) | 487 | 480 |

정적 연결은 조건·함수 안 import까지 포함한다. 모든 파일의 모든 함수가 기본 학습에서 실행된다는 뜻은 아니다. 보관본과 학습 결과 파일은 활성 Python 수에 넣지 않았다.

## 통합 위치

| 이전 구현 | 현재 실제 구현 |
| --- | --- |
| `music_task.py`, `song/task.py`, `song/wrist_guide.py` | [song/task.py](/home/ajou/yigyu/3/guitar_learning/song/task.py): 목표 자료형·원장·전곡 일정·손목 기준 |
| `score/canonical.py`, `score/events.py` | [score/canonical.py](/home/ajou/yigyu/3/guitar_learning/score/canonical.py): 시간표 컴파일·과제 입력 |
| `song/left_curriculum.py`, `song/gpu_left_curriculum.py` | [song/curriculum.py](/home/ajou/yigyu/3/guitar_learning/song/curriculum.py): 명시적으로 구분한 CPU/GPU 설정·상태 |
| `training/recording.py`, `training/training_log_io.py` | [training/training_log_io.py](/home/ajou/yigyu/3/guitar_learning/training/training_log_io.py): 소스·SHA·JSON부터 저널·운영까지 |
| `gpu/geometry.py`의 회전·상대속도6함수 | [gpu/control.py](/home/ajou/yigyu/3/guitar_learning/gpu/control.py) 앞부분 |
| `gpu/geometry.py`의 표면·압현면·손목10함수 | [gpu/contact.py](/home/ajou/yigyu/3/guitar_learning/gpu/contact.py) 앞부분 |
| `native/paths.py`, `native/lower_body_release_v1/common.py` | [native/paths.py](/home/ajou/yigyu/3/guitar_learning/native/paths.py): 내부 입력 경로·105축 기준·봉인 |

CPU/GPU의 상태 길이27/3331·가중치·판정은 그대로 두고 클래스·설정·상수 이름만 `CPULeftCurriculum`/`GPULeftCurriculum`, `cpu_default_config`/`gpu_default_config`, `CPU_*`/`GPU_*`로 구분했다. 이름이 겹치는 손목·악보 스키마는 `WRIST_GUIDE_SCHEMA`, `EVENTS_SCHEMA`로 구분했다. 스키마 문자열 값은 유지했다.

GPU 공통 회전을 control에 두어 contact→finger_reward의 순환 import를 피했다. CPU 손목 계산의 NumPy와 frame은 사용 시 import하여 악보·입력 모듈이 무거운 물리 라이브러리를 가져오지 않도록 했다. 계산·보상·종료·PD·행동·PPO 설정은 유지했다.

## 참조·입력 보존

현재 학습·도구·검사의 import와 패치 대상, 현재 물리/분류 소스 pin을 새 위치로 갱신했다. 고정된 과거 체크포인트 이전 허용 목록과 CAS의 과거 경로·원 SHA는 바꾸지 않았다. 해당 구형 이전 도구는 삭제되거나 바뀐 현재 소스를 계속 거부한다. 없는 파일도 명시적인 검증 오류로 처리한다.

native의 원래 경로·원본 SHA를 보존했다. 합쳐진 common의 내부 위치는 paths로 바꾸고 현재17개 출처 행의 SHA를 갱신해190개 전체 출처 검증을 통과했다. 실제 물리 자산·준비 스냅샷은 바꾸지 않았다.

다른 창에서 완료한 train.py·launch.py 상단 설명문 삭제는 보존했다. 해당 상태도 최종 소스480개 SHA와 GPU 검증에 포함했다.

수정 전 Python487개와 문서·코드해설·provenance를 포함한538개 파일은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_learning_consolidation_v2/manifest.json)에 원래 경로·SHA와 함께 보존했다.

## 검증

| 검사 | 결과 |
| --- | --- |
| 구문·내부 import·정적 경로 | 활성480개 검사, 기본24+8개 확인 |
| 이동 정의·상수 | 작업자 AST 검사 및 독립 검수에서 명시한 이름·import·출처 이동 외 계산 동일 |
| 정책9조건 | 초기화·RNG·행동·확률·가치·가치망 매개변수 순서 정확히 일치 |
| JSON | 실수1,012개 × 옵션5종, NumPy·gzip·사용자 인코더·해시·원본과 동일 |
| 곡·초기 입력 | 66이벤트→67목표·1969tick·목표/일정 해시 및105축 복원 동일 |
| 전체 CPU | 188모듈·1,318건,157모듈 통과·기존31모듈 실패 유지. 최종 신규/변경 실패0 |
| GPU 새 학습 | 2환경/H8/2회·32전이·optimizer2 완료 |
| GPU 엄격 재개 | 추가1회·16전이·optimizer3 완료 |
| GPU 입력·종료 감사 | 변경 입력·누락 pin·정리 오류0, GPU 장면 정상 종료 |
| 독립 검수 | 수정 필요 문제 없음 |

CPU는 전부 통과한 상태가 아니다. 기존31개 실패 모듈에는 구형 계약 fixture·이미 없어진 과거 산출물·고정 소스 SHA를 요구하는 검사 등이 포함된다. 이번 첫 검사에서 삭제된 events.py를 현재 출처로 요구한 test_internal_score가 실패해 기대 출처를 실제 통합 파일로 갱신하고, 모든 현재 출처가 존재하는지 추가 확인했다. 해당5건 재실행은 통과했고 나머지 최종 결과는 변경 전과 같다. [전후 비교](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/test_comparison.json) · [전체 출력](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/cpu_test_output.txt).

GPU 검사는 실행·저장·복원 연결의 짧은 확인이며 장기 연주 성능 향상 검증은 아니다. 기존 체크포인트는 소스 경로·SHA가 달라 현재 트리에서 바로 재개·평가되지 않을 수 있다. 기존 검증을 완화하지 않고 새 소스로 만든 저장본의 엄격 재개를 확인했다.

[검증 요약](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/validation.json) · [독립 검수](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/review_findings.md) · [GPU 검사](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/gpu_verification.json) · [모듈 이동표](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/module_mapping.json) · [검증 소스 SHA](/home/ajou/yigyu/3/docs/2026-10-28/guitar_learning_consolidation_v2/source_freeze.json)

## 현재 코드를 읽는 방법

핵심 흐름은 `train.py` → `training/launch.py` → `training/finger_skill_runner.py` → `training/rollout.py`다. 정책·PPO·공용 환경·현재 자식 환경은 독립적으로 읽을 수 있도록 유지했다.

[코드해설 목차](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md)의 역할별 본문·파일 대응표·소스 SHA·정의561개 링크를 현재 구조로 갱신했다. [CODE_STRUCTURE](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md) · [작업 계획](/home/ajou/yigyu/3/docs/plans/guitar_learning_consolidation_v2.md).
