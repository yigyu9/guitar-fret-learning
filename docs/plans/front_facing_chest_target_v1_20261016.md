# 정면 자세: 실제 가슴 기울기 초과에 따른 유한 목표 보완

첫 native_static_v1은10초 완료했고 새 정면 방향·기타·발·금지조건 및 산술은 통과했으나, Chest 최대5.31067856°(0.43333초),유지5..10초 최대5.22058°로 원5° 기준에 실패했다. Torso 최대4.88469°,Spine4.96390°이며 기존 원자료·code/config/source7을 모두 보존한다. 25개 중24개 통과와 전체 실패를 구분한다.

관측된 Chest 편차 약0.42~0.51°를 감안해 **gain/cap은 바꾸지 않고**, source7 초기상태는 그대로 두며 Chest의 유한 목표만0.8° 더 직립 쪽으로 돌린다. 실제 관절 좌표와 world body 회전을 FK로 맞추고 yaw는 기존 새 정면 기준을 보존한다. 목표의 형상 예측은 실제 접촉/안정성과 구분한다.

우선 Torso/Spine/하체/손가락 목표를 source7과 같게 유지한다. LH12는 world palm을 유지하도록 필요한 경우 refit하고 Head/Neck6은 머리 world heading을 유지하도록 미소 보상할 수 있다. 오른팔은 기존 finite world IK가 최종 목표를 소유하므로 raw base target과 runtime override를 구분한다. 원105범위/8zero/원mass·shape·cap/rate·Root고정/G자유·중력ON·strapOFF를 유지한다.

새 목표보고서와 입력을 새디렉토리 posture_target_v*에 봉인한 뒤 새config로 실제10초를 재시험한다. 원5° 기준과 기존 기타·발·heading·지지 기준은 완화하지 않는다. 실패시 원자료에 근거해 다음 새버전에서 조정한다. 통과후 동일조건 반복으로 확인한다. 새 PPO는0이다.
