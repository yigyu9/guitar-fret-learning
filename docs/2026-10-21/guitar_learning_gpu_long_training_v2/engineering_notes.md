# 메모리 개선의 근거와 범위

이전 최종1024 시험은 PPO 메모리 피크를 줄인 뒤에도39업데이트 다음 수집에서 PhysX48MiB 할당 실패와CUDA 오류로 중단됐다.512환경도 업데이트 후 유휴Torch 캐시를 반환한 상태에서 여유 메모리가9.17→1.83GiB로 줄었다. 내부 누수인지 접촉/공간 탐색 버퍼의 고수위 확장인지는 SDK 내부를 직접 측정하지 못해 확정하지 않았다.

이번 최소 변경은 환경마다 인체·기타·의자를 하나의 PhysX aggregate로 묶는 것이다. 실제 asset 합계68강체·145형상을 사용하고 내부 충돌을 허용하는 True를 지정한다. actor 생성 순서·충돌 그룹·shape 필터/접촉 속성·관절 제어·보상·안전 종료·reset은 유지한다. 이는 강체를 서로 물리적으로 부착하는 기능이 아니다. [설치SDK 설명](/home/ajou/yigyu/3/isaacgym/docs/programming/physics.html:143), [공식 PhysX 설명](https://nvidiagameworks.github.io/PhysX/4.1/documentation/physxguide/Manual/RigidBodyCollision.html#aggregates).

원문은 guitar_learning/archive/20261021_before_gpu_aggregate_v1/에 보존했다. GPU backend v3와 scene v3로 계약을 구분하고 aggregate 구성을 checkpoint 입력에 포함했다. 이전v2 저장본은 strict load에서 거부하며 학습 성공을 상속하지 않는다.

독립 준비 검수와 관련CPU42검사,1024환경2회 학습/저장,4환경 실제 강체/DOF/actor 수, 인체·기타 하중, 선택reset 보존을 확인했다. 개선 전후 모든shape 필터/마찰/접촉 오프셋이 정확히 일치했다. 기타 최대 합력은43.2289505/43.2289543N였다. 이 하중은 접촉이 살아 있다는 기능 검사이며 개별 상대 몸체/접촉 witness를 인증하지 않는다. 고정 의자의 양의GPU 접촉 힘을 요구한 최초 검사는 기준 실행에서도 실패해 부적절한 요구를 제거했다. 최초 로그와 검사 원문은 별도 보존했다.

v3 저장본의 전체 nonmetadata 항목(정책·두optimizer·난수·보상 단계)은 정확히 복원됐고 실제v2 저장본은 거부됐다. 이 준비 검사는 장기 메모리 안정성을 증명하지 않는다. 장기 결과는 별도 실행 원자료로 판단한다.

조사 중 `always_use_articulations`를 다음 해결 후보로 검토했으나 채택하지 않았다. 이 옵션은 단일 강체까지 articulation으로 생성하는 설정이다. 공식 논문은 다강체 actor를 기본적으로 reduced-coordinate articulation으로 설명하므로, 인체를 maximal-coordinate에서 전환하는 스위치가 아니다. 과거39강체 기타가 maximal-coordinate 고정 제약 체인이었을 수 있다는 이전 추정은 근거가 없어 철회한다. [NVIDIA 논문 §2.2](https://arxiv.org/html/2108.10470), [설치SDK 옵션 정의](/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html:1065). 이 옵션이 장기 메모리 증가를 고친다는 직접 근거도 찾지 못했다.
