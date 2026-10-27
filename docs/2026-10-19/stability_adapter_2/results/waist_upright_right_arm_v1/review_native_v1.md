# waist 척추 완화·오른팔 접근 실제 결과 독립 검수 V1

요약 판정: **문제없음**. Critical / Warning / Suggestion 없음. Source 수락/거절·실제 초기 자세·3회 native 명령/waist/기타 변화·팔꿈치 비교가 원자료와 일치한다. 요청 방향의 초기 자세 후보와5초 비교를 확인한 판정이며, Thorax 지속 지지 또는 장기 안정·연주 성공 인증은 아니다.

## 검수 범위와 보존

새 search V2/V3 결과, 수락 candidate/config, 세 native 초기/최종 상태·명령·접촉·녹화, `analysis_final_v1/analysis.json`, `posture_final_v1.json`을 검수했다. 기존 runner/controller는 수정하지 않았다.

- Source V2는3후보 모두 거절, V3는4°/2° 수락·8° 거절이며 이전 검수에서 재계산한 gate와 같다.8°는 Thorax4.673mm와 전체 상완−0.138mm로 거절 유지한다.4°/2°의 실제 초기 팔꿈치 접근을 요청8/5mm 전체 달성으로 표현하지 않는다.
- V2/V3·static/final 분석·static/final posture의 입력8개 map을 병합한 고유3334개 파일 SHA가 모두 현재와 일치했다. 각 native attempt의1402개 입력 SHA도 변경0개다. 실행 당시 소비된 원본과 결과가 보존됐다.
- 세 report는 모두 `completed=true`, 각1200 physics/300 control/5.0초, 금지 호출0, 입력 변경0, strap OFF, checkpoint 연결0, 학습0이다. 합계는 **3회/3600 physics/900 control**이다.

## 실제 명령3600행 독립 재계산

[run_right_body_approach_v1.py:88](/home/ajou/yigyu/3/stability_adapter_2/run_right_body_approach_v1.py:88)의 초기 검증 결과는 세 case 모두 invariants/FK/source audit 통과다. 실제 초기 driveMode는33 EFFORT+48 POSITION이다.

모든240Hz 명령 행에서 아래 항목을 저장된 수치로 재계산했다.

- right 제출 벡터에 left 요청을 native effort cap으로 제한해 결합한 값이 두 블록 처리 전 벡터와 exact하다.
- 두 근위점의 K/D virtual request와40/10N cap, Jacobian 기여·기존 task 제거 후 right 요청, float32 cap 결과가 저장된 중간 벡터와 일치한다.
- body9 gravity Jacobian 합·근위 task·실제 scalar PD·cap 결과가 최종 제출81벡터 및 tracking 최종벡터와 exact하다. 소유한33관절 외48개의 effort는0이며 모든 관절 cap을 지킨다.
- 각 physics 행의 elbow target/target velocity가 기록한 단일 R_Elbow_y sine 목표와 exact하다.900개 POSITION 행의48개 목표 readback 및 상태 보존 검사도 통과한다.
- 각 case의 final root/하체 native body state는 자체 초기 상태와 exact하다. 초기 finger42/모델 질량/PD/기타 배치·한계 검증도 모두 통과한다. source 비겹침을 cooked 관통 깊이 인증으로 확대하지 않는다.

이 검사에서 virtual request 단위N과 native 접촉 `lambda`를 구분했다. `lambda>0`은 양의 raw 값 유무이며 접촉힘N으로 변환하지 않았다.

## 실제 자세와 기타 변화

원자료 trace와 실제 초기/최종 body pose에서 bbox/SO3/Chest 투영값을 독립 재계산하고 최종 분석과 대조했다.

| 실행 | 기타 bbox 최대 이동 mm | 기타 최대 SO3° | body9 scalar 최대 변화°(240Hz) | 실제 elbow scalar 범위°(2.5–5초,60Hz) |
|---|---:|---:|---:|---:|
|4° 정지|14.545447|8.012684|2.451027|0.035913|
|2° 정지|17.004627|8.473343|2.902462|0.041131|
|4° + elbow 목표±5°|14.545447|8.012684|2.451027|10.078053|

두 정지 시험의 최대 이동·회전이 더 작은4°를 이번 비교 대표로 선택한 근거는 수치와 일치한다. 이는 모든 지표의 우위·반복 재현성·장기 유지 성공을 뜻하지 않는다.

4° actual 초기 Chest localZ 전방 투영은 baseline65.412311652°→61.412311100°로4.000000552° 줄었다. 실제 팔꿈치 bbox 거리 감소는3.119324mm, 접근축 투영은3.135013mm다. 초기 body9 **최대 scalar 차이1.437230603°**와 Pelvis→Torso / Torso→Spine / Spine→Chest **상대 회전 차이0.999995°/1.499986°/1.500019°**는 다른 양으로 별도 보고됐다. 초기 G39 최대차이는 위치0.111510µm/회전1.300877e−7rad로 native 초기 허용차 안이며 byte-exact 기타 상태로 표현하지 않는다.

4° 정지의 최종 Chest 투영은63.364036896°, elbow5는63.384213599°다. 초기 완화각 전부가5초 동안 그대로 유지됐다고 쓰지 않는다.4° 정지의 runtime Chest world 회전 최대차이3.925893°도 body9 scalar 최대차이2.451027°와 구분한다.

## elbow 비교의 정합성

4° 정지 config와 elbow config의 유일한 설정 차이는 `elbow_motion_amplitude_rad: 0→0.08726646259971647`이다. 초기 전체 값이 exact하며 첫2.5초까지 trace151개가 exact하다. 실제 sine 목표는2.5–4.5초의1주기이며 DOF suffix를 world축으로 해석하지 않는다.

같은 시각의 정지 대비 elbow 시험 차이는 기타 bbox최대 **0.180524888mm**, SO3최대 **0.083761575°**다. 두 시험의 절대 최대14.545mm/8.013°는 같은 첫2.5초 구간 peak로, elbow 영향이 수치상0이라는 뜻이 아니다.

## waist·접촉·녹화

세 case의 physics endpoint3600행에서 actual 기타 root/body pose와 접촉 local 좌표로 waist 영역을 재계산했다. 각 case의 waist 양의 raw lambda 접촉은1198/1200회, 마지막0.5초120/120회다.

세 case 모두 마지막0.5초 Thorax 접촉 **0/120**, 상완 접촉 **120/120**, waist 접촉 **120/120**이며 전 구간 right forearm/distal 기타 접촉은0이다. 상완 후기 endpoint-clamped proximal30 통계도120/120이다. Thorax+상완 두 블록의 후기 지속 동시 지지는 회복되지 않았다. 이 결과를 숨기거나 Source gate 통과만으로 두 블록 유지 성공을 선언하지 않는다.

세 capture의 physics step은0,8,…,1200이고 상태 보존 flag453개가 모두 true다.906개 raw PNG SHA를 전수 확인했고6개 native MP4는 각30fps/151frames/5.033333초 및 report SHA와 일치했다.4° elbow 시험의 실제 처음/마지막 whole-body PNG도 열어 확인했다. 영상 길이5.033초와 물리5.0초를 구분한다.

## 최종 검수 입력 SHA256

- `analysis_final_v1/analysis.json`: `5aa490d730399f7a7c48975070d5baf6efb05e857773283438a48b39f137d5f8`
- `posture_final_v1.json`: `274bf2881d450addcd04e2e62c3f0eec3005a741b12780049e5dc6786d606eec`
- `config_v1/relief4_elbow5.json`: `65ac6275c6e57046e9aee7d532cf390fedf584b7512f2364483b87a09097a6e6`

검수자는 원자료/producer/계획을 수정하거나 물리/후처리 producer를 재실행하지 않았다. 저장된 자료를 읽어 독립 검산했고 지정된 이 검수 파일만 생성했다. 최종 phase inventory/source_final 봉인은 root 담당 범위다.
