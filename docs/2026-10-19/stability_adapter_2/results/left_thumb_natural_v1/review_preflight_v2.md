# 엄지 V2 탐색 범위·사전 핀·카메라 포장 검수

요약 판정: 문제없음. V1 끝범위 후보는 미실행으로 보존하며 V2의 읽기 순서·5관절 탐색 box·읽기 전용 카메라 추가가 계획과 일치한다.

Critical: 0

## 확인 근거

- [V2 source:27](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v2.py:27): anchors SHA 저장 후 CFG/manifest를 읽고 XML discovery SHA를 저장한 뒤 mesh 선언을 파싱한다. 전체 입력 저장 후 contract/seed/BASE/FK/shape를 구축한다. discovery와 XML discovery가 전체 맵/current SHA와 일치하며 현재 입력829개 변경이 없다. V1의 early-read 순서 제한을 새 버전에서 보완했다.
- [탐색 box:67](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v2.py:67): 모델 교집합에 x≤35/y≥−75/z≤75/thumb2≤65/thumb3 0~35°를 적용한다. hard 모델 자체를 변경하지 않고 source의 임시 box만 줄인다. 선호·normal/위치 weight 변경은5개 초기각 fitting에만 적용한다. fixed76/nonthumb pose 및 whole source audit 조건을 유지한다.
- [source 수락:91](/home/ajou/yigyu/3/stability_adapter_2/search_left_thumb_natural_v2.py:91): back16mm는27.001681mm 점오차로27mm gate를 초과해 거절, back24mm는19.979960mm/whole clear/76각·nonthumb pose exact로 수락한다. 이는 native나 anatomy 인증이 아니다. V2 source/runner AST를 확인했다. optimizer/native를 재실행하지 않았다.
- [runner camera:90](/home/ajou/yigyu/3/stability_adapter_2/run_left_thumb_natural_v2.py:90): 엄지3/palm의 world midpoint와 currentG offset[.13,.07,−.28]로1280×720 카메라를 생성한다. 카메라 pose만 설정하고 human/G state·joint/material properties를 바꾸지 않는다. source accepted와37/5 finger guard, EW V7 제어/캡/동작 gate는 V1에서 그대로다.
- [views 포장:99](/home/ajou/yigyu/3/stability_adapter_2/run_left_thumb_natural_v2.py:99)은 outer recorder와 recorder.strap의 tuple을 함께 확장하고 양쪽 frames/thumb_back 경로를 생성한다. 원 V7의4patch 아래 recorder.strap은 GymTrialRecording이므로 이 두 레벨이 실제 raw capture→string overlay→encode 경로와 맞는다. [원 overlay:43](/home/ajou/yigyu/3/stability_adapter_2/string_trial_recording_v1.py:43)의720×1280 depth shape에도 일치하며 원 render 전후 state guard를 재사용한다.

## Warning

- back24 후보 thumb2=65.000000670°는 fit의 float32 변환 후 임시65° 상한을 .00000067° 초과한다. 실제 모델90° 범위 안이며 실질적 안전 위반은 없지만 임시 box를 엄밀히 `<65°` 인증한 것으로 쓰지 않는다. float32 오차 범위를 기록하거나 후속 버전에서 cast 후 허용오차를 명시한다. y≈−75°도 새 임시 box 끝이며 자연스러움을 자동 보장하지 않는다.
- `back24mm`는 명목 target label이고 실제 facet back-plane gap39.424145mm다. 선택facet 평면 지표를 엄지–넥의 실제 최소 간격/접촉 또는 해부학적 패드 인증으로 설명하지 않는다. source clear·모델 내 각도·범위 축소는 실제 엄지 시각 평가와 별개다.
- 새 카메라 방향이 엄지를 실제로 잘 보여 주는지/가려지는지는 최초 native frame으로 확인해야 한다. 원 capture의 고정 `camera_config_source`는 기존 카메라 helper 표기라 새 thumb_back 설정을 모두 설명하지 않는다. 실제 runner SHA와 frame별 view/projection 및 이미지 SHA를 함께 출처로 삼는다.
- 실제76 scalar/nonthumb pose/37finger 초기 exact, thumb 접촉·G drift·양방향6줄 판정은 후속 native 원자료 범위다. thumb pose 변화가 중력/동역학에 영향을 주므로 다른 목표를 유지해도 실제 상태나 첫2초 trace의 동일성을 미리 인증하지 않는다.

## Suggestion

없음. 현재 narrow diff에서 새 native 시험을 막는 구현 오류를 발견하지 못했다. 실제 카메라·모습·접촉·타현 검증을 다음 단계에서 수행한다.
