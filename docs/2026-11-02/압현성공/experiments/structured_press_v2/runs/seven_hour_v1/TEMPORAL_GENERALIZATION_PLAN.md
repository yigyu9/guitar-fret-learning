# 음 시작 시각 일반화 진단의 사전 조사와 최소 계획

2026-10-31. **조사와 계획만 작성했다. 시간 변경 hook은 구현하지 않았고 GPU 검사를 실행하지 않았다.** 현재 실험과 봉인 runtime을 변경하지 않는다.

## 확인하려는 한계

현재 손가락별 A 유래 free 정책은 한 고정 줄·프렛을 대상으로 준비 3초 뒤 2.5초 동안 압현한다. 이 조건의 성공만으로 음표 관측에 반응하여 접촉 시점을 조절하는 전략을 학습했다고 할 수 없다. 고정된 초기 상태·에피소드 시계 또는 반복되는 관측을 이용한 동작도 가능하다. 반대로 현재 결과만으로 시간 암기를 확정할 근거도 없다.

지원 A에서 단계가 나뉘었다는 사실과 free 정책이 같은 시간 순서를 스스로 학습했다는 주장은 다르다. free 실행에서는 지원 단계가 해제된다. 이번 진단은 목표 기하 일반화나 자연스러운 동작 검증과도 구분해야 한다.

## 시간이 연결되는 코드와 주의점

아래 경로는 모두 연구 사본 `runtime/guitar_learning/` 아래이며 읽기만 했다.

| 위치 | 확인한 연결 |
|---|---|
| `training/finger_skill_runner.py:497~507` | 원본 pool/policy 생성 → trainer.load의 strict 검증 → 평가 설정 → reset 순서 |
| `song/task.py:298`, `:356~357` | make_task가 원본 음 시각과 pre_roll을 합쳐 onset/end/press 시각 및 에피소드 일정을 구성 |
| `gpu/environment.py:126`, `:166`, `:321~323` | task 생성 뒤 ObservationBuilder와 onset/end/press GPU 텐서 구성 |
| `gpu/finger_skill_environment.py:70~74` | pre_roll=3초를 검사하고 preparation_s=3초의 phrase catalog 생성 |
| `gpu/finger_skill_environment.py:171`, `:194` | task 기반 진단 구성과 full-song view_first=3초 |
| `gpu/finger_skill_environment.py:253~255` | 안내 시계에서 pre_roll을 차감 |

따라서 생성 후 task의 onset 하나만 덮어쓰거나 보상 구간만 옮기는 방식은 부적절하다. 음표 토큰, press 접근·접촉 창, audible 보상·오압현 창, 음 수행 부족 정산, phase/readiness, standby/recovery, 진단 원장, 안내 시계, 노출 일정과 종료 길이가 같은 이벤트를 가리켜야 한다. 원본 contract에 다른 시간을 넣고 동일한 identity라고 주장해서도 안 된다.

## 미래의 최소 안전 실험

1. 이미 원본 검증을 마친 **free_v9 export 정책**으로 먼저 검지 하나만 검사한다. 원본 checkpoint SHA, source pins와 저장 identity를 기존 원본 환경에서 strict 검증한다. 원본 optimizer를 실행하거나 저장 파일을 변경하지 않는다.
2. 검증 완료 뒤 별도의 진단 pool을 만든다. 원본과 같은 기하·물리·압현 판정·보상 계수·평균 정책 가중치를 사용하고 이벤트 시각 변경만 별도 provenance로 기록한다. 새 task를 환경 생성 시작부터 일관되게 전달하여 관련 관측·시간 텐서·catalog·진단을 함께 구성한다. 원본 identity 검증 결과와 진단 설정 SHA를 분리한다.
3. baseline은 onset=3.0초/end=5.5초/음 길이2.5초/tail0.5초다. 첫 변경은 onset=4.0초/end=6.5초/음 길이2.5초/tail0.5초로 한다. 기존 3초 준비 계약을 유지한 뒤 음 시작만 1초 지연하는 해석이다. 단순 event shift만으로 전체 의미가 일치하는지는 CPU 계약 검사로 먼저 확인한다.
4. 두 조건 모두 native 평균 정책 최초32환경 episode를 모은다. 물리·손목 실패도 분모에 포함한다. 초기 actual q와 hold_target을 직접 저장·비교하여 reset 대응을 증명한다. 같은 seed/명령만으로 대응되었다고 쓰지 않는다.
5. 원본 baseline 성공과 판정이 재현되고 입력 무결성·시간 일관성 검사가 통과한 후에만 지연 조건을 실행한다. 네 손가락 확대는 검지 결과를 확인한 뒤 결정한다.

onset=2초로 앞당기는 실험은 별도 후속안이다. 기존 3초 준비의 assertion·view_first·guide·standby/recovery 등의 의미를 명시적으로 재정의해야 하므로 최소 지연 실험에 끼워 넣지 않는다. 현재 코드에 작은 사후 patch만 추가하는 작업으로 취급하지 않는다.

## 반드시 기록할 값

- 실제 목표의 onset/press/end, episode 종료, task·토큰·보상 창·진단의 시각 일치 여부.
- 최초 유효 접촉의 절대 시각과 `접촉 시각 − onset`, onset 전 candidate/접촉 지속 시간.
- 전체 clean 시간, 최장 연속 clean, 음 시작 후 첫0.5초 clean, 오압현 종류와 지속 시간.
- 물리·손목 실패, 단계·준비 조건 차단 시간, 목표 패드/손목 실제 궤적.
- 원본 체크포인트와 model tensor의 전후 동일성, optimizer update=0, 원본 strict 검증 완료 여부.
- 진단 스크립트·설정·task/provenance·raw 결과 SHA와 실제 초기 q/hold 대응 증거.

## 판단의 한계

지연된 음도 성공했다고 해서 음표 시작에 맞춘 동작이 입증되지는 않는다. 원래 3초 부근에 미리 누른 상태를 4초 이후까지 유지해도 성공할 수 있다. 그래서 precontact와 최초 접촉 상대 시각을 함께 확인한다. 반대로 지연 실패는 물리 settling 시간이 길어진 영향과 시간 전략 문제를 나누어 봐야 한다.

이 검사는 단일 목표의 시간 변화 진단이다. 여러 줄·프렛 전환, 곡 단위 일반화, 엄지 지지 또는 실제 현별 힘·소리를 입증하지 않는다. 목표 기하와 초기 자세의 안내는 계속 남으므로 ‘안내 없는 학습’ 실험도 아니다.

현재 상태: **미구현·미실행. 기존 학습/평가 결과에 이번 계획을 적용한 것처럼 해석하지 않는다.**

## 추가 조사: 2초·4초 준비 길이 변경의 정확한 영향과 보류 사유

현재 연구에서는 구현하지 않는다. 고정 체크포인트 표본화와 B 팔 제한의 원인 대조를 먼저 마무리한다. 다음은 조사한 변경점이며 적용한 변경 내역이 아니다.

2초/4초를 실제 준비 길이 변경으로 검사하려면 다음 요소를 같은 이벤트 시계로 구성해야 한다.

1. task 생성 시작부터 onset·press·end와 episode duration을 함께 바꾼다. 목표 음 길이2.5초와 tail0.5초를 유지하면 종료는 각각5초/7초다. source 원본과 진단 시간 변환 provenance를 분리한다.
2. 환경 생성 시 ObservationBuilder, onset/end/press 텐서, 관측 정규화 scales에 같은 task를 공급한다. 생성 후 onset 텐서 하나만 바꾸지 않는다.
3. FingerSkillEnvironment의 pre_roll=3 검사, build_phrase_catalog(preparation_s=3), full-song view_first=3, 안내 시계의 pre_roll 차감, SkillEpisodeDiagnostics의 초기3초 준비 창을 함께 검토한다.
4. 손목 정상 종료의 local3초 enable도 실제 준비 종료와 맞추어야 한다. 기하 기반 readiness 자체는 유지한다. free_v9의 phase는 기록·관측용이며 실행 지원을 새로 켜지 않는다.
5. 평가 collector의 최대 tick 계산과 실제 episode 종료도5초/7초를 모두 수집하도록 일치시킨다. 긴7초 에피소드를 기존6초 수집 제한으로 잘라 불완전 결과를 실패로 세지 않는다.

가장 안전한 설계는 원래3초 source 환경에서 원본 trainer.load의 strict identity 검증을 먼저 통과한 정책을 고정하고, 새 시간 과제를 별도 진단 pool의 생성 시작부터 구성하는 것이다. 새 과제를 원본 identity로 위장하지 않는다. 원본 검증·가중치 동일성과 진단 task/시간 변경 SHA를 별도 기록한다. 실제 q/hold에 더해 가능하면 body/root 초기 snapshot도 비교한다.

검증 순서는 다음과 같다.

1. 외부 진단의 onset3초 대조가 원래 평가의 최초32 episode 결과·요청 행동·9항 보상·종료를 재현하는지 확인한다.
2. CPU에서 목표 onset 직전/직후 각1/240초의 token, press/contact/audible 창, 수행 부족 정산, standby/recovery를 검사한다. 종료가 정확히5초/7초인지도 확인한다.
3. 위 검사를 통과하면 native 평균 정책으로2초와4초를 각각 최초32 episode 평가한다. 실패도 분모에 포함한다.
4. 최초 접촉의 절대 시각·onset 대비 상대 시각, 준비 중 접촉, 음 시작 후 첫0.5초 clean을 함께 분석한다. 원래3초 무렵 미리 눌러 지연된 음까지 유지한 결과를 목표 시각에 반응한 성공이라고 해석하지 않는다.

고정3초 가정이 여러 곳에 있어 엄격한2초/4초 비교를 작은 외부 도구 하나로 안전하게 구성하기 어렵다. 검증 없이 기존 초기화 검사를 우회하거나 환경 일부 시계만 바꾸면 원인 해석이 더 불명확해진다. 따라서 이번 연구의 남은 시간을 원인 대조에 사용하고, 시간 일반화는 별도 후속 과제로 남긴다. 필요하면 우선3초 준비 뒤1초 무음을 추가한4초 지연만 좁게 검사할 수 있지만 이 조건 역시 이번에는 구현·실행하지 않는다.
