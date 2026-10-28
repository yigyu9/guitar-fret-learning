# J 전용 손가락 학습 정리

사용자가 기존 R/F 코드를 삭제하고 J만 남기며 이전 checkpoint 호환은 필요 없다고 명시했다. 변경 전 소스·검사·해설·SHA는 `guitar_learning/archive/20261028_before_joint_only_v3/manifest.json`에 보관했다.

## 변경 계약

- 현재 family는 `guitar_learning.finger_skill.v3`, J33·독립 탐색·정책60Hz/K1만 지원한다. R/F/auto·actor 단계 이전·상관 탐색·유지 행동 옵션을 활성 경로에서 제거한다.
- 현재 환경은 `FingerSkillEnvironment` 하나로 합치고 기존 Simplified의9보상·손목/물리 종료·구간 균형·reset·기하·진단을 유지한다.
- 관측의 R/F/J one-hot3개와 planned_ticks1개를 제거한다. `finger_skill.remaining_s`와 손목 종료4열은 유지하여557상태가 된다. `SKILL_FIELDS=('finger_skill.remaining_s',)`로 정의한다.
- `FingerSkillPolicy`는 phase/exploration 선택 인자·동결·기저·전환 API를 없애고 `phase='J'`, `exploration='independent'`를 고정한다. 정책 schema는 v2, runner metadata resume schema는 v3로 구분해 구형 모델을 거부한다.
- 노출 예산25% 문턱과 commit 후 다음 reset에서 전곡 전환, 새 계약 안에서의 엄격 재개를 유지한다.
- 기존 v24 CLI 지원을 제거하고, 평가·영상·현재 J 진단 도구는 새 계약으로 갱신한다. 호환되지 않는 과거 R/F 전용 도구·검사는 원본 보관 후 활성에서 제거한다. 다른 song/CPU/오른손 체계는 이번 R/F 삭제와 섞지 않는다.

## 작업과 검증

- [x] 수정 전 원문·테스트·문서·SHA 보관
- [x] J 전용 정책·환경과 계약 구현, R/F 관련 검사 교체
- [x] K1 수집기·풀·도구 연결과 구형 전용 경로 정리
- [x] 실행기·설정·재개·평가에서 RFJ 전환 제거
- [x] 전체 구문·CPU 검사, 유지할 계산과 종료·노출·gradient 검증
- [x] 새 GPU 학습·동일 소스 재개·평가 검증
- [x] 현재 해설·README·정의 색인·소스 SHA 갱신
- [x] 독립 change-reviewer 검수 및 최종 기록

최종: J 전용v3/557상태·정의533개. 전체CPU186모듈155통과/31기존동일실패, GPU새학습32전이·재개16전이·전곡2에피소드 정상완료. 독립검수 문제없음. [결과 기록](/home/ajou/yigyu/3/docs/2026-10-28/guitar_joint_only_v3/README.md).
