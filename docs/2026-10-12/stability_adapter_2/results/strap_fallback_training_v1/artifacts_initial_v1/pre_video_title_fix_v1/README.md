# 스트랩 OFF/ON 초기 정책 비교 산출물

두 조건은 초기 정책 checkpoint 상태다. 기록된 입력 대조에서 ON/OFF의 초기 모델과 RMS는 모든 key가 exact 일치하고, 양쪽 Adam 상태는 비었으며 update/transitions는 모두 0이다. 초기 native 상태도 exact 일치했다. 아래 결과는 스트랩 fallback OFF에서 ON으로 바꾼 비교 관측이다.

## 비교 영상

각 쌍은 같은 시각의 원본 whole_body/hands MP4 492 frames를 그대로 입력해 좌우 분할(hstack)로 다시 인코딩했다. 프레임을 잘라내거나 늘리지 않았다. 왼쪽은 OFF, 오른쪽은 ON이며 영상 길이는 16.4초(30 fps)다.

### 전신 카메라

![전신 카메라 OFF 왼쪽, ON 오른쪽](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_whole_body.mp4)

[전신 좌우 비교 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_whole_body.mp4)

### 손 확대 카메라

![손 확대 카메라 OFF 왼쪽, ON 오른쪽](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_hands.mp4)

[손 확대 좌우 비교 MP4](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/comparison_hands.mp4)

## 실제 native Isaac Gym 원본 프레임

Contact sheet는 `media/raw/frames`에 저장된 native 카메라 원본 픽셀을 사용했다. 각 행의 시각은 같은 capture metadata의 프레임을 짝지었다. 프레임 자체에는 경로나 글자를 합성하지 않았고, 시트 바깥의 한국어 캡션만 추가했다.

![OFF/ON 전신 및 손 확대의 t0, 2초, 5초, 마지막 native 원본 프레임](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/native_raw_contact_sheet.png)

원본 프레임과 SHA-256:
- OFF: `0.0000s`: 00000.png (SHA-256 `4974b21aa6618dca261f572ad50c9e287c1dc244fa67f7b9a503cd73c3dd70f8`); `0.0000s`: 00000.png (SHA-256 `43137b47dc55e5d5be7f5ede5672efa0d9b533c11f11da2e068c6bfbf6f0af95`); `2.0000s`: 00060.png (SHA-256 `71d38f72473aa1c8f86f49256ea28fac830d97fb2841af0081f2428ee616c011`); `2.0000s`: 00060.png (SHA-256 `590a8a8fd9fd57921c55a3fbf7d23be8f0e5e51f1edaa71776c5b2fbf4f94179`); `5.0000s`: 00150.png (SHA-256 `52da81f7bdbd0bae5738cffdbe305dc5714f83fcc6a641155cd0bdd1dc03eb2e`); `5.0000s`: 00150.png (SHA-256 `b9774704ed0e53bafc53c107e8da7f2af4855b85846cb2fc2224003784a0317b`); `16.3667s`: 00491.png (SHA-256 `93b61e6689e13ea3e285ff63b5af4f5ecce675dd7cdc59bd5e260efb8535452b`); `16.3667s`: 00491.png (SHA-256 `26ddb7a64df95fb5ba88a7e5c075d96079d9b75eee00f53688c660202cce51d1`)
- ON: `0.0000s`: 00000.png (SHA-256 `4974b21aa6618dca261f572ad50c9e287c1dc244fa67f7b9a503cd73c3dd70f8`); `0.0000s`: 00000.png (SHA-256 `43137b47dc55e5d5be7f5ede5672efa0d9b533c11f11da2e068c6bfbf6f0af95`); `2.0000s`: 00060.png (SHA-256 `e0dd0f7e1f5f73e4778ba0a48175cd1fddae0e6c517c29bd958fc83a9825fffc`); `2.0000s`: 00060.png (SHA-256 `1da30ed6f34f814977c8365d15a2c35f75cfa4f6ff96d13f722998e373157954`); `5.0000s`: 00150.png (SHA-256 `66b7109cf81d49f808cf1cae0bfe4d4e53a9e131811d7a00e68d06a4237f2a9d`); `5.0000s`: 00150.png (SHA-256 `995c90c8facffd9e3ea51d1b0ccd7d6790f3be54b7f59e93b95a3350848504c6`); `16.3667s`: 00491.png (SHA-256 `cc4c482982b2a2b0f09f2704c402e6136b9a27fbf59e2485ccd7b3564a1ce5e6`); `16.3667s`: 00491.png (SHA-256 `5a41042032a906ea588ef9706e9bf86639db29b9514787a84668d801b828a3f3`)

## 실제 측정 시계열

아래 그래프는 native 수치 기록이며 렌더 이미지 분석이 아니다. 상단은 `controls.json`의 `position_outside_m` 3성분 벡터를 각 제어 시점마다 유클리드 norm 후 mm로 환산했다. 가운데는 `trace.json`의 `quaternion_xyzw`를 t=0 quaternion과 비교한 shortest-arc 각도 `2 acos(|q·q0|)`이며 30 Hz(physics_step 간격 8)만 표시한다. 하단은 `controls.json`의 `strap.last_applied_tension_n` 60 Hz 값이다. 모든 점을 finite/비어있지 않음으로 확인하고 원자료 관측 범위를 축에 포함했다.

![60Hz 범위이탈·30Hz 초기 대비 정확 회전·60Hz 적용 명령 장력](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/artifacts_initial_v1/measured_control_and_rotation_traces.png)

## 결과 비교

| 측정 항목 | 스트랩 OFF | 스트랩 ON |
|---|---:|---:|
| 최대 초기 translation | 1.142949 m | 0.583618 m |
| 최대 초기 회전 | 121.20395° | 96.50422° |
| actor-root 범위 이탈 | 84.01222% | 84.62322% |
| 연속 범위 밖 최장 시간 | 12.55 s | 12.60 s |
| 최대 position outside norm | 1.030781 m | 0.478041 m |
| 양수 last-applied 장력 endpoint 비율 | 0.00000% | 82.17923% |
| 최대 last-applied 장력 endpoint 명령 | 0.000000 N | 29.082695 N |
| strap rest length / 초기 slack | 1.101846972 m / 28.269638 mm | 1.101846972 m / 28.269638 mm |
| physics/control steps; 경과 | 3928/982; 16.3667 s | 3928/982; 16.3667 s |
| settled events / joint success / accepted crossings | 42 / 0 / 0 | 42 / 0 / 0 |

두 조건 모두 3928 physics steps, 982 control steps, full 16.3667 s episode, 42 events를 완료했으며 joint success 0회와 accepted crossings 0회다. ON에서 최대 초기 translation/회전과 최대 position outside norm은 줄었지만 범위 이탈 비율은 84.01222%에서 84.62322%로 늘고 최장 이탈 시간도 12.55초에서 12.60초로 늘었다. 관측은 strap 낙하 감소와 일치하지만 자연스러운 연주 자세·범위 유지 또는 음악적 성공을 보여주지 않는다.

초기 fallback baseline에서 OFF의 strap force calls는 0이며 zero-force submissions도 집계했다. ON의 양수 장력 비율과 최대값은 `last_applied_tension_n`의 60 Hz 제어 endpoint 기록이다. 이는 integration 직전 케이블 명령값이며 센서 측정 힘도, 전체 240 Hz 물리 스텝의 최대 힘도 아니다. 현재 계산 장력과 last-applied 명령은 서로 다른 시점의 값이므로 혼합하지 않았다.

### 이미지/overlay/물리량의 출처

- `media/raw/frames`: native Isaac Gym 카메라의 raw RGB 프레임. contact sheet가 사용한 원본이다.
- `media/frames`: 카메라 캡처에 strap route 표시와 상태 문구를 덧그린 시각화 프레임이며, depth map이 아니다. 선의 진함/희미함은 화면상 가시성 projection overlay를 나타낼 뿐 접촉/관통 검증이 아니다.
- `controls.json` 및 `trace.json`: 범위 밖 변위, orientation quaternion, last-applied cable command 같은 수치 측정의 근거다. overlay 픽셀에서 이 수치를 추정하지 않았다.
- 제어 장력은 commanded force scalar로 표기했다. 센서 힘으로 부르지 않는다.

initial state equivalence 기록은 초기 model+RMS 전체 key exact 동일, Adam empty, update/transitions 0을 표시한다. 별도 smoke run 뒤 병렬 진행 중인 12-update 학습 결과는 이 산출물의 측정치나 확정 결과로 포함하지 않았다.

### 입력 무결성

실행 전후 producer 및 아래 raw report/JSON/영상/사용 프레임 SHA-256은 [input_hashes.json](input_hashes.json)에 기록했다. 비교 영상은 저장된 원본 MP4를 재인코딩한 산출물이며 native physics 재실행은 하지 않았다.
