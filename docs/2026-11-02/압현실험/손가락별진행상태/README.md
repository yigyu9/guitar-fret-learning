# 손가락별 진행 상태 분리

검지의 준비와 중지의 압현 유지처럼 서로 다른 시점의 동작을 한 정책에서 표현하기 위한 작업이다. 새로운 진행 상태는 손가락별 관측·진단이며 행동을 잠그는 직렬 제어가 아니다.

진행 중인336조합 검사의 기존 소스·입력은 보존한다. 이번 구현은 새 환경·정책·실행기·검사 파일로만 추가하며, 기존557상태 기본 정책과601상태 단음 자연스러운 준비 정책의 계약을 바꾸지 않는다. 새 곡 학습 경로는 새 관측·architecture로 명시적으로 실행하며 구형 체크포인트를 암묵적으로 재개하지 않는다.

## 동작 원칙

- 네 손가락의 현재 목표·다음 목표·진행 상태·경과 시간을 각각 관리한다.
- 같은 손가락에서는 현재 울리는 음의 유지가 미래 준비보다 우선한다.
- 다른 손가락의 목표 변경·음 종료가 현재 손가락의 타이머를 초기화하지 않는다.
- 음 종료 후 남은 접촉의 해제와 다음 목표의 준비를 구분하되, 상태 때문에 행동을 잠그거나 모든 관절의 이동을 강제하지 않는다.
- 손목은 네 개로 나뉘지 않는다. 기존 공통 손목 안내 영역을 유지하고 압현 중인 목표와 미래 준비 목표의 공통 실현성은 별도로 검증한다.
- 보상 예산·접촉 기준·PD·물리·손가락 제어 범위·음별 달성 원장은 변경하지 않는다. 새 곡 경로는 E4의 조기 목표 노출·준비 접근 방식을 명시적으로 사용한다.

## 검증과 한계

CPU에서 손가락별 비동기 상태, 목표 우선순위, 부분reset, 수집 경계, 관측과 정책, 저장/엄격복원을 검사한다. 실제 GPU 학습 성공과 다중 압현의 물리 가능성은 별도다. 현재336검사와 GPU를 동시 사용하지 않는다.

구현 및 검증 결과는 작업 종료 후 아래에 갱신한다.

## 구현 완료: 새 곡 학습 경로

새 파일4개만 추가했다. 기존 활성 Python295개의 SHA는 작업 전과 동일하다.

- [상태·환경](/home/ajou/yigyu/3/guitar_learning/gpu/finger_progress.py): 손가락별 목표/진행 상태/타이머와 로그
- [정책·실행기](/home/ajou/yigyu/3/guitar_learning/tool/experiments/song_finger_progress.py): 새 관측을 실제 정책에 연결하고 학습·재개·평가·영상 제공
- [상태 검사](/home/ajou/yigyu/3/guitar_learning/tests/test_finger_progress.py)
- [정책·저장 검사](/home/ajou/yigyu/3/guitar_learning/tests/test_song_finger_progress.py)

기존557상태에 손가락당14개씩56개를 더한 **613상태**다. 네 손가락의6상태 one-hot, 추종 목표 유효 여부·원래 목표 인덱스, 시작/누름/종료까지 남은 시간, 해당 목표 선택 후 시간, 연속 정렬/clean 시간을 제공한다. 지지17축 정책은 네 손가락의 진행 상태를 함께 보고, 각 손가락4축에는 해당 손가락의 상태 branch를 추가했다. 모든 왼손33축이 함께 학습되며 단계별 행동 잠금·팔 교사는 없다.

| 상태 | 의미 |
| --- | --- |
| idle | 현재 추종·준비·최근 종료 목표 없음 |
| prepare | 담당 목표를 준비 중이며 준비 영역 정렬 조건은 미충족 |
| aligned | 담당 패드의 E4 준비 영역과 공통 손목 허용 영역 조건 충족 |
| press | 담당 목표의 압현 시각에 도달했지만 현재 음의 clean 접촉은 미충족 |
| hold | 담당 목표가 발음 구간 안이며 candidate이고 wrong이 아님 |
| release | 다음 준비 목표가 없고 직전 담당 목표 종료 후0.25초 이내 |

상태들은 반드시 차례로 거쳐야 하는 명령 시퀀스가 아니다. 다음 목표의 준비가 가능하면 release를 강제하지 않고 준비로 넘어간다. clean이 끊어지면 hold에서 press로 돌아갈 수 있다. 해당 타이머와 상태 변화가 다른 손가락의 기록을 초기화하지 않는다. 상태의hold는 그 손가락이 현재 추종하는 목표의 접촉이지, 화음 전체·현 압력·음향 성공 인증이 아니다. 전체 목표의 성과는 기존 음별 원장을 그대로 따른다.

E4의 조기 목표 노출·목표 손가락 대기 보상 gate·준비 영역에서 압현면으로 연결되는 접근 potential을 재사용한다. 이는 기존단음E4와 같은 준비 방식이며, E4를 끈 기본J 경로와 보상의 활성 시점까지 같다는 뜻은 아니다. 새로운 진행 상태 자체는 보상·행동·물리 원장을 변경하지 않는다.

### 실행 예시 — 이번 작업에서 학습을 시작한 것은 아님

프로젝트 루트에서 Isaac Gym 환경의 Python으로 실행한다. 아래 새 명시 경로를 사용해야613상태가 적용된다. 기존 `python -m guitar_learning.train`은 변경하지 않았다. 현재336조합 검사와 GPU를 동시에 사용하지 않는다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.song_finger_progress train \
  --song 05_BN2-131-B_solo --size large --num-envs 1024 \
  --horizon 32 --updates 3000 --out runs/song_finger_progress_v1

python scripts/tab2body.py run -m guitar_learning.tool.experiments.song_finger_progress train \
  --resume runs/song_finger_progress_v1/J/final.pt \
  --updates 100 --out runs/song_finger_progress_v1_continue

python scripts/tab2body.py run -m guitar_learning.tool.experiments.song_finger_progress evaluate \
  runs/song_finger_progress_v1/J/final.pt --num-envs 32 --out runs/song_finger_progress_v1_eval

python scripts/tab2body.py run -m guitar_learning.tool.experiments.song_finger_progress render \
  runs/song_finger_progress_v1/J/final.pt --num-envs 4 --out runs/song_finger_progress_v1_video
```

새 architecture/policy/resume 계약으로 저장·엄격 재개한다. 기존557/601상태 모델을 암묵 변환하지 않으며 동일 새모델의 입력SHA·설정 snapshot·PPO identity를 검증한다. 전체 스케줄·직접각 제어·관절 범위·물리·보상 예산은 기존J 기반을 유지한다. 곡 입력에1~14프렛 제약이 지켜졌는지는 전처리에서 별도로 확인해야 하며 이 모듈이 범위 밖 음을 삭제하지 않는다.

## 실제 검증 결과

- 신규CPU17검사 통과: [원문](CPU_검증.log).
- 검지 준비/중지 유지, 검지 목표 교체 중 중지timer 보존, 중지 종료 중 검지 유지, 각자 정렬 손실, 같은손가락 현재음 우선·다음준비 우선 확인.
- 일부 환경reset 격리·종료행 보존·H32 경계 및 중복시각에서의 타이머 보존 확인.
- 기존 E4 기반557관측·보상·비용·종료·모든 음 원장과32스텝 bit-exact 비교 통과.
- 실제613관측의 정책 출력/gradient, logp·KL·entropy·유한성, actor/critic 분리, 새모델 엄격 저장복원·구형 모델 거부·SHA 변조 거부 확인.
- 별도 독립 에이전트의 읽기 검토와CPU검사를 수행했다. GPU검증은 미실행이다. 이 결과로 곡 학습 수렴·다중 압현 물리 성공을 선언하지 않는다.

추가로 기존 `test_natural_press_runtime`7개는 과거 natural_press_v3 catalog의 contact.py pin이 현재 소스와 달라 시작 단계에서 실패했다. 현재 contact.py는 작업 전SHA와 같으므로 이번 신규파일로 바뀐 문제가 아니다. 과거봉인hash를 갱신하거나 검증을 우회하지 않았다. [기존 소스 보존 검증](기존소스_보존검증.json)을 참고한다.

## 기존336검사에 대한 간섭과 복구

기존파일은 수정하지 않았으나, 검사기가 active_source_paths로 신규파일도 봉인하기 때문에 작성 도중 `ring_s3_f4` 두 시도가 종료SHA불일치로 무효가 되었다. 이 두 원문은 보존했고 정상과제 실패로 계산하지 않는다. 신규4파일을동결한뒤의정상결과도현재SHA와일치한다. 당시영향점검JSON은해당시점의스냅샷이며누적결과는원장을따른다.

기존336검사가끝나고GPU가비면, 같은소스·seed7·목표에서 `attempt03`을실제재검사하도록 별도복구대기프로세스를실행했다. 성공여부와무관하게정상검사완료·입력SHA·identity·cleanup을검증한경우만별도 `integrity_recovery` 기록과함께원장을보완한다. 기존물리실패조합을재시도하는작업은아니다.

[복구 대기 상태](작업자료/소스간섭_재검사/state.json) · [작업 시점 영향 점검](진행실험_소스추가영향_점검.json) · [동결SHA](신규소스_동결_SHA.json)

## 손목을 곡 시작 전에 계획할 수 있는가

가능하다. 현재도 시간별 손목 허용 영역은 사전 계산한다. 다만 여러 음의 동시 접촉을 만족하는 실제 팔·손목 자세와 이동 경로를 구하는 solver는 아직 없다. 현재 유지해야 할 모든 음을 우선 제약으로 두고 다음 준비 음을 함께 고려해 구간별 공유 자세를 구한 뒤, 경로/속도/충돌과native실행을 검증하는 것이 다음 작업이다. 기타가 실제로 움직이므로 사전 계획 뒤에도 실측 보정이 필요하다.

[기존 코드와 손목 사전 계획 상세 검토](손목사전계획_검토.md)
