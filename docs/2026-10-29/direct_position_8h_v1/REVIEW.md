# 8시간 실행 도구 독립 검수

요약 판정: 문제없음. 학습 시작을 차단하는 Critical 문제는 발견하지 않았다.

검수 범위는 이번 실행용 `tools/train_timed.py`, `tools/pipeline.py`, `tools/analyze.py`와 이들이 호출하는 기존 실행·평가·영상 API의 계약이다. 활성 학습 코드는 수정하지 않았다.

## Critical

없음. large/1024/H32, 새 학습, 28800초 시간예산 전달과 최종 저장 흐름이 기존 실행기에 연결된다. 최상위 completed=false/stopped=wall_budget를 실패로 잘못 취급하지 않고 J 보고서 완료 및 실패 상태를 확인한다. 시간 검사는 optimizer 경계에서 이루어져 한 업데이트와 정리 시간만큼 초과할 수 있다.

## Warning

없음. 최초 검수의 중간 평가 누락은 수정되었다. `tools/analyze.py:124`가 초기·중간·최종을 모두 읽고, 선택 후보의 평가 근거 존재를 검증하며 결과 문서에 선택 이름·경로·규칙을 남기는 것을 재확인했다.

## 확인 근거

- 실제 pilot 8업데이트의 J 보고서 wall_s=133.552369, completed=true. steady-state 수집 약11.6~13.4초와 최적화 약3.8초/업데이트다. 최종 pipeline은 pilot 평균과 마지막3회 중앙 처리시간 중 빠른 값을 사용하고 35% 여유를 둔 업데이트 상한을 설정한다. 현재 실측 조건에서 8시간 시간예산에 도달할 수 있는 범위다. 향후 처리속도 변화나 조기 업데이트 상한 도달 시 실제 wall_s를 보고한다.
- 초기·중간·최종은 동일 전곡 범위 및128환경 독립 평가로 실행하고, 평균 달성 음으로 평가한 후보 안에서만 선택한다. 전체 저장본 최고라는 주장은 하지 않는다.
- 9보상항은 실제 control transition 수로 가중한다. 구간·전곡 에피소드, 완료·마감 미완료 진단, sensor 유효 표본을 분리하고 RMS는 제곱평균으로 합친다.
- 신규 진단의 실제 pilot 기록 전체를 읽어 CPU에서 분석·그래프 출력을 실행해 종료코드0을 확인했다. 산출물은 `/tmp/direct8h_review_q9xr727v/analysis/`에 두었다. GPU 작업은 시작하지 않았다.
- 상세 trace는 첫600제어틱뿐이므로 후반 정책의 증거로 사용하지 않는 제한을 명시했다. native 센서를 모터 구동력/힘 상한 도달률로 오해하지 않는 설명도 유지했다.
- 디스크 사용량 전망과 실제 장기 학습 성과는 root가 별도 확인한다. 8시간 실행 완료를 미리 주장하지 않는다.

최종 재검수: 실행 도구3개의 AST 문법 검사를 통과했다. 중간 평가 포함·선택 근거 읽기 변경은 도구 내부 집계에 한정된다. 새 GPU 작업은 수행하지 않았다. 장기 학습 완료 이후 실제 보고서·평가·영상은 별도 확인이 필요하다.

## 실제 8시간 결과 독립 검수 (2026-10-29)

요약 판정: **문제없음**. 아래는 실행 준비 검수와 구분한 실제 완료 산출물 검수다. 성능이 충분하다는 판정은 아니다.

### Critical

없음. `pipeline_status.json`은 completed=true/phase=complete다. `train/J/report.json`에서 1626회, 53,280,768전이, 28,802.980245초를 확인했다. 이는 1024×32×1626과 일치한다. phase completed=true, stopped=wall_budget, failure=null, lifecycle_verified=true, 변경 입력·누락 pin·정리 오류가 모두 비어 있다. 저널은 전이가 모두 committed/durable이고 closed=true/failed=false다. 최상위 train/report.json의 completed=false는 요청 상한2350회를 소진하지 않은 시간예산 종료를 나타내므로 실패로 해석하지 않는다.

### Warning 및 해석 제한

- 별도 평가128환경의 평균 달성은 초기1.5625 → 중간3.328125 → 최종7.9296875/67(11.835%)이다. 각 `evaluation/*/episodes.jsonl`의128행을 독립 합산해200/426/1015개를 확인했다. 세 평가 settings는 완전히 같고 full_song이며 실제 실행기는 deterministic=True를 사용한다(`guitar_learning/training/finger_skill_runner.py:440`). **전곡 stage_success는 모두0/128**이므로 전곡 연주 성공이나 충분한 숙련으로 해석하지 않는다.
- 최종 평가의 물리·손목 실패는0/128, timeline_complete128/128이다. 이는 해당 평가의 안정성 근거이며 학습 중 실패가 없었다는 뜻은 아니다. 학습 전곡17,822에피소드 중3,252개가 terminal_failure다.
- 영상은 선택한 final.pt와 동일 checkpoint SHA이며 env0 한 에피소드의 달성은3/67이다. 별도128환경 평가 평균7.9296875를 영상 한 회가 재현한다고 주장하지 않는다. 영상은 전곡 시각 검토 자료이고128환경의 대표 표본임을 보장하지 않는다.
- 앞뒤10% 보상 비교는 초기 구간 학습과 후반 전곡 학습이 섞여 있어 동일 과제의 인과 비교가 아니다. 관절 추종 요약도 전 학습 완료 에피소드 집계다. 낮은 평균 오차만으로 압현 구간의 국소적 막힘이나 접촉 문제를 배제하지 않는다. 상세 trace는 최초600제어틱이므로 최종 정책의 증거로 사용하지 않는다. net generalized force는 모터 힘이나 힘 상한 포화율이 아니다.
- 접촉/달성은 현재 GPU 패드 기하 및 하중 판정이다. 실제 줄 압력·발음·음향 성공, 다른 곡·seed에 대한 일반화, 누적제어와 동일조건 성능 우위는 이 자료만으로 입증되지 않는다. 선택 후보는 초기·중간·최종3개이며 모든 저장본 중 최고라는 뜻이 아니다.

### 영상 검증

`video/report.json`은 completed=true/failure=null/scene_closed=true/lifecycle_verified=true, 인코더2개 exit0, policy_unchanged=true/native_pixels=true, source_checkpoint_pins_validated=true다. 손·전신 mp4를 각각 ffprobe로 검사해 H.264,1280×720,30fps,984프레임,32.8초를 확인했다. 두 파일 모두 `/usr/bin/ffmpeg -v error -i <file> -f null -` 전체 디코드에서 exit0 및 오류 출력 없음. GPU 작업이나 활성 학습 코드 변경은 하지 않았다.

### 최종 해석·추가 집계 재검수

요약 판정: **문제없음**. 새 `README.md`, `analysis/INTERPRETATION.md`, `analysis/final_detail.json`, `analysis/overview.png`, `analysis/evidence_manifest.json`을 확인했다. 최종 평가128개 원시 에피소드의 ledger를 독립 재계산해 최초 접촉 미달7,257건·접촉 후 달성 미달304건·달성1,015건, 합계8,576건을 확인했다. 달성인데 최초 접촉 미달인 사례는 없었다. 손가락별 목표 분모3,200/2,304/1,536/1,536과 near·contact·success 비율을 원시 finger_metrics로 다시 가중 합산했으며 추가 집계 및 문서와 일치한다.

원시240Hz 관절 요약에서 유효 물리 표본 수로 RMS를 재계산한 비엄지16축 전달목표 오차 범위는0.00157081677~0.02568564458rad다. 원시 에피소드의 목표각 범위 평균을 재계산한 pinky1_x는0.0002767322585rad=0.01585559도다. 엄지 접촉 후보0.17190277%·근접1.55158869%·평균 signed gap7.57472803mm도 시간 가중 재계산 결과와 일치한다. 좁은 목표 움직임을 근거로 명령 측 병목 가능성을 제시하되 힘 부족을 확정 배제하지 않은 해석은 타당하다.

성과 그래프를 직접 열어 숫자·단위·목표 분모·기하접촉 판정 주석과 한글 렌더링을 확인했다. evidence_manifest의11개 파일 SHA256은 모두 실제 파일과 일치한다. 영상env0=3/67과 별도평가평균7.93/67 구분, 단일seed·곡 및 미평가 저장본·접촉 판정의 제한, 구간/전곡 보상 비교의 교란을 최종 해석 문서가 명시한다. 활성 코드 수정이나 새 GPU 작업은 하지 않았다.

### 원인 분석 문서 검수

요약 판정: **문제없음**. `analysis/CAUSE_ANALYSIS.md`를 추가 집계와 실행 당시 소스에 대조했다. 원시 learning_metrics.jsonl 전체1,626행을 CPU에서 다시 읽어 학습률 변경이 index173의3e-5→1.875e-6 한 번뿐이고 해당 행 재시도2·최대 시도KL0.02291435임을 확인했다. 낮은 학습률 기록은1,453/1,626=89.3604%다. 마지막100회의 raw reward/cost advantage 표준편차 평균0.17480359/0.69359747, accepted minibatch 제한 전 경사norm 평균8.001657, 최종KL 평균0.00470212도 독립 재계산과 일치한다.

`training/ppo.py`의 재시도 가중치·Adam 복원 후 학습률 감소와 이후 회복 경로 부재, joint advantage 결합 후 정규화를 확인했다. `gpu/finger_skill_environment.py`의 거리 potential 및 최대20% 방향 감소, `gpu/finger_reward.py`의 tracking=1-idle과 준비 lead0.35초 계약은 문서 설명과 일치한다. 이 파일들과 control.py·training/policy.py 총5개 SHA256이 학습 inputs_before.json과 일치함을 별도 확인했다.

작은 동작 범위·접촉 획득 병목은 기존 독립 확인된 최종평가 근거와 일치한다. checkpoint_exploration.json의 초기/최종 표준편차와 evaluation_reward_comparison.json의 보상 합산 수치는 문서 반올림과 일치한다. 이번 재검수에서 checkpoint를 직접 재로드하거나 원시4.6GB 에피소드 스트림을 다시 읽지는 않았다. 표준편차 데이터 파일의 key 이름은 log_std지만 문서는 변환된 실제 std 값으로 올바르게 설명한다.

비용 advantage 규모를 정책 경사 기여율로 단정하지 않고, 낮은 학습률을 실제 갱신량16배 감소로 해석하지 않으며, 좁은 탐색/준비 창/방향 신호는 통제 실험 전 가설로 구분한 점이 적절하다. 전면 재작성이나 전역 힘 증가·안전 종료 제거를 근거 없이 요구하지 않는다. 추가 학습 가능성과 원인별 기여율 미확정을 함께 명시했다. 활성 코드 변경·GPU 실행은 하지 않았다.
