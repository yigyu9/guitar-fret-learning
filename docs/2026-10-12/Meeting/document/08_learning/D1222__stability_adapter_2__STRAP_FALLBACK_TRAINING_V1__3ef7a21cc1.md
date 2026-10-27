# 이탈 대응: 스트랩 비교와 안전실패 재설정

2026-10-12 사용자: 기타이탈이많으면스트랩추가버전도고려한다. 최초평가위치이탈84.6–84.7%/최장12.8초이며조건이충족됐다. 무스트랩long_run_v3는관절상태안전검사로중단됐고,기존입력SHA불변/체크포인트/영상을보존한다. 기존소스는수정하지않는다.

## 새 소단계

1. [x] 저장native이탈분석과원본스트랩길이검토: docs/results/strap_fallback_assessment_v1. 고정rest length1.1018469719600776m,6000N/m,120N·s/m,cap300N,13route 인장전용법칙을그대로사용한다.
2. [ ] 새native버전에서스트랩ON/OFF·관절안전실패수치/관절명 기록을구현한다. actor-root·하체고정·81owner·원래초기값·PD·2초준비·fullsong조건은같다. 길이를줄이지않고live초기body매핑/route/slack을검증한다.
3. [ ] 순수힘합/작용반작용/forceguard/관측/안전종료비용반례와새warm-start정책입력확장일치검사,독립검수.
4. [ ] 같은warm-start정책으로두조건평가영상을먼저만들고이탈·회전·장력·음악·안전실패를비교한다. 통과후별도조건학습을실행하고30분CP/전체영상/11:40cutoff를유지한다.

## 제어·학습 계약

스트랩의양끝과humanoid guide에동일route법칙의작용/반작용만적용한다. 기타를목표p/q로당기는별도힘은없다. 기존힘금지guard는새scene에서해당strap계산·적분구간에한해정확한인자검사로허용하고다른외력/상태쓰기/PD쓰기금지는유지한다. 현재route길이·rest length·길이변화율·계산장력·ON/OFF를추가한825관측으로두조건을구분한다. 기하·장력은실제worldpoint/COM보정속도로계산한다. 장력은force sensor측정으로부르지않는다.

이미저장된820checkpoint는원문ABI digest/이전소스SHA/모델형상/입력앞820계약을검증해warm start만허용한다. Actor/Critic 첫입력층에5개의0열을추가하고RMS추가차원은mean0/var1로둬기존출력의수치동등성을검사한다. 분포와기존가중치는상속하고새Adam/새ABI/새physicalepisode로시작한다. 원문ABI를무시한exactresume로설명하지않는다.

현재한번의유한관절속도실패가전체훈련을끝내는문제를시험보상v2에서구분한다. 비유한측정/API/금지호출은계속실행오류다. 유한qdot안전초과는실제physicalepisode의early termination으로기록·영상종료·reset한다. 물리끝난뒤가짜프레임을붙이지않는다. 정상보상은control당하한−2로제한하고조정량을ledger에명시한다. 안전실패는현재하한과남은horizon의할인된하한합에추가−1을부과해조기종료로음수보상을피하는이득을막는다. gamma는60Hz/10초half-life와동일하다. 모든스칼라보상에0.1을적용하고raw·scaled값을구분한다. 이것은명시적pilot보상변경이며정식v4/v5전체계약인증이아니다.

## 결과 경로·보존

`/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/strap_fallback_training_v1/`

기존deadline phase/무스트랩run/파일을그대로보존한다. 새로운파일과새결과경로만사용한다. native가읽는동안A/main4를수정하지않는다. 학습실패원인의정확한q/qdot수치가이전로그에없다는한계를남기고새버전에서반드시기록한다.
