# 최종 타이밍 정책의 정면 결과 영상

요청: 최종 학습 결과를 정면에서 확인할 영상을 제공한다. 이전 학습·평가를 반복하거나 봉인 결과를 수정하지 않는다.

선택: 최종 stage1 평가 episode0의240Hz 실제 몸체 자세에서60Hz 표본을 추출해 기존 source visual 렌더러로 표시한다. 관절 FK나 새 물리로 재계산하지 않고 몸체 world pose를 직접 사용한다. 이는 실제 기록의 시각화이며 새 native camera 실행이나 새 학습/평가가 아니다. 정책 준비1초를 포함한5초를 손별로 제공하고, 별도 시험 전환을 명시한 합본과0.5배속도 만든다. native 정착2초는 원평가 trace에 없으므로 임의로 만들지 않는다.

- [x] 원 평가·모델·형상 SHA와 표본 연속성 확인.
- [x] 원본 불변인 새 렌더링 진입점 작성·문법/실제 pose readback·미디어 확인. 위치오차0m·720p60fps·5/11/22초검사통과.
- [x] 독립 검수와 입력 불변/프레임수·재생시간 검사. 검수문제없음·입력121개불변·양손원checkpointSHA일치.
- [x] 정면 영상·설명·경로 전달. 원속도11초/느린22초합본과손별5초파일준비완료.

새 코드: guitar_learning/render_timing_video_v1.py. 결과: docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1. 과거 렌더러는 재사용만 하고 수정하지 않는다.

EGL import 호환성 실패는첫로그로보존했고OSMesa로설치/소스변경없이렌더성공했다. 이전trainingphase봉인artifact1075개SHA재검증변경0. 최종영상은600개의실제60Hz반환끝점frame이며학습/새물리없음.
