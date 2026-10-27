# 기존 최선 실행 전체 영상 독립 검수

- 검수일: 2026-10-07
- 범위: 선정 54기록, 신규 replay producer, `render_v2` 두 영상·manifest, 계획·workflow·결과 설명.
- 방식: 저장 trace 재계산, 코드·SHA·ffprobe 및 실제 영상 프레임 확인. 추가 native 물리 실행과 원자료 수정은 없다.

요약 판정: **문제없음. 남은 Critical/Warning 없음. 기존 후보의 전체 움직임을 보여주는 영상이며 안정성·연주 성공 인증은 아니다.**

## 선정 및 재생 대응

- 반복을 포함한 1초 이상 54기록의 실제 trace에서 기간·sample 수·전체 최대/종료 p/q 오차를 독립 재계산했다. 선택 원본 `left_palm_boundary_v1/hold_1s/l_wrist_x_minus0125`는 두 최대 오차 모두 최소(73.268255 mm, 13.439339°)이며 동일 수치 반복보다 먼저 측정한 원본이다. 짧은 0.1/0.5초 기록을 같은 유지 시간으로 순위 비교하지 않는다.
- 저장 state 0–240와 trace 0–1초의 241시점을 생략·보간 없이 사용한다. 각 body pose는 이름에 대응하는 평탄화된 source 형상에 적용하며, 같은 시점의 `route_points_m`·오차·속도를 표시한다. 이는 별도 replay 모델의 표시 갱신이며 실제 제어환경 pose 덮어쓰기나 새 rollout이 아니다.
- 두 camera는 전체 구간에서 고정된다. probe 준비 `mj_forward` 1회, 표시 loop 241회, 총242회를 명확히 구분하며 `mj_step`과 native sim 초기화는0이다.

## 실행·영상·보존

- 최종 manifest의 선정 파일6, 원자료 입력111, geometry asset40, helper5, preview3 및 두 MP4 SHA가 현재 파일과 일치한다. 최종 producer와 실제 실행에 사용한 producer가 일치한다.
- 두 MP4를 독립 ffprobe로 확인했다: H.264/yuv420p, 1280×720, 각241프레임. 60fps는4.016667초(0.25배속), 240fps는1.004167초(실시간)이며 마지막 저장 시점도 프레임으로 포함한다.
- 실제 slow MP4에서 프레임 n=0/120/240을 `/tmp/best_run_video_reviewer_dznd44vc`에 decode해 직접 확인했다. 전신·양손 확대, 기타/손/route 색상, 0/0.5/1초 표시와 오차·속도 값이 맞고 글자·주요 형상이 읽힌다. 저장 preview만 보고 영상 검수를 대신하지 않았다.
- README 및 CHANGED_FILES의 절대 경로·줄과 VISUAL_REPORT §49:926을 확인했다. EGL 실패/OSMesa 성공 및 이전 제작본은 보존하며, 현재 `render_v2`가 canonical임을 명시한다.

## 지적 해소 및 해석

- **Critical 해소:** ffprobe 해상도의 int를 문자열과 비교해 정상 영상도 거부하던 분기를 정수 비교로 수정했다.
- **Warning 해소:** 두 영상별 중복 렌더로 호출 수가 틀리던 기록을 step당 한 번 렌더·두 label 합성으로 수정했다. renderer와 encoder 예외 정리도 `finally`로 보장한다.
- **문서 Warning 해소:** workflow:85–86은 사용자 자율결정 지침과 구현된 팔24 PI/RATE_PI/PALM_RATE를 반영하고 미구현 기타 p/q 직접 feedback과 구분한다.
- source collision geometry 재구성은 PhysX renderer/cooked 접촉·지지 인증이 아니다. `stability_success=false`, 종료 선속도0.293 m/s·각속도1.192 rad/s를 명시하며 후기 안정성이나 연주 가능성을 선언하지 않는다.

## 최종 판정

문제없음. 요청한 기존 최선 후보의 시작부터 종료까지 영상은 준비·검수됐다. 이 리뷰를 동결하며 다른 코드·원자료·기존 동결 리뷰는 수정하지 않았다.
