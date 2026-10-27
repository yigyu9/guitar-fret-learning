# 표면 압현 보상v3 장기 학습·평가·전신영상

새 정책의 최종 모델 경로 **2,000회·65,536,000전이**를 완료했다. 초기·최종 고정 정책의 평균 달성은 **3.86→8.30/67음**으로 증가했지만 최종 달성의 **98.6%가 검지**이고 중지는0,67음 전체 과제 성공도0이다. 네 손가락의 곡 연주가 충분히 학습된 결과는 아니다.

## 고정 초기·최종 평가

각 체크포인트를 `large/1024환경/seed7`의 같은67음 곡·035/v14 준비 자세에서 결정적 행동으로 평가하고 환경별 첫 곡만 집계했다. 자체 curriculum 관측은 초기0/최종1이므로 순수 Actor만의 ablation은 아니다.

| 지표 | 초기0회 | 최종2000회 |
| --- | ---: | ---: |
| 평균 달성 음 / 곡67음 | 3.8613 | 8.3008 |
| 안전 시간축 완료 /1024 | 1024 | 1020 |
| 물리 종료 | 0 | 4 |
| 67음 전체 달성 | 0 | 0 |
| 관찰된 최대 달성 음 | 8 | 16 |

최종 총8,500개 달성은 검지8,383·중지0·약지111·새끼6개다. 손가락별 배정 음 기회에 대한 달성률은 각각32.746%·0%·0.903%·0.049%다. 안전곡만의 최종 평균은8.3108음이며 두 정책 모두 안전한 동일1020환경 집단도3.8657→8.3108음으로 증가했다. 물리 종료4건은 모두 기타 변위이며8.467/23.117/26.600/31.067초에 발생했다. 실제 현 압력·음향 성공이나 다른 곡/독립 seed의 일반화 검증은 아니다.

[고정 평가 상세 해석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/evaluation_interpretation.md) · [집계 수치](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/evaluation_analysis.json) · [체크포인트·종료 검증](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/checkpoint_evaluation.json)

## 학습 로그가 보여주는 병목

접근 승급은574회에 시작해596회에 접촉 단계1이 됐고 끝까지 단계1이었다. 최종 최근256곡의 접촉은 검지44.92%·중지0.803%·약지2.474%·새끼0.293%로 모든 손가락20% 조건을 검지만 충족했다.

중지의 고정 평가 접근은83.1%인데 유효 접촉은0.076%이고 음 달성은0이다. 실제 음 구간에 clean이 있었던67개 기회도 모두 요구 유지시간 미달이었다. 약지는 다른 조건의 몸체 하중이 많아도 목표 위치의 하중은 드물고, 새끼는 접근 자체도22.1%로 낮다. 같은 방식으로 한꺼번에 설명할 병목이 아니다. 선택 표면 표본의 몸체 하중을 손가락 전체 하중이나 현 압력으로 해석하지 않는다.

학습 수집의 마지막100회 평균은8.061/67음이며, 마지막250회 안전곡 평균8.090음의99.43%가 검지였다. 약지·새끼는 학습 후반 낮아진 구간이 있다. 이는 변동하는 확률 정책의 수집이며 위 고정 평가와 분모·정책이 다르다. 현재 코드에 이미 손가락별 음 수 정규화가 있어 단순히 검지 배정 음 수가 많은 탓으로 결론내리지 않는다.

PPO 비유한 기록0·행동 포화0, latent std평균0.04956이다. actor LR은55회/916회에기존 KL 재시도로3e-5→7.5e-6→1.875e-6가 됐다. 후반 추가 변경은 없었다. 후속 우선순위는 목표 위치에서의 하중과 clean 유지, 손가락별 수집·공유 정책 간섭을 분리 비교하는 것이다. 추가 계수·물리 변경은 이 실행에 포함하지 않았다.

[학습 수집 상세 해석](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/training_interpretation.md) · [곡선](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/analysis_final/training.png) · [PPO](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/analysis_final/ppo.png) · [자원](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/analysis_final/memory.png)

## 최종 체크포인트의 전신 영상

[전신 영상:1280×720·60fps·32.8167초](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/final_video/final_fullbody_60fps.mp4) · [최종 체크포인트](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/resume1200/final.pt)

미리 정한 환경0~7 중 안전하게 첫 곡을 끝낸 최저ID인 환경0을 사용했다. 이 영상의 달성은9/67음이며 최고 음악 점수를 골라낸 영상이 아니다. 최종2000회 정책의 실제 GPU 평가 자세를60Hz로 저장하고 같은 원자산으로 정적 렌더링했다. 새 물리 적분·정책 재실행·프레임 보간은 없다.

원자료1970자세(t0포함) 중 실제 endpoint1969프레임을 영상에 사용했다.106몸체/105관절·영상시간·전 프레임 pose/projection 검사를 통과했고 최대 위치오차0m·회전오차6.29e-16rad다. 독립 ffprobe로H.264/1280×720/60fps/1969프레임을 확인했다. 처음·중간·마지막 이미지를 직접 열어 머리·발끝·기타와 자막 구도를 확인했다.

[영상 원자료·프레임 감사](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/final_video/pose_audit.json) · [육안·독립 미디어 확인](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/video_visual_check.json)

![전신 영상 중간 프레임](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/final_video/preview_0985.png)

## 실행·오류 복구와 검증 범위

| 구간 | 사용한 업데이트 | 다음 저장 시점 | 제외한 미저장 업데이트 |
| --- | ---: | ---: | ---: |
| 최초 실행 | 300 | 300 | 8 |
| 첫 재개 | 150 | 450 | 35 |
| FE_INEXACT 보호 후 재개 | 350 | 800 | 20 |
| Dragon4 적용 후 재개 | 1200 | 2000 | 0 |

앞선 세 실행은 로그의 CPython float 변환 중 SIGFPE로 종료했다. CPU 검산에서도 같은 오류가 관찰됐다. 첫 FE_INEXACT 보호는 불충분했으며 과거의 Dragon4 직렬화 구현을 찾아 로컬 기본 인코더에 적용했다. 전역 JSON API/FP상태와 물리·보상·성공·PPO 계약은 바꾸지 않았다. x87 상태 변경의 근본 주체는 여전히 미확인이다.

미저장63회·2,064,384전이는 원로그에 보존하되 최종 모델 경로에서 제외했다. 세 과거 전체 gzip CRC/EOF 감사는 각각 통과했지만 정상 native 종료·cleanup이 없었으며, 이 실패를 완료 실행으로 재분류하지 않는다. 재개는 모델·양 optimizer·RNG·3331값 curriculum을 정확히 복원하고 물리는 준비 자세의 새 곡으로 시작했다. 단일 프로세스의 연속2000회 실행이 아니다.

마지막1200회는3시간38분30초 후프로세스exit0/GPU close/cleanup오류0·변경입력0·누락핀0으로 종료했다. 자원 guard의 GPU 여유 최저6.927GiB와 optimizer후cache반환 직후 최저7.638GiB를 구분한다. 해당 구간의 비Torch 잔차 추정 증가는34MiB에서 일정했다. OOM·추가 SIGFPE는 없었지만 모든설정의 누수 부재나 런타임 근본 해결을 뜻하지 않는다.

전체CPU831검사, 관련48검사·독립검수, 새 기록 방식의370회 전체CPU재생3회가 통과했다. 최종 경로원시64,000행·보상/비용/episode 대응·입력SHA·최종 모델/두optimizer 유한성·3331상태 재생오차0도 통과했다. 과거427/427/429소스는 당시snapshot으로, 새429소스는 현재snapshot으로 검증했다.

[최종 실행 검산](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/training_verification.json) · [학습 프로세스 정상 종료](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/training_process_result.json) · [전체CPU검사](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/cpu_tests.json) · [실행 원로그](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/resume1200_gdb.log) · [최종 설정](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/resume1200/settings.json)

과거 실패 원자료: [최초](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_v1/README.md) · [첫 재개](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_recovery_v1/README.md) · [첫 보호 실패](/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1/README.md).

실제 마지막 구간의 일반 학습 명령은 다음과 같다. 환경 설정은 [기본 README](/home/ajou/yigyu/3/guitar_learning/README.md)를 따른다.

```bash
python -m guitar_learning.train --hand left --physics gpu --device cuda:0 \
  --size large --num-envs 1024 --horizon 32 --seed 7 \
  --updates 1200 --checkpoint-every 50 \
  --resume /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_logging_fix_v1/resume1550/checkpoint_000349.pt \
  --out /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_surface_training_json_v2/resume1200
```

위 출력은 이미 생성된 증거이므로 재실행 때는 새 출력 디렉토리를 지정한다. 실제 실행은 GDB·faulthandler로 감시했고 감독 프로세스가 학습 종료 뒤검산→분석→초기/최종 평가→비교→영상 순으로 정상 완료했다.
