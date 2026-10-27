# 학습 코드 계보 문서 독립 검수

**요약 판정: 문제없음.** 미해결 Critical·Warning·Suggestion과 전달 차단 문제는 없다. 검수자는 구현·원자료·타인 문서를 수정하지 않고 이 보고서와 대응 JSON만 작성했다.

검수 범위는 `guitar_learning/CODE_LINEAGE.md`, `code_map_v1.json`, `legacy_music_v1.md/.json`, `native_provenance_v1.md/.json`이다. 현재 실행 소스와 과거 비교 소스를 읽고, 저장된 실제 reset 계약으로 CPU 모델만 구성했다. 새 물리·정책 실행·학습이나 직전 접촉 trace의 재집계는 하지 않았다.

- **실제 실행 경로:** `train_actionable_preparation.run`→`train_timing.run`→`train_specialists.run`→`train_parallel.main`과 환경 factory·Pool·Policy·PPOTrainer의 실행 중 binding 교체 설명은 소스와 일치한다. 근거: `train_actionable_preparation.py:73`, `train_timing.py:94`, `train_specialists.py:41`.
- **상속과 보상:** actionable→timing→skill-v2→skill→TrainingEnvironment와 내부 contact/persistent 결합을 구분했다. Dense/Specialist 환경 전체를 상속·누적한다고 설명하지 않는다. 최종 reward는 action-change·terminal-failure·timing 항·준비 접촉 항이며, 별도 cost 전달도 명확하다. 근거: `timing_environment.py:65`, `timing_environment.py:134`, `skill_environment.py:300`, `actionable_preparation_environment.py:53`.
- **실제 모델:** 저장된 양손 reset의 536 상태 계약으로 medium SpecialistPolicy를 독립 생성했다. 총 파라미터 2,944,336개, requires_grad 기준 LH 1,964,874개·RH 1,957,935개로 문서와 일치한다. 반대 손 Actor의 저장 파라미터와 선택 손 likelihood를 구분하며, 105 관측 관절·39 행동 슬롯·선택 손33/6 출력을 혼동하지 않는다. 근거: `specialist_policy.py:24`, `specialist_policy.py:112`.
- **PPO와 가중치 계보:** 현재 자체 PPO와 기존 tab2body/fresh54를 구분했다. Actor/std 이전은 critic·optimizer·카운터를 이어받는 strict resume와 다르며, 물리 episode/solver 복원도 주장하지 않는다. 초기화 설정은 자체 timing stage1 final.pt를 가리킨다. 근거: `ppo.py:60`, `ppo.py:218`, `actionable_preparation_transfer.py:64`.
- **직접 재사용·복사·변형:** 음악 compiler 실제 호출, manifest로 확인되는 복사, strike의 명시적 NumPy adaptation, 네트워크/PPO의 설계 비교를 구분했다. 코드 유사성만으로 역사적 복사량을 단정하지 않는다. origin manifest 15쌍의 양쪽 기록 SHA가 모두 일치하며, 서로 바이트까지 같은 3쌍과 변경된 정리본을 구분한 최신 설명도 맞다.
- **legacy/native 범위:** 기존 FretReward의 veto·NO_PRESS·오압현 감점, StrikeTask 준비·ordered strum·회복·뮤팅 감독의 미이식/축소를 정확히 설명한다. reward_mode="legacy"를 옛 보상 클래스 직접 실행으로 오해하지 않는다. native 장면/유한 제어·생성자의 FK/참조·legacy 자산 의존과 정책 제출 시 스크립트 우회, 준비 snapshot step5280과 reset 물리 시각0을 구분한다. 이 정적 감사로 압력·음향·물리 파지를 인증하지 않는다.

독립 SHA 대조에서 code_map 소스30개, legacy 입력32개, native 소스46개와 origin manifest 원본/정리본15쌍은 모두 일치했다. 세 문서의 local 링크240개는 경로 존재와 줄번호 범위 검사를 통과했다. 핵심 실행·보상·모델 링크는 실제 정의/처리와 직접 대조했다.

검수 중 `CODE_LINEAGE.md:21`·`:49`의 runner 링크가 함수 대신 preparation summary의68행을 가리키는 작은 위치 문제를 전달했다. 작성자가 실제 `run`의73행으로 정정했고 재확인했다. 해결된 위치 Suggestion이며 내용상 필수 수정은 발견하지 않았다. 추가된 manifest 동일성 구분과 native 생성 의존/시간/metadata 한계 설명도 기존 근거와 일치한다.

이 두 검수 파일을 최종 확정한다. 후속 구현 제안은 문서의 감사 결과이며 이번 검수에서 코드·학습 조건을 변경하지 않았다.
