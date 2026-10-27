# 병렬 환경 수와 장기 학습 설정 선정

사용자는 장기 학습을 위해 여러 환경 수를 실제 시도하고 적절한 파라미터를 정해 달라고 요청했다. 기본 학습은 자유 기타·Root 고정/하체 유한·105/97/8·준비2초·현재 음악/보상/종료를 유지한다. 기존 검증의 왼팔/복합 큰 행동 실패와 음악 성공0을 숨기지 않는다. 설정 시험을 통해 실제 장기 실행용 파일과 실행법을 제공하되 시험 결과를 수렴한 연주로 설명하지 않는다.

- [x] 기존 소스/문서/검사를 archive에 보존하고 장비를 기록한다.
- [x] 원 모델/제어를 유지하는 카메라 비활성 세션과 spawn 독립 환경 pool·batched policy collector를 구현한다. terminal/truncation/bootstrap/부분reset/오류중단을 검사한다.
- [x] headless/thread1 경로를 기존 실제 준비 상태와 비교하고 native 사전 검수한다.
- [x] N=1/2/4/8에서 같은 물리·망·역할 범위·PPO 기본 설정/seed 계열로 128control ticks를 수집하고 초기화/수집(재준비 포함)/학습 wall time·RSS·GPU memory·음악/안전 지표를 측정한다. N8이N4대비30%이상빨라지고MemAvailable8GiB이상이면16도시도한다. 자원부족/worker오류는보존하고중단하며다음독립설정으로진행한다.
- [x] 가장 빠른 유효 처리량의90%이내인 최소 환경 수를 우선 선택하고 상위 두 개를 반복 확인한다. 단일seed/짧은성능시험으로학습최적성을주장하지않는다.
- [x] 선택한 환경 수에서 동일총batch2048(N16×H128)/일정horizon,medium망,초기탐색std와actor lr의소수후보를4update씩실제비교한다. 모델/보상/안전임계값은바꾸지않는다. KL/반환값/비용/압현/타현/접근/실패/최종행동을기록하고가능하면GPU/CPU update시간을대조한다.
- [x] 최종 환경 수·horizon·batch·minibatch·epochs·lr·gamma·GAE·KL·exploration·보존주기·목표전이/시간한도 설정파일을저장한다. 실제측정처리량으로장기학습시간을추정하고독립검수/입력봉인/문서를완료한다.

장비: i9-13900/32 logical CPU/RAM31GiB(시작MemAvailable약19GiB,swap2GiB사용중)/RTX4070Ti12,282MiB(시작20MiB)/디스크잔여24GiB. 기존Scene은CPUPhysX 및 env1 Jacobian/질량행렬/원접촉query를사용한다. 이번구현은독립CPU simulator N개와중앙batched정책이며GPU수천환경벡터화구현으로부르지않는다. CPU물리thread1은원thread값도기록하고초기화/물리비교로변화를공개한다. 원코드와사후원자료는수정하지않는다.

소유권: worker1 headless_session.py/해당검사,worker2 parallel.py/해당검사,root runner·선정기준·실행·문서·최종봉인,독립change-reviewer 사전/사후검수. 결과: docs/2026-10-12/stability_adapter_2/results/guitar_learning_parallel_tuning_v1. 새파일이외기존runtime은보존한다. 장기예산은우선설정파일로구체화하며무기한학습을시작하지않는다.

진행 기록: N1/2/4/8/16의 첫 CPU 시험이 모두 완료됐다. 수집 TPS는 각각3.8493/6.7212/11.7052/17.6976/21.6978 근처이며 정확한 값은 report.json을 따른다. N8/N16 반복을 수행한다. 초기화와 각 control tick 뒤에 관측한 MemAvailable 최저만 기록하며 준비 중 순간 최저 보장은 아니다. GPU optimizer 비교 후 CUDA를 채택한다면 수집 마지막 비동기 tail을 동기화하는 runner 개정을 이전본 보존 후 적용한다. 후보는 동일 H128/선택N/4updates에서 std=exp(-3),actor_lr=3e-5; std=.12,actor_lr=3e-5; std=.12,actor_lr=1e-4의 세 구성이다. 과학적 수렴 비교가 아닌 장기 시작 설정의 제한 시험이다.

최종 시험 예산: 반복 평균 수집TPS N8=17.8478332, N16=21.9705 근처로16선택(정확값은원자료). optimizer warm CPU8.2012818s/CUDA0.2075239s로GPU선택. 초기화를포함한전체GPU학습은pilot에서확인한다. H64는1.0667초로B첫onset1.12초전에서수집구간을나누므로H128을유지한다. 실제batch2048, 후보당8192전이,세후보총24576전이다. batch약1024의초기예상보다늘었으나후보간동일하며첫사건의접근·타현·종료를포함하는horizon을우선한다. 104CPU재검사통과. GPU timing수정전파일을추가archive후새source_run_v2봉인으로진행한다.

중간 결과: baseline8192전이/80완료episode, 실패0, matched50/100=0, held0, 평균cost0.00273559, 수집19.98945TPS. explore8192전이/80완료episode, 실패0, matched50/100=0, held0.0291667s(현압력아닌접촉후보유지), 평균cost0.396874, 수집20.02210TPS. 기타변위 compact60Hz최대baseline2.22077mm, explore46.41372mm. faster는수행중이다. 최종선정은음악매칭/비용/가시적편차를함께보며, 매칭0이면성능최적값이라고부르지않는다.

후보3개4회씩총24576전이완료. 세후보타현매칭0, 실패종료0. 확대std는짧은후보접촉만얻고비용/기타편차가증가하여baseline(stdexp(-3),actor3e-5)을장기시작값으로선택한다. long_B_16env_v1.json: N16,H128,batch2048,GPU,256추가updates상한524288전이,8hsoft,10회체크포인트. 실제pilot전체wall로환산약8.09h이며시간예산으로256미만에서끝날수있다. longrun자체는시작하지않았다.

최종 완료: 독립 change-reviewer 문제없음, root 입력 감사1580경로/실제XML+mesh106파일/보관 및snapshot151SHA 통과. 총10native/31616전이/295완료episode/실패0, 준비398회, 측정126464물리표본과준비191040step은환경합산1322.9333초다. fullraw저장은398ticks/1592표본이며나머지는60Hzcompact다. 현행소스·설정·문서와입력변종(runner v1/v2)·출력inventory를최종보존했다. 음악수렴과8h자원거동은미검증이며장기run은실행하지않았다.
