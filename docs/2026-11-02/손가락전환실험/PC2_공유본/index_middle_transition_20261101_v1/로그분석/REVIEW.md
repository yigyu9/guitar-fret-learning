# 원시 로그 분석 독립 검수

범위: 봉인된 기존 `도구/analyze.py`, 현재 GPU 접촉·원장·보상·기록 코드와 새 `로그분석/tools/observe_evaluate.py`, `repeat.py`. 출력은 이 `로그분석/` 안에만 작성했다. 공유 코드, 봉인 소스·모델·원시 로그, 기존 status/results는 수정하지 않았다. GPU·물리·학습을 실행하지 않았다.

## 동시 후보 assert의 정확한 의미

기존 `도구/analyze.py:21–23`은 에피소드의 모든 240Hz 끝점에서 `all(all_env_candidate)`를 세어 하나라도 있으면 중단한다. audible 마스크는 없다. 이 필드는 `gpu/environment.py:660–667`의 `positive & ~wrong`이므로 **이미 오압현이 제외된 effective 기하 후보**다. `all_env_raw_candidate`는 같은 함수에서 `pad['positive']`로 저장한 담당 loaded distal 패드 원시 positive다. 두 필드를 반대로 읽었던 이전 검수 지적은 여전히 철회 상태다.

그러나 effective 기하 후보와 해당 시각의 audible clean은 다르다. `environment.py:1047–1056`의 실제 clean 적분은 앞/뒤 끝점의 candidate가 모두 참이고, `[before, now]`가 해당 음의 onset..end와 겹칠 때만 증가한다. 같은 함수의 wrong 적분도 audible overlap과 앞/뒤 wrong 평균을 사용한다. 준비·휴지·말미의 기하 후보 자체는 그 음에 clean 수행이나 오압현 비용을 지급하지 않는다.

따라서 기존 assert는 **모든 시각의 counterfactual 기하 배타성**이라는 더 강한 검사다. 음이 없는 시간의 두 후보만으로 실제 동시 발음 달성·보상 모순이나 물리 실패를 확정하는 것은 과도하다. 반대로 이를 무조건 정상이라고 버려도 안 된다. 높은 프렛 간섭 측정이 포착되지 않은 원인, 표본·좌표·셀 판정 불일치 등을 조사할 측정 경고로 보존해야 한다. 현재 기존 결과를 무효화하는 실제 원시 로그 사례를 이 독립 검수에서 발견했다고 주장하지 않는다.

이번 A3..4.5초/B5.25..6.75초는 시간창이 겹치지 않는다. `all(candidate & audible)`는 정의상 항상 거짓이므로, 그 값이 0이라는 사실만으로 높은 프렛 veto가 정상이라고 입증할 수 없다. 새 분석에서는 아래를 구분하는 것이 적절하다.

- 두 raw positive, 두 effective 후보: 준비/A/휴지/B/말미별 endpoint 수와 첫 시각.
- 두 audible effective 후보: 정의와 개수는 기록하되 이 AB 일정에서는 검사력이 없음을 명시.
- 낮은 A가 audible일 때 높은 B의 raw positive와 A의 effective가 동시에 참인 끝점: 놓친 간섭의 **의심 사례**로 별도 보존.
- 실제 원장 clean·wrong·달성 및 지급 보상: 끝점만의 계수와 구간 적분을 구분.

기존 assert·기존 metrics·채택 문턱은 수정하지 않는다. 새 원시 평가가 native/strict load/lifecycle까지 완료했는데 기존 분석 assert가 실패하면, 실행 완료와 분석 실패를 따로 기록하고 해당 raw 자료를 보존한다.

## 높은 프렛 veto와 낮은 부수 접촉

`gpu/contact.py:883–894, 922–983` 및 `tests/test_simplified_wrong_press.py`를 대조했다.

- 담당 손가락의 같은 줄 높은 distal 패드는 낮은 목표를 차단한다. 목표 positive·동시 허가·다음 준비 여부도 면제가 아니다.
- 다른 손가락은 loaded 전체 thumb/finger2/3 표면의 virtual-string 표본에서 목표 줄의 더 높은 프렛이 확인될 때 차단한다. 같은/낮은 프렛은 차단하지 않는다.
- 담당 목표 positive가 있으면 낮은 프렛·다른 줄의 일부 부수 자기 표본보다 positive를 우선한다. 이 판정은 모든 비목표 줄의 무압현 인증이 아니다.
- 높은 프렛 witness의 raw 기하는 scope 안에서 계산되며 audible 밖에서도 존재할 수 있다. 비용·원장 시간의 적분은 별도로 audible에 제한된다. 준비가 간섭 면제라는 해석은 틀리다.

다른 손가락 higher의 전체 표면 표본은 고정 방향의 유한 mesh 표본이고, positive는 별도의 128개 distal 패드 표본이다(`environment.py:33–38, 584–667`). 두 표현의 witness는 코드상 자동 동치가 아니다. 실제 물리 접촉 상대나 현 압력을 측정한 것도 아니다. 그래서 all-time effective exclusivity가 모든 입력에서 논리적으로 보장된다고 가정하면 안 된다.

CPU Boolean 입력 수준 예시를 `reviewer_logical_example.json`에 새로 기록했다. raw A/B positive가 모두 참이어도 다른 손가락 full-surface higher witness가 없으면 두 effective가 남고, witness를 추가하면 낮은 A만 차단된다. 시간만 준비/A/휴지/B/말미로 바꿔도 이 raw 기하 차단은 그대로다. **이 예시는 native 도달 가능 자세나 실제 기하 반례를 재구성한 것이 아니며, 해당 입력 플래그 사이의 논리적 보장 범위만 확인한다.**

## 기존 로그로 알 수 있는 것과 없는 것

|자료|실제로 남는 정보|복원할 수 없는 정보|
|---|---|---|
|240Hz finger trace|env0 관절 요청/적용/실제각·속도·제출 effort·native generalized sensor, 모든 환경의 episode ID/시계와 후보·wrong·기하·하중 bool 등 연구 추가 필드|모든 환경의 전체 q105/body pose, 모든 원시 contact witness, 시각별 body×cause wrong_source_flags, 특정 접촉 쌍·현 압력|
|완료 episode 원장|음별 clean/wrong/missing, streak, 달성, body×cause의 audible 적분 `wrong_source_time`, source fret 최소/최대, episode 보상 9항 합계|일반적인 경우 누적 source 시간을 어느 시각·표본에서 발생했는지 유일하게 역산하는 것|
|학습 transitions/decisions 저널|60Hz total reward/cost·종료·episode 연결, K1 decision 시각 및 할인 reward/cost|각 60Hz 보상의 9항 분해, 당시 observation/latent/value와 실제 rollout 경사|
|학습 metrics|H32 update의 항별 평균·총량과 PPO/advantage 진단|episode 시계별 항 지급, 항별 경사 기여율|
|기존 평가|완료 episode 합계와 위 trace|별도 보존하지 않은 모든 60Hz reward/9항 배열|

`environment.py:1174–1195`의 source 적분은 audible overlap에 앞/뒤 flags의 평균을 곱한다. body/cause 시간은 겹칠 수 있어 합산하면 실제 wrong 시간이나 패널티가 중복될 수 있다. source fret min/max는 episode 범위이며 특정 시각의 단일 witness가 아니다. `FingerSkillEnvironment._episode()`는 현행 cause 이름으로 바꾸지만 시간 정보를 추가하지 않는다.

후속 반복이 기존 runtime 그대로라면 raw source의 240Hz 시각별 행이 새로 생기지는 않는다. 새 observer가 추가하는 것은 다음 절의 60Hz 항별 지급이다. source 시각을 꼭 확인하려면 별도 읽기 전용 관찰 계약과 SHA 아래 current wrong_source_flags/fret 범위 및 초기 끝점을 기록해야 하며, 이번에 없는 정보를 누적 원장에서 만든 값처럼 표현하지 않는다.

## 새 60Hz 보상 관찰 검수

`observe_evaluate.py` 수정본에서 다음을 확인했다.

- 원본 runtime을 runpy로 실행하고 strict loader/identity/입력 검사·정책/물리 반환을 바꾸지 않는다.
- `FingerSkillEnvironment._reward_components`의 원본 반환 텐서를 clone해서 exact 지급 항을 보존하고 원본 dict를 그대로 반환한다. `end_control`의 원본 반환도 그대로 반환한다.
- `reward_terms`, `returned_reward`, 누적 float32 counter의 `counter_delta`, cost·종료·episode ID·끝 시각을 분리한다. counter 차이는 반올림 때문에 지급 term 그 자체와 다를 수 있다.
- 임시 관찰 attribute를 삭제하고 finally에서 원본 method와 stream을 정리한다. gzip은 `xt`로 새 파일만 만들므로 이전 실패 trace도 덮어쓰지 않는다.
- CPU 패리티 로그는 출력 텐서·RNG·counter 동일성 검사 1개가 0.664초에 통과했다고 기록한다. 독립 검수에서는 수정 코드와 그 로그를 읽었고 해당 검사를 다시 실행하지 않았다.

기존 보상은 모두 240Hz 항이 아니다. `environment.py:1238–1315`와 `finger_skill_environment.py:475–522`에 따라 접근 potential·terminal 정산·수행 부족·실패 cost·행동 변화 등은 60Hz 경계에서 결정된다. 새 exact 60Hz 행을 4개 physics 끝점에 균등 배분하면 안 된다. 사전 지급/정산과 실패 tick 양성 억제도 유지한다. episode ID·시계로 각 첫 episode를 고르고, 다른 환경을 기다리는 동안 먼저 끝난 환경의 후속 episode를 섞지 않는다.

추가 clone/cpu 기록은 RNG를 사용하지 않지만 GPU 동기화와 실행 시간에 영향을 줄 수 있다. 기존 무관찰 평가와 bit 동일한 물리 궤적을 보장하는 검사가 아니며, 결과 반복 변동의 단독 원인을 정하는 실험으로 확대하지 않는다.

## 반복 평가 실행기

`repeat.py`는 기존 study lock, SIGINT/SIGTERM 예외 전환, 현재 GPU compute 비점유 검사, 소스·모델·관찰 도구 SHA, 순차 32/128 각 3회, timeout과 자식 process group 정리를 사용한다. 새 출력은 `로그분석/runs`, `logs`, 자체 status에만 둔다. 기존 D/status/results를 호출하거나 바꾸지 않는다. 확인한 범위에서 시작을 막는 추가 필수 오류는 발견하지 못했다.

견고성 권고는 새 status의 예외 시 stopped_error 기록과 killpg 경합 시 ProcessLookupError에도 wait 보장이다. 이 권고는 기존 연구 결과나 성공 기준 변경을 요구하지 않는다.
