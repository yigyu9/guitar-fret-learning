# right_shoulder_audit_v1 별도 변경 검수

2026-10-06. 검수자: 별도 change-reviewer. 구현·원자료·그림은 읽기 전용으로 확인했다.
검수자가 생성한 파일은 이 기록뿐이며 새 native 초기화/physics 실행은 하지 않았다.

## 요약 판정

**문제없음**. 남은 Critical/Warning/Suggestion 없음.
이번 단위는 저장된 pose의 source 형상 거리와 관측된 contact 두 행을 대조한다.
새 초기각·스트랩·gain·controller·hard gate 적용이나 안정성 성공을 주장하지 않는다.

## 코드와 원자료 대조

- `/home/ajou/yigyu/3/stability_adapter_2/audit_right_shoulder.py:29`부터의
  2 run × 5 저장 시점 × 5 사람 부위 × 2 기타 body = 100개 logical body-pair query를 확인했다.
  여러 활성 사람 geom은 각각 조회하며 helper가 각 기타 geom을 비교해 unsigned 거리 최솟값을 선택한다.
  unsigned hull 거리와 선택된 geom pair의 20mm cutoff backend signed gap을 구별한다.
- 저장 native pose에서 100행의 per-human query/QP 결과와 최솟값을 재계산해 원자료와 exact 일치를 확인했다.
  이전 `audit.json` 80행은 `audit_v2.json`의 exact subset이다. 현재 입력/source SHA도 모두 일치한다.
- 초기 R_Shoulder/G:body 거리는 reference 35.395mm, candidate_01 0.787mm이며,
  RH:palm/G:body는 100.306mm/3.230mm로 이전 right-support 결과와 일치한다.
- `contact_alignment.json`의 step3/4 native raw field를 원 contact 행과 직접 대조했다.
  직전 저장 step2/3의 source signed gap과의 차이는 각각
  2.0429064447047285e−8m, 6.7059138034175625e−9m로 exact 일치한다.
  같은 번호의 post-step source 값과는 다르다. 두 관측을 전체 solver 단계나 cooked geometry로 일반화하지 않는다.

## 그림·문서·보존

- `/home/ajou/yigyu/3/stability_adapter_2/plot_right_shoulder_audit.py:16`의
  거리 그래프를 원 JSON·단위·저장 시점과 대조했다. 상단은 5개 이산 관측을 연결한 그림이며
  하단은 두 contact 행의 native/직전 source/동일 번호 source 값을 구별한다.
- 같은 파일 `:71`의 시작 pose 그림 두 패널은 공통 world bounds/view를 사용한다.
  두 PNG를 직접 확인했으며 기타 body/neck, 어깨, 손바닥, 가까운 오른팔 색상과 witness 설명이 일치한다.
  저장 native pose에서 CPU로 재구성한 source 형상으로 native renderer 출력이 아니다.
- 결과 README `:7`, `:24`, `:41`과 누적 VISUAL_REPORT `:574`, `:580`, `:586`의 수치·해석은 원자료와 일치한다.
  unsigned convex-hull proxy는 실제 cooked clearance, 관통 깊이 또는 접촉 지지력 판정이 아니다.
- README `:50`의 지원 CLI와 parent가 생성한 `/tmp/right_shoulder_audit_reproduction` 결과를 확인했다.
  저장 PNG 두 장과 재생성 PNG의 픽셀이 각각 exact 일치한다. 새 native 실행은 없다.
- `plot_manifest.json`의 입력11/helper8/geometry asset40/출력2, 총61개 SHA를 현재 파일에서 readback해 모두 일치했다.
  최초 source snapshot4개와 v1 script의 원 audit SHA도 일치한다.
  `protected_validation.json`에는 기존 보호87파일과 August19 자료49파일의 변경 목록이 모두 비어 있다.

검수 범위 밖의 다른 작업 트리 변경은 수정하거나 되돌리지 않았다.

최종 확인: `source_manifest_final.json`의 8개 current/source_final 사본 SHA-256을 readback해 manifest와 모두 일치함을 확인했다. 판정은 문제없음으로 유지한다.
