# GPU 왼손 clean 유지·연속 달성 v12

음 달성 보너스의 조건을 **누적clean40% → 연속clean40%**로 바꿨다. 유지 보상은 기존의 `2 × 정상 압현 시간 / 음 길이`를 사용한다. 이번 작업은 보상 구조 개선이며 native/GPU 학습을 실행하지 않았다.

## 동작과 범위

- 달성 시간은 음의 시작 `onset_s`부터 끝 `end_s`까지 계산한다. 이전·현재 정상 압현 후보가 모두 유효한 물리240Hz 구간의 겹치는 시간만 새 `clean_streak`에 더한다. 정상 압현이 끊기거나 시간창 밖이면0으로 초기화한다.
- 문턱은 기존 `min(D, max(0.05초, left_fraction×D))`, 기본 `left_fraction=0.4`다. 1초음은 연속0.4초,0.1초음은 연속50ms,50ms보다 짧은 음은 음 길이가 문턱이다.
- 처음 문턱을 채우면 기존 `0.5 × 손가락별 균형계수 × timing 단계계수` 보너스를 한 번 지급한다. `left` 달성 flag는 이후 단절돼도 유지하며 같은 음에 다시 지급하지 않는다. 같은 프렛·손가락의 다음 음은 별도 목표다.
- 누적 `clean`·`held` 및 유지 보상은 보존한다. 단속 접촉도 실제 정상 구간만큼 유지 보상을 받지만, 짧은 접촉을 합쳐 달성 보너스를 얻지는 못한다. 달성 후에도 음 끝까지 유지 보상이 계속된다.
- 최초접촉의 `contact_streak`는 기존 press~end 연속50ms 조건을 유지한다. 준비 구간에서 최초접촉을 달성했어도 onset 이전 시간은 음 달성에 포함하지 않는다.
- 수집 경계에서는 연속시간이 이어지고 에피소드reset은 해당 환경만 초기화한다. 한 표본의 정상후보 소실도 연속성을 끊는다.

GPU 왼손은 길이가0 이하인 onset~end 창을 초기 단계에 거부한다. 기존 양수 press~end 검사와 함께0문턱 무접촉보너스·0분모를 막는다. 공유 작업 정의·CPU왼손·오른손의 기존 입력·누적 판정은 유지한다.

## 관측·기록·버전

GPU 왼손 event11은 `clean_streak_s`로 현재 음 시작 이후의 연속 정상압현 시간을 전달한다. 기존 크기와 scale을 유지하고 event12/13은 계속 누적held시간·비율을 전달한다. 상태544·event24·priority8·커리큘럼3331값은 그대로다. 누적clean 비율의 history도 보존한다.

보상은 `gpu_tensor_song_reward.v12`, 표면 보상 묶음은 `surface_fretting.v6`, 표면 관측 의미는 `left_surface_events.v4`, 원장은 `surface_note_ledger.v5`다. 원장에 `clean_streak`를 추가하며 이는 현재 연속시간이고 최대 연속시간은 아니다. v11 이하와 의미가 달라 strict resume를 거부하며 동일v12 전체 계약만 복원한다.

패드·프렛·법선·하중·오압현 판정과 보상 크기·최초접촉·손목·손가락 움직임 비용0·물리·제어·PPO는 유지했다. 연속40%는 **학습용 중간 달성** 기준이다. 음 전체의 압현·압력·음향 품질이나 연주 수렴을 입증하지 않는다.

## 검증

관련 **23모듈229개 CPU검사 전부 통과**했다. 새 전용14개는 연속/단속 접촉·정확40% 문턱·준비접촉 제외·비정렬 시간창·최소50ms와 짧은음cap·보너스최초1회·지급후유지·유지보상원식·반복음/행독립·reset/수집경계·관측/원장·오른손누적보존·0음길이거부·v12복원/v11재개거부를 확인했다. 양수음길이guard를 추가한 후 관련8모듈82개도 다시 실행했다.

독립 change-reviewer가 관련75개 검사를 확인하고, 비정렬 onset/end와 무작위 접촉 패턴의1,152개 물리표본·목표 쌍을 별도 스칼라 적분과 대조했다. 연속clean·누적clean/held·달성래치·최초접촉streak가 일치했으며, 발견한0음길이 경계도 수정·검증했다. 남은 지적은 없다. 활성446개 Python의 문법과 동결SHA, 보관462개 원문과 이전v11 보고서472개 파일의 SHA를 확인했다. [검사 목록·원문 로그](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_clean_v1/cpu_tests.json)와 [수치 검증 기록](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_clean_v1/verification.json)을 보존한다.

이는 CPU 텐서로 GPU 경로 계산·관측·보상·저장 계약을 확인한 검사다. native/실제GPU 실행·학습 성능 검증은 이번 범위에 포함하지 않았다. 기존 별도 GPU544/옛512 기대 불일치는 [이전 보고서](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_wrist_region_v1/README.md)에 보존했고 이번229개 검사 수에는 포함하지 않았다.

변경 전 v11 코드·검사·관련 문서462개 원문은 [보관 목록](/home/ajou/yigyu/3/guitar_learning/archive/20261023_before_continuous_clean_v1/manifest.json)에 보존했다. [v11 최초접촉의 구현·검증](/home/ajou/yigyu/3/docs/2026-10-23/guitar_learning_continuous_contact_v1/README.md)은 이전 결과로 유지한다.
