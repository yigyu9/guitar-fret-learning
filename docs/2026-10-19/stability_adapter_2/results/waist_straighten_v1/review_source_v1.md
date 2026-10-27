# 추가 허리 완화 Source 결과·자세 분석기 검수 V1

요약 판정: **문제없음**. Critical: 0 / Warning: 0 / Suggestion: 0. 추가4°/8° 두 수락 후보의 기존 runner를 이용한 각5초 정지 native 비교로 진행 가능하다. 이는 Source/분석기 검수이며 실제 자세 유지 성공 판정은 아니다.

## Source 결과 검수

실제 결과 경로는 `search_v1/search.json`이다. 입력752개 SHA가 모두 현재 파일과 같고 selected2개/native_runs0이다. 사전 검수751개 경로에 새 분석기 Python이 추가된 범위도 실행 입력에 포함됐다. 실제 수락 gate를 저장된 원자료로 재계산해 두 후보 수락과 일치했다.

| 현재4° 기준 대비 후보 | Chest localZ 투영° | Thorax gap mm | 상완 전체 gap mm | 전완 gap mm | waist gap mm | 현재 elbow origin 목표 오차 µm |
|---|---:|---:|---:|---:|---:|---:|
|추가4°|57.412311|5.391771|0.800601|22.891186|0.300093|0.786978|
|추가8°|53.412312|7.408545|0.801072|22.909369|0.300093|1.432802|

- [search_waist_straighten_v1.py:114](/home/ajou/yigyu/3/stability_adapter_2/search_waist_straighten_v1.py:114): body 목표 오차/tilt·waist·full source clear·capsule 최소 gap·상완 근위 gap·전완12mm·자연 팔·head/왼손목·finger42·모델 한계를 모두 통과한다. Thorax 최대3mm와 의무적 elbow 접근 gate가 남아 있지 않다. 실제 작은 음의 elbow 접근축 투영(−0.189/−0.343µm)은 수치상 현재 origin을 유지하는 fit 결과이며 수락을 막는 잔존 조건이 없다.
- 후보 config 전체는 이전4° config에서 candidate 경로/SHA 및 elbow amplitude0을 설정한 값과 exact하다. native controller/PD/cap/모델/strap 조건 변경이 없다. 후보의 joint 각과 해당 audit row/EnvironmentContract float32 q가 exact하며 각 그룹 변화는 허용 bounds 안이다.
- 기준 native에서 독립 재구성한 FK와 candidate 예측 pose 최대차이는 위치 <2.78e−16m/회전 <8.46e−16rad다. finger42 q는 exact, lower/hip은 고정 FK 기준이다. G39 예측 상태는 현재4° native 기준과 최대 위치2.24e−16m/회전0rad 차이로 같다. 부동소수점 round-trip을 byte-exact native 재현이라고 표현하지 않는다.
- 입력751→752개의 추가 항목은 새 분석기이며 기존 소비 source/geometry가 변경됐다는 뜻이 아니다. 새 source SHA는 사전 검수와 같다. 기타 source 비겹침과 실제 cooked/5초 유지 검증은 분리한다.

## 새 실제 자세 분석기

- [analyze_waist_straighten_v1.py:29](/home/ajou/yigyu/3/stability_adapter_2/analyze_waist_straighten_v1.py:29): 원래 waist/직전4° 실제 초기값, 각case initial/final/report, pose helper·self SHA를 읽기 전에 기록하고 종료 재검사한다. 현재4° native와 동일 human/joint 순서를 요구하고 completed report를 소비한다.
- [analyze_waist_straighten_v1.py:45](/home/ajou/yigyu/3/stability_adapter_2/analyze_waist_straighten_v1.py:45): Torso/Spine/Chest 각각의 localZ를 고정 human world 앞축과 up으로 투영해 초기/최종 기울기를 계산한다.61행의 parent inverse × child 상대 회전 차이와 분리하며 임상 spine 각도 또는 DOF scalar 합으로 설명하지 않는다.
- [analyze_waist_straighten_v1.py:66](/home/ajou/yigyu/3/stability_adapter_2/analyze_waist_straighten_v1.py:66): G39 body 수를 양쪽에서 확인하고 초기 위치/회전 차이를 각각 원래waist 및 직전4° 기준과 비교한다. 기존 native 허용차를 적용한다. 현재 대비 추가 완화와 원래 대비 전체 변화는 서로 다른 `comparisons`로 기록한다.
- AST 문법 검사 통과. 분석기 실행은 검수자가 수행하지 않았으며 실제 결과값은 native 완료 후 대조한다. body9 scalar 변화가 필요한 보고에서는 별도 q/명령 원자료 값으로 표시하고 이 proxy/relative rotation과 혼동하지 않는다.

## 검수 SHA256

- 새 분석기: `e525f6ee200680f858e5bc00b59480a4ff540700e556cb6bc0c4da72288c4e31`
- 추가4° candidate: `34e10c1f073caa09e7dfd1500f6158cbbde105310795e58935319bd524fef0c5`
- 추가4° config: `7f63a3898c454cd03242ad1c64c8eff8f2fbca2c3cb30632c956af8843e5d29b`
- 추가8° candidate: `5422e05661175cd945f9fe73ce626d24309f12330e3abc962c9f149fee2ad520`
- 추가8° config: `1f076a6f30cd516d2b8dd18f54440f887ef672b5daa0e4ad7a5359851c18656f`

원자료를 읽어 검산했으며 Source/native/producer 재실행·원본 수정 없이 지정된 이 검수 파일만 생성했다.
