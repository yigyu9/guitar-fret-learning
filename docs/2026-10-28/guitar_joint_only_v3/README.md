# J 전용 학습 코드 정리

기존 R/F 단계와 단계 전환 코드를 활성 경로에서 삭제했다. 현재 `python -m guitar_learning.train`은 처음부터 끝까지 J 공동 학습만 실행한다. 이전 checkpoint 호환은 지원하지 않는다. 변경 전 소스·검사·문서531파일(당시 활성 Python480개)은 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261028_before_joint_only_v3/manifest.json)에 SHA와 함께 보존했다.

## 변경한 내용

- `FingerSkillCurriculum`, R/F/auto 선택, 숙련도 평가 gate, 단계별 예산과 actor 이전을 제거했다. `finger_skill_runner.py`는 J 단일 학습·저장·재개와 독립 평가를 담당한다.
- 정책의 R/F 동결·별도 확률 마스크·상관 탐색 기저·이전 API를 제거했다. 지지17축과 연주 손가락16축을 항상 함께 학습한다. 오른손6축은 기존처럼0이다.
- 기존 부모/자식 환경을 `FingerSkillEnvironment → TensorSongEnvironment` 두 단계로 합쳤다. 최종9보상·음별 정산·손목/물리 종료·초기 자세·PD·접촉·충돌은 유지했다.
- R/F/J one-hot3열과 계획 행동 길이1열을 관측에서 제거했다. 현재557상태는 공유552+로컬 잔여시간1+손목 종료4다. 매60Hz tick 새 행동을 결정하는 K1 수집으로 단순화했다.
- 최초 계획 전이25%를 PPO commit한 뒤 다음 reset부터 전곡을 선택하는 일정은 유지했다. 재개 때 추가 업데이트 수로 원래 전환 문턱을 옮기지 않는다.
- v24 명령행과 구형 R/F 실험 `active_press_v25`, 단계 전환 전용 검사를 원본 보관 후 활성에서 제거했다. 현재 평가·영상·짧은 손가락 진단 도구는 새 계약으로 연결했다. 별도 song·CPU·오른손 실행은 유지한다.

| 구분 | 현재 계약 |
| --- | --- |
| 과제 | `guitar_learning.finger_skill.v3` |
| 정책 | `guitar_learning.finger_skill_policy.v2` |
| 실행 보고서 | `guitar_learning.finger_skill_run.v2` |
| 재개 metadata | `guitar_learning.finger_skill_resume.v3` |
| 기본 연결 | 32파일: 구현24+초기화8 |
| 정의 | 533개: 이전561개에서28개 감소 |
| 활성 Python | 474개: 이전480개에서6개 감소 |

기본 연결 파일 수는 그대로지만 파일 안의 R/F 분기와 관련 정의를 줄였다. 모든474개가 기본 학습을 수행하는 파일은 아니다. 다른 실행·검사·도구·내부 native도 포함한다. 기본 코드의 상세 설명은 [코드해설](/home/ajou/yigyu/3/docs/2026-11-02/코드해설/README.md), 현재 계약은 [학습 README](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다.

## 확인한 결과

- 전체 활성 Python474개 구문 검사 통과. 원본 보관531개 SHA와 native provenance180개 현재 SHA에 불일치가 없다.
- 전체 CPU186모듈·1287개 검사 실행: 155모듈 통과,31모듈 실패. 실패 모듈 집합·개별 실패 사례·마지막 예외 문구가 변경 전과 동일하며 새 실패는0이다. 구형 fixture와 고정 provenance 관련 기존 실패를 이번 정리의 통과로 재분류하지 않았다.
- 기존 J의 보상·정산·종료·기하·진단 등24개 계산을 원본 AST와 대조했다. 정책33축 gradient·확률·KL·entropy,557관측의 필드/순서, 부분 reset·노출 전환 검사도 통과했다.
- 새 K1 수집기와 이전 J/K1을 정상·실패·truncation 상황, 연속된 H5/H2에서 비교했다. 공통21개 buffer 필드·행동·로그·reset·최종 난수 상태가 일치했다. 삭제한 `planned_ticks`는 현재 자료에 없다.
- 독립 검수자가 관련 CPU91개를 별도로 통과시켰다. 현재 J-only 경로와 새 계약·엄격 재개를 검수했다.

| 실제 GPU 검사 | 환경/H | 이번 실행 갱신/전이 | 누적 optimizer | 결과 |
| --- | --- | --- | ---: | --- |
| [새 학습](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/gpu_smoke/J/report.json) | 2/H8/small | 2회/32개 | 2 | 정상 완료 |
| [동일 소스 재개](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/gpu_resume/J/report.json) | 2/H8/small | 1회/16개 | 3 | 정상 완료 |
| [독립 전곡 평가](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/gpu_evaluation/report.json) | 2/H8/small | 학습 없음/3952전이 | 변경 없음 | 2에피소드 정상 완료 |

두 GPU 실행은557관측·GPU PhysX·CUDA tensor·단일 simulator·장면 close와 strict 입력 검사를 통과했다. `changed_inputs`, `missing_import_pins`, `cleanup_errors`는 모두 빈 배열이다. 최초 계획32개/전환 문턱8개를 유지하면서, 새 실행의 실제 노출32구간/0전곡에서 재개 뒤 누적32구간/16전곡으로 이어졌다. 짧은 실행은 연결 검증이며 장기 수렴이나 연주 성능 개선의 근거가 아니다.

평가는 각 환경의 첫 에피소드만 고정 분모로 사용했다. 두 에피소드 모두1969tick 전곡을 끝냈고 물리/손목 실패는0이었다. 평균 달성1/67음은2회 갱신한 연결 검사 모델의 결과이므로 기존 학습과 성능 비교하지 않는다. 선택 에피소드3938전이와 수집창 끝까지 실제 실행한3952전이를 구분한다. [GPU 검증 요약](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/validation/gpu_verification.json)에 검사 조건과 결과를 남겼다.

## 저장 자료

검증 상세·원본 비교·동결 SHA·독립 검수는 `validation/`에 모았다. GPU 실행의 원본 설정·로그·checkpoint·장면 감사는 각 `gpu_*` 하위 디렉토리에 있다. 이전 모델의 입력 SHA를 고치거나 현재 모델로 자동 이전하지 않았다. 새 소스에서 학습한 checkpoint만 같은 전체 계약·동일 소스에서 재개한다.
