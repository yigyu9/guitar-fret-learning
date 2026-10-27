# 저장 몸체 pose 직접 시각화 사전 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`.

**요약 판정: 문제없음. replay_v8 + static_visual_v7로 미리보기 렌더링을 진행할 수 있다.** 실제 화면 품질과 전체 프레임 검증은 후속 작업이다.

## 검수 대상과 SHA-256

- [replay_v8.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/replay_v8.py): `d2509d9b5de8c44b371e06366487909fdd0e3b7861c16bdb816c31ea89e05eee`
- [static_visual_v7.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/static_visual_v7.py): `2a2855f6c14bad20db8ed50ba5506b0d4c00fd6298dddfc0d3d98eed981029bb`
- 재사용 순수 helper [replay_v6.py](/home/ajou/yigyu/3/stability_adapter_2/initial_pose_video60_v1/replay_v6.py): `17f6bcf5008ef1ed1334acadea31baa268ea9a8b04a5ef150dac58df353b0d09`
- [BRIEF_v3.md](/home/ajou/yigyu/3/paper/initial_pose/current_v3/presentation_60fps_v1/BRIEF_v3.md): `fed5addc661f93b47c06baad3b4572b634419177ca6ff4ba40275337baea24d5`

## 구현 확인

각 기록 body를 world의 직접 자식으로 배치하고 저장 p와 정규화 quaternion을 적용한다. 관절을 생성하지 않으므로 인체 관절 FK를 통해 자세를 재구성하지 않는다. `mj_kinematics`와 `mj_camlight`만 호출하며 `mj_step`은 차단한다. Isaac Gym scene이나 새 접촉·힘 계산은 생성하지 않는다.

원 XML과 저장 이름을 독립 대조해 human 66개, guitar 39개가 모두 대응하며 누락 또는 추가 source body가 없음을 확인했다. 의자 1개를 더해 총 106개다. 실제 두 XML의 각도 단위는 degree이며, mesh scale 및 선택한 geom의 local 위치·회전·크기·fromto 속성을 유지한다. 의자는 기록 pose와 초기 half-size를 사용한다. 원 source에서 alpha 0인 geom을 제외하고 명시 group 1 visual을 중복 collision geom보다 우선하는 선택을 제작 메타데이터에 공개한다.

인체·기타·의자 world pose를 프레임마다 readback하고 `1e-9m/rad` 오차와 clock 0을 검사한다. 렌더링 전후 body 위치·회전·clock의 불변을 검사한다. 여섯 현은 기록된 양 끝 body 위치를 잇는 3D capsule로 추가하므로 장면의 깊이 처리를 받는다.

원 모델 XML과 선언 mesh의 expected SHA 대조, 직접 읽는 자료·코드·폰트·brief의 전후 SHA 검사, 240Hz stride 4 표본 선택, 전환 후 인코딩 인덱스 60 보정을 유지한다. 보고서에는 MuJoCo source geometry 시각화이며 Isaac Gym cooked rendering 또는 physics replay가 아님을 명시한다.

## 독립 CPU 확인

MuJoCo 3.2.3에서 Renderer나 그래픽 context 없이 모델을 생성해 `nq=nv=0`, 106 body mapping, 84 geom을 확인했다. 두 실행의 원 자산 SHA 각각 106개가 일치했다.

| 원 실행·시각 | 최대 위치 오차 | 최대 회전 오차 | clock |
|---|---:|---:|---:|
| free_strike 17초 | 0m | 5.087710622580481e-16rad | 0초 |
| free_strike 29초 | 0m | 4.002966042486721e-16rad | 0초 |
| regrasp 44초 | 0m | 4.440902686916832e-16rad | 0초 |

위 세 표본은 저장 gzip에서 독립적으로 읽어 실제 helper로 배치하고 검사했다. 재접촉 첫 인코딩 프레임 1440 및 마지막 1979도 재확인했다. GPU·Isaac Gym·Renderer·시간 적분은 호출하지 않았다.

Critical / Warning / Suggestion: 현재 미해결 항목 없음.

## 후속 확인

미리보기에서 정면 전신 구도, 양손·기타·발의 가시성, source visual 형상과 3D 현의 깊이 처리, 자막 배치를 확인한다. 전체 제작에서는 1,920개 저장 표본의 pose readback, 입력 SHA 불변, 전환 카드 60개를 포함한 1,980프레임·60fps·33초 및 영상 decode를 확인한다. 기존 native 재생 실패와 물리 실험 판정은 보존하며 이 시각화를 새 물리 성공이나 원 native camera 녹화로 설명하지 않는다.

검수자는 기존 코드·원자료를 변경하지 않았으며 이 검수 문서만 작성했다.
