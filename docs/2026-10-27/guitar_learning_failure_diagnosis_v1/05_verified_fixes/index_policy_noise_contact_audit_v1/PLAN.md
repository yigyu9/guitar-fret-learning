# 고정 마지막 모델의 잡음·오압현 출처 진단

이전 단계는 V7 실제PPO300·7평가·903SHA 분석검수·714SHA 영상검수를 완료한 진전이다. 기본 채택은 하지 않았다. 이 계획은 기존에 승인된 원인 진단과 필요한 추가 작업의 후속이며, 학습 예산을 늘리거나 원 수용기준을 낮추지 않는다.

## 목적과 고정 조건

마지막 V7 평균행동은 세음13/128·달성+첫음해제5/128, 확률행동은58/30이다. 평균행동의 뒤두음 오압현 비율각약.74219와 확률행동 약.0234의 차이를 실제 v2 출처로 설명하고, 동일 물리 초기 조건에서 잡음 표본만 달리했을 때 재현되는지 검사한다. 이 결과만으로 일반적인 원인이나 실제 줄압력/음향을 확정하지 않는다.

- V7 마지막300 checkpoint와 원settings/architecture/엄격load를 그대로 사용한다. 새 fit/PPO/optimizer update는0, 보상9개·물리·접촉 문턱·목표·지원 제어는 불변이다.
- 원 평가 루프를 그대로 재사용한다. 각 실행은 원128환경의 첫3음[4,7,8]/354tick이며 실패도 분모에 남긴다. 기타 고정·검지4축·원초기화seed7 범위다.
- 미리 정한4조건: 원평균행동, 별도 정책잡음seed7/17/27. 잡음seed는 물리/reset seed 또는 새 학습seed와 구분한다. 실행당1개 private RNG를 유지하고 tick/H32/reset마다 재seed하지 않는다.
- 원bound act를 private device RNG scope에서 호출해 원Normal.sample과[128,4] 추출을 보존한다. 전체33/39축 추출 후 자르지 않는다. 첫seed7 state가 원post-load seed7 state와 같아야 한다. scope 종료/예외 때 global RNG/factory/step wrapper를 복원한다. 진행된 global RNG 최종값 자체가 원stochastic 수행과 같다고 주장하지 않는다.

## 최소 수집

원GoalPool.step를 한 번 호출해 반환값 그대로 돌려주는 observer로 compact 전 raw128 첫시도 음 원장을 보존한다. first mask는 원step 전에 복제한다. 원래10몸체·3원인(other_higher/own_wrong_fret/own_wrong_string)·240Hz 누적 source time·출처프렛 범위를 저장한다. 이미 있는 env0 제어trace를 재사용하고557상태/event/GAE/critic/전체환경105축 로그는 추가하지 않는다.

필요한 경우60Hz의 실제시계/원인 endpoint·프렛범위·원누적 source time만 추가한다. endpoint와240Hz 누적 적분을 구분하며 정확한 substep 발생시각을 복원했다고 하지 않는다. 원act 반환의4축 mean/log_std/latent/action은 추가forward/추가난수 없이 보존해 실제 물리 목표 변화와 비교한다.

## 진행과 검증

1. 신규얇은wrapper·CPUfixture를 구현한다. 임시hook 원복·원step1회·firstmask/reset 경계·고정잡음연속성·원boundNormal.sample·미수용입력/부분실패보존을 검증한다. 생산281Python·V7/A 봉인원문은 수정하지 않는다.
2. 비구현자의 독립 준비검수 뒤 입력/코드를 봉인한다. gate는 수치/native import 전에 확인한다.
3. 먼저 평균행동/seed7 두 GPU 수행을 하나씩 실행한다. V7 원평가의 전체128음원장·9보상, env0 관절/목표/몸체/후보/NNgoal이 같아야 한다. 힘 미세차이는 별도 보고한다. 재현 실패 시17/27 수행 전에 중단하고 원인을 고친 새 버전으로 재검증한다.
4. 통과하면 잡음17/27을 같은조건으로 실행한다. 모델·optimizer·원checkpoint·입력불변·장면종료와 실제 종료코드를 검사한다.
5. 원128/384 분모로 all3/joint/음별clean·wrong·missing·v2원인·출처프렛을 비교한다. 원인별 시간은 겹칠 수 있어 합산 감점으로 해석하지 않는다. 평균/확률 차이의 반복성과 표본에 민감한 gate를 구분하고 필요한 제어/보상 수정 하나를 좁힌다. 분석·그림·해석을 독립 검수한다.

## 원범위의 병행 확인

현재 계약에서 네 손가락의 사전선정 목표와 scripted positive/negative 근거를 대조하고, loaded-facing negative·자유조건 엄지해제/학습과부하의 미완료 부분을 별도 분기로 준비한다. 검지3음만으로 원목표를 대체하지 않는다. 다른손가락/학습seed·자유기타J33·원67음 평가와 최종영상·보상문서 요구는 그대로 남는다.

체크리스트는 실행 전 봉인 원문으로 보존하며 실제 완료는 상위README/status와 별도RESULTS에서 갱신한다.
