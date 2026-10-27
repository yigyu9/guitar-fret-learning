# 사용자 허용 범위 안에서 연주하는 기준

![기존 수평 넥 0도 후보의 t=0 실제 Isaac Gym 정면 이미지](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/horizontal_neck_initial_v1/native/scene/candidate_001/front.png)

사용자는 지정한 넓은 기타 상태 범위 안에서 초기점의 정확한 복귀보다 연주를 우선하기로 했다. 위 이미지는 이전 단계의 t=0 native 정적 촬영을 재사용한 것이다. 범위 박스나 접촉·관통 인증은 포함하지 않으며, 이번에 이미지나 물리 실행을 새로 만들지 않았다.

범위의 위치 기준은 기타 전체 형상이나 바디 중심이 아닌 **world 기타 actor-root**다. 위치 범위는 X `[-0.50, -0.15] m`, Y `[-0.15, 0.15] m`, Z `[0.65, z_chest] m`이며 `z_chest`는 초기 Chest rigid-body origin 높이의 근사치(과거 기록 약 `0.883738 m`)로 이후 환경 초기화 때 다시 확인한다. 회전은 extrinsic Euler xyz X `[45,90]°`, Y `[50,100]°`, Z `[135,180]°`가 만드는 회전 집합으로 정의한다. 이전 임시 `30 mm/5°` 경계나 이번 넥 회전 비교의 ±10°로 줄이지 않는다.

수평 넥 후보 quaternion xyzw `[-0.5, 0.5, 0.5, 0.5]`는 Euler xyz `[67.5, 90, 157.5]°`와 같은 회전이며 위치 예시는 기록된 범위 안에 있다. 두 표현의 오프라인 동치 오차는 `1.1017764609091714e-14°`였다. Y=90°의 Euler 특이점 때문에 단일 `as_euler()` 결과를 축별로 직접 비교하지 않는다. 이 확인은 저장된 pose의 범위 포함 설명이며, 회전 판정기나 런타임 기능 구현은 아니다.

현재는 설계 계약만 정했다. 범위 안에서 내부 초기점 복원 비용은 0으로 두고 fret/strike 연주를 우선한다. 경계 접근이나 이탈에는 경계 여유와 기타 속도에 따른 부드러운 보정을 설계하지만 임계값은 정하지 않았다. 범위 밖 복귀도 작은 떨림이나 한 번의 경계 교차만으로 즉시 종료·초기화하지 않도록 설계한다. 동결 fret/strike 목표와 보정은 하나의 최종 관절 목표로 합치는 구조를 의도하며, 별도 PD 제어기를 둘로 나누지 않는다. 이 판정·보정·목표 합성 구조는 아직 구현되지 않았다.

기타 고정, 손 부착, 지속적인 pose 덮어쓰기는 사용하지 않는다. 범위 포함만으로 연주 정확도, 손 도달, 접촉, 관통, 안정성을 인증하지 않는다. 사용자 결정과 다음 설계는 [계약 문서](/home/ajou/yigyu/3/stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md:1), 확인 근거는 [phase verification](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/playable_envelope_contract_v1/verification.json)에 기록했다.
