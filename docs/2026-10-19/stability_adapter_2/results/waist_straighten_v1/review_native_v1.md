# 허리 추가 완화 실제 두 시험 독립 검수 V1

요약 판정: **문제없음**. Critical: 0 / Warning: 0 / Suggestion: 0. 두 native 완료·명령·초기/최종 자세·waist 분석은 원자료와 일치한다. 추가8° 선택은 더 펴진 자세와 작은 후기 변화라는 목적에 부합하며 모든 안정성 지표의 우위나 장기 유지 성공을 뜻하지 않는다.

## 실행·보존·초기값

Source2후보 수락, native2회 모두5초/각1200physics·300control 완료다. 합계2400physics/600control이며 파동/학습/checkpoint 연결0, strap OFF, 금지 호출0이다.

- Source/최종 analysis/support/posture4개 input map의 고유2694개 SHA가 현재와 모두 같다. 각 native attempt의1405개 입력 SHA도 변경0개다.
- 실제 초기33 EFFORT+48 POSITION·q_ref/native 초기81각 exact·모델 한계·FK/source/invariants 검증이 모두 통과한다. 독립 재구성한 FK와 실제 초기 pose 최대차이는 추가4° 위치2.23e−7m/회전5.10e−7rad, 추가8° 위치2.71e−7m/회전4.37e−7rad로 허용차 안이다.
- 두 초기값의 root/하체·finger42·질량은 직전4° 기준과 exact하다. 두 최종 root/하체는 각 초기 native 상태와 exact하다.
- G39 초기 위치/회전의 최대차이는 원waist 대비2.112604e−7m/2.601754e−7rad, 직전4° 대비9.996003e−8m/1.300877e−7rad다. 모두 native 허용차 안이며 byte-exact 상태 보존으로 확대하지 않는다.

## 2400행 명령 독립 재계산

모든240Hz 행에서 actual saved body/root pose·COM velocity로 현재 기타 기준의 두 근위점 goal/velocity와 human point/velocity를 다시 계산했다. K/D virtual request·40/10N cap·Jacobian 기여·기존 right task 제거·right/left 결합·body9 gravity/task/scalar PD·최종 cap을 재계산해 저장된 제출81벡터와 일치했다.

최종 effort는 소유한33관절에만 있고48관절은0이며 native cap을 지킨다.600개 POSITION 행은48목표 readback/state 보존을 통과한다. 모든 physics 행의 body9·right posture 목표는 해당 q_ref 정적값이며 elbow amplitude0·목표속도0이다. CPU Thorax 근접 gate를 제거했어도 기존 실제 human Thorax 가상점 task가 유지된 사실을 확인했다. 이 request와 native 접촉 raw lambda를 접촉힘N으로 혼동하지 않는다.

## 실제 자세·기타 변화

trace·초기/최종 body pose에서 bbox/SO3·Torso/Spine/Chest proxy·parent-relative 회전·G39 오차를 재계산해 최종 JSON과 일치했다.

| 현재4° 기준 대비 후보 | 실제 Chest 초기/최종 proxy° | 기타 bbox 최대 이동 mm | 최대 SO3° | bbox2→5초 변화 mm | SO3 2→5초 변화° | body9 scalar 최대변화°(240Hz) |
|---|---:|---:|---:|---:|---:|---:|
|추가4°|57.412325 /59.760315|13.040470|7.353169|1.893491|0.893689|2.777602|
|추가8°|53.412323 /56.421877|12.882340|7.542856|0.381862|0.143808|3.285253|

추가8°는 현재61.412311°에서 실제 초기7.999988° 줄었고 원waist65.412312° 대비11.999989° 줄었다. Torso/Spine 초기 proxy는29.529143°/28.403364°, final은32.244674°/31.474369°다. 초기 완화각 전부가 그대로 유지됐다고 표현하지 않는다.

추가8°의 직전4° 대비 parent-relative 차이는 Pelvis→Torso3.199999°/Torso→Spine2.800007°/Spine→Chest1.999982°이며 원waist 대비4.199994°/4.299993°/3.500002°다. 이는 proxy 기울기나 DOF scalar 합과 다른 양이다. runtime Chest world 회전 최대5.040785°도 body9 scalar 최대3.285253°와 구분한다.

추가8°는 추가4°보다 최대 bbox 이동·2→5초 추가 변화가 작고 자세가 더 펴졌다. 최대 SO3는7.542856°로 추가4°의7.353169°보다 조금 크므로 두 최대 지표 모두 우월하다고 쓰지 않는다. 이번 값은 원waist 정지 최대11.831mm/6.095°보다 여전히 커 원waist 대비 안정성 향상 인증이 아니다.

## waist·접촉·영상

endpoint2400행의 실제 기타 root/body pose와 contact local 좌표로 waist 영역을 재분류했다. 추가4° waist presence1198/1200·양의 raw lambda1197/1200, 추가8°는 presence/양의 lambda 모두1198/1200이다. 두 시험의 마지막0.5초는 waist·상완 각120/120, Thorax0/120이다. 전 구간 오른 forearm/distal 접촉0이며 LH:index2/middle2/pinky3 실제 접촉이 남는다. 왼손 없는 유지·두 블록 지속 지지는 검증하지 않았다.

두 capture의0,8,…,1200 physics step·302개 render 상태 보존 flag를 확인했다.604개 원PNG SHA와4개 native MP4 SHA를 확인했고 실제 ffprobe는 각30fps/151frames/5.033333초다. 물리 시간은5.0초다. 추가8° 전신 첫/마지막 native PNG도 열어 확인했다.

## 최종 검수 SHA256

- `analysis_final_v1/analysis.json`: `dc76a7a770532bfa55a3e113a1982615c6ce58f628f1eca542c500dafa3500c0`
- `posture_final_v1.json`: `4e9f7338fbf37c8d18060cf009831c21a73be3685a1cfadc01d309672872506c`

원자료를 읽어 독립 검산했으며 물리/producer 재실행·source/root/다른 출력 변경 없이 지정된 이 검수 파일만 생성했다. Source clear는 cooked 관통 깊이·반복 강건성·연주 성공 인증이 아니다.
