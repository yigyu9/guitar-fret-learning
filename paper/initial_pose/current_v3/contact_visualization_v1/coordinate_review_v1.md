# 저장 접촉점의 좌표 의미 검수

2026-10-17. 독립 검수자 `current_pose_materials_review`. 렌더링·새 물리 실험 없이 설치 문서, 기존 helper와 29초 원자료를 대조했다.

**결론: 이 자료의 접촉점은 `p_world = p_body + R_body(localPos)`로 변환한다. native COM offset을 추가하거나 빼지 않는다.** 회전은 해당 저장 body의 quaternion을 정규화해 사용한다. 기타 actor root가 아니라 접촉 레코드에 이름이 기록된 각각의 body pose를 사용한다.

## 근거

- 설치된 [Isaac Gym RigidContact 문서](/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html:868)는 local_pos0/1을 각 body의 local contact feature 위치로 정의하며 두께를 제외한다고 설명한다. normal은 body0에서 body1으로 향하는 world 벡터다. offset0/1은 별도의 local feature-to-surface 변위이며 마찰이 적용되는 위치에 관한 값이다. 따라서 feature 표시에는 offset이나 minDist를 임의로 더하지 않는다.
- 같은 문서의 [RigidBodyProperties.com](/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html:381)은 COM을 body space의 별도 값으로 정의한다. 문서의 local space 표현만으로 모든 백엔드 내부 좌표를 확정하지 않고, 아래 실제 양측 접촉점 일치로 현재 저장 자료의 변환을 검증했다.
- 기존 [guitar_relative_readiness_v2.py](/home/ajou/yigyu/3/stability_adapter_2/guitar_relative_readiness_v2.py:42)와 [analyze_right_thigh_waist_v1.py](/home/ajou/yigyu/3/stability_adapter_2/analyze_right_thigh_waist_v1.py:28)도 body pose와 localPos를 직접 합성하며 COM을 사용하지 않는다.

## 실제 원자료 대조

대상은 `native_free_strike_v14`의 `states240.json` 및 `contacts240.json`, 동일 physics step 6960·29초다. 두 gzip 파일에서 해당 행을 직접 읽고 initial_values의 body 이름과 native_properties의 COM을 사용했다.

이 시각의 기타–인체 raw contact는 8개이며 positive raw lambda 7개, zero lambda 1개다. 같은 위치가 반복된 항목도 있으므로 8개의 독립 접촉 부위나 고유 물리점이라고 설명하지 않는다.

COM을 사용하지 않으면 두 body에서 독립적으로 변환한 접촉점의 차이는 모두 약 `8.1e-8m` 이하로 일치한다. COM을 추가하면 허벅지 접촉의 양측 점 차이가 약 203mm, 상완 접촉은 약 152mm까지 커진다. COM을 빼는 경우에도 같은 크기의 불일치가 생긴다.

| 대표 접촉 | 기타 측 세계 feature 위치(m), 반올림 |
|---|---|
| G:body – R_Hip | `[0.132522794, 0.084637515, 0.521767546]` |
| G:body – Spine | `[-0.025650630, -0.119042782, 0.812136787]` |
| G:body – R_Shoulder | `[0.232861536, 0.079516470, 0.877974150]` |
| G:body – Chest | `[-0.002993665, -0.112096488, 0.820152349]` |

## 표시 지침과 한계

기타 측 변환점을 마커로 사용하거나 양측 점의 평균을 사용하되, 선택한 규칙과 양측 점 잔차를 기록한다. 접촉 레코드·상태 행은 반드시 같은 physics step으로 대응시킨다. raw contact와 positive lambda contact는 표시나 범례에서 구분하며 raw lambda를 임의로 뉴턴 단위로 환산하지 않는다.

이 좌표 검수는 접촉 feature 마커 위치를 확인한 것이다. source visual 표면, source collision mesh, PhysX cooked 표면과 contact offset을 모두 동일하다고 증명하지 않는다. `initialOverlap`은 문서상 time-step 시작 시 normal 방향 overlap이며, 이를 현재 source visual의 침투 깊이로 바꾸어 해석하지 않는다. source 시각화에서 마커와 표면이 벌어져 보이면 위 범위를 구분해 설명해야 한다.

원본·코드·실험 상태는 수정하지 않았다.
