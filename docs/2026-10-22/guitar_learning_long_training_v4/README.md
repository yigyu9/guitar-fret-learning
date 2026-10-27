# 현행436 왼손 장기 학습·고정 평가·영상

**fresh large1024 학습을2000회 정상 완료했고, 평가한 학습모델4개 중 최종2000회 모델이 가장 좋았다.** 동일한1024환경 첫 곡 평가에서 초기 평균4.0273/67음이 최종5.4258/67음으로 늘었다. 그러나 네 손가락의 연주를 완성한 결과는 아니다. 중지·소지 성과와 손가락별 해법의 동시 유지가 부족하며, 전체67음 성공은 모든 평가에서0이다.

## 실행 결과와 선택 범위

- 본학습은 left / `05_BN2-131-B_solo` / large / N1024 / H32 / seed7 / fresh2000 / checkpoint100이다. 합의한035/v14 초기자세·자유기타·240Hz·보상v4·누적 왼손 제어·진단v2를 동결했다. 일반 기본값128/medium을 바꾼 것이 아니라 이번 명령에1024/large를 명시했다.
- 실제2000회·65,536,000전이·raw64,000행·2,000gzip member·약6시간18분13초를 완료했다. 전체CRC/EOF, source436/581입력pin, 모델·양optimizer 유한성,3331 curriculum 재생, GPU1sim/1024환경과 정상close를 검산했다. discarded/pending/unresolved·cleanup/input변경은0이다.
- 매100회 중간19개와initial/final까지21개checkpoint를 보존했다. 학습 수집의 마지막100회 안전률97.520%/안전곡 평균3.6476음은 **변하는 확률적 정책의 수집 통계**다. 아래 고정 정책 평가 평균과 같은 값이 아니다.

|고정 checkpoint|전체1024환경 평균/67음|안전완주/1024|
|---|---:|---:|
|초기0|4.02734375|1,024|
|500|0.9521484375|926|
|1000|0.3837890625|99|
|1500|3.6552734375|967|
|최종2000|5.42578125|1,019|

선정 규칙은 **평가한 학습checkpoint끼리 전체1024 첫 곡 평균 달성→안전완주 수→최신update**다. 초기0은 별도 기준이며 선택 후보가 아니다. 이에 따라 best=latest2000이고 초기보다 평균1.3984375음 증가했다. 보관한 모든20개 학습모델을 평가한 것은 아니므로 전체checkpoint의 전역 최적이나 수렴을 주장하지 않는다. 중간500/1000/1500이 초기보다 낮았던 회귀도 남긴다.

최종 평가의 안전곡 달성은 검지5,185/중지0/약지369/소지0으로 편중됐다.1500평가에서는 검지0/중지3,606/약지94/소지0이었다. 공통 안전963환경에서도 중지3,588→0/검지0→4,943으로 해법이 바뀌었다. 이는 정책 간섭·망각의 통제된 인과실험은 아니지만, 네 손가락 성과가 함께 유지됐다는 설명과는 맞지 않는다.

[학습 수집 상세](final_training_report.md)에는20개100회/마지막250회·손가락 원장·PPO/std·행동 한계·기저 회전·자원을, [고정 평가 상세](fixed_evaluation_report.md)에는 동일1024첫곡·공통 안전cohort·음별/손가락별 성과·모델 선정을 분리해 정리한다. [전체 평가 원자료](checkpoint_evaluation.json)와 각 평가 폴더의1024개 첫 종료 원장은 유지한다.

## 선택 모델 영상

선정된 final.pt의 실제GPU 고정 평가에서 저장한 body pose를60Hz로 재생했다. 사전 캡처환경0..7 중 안전완주 최저ID 규칙으로 env0을 선택했다. env0은 안전완주9/67음으로, 전체 평균5.4258음을 대표하거나 최고성과 환경인 것은 아니다. 정책 추론·새 동역학·보간을 추가하지 않았다.

두 영상 모두1280×720/H.264/yuv420p/60fps/1,969프레임/32.8167초로 정상 완료했다. 원pose/SHA·추가 물리0·모든 프레임pose·투영 경계를 확인했다. root가 독립ffprobe와985/1969프레임 시각QA를 마쳤다. [영상QA](qa/video_checks.json)의 pose위치 최대오차는0m, 회전 최대오차는6.70e−16rad다. 전신/손·자막이 화면에 들어오는지 확인했다.

![선정 최종모델 전신 영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/best_video/best_fullbody_60fps.mp4)

[전신 영상](best_video/best_fullbody_60fps.mp4) · [영상보고서](best_video/report.json) · [pose 감사](best_video/pose_audit.json).

![선정 최종모델 왼손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4/best_hand_video/best_left_hand_60fps.mp4)

[왼손 확대 영상](best_hand_video/best_left_hand_60fps.mp4) · [영상보고서](best_hand_video/report.json) · [pose 감사](best_hand_video/pose_audit.json).

전신SHA: `09f3cde713a66315b36cd0001ad91ce3344f850086386159a6a0a26e48ebf80f`; 왼손SHA: `ca823ef5d4769a58a52254a7488f1d04996420754a5b631b3344ff4d35c43ddc`.

## 해석의 한계

- stage0/surface_approach는 손가락 동작 금지가 아니다. 왼손21축 누적 명령·실제 표면 관측과 contact/timing 양성 가중치0.5는 계속 동작했다. 모든 손가락near20%gate를 통과하지 못해 progress0으로 남았다. 최종 최근256안전률98.4375%에도 near는 검지42.0781/중지0/약지18.5547/소지0%다.
- 각 고정 평가는 동일곡·초기자세·1024환경·deterministic정책의 첫 곡이며 PPO/curriculum 갱신이 없다. 각checkpoint 자신의 저장curriculum/관측을 사용했다. 여기서는 모두 progress0/같은stageweight였지만 동일관측으로 가중치만 바꾼 인과실험이나 독립seed/곡 일반화는 아니다.
- 판정은 기존 현 기하·지정 손가락 몸체net load와 **유효 clean 시간의 누적 조건**이다. 후보의240Hz 두 끝점 확인과 전체 성공문턱까지의 시간 누적을 구분하며, 요구시간이 연속 한 덩어리여야 한다는 뜻은 아니다. 최근접 표면 몸체 하중과any qualifying sample은 동일점·시점이 아닐 수 있고, contact pair/witness·교정압력·진동·음향의 인증도 아니다. 큰 기저y/zero-y참조오차도 SDK내부drive오차나0음의 단독 원인으로 단정하지 않는다.
- 이번436계약으로 **fresh2000과 고정 평가strict load/3331복원은 검증했지만, final2000→2001의 실제PPO resume는 아직 실행하지 않았다.** 구현상resume는 모델/양optimizer/RNG/curriculum을 복원하고 물리 장면·곡시계·진행episode는 새035/v14로 시작한다. 과거435진단v1 checkpoint는 같은512/39차원이어도 현행진단v2 계약의strict resume를 허용하지 않는다.

## 결과 위치·무결성 범위

|자료|위치/범위|
|---|---|
|고정소스|[training_source_manifest.json](training_source_manifest.json), [source_training](source_training) — 활성Python436개/SHA동결|
|본학습|[train2000](train2000) — settings/contract/입력581핀·raw/원장/업데이트·21모델·완료보고서|
|native실행기록|phase의 [train2000_gdb.log](train2000_gdb.log) — 학습 GDB/stdout·정상종료|
|완료분석|[analysis_final/analysis.json](analysis_final/analysis.json) — 전체CRC/EOF·3331·finite·close검산과5종PNG/SVG|
|고정평가|[checkpoint_evaluation.json](checkpoint_evaluation.json), `evaluation_initial_1024`, `evaluation_update_0500_1024`, `evaluation_update_1000_1024`, `evaluation_update_1500_1024`, `evaluation_final_1024`|
|영상|[best_video](best_video), [best_hand_video](best_hand_video), [독립영상QA](qa/video_checks.json)|
|실행전기준|[before_manifest.json](before_manifest.json), [preflight](preflight.md), [계획](../../plans/guitar_learning_long_training_v4_20261022.md)|

입력pin 수는 실행별로 다르다. 본학습581, 초기평가589, 학습모델500/1000/1500/2000평가 각590, 전신·왼손 렌더 각597이다. 초기checkpoint의 같은 경로 중복이 합쳐지고 설정/모델/도구/폰트/선정자료가 추가되는 범위 차이다. source436과 같은 분모가 아니며, 누락pin을 허용해 개수를 맞추지 않았다.

최종GPU cache반환 후 free최소7.5205GiB/final8.1357GiB, 일반 실행샘플 최소6.7236GiB로 완료했다. free+reserved잔차 증가 추정0.03320GiB는 후반plateau였으나 native할당 소유권/SDK누수의 일반 증명은 아니다. 본학습 폴더 실측은 약5.732GiB, finaldisk 관측free는6.4247GiB다. 평가·분석·영상·source snapshot은 별도다.

root의 [실행 후 무결성 검산](integrity_after.json)은 활성436Python 집합·모든SHA와source_training 원문사본 일치, 기존3봉인 전체1,075파일(881+109+85)의bytes/SHA·여분파일 없음을 확인했다. 아래manifest SHA도 [실행전기준](before_manifest.json)과 일치한다. 현행4문서는 root가 변경 전 원문을archive/20261022_before_long_training_results_v4에 보관하고 before/after SHA를 따로 기록했다. [result_manifest.json](result_manifest.json)은 자기 자신을 제외한 이번phase 파일을 봉인하며 최종root 검산으로 확인한다.

|기존봉인|파일수|result_manifest SHA256|
|---|---:|---|
|[press control v1](../../2026-10-21/guitar_learning_press_control_v1/README.md)|881|`855ad6dd2f5e56eea43705e9c3f3b54abc1251bf12787ab9e1dab394cd83747a`|
|[ring/pinky probe v1](../guitar_learning_ring_pinky_probe_v1/README.md)|109|`638df08ba0500ad429ba66ce4e3f36c6dcaa0ea7a7386b4fc9ace8a487b6a6ec`|
|[finger tracking fix v1](../guitar_learning_finger_tracking_fix_v1/README.md)|85|`c00d20534b2dfba088fdcd4b38a43f9eeeb3403824666f0a9319cd832b820ab4`|

## 동일 기준 재현 명령

아래는 실제 실행 조건을 재현하는 예다. **이미 완료된 출력 폴더를 덮어쓰지 않고** 새 이름을 사용한다. 동결 source436·자산SHA와 rl38/IsaacGym 환경이 같아야 하며, GPU 작업은 동시에 실행하지 않는다. 명령을 제시하는 것과 새 재현을 실행·검증한 것은 다르다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1 PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
RUN_PHASE=/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v4
/home/ajou/miniconda3/envs/rl38/bin/python -B -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 --seed 7 \
  --updates 2000 --checkpoint-every 100 --out "$RUN_PHASE/train2000_reproduce"
```

원본 완료 학습 자료의 CPU 검산·분석을 새 디렉토리에 재생성하려면:

```bash
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/analyze_training.py" --run "$RUN_PHASE/train2000" \
  --updates 2000 --plots --out "$RUN_PHASE/analysis_recheck"
```

원본5모델을 다시 고정 평가하려면 새 tag를 사용한다. 각 환경은 첫 종료 곡만 성과로 집계하고, 완료 행은 batch 유지를 위한 filler로만 재설정한다. 전체1024환경을 분모로 사용한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -B "$RUN_PHASE/evaluate_checkpoints.py" \
  --run "$RUN_PHASE/train2000" --expected-updates 2000 --num-envs 1024 \
  --checkpoints 2000 0 500 1000 1500 --tag recheck
```

기존 완료 평가에서 선정한 모델의 pose를 새 영상으로 재생하는 명령이다(추가 물리0):

```bash
MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/render_video.py" --evaluations "$RUN_PHASE/checkpoint_evaluation.json" \
  --selection best --view fullbody --out "$RUN_PHASE/best_video_recheck"
MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/render_video.py" --evaluations "$RUN_PHASE/checkpoint_evaluation.json" \
  --selection best --view hand --out "$RUN_PHASE/best_hand_video_recheck"
```

본학습은 fresh이므로 resume 명령을 사용하지 않았다. 추가 학습의 `--updates`는 추가 횟수이며 새 출력 폴더가 필요하다. 실제 resume 성공은 별도 복원·1회PPO·close 검산을 한 뒤에만 보고해야 한다.
