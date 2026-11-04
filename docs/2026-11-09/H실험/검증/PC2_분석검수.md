# PC2 H 분석·후처리 도구 독립 검수

검수일: 2026-11-04 KST. 대상은 새 `도구/pc2_analyze_v1.py`, 이어 요청된 `pc2_finish_v1.py`·`pc2_report_v1.py`, 공식 V5 원장·checkpoint reader·renderer schema와 CPU 검사 기록이다. 도구 코드는 직접 수정하지 않고 메시지로 보완을 전달했다. 검수자가 작성한 파일은 이 문서뿐이며 원본 snapshot·C1·봉인·진행 중 감독·로그·결과를 변경하지 않았다. GPU·학습·평가·렌더 및 전체 분석 main을 실행하지 않았다.

## 판단

**확인한 실행 전 코드 범위에서 미해결 필수 수정 사항은 없다.** 준비 관측 노출과 진단창의 혼동, 동률 모델 선택의 모호성은 아래와 같이 보완됐다. 아직 본 실험의15개 평가가 없으므로 전체 main·완성 집계·선정 결과·6개 영상의 종단 검증은 수행하지 않았다. 실제 산출물은 완료 후 별도 대조해야 한다.

## 공식 유지·해제와 분모

- 압축 episode는 봉인 사본의 `training_log_io.iter_episode_rows()`로 복원한다. report 완료·첫 환경별 episode·실패 포함, env_id 0..31의32개와 full_song/선택20목표를 확인한다. 고정 분모는640음, P1~P9×32의288구간이다. 실패 전에 도달하지 못한 음을 분모에서 제거하지 않는다.
- 개별 strict는 공식 best_clean_streak가 전체 음 길이에 도달했는지 1e-9 허용치로 계산하고 원장의 strict_success와 동치인지 검사한다. legacy40% 달성이나 누적 clean을 전체 연속 유지로 치환하지 않는다.
- 필요한 해제는 공식 `press_completion`의 released/not_required만 인정한다. pending/missed/aborted를 성공으로 바꾸지 않으며 note end 관측도 요구한다. 연속된 동일 목표의 중간 해제 예외는 공식 release_required/status를 그대로 소비한다.
- 앞 음을 완료한 뒤 후반 episode가 실패한 기록은 개별 hold+release와 safe_episode_hold+release를 나눠 보존한다. 개별 기하 수행 기록을 해당 note의 독립적인 물리 안전 인증으로 확대하지 않는다. 전곡 completion은 공식 safe/timeline/strict note·overlap group·release 조건의 완료 flag를 사용한다.
- P1~P9는 원본 metadata와 source 시각으로 연결하고 구간별 목표 수를 확인한다. 겹치는 target 집합의 공식 coordination strict도 구간 판정에 요구한다. 개별 note가 달성됐다는 이유로 동시 구간을 자동 성공 처리하지 않는다.

`검증/PC2_strict해제_집계검사.json`은 실제 중단 scope, 완료 음 뒤 후반 실패, missed release, 1physics tick 부족의4개 CPU fixture 통과를 기록한다. 검수자는 공식 구현과 검사 기록을 읽었고 이를 다시 실행하지 않았다.

## 준비 노출 보완

초기 구현은 `values.exposure_time>0`을 preparation_observed라고 불렀다. 실제로 이 값은 `[press−2,end]` 표면 기하 진단창 적분이다. V5 E4의 첫 목표는 t0부터 priority에 노출될 수 있어, 이 창 이전 실패에서도 목표를 이미 관측했을 수 있다. 이를 실제 준비 관측 또는 목표 미노출로 해석하면 안 된다고 지적했다.

수정본은 `surface_diagnostic_window_exposed`/`surface_window_exposed_notes`로 이름을 바꿨고 실제 `preparation_goal_observation_exposed`는 미기록 None으로 남긴다. 전체 환경의 observation/goal-mask 이력이 없어 selector를 임의 재구성하지 않는다. 원래 source clock으로 발음 시작·음 끝 도달만 별도 집계한다. 보고서도 목표 미노출 대신 발음 구간 미도달과 도달 후 미완료를 구분하도록 보완됐다. `exposed_failed_notes`라는 내부 집계는 audible_started 기준이므로 실제 목표 토큰 노출 지표로 해석하지 않는다.

## 모델 선정 보완

처음 구현은 상위 유지+해제/실패/clean이 같은 중간 모델들 사이에서 전이가 더 큰 것을 골랐다. 이는 “동률이면 final”이라는 사전 규칙을 항상 구현하지 못한다. 중간 둘이 최고 동률이고 final이 낮아도 final fallback을 명시하도록 요청했다.

수정 `select_model()`은 유지+해제 음 수 최대→실패 episode 최소→clean 최대 순으로 후보를 좁히고, 마지막 집합이 복수이면 final이 집합 밖이어도 final을 선택한다. clean의1e-9초 수치 동률만 허용하며 원시 성공 판정은 바꾸지 않는다. 유일 최고는 해당 모델을 선택한다. `검증/PC2_모델선정검사.json`의3개 CPU 검사(중간 둘 동률/final 열세, 유일 중간 최고, 안전성 우선) 통과 기록과 수정 코드를 확인했다.

선정은 같은 C1 평가에 사용한 모델 가운데 대표를 고르는 과정이다. 별도 테스트셋 일반화 성과가 아니며 후속 보고도 이를 명시한다. 주 H 비교는 공통 최종16,777,216전이 결과를 사용하고 대표 영상 선정값과 분리한다.

## 입력·초기 모델·시간·학습 지표

- 모든 checkpoint를 저장 manifest SHA 및 공식 V5 read_checkpoint로 검증한다. source clock·입력·전체 architecture/contract 검사를 임의로 우회하지 않는다. 저장 update×H×1024와 지정 평가 전이를 대조한다.
- 세 조건 초기 model tensor SHA의 동치를 확인하도록 구성됐다. 동일 초기 신경망을 확인하는 검사이며 전체 초기 native 상태·GPU 물리 궤적의 bit 재현까지 보장하는 것은 아니다.
- 실제 latent std는 checkpoint의 log_std33에 원래 clamp[-5,2]와 exp를 적용한다. support17/finger16 구분은 공식 구조와 맞는다. entropy는 latent Gaussian이며 물리적 관절각 또는 tanh 행동 entropy가 아니다.
- native events UTC와 감독의 실행 시작 시각을 비교해 시간축을 만든다. 초기/중간 점은 해당 checkpoint 직후 다음 collecting phase가 시작된 관측 시각이고, 최종은 감독 receipt wall_s로 검증 등 종료 후 overhead도 포함한다. checkpoint 파일의 정확한 fsync 완료 timestamp라고 확대하지 않는다. 수집+업데이트 합과 평가 시간은 별도로 보존한다.
- 원래 `update_s`는 PPO와 commit 등 업데이트 구간의 시간이다. 보고서의 최적화 시간은 이 필드를 집계한 값이며 순수 GPU optimizer kernel 시간으로 해석하지 않는다.
- 실제 memory 실행 schema에서 manifest optimizer_updates, report/curriculum, entropy·EV 필드를 확인했다. loss는 마지막 minibatch, EV는 post-update valid decision 기준으로 구분한다. 보상 평균·advantage 표준편차로 항별 경사 기여율을 만들지 않는다.

## 후처리 감독과 원본 렌더

- 본 감독이 training_evaluation_complete에 도달하기 전에는 대기한다. 기존 감독 PID 부재·stopped_error는 후처리 중단 사유다. 동일 local lock을 획득한 다음 분석·원본 renderer·보고·공유를 순차 실행한다. 실행 중 도구·설계·봉인 pin을 동결해 검사한다.
- 자식 실행은 생성 직후 try/finally에 들어가고 signal·timeout에서 자기 process group을 종료·회수한다. 학습 실패를 본 실험 성공으로 바꾸지 않는다. 진행 중 본 학습 status를 후처리 대기 실패로 덮어쓰지 않는 분기도 확인했다.
- 렌더는 원래 argv에서 checkpoint만 선정 모델로 교체하고 full_song/N1/원래 출력 경로를 유지한다. checkpoint SHA, native report·정리·원본 source pins·policy 불변·두 인코딩 성공을 검사한다. 검사 키는 공식 renderer와 일치한다.
- hand/fullbody 두 시점을 조건당 저장하고6개 비디오만 동영상 폴더에 두도록 검사한다. 원본 metadata의 env0 첫 episode·프레임·모델 SHA를 보존한다. 조기 실패 영상도 원래 episode를 유지하며 좋은 장면으로 교체하지 않는다.
- ffprobe, 전체 ffmpeg decode와 중간 PNG 추출은 파일·디코딩 검사다. 사람의 영상 의미·화면 구성 검수를 대신하지 않으므로 최종 제출 전 생성된 프레임/실제 영상을 별도로 확인해야 한다. 현재 report 도구는 자동 decode를 시각 검수 완료라고 주장하지 않는다.
- 완료 후 분석·동영상·새 도구·검증·명령/로그를 공유하고 SHA를 대조한다. 로컬·공유 snapshot/design을 재검사하고 기존 검증 파일이 다르면 덮어쓰지 않는다. 렌더·전달·보고의 실패를 숨기고 complete로 진행하는 경로는 확인되지 않았다.

최종 H 추천은 seed7 단회 선별과 평가32환경의 한계를 명시하고, 추가 seed 재현 후보와 기본 코드 채택을 구분한다. 전체 유지·필요 해제가 없을 때 legacy/보상 차이만으로 더 긴 H를 채택하지 않는 설명도 적절하다. 실제 숫자·최종 결론·영상 품질은 앞으로 생성되는 원자료에 대해 후속 확인한다.
