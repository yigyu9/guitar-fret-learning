# 최신 손별 정책 결과 영상

요청: 학습 결과를 설명하고 영상으로 보여준다.

최신 BC 정책의 실제 검증 기록 episode0을 재생한다. 기존 평가·모델·봉인 소스는 수정하지 않으며, 새 학습이나 물리 시험은 수행하지 않는다. 왼손7초와 오른손7초는 별도 시험임을 화면에 표시한다. 원본 몸체 world pose를60Hz로 표시하고 정면 전신·상체 확대 영상을 제공한다.

- [x] 최신 결과 및 영상 유무 확인, 입력 형상·모델·평가 기록 SHA 대조.
- [x] 새 렌더링 진입점 작성, 실제 저장 자세·시계 연속성 및 영상 프레임/시간 확인. v2 손별420/합본900프레임·720p60fps·7/15초 확인, 모든840자세 위치오차0m·126입력SHA 불변·새 물리0step.
- [x] 독립 검수와 화면 점검 후 영상과 결과 한계 전달. v2 검수 문제없음, 별도 ffprobe로4개 미디어의 길이·프레임·60fps·무음 확인. 정면 전신/상체·좌손 해제 후·우손 타현 시점·별도시험 전환카드 점검. 기존169/6/15개 봉인 입력 변경0.

코드: guitar_learning/local_skills/render.py. 최신 출력: docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1/front_video_v2.

첫 v1의 전신 영상은 정상이었으나 상체 free camera90도는 후면이었다. 기존 소스는 guitar_learning/archive/20261019_before_local_video_front_camera_fix에, 출력과 로그는 실험 phase/archive/front_video_back_camera_v1에 보존했다. 상체 카메라와 보고서의 azimuth를270도로 바꾸고 v2로 다시 렌더링한다. 실제 기록·모델·기존 평가의 입력은 수정하지 않았다.
