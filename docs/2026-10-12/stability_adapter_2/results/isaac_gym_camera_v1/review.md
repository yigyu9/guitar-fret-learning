# Isaac Gym native camera 독립 검수

검수일: 2026-10-07.

범위: `capture_isaac_gym_initial.py`, 촬영 계획, default/front 실행 기록·producer 사본·PNG·검증 기록 및 이번 결과 문서. 추가 native 초기화·physics 실행 없이 읽기 전용으로 검수했다.

## 요약 판정

**문제없음. 남은 Critical / Warning / Suggestion 없음.** 초기 Isaac Gym camera 이미지 생성 목적과 검증·해석 범위가 일치한다.

## 확인한 근거

- native camera의 `step_graphics` → `render_all_camera_sensors` → image 저장 경로와 cleanup을 검토했다. MuJoCo 렌더나 추가 physics step으로 생성한 이미지가 아니다.
- default/front 두 캡처의 body/DOF 초기 full-state는 이전 self-collision ON의 저장 step 0과 정확히 일치한다. 캡처 전후 상태 불변, 명시적 physics step 0 및 collision-mask audit가 통과했다.
- 각 실행의 73개 입력 SHA, 실행 당시 producer 사본, PNG 출력 SHA를 대조했다. PNG 픽셀 범위와 전신·손 이미지도 직접 확인했다.
- PhysX CPU / GPU pipeline 비활성화와 graphics device 요청값 0을 실제 Vulkan device 식별 결과로 확대하지 않는다. 경고 로그와 카메라 출력의 한계를 문서가 보존한다.

## 지적 및 해소

- `hands_collision.png`의 초기 all-black 설명을 정정했다. 실제 파일은 정상 손 이미지이며 `hands.png`와 byte-identical이다. 별도 collision geometry의 확인 자료로 채택하지 않고, 동일한 이유도 단정하지 않는다.
- [결과 README:9](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/README.md:9)는 body/DOF 상태·mask 검사만 포함하며 native 목표 getter 대조는 수행하지 않았음을 명시한다.
- [결과 README:23](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/isaac_gym_camera_v1/README.md:23)는 이전 ON report 자체가 실행 당시 입력 SHA 목록에서 빠졌음을 공개한다. 최종 verification의 보존 inventory 연결은 사후 대조이며 원 producer의 봉인 범위를 소급해 확장하지 않는다. 원본·이전 산출물 보존 검증 기록도 연결했다.

## 최종 판정

현재 문서·이미지·실행 기록은 서로 정합적이다. 이 자료는 초기 시점의 native visual image이며 접촉력, cooked collider, 충돌 반응, 기타 안정성 또는 연주 성공의 인증이 아니다. 이번 검수 기록을 동결한다.
