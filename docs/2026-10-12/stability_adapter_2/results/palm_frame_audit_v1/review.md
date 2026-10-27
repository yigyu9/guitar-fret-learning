# Palm-frame audit 독립 검수

2026-10-07. 대상은 이번 audit/plotter, 최종 `measurements_validated/`,
`artifacts_validated/`, 관련 계획·제안·결과 문서다. 다른 파일은 수정하지 않았다.
검수자는 native 초기화·조회·simulation을 실행하지 않았다.

요약 판정: 문제없음. 준비 상태 계측이며 Jacobian 정확성·위치 제어·안정성 인증이 아니다.

## Critical / Warning / Suggestion

- Critical: 없음.
- Warning 해결: `audit_palm_frames.py:98`에서 양손 palm 행 nonzero를 성공 조건에
  포함하고 `:114`에서 실패를 거부한다. 실제 helper의 zero/한쪽 nonzero/양쪽 nonzero
  순수 배열 회귀는 각각 거부/거부/준비 통과였다. 최종 9개 검사는 모두 참이다.
- Suggestion 해결: 결과 `README.md:20`의 수치를 초기 local offset으로 world 형상
  중심을 재구성한 오차로 명확히 했다. offset 차이와 재구성 오차는 다른 필드다.
  `CHANGED_FILES.md:3/:18`도 산출물 작성 범위와 readiness 보완을 구분했다.

## 독립 확인

- CPU device/dtype/전체 shape/null 주소 검사 후 float32 버퍼를 복사하며,
  scene 종료 전에 소유 배열을 확보한다. 순수 ctypes 복사 수명 검사도 통과했다.
- 저장 native body pose를 별도 회전 행렬로 대조한 local offset/world 재구성,
  source palm convex-hull 중심, 중심·body origin·wrist 변위 계산이 일치했다.
  source 중심은 접촉점·해부학적 중심·native COM으로 해석하지 않는다.
- 최종 tensor `(1,65,6,105)`, palm rows L17/R43와 finite/nonzero를 확인했다.
  최종 저장 점·tensor는 이전 성공 자료와 동일하며, 네 query 시도의 실패/성공
  이력 1/1/0/0과 steps=0을 보존했다. 67개 명시 입력 SHA가 현재 파일과 일치했다.
- README 지원 plot CLI를 독립 `/tmp`에서 실행해 exit 0을 확인했다.
  canonical PNG와 byte/RGBA가 같고 2040×944다. 직접 그림을 확인했으며,
  audit/Jacobian·embedded inputs·producer·출력 manifest SHA도 일치했다.
- README 표, 누적35절, PLAN43, 현재 제안의 수치·범위가 일치한다.
  LH source 중심 변위 1초138.278237mm/3초144.535203mm는 이산 저장 관측이다.

## 최종 판정 및 동결

frame/기준점/DOF 미분은 아직 미검증이다. 다음 fresh FK 유한차분과 새 위치 task·
변화율 제한을 분리하고 사용자 확인 전 제어를 적용하지 않는 문서 계약이 타당하다.
미해결 finding은 없다. 이 검수 기록을 동결했으며 이후 추가 편집하지 않는다.
