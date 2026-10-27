# 기타 집중 초기 이미지 검수

판정: **문제없음. Critical 0건, Warning 0건, Suggestion 0건.** 지정된 새 카메라 진입점·완료 초기 이미지·저장 원자료만 읽기 전용으로 확인했다. 추가 물리·학습은 실행하지 않았고 이 리뷰 외 파일은 수정하지 않았다.

[새 진입점:9](/home/ajou/yigyu/3/stability_adapter_2/run_guitar_focused_view_v1.py:9)는 첫 capture에서 OM_appearance 카메라만 기타 root pose 기준 target `[0,-0.145,-0.02]m`, eye offset `[0.08,0,0.66]m`로 이동한다. native_state exact 검사 후 기존 녹화 wrapper가 카메라를 다시 렌더하므로 색상·depth·6현 투영은 변경된 카메라에 대응한다. 기존 전신·손 영상 카메라와 물리 제어는 그대로다.

[실제 초기 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/native_v1/media/initial_strings.png)를 직접 열어 전체 기타 바디·넥·헤드스톡과 양손이 프레임 안에 들어오는 것을 확인했다. 여섯 밝은 선은 렌더 후 오버레이이며 물리 현의 굵기·진동을 뜻하지 않는다. 이 변경은 초기 정지 이미지 구도이며 전체 영상의 기타 추적 카메라 기능은 아니다.

[검증 JSON](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_focused_view_v1/verification_v1.json:1)의 입력 SHA, 직전 현 표시 실행과 trace·contacts·initial_values·native_properties·native_shapes·property_cache_checks 6개 JSON의 exact 일치를 독립 대조했다. 실제 1,200 physics/300 control 완료·금지 API 0과 세 녹화 단계의 151frame/상태 보존을 확인했다. main4 append prefix·SHA와 보관 전신/손 MP4 2개 원본/복사 SHA도 일치한다. README는 외관 정지 이미지용 카메라와 기존 영상 카메라를 정확히 구분한다. 초기 자세 유지·연주 성공·전체 영상 디코딩은 이 검수의 인증 범위가 아니다.
