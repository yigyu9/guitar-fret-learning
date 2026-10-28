# 현재 학습 코드 가독성 정리

기본 J 학습에 연결된24개 구현을 검토하고, 읽기 어려운 **training6개·GPU6개 파일**의 표현과 설명을 정리했다. 파일 수는 활성281개·기본 연결32개(구현24+초기화8)·정의533개로 유지한다. 학습 방식·보상·제어·종료 조건을 바꾸는 작업이 아니다.

변경 전 소스281개와 당시 문서/해설을 포함한318파일은 [원문 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_readability_v1/manifest.json)에 SHA와 함께 보관했다. 다른 창의 이전 편집을 되돌리지 않았다. native·자산·과거 결과도 유지한다.

## 코드에서 달라진 부분

| 영역 | 정리한 내용 |
| --- | --- |
| `training/launch.py` | 공용 song 설정 뒤 J 설정을 확정하는 순서, 환경 수·수집 tick 이름, 공용 검증과 GPU 환경 수 검증 구분 |
| `training/finger_skill_runner.py` | 복구 저장 가능 flag와 노출 집계 이름, 수집→PPO→저널 commit→노출 commit→환경 진행도 순서 |
| `training/rollout.py` | 현재/다음 가치와 제어 tick 이름, 기본 J와 별도 song 수집기 구분, buffer 모양·reset 전 bootstrap·복제본 수명 |
| `training/policy.py` | 손가락별 우선토큰2개+자기 상태20열을 명시 loop로 구성, 지지17+손가락16+오른손6 출력, log_std 이름 |
| `training/ppo.py` | reward/cost advantage·return 약어를 풀고 GAE→유효 결정→actor KL 재시도→critic 순서를 설명 |
| `training/training_log_io.py` | 한 줄 복합문 분리, 입력/JSON·저널·song 로그·에피소드·checkpoint/감시의 영역 구분 |
| `gpu/environment.py` | 환경/목표/표면/패드 축, 음별 원장·tick 합산·수집 통계의 수명, 원시 측정과 최종 J 보상 경계 |
| `gpu/finger_skill_environment.py` | 수행 부족 정산→실패 예산→원시 terms의 최종9항 조합, 부모와 자식의 계수 관계 |
| `gpu/contact.py` | 접근용 최근접 표본과 양성 접촉 존재 조건의 차이, 목표·몸체·원인 축과 격자 인덱스 |
| `gpu/control.py` | 관절 목표 제한·손가락 증분·발 보정 순서, 중력/자세·어깨/가슴/하체 지지·상한 적용 순서 |
| `gpu/finger_reward.py`, `episode_diagnostics.py` | 손가락×목표 축과 phase/finger/component 진단 축 설명 |

주요 지역명은 아래와 같이 읽는다. 공개 인자·로그 키·state_dict·schema 문자열은 그대로다.

| 현재 이름 | 의미 |
| --- | --- |
| `recovery_eligible` | 지금 상태를 유효 복구 checkpoint로 저장할 수 있는가 |
| `update_exposure` / `committed_exposure` | 현재 수집창 노출 / 학습 반영을 확정한 누적 노출 |
| `reward_advantage` / `cost_advantage` | 행동 정책 갱신에 사용하는 보상·비용 우위값 |
| `reward_return` / `cost_return` | 두 critic이 맞춰야 할 GAE 반환 목표 |
| `old_log_std` / `active_log_std` | 표준편차 자체가 아닌 로그 표준편차 |
| `priority_tokens` / `local_state` | 손가락 tracking/next 우선토큰 / 본인 관절·자세20열 |

원시 측정·수식의 계산 순서는 유지했다. 가상 현 분류 표면과 담당 끝마디 패드는 표본 목적이 달라 합치지 않았고, 준비 자세 함수의 여러 호출도 실제/직전 접촉 시점이 달라 캐시하지 않았다. 충분히 설명된 곡·compiler·공용 기하·초기 입력·native 코드는 이번에 전면 재작성하지 않았다.

## 검증

- 활성281개 Python 구문 검사 통과. 원문318파일·native/provenance190파일의 SHA와 동결 후281개 소스에 불일치가 없다.
- 복합문 분리만 한 단계에서는12파일 모두 AST가 동일했다. 최종에는 docstring 제외·함수별 지역명 역치환 후 기본32파일의 AST가 같으며, 정책 forward의 명시 loop는 별도 독립 구조 대조와 수치 비교로 확인했다.
- root의 직접 수치 비교: 모델 크기3종×목표 mask3종=정책9조건에서 초기 가중치·출력·확률·기울기·KL·난수 상태가 bitwise 일치했다. 종료/비종료/truncation 수집3조건의 buffer·행동·에피소드·결정 로그·reset·난수도 일치했다.
- 기본 결정 PPO와 공용 PPO3조건의 지표·모델·두 Adam 상태·난수, KL 실패의 전체 rollback도 bitwise 일치했다. 작업자 검증은 실제 J 정책의 float32/64와 실제 J PPO 갱신을 추가 대조했다.
- 전체 CPU117모듈·923개 검사에서100모듈 통과·17모듈 실패. 실패 사례·예외 문구는 변경 전과 동일하고 새 실패는0개다. 기존 검사를 삭제하거나 기대값을 완화하지 않았다.
- 독립 검수에서 잘못 좁혀 쓴 지지 관절 범위와 raw terms의 측정 시점 설명2곳을 고쳤다. 실행 코드는 바뀌지 않았고 수정 뒤 새 SHA를 봉인했다.

| 실제 GPU 검사 | 조건 | 결과 |
| --- | --- | --- |
| [새 학습](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/gpu_smoke/J/report.json) | small/2환경/H8 | 2회·32전이, optimizer2 |
| [동일 소스 재개](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/gpu_resume/J/report.json) | 같은 설정 | 추가1회·16전이, optimizer3 |
| [독립 전곡 평가](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/gpu_evaluation/report.json) | small/2환경/전곡 | 2에피소드 모두1969tick 완료 |

두 실행은557관측·J33/K1·원래 계획32전이/전곡 전환 문턱8·누적 committed48·GPU PhysX·CUDA tensor·단일 simulator·장면 종료를 확인했다. changed_inputs/missing_import_pins/cleanup_errors는 모두 빈 배열이다. 이번 작은 실행은 연결 검사이며 장기 성능 향상의 근거가 아니다.

전곡 평가에서는 환경별 첫 에피소드2개를 고정 분모로 포함했다. 실제3952전이·선택3938전이, 정상 곡 끝2·물리/손목 실패0·평균 달성1/67음이다. 2회 갱신한 연결 검사 모델이므로 장기 성과와 비교하지 않는다. [GPU 검증 요약](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/validation/gpu_verification.json).

독립 change-reviewer의 최종 판정은 **문제없음**이다. 원본과의 AST·정책 loop의 독립 복원·실제 수치·문서·새 GPU학습/재개/평가를 확인했다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-28/guitar_readability_v1/validation/review_findings.md).

## 읽는 순서와 자료

현재 코드는 [읽는 순서 지도](/home/ajou/yigyu/3/guitar_learning/docs/CODE_STRUCTURE.md)의 여섯 파일부터 읽는다. 상세 [코드해설](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md)의 변수 설명·소스 SHA·정의533개와 문장/선언 링크138개도 현재 코드로 갱신했다.

동등성·전체 CPU 원문·소스 SHA·독립 검수는 `validation/`, 실제 GPU 설정·모델·로그·장면 감사는 `gpu_*`에 모았다. 공개 학습 계약은 같아도 소스 SHA가 바뀌므로 정리 전 checkpoint의 pin을 고치지 않는다. 이전 저장본은 정리 전 코드를 보존한 별도 작업 공간에서 사용하고, 현재 트리는 현재 소스에서 새로 저장한 checkpoint를 엄격 재개한다.
