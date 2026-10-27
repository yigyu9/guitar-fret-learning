# Isaac Gym 정면 전신 물리 캡처

`front_fullbody_step024.png`는 선택된 `axis_00` 시작 상태와 저장된 팔 PD 목표로 CPU PhysX를 240 Hz에서 24 step(0.1초) 실제 진행한 뒤, Isaac Gym native camera가 직접 저장한 이미지다. 카메라는 world +Y 정면에서 -Y 방향을 본다. physics를 먼저 진행하고 마지막에 렌더했다.

현재 Isaac Gym 장면에는 strap 시각 geometry가 없어 strap은 보이지 않는다. 5초 구간은 이번 캡처에 포함하지 않았다. checks와 입력/출력 SHA는 `capture.json`에 있다.
