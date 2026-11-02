# 실행 전 변경 검수

요약 판정: **수정 권장**. 현재 정상 경로에서 실행을 막는 Critical은 발견하지 않았다. GPU 실행은 하지 않았으며 새 도구만 읽고 CPU 검사를 수행했다.

## Critical

없음.

## Warning

- `tools/benchmark_envs.py:76`, `:88`: KL 실패를 조건 탈락으로 처리할 때 `lifecycle_verified`를 확인하지 않는다. 따라서 KL 오류와 함께 장면 종료·단일 GPU 환경 계약이 미검증된 보고서도 다음 조건으로 넘어갈 수 있다. OOM의 초기화 실패와 구분하고, KL 분기는 `lifecycle_verified is True` 및 `changed_inputs`, `missing_import_pins`, `cleanup_errors`가 명시적으로 빈 배열인지 확인한 뒤 건너뛰는 것을 권장한다.

## 확인한 정상 경로

- `tools/benchmark_envs.py:13`, `:37`: 총 524,288 전이와 warmup 65,536 전이 고정. 256/512/1024환경은 64/32/16회, warmup은 8/4/2회로 계산된다. H32 고정이며 기존 6→7 workload임을 결과에 명시한다.
- `tools/benchmark_envs.py:40`, `:43`, `:67`, `:99`: GPU 계산 프로세스 확인, 기존 연구 입력·소스 및 이 벤치 도구의 SHA 봉인, 실행 전후 비교가 있다. 새 6→8 도구 생성 영역은 기존 workload의 봉인 범위에 들어가지 않는다.
- `tools/benchmark_envs.py:17`, `:85`: 최초 에피소드를 환경 ID별 하나씩 집계하고 전체 환경 수가 채워져야 적격이다. 물리/손목 실패 환경의 합집합을 분자로 사용한다. 1024환경에서도 16×32=512 control ticks로 7.25초 음열의 최초 에피소드를 관측할 길이가 있다.
- `tools/benchmark_envs.py:77`: 실제 보고서의 `updates_in_run`, `transitions`, `min_cuda_free_bytes` 및 학습 원장의 시간·전이·진단 키와 연결됨을 확인했다. 적격 조건은 VRAM 1GiB, RAM 4GiB, 최초 에피소드 실패율 1% 이하이며 적격 중 초당 전이가 가장 높은 조건을 고른다.
- `tools/benchmark_envs.py:59`, `:62`: 조건당 30분 제한과 프로세스 그룹 TERM→KILL 정리가 있다. 예상 외 오류는 전체 실험을 중단한다.
- `tools/runtime.py`: 새 음열·A 초기 catalog와 물리 입력의 SHA를 별도 검증한다. 저장 설정과 현재 설정 비교 및 기존 checkpoint identity/pin 검증을 유지하며 원본 모델이나 metadata를 바꾸는 경로가 없다.
- `tools/reference_native.py`: 학습과 같은 A 초기 catalog를 `NaturalScene`에 전달한다. 중간 reset·상태 순간 이동·clock 대입 없이 기존 직접 위치 제어기와 네 번의 물리 substep을 통과한다. 실제 clock과 물리 step 수 일치, 소스 불변, 장면 정리, 유한 상태를 별도 검사한다.
- 참조의 AB 시간창은 3–4.5초와 5.25–6.75초다. 엄격한 `accepted`는 두 음 모두 실제 1.5초 관측·전체 clean·첫 clean 지연 한 240Hz tick 이내를 요구한다. 약한 90% 유지 지표인 `native_verified`와 구분해 후속 학습의 gate는 `accepted`를 사용해야 한다.
- 참조는 유한한 요청각 궤적의 물리적 수행 가능성 진단이며 학습 정책 성공을 증명하지 않는다. CPU endpoint 통과도 native 통과와 구분되어 있다.

## CPU 검증

`/home/ajou/miniconda3/envs/rl38/bin/python -m unittest discover -s docs/2026-11-02/압현실험/중지6에서8프렛_환경수비교_20261101/tools -p 'test_*.py' -v`

13개 모두 통과. runtime 계약 8개, 참조 5개이며 CPU geometry endpoint 4개의 후보 유효성도 검사한다. GPU 물리·메모리·처리량 결과는 이 검수에서 실행하거나 추정하지 않았다.

## 후속 확인

- 위 KL Warning은 root의 `clean_kl_failure` 추가로 해결됨을 확인했다. phase와 outer 오류 모두 KL인지, phase lifecycle이 참인지, phase 입력·import·cleanup 오류 배열이 명시적 빈 배열인지, outer 추가 오류가 없는지 검사한다.
- 별도 native 실제 실행에서 `planned_transitions=2`, `full_song_after=1`이 현행 고정 quarter 계약과 맞지 않아 환경 생성 실패가 발견되었다. 최초 CPU 테스트는 이 계약을 실제 환경 생성 전에 검사하지 못했다. 참조 worker가 4/1 계약으로 수정하고 회귀 검사를 추가할 예정이며, 수정 이후 검수 결과를 별도로 기록한다. 이 실패 결과를 native 물리 통과로 해석하거나 장기 학습 gate로 사용하면 안 된다.

## 최종 코드 재검수

최종 요약 판정: **문제없음**. 위 KL Warning과 참조 노출 계약 오류는 수정되었다. 실제 GPU 성공·속도 결과에 대한 판정은 별도이며 이 문서는 코드/CPU 검수다.

- 참조의 노출 계약을 4/1로 바꾸고 생산 `ExposureSchedule(4, 1)` 허용 및 `(2, 1)` 거부를 회귀 검사한다. 환경 생성 예외도 `completed=false`, `accepted=false` 보고서와 원래 예외·정리·소스 불변 정보를 보존한다.
- `tools/run_study.py`: 완료·적격 벤치와 소스 SHA, native의 엄격한 `accepted`·AB 전체 유지·onset·정리·유한·clock·동일 A catalog·후보 SHA를 선행 조건으로 검사한다. 실제 중지 3번줄 6/8 후보인지도 확인한다.
- 새 학습은 두 seed 모두 622,592 → 1,245,184 → 2,097,152 전이로 균형 있게 진행한다. 모든 예산 차이는 256/512/1024환경의 H32 batch로 나누어지며, resume의 seed/환경 수와 실제 committed 전이를 검증한다. smoke 2회·resume 1회·평가를 장기 학습 전에 실행한다.
- 선정은 중간 32환경으로 하고 최고/마지막을 각각 128환경 두 번 및 탐색 32환경으로 평가한다. 두 seed가 32환경과 별도 128환경의 성공/전체 유지/정시 기준을 모두 만족할 때만 예산 확장을 조기 중단한다. 영상은 실제 평균 정책을 사용하고 정책 불변·생명주기·MP4 유효 길이를 확인한다.
- `tools/analyze_results.py`: 최초 환경별 에피소드에 실패를 포함하고 두 음 원장·시간표·관측 schema·보상 성분 합계를 확인한다. 후보 중복은 경고 수치로 남기며 이를 근거로 분석을 중단하지 않는다. 발음 구간의 위치/방향/하중/오압현 순서별 거부 partition을 기록한다. 정시 전환은 이전 음 마지막 50ms와 B 첫 endpoint를 사용하며 이 제한을 결과에 명시한다.
- 공유 생산 코드와 과거 v2/v3 소스·모델을 변경하거나 checkpoint identity 검사를 우회하는 경로는 발견하지 않았다. 새 도구는 기존 supervisor의 프로세스/공간/봉인 검증 helper만 재사용하며 과거의 잘못된 동시 후보 분석 함수를 호출하지 않는다.

독립 재실행: **26개 CPU 검사 모두 통과**(runtime 8, 참조 6, 분석 4, runner 8). 추가로 벤치 KL helper의 허용/거부 8분기를 AST 추출하여 검사했고 모두 통과했다. 이 검수는 GPU를 실행하지 않았다.

## 자동 연결 launcher·그림 추가 검수

요약 판정: **문제없음**. `tools/launch_pipeline.py`와 `tools/analyze_results.py`의 새 그림/CLI 부분만 추가 검수했다.

- launcher는 기존 벤치의 완료를 기다리고, 실패/프로세스 소멸/5분 이상 진행 기록 정체에 중단한다. native는 별도 `reference_native_v2` 출력에서 실행하고 엄격한 `accepted=true`인 경우에만 이미 검수한 학습 supervisor를 실행한다. 기존 pipeline/로그/출력을 덮어쓰지 않는다.
- 신호 수신 시 현재 자식 프로세스 그룹에 TERM을 보내고 30초 뒤 KILL한다. 실제 학습 supervisor도 별도의 자식 정리 경로를 가진다.
- CPU mock으로 세 가지 흐름(벤치 정상+native 통과, 벤치 정상+native 실패, 벤치 실패)을 검사해 모두 통과했다. native 미통과일 때 학습이 호출되지 않고 pipeline 상태가 failed로 저장됨을 확인했다. 이 검사는 GPU를 사용하지 않았다.
- `plot_study`는 개발용 평균 정책 결과만 seed·누적 경험량별로 표시하고, 에피소드 수로 정규화한 AB/전체 유지/정시 전환과 보상 성분을 분리한다. 판정 함수는 변경하지 않는다. CPU 합성 자료로 성능/보상 PNG 두 개가 실제로 생성되고 비어 있지 않음을 확인했다.

## 장기 학습 전 영상 smoke 추가

`tools/run_study.py:179`의 추가 한 줄을 확인했다. smoke 학습 2회 → strict resume 1회 → 평균 32환경 평가 이후, 재개 checkpoint를 4환경에서 native render하고 기존 `validate_job`의 정책 불변·lifecycle·입력·정리 검증을 통과해야 장기 예산 loop에 진입한다. 영상은 `jobs/smoke_render`에만 저장하며 최종 결과 영상과 섞지 않는다. 이 수정 이후 전체 CPU 26개를 독립 재실행해 모두 통과했다. 추가 문제없음.

## 참조 안착 0.30초 독립 버전 검수

요약 판정: **문제없음**. 실패한 0.20초 안착 버전의 파일·봉인·출력은 유지한다.

- `reference_motion_settle030.py`와 원본 motion의 diff는 `SETTLE_S=.20 → .30` 한 줄이다. 휴지 0.75초 안에서 이동 시간이 0.55초에서 0.45초가 되어 B 요청각 도착이 4.95초로 당겨진다. A/B 실제 음 시간창, 목표각 endpoint, 최초 초기 상태, 물리/제어/성공 기준은 바뀌지 않는다. 이는 참조 요청 궤적 변경이며 성공 기준 완화나 새 정책 학습이 아니다.
- `reference_native_settle030.py`는 새 motion import와 새 motion 파일의 명시적 SHA pin만 추가한다. 기존 후보의 기하 SHA와 원래 source SHA도 계속 검사한다. `accepted`의 전체 clean 1.5초·정시 시작·정리·유한·clock 판정은 원본과 같다.
- `launch_pipeline_v2.py`의 원본 대비 변경은 pipeline 상태 파일, 로그 이름, native 출력 경로와 새 native 모듈 경로다. 기존 실패 출력과 충돌하지 않는다. 엄격한 native `accepted`가 거짓이면 새 학습을 차단하는 경로를 유지한다.
- 새 참조 CPU 7개를 독립 재실행해 모두 통과했다. 동일 발음 시간창·기하 endpoint 4개·연속 quintic 요청 속도 제한·4/1 생산 노출 계약·중간 reset/clock 대입 금지·새 motion pin·B 4.95초 도착을 확인했다. GPU 물리 통과는 이 코드 검수에서 주장하지 않는다.
