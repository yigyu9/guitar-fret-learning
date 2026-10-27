# 장기 학습 중단과 음악 학습 정체 분석

**실행은 중단됐다. 직접 예외는 worker0 응답 대기 시간 초과이며, 같은 시각의 호스트 RAM 부족이 가장 유력한 원인이다. 별개로 중단 전14업데이트에서도 음악 수행 개선은 확인되지 않았다.** 기존 실행·소스·설정을 수정하거나 새 학습을 시작하지 않았다.

대상: [원 실행 폴더](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_20261018_100545) · [실패 report](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_20261018_100545/report.json).

분석 권장본: [analysis_v2.json](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/analysis_v2.json). v1은 reset별 RSS 원자료의 사전 SHA가 누락된 제한을 보존했고 v2에서 해당352개 초기 기록을 읽기 전에 추가 봉인해 같은 집계를 재실행했다. native 재실행은 없다.

## 확정된 중단 경과

| 시각(KST,2026-10-18) | 기록 |
| --- | --- |
|10:05:45경|학습 실행 시작|
|10:25:26경|10번째 업데이트와 checkpoint_000009.pt 저장|
|10:32:59|14번째 업데이트 완료|
|10:34:34|커널 OOM-killer 첫 호출 기록|
|10:47:59|여러 Chrome 프로세스와 rg 프로세스의 OOM 종료 기록|
|10:48:01|worker0 IPC timeout으로 실패 report 저장|

직접 예외는 `TimeoutError: worker IPC timeout: 0`이다. 부모가 pool.step에서300초 응답 대기를 설정했으며, 시스템 메모리 부족과 일정 지연을 겪은 전체 벽시계 경과는 그보다 길었다. 현재 학습 부모 프로세스는 없다.

완료된 PPO 업데이트는14회/28672전이다. 압축 전이 로그에는 총30464전이가 있다. 차이1792전이는 **15번째 수집의112/128단계×16환경**이며 optimizer에 반영되지 않았다. 원 로그를 읽은336완료 에피소드 중320개는 완료 업데이트에,16개는 미완료 수집에 속한다.

report.completed=False이고 worker0 최종 감사가 없다. `stopped="updates_complete"`는 실패 때 갱신되지 않는 현 runner의 초기 라벨이므로 정상 완료의 근거로 사용하면 안 된다. failure와 completed를 우선해야 한다. 이 실행을 전체 감사 완료로 인증하지 않는다.

## 메모리 원인: 확인과 미확인

원 report의 관측 MemAvailable 최소는585998336bytes, 약**0.546GiB**였다. [커널 원기록](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/kernel_window.txt)에는 global OOM이 명시돼 있다. 마지막 task 표의 큰 프로세스는 다음과 같다.

| 프로세스 | PID | 해당 시각 RSS |
| --- | ---: | ---: |
|rg 검색 프로세스|3201193|약7.86GiB|
|MainThread라는 이름의 다른 프로세스|2897131|약4.09GiB|
|code|79977|약1.74GiB|

rg는 최종적으로 anon-rss8240456kB를 사용하다 OOM으로 종료됐다. 누가 어떤 명령으로 실행했는지는 이 기록만으로 알 수 없다. MainThread의 역할도 이름만으로 추정하지 않는다. task 표의 RSS는 페이지 단위로 보고되어 실제 시스템 page size4096bytes로 환산했고, 커널의 killed line은 kB 단위다.

학습 환경16개의 RSS peak 합도 약12.97GiB, 부모 peak는약1.29GiB였다. 이는 각 프로세스의 서로 다른 시점 최대값 합이고 공유 페이지를 중복 포함하므로 위 task 표의 동시 RSS와 직접 더한 정확한 전용 RAM 소비가 아니다. 다만16개 환경 외에 대용량 검색과 다른 작업이 함께 있었음은 확인된다. **16환경 자체만으로 메모리를 모두 소진했다거나, 학습 코드의 무한 누수가 입증됐다고 말할 수 없다.**

reset 직후 worker별 RSS high-water 평균은 첫679.3MiB에서22번째829.8MiB로 늘었다. 중간 약11개 reset은804.5MiB 부근에 머물렀다. 초기화/캐시/allocator 또는 누수 가능성을 분리할 현재 RSS·PSS 시계열은 없으므로 누수를 확정하거나 배제하지 않는다. 짧은4업데이트 시험으로8시간 자원 안전성을 검증하지 못한 한계가 이번에 드러났다.

해당 커널 kill 목록에 학습 부모/16worker의 PID는 없다. 따라서 “worker0이 OOM-killer에 직접 죽었다”는 설명은 근거가 없다. 다른15worker는 종료 감사에 failure=None을 남겼고 worker0은 감사가 없다. 메모리 압박으로 worker0이 제때 응답하지 못하고 부모의 timeout 정리에서 종료됐다는 해석이 가장 유력하지만, 정확히 어떤 native 호출에서 막혔는지는 stack/heartbeat 기록이 없어 미확정이다.

CUDA OOM 예외나 해당 커널 구간의 NVRM/Xid는 확인되지 않았다. Torch 할당 GPU peak는약279MiB지만 장치 전체 메모리와 같지 않으며, 이것만으로 모든 GPU 원인을 배제하는 것은 아니다. **확인된 자원 이상은 호스트 RAM OOM**이다.

## 중단 이전 학습은 무엇을 배웠나

아래 집계는 완료14업데이트에 해당하는28672전이/320완료 에피소드다.

| 지표 | 결과 |
| --- | ---: |
|50ms/100ms 타현 매칭|0/0|
|목표 음 후보 유지 누적|0초|
|60Hz 끝 표본 압현 후보|0|
|목표 미스|320|
|물리 실패 종료|0|
|기타 변위 최대|2.221mm,60Hz 끝 표본 기준|
|양발 접촉/주요 지지 부위 중 하나 이상 접촉|각100%,60Hz 끝 표본 기준|
|최대 analytic KL|0.013564,상한0.02|
|KL rollback 재시도|0|
|actor lr|3e-5 유지|

실패 판정과 음악 적분은 환경 안에서240Hz로 수행되지만, 전체 동작 원자료 저장은60Hz compact이므로 위 변위·접촉·후보 표본을 전체240Hz 정밀 최대/비율로 설명하지 않는다. 목표 유지0초는 음악 적분 결과이고, 준비 구간의 모든 짧은 접촉이 없었다고 주장하는 수치는 아니다. 전체 자유도·V3 자세 감사 완료도 뜻하지 않는다.

평균 episode reward는 약−0.485로 정체됐다. 첫값−0.484765와 마지막−0.484924의 차이는 음악 개선 근거가 아니다. 완료 수집 구간의 보상 성분은 미스−160,접근+4.7345,행동 변화−0.02344이며 타현·유지 보상은0이다. critic reward loss는0.0034025→0.00001307로 줄었지만, **거의 일정한 미스 반환값을 예측하는 개선과 연주 학습 성공을 구분해야 한다.**

저장된10업데이트 체크포인트의 모든 가중치는 유한하다. std평균0.0497907/최소0.0497308/최대0.0498383으로 초기0.049787에 가깝다. 분산 붕괴나 NaN 때문에 중단됐다는 증거는 없다. actor_grad_norm은 clip_grad_norm이 반환하는 **클리핑 이전 norm**이므로0.5를 넘는 로그만으로 gradient clipping 실패나 폭주라고 판단하지 않는다. [체크포인트 검사](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/checkpoint_analysis.json).

![완료 업데이트의 보상·비용·KL과 worker RSS high-water](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/training_diagnosis_v3.png)

오른쪽 아래 분홍색은15번째 미완료 수집이다. RSS는 high-water 합이며 시스템 전체 사용량 시계열이 아니다. global RAM은 최소값 하나만 있고, 그림에 알려지지 않은 시간 곡선을 만들지 않았다. v1의 주석이 초반 RSS 점을 가린 문제를 원본 보존 후 v2에서 위쪽으로 옮겼고, v3에서는 유지 지표를 target-contact candidate hold로 명시했다. 음향을 측정한 그래프가 아니다.

## 음악 정체에 관한 설계상 의심점

이는 가능한 원인과 다음 검증 항목이며, 이번 로그만으로 인과가 확정된 것은 아니다.

1. std약0.05와 기존 smoothing/rate limit의 탐색이 현재 복합 목표를 발견하지 못했다.16개 환경 모두 같은 첫 단음만 반복했고320에피소드에서 실제 음악 보상이0이다. 그렇다고 std를0.12로 한꺼번에 늘리는 것도 이전 시험에서 기타 편차/비용이 크게 늘어 좋은 해법으로 검증되지 않았다.
2. 현재 B목표의 왼손 접근 보상은 음악시간1.00~1.12초, 약120ms에만 적용된다. 손가락 distal body 원점과 명목 fret점의 거리로 계산하며 실제 접촉면 격차가 아니다.
3. 이 fretted 목표에서 approach 항은 왼손 거리만 사용한다. 관측에는 pick_delta도 있지만 오른손에는 연속적인 피크 접근/타현 궤적 보상 항이 없다. 오른손은 기하 통과·방향·시간·왼손 적합성이 결합된 음악 이벤트로 성공 보상을 얻어야 하므로 초기 발견이 어려울 수 있다.
4. 보상/목표/탐색 문제를 먼저 분리해야 한다. 현재 KL은 안정적이므로 이 로그만 보고 더 큰 망이나 무조건적인 학습률 감소를 처방할 근거는 없다. 현재 허용 행동 범위에서 지정 운지와 피크가 목표에 도달할 수 있는지도 별도 native 검증 대상이다.

## 복구 지점과 권장 순서

**복구 가능한 마지막 저장 모델은 [checkpoint_000009.pt](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_20261018_100545/checkpoint_000009.pt)의10업데이트 상태다.** 11~14번째 모델 가중치는 저장되지 않았고15번째 수집은 업데이트조차 되지 않았다. final.pt도 없다. 로그만으로14번째 모델을 복원할 수 없다. 이번 검사는 CPU 가중치 검사이며 native 재시작이나 엄격한 resume실행을 새로 한 것은 아니다.

1. 우선 대용량 검색과 학습의 동시 RAM 경쟁을 줄인다. 소스 검색은 필요한 코드 경로로 한정하고 거대한 결과 JSON/원자료를 재귀 검색 대상으로 포함하지 않는 것이 좋다. timeout만 늘리는 것은 OOM 해결이 아니다.
2. 재시작은 새 폴더·새 설정에서8환경으로 낮추는 보수적 운영을 권장한다. H256이면 기존 batch2048을 유지할 수 있지만8×256 장기 조합은 이번에 실제 검증한 설정이 아니다.16환경을 다시 쓰려면 다른 작업을 포함한 RAM 여유와 긴 실행을 다시 확인해야 한다. 모델/PPO 계약이 같은 checkpoint를 사용하고 물리 장면은 새 에피소드에서 시작한다.
3. 저메모리 감지·현재 RSS/PSS와 시스템 RAM 주기 로그·worker별 heartbeat·오류 종료 원인의 정확한 라벨·실패 시 마지막 유효 모델 저장을 먼저 보완하는 것이 좋다. 아직 구현하지 않았다. 마지막 저장 모델 유실을 줄이려면 저장 간격도 줄인다.
4. 장기 연주 학습 전 왼손 압현과 오른손 기하 타현을 각각 발견하는지 확인하고, 그 뒤 동시 목표로 연결하는 curriculum/접근 보상을 검토한다. 같은 음에서 성공 신호가 계속0이면 단순히8시간 더 돌렸다는 사실을 성과로 해석하지 않는다.

이전 N16추천은 단기 처리량과 짧은 자원 측정에 근거했다. 다른 작업과 공유하는 장기 RAM 여유를 보장한 설정으로 취급하기에는 근거가 부족했다. 이번 분석에서는 추천을 위와 같이 보수적으로 조정한다. 원 설정·원 실패·과거 검수는 변경하지 않았다.

분석 원자료·producer·SHA는 이 폴더에 보존했다. [독립 검수](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/review.md) · [최종 입력 보존 확인](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_long_B_16env_analysis_v1/final_verification.json).
