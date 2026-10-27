# 자유 기타 학습

**v8 장기 학습 진행 중:** 2026-10-22 22:52 KST에 large/1024환경/H32/seed7의 새 모델2000업데이트(65,536,000전이) 예산을 시작했다. 외장 저장소의 새 경로에100회 간격checkpoint와 원자료를 보존한다. 완료 결과와 연주 성능은 아직 평가 전이다. [진행 기록](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v8/README.md).

현재 GPU 왼손은 **544상태·8우선순위 토큰·보상v8·손가락별 전용 출력 분기**를 사용한다. 손가락 움직임 비용0을 유지하면서 원거리 접근 신호, 동일 목표 기반 potential, 보상/안전 비용 advantage의 개별 정규화, GAEλ0.98, 부드러운 관절 분담·대기 자세 prior를 적용했다. 전체 가동범위·독립 누적제어·PD·물리·접촉/성공·안전 기준은 유지한다. CPU 왼손·오른손의 기존 정책/PPO 경로는 보존한다. 이전v7 이하 저장본은 strict resume하지 않고 새v8로 시작한다. 실제 연주 성능과 자연스러움은 별도 학습·평가가 필요하다. [구현·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_targeted_finger_learning_v1/README.md).

실제 large/1024/H32의 새 모델8회와 동일계약 재개1회(총294,912전이)는 정상 종료·로그/입력SHA·모델/두Adam/RNG/3331복원을 검증했다. 관련CPU218개 중217개 통과, 기존512/544가정 실패1개는 분리했다. 이 짧은 검증은 전곡 성능이나 자연스러움 향상의 증거가 아니다.

**이전 보상v6 장기 결과:** large/1024환경/H32/seed7의 유효1300+재개700회·65,536,000전이를 완료하고 전체 선택 raw·3331·입력 SHA·모델/양 optimizer·새700 정상 close를 검산했다. 저장 공간·NTFS/FUSE EIO로 중단된 별도 분기80회는 합산하지 않으며, 원실행의 전체 EOF/정상 close나 연속 fresh2000회를 주장하지 않는다. 동일1024환경 고정 평가에서 초기3.8408203125/67음·safe1024, 평가한 학습모델 중 best500은5.4287109375음·safe414, 최종2000은0.7451171875음·safe961이다. 사전 선정 규칙의 평균 달성은 높아졌지만 안전성이 크게 낮아졌고 후반 성과가 퇴행했으므로 장기 연주 개선·수렴으로 분류하지 않는다. 모든 모델은 단계0·67음 전체 성공0이며, 실제 자세 캡처에서도 끝관절 편중·대기 자세 문제가 남았다. [장기 결과·평가·자세·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/README.md) · [학습 수집 해석](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/training_findings.md).

**이전v5 개선:** 당시 GPU 왼손 보상은v5였다. 이전 최종 영상에서 실제 중간 관절이 거의 펴지고 끝관절만 크게 굽혀지는 현상을 확인해, 실제 몸체 회전 기반의 부드러운 관절 분담 보상과 비사용 손가락의 넓은 대기 자세 보상을 추가했다. 손가락별 추종 보상은 해당 손가락의4축 요청만 보며 기존 축당 계수1/21을 유지한다. 전체 가동범위·독립 누적 제어·PD·물리·관측512·기존 성공/안전 기준은 유지한다. 보상v4 저장본은 strict resume할 수 없어 새v5 모델로 시작한다. 짧은 GPU 검증을 자연스러운 연주 학습의 완료로 해석하지 않는다. [손가락 관절 분담 개선·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_coordination_v1/README.md).

이전 보상v4의436소스로 GPU 왼손 `large/1024환경/H32/seed7` fresh2,000회·65,536,000전이를 약6시간18분 동안 끊김 없이 학습하고 정상 종료했다. 같은 고정1,024환경 첫 곡 평가에서 초기4.02734375→최종5.42578125/67음, 안전 완주1,024→1,019개다. 평가한500/1000/1500/2000회 중 최종 모델이 가장 좋았지만 단계0·중지/소지0음·67음 전체 성공0이며, 손가락별 성과 유지가 부족하다. 이 장기 실행은 진단 추가만의 성능 효과나 소지 추종 잔차 해결을 입증하지 않는다. [보상v4의436소스 장기 학습·분석·영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/README.md).

현재 환경·측정·학습·평가 코드는 이 패키지에서 관리한다. 새 손별 학습은 아래 기본 실행에서 시작한다. 연구 범위·실험별 성과는 [master_plan](/home/ajou/yigyu/3/master_plan/README.md)을 따른다. 상태 차원이나 파일 버전이 같아도 목표·보상·입력 SHA가 다른 checkpoint를 혼용하지 않는다.

이전 진단v2 변경에서는 손가락 실제 자세 진단을 추가했다. `episodes.jsonl`의 `left_finger_motion.base_rotation`은 검지·중지·약지·소지 기저의 palm 상대 회전과 zero-y 명령 참조 대비 회전오차를60Hz RMS/최대로 기록한다. 두 관절각의 추종 오차만으로 실제 전체 자세를 판단하지 않는다. 실제 N6 대조에서 굽힌 소지의 벌림 추종 잔차가 남았고 물리 반복4→16도 개선하지 못해 기본4를 유지했다. 이번 변경은 진단v2이며 상태512·보상v4·제어·PPO는 같다. 전체 계약 비교가 달라지므로 기존 checkpoint의 strict resume를 완화하지 않는다. 과거435소스 결과를 이전 보상v4의436소스 학습 성과로 상속하지 않는다. [추가 진단·검증](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_finger_tracking_fix_v1/README.md).

## 곡 단위 손별 학습 시작

`guitar_learning.train`은 합의한 초기 자세에서 새 손별 정책으로 곡 전체를 학습한다. 기본 곡은 검수된 `data/song_bundles/05_BN2-131-B_solo`의67음 전부다. GPU 왼손은 실제 손가락 표면 접근·압현·곡 연결을 단계적으로, 오른손은 타현을 학습하며 선택하지 않은 손의 정책 행동은0이다. 시작 전에 BC·전문가 모델이나 과거 성공 평가4회를 준비할 필요가 없다.

프로젝트 루트에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. 먼저 실행 환경을 설정한다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
```

학습할 손을 골라 아래 명령 중 하나를 실행한다. `--out`은 아직 존재하지 않는 새 출력 경로로 지정한다.

```bash
python -m guitar_learning.train --hand left --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/runs/left_song_press_v1
python -m guitar_learning.train --hand right --device cuda:0 --physics gpu --song 05_BN2-131-B_solo --out /home/ajou/yigyu/3/docs/2026-10-20/right_song_01
```

흐름은 **곡 입력 확인 → 하나의 GPU PhysX 장면에 환경별 aggregate로 배치 → 합의한035/v14 초기 자세 복원 → 준비3초와 곡을 연속 진행 → 32tick마다 GPU PPO 업데이트 → 모델 저장**이다. native 대기는0초이며 첫 tick부터 정책이 행동한다. 기본 곡은 원오디오29.3064초에 정책 준비3초·말미0.5초를 더하고60Hz 경계로 올린1969tick, 약32.8167초다. 원곡 시간축과67음 전체를 유지하며GPU왼손544상태/오른손500상태·39행동·실제240Hz 접촉/안전 측정을 사용한다.

기본 GPU 실행은 환경128개·수집32tick·PPO100업데이트·`--device cuda:0`·seed7·medium 모델이다. `--num-envs`는1~1024를 지원한다. 누적 제어 적용 전 위치제어 계약의 과거2000회 결과는 [실행·평가·영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md)을, 구현 초기 검증은 [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md)을 따른다. 이전 보상v2의 `large`/1024환경 장기 결과는아래 과거 기록이다. 곡 전체는1969tick이며32tick의 PPO 경계에서도 시계와 음별 원장이 이어진다. `--horizon`을 짧게 지정해도 PPO 업데이트 경계에서 장면·기타·곡 시계·음별 원장을 초기화하지 않고 다음 수집으로 이어간다. 곡 종료나 물리 실패 때만 초기 자세로 돌아간다. `--updates 1`은 PPO 업데이트 한 번을 뜻하며, 물리 실패가 있으면 곡 완주를 보장하지 않는다.

**이전435소스 압현 접근·유지 개선100회:** GPU 왼손의 실제 압현면 접근·감속·유지 보완을 구현했다. 실제 large1024/H32 fresh100회·3,276,800전이, 동결435Python·580입력·로그/저장·실제100→101재개 검증을 통과했다. 다만 고정0/100 평가에서 평균3.8046875→0.0/67음, 안전 완주1024→1021/1024로 연주 성능 향상을 입증하지 못했다. 해당435소스100회 평가 당시에는 지속 한방향 명령이 남아2000회 장기 실행을 진행하지 않았다. 이전 보상v4의436소스의 장기 결과는 위 기록을 따른다. 충돌하지 않는 현 중심선 대신 pin된 넥 mesh에서 추출한 압현면을 접근 관측·보상 목표로 사용하며, 현재 음 우선 선택과 실제 속도/지속 이동 명령을 함께 보는 유한 양성 보상을 추가했다. 관절 가동범위·누적 제어·PD·물리·기존 접촉/성공 판정은 유지한다. 새 보상v4/표면 관측v2 계약으로 fresh 시작하며 보상v3 모델의 strict resume를 거부한다. [이번 개선·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_press_control_v1/README.md).

**이전 보상v3 누적 제어 검증:** GPU 왼손21축 누적 제어 구현과 검증을 완료했다. CPU843개·GPU84명령시험·large1024/H32 fresh100회·실제100→101재개를 통과했고 실제 굽힘/펴짐을 확인했다. 다만 고정1024평가에서 평균 달성4.200→0.978/67음, 안전 완료1023→311곡으로 회귀해 조건부2000회 장기 학습은 실행하지 않았다. CPU·오른손·팔/손목·PD·보상·PPO는 유지했고 이전 위치제어 모델은 새 행동 계약에 strict resume할 수 없다. [구현·검증·영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

**누적 제어 적용 전 GPU 왼손 장기 결과:** 보상v3·표면 관측v1의 새 정책을 `large/1024환경/H32/seed7`로 시작해 저장본 복구를 포함한2,000회·65,536,000전이 경로를 완료했다. 마지막1,200회는 정상 종료했고 전체CPU831검사·원시64,000행·3331값 단계 재생·입력SHA 검증을 통과했다. 초기/최종 고정1024환경 평가는 평균3.861→8.301/67음, 안전 시간축 완료1024→1020곡,67음 전체 달성0→0곡이다. 최종 달성98.624%는 검지이고 중지0·약지111·새끼6개로 편중돼 곡 연주 학습 완료로 해석하지 않는다. 접촉 단계1에 머물렀다. 앞선 세 SIGFPE와 미저장63회는 별도 보존하며 끊김 없는 단일2000회 실행은 아니다. 로그 실수 변환은 기존 Dragon4 방식으로 우회했고 x87 근본 원인은 미확인이다. [결과·분석·전신영상](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/README.md). 물리·힘·성공·보상/PPO 계약은 이번 기록 오류 수정에서 바꾸지 않았다.

**이전 보상v2의 장기 실행 검증:** 환경별 aggregate를 적용한 GPU 물리 `guitar_learning.gpu_batch.v3`와 왼손 보상 `guitar_learning.gpu_tensor_song_reward.v2`에서 `large/1024환경/H32/seed7` 왼손 학습을 2000업데이트·65,536,000전이·5시간41분25초 동안 정상 완료했다. 전체 raw 64,000행의 CRC·에피소드 대응, 입력 568개 SHA·동결 Python 423개·최종 모델/optimizer의 유한 텐서 167개 검사를 통과했다. Torch 캐시 반환 후 GPU 여유는 최저 7.374GiB·최종 8.206GiB였으며 비Torch 메모리 추정 증가는 136MiB 이후 일정하게 유지됐다. 이전 보상v2·동결 소스의 해당 실행 조건에서의 검증이며, 현재 보상v8의 장기 결과로 상속하지 않는다. 모든 설정의 메모리 누수 해결이나 물리적 무실패를 뜻하지 않는다. [2000업데이트 실행·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md) · [실제2000→2001 재개 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_verification.json).

위 이전 보상v2 학습 중 종료 34,069회는 곡 시간축 완료 31,524회와 물리 실패 2,545회이며, 67음 전체 과제 성공은 0회다. 당시 curriculum은 1788업데이트에 진행도 1.0(압현 단계)에 진입했고 다음 단계 조건은접촉 후보 평균60%였다. 초기/최종 고정 정책의 각 1024환경 별도 평가도 종료·입력 검증을 통과했다. 안전 타임라인 완료는 1024→1023곡, 전체 첫 곡의 평균 달성 음은 3.969→4.232/67이며 전곡 과제 성공은 모두 0이다. 두 모델의 curriculum 관측이 다르고 특정 음의 향상·저하가 공존하므로 일반적인 연주 향상이나 수렴을 뜻하지 않는다. 첫 평가의 native 종료 실패와 보완 후 정상 재평가도 [별도 평가 분석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/README.md)에 구분해 기록했다.

**과거2026-10-20 GPU v1 진단:** 대규모 GPU 배치에서 행동0만으로도 기타 이탈·회전 실패가 재현됐다.128은 현재 설정의 기본값이며 안정적인 학습 권장값으로 검증된 수가 아니다. [실제 CPU/GPU 무행동 비교 영상과 원인 범위](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_failure_video_v1/README.md)를 먼저 확인한다. 이 결과는 현재 aggregate v3 적용 전 진단이며, 당시 1024환경의 장기 안정 학습을 권장하지 않은 근거다.

**과거2026-10-21 GPU v2 완화 수정:** GPU 기타를39개 몸체·38개 고정 관절에서 하나의 자유 강체로 바꿨다. 질량·COM·관성과89개 실제 충돌 형상을 유지하고, 기존39개 마커는 강체 자세에서 복원한다. 두 비물리 proxy의 충돌은 완전히 제외했다. 수치 폭발은 크게 줄었지만 긴 무행동 시험의 느린 이탈이 남으므로 안정화 완료나1024환경 권장으로 해석하지 않는다. [원인 분리·수정·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1/README.md)을 따른다. 이전GPU v1 checkpoint도 새GPU v2 물리 계약에 strict resume할 수 없다.

**aggregate 적용 전 장기 실행 점검:** 사용자가 자연스러운 이탈/종료는 허용했다. 다만 실제`large/H32` 학습에서1024환경은39업데이트까지 진행한 뒤PhysX 메모리 부족으로 중단됐고,512환경도후반 GPU 여유가약9.2→1.8GiB로 감소해94업데이트에서정상중단했다. 환경 수를줄이는것만으로긴학습준비가됐다고판정하지않는다. 당시에는장기학습권장환경수가미확정이었다. [전체점검·수정·원자료](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/README.md)를따른다. 기록RAM누적·PPO전체평가피크·Torch캐시경쟁을줄였고관련60개검사와실제저장모델94→95재개는통과했지만,당시네이티브메모리증가는미해결이었다. 이후 aggregate v3의 2000업데이트 결과는 위 이전 보상v2 검증과 구분한다.

추가저장간격은`--checkpoint-every N`(기본5,양의정수)로지정한다. 현재544상태/8슬롯 GPU`large` 최종 저장본은92,108,796bytes(약87.84MiB)이며, 매5회 저장으로1만업데이트를하면 모델 파일만 대략172GiB가 필요하다. 초기본은 optimizer moment가 없어 더 작고 실제 크기·임시 저장 여유를 따로 확인한다. GPU`song_report.json`은v2의counter/`episodes_path`를사용하며전체기록은`episodes.jsonl`에유지한다. counter는PPO에반영된수집기준이며오류/중단때raw기록의미반영분은journal의discarded와구분한다. 이전 보상v2의2000업데이트 검증은50회마다 저장했다. 실행 완료와 실제 음악 성공을 구분하며, 단계 진입은 위 기록의 범위로만 해석한다.

기본 실행은 GPU가 없으면 오류로 종료한다. `--device auto`를 명시하면 CUDA를 사용할 수 있으면 `cuda:0`, 그렇지 않으면 CPU를 선택하며 실제 장치를 `settings.json`에 저장한다. 필요하면 `--num-envs`, `--updates`, `--horizon`, `--device auto/cpu/cuda:0`, `--physics auto/cpu/gpu`, `--seed`, `--size`로 바꾼다. `--physics auto`는CUDA 정책이면GPU 물리, CPU 정책이면CPU 물리를 선택한다. 이전 CPU 물리 경로는 `--device cuda:0 --physics cpu` 또는 `--device cpu --physics cpu`로 명시하며 환경1/2/4/8/16·기본수집전곡 조건을 유지한다. `--device cuda:0`를 명시하면 CUDA를 사용할 수 없을 때 오류로 종료한다.

`--song`은 `data/song_bundles` 아래의 곡 식별자다. 시작 전에 전체 악보·타현 계획·오디오 길이를 확인하고 지원하지 않는 입력은 거부한다. 현재 검수된 압현음·일반 타현/명시적 재타현 곡을 지원하며 열린현이나 지원되지 않는 동작을 임의로 생략하지 않는다. 확인된 곡은 아래와 같다.

| 곡 식별자 | 목표 음 수 | 준비·말미 포함 길이 |
| --- | ---: | ---: |
| `02_Jazz1-200-B_solo` |42|17.9초|
| `03_Rock1-130-A_solo` |59|25.65초|
| `05_BN1-129-Eb_solo` |46|25.8333초|
| `05_BN2-131-B_solo` |67|32.8167초|
| `05_Rock2-142-D_solo` |84|30.55초|

실행 설정은 출력의 `settings.json`에 자동 저장한다. 자산·현재 소스 SHA와 물리 안전 조건은 내부에서 검사한다. 같은 계약의 checkpoint를 이어 학습하려면 기존 실행과 같은 손·설정으로 새 출력 경로를 지정하고 `--resume /절대경로/checkpoint.pt`를 추가한다. checkpoint의 관측·행동·목표·보상·물리·PPO 계약은 strict하게 비교하고, 현재 실행 입력의 SHA는 별도로 기록·검사한다. 이전563상태 단음 checkpoint와 이전500상태 왼손 전곡 checkpoint는 현재GPU544상태 왼손 계약의 `--resume`에 사용할 수 없다. 손가락 제어 프로필 적용 전512상태 왼손 checkpoint도 제어 계약이 달라 strict resume할 수 없다. 오른손의 상태 차원은500이지만 GPU 물리·제어·접촉 계약이 달라 기존 CPU checkpoint를 재개할 수 없다. 현재 GPU v3 물리 계약은 이전 GPU v1/v2 checkpoint와 호환되지 않는다. 현재 GPU 왼손 보상v8·544상태/8우선순위·표면 관측v2는 이전v1/v2/v3/v4/v5/v6/v7과 보상·정책·PPO 계약이 달라 strict resume을 거부한다. 이전 다른 보상 계약의2000회 모델에서 자동 Actor 이전은 하지 않고 fresh로 시작한다. 동일한 현재 v8 전체 계약의 저장본만 strict resume한다.

같은 실행 안에서 PPO 수집을 나눌 때는 곡 중간 상태를 유지한다. 새 프로세스의 `--resume`은 모델·optimizer·난수 상태를 복원하고, 물리 환경은 초기 자세에서 새 곡 에피소드를 시작한다.

선택한 손의 보상과 전곡 성공을 학습 기준으로 삼는다. 양손 협응 성공과 원래50/100ms 음악 판정은 별도 진단이다. `song_report.json`은 실제 종료 에피소드와 손별 성공·물리 실패를 저장한다. 진행 중인 곡의 원장은 메모리에 유지하며 이 파일에 부분 원장 snapshot을 저장하지 않는다. 부분 수집을 완주 성공으로 세지 않는다. 접촉·기하 타현의 성공을 실제 음향 성공으로 해석하지 않는다.

## GPU 물리·관측·보상

기본 실행은 환경마다 프로세스를 만들지 않는다. 하나의 GPU PhysX 시뮬레이터에서 모든 환경을 동시에 진행하고, 관절·몸체·접촉 힘·Jacobian·유한 하체/상체 제어·관측·보상·PPO를CUDA 텐서로 처리한다. 환경마다 68몸체·145shape 용량의 aggregate에 human→guitar→chair를 넣고 self-collision을 유지한다. 완료 에피소드 요약과 로그만 CPU로 옮긴다. 물리240Hz·정책60Hz이며 선택한 환경만 에피소드 경계에서 초기화한다.

사용자 선택에 따라 GPU 전용 접촉 판정을 새로 설계했다. 실제 손가락 충돌 STL의 표면 샘플이 유한한 현·프렛 영역에 들어오고 해당 몸체의 GPU 접촉 합력이 있을 때 새로운 압현 후보로 판단한다. 접촉 몸체 쌍·실제 witness를 제공하지 않는 GPU API 특성 때문에 기존 CPU의 pair-feature clean 판정과 구분한다. 이를 실제 현 압력·음향 성공으로 해석하지 않는다. 이번 수정에서도 이 접촉 판정은 유지하고, GPU 왼손의 관측·접근/접촉/유지 보상과 손가락별 단계를 별도 계약으로 바꿨다.

하체는 GPU 기하 질량행렬·유한 stable PD·반복 IK, 상체는 중력 보상·Chest/오른팔 지지 제어를 사용한다. native힘 상한과관절 제한을 유지하며 세부 solver 차이를 새 계약에 기록한다. 초기035/v14·자유 기타·중력ON·스트랩OFF·왼손 유연 프로필을 유지한다. 기존 CPU512/500 checkpoint도 새GPU 실행에 strict resume할 수 없으며 새 GPU 계약의 checkpoint끼리 재개한다.

구현은 `gpu/scene.py`·`gpu/control.py`·`gpu/environment.py`·`gpu/geometry.py`, 수집과 학습은 `training/gpu_pool.py`·`training/gpu_runner.py`다. CPU 재현 경로와 전문 실험기는 기존 구현을 유지한다.

`gpu/rigid_guitar.py`와`assets/gpu_rigid_guitar_v1/`은GPU 전용 강체 표현이다. native몸체는환경당68개, 관측의 논리몸체는106개다. 논리 기타 마커의 위치·회전·각 마커 COM 속도를 복원하며, 기타 전체 접촉 합력은 논리root에만 표시한다. 마커별 접촉력을 만들어 배분하지 않는다. native질량행렬도CUDA에서 제공됨을 확인했으며, 현재 기하 질량 경로는 별도 비교 후 유지한 명시적 구현 선택이다.

## 왼손 손가락 제어

GPU 기본 왼손은 손가락21축(엄지5축·검지~새끼각4축)에 `guitar_learning.gpu_left_incremental_fingers.v1`을 사용한다. 매60Hz 틱에 `목표_next = clamp(목표_previous + 행동×4/60, native하한, native상한)`으로 움직인다. 행동0은 현재 목표 유지이고 반대 명령은 다음틱부터 목표를 반전한다. 한계 밖 누적값을 남기지 않는다. 초기035/v14는 에피소드 경계에서 복원하고 H32 수집 경계에서는 목표를 이어간다. 실제 관절 반응은 접촉과 native PD를 따른다.

| 항목 | GPU 왼손 손가락21축 |
| --- | --- |
| 목표 변화율 | 행동×4rad/s, 최대4rad/s |
| 목표 평활화 | 손가락은 우회; 팔/손목 등은 기존0.2 |
| 목표 범위 | 기존 native 관절 하한~상한 전체 |
| 검지·중지·약지·새끼 native K/D | 12/1.5 |
| 엄지 native K/D | 8/1.25 |
| 기존 effort 상한 | 엄지4Nm, 다른 손가락20Nm |

CPU 왼손은 기존 `flexible_left_fingers.v1`의 초기 자세 기준 비례 위치·평활화0.45를 유지한다. GPU 오른손·팔/손목·전문 실행기도 기존 제어를 따른다. native PD 프로필은 준비 자세 복원 후 step0에서 한 번 적용하고 이후 reset에서 유지한다. 관절 한계·POSITION 모드·힘 상한과 물리 안전은 그대로다. 엄지는 넥에 고정하거나 비교 이미지의 후보 자세를 강제하지 않는다.

누적 제어 도입 당시에는 관측512·행동39 차원이 같아도 행동 의미가 달라 이전 위치 제어 checkpoint를 strict resume하지 않는다. 새 정책에서 시작하며 새 계약끼리만 재개한다. 이전 장기 결과는 누적 제어 성과로 상속하지 않는다. [누적 제어 구현·검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_incremental_fingers_v1/README.md).

구현은 [GPU 목표 제어](gpu/control.py), 기존 PD 프로필은 [손가락 설정](core/finger_control.py)과 [native 세션](runtime/finger_session.py)을 따른다. 종료 에피소드의 움직임 진단은60Hz 제어 끝점으로 집계하며 실제240Hz 극값이나 압현 성공과 구분한다.

## 왼손의 보상 단계

GPU 왼손은544상태와64×24 음 토큰·손가락별 우선순위8×24 토큰을 받는다. 표면 관측v2의 토큰9/10은 기존 현 기준 순간candidate/wrong이다. 토큰16~21은 지정finger2/3 실제 mesh 표면에서 **넥 압현면의 목표 선분**까지의 오차와 실제 상대속도다. pin된 충돌 neck mesh의 상향 평면을 추출하고(현재Gz9.3mm), 현의x/y를 유지해 투영한 뒤 프렛 셀 안쪽2mm~안쪽2mm·유한 현 범위로 제한한다. 현 중심Gz12.3mm·기존±3mm 접촉 판정과 구분한다. 속도는 실제 선택점의 움직이는 기타 프레임 상대속도 음수이며 샘플 교체 차분이 아니다. scale3cm/0.5m/s는 유지한다. 실제 cooked 접촉·하중은 별도 검증 대상이다.

접근 보상은 공통 손가락 목표 선택기의 유효 tracking slot0만 최대4개 합산하는 시간 의존 potential `Φ=Σ_selected w_f·exp(-표면거리/0.03)`에 `γΦ(next)−Φ(current)`를 적용한다. γ는 PPO reward γ와 같은 0.99이며 접근 계수는 단계와 무관하게 1이다. 실제 terminal의 다음 potential만 0으로 하고 H32 경계에서는 이어간다. 접근 potential과 양성 접촉·유지·음 달성에는 `w_f=M/(곡에 존재하는 손가락 수×그 손가락의 음 수)`를 적용한다. 기본67음의 검지/중지/약지/새끼 가중치는 약0.670/0.931/1.396/1.396이다.

기존 압현 성공 조건인 지정 손가락·현·프렛과 유효 clean 누적시간40%/최소50ms(음 길이를 넘지 않음)는 바꾸지 않는다. 준비 시작~음 끝의 기존 contact_done 기준을 최초로 채울 때0.5 보너스를 한 번 주고, 음 진행 중에는 `2×Δclean/음 길이` 유지 보상을 달성 이후에도 계속 준다. 기존 clean 달성 문턱을 넘을 때의 보너스는0.5다. 이 양성 항들은 손가락 가중치와 해당 단계 비중을 적용한다. 오압현·누락·놓친 음의 기존 공식과 legacy 단계 계수, 행동 변화·terminal·안전 비용은 별도로 유지한다.

GPU 왼손 단계는 **표면 접근 → 접촉 → 유지·전환**이다. 최근256개 종료곡이 쌓인 뒤 안전 완주90% 이상이고 곡에 존재하는 모든 손가락의 접근 달성 평균이각 20% 이상이면0→1을 진행한다. 접근 달성은 준비 시작2초 전~음 끝에 표면거리10mm 이내 누적100ms(구간 길이를 넘지 않음)다. 1→2는 접근 기준 대신 각 손가락의 기존 contact_done 달성 평균20%를 사용하며 안전90% 조건은 유지한다. 실패곡은 모든 지표0으로 포함하고 부분 궤적은 제외하며, 새 안전 완주가 포함된 committed PPO 수집 뒤 최대0.1만 올린다. 이256곡은 독립 seed256개를 뜻하지 않는다.

양성 비중은 단계0/1/2에서 손목0.2/0.1/0.05, 접촉0.5/1/1, 유지·달성0.5/1/2, 접근1/1/1이며 중간 진행도는 선형 보간한다. 모든 단계에서 접촉·유지 보상은 유효하고 손목 도달은 gate가 아니다. 손목 guide는035/v14 reset의 실제 x/z·상대 방향을 기준으로 anchor 프렛의 y 변화를 따르는 약한 자세 보조로 남긴다.

완료곡의 `episodes.jsonl`에는 `left_note_ledger`(음별 표면 최단거리·노출/접근시간·기하/하중·오프렛/오손가락 원인·clean/contact/달성), 손가락별 지표와 `reward_components`를 저장한다. 최소거리0은 노출시간0일 수 있으므로 함께 해석하고, 기하/하중/원인별 시간은 겹칠 수 있다. `update_*.json`에는 수집 전이 기준 `reward_component_means`와 단계 요약을 기록한다. GPU 단계 이력은 3331값 checkpoint buffer로 저장하며 CPU의8곡/27값 계약은 유지한다.

현재 `song_finger_tracking`은240Hz마다0~4/s의 양성 보상률을 적분한다. 손가락별 현재 음을 우선하고 없으면 준비창의 다음 음을 선택한다. 추종 품질은 지정 손가락 표면의 목표 거리와 candidate만으로 계산한다. 원하는 접근속도/감속/접촉 후 정지·실제속도 오차·지속 이동 요청에 따른 감쇠는 제거했다. 전역 `action_change`도 엄지를 포함한 LH21을 제외하며 팔·손목 등의 나머지 축은 원래39축 분모로 기존 축당 계수를 유지한다. 위치·접촉·자세가 같으면 손가락 명령이나 속도만 바뀌어도 이 보상은 변하지 않는다. 자세·clean유지·접촉/달성·성공·물리안전은 유지하며, 극단적인 전체 관절속도50rad/s 초과 안전종료도 유지한다. 이 새 보상v8은 이전v7 이하 모델과 strict resume하지 않는다. 추종 품질은 `(1+거리/.04)^-2×(1+candidate)`다.

초기 latent Gaussian std는 기존 `exp(-3)≈0.049787`을 유지한다. std0.08 확대는 후속 분리 비교 실험이며 이번 기본값 변경에 포함하지 않는다. 기본 학습률·안전 비용 설정은 유지한다. GPU왼손의 PPO는 reward/cost advantage 각각 표준화 후 cost_weight로 결합하고 최종 표준화하며 GAEλ는0.98이다. H32·rewardγ0.99/costγ1·critic 손실은 유지하며 기존 KL retry의 자동 actor LR 감소는 적용한다. 설정 고정과 학습 중 파라미터 불변을 혼동하지 않는다.

CPU 왼손의 기존 손목→접촉 단계와 오른손 보상은 이번 GPU 표면 계약을 자동 상속하지 않는다. [표면 압현 개선·검증 현황](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_fretting_v1/README.md)을 따른다.

현재 GPU 왼손은 기존 실행 중 안전 비용과 종료 실패 비용 +5를 유지하고, 물리 실패 때 남은 곡 시간에 비례한 비용을 한 번 추가한다: `5 × max(곡 길이 − 실패가 발생한 실제 control tick 뒤의 곡 시각, 0)`(초당5). 이는측정한 미래 비용이 아닌 고정률 absorbing-failure 모델이며 curriculum 비중으로 낮추지 않는다. CPU와 오른손 비용 계약은 변경하지 않았다.

## 전문 실험과 이전 실행 재현

2026-10-20 기준. 실험 수치·완료 여부는 [master_plan의 검증 결과](/home/ajou/yigyu/3/master_plan/09_curriculum_and_evaluation.md)와 연결된 원자료를 따른다. 루트 CURRENT_STATUS의 첫 전곡 V1 요약을 최신 실행 경로 전체의 결과로 해석하지 않는다.

| 목적 | 진입점 | 계약·범위 |
|---|---|---|
| 접촉 회복 평가·교사 수집 | `guitar_learning.tool.experiments.contact_recovery.run evaluate/collect` | 상태500·왼손33/전체39. native 원자료·240Hz 회복 기록. 새 PPO를 시작하지 않음 |
| 회복 자료 감사·내보내기 | `guitar_learning.tool.experiments.contact_recovery.dataset_v2` | 실제 회복·원 음악·안전·교사 보정이 감사된 행만 채택 |
| 왼손 정밀화 평가·PPO | `guitar_learning.tool.experiments.transition_refinement_runtime_v2.run eval/train` | 상태500·오른손0. 새 보상·탐색·시연 자료·초기 평가4회와 runtime 감사 |
| 전곡 보상 V2 | `guitar_learning.tool.experiments.song_reward_v2.train/evaluate` | 전곡67음·500상태·33+6행동·정책 준비3초·1969tick |
| 단음 양손 기준 경로 | `guitar_learning.tool.experiments.joint.train/evaluate` | 상태1132·Actor 각569·33+6행동 |
| 초기 전문가 생성·검증 | `guitar_learning.tool.experiments.local_skills` | 이전563상태 품질 경로. 이후 초기화 검증이 일부 함수를 재사용 |
| 입력 생성·검수·진단 | `guitar_learning.tool` | [도구별 명령](tool/README.md) 참조 |

실제 명령·설정·전제는 [회복](/home/ajou/yigyu/3/guitar_learning/tool/experiments/contact_recovery/README.md), [정밀화 runtime V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/transition_refinement_runtime_v2/README.md), [전곡 V2](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_reward_v2/README.md), [양손 단음](/home/ajou/yigyu/3/guitar_learning/tool/experiments/joint/README.md) 문서를 따른다. 기존 결과는 해당 원입력 또는 명시적 이전 절차에서 재현한다. 파일 정리만으로 기존 checkpoint의 계약 불일치를 허용하지 않는다.

## 코드 구조와 공용 기반

루트의 실행 진입점은 `train.py` 하나다. 일반 학습은 아래 공용 코드로 이어지고, 전문 실험·평가·시연·입력 생성은 `tool/`에서 찾는다.

```text
guitar_learning/
├── train.py                 # 곡 단위 손별 학습 시작
├── music_task.py            # 공통 악보·목표 계약
├── historical_inputs.py     # 이전 입력의 정확한 원문 검증
├── training/                # 설정·runner·정책·PPO·수집·기록
├── gpu/                     # 기본 GPU 물리·배치 제어·관측·접촉 후보·보상
├── core/ · runtime/         # 기존 CPU 환경·접촉·안전·native 세션·reset
├── skills/ · imitation/     # 손별 정책과 재사용하는 행동·모방 기반
├── timing/ · quality/       # 시간창·준비·음악 품질 환경과 기록
├── score/ · song/           # 악보·전곡 환경·손별 보상·worker·요약
├── native/ · assets/        # 물리 구현과 모델·자세·설정
├── tool/                    # 부가 실행·전문 실험·검증 도구
├── tests/ · docs/           # 회귀 검사·세부 계약
└── archive/                 # 실행하지 않는 이전 원문
```

`training/start.py → training/gpu_runner.py → training/gpu_pool.py → gpu/`가 기본 GPU 실행을 연결한다. `song/task.py`가 전체 곡을 확인한다. 명시적인 CPU 재현은 `training/runner.py`와 `song/runtime.py`의 worker·요약 및 `song/hand_environment.py`의 손별 보상·성공을 사용한다. 전곡 환경·측정·판정은 `song/`의 공용 라이브러리로 모았으며 기본 실행은 `tool/`의 전문 실행기를 import하지 않는다.

이전 `train_parallel.py`는 `training/runner.py`로 옮겼고, 사용되지 않는 루트 `environment.py` facade는 보관했다. 전문 실행기17개는 `tool/training/`, `tool/evaluation/`, `tool/demonstration/`으로, 검증 전용 환경·rollout은 `tool/validation/`으로 모았다. 전문 패키지8개는 `tool/experiments/`에서 관리한다. [도구 안내](tool/README.md)를 따른다.

공용 환경의 구버전 접미사는 삭제 근거가 아니다. 현재 환경의 상속·호출과 checkpoint 계약에 필요한 구현은 남겼다. `song/task.py`와 `music_task.py`는 이전 checkpoint가 검증하는 경로·원문을 보존한다. 곡 단위 학습이 기본 경로가 되어 환경·측정·보상6개 모듈을 `song/`의 공용 라이브러리로 승격했고, 과거 BC 이전·평가·전문 실행기는 `tool/`에 유지한다. 검사도 이동 전후의 동작·물리·checkpoint 계약을 확인하므로 유지한다. [파일 배치와 유지 이유](docs/CODE_STRUCTURE.md)에 상세히 기록했다.

## 물리와 입력 계약

Root 고정·하체 유한 제어·105입력/97비영 범위/8원 영범위를 유지한다. 정책 행동은 왼손33+오른손6이며 왼손 과제에서는 오른손 정책 행동이0이다. 기타는 자유 강체·중력ON·스트랩OFF이고 직접 보조 힘·부착·실행 중 상태 덮어쓰기를 사용하지 않는다. 가슴 접촉 지속은 성공의 필수조건이 아니다. 물리240Hz·정책60Hz와 실제 표본 기반 음악/안전 판정을 유지한다. 기본 왼손의 손가락21축만 위의 명시적 제어 프로필을 사용하며, 나머지 제어 gain·관절 한계·힘 상한·안전 종료 기준을 유지한다. GPU 제어 solver와 접촉 후보의 차이는 위 새 GPU 계약을 따른다.

초기 자세는 기존035/v14를 기준으로 하며 현재 자산은 내부 `assets/`에서 읽는다. 준비·정착·정책 pre-roll은 경로별 설정을 따른다. 과거 정착2초 규칙을 native0초인 전곡·전환 경로에 자동 적용하지 않는다. 자세 연구의 새 후보도 학습에 자동 적용되지 않는다.

`assets/native_provenance.json`은 원본과 현재 SHA를 구분한다. `historical_inputs.py`와 실행하지 않는 `assets/historical_inputs/` 원문은 기존 gate·checkpoint의 정확한 입력을 검증한다. 내부화·정리 전 원문 검증을 현재 실행 소스의 검증과 섞지 않는다. 외부 Isaac Gym, `data/song_bundles`, 기존 `docs`·`paper`의 checkpoint와 증거는 계속 필요하다.

Actor 초기값 이전과 strict resume를 구분한다. 새 목표·보상·탐색·자료 계약에는 명시적 이전·검증이 필요하다. 이미 성공한 초기 모델이나 교사 자료를 새 정책의 성공으로 상속하지 않는다. 정밀화 단음의90% 유지와 전곡의 원 유지 기준·strict50/100ms는 별도 계약이다.

## 실행과 검사

프로젝트 루트 `/home/ajou/yigyu/3`에서 Isaac Gym Preview4가 설치된 `rl38` 환경을 사용한다. native 진입점은 Isaac을 NumPy·Torch보다 먼저 import한다. 실제 설정과 새 출력 디렉토리를 지정하고 기존 실행 결과를 덮어쓰지 않는다.

```bash
PYTHONDONTWRITEBYTECODE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B -m unittest discover -s guitar_learning/tests -t . -v
```

`settings.json`·`training_contract.json`·`inputs_before.json`은 실행 계약, `transitions.jsonl.gz`는 전이, `episodes.jsonl`은 실제 에피소드 종료다. `learning_metrics.jsonl`, 최종 `report.json`, native/runtime 감사와 checkpoint를 함께 확인한다. sampled/logged/durable/committed/discarded와 완주·음악·안전·런타임 실패를 구분한다. 상세는 [LOGGING](docs/LOGGING.md)을 따른다.

저장 모델의 strict load는 같은 관측·행동·목표·보상·물리·PPO 계약에서만 허용한다. 접촉 후보·기하 타현·음악 성공·안전 완주·정상 실행 완료를 각각 보고한다.

## 이전 단계 문서

[TRAINING](docs/TRAINING.md), [SPECIALIST_TRAINING](docs/SPECIALIST_TRAINING.md), [SKILL_CURRICULUM](docs/SKILL_CURRICULUM.md), [IMITATION_TRAINING](docs/IMITATION_TRAINING.md), [TIMING_TRAINING](docs/TIMING_TRAINING.md), [ACTIONABLE_PREPARATION](docs/ACTIONABLE_PREPARATION.md), [MUSICAL_QUALITY](docs/MUSICAL_QUALITY.md)는 단계별 계약·구현 근거다. 그 안의 과거 실행 설정이나 성공을 최신 과제에 자동 상속하지 않는다. [CODE_LINEAGE](docs/CODE_LINEAGE.md)는 원구현의 역사적 대응을 설명한다.

구형 프로젝트 여섯 디렉토리는 [legacy 보관소](/home/ajou/yigyu/3/archive/legacy_guitar_20261019/README.md)에 있다. 구조 정리 전 소스는 [20261019_before_structure_cleanup](archive/20261019_before_structure_cleanup/manifest.json)에 보존했다.

2026-10-19 구조 정리의 도구 이전·보관 범위·동등성 검증은 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-19/guitar_learning_structure_cleanup_v1/README.md)에 기록했다.

2026-10-20 역할별 파일 이동표·경로 검증은 [재배치 기록](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_role_layout_v1/README.md)에 기록했다.

새 기본 손별 실행의 단기 학습·저장·재개 확인은 [실행 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_simple_start_v1/README.md)에 기록한다.

2026-10-20 메인·도구 재정리의 전체 파일 검토·이동표·검증 범위는 [정리 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_main_tools_v1/README.md)에 기록한다.

현재 곡 단위 기본 실행의 변경·검증 범위는 [전곡 시작 결과](/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_song_start_v1/README.md)를 따른다.
