# 부록

논문 제목: **From Audio to Full-Body Guitar Performance with a Freely Moving Instrument**

## A. 용어와 범위

| 용어 | 현재의미 |
|---|---|
| 전신장면 |휴머노이드전체와신체·의자·바닥·기타의물리상호작용.105축전체정책학습과다름|
| Root 고정/하체 유한 제어 |전체기준위치·방향은고정하고하체는잠금없이유한한관절제어로유지|
| clean압현 |원목표접촉후보에확인된높은프렛/오프렛/배정오류를반영한유효후보|
| 기하타현 |이전·현재피크선분의유한현영역통과. 실제 현진동/음향아님|
| Actor/Critic |관측→관절명령을만드는신경망/미래보상·안정성비용을평가하는신경망|
| 협응/공동 성공 |타현시의올바른압현결합/양손전체품질과안전을포함한완료조건|
| strict resume |동일 계약의모델·optimizer·RNG·카운터복원.새계약의특징 초기화와다름|

## B. 관절과 관측 계약

| 경로 | 상태 | Actor입력 | 행동 | 조건 |
|---|---:|---:|---:|---|
| 손별품질 |563|563|39중해당손|단음·손별이력|
| 단음 joint |1132|각569|33+6|두563+공동6,중앙reward/cost Critic|
| 전곡 song |500|각500|33+6|기본468+곡 이력32,새 음악/이력40열|

105입력채널·97비영 범위·8원 영범위는모델/제어계약이다. 현재정책행동39와혼동하지않는다. 하체유지목표가일정해도관절은유한구동을받는다. 물리 240Hz/정책 60Hz를사용한다.

## C. 시간·입력·재현

학습기준은기존035설정·v14준비상태이며native정착wait0이다. 단음 joint는정책7초/420tick,목표 시각4.12초다. 전곡은원 오디오시계에정책 준비3초를더하며첫 음시각3.6385초,원음 67개·정본 66이벤트다. 마지막end는30.0048초이며audio끝과tail을포함해32.8166667초/1969tick으로종료한다. 단음과전곡의시각원점을그대로섞지않는다.

42번묶음의두공격은원onset으로펼쳐각각down을상속한다. 두공격이23.3ms간격이라는점과두번째방향이원자료의개별표기가아니라는점을보고한다. release상한으로11개음의지속구간이원note-off보다총0.8044초짧다.

## D. 원자료

- [기준config](/home/ajou/yigyu/3/paper/initial_pose/lower_body_release_v1/front_facing_ready_v1/inputs_spine_margin035_v1/baseline_v1.json)
- [초기 자세값·제어](/home/ajou/yigyu/3/paper/initial_pose/current_v3/VALUES.md) · [매체](/home/ajou/yigyu/3/paper/initial_pose/current_v3/MEDIA.md)
- [단음 joint코드](/home/ajou/yigyu/3/guitar_learning/joint/README.md) · [실제 결과](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_joint_v1/README.md)
- [전곡시간표](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/score_schedule_v1.json) · [전곡구현](/home/ajou/yigyu/3/guitar_learning/song/task.py) · [전곡 최종보고](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_full_song_v1/training_v2/report.json)
- [현행학습안내](/home/ajou/yigyu/3/guitar_learning/README.md)

실행별settings·training_contract·소비입력SHA와실제episode/전이/update/report를함께보존한다. 자산치수·mesh·질량자료는 [모델명세](/home/ajou/yigyu/3/paper/object/README.md)를참조하며시각mesh/source형상/실제native접촉을구분한다.
