# guitar_learning 실행 의존성 내부화

현재 실행이 최상위 `tab2body`·`stability_adapter_2`의 코드나 자산을 읽지 않도록 필요한 구현을 `guitar_learning` 안으로 옮겼다. 기존 두 디렉토리와 과거 결과는 보존했다.

## 구현 위치

| 내부 경로 | 역할 |
|---|---|
| `guitar_learning/native/` | native 장면·유한 제어·접촉·FK·기록·정적 렌더 의존 모듈 65개 |
| `guitar_learning/assets/` | 인체·OM 기타·의자 XML, mesh, 자세·gain·실행 설정·검사 fixture |
| `guitar_learning/score/` | canonical 이벤트·strike goal compiler·음악 task 입력 |
| `guitar_learning/assets/native_provenance.json` | 원본 180개 파일과 현재 190개 파일의 SHA 대응 |
| `guitar_learning/historical_inputs.py`·`assets/historical_inputs/` | 과거 gate가 봉인한 1,974개 경로·1,980개 SHA 버전의 검증용 원문 자료 |
| `guitar_learning/dependency_inputs.py` | 원본 baseline parity와 현재 물리 입력 SHA의 별도 검증 |

과거 입력 원문은 중복 제거한 1,957개 `.data` 자료(약22.8MB)이며 import하지 않는다. 새 실행은 현재 실행 소스와 과거 증거의 실제 CAS 파일을 각각 pin한다. 같은 경로의 과거 SHA로 현재 실행 소스 검증을 대체하지 않는다. 증거 검증 이후 pin 생성 사이의 변경도 요구 SHA와 대조해 거부한다.

## 검증

- 원래 사용한 소스·자산 180개와 변경 전 활성 패키지 보관본 334개의 SHA가 유지됐다. 현재 native 파일 190개도 manifest와 일치한다.
- 활성 Python 소스에 최상위 두 패키지의 직접 import가 없다. 별도 프로세스에서 두 경로의 파일 읽기와 import를 강제로 차단해 준비 상태, 모델·mesh, FK, baseline parity, 실제 손별·양손·전곡·reward v2·transition 입력 gate를 검증했다.
- 실제 Isaac Gym의 이전/이후 12스텝에서 상태 표본·105관절 목표·PD·관절/몸체 순서·물리 플래그가 완전히 일치했다. 달라진 필드는 자산 경로와 import 모듈 경로다.
- 접근 차단 상태의 실제 학습은 2전이·1업데이트와 모델 저장을 통과했다. 저장 모델을 strict resume해 누적2업데이트까지 확인했다. 이는 연결 검사이며 연주 성능이나 전체 에피소드 성공을 뜻하지 않는다.
- 같은 native 장면에서 4물리 스텝 후 두 번째 reset을 실행했다. 초기 native 상태가 완전히 같았고 장면·자산을 재생성하지 않았다.
- MuJoCo 정적 모델 106body 복원에서 위치 오차0, 회전 오차 약5.09e-16rad, 시계0을 확인했다. 카메라 영상 생성 없이 모델 구성·좌표 복원만 검사했다.
- 독립 change-reviewer 검수에서 발견한 증거 pin 경쟁 조건을 수정했고 최종 actionable 문제는 없다. 표준 전체655개 검사를 실행했고, 마지막 설정 경로 보완은 해당 모듈6개와 증거 경계4개 재검사로 확인했다. 최종 판정과 원래 실패·재검사 대응은 `validation_summary.json`을 참고한다.

기존 Isaac Gym 로그의 visual geom 경고6개와 초기 rigid-body setter 경고는 이전·이후 모두 존재한다. 이번 작업은 이 경고의 수정이나 렌더 품질 개선을 포함하지 않는다.

## 기록

- `integrity_report.json`: 보존 원본·현재 SHA, 직접 import 검사, 실제 수치 비교
- `isolated_cpu_report_final.json`: 구형 디렉토리 접근 차단 검사
- `score_migration_report.json`: 7개 정상 곡 결과 일치, 1개 기존 입력 오류 동일 거부
- `native_migration_report.json` / `historical_inputs_report.json`: 이전 범위·원본 대응
- `native_before_v2/result.json` / `native_after_v1/result.json`: 실제 수치 비교 원자료
- `ppo_final_v1/report.json` / `ppo_final_resume_v1/report.json`: 학습·strict resume 결과
- `persistent_reset_v2/result.json`: 실제 장면 재사용 reset
- `review_report.md`: 독립 검수와 보완

실패한 초기 실행·검사 기록은 남겼다. native_before 첫 시도는 실행 환경의 ninja 경로 누락, persistent_reset 첫 시도는 검사기의 출력 하위 폴더 누락으로 실패했다. 초기 CPU 검사에서 발견한 경로·과거 입력 검증 연결은 수정 후 재검사했다. 전체 검사 프로세스가 마지막 경로 보완 전 코드를 이미 읽은 상태였으므로 표준 로그에는 해당1개 실패가 남아 있으며, 수정 후 `cpu_teacher_proof_final.log`의6개 모두 통과와 `cpu_evidence_path_regressions.log`의4개 통과로 검증했다. 최종 판정은 위의 완료 결과와 재검사 대응을 사용한다.

`cpu_custom_order.log`의1개 실패는 특정 teacher-proof→refinement 순서에서 기존 `patch.dict(sys.modules)`가 부모 패키지 참조와 모듈 캐시를 다르게 남기는 기존 테스트 격리 문제다. 관련 실행기·worker·검사 파일이 이전 보관본과 동일하고, 단독 및 표준 discovery 순서는 통과한다. 이 작업에서 해당 코드는 변경하지 않았다.

## 남은 외부 자료

Isaac Gym 설치와 Python 환경, `data/song_bundles`, `docs`/`paper`의 저장 준비 상태·checkpoint·평가 결과는 계속 사용한다. 최상위 두 개발 디렉토리의 실행 의존성을 분리한 것이며 독립 설치 패키지를 만든 작업은 아니다. 원본·archive는 현행 실행에서 import하지 않으며, 물리·행동·관측·보상·checkpoint 계약은 유지한다.

변경 전 전체 활성 패키지는 `guitar_learning/archive/20261019_before_dependency_internalization/`에 보관했다. 작업 계획은 `docs/plans/guitar_learning_internalization_20261019.md`다.
