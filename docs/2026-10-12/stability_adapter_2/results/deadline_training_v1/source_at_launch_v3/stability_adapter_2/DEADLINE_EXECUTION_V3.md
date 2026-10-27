# 마감 실행 v3 — GPU 재확인 후

기본 계획은 DEADLINE_TRAINING_PILOT_V1.md다. 소비된 v1/v2와 실패·성공 로그는 보존한다. v1의 Python3.8 dict union 오류는 새 v2에서 교정했고, v2는 실제PPO1회/256transition과 학습전·후 전체영상 검증을 완료했다.

실행은 run_deadline_training_v3.py, 물리는 deadline_native_v1.py, GPU학습은 deadline_ppo_v1.py, 회전집합은 deadline_rotation_v3.py다. 등록된 두baseline을 실제호출하며 820D관측/81D행동/동적anchor/단일PD 제출을 사용한다. 시험보상 PROFILE은 native 파일에 명시한다. 정식v4/v5 인증이나 연주 성공을 주장하지 않는다.

## 검증된 사실

- RTX4070Ti12GB/580.178.04 드라이버 정상. 격리 실행에서는 장치 접근불가, GPU접근 실행에서 CUDA 행렬연산과 독립GPUPhysX step 실제통과. 사용자 재설치/재부팅은 필요없다.
- CPU/CUDA PPO검사에서 Actor·Critic 실제갱신/RNG정확복원/덮어쓰기거절/ABI변경거절 통과. native 순수7검사,회전8묶음,스케줄gate3검사 통과.
- v2 두평가 각각982control/3928physics/16.3667초,양baseline862회씩,42event정산/성공0/accepted0,금지호출0,입력SHA불변. 보상합−397.140450→−397.744697은 개선 증거가 아니다.

## 장기 운영

한국시간11:40 이후 새control/reset/optimizer 진입을 차단한다. 미완료rollout은 학습에 사용하지 않는다. 저장된마지막완료 모델로 최종평가 시간을 확보한다. checkpoint는 최초/1회갱신 확인/이후벽시계30분마다 불변파일로 생성하며, 평가영상은2초준비부터곡전체16.3667초까지다. 평가 동안 학습은 대기하며 이전완료checkpoint와영상은 보존한다.

평가에는600초 및11:59남은시간을 고려한timeout,TERM15초/KILL5초 대기를 적용한다. native호출/CUDAupdate 내부를 강제로 순간 중단하는 계약은 아니며 OS응답을 포함한 절대완료시간을 보장하지 않는다. timeout은 실패로 기록하고 실행을 중단한다. 이미캡처된PNG 보존은 가능하지만 중단시원시episodeJSON/완성MP4/부분encode는 미완성일 수 있다. 정상예측시간은 실제v2검증에서곡전체평가 약수분으로 측정했다.

새 장기 실행은 v3소스ABI로 새 정책을 초기화한다. v2한회학습checkpoint를 ABI무시해서복사하지 않는다. main4는 실행전에추가기록하고 native가읽는동안수정하지 않는다. 실시간기록은 docs아래live_progress.jsonl과장기run/training.jsonl이다.

## 결과 경로

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/deadline_training_v1/`

GPU진단: GPU_DIAGNOSIS.md. 검증영상·이미지·비교: artifacts_smoke_v2/README.md. 독립검수: review_v1.md. 장기실행예정: long_run_v3/. 실제실행여부는 live_progress.jsonl 및로그로 확인한다.
