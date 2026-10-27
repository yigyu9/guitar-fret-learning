# 최종 학습 정책의 정면 결과 영상

최종 stage1 정책의 실제 평가 episode0에 저장된 몸체 자세를 정면에서 재생했다. 1280×720·60fps이며 초록색은 왼손, 자주색은 오른손이다. 두 손은 별도 시험이다.

- [정면 합본 — 원래 속도·11초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/front_combined_60fps.mp4): 0~5초 왼손 접촉 유지, 5~6초 시험 전환, 6~11초 오른손 타현. 첫 목표 타현은 합본 약8.1초다.
- [정면 합본 — 0.5배속·22초](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/front_combined_slow_60fps.mp4)
- 개별5초 영상: [왼손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/front_left_60fps.mp4), [오른손](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/front_right_60fps.mp4)

정면 카메라는 eye[0,3.1,.8]m·target[0,0,.72]m다. 정책 준비1초를 포함한5초의 동작이다. 원평가에 native 정착2초의 프레임이 없어 그 구간을 임의로 만들지 않았다. 첫 영상 프레임은 정책 시각1/60초의 반환 끝점이며, 매 제어tick의 마지막 실제240Hz 표본을 선택했다.

기존 source visual 형상을 MuJoCo로 표시했으며 Isaac Gym에서 다시 실행하거나 새 물리·학습을 진행하지 않았다. 관절 FK로 동작을 재구성하지 않고 저장된 몸체 world pose를 직접 표시했다. 원 native 렌더링의 cooked 형상이나 압력·음향을 인증하는 영상은 아니다. 기록·모델·형상 SHA는 [입력 목록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/inputs_before.json)에 있다.

검사 결과: 원자료 불변, 두 손 각300프레임, 합본660프레임, 느린 합본1320프레임, 각 영상의60fps·재생시간 검사 통과. 600개 선택 프레임의 몸체 위치 readback 최대오차0m이며 새 물리 step은0이다. [실행·미디어 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/report.json) · [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_front_video_v1/review_v1.md).

코드는 [render_timing_video_v1.py](/home/ajou/yigyu/3/guitar_learning/render_timing_video_v1.py)이며 이전 렌더러·학습 코드·평가·봉인 산출물은 수정하지 않았다. EGL import 호환성 오류 후 설치 변경 없이 `MUJOCO_GL=osmesa`로 성공했다. 첫 실패 로그와 성공 로그는 이 결과 폴더 옆의 `guitar_learning_timing_front_video_v1.log`, `guitar_learning_timing_front_video_v1_osmesa.log`에 보존했다.

[원래 학습·수치 분석](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_timing_training_v1/README.md)
