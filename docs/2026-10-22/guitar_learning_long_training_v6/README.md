# 보상 v6 장기 학습·고정 평가·자세 분석

**유효1300+700회·65,536,000전이의 학습 경로를 완료했지만, 연주 성능과 자연스러움이 개선됐다고 판정할 수 없다.** 평가한 학습모델 중500회의 전체 평균은5.4287/67음으로 초기3.8408보다 높았으나, 안전 완주는1024→414로 줄었다. 최종2000회는0.7451/67음으로 퇴행했다. 모든 모델은 단계0·67음 전체 성공0이며 손가락별 성과 유지와 실제 자세 문제가 남았다.

[학습 수집 상세](training_findings.md) · [완료 분석/곡선](analysis_final/analysis.json) · [전체 고정 평가](recovery_checkpoint_evaluation.json) · [저장 자세 분석](posture_analysis/report.md) · [검산 증거](recovery_verification.json).

## 실제 완료한 학습 경로

- 동결한436 Python, GPU 왼손 보상v6·544상태/8우선 슬롯·large/N1024/H32/seed7/checkpoint100이다.035/v14·자유 기타·240Hz·LH21 누적 제어·PD/힘·성공/안전·PPO 설정을 실행 중 바꾸지 않았다. 일반 기본값128/medium은 그대로다.
- 처음부터 시작한 원실행의 **저장1300회/42,598,400전이**와 동일 계약의 **재개700회/22,937,600전이**만 최종 정책 경로에 포함했다. raw는41,600+22,400=64,000행이다.1300 checkpoint→새 initial1300은 metadata 외 모델·양 optimizer·RNG·3331 커리큘럼 전체가 정확히 복원됐다.
- 물리 장면·부분 곡은 재개 때 새035/v14 episode로 시작했다. **연속 fresh2000 단일 프로세스가 아니다.** 원실행은1300 prefix의 CRC 완료행만 인증하고, 전체 gzip EOF/정상 native close는 인증하지 않는다. 마지막700은 전체 CRC/EOF·실제 GPU close·GDB 정상 exit를 통과했으며 wall8175.3926초(약2시간16분15초)다.
- 별도13회·원실행 후속62개 update파일·첫 재개5회의 합80은 최종 집계에 넣지 않았다. 업데이트당32,768 기준 명목 예산은2,621,440전이지만, 특히62개 후속파일의 raw 완전성/commit까지 최종 prefix proof가 인증하는 것은 아니다. 별도의 부분 수집도 구분하며 journal의 공식 discarded로 일괄 재분류하거나 원자료를 삭제하지 않았다.
- 원인은 학습 수치 오류로 통합하지 않는다. Git 임시 pack의 저장 공간 증가와 NTFS/FUSE 외부 볼륨의 EIO로 중단·복구했다. 외부 파일의 SHA 동일 복사와 경로 이전 증거를 보존했으며, 파일시스템/하드웨어의 근본 원인 해결을 주장하지 않는다. [운영 이력](OPERATION_STATE.md), [위치 이전](recovery_storage_relocation.json), [복구 manifest](recovery_copy_relocated_manifest.json)을 따른다.

학습 중 종료34,841곡은 안전27,325/물리종료7,516이고 전체 평균2.8163음·안전곡 평균3.0894음이다. 안전곡 평균은1400–1499에서6.9814음, 마지막100회에서1.8553음으로 변했다. 이것은 **변화하는 확률적 정책의 수집 통계**로 아래의 고정 평가 수치와 섞지 않는다.20개100회/8개250회 구간, 손가락 원장·보상/PPO·행동 한계·기저 회전과 자원은 [학습 관찰](training_findings.md)에 정리했다.

## 별도 고정 정책 평가와 모델 선정

동일한 첫 곡·035/v14·1024환경을 각 모델의 deterministic 정책으로 평가했다. 첫 종료만 집계하며 이후 batch 유지를 위한 filler episode를 성과에 넣지 않는다. PPO·커리큘럼은 갱신하지 않고 각 checkpoint의 저장3331 상태를 복원·동결했다. 모든 모델의 progress는0이지만, 저장 이력까지 동일하게 만든 가중치 격리 실험은 아니다.

| checkpoint | 전체1024 평균/67음 | 안전/1024 | 안전곡 평균음 | 전체 첫 곡 검지/중지/약지/소지 성공 |
|---|---:|---:|---:|---|
|초기0|3.8408203125|1024|3.84082031|3933 / 0 / 0 / 0|
|500 — 선정 모델|5.4287109375|414|5.99758454|3387 / 2144 / 28 / 0|
|1000|2.8525390625|719|2.97218359|2921 / 0 / 0 / 0|
|1500|1.6845703125|459|1.66884532|1725 / 0 / 0 / 0|
|최종2000|0.7451171875|961|0.78251821|763 / 0 / 0 / 0|

선정은 **평가한 학습모델끼리 전체1024 평균 달성→안전 완주 수→최신 순**이라는 사전 규칙이다. 초기0은 별도 기준이며 후보가 아니다. 따라서 best500/latest2000은 다르다.500의 초기 대비 평균 증가는1.587890625음이지만610환경이 물리종료했고, 이 규칙은 안전성을 우선하는 규칙이 아니다. 모든 저장본을 평가한 전역 최적·학습 수렴·일반 연주 개선을 주장하지 않는다.

500의 중지2144건은 전체 첫 종료곡에서의 값이고 안전414곡 안에서는1112건이다. 해당 모델의 안전곡 검지/중지/약지/소지 성공은1360/1112/11/0이다. 이후 모델들의 중지·약지·소지 성공은 모두0이다. 최종 모델은347환경이0음이고 최대5음이다. 이는 기능의 동시 유지가 부족하다는 관측이며, 망각이나 보상 한 항의 원인을 확정하는 인과 대조는 아니다. 한 곡·한 seed·한 준비자세의 반복 환경을 독립적인 일반화 시험으로 읽지 않는다.

## 실제 저장 자세에서 남은 문제

사전 지정 env0..7의 첫 곡 실제 body quaternion을 재구성했다. **5모델의 이8개 캡처는 모두 안전완주**라 실패 자세 표본은0이다. 특히500모델의 나머지610실패 환경을 대표하지 않는다. t0를 제외한60Hz 끝점이 분모이며, 각 손가락/모델의 유효 끝점은15,752개다. 분석은 full quaternion의 부모-자식 상대회전·source 굽힘축을 쓰고 독립 SciPy 수식과 대조했다.

| 모델 | 검지 PIP 평균 | 중지 PIP 평균 | 약지 PIP 평균 | 소지 PIP 평균 |
|---|---:|---:|---:|---:|
|초기0|51.823°|38.353°|89.330°|22.645°|
|500|84.797°|79.523°|89.988°|57.755°|
|1000|84.037°|78.159°|89.996°|82.649°|
|1500|6.566°|8.451°|89.996°|80.803°|
|2000|14.796°|1.175°|7.704°|85.687°|

500에서 `DIP−PIP>20°`는 네 손가락 모두0이었지만, 소지의 **완전 대기** 끝점 중DIP>60°는50.2%였다. 최종2000에서는 검지83.6%·약지91.3%의 유효 끝점이 `DIP−PIP>20°`였고, 소지는 완전대기DIP>60°가76.3%였다. PIP 평균 증가나 한 soft prior 위반의 감소만으로 자연스러움 개선을 결론내릴 수 없다. 이 값은 실험적 source 기하 기준이지 인체 가동범위 인증이 아니다.

현재음·준비음·완전대기와0.25초 fade, 안전/실패, 동일 envID의 공통 안전 비교는 [자세 원자료](posture_analysis/analysis.json)에 분리돼 있다. raw helper 품질은 실패/단계 마스크 이전60Hz 진단으로 실제240Hz 획득 보상과 같지 않다. native q1_x와 실제 MCP의 정의도 다르며 차이를 추종 오차로 바꾸지 않는다. 속도·jerk를 측정하지 않아 급가속 개선도 주장하지 않는다.

## 선정500회 모델의 영상

선정500모델의 실제 GPU world pose를 software GL로 재생한 전신·왼손 영상이 모두 완료됐다. 두 영상은1280×720/H.264/yuv420p·60fps·1969프레임·32.816667초다. root가 전프레임 decode와1/985/1969프레임의 전신·손·넥·자막을 직접 확인했다. [영상QA](media_qa.json)의 위치오차는0m, 회전 최대오차는6.38e−16rad이며 추가 물리 적분은0이다. 입력 SHA 불변과 렌더 GDB 정상 exit도 확인했다.

![선정500회 모델 전신 영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/best_fullbody_video/best_fullbody_60fps.mp4)

[전신 영상](best_fullbody_video/best_fullbody_60fps.mp4) · [완료보고서](best_fullbody_video/report.json) · [pose 감사](best_fullbody_video/pose_audit.json).

![선정500회 모델 왼손 확대 영상](/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6/best_hand_video/best_left_hand_60fps.mp4)

[왼손 영상](best_hand_video/best_left_hand_60fps.mp4) · [완료보고서](best_hand_video/report.json) · [pose 감사](best_hand_video/pose_audit.json).

사전 캡처 env0..7의 안전완주 최저ID 규칙으로500모델 env0을 사용했다. 이 예시는4/67음이며 전체 평균5.4287음이나 전체610실패를 대표하지 않는다. 실제 GPU world pose의60Hz 프레임을 재생했고 새 물리 적분·정책 추론·보간·음향을 추가하지 않았다. source t0 포함1970프레임 중 control endpoint1969개를 영상에 썼다.

전신 SHA: `5465bcd677b0e796500214d2ea8d53f39949738e2962dff9713e1d379a980bf4`; 왼손 SHA: `24cbe1699a3afd6b3ee5ccd93add0a29e76385f943fcfb6af2de24cf6e00fb65`.

## 해석과 호환성의 경계

- 단계0은 손가락 동작 금지가 아니다. 접촉/타이밍 가중치.5와 독립 LH21 누적 제어가 계속 유효했다. 마지막 최근256 안전율87.8906%와 중지·약지·소지 near0%는 안전90%·모든 등장 손가락 near20% gate를 충족하지 못했다.
- 성공은 기존 현·프렛·지정 손가락의 후보와 **유효 clean 시간 누적40%/최소50ms** 조건이다. 후보의240Hz 양끝 확인과 전체 요구시간 누적을 구분하며, 요구시간이 연속한 한 덩어리여야 한다는 뜻은 아니다. GPU net body load·유한 표면 표본은 접촉 pair/witness·교정압력·진동·소리를 인증하지 않는다.
- 가동범위·관절 독립성·PD·물리·PPO 설정·초기 latent std `exp(-3)`는 바꾸지 않았다. 기존 KL retry는 global18/832에서 자동 actor LR 감소를 적용했고 최종1.875e−6이었다. source/config 불변과 학습 파라미터 불변은 다르다.
- 동일 v6의 **1300→2000 strict 복구는 실제 검증**했다. 최종2000→2001의 추가 실제 PPO 재개는 실행하지 않았다. 구 v4/v5 및 다른 입력/보상 계약은 source 개수436이 같더라도 strict resume할 수 없다. CPU·오른손의 별도 계약도 유지한다.

## 결과 위치와 보존·봉인

| 자료 | 경로·검증 범위 |
|---|---|
|유효 원prefix1300|[프로젝트 밖 durablecopy](/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1), [phase alias](recovered_train2000_restart1). 원본1387파일/4,499,049,842bytes를 보존하며 prefix 외62개 후속 update도 그대로 남는다.|
|새700 정상 실행|[train_resume700_restart1](train_resume700_restart1), [GDB 로그](train_resume700_restart1_gdb.log), [report](train_resume700_restart1/report.json)|
|전체 검산|[recovery_verification.json](recovery_verification.json): source436·원/새입력581/582·3331 재생오차0·모델/양optimizer56/54/57 finite, 구간별 raw/close 범위|
|고정5평가|[recovery_checkpoint_evaluation.json](recovery_checkpoint_evaluation.json), [실제 GDB](evaluate_recovery_gdb.log). 각1024환경·각602입력pin·실제close|
|학습·자세 분석|[analysis_final](analysis_final), [training_findings.md](training_findings.md), [posture_analysis](posture_analysis) — 자세40캡처/668핀, 고정평가/영상과 분모 분리|
|선정 영상|[best_fullbody_video](best_fullbody_video), [best_hand_video](best_hand_video), [media_qa.json](media_qa.json) — 각609핀/새물리0/모델500·env0·4음|
|소스/기준/원문 보관|[training_source_manifest.json](training_source_manifest.json), [source_training](source_training), [before_manifest.json](before_manifest.json), [preflight](preflight.md), [계획](../../plans/guitar_learning_long_training_v6_20261022.md), [4문서 변경 전 보관](/home/ajou/yigyu/3/guitar_learning/archive/20261022_before_long_training_results_v6/manifest.json)|

복사 target은 원NTFS 볼륨이 아니라 **프로젝트 밖의 같은 로컬 SSD**에 있다. 원래 phase 경로는 symlink로 보존했고 원manifest/입력pin은 고치지 않았다. [별도copy 봉인](external_copy_seal.json)의 target manifest SHA는 `e221dfbee9a01a6f5cbac99cef0fe5eb336f00eb2348687c1b56ff4c907689aa`다. phase [result_manifest.json](result_manifest.json)은 자기 자신을 제외한 결과 파일과 alias를 봉인하고, alias target의 파일들은 별도 manifest로 검증한다. 로컬 phase의 최종 봉인은 문서 검수 후 root가 생성할 manifest를 기준으로 확인한다. 이 문서 작성 시 별도copy 봉인은 완료했으나 로컬 phase까지 이미 봉인했다고 주장하지 않는다.

[보존 검산](preservation_final.json)은 활성436 Python/SHA·동결 사본 및 다음 과거3봉인을 확인했다. 파일·자산·과거성과를 이번 결과로 덮어쓰지 않았다.

| 기존 봉인 | 파일수 | manifest SHA256 |
|---|---:|---|
|[손가락 입력 v6](../guitar_learning_finger_inputs_v1/README.md)|493|`03588cd5c3c5b042eb3f3f64d1574aed8d2902c716e7a4b850309f3e4a20f42a`|
|[관절 분담 v5](../guitar_learning_finger_coordination_v1/README.md)|516|`eeb234a0f07cde359a7266d0ed5c1d43ac30099a560b91aaf6fa570f2e0623a5`|
|[이전 장기 v4](../guitar_learning_long_training_v4/README.md)|2659|`8a167fe1090c35fee83fa5f8aa0704b6ee043af675ccbdf3986f2c40e52c47ef`|

[임시 자원 원복](temporary_storage_final.json)은 RAM 캐시3,644,790,537bytes 해제·잔존 없음, 임시 `gc.auto=0`/`maintenance.auto=false` 두 키의 원래 absent 상태 복원, 새 Git connectivity 검사exit0을 확인했다. 유효 pack/refs/index와 학습 원자료는 바꾸지 않았고 `.gitignore`의 세 학습 출력 pattern은 유지했다. 원복 직후 여유는 root 확인 약3.68GiB이며 이후 시점의 여유를 보장하지 않는다.

[고정 평가 독립검수](independent_fixed_evaluation_review.md)·[학습 검수](independent_final_training_review.md)·[자세/영상 독립검수](independent_pose_media_review.md)의 인증 범위는 실행·데이터 정합성이며 성능/자연스러움 개선 인증이 아니다.

선택 경로의 post-cache GPU free 최저7.0186GiB, host available 최저9.1799GiB, run/project disk의 귀속된 관측 최저3.2842GiB다. GPU free+reserved 잔차 증가는 프로세스별 최대.0332/.0957GiB로 각각 계산하며 SDK 누수 해결의 일반 증명으로 합치지 않는다. 자원 여유가 관측됐다는 사실은 앞선 저장 I/O 중단이 없었다는 뜻도 아니다.

## 동일 조건과 원자료의 재현

이미 존재하는 결과는 덮어쓰지 않는다. 동결436소스·자산·rl38/Isaac Gym 환경을 사용하고 충분한 **현재** 저장 공간·host/GPU floor를 확인한 뒤, native 학습/평가/GL은 한 번에 하나씩 실행한다. 아래는 재현 명령 예시이며 이 새 이름으로 추가 재현을 수행했다는 뜻은 아니다.

```bash
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1 PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
RUN_PHASE=/home/ajou/yigyu/3/docs/2026-10-22/guitar_learning_long_training_v6
HISTORY=/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recovered_train2000_restart1
RESUMED="$RUN_PHASE/train_resume700_restart1"
/home/ajou/miniconda3/envs/rl38/bin/python -B -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 --seed 7 \
  --updates 2000 --checkpoint-every 100 \
  --out /home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/train2000_reproduce
```

이번에 저장한1300회에서 추가700회를 재현하려면 같은 조건과 새 출력 경로를 지정한다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -B -m guitar_learning.train \
  --hand left --song 05_BN2-131-B_solo --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 --seed 7 --checkpoint-every 100 \
  --resume "$HISTORY/checkpoint_001299.pt" --updates 700 \
  --out /home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/resume700_reproduce
```

현재 완료 경로의 CPU 검산·분석은 아래처럼 실제old/new/derived manifest를 명시한다. **봉인 phase 안에 파일을 추가하지 않고**, 아래의 별도 새 `RECHECK_OUT` 아래에 모든 재검산·평가·영상 출력을 둔다. 같은 이름이 이미 있으면 다른 새 이름을 고르고 원raw는 복제하지 않는다.

```bash
RECHECK_OUT=/home/ajou/yigyu/guitar_learning_runs/20261022_v6_long/recheck_01
mkdir "$RECHECK_OUT"
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/verify_recovery.py" --old-run "$HISTORY" --run "$RESUMED" \
  --copy-manifest "$RUN_PHASE/recovery_copy_relocated_manifest.json" \
  --out "$RECHECK_OUT/recovery_verification.json"
CUDA_VISIBLE_DEVICES='' /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/analyze_recovery.py" --old-run "$HISTORY" --run "$RESUMED" \
  --copy-manifest "$RUN_PHASE/recovery_copy_relocated_manifest.json" \
  --verification "$RECHECK_OUT/recovery_verification.json" --plots \
  --out "$RECHECK_OUT/analysis"
```

같은5개 모델을 새tag로 다시 고정 평가하고, 그 재평가의 `recheck_checkpoint_evaluation.json`이 선정한 모델의 새 저장 pose를 재생하는 예시다. 출력은 모두 위의 별도 `RECHECK_OUT` 아래이며 기존 평가·영상을 바꾸지 않는다.

```bash
/home/ajou/miniconda3/envs/rl38/bin/python -B "$RUN_PHASE/evaluate_recovery_checkpoints.py" \
  --prefix "$HISTORY" --resumed "$RESUMED" \
  --copy-manifest "$RUN_PHASE/recovery_copy_relocated_manifest.json" \
  --verification "$RUN_PHASE/recovery_verification.json" \
  --out "$RECHECK_OUT" --tag recheck --checkpoints 2000 0 500 1000 1500
MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/render_video.py" --evaluations "$RECHECK_OUT/recheck_checkpoint_evaluation.json" \
  --selection best --view fullbody --out "$RECHECK_OUT/best_fullbody"
MUJOCO_GL=osmesa LIBGL_ALWAYS_SOFTWARE=1 /home/ajou/miniconda3/envs/rl38/bin/python -B \
  "$RUN_PHASE/render_video.py" --evaluations "$RECHECK_OUT/recheck_checkpoint_evaluation.json" \
  --selection best --view hand --out "$RECHECK_OUT/best_hand"
```

모델 선정 규칙의 best 영상과 latest 모델은 구분한다. 이 명령은 새 물리로 음악·압력을 생성하거나 학습을 보완하는 과정이 아니다.
