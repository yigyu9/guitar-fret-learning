# Runtime Palm Jacobian 독립 검수

2026-10-07. 신규 runtime query/cache 비교/plotter, 현재 원자료·문서와 다음 비교안을 검수했다.
검수자는 저장 자료 계산과 순수 CLI만 실행했다. Native 초기화·simulation·source query는
재실행하지 않았고 다른 공유 파일·기존 검수 기록은 수정하지 않았다.

요약 판정: 문제없음. 현재 0.1초 계측 근거이며 정확한 항등식·전범위·안정성 인증은 아니다.

## Critical / Warning / Suggestion

- Critical: 없음. 현재 계산 코드에 수정 요구 사항 없음.
- Warning 해결: 우측 panel은 native body linear velocity의 COM/origin 가설 비교다.
  `check_palm_jacobian_runtime.py:99`는 native v를 origin 값으로 가정해
  `v + ω×(COM−origin)`으로 COM에 옮기며 Jacobian 기준점을 바꾸지 않는다.
  최종 plotter/README:11/누적37절의 제목·설명을 이 계산에 맞췄다.
- Suggestion 해결: 위치 보정 제안의 모든 한계를 delta 좌표로 명시하고,
  단조 blocked-mask의 최대24축/최초 포함 최대25 solve를 명확히 했다.
  초기 legend 잘림 우려는 실제 bbox가 canvas 안에 있음을 확인해 철회했다.

## 독립 확인

- 25표본의 양손 6×105 행렬에 전체 native DOF velocity를 곱해 COM·각속도
  residual과 source/origin 가설 cross-product를 독립 재계산했다. 모든 최대값이 일치했다.
  Refresh 후 COM 오차 LH1.500569/RH1.371527mm/s, angular 오차
  LH0.001590517/RH0.004353958rad/s다. Source 속도는 body v/ω에서 도출한 비교값이다.
- t=0 before-refresh는0, refreshed는 직전 초기 tensor와 같았다. 이후 모든
  before-refresh 행은 직전 refreshed 행과 같았고 조회 상태/target/PD 보존을 확인했다.
  CPU buffer는 scene 수명 안에서 copy/list로 보존하므로 종료 후 alias를 사용하지 않는다.
- Native report 9개 검사·71개 입력 SHA, cache 3개 검사·75개 입력 SHA가 통과했다.
  기존 승인 PI states25/trace25/controls24 prefix가 같고 saved-only cache CLI도 전체 JSON이 같았다.
- 최종 plot 지원 CLI를 새 `/tmp`에서 실행해 exit0을 확인했다. Validated PNG
  2396×977은 canonical과 byte/RGBA가 같고 직접 시각 QA를 마쳤다. 71/75 embedded 입력,
  소비 JSON3개·producer·출력 SHA, 위치값 mm/s 환산·post-step 표본1–24가 일치했다.
- 현재 계획·표·누적37절은 관측 범위와 기타 종료 오차6.874401mm/1.519676°를 정확히 구분한다.

## 최종 판정 및 동결

새 위치 비교안의 수식은 차원이 맞고 최종 목표 box와 보수적 anti-windup 종료가 명시됐다.
사용자 확인 전 제안이며 controller/task/rate/gain은 아직 구현하지 않았다. 기타 p/q feedback과
접촉·연주 성공을 인증하지 않는다. 미해결 finding 없이 이 검수 기록을 동결한다.
