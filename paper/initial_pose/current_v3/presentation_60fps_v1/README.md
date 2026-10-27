# 정면 전신 60fps 영상

저장된 두 개별 시험을 이어 편집한 33초 영상입니다. 첫 구간(17–40초)은 왼손 넥 해제와 오른손 타현이 포함된 `free_strike_v14`이고, 1초 전환 카드 뒤에는 왼손 넥 재접촉과 준비 복귀를 담은 `regrasp_v14`(40–49초)가 이어집니다. 재접촉 시험에는 타현이 없습니다.

![저장 몸체 자세를 재생한 정면 전신 영상](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/full_v1/front_full_body_60fps.mp4)

이 영상은 저장된 world body 위치와 정규화 quaternion을 원본 source 형상에 적용한 MuJoCo 시각화입니다. Isaac Gym/PhysX cooked 렌더 녹화가 아니며, 새 물리 적분·접촉 계산을 하지 않았습니다. body마다 독립 배치하므로 관절 FK로 자세를 다시 계산하지 않습니다. 영상용 변환 readback은 1,920개 기록 프레임의 106개 body에서 위치 최대 0m, 회전 최대 `6.754e-16 rad`였고 시각(clock)은 0을 유지했습니다.

출력은 1280×720, 60fps, 1,980프레임, 33초이며, 매 4번째 240Hz 원시 표본을 사용했습니다. 전체 파일 decode가 성공했고 실행 중 핀한 입력 119개의 SHA-256은 모두 유지됐습니다. 새 물리 스텝은 0입니다.

제작 기준은 [BRIEF_v3.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF_v3.md), 검수 가능한 표본 변환과 입력 지문은 [replay_report.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/full_v1/replay_report.json) 및 [inputs_before.json](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/full_v1/inputs_before.json)에 기록했습니다. 전체 렌더 로그는 [full_v1.log](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/phase/full_v1.log)입니다.
