# 자원 활용 장기 학습 시작·초기 경과 최종 검수

- 요약 판정: **문제없음**.
- 검수 상태: **completed=true**. 장기 실행 자체는 진행 중이며 종료 검수가 아니다.
- 범위: 실행기, 자원 비교, 장기 설정·재개·봉인, [README.md](README.md), [초기 보고서](early_status_v1.md)와 [JSON](early_status_v1.json).
- 초기 수치 기준: `2026-10-18T15:54:03.256325+00:00`의 snapshot. 이후 증가하는 실시간 로그와 구분한다.

## Critical / Warning / Suggestion

남은 차단 문제와 필수 수정 사항은 없다. 추가 구현 권고도 없다.

보존한 [review_v1.md](review_v1.md)의 H120 pilot 범위 제한은 README에 반영됐다. pilot의 첫 준비2초 관측을 장기 처리량·음악 성공으로 확대하지 않는다. 실제 장기 로그에서 업데이트를 넘는 전체7초 episode와 reset을 확인해 사전 검수의 미확인 항목을 해소했다.

## 설정·실행기·재개

- [long_plan_v1.json](long_plan_v1.json)과 손별 설정은 N16씩 총32 worker, H120, 손별 최대256 update·7200초 soft 제한, `cuda:0`·medium·상태563/행동39, 메모리 여유6GiB 보호선을 유지한다. 손별491,520·합계983,040 최대 전이 산식이 맞으며 이 상한을2시간 내 달성한다고 주장하지 않는다.
- [run_pair_v1.py](run_pair_v1.py)는 파일로 stdout/stderr를 기록하고 새 session의 trainer를 시작한다. 중단 시 직접 생성한 자식만 SIGINT로 정리를 요청한다. trainer의 기존 worker timeout·메모리 보호·종료 자원 정리 경로를 사용하며 다른 프로세스를 종료하지 않는다. supervisor `completed`와 trainer 성공·음악 성공을 구분한다.
- 실제 재개 모델은 dual16 pilot final **LH update4 / RH update2**다. CPU로 원 checkpoint와 장기 `initial.pt`를 재귀 비교했다. metadata만 다르고 모델·Adam·RNG·identity·counter는 정확히 같다. 공통 pilot 출발 LH3/RH1과 혼동하지 않는다.
- 실제 actor LR은 LH `1.5625e-7`, RH `6.25e-7`로 이전 KL 보호 이력을 이어받았다. 선언된 PPOConfig LR로 재초기화하지 않았으며 README가 이 차이를 명시한다.
- 현행 [source pin](source_pins_v1.json) **169파일**, [장기 실행 pin](long_execution_pins_v1.json) **6파일**의 SHA를 재검사해 변경0개를 확인했다. 생산 코드·기존 결과·원 모델은 수정하지 않았다.

## 선택 근거 독립 대조

- [pilot_comparison_v1.json](pilot_comparison_v1.json)을 원 report와 supervisor 자료에 대조했다. 동시 실행은 합산 전이 / supervisor wall을 사용한다. dual8은 **1920 / 65.759918초 = 29.197117전이/s**, dual16은 **3840 / 104.267517초 = 36.828344전이/s**다. 약26.1% 차이와 단독 trainer wall의 계측 범위를 문서에서 구분했다.
- dual16의 host 원자료 전체를 재집계해 첫 표본 제외 CPU 평균 **80.610135%**, GPU 메모리 최대 **7035MiB**, host 최소 여유 **14.456669GiB**가 일치함을 확인했다. trainer 최소 **13.934986GiB**는 별도 표본이다. GPU busy나 host 점유를 학습 전용 사용률로 확대하지 않는다.
- 비교한 구성 중 가장 높은 짧은 실측 처리량과 메모리 여유를 선택한 근거는 타당하다. 미측정 환경 수 전체에서의 최적성이나 장기 성능 개선을 입증한 것으로 해석하지 않는다.

## 초기 실행 원자료 대조

- 양손 각각 **4 update / 7680전이**가 commit됐다. 해당 snapshot의 sampled=logged=durable=committed=7680, discarded=0이다. `early_status` journal은 실제 네 번째 learning record와 같고, 선택한 누계·분모·group·open episode 항목도 일치한다.
- 실제 네 번째 learning record의 optimizer counter는 **LH8 / RH6**으로 재개4/2에 각각4회가 추가됐다.
- 양손 각각16개 episode가 **420tick / 7초 / 1680물리 step**, `timeline_complete`로 끝났다. 물리 실패0개다. 다음 episode는 모든 worker에서60tick·1초까지 이어졌다.
- `train_parallel.py:224`의 Collector는 실행 중 한 번 생성된다. `parallel.py:369`는 관측이 없을 때만 초기 reset하고 `parallel.py:402`는 done worker만 reset한다. 실제 episode0가 네 번째 update에서 끝난 기록과 다음 episode1이 이를 뒷받침한다. H120마다 준비 자세로 되돌리지 않는다.
- 실제16개 완료 episode를 각각 재집계했다. LH timing-only16/16·품질0/16, clean audible 평균1.0·해제완료0·late2.5478초다. RH timing-only15/16·품질0/16, accepted15·extra15·unprepared0·wrong-native-eligible15·최종 recovery15가 일치한다. extra와 wrong을 합산 실패 횟수로 만들지 않았다.
- 초기 host snapshot까지의 원자료76개 표본에서 최소 여유 **13.618431GiB**, GPU 메모리 최대 **7603MiB**를 재계산해 보고서와 일치했다. 현재 보호선 이상의 여유이며 향후 자원 추이는 계속 기록된다.

README와 초기 보고서는 실행 시작·전체 구간 연결 확인을2시간 완료나 정책 개선·결정적 평가·양손 결합 성공으로 표현하지 않는다. 종료 후 전체 report/accounting·checkpoint와 품질 추이에 대한 검수는 별도 범위다. 검수자는 이 신규 보고서만 작성했고 사전 보고서를 보존했으며 추가 실험·학습을 실행하지 않았다.
