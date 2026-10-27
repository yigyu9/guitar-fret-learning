# 왼손 넥 세 면 배치 source 사전 검수

요약 판정: 문제없음. frame/normal 부호와 세 면 gate는 요청과 일치한다. 완료 V2의 두 후보는 거절됐으므로 현재 native로 진행하지 않는다.

Critical: 0

## 확인 근거

- [계획:5](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_PLAN_V1.md:5)와 실제 G축은 일치한다. +GX world=[−.01116,.08716,−.99613]로 아래쪽,−GZ=[−.000976,−.99619,−.08715]로 뒤쪽,+GZ는 앞쪽이다. [면 helper:32](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:32)의 palm outward [1,.0163159,0]는 taper된 +GX 측면,thumb outward−GZ/fingers outward+GZ다. facet은 반대방향으로 넥을 바라보므로 alignment=facetNormal·(−outward)가 올바르며 palm world normal 위반구 검사도 별도다.
- [V2 gate:132](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v2.py:132): 전체 source clear/frozen48/6facet 오차<10mm/plane gap2..12mm/alignment>.3/palm normal worldup/왼팔4 ballnorm<160°를 모두 요구한다. 초기 fit의 thumb2≤80/thumb3 0..55° 및 모델 교집합도 유지한다. 실제 두 행을 FK로 재계산해 facet gap·alignment·target 오차와 최종 수락 논리를 대조했고 일치했다.
- source V2는 station20/60 두 후보로 닫혔다. station20은 whole source clear=False 및 면오차138–227mm로 거절. station60은 whole source clear=True이나 thumb gap15.200/error11.200mm,index gap−35.556/error41.690mm 및pinky alignment .180934 등 gate 미달로 거절한다. 두 행 frozen48=True, 모델 범위 내이며 selected=[]/native_runs=0다. 엄지각 완화 또는 whole clear만으로 면 관계 성공이라고 하지 않는다.
- [V2 사전 pin:39](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v2.py:39)은 anchor→CFG/manifest→XML discovery→전체 선언 mesh·candidate/reference pin→contract/FK 순서다. 현재832개 입력 SHA 변경이 없다. V2 AST를 확인했다. 원 source/결과를 수정하거나 최적화/native를 재실행하지 않았다.
- [historical warmstart:61](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v2.py:61)는 현재 candidate의 과거 row에서 왼33각만 사용한다. 새 판정은 current baseline FK/G/형상에서 계산하며 나머지48각·G 초기조건·자산·controller를 변경하지 않는다. V1 없는 warmstart 경로 실패는 geometry/native0인 setup 실패로 분리해 보존한다.

## Warning

- [계획:5](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_PLAN_V1.md:5)의3..12mm 문장과 [계획:7](/home/ajou/yigyu/3/stability_adapter_2/LEFT_NECK_THREE_FACE_PLAN_V1.md:7)의2..12mm gate가 다르다. 현재 코드는 후자의 strict2..12mm를 사용한다. 이번 두 후보는 모두 거절돼 실행 영향은 없으며 후속 leaf/완료 설명에서는 하한을 명확히 통일한다. 소비 원본을 소급 편집하지 않는다.
- [면 helper:30](/home/ajou/yigyu/3/stability_adapter_2/left_neck_near_geometry_v1.py:30)은 유한면 내부 기준점·plane gap/point target error를 사용한다. 실제 최단거리나 피부 패드·접촉/압현 인증이 아니며 selectedfacet의 해부학적 정체도 미검증이다. 표면 x/y clip과<10mm target 오차가 finite face 전체 containment를 엄밀히 인증하는 것은 아니다. native 초기/2/5초 actual facet·영상·접촉으로 관계를 다시 확인해야 한다.
- [proxy:77](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v2.py:77)의 mj_geomDistance는 정적 최적화 보조다. [최종 LP:131](/home/ajou/yigyu/3/stability_adapter_2/search_left_neck_three_face_v2.py:131)는 fresh 예측 상태로 전체 겹침을 별도로 판정하지만 cooked/native clearance는 아니다. optimizer 실패를 모든 왼손33 자세의 불가능 증명으로 확대하지 않는다.
- 현재 요청 범위는 source 사전 검수다. 작성 중 native wrapper의3카메라/240Hz observer/후속 finite wrist currentG 보정은 아직 검수·실행 인증하지 않았다. source 수락 후 별도 단계에서 실제 geometry·LEFT 접촉·G drift·원 detector·초기 frozen48을 확인한다.

## Suggestion

없음. 현 두 후보는 거절로 보존하고 geometry 수정은 새 버전에서 진행한다.
