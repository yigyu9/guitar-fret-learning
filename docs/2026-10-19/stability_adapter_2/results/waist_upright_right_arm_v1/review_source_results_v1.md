# waist 자세 Source V3 결과·native 진입 검수

요약 판정: **문제없음**. Critical / Warning / Suggestion 없음. `relief4_arm8mm`와 `relief2_arm5mm`의 기존 runner를 이용한 각5초 정지 native 비교로 진행 가능하다.8° 후보는 계속 거절한다. 검수 시 native 실행0이며 Source 통과를 cooked clearance 또는 유지 성공으로 해석하지 않는다.

## 결과와 수락 조건

[search_waist_upright_right_arm_v3.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_waist_upright_right_arm_v3.py:114)의 수락 조건을 저장된 원자료로 재계산해 세 후보의 수락/거절과 일치했다.

| 후보 | Chest 기울기 감소° | 팔꿈치 축 투영 mm | bbox 거리 감소 mm | Thorax gap mm | 상완 전체 gap mm | 전완 gap mm | 수락 |
|---|---:|---:|---:|---:|---:|---:|---|
|4°/8mm 요청|3.999999|3.134946|3.119256|2.415592|0.076092|22.866546|수락|
|8°/12mm 요청|7.999998|4.269068|4.245703|4.673177|-0.138095|22.738357|거절|
|2°/5mm 요청|2.000000|2.096376|2.089926|1.119876|0.469325|23.047395|수락|

수락 두 후보는 body 방향 오차·Chest 기울기 감소·팔꿈치 접근25%·실제 거리 감소25%·waist·상완 근위30%·전완·자연 팔 모양·왼손목·머리·source 비겹침·finger42·native 한계를 모두 통과한다. 요청8/5mm에 대한 실제 접근은3.135/2.096mm이며 요청량 전체를 달성했다고 표현하지 않는다.8° 후보는 Thorax <3mm 및 전체/근위 상완 양의 여유 조건을 통과하지 못한다. 이 후보는 source LP audit의 `source_clear=true`만으로 사용할 수 없다.

## 입력·후보·초기 배치 확인

- `search_v3/search.json`의 입력750개 SHA를 현재 파일과 전수 대조해 변경0개였다. Source V3 및 계획 V3 SHA는 사전 검수 기록과 같으며 geometry/human/guitar 입력과 원본 V2도 보존됐다.
- 선택 config의 candidate 파일 SHA와 `EnvironmentContract` 입력 SHA 검증이 통과했다. config 전체는 기존 waist config에서 candidate 경로/SHA와 elbow amplitude0만 바꾼 값과 정확히 같았다. 후보 row는 `search.json`의 해당 수락 row와 같다. 실제 PD/controller/cap/물리 설정을 바꾼 후보 config가 아니다.
- 기준 native에서 독립 재구성한 FK와 두 candidate의 예측 human pose 최대차이는 위치 <2.55e-16m, 회전 <7.32e-16rad였다.81개 이름 순서·float32 초기각·모델 한계·각 그룹 초기각 변화 범위를 확인했다. root/하체의 FK pose 차이는0, finger42 초기각은 exact다. R_Elbow_y 모델 한계 여유는 각각37.7726°/37.7617°로 ±5°보다 크다.
- 기타 root 초기 p는 기준과 exact, 회전 SO3 차이는0이다. G39 예측 body는 기준 강체 배치와 최대 위치6.21e-17m/회전0rad 차이로 같다. 변환 helper의 부동소수점 round-trip 차이까지 byte-exact라고 표현하지 않는다. 모델 형상/질량·hip pose·waist gap0.300049mm는 기존 기준을 유지한다.

## native 비교의 제한과 재검증

4° 후보의 상완 source 간격 **0.076092mm**는 gate 최소0.05mm보다 약0.026mm 클 뿐이다. 이것은 source proxy의 양의 간격이며 cooked 형상 또는 실제 동작의 안전 여유를 인증하지 않는다.2° 후보의 source 간격0.469325mm도 실제 접촉 유지 인증은 아니다.

[run_right_body_approach_v1.py:88](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:88)의 기존 실제 초기 invariants/FK/source 검사를 통과해야5초 진행한다. 초기 cooked 접촉·관통 가능성, 이후 기타 이동/회전과 양팔/몸통 움직임·허벅지/두 블록 접촉을 실제 기록으로 판정하며 기존 안전 중단을 유지한다. native 결과 없이 안정 후보 선택이나 팔꿈치 동작 성공을 선언하지 않는다.

## 수락 후보 SHA256

| 후보 | candidate SHA256 | config SHA256 |
|---|---|---|
|relief4_arm8mm|`7870cba52419d969ca796b52d873cc109877a4cf1b11d0725dfffac873c0c4f5`|`ccd5ca5663154696d0cb68786eaf32709ec8e1ff19f86b5e5d89a43aca454653`|
|relief2_arm5mm|`08b70b1079645341af7270a48e321600090c1338a8594ac8e46d3a1b7c5ee5d7`|`8aa5025b06d4a390e47a6febd1c0c3b64015f41df9d871dc10160470640d6ed5`|

수치 검증은 저장된 Source 결과·candidate/config·기준 native 초기값을 읽어 수행했다. 검색/native 재실행 또는 원본 수정 없이 지정된 검수 기록만 생성했다.
