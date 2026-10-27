# 하체 완전 고정 구현·실행·영상 독립 검수

- 검수일: 2026-10-07
- 범위: 파생 모델 생성기·환경·wrapper, `short_v4`/`full_1s` 저장 원자료, 최종 `render_v2` 영상·문서.
- 방식: 코드 읽기, XML·저장 수치·SHA 독립 대조, ffprobe 및 실제 영상 decode. 추가 native 실행·원자료 수정은 없다.

요약 판정: **문제없음. 남은 Critical/Warning 없음. 요청한 하체 고정은 확인했으며 기타 안정성은 달성하지 못했다.**

## 모델·제어 조건

- 양쪽 Hip/Knee/Ankle/Toe 8링크의 24joint 제거와 나머지 81joint 보존을 확인했다. 81 DOF는 main66+몸통9+목/머리6이며 팔24 PI 연결을 유지한다.
- 저장 step0의 parent-relative p/q를 독립 SciPy로 world pose에 복원해 8링크 모두 원본과 일치했다. geom·inertial XML과 나머지 joint 정의가 동일하고 파생 asset 및 manifest 입력 SHA가 일치한다. 원본 자산은 수정하지 않는다.
- 고정 링크와 fixed root로 하체를 지지하며 runtime pose/state 재주입은 없다. 기타는 자유·중력 유지다. 남은 관절의 초기 목표·kp/kd/effort/drive mode/native bounds는 원래 105 DOF 보고서와 이름으로 대조해 exact 일치한다.

## 저장 실행 독립 확인

- `short_v4` 24step 및 `full_1s` 240step은 각각 native11·고정12계약을 통과했다. 상태/trace/control coverage·step mapping, 초기 기타 전체 body struct와 root의 기준 일치, 65개 runtime source SHA 및 short/full 5배열 prefix exact를 확인했다.
- 전체241상태에서 하체8링크의 pose·속도 full struct가 초기와 exact 일치했다. 보고된 회전 0.000002415°는 동일 quaternion의 정규화·acos 수치 잔차다. 초기 기준과의 최대 위치 잔차7.772923e−7 m/회전8.537736e−6°도 저장값과 일치한다.
- 60회 PI update의 e+2I, 조건부 적분 rollback, ±.15 및 관절 box clipping, float32 제출 오차2e−7 이내와 4tick held target을 독립 대조했다. LA는 고정이며 240개 이전-state cable law를 다음 완료 trace의 실제 기록 장력과 대조해 최대 차이1.34e−12 N 이하였다.
- 기타 최대·종료 오차149.372986 mm/62.331933°, 종료 속도0.892343 m/s/3.413599 rad/s가 원자료와 일치한다. 이전 동적 하체 기준73.268255 mm/13.439339°보다 악화됐다. 사용자 지정 고정 조건의 채택과 현재 상체/스트랩의 안정성 성공을 구분한다.

## 영상·문서·지적 해소

- 최종 manifest의 선택 파일6·원자료6·geometry asset40·helper6·preview3·두 MP4 SHA가 현재 파일과 일치한다. 독립 ffprobe: H.264/yuv420p, 1280×720, 각241프레임, 60fps4.016667초/240fps1.004167초.
- 실제 slow 영상의 n=0/120/240을 `/tmp/lower_fixed_video_reviewer_dn29v_0g`에 decode해 직접 확인했다. 고정된 발·다리, 기타의 큰 회전, 양손 확대와 저장 시각·오차·속도·strap route 및 footer가 읽힌다. 저장 pose 재생은 source collision geometry 표시이며 새 physics step은0이다.
- **Warning 해소:** 과거 공용 renderer의 `stability_success=False` 고정 문구가 이번 report의 null과 달랐다. 별도 `render_fixed_lower_video.py`가 하단 문구만 중립 “Stability success not certified”로 바꾸고 실제 null·wrapper SHA를 manifest에 기록한다. 기존 renderer와 잘못된 footer의 이전 영상은 보존했다.
- VISUAL §50 링크를 실제938행으로 교정했고 README·CHANGED_FILES의 절대 경로·줄을 확인했다. 절대 meshdir 실패와 float32 각도 감사 실패 자료를 보존하고 측정 정밀도를 float64로 수정했으며 허용 오차를 완화하지 않았다.

## 최종 판정

문제없음. 하체 고정의 구현·1초 불변 검증·전체 영상은 준비됐다. 초기 발 모양·겹침이나 오른발 문제의 원인을 교정·확정한 것은 아니며 기타 안정성·연주 성공 인증도 아니다. 이 리뷰를 동결하고 다른 코드·원자료·기존 리뷰는 수정하지 않았다.
