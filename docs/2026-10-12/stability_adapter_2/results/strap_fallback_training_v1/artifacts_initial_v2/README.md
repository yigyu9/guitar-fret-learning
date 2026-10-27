# 초기 스트랩 OFF/ON 비교 그래프 보완

이 폴더는 기존 초기 조건 비교의 수치 그래프만 다시 그려 범례를 plot axes 바깥에 배치한 시각 보완본이다. 기존 비교 영상과 raw Isaac Gym frame sheet는 [artifacts_initial_v1 README](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/README.md)에 기록된 결과 그대로 링크한다. 이 문서는 초기 정책 조건만 다룬다.

## 기존 비교 영상과 원본 프레임

whole_body 및 hands 좌우 비교 영상과 실제 native 카메라 원본 contact sheet는 v1 산출물을 직접 참조한다. v1 파일은 이 보완 과정에서 수정하거나 다시 인코딩하지 않았다.

- [전신 비교 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_whole_body.mp4)
- [손 확대 비교 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_hands.mp4)
- [t=0/2/5초 및 마지막 whole-body/hands raw frame sheet](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/native_raw_contact_sheet.png)

## 범례 바깥 배치 그래프

범례는 세 축 영역 아래의 공용 여백에 배치했다. 따라서 OFF/ON 선과 평탄 구간, 실제 표본을 가리지 않는다. ON은 점선, OFF는 실선으로 표시해 값이 겹치는 구간도 구분한다. 이번 시각 변경은 색·자료·수식·표본 시점을 바꾸지 않는다.

![범례를 axes 바깥에 둔 초기 조건 측정 그래프](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/measured_traces_external_legend.png)

## 측정 정의

- 상단: native `controls.json`의 `position_outside_m` XYZ 벡터를 각 control endpoint에서 유클리드 norm한 뒤 mm로 변환한 값이다. 60 Hz 자료를 모두 표시했다.
- 가운데: native `trace.json` quaternion `xyzw`와 같은 실행의 t=0 quaternion 사이 shortest-arc 각도 `2 acos(|q·q0|)`를 degree로 표시했다. `physics_step` 간격 8인 표본을 써 30 Hz로 나타냈다.
- 하단: native `controls.json`의 `strap.last_applied_tension_n`을 N으로 표시했다. 60 Hz 제어 endpoint에서 다음 적분 직전에 적용하도록 기록된 cable 명령값이며 센서 측정 힘이 아니고 240 Hz 전체 physics-step 최대값도 아니다.

입력 array가 비었거나 유한하지 않은 값이 있으면 producer가 중단한다. 그래프 축은 두 조건의 실제 각 표본 최소·최대값을 포함한다. 입력 및 runtime font 전후 SHA-256은 [input_hashes.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/input_hashes.json)에 기록했다. standalone producer와 runtime font SHA 실행 기록은 [producer_execution.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v2/producer_execution.json)에 있다.
