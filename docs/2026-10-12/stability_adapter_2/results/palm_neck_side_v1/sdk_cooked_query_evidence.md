# 설치된 Isaac Gym 공개 API의 cooked 형상 조회 범위

이 단계의 읽기 전용 SDK 조사에서는 공개된 rigid convex cooked vertex/local transform/
bounds 조회 API를 찾지 못했다. 없다는 구현 전체 증명이 아니라 설치본의 공개 API
문서와 Python wrapper 범위에 대한 결과다. 새 native 초기화/물리 step은0이다.

- [body→shape span](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:2281)
- [actor shape properties](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:2336)
- [asset shape properties](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:2956)
- [RigidShapeProperties](/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html:648) — filter/friction/contact/rest offset 계열
- [triangle 조회](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:2527)와
  [particle triangle](/home/ajou/yigyu/3/isaacgym/docs/api/python/gym_py.html:4086)은 soft/deformable 범위다.
- [mesh cooking 기본값](/home/ajou/yigyu/3/isaacgym/docs/_sources/programming/assets.rst.txt:62)은
  triangle mesh의 single convex hull을 설명하지만 OBJ unused vertex 취급을 명시하지 않는다.
- [collision camera 옵션](/home/ajou/yigyu/3/isaacgym/docs/api/python/struct_py.html:1443)과
  [collision mesh visual 사용](/home/ajou/yigyu/3/isaacgym/docs/_sources/programming/assets.rst.txt:78)은
  렌더 옵션이며 형상 vertex query나 관통 인증은 아니다.
- [native wrapper import](/home/ajou/yigyu/3/isaacgym/python/isaacgym/gymapi.py:63)는 compiled symbols를 불러온다.

Source OBJ의 face-used vertices로 만든 hull과 기존 all-vertex hull 결과는 별도 기록한다.
두 source 결과의 차이를 PhysX 오류라고 단정하지 않는다. 이번 실제 native 접촉 대조는
`facet_native_first/probe.json`과 `facet_native_short/probe.json`이다. 첫step LH:palm–넥
4manifold 점은 raw lambda0이며 후기 접촉은 소실한다. `initialOverlap`, `minDist`는
그 이름만으로 측정 관통 깊이나 하중으로 환산하지 않는다. camera 역시 가려짐이 있으므로
초기 무관통의 단독 증거로 사용하지 않는다.
