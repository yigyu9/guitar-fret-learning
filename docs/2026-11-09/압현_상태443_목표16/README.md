# 압현 상태443·목표16 전용 학습

기존 `guitar_learning.train`과 기존 checkpoint를 보존하고, 명시적 별도 진입점으로 새 압현 입력·신경망을 학습한다. 기존 모델의 가중치 변환이나 입력 SHA 검증 우회는 제공하지 않는다.

## 입력과 신경망

| 상태 묶음 | 차원 |
|---|---:|
| 전신105축의 기준각 대비 차이·속도·적용 목표각과 실제각의 차이 | 315 |
| 압현 정책의 이전 행동 | 33 |
| 골반 기준 기타 상대 위치·6D회전·선속도·각속도 | 15 |
| 기타 기준 왼손 손목 상대 위치·6D회전·선속도·각속도 | 15 |
| 가슴·오른쪽 상완·오른쪽 허벅지·왼손5손가락·양발 접촉 | 10 |
| 초기 기타 자세와 양발 위치 대비 변화 | 12 |
| 검지~소지 각각 유효 압현 여부·연속 유지 시간 | 8 |
| 공통 손목 안내 유효 여부·중심·반폭 | 7 |
| 엄지–넥 상대 상태 | 8 |
| 검지~소지 실제 굽힘각12개·측정 유효 여부4개 | 16 |
| 손목 이탈 감시·누적·초기 유예·심각한 연속 이탈 | 4 |
| 합계 | **443** |

`--include-pelvis`를 지정하면 골반 기준 중력 방향·선속도·각속도9개를 더해 **452차원**이 된다. 이는 관측을 추가하는 옵션이며 root 고정을 해제하는 옵션이 아니다. 기본443차원은 사용자의 최종 목록대로 손목 안내7개를 상태에 유지한다.

목표는 검지·중지·약지·소지 각각 현재 추종 목표와 다음 목표, **총8슬롯**이다. 목표당16개는 줄·프렛·손가락·압현 시작/발음 시작/해제까지 시간6개, 패드 위치 오차3개·상대속도3개·방향 일치도·표면 높이·접촉 후보·오압현이다. 유효 마스크8개를 별도로 사용하며, 빈 슬롯의 인코딩 결과는0으로 만든다. 기존 일반 미리보기 목표의 추가 attention 요약은 사용하지 않는다.

```text
상태443 (골반 추가 시452) → 256 → 256 → 상태 특징256
각 목표16 → 공유 인코더64 → 64 → 8개 목표 특징512
연결768 → 결합부512 → 256 → 왼손33축 출력
```

신경망 크기는 고정이다. `--size small/medium/large`는 기존 설정·metadata 형식과의 연결을 위해 받지만 이 별도 정책의 은닉층 크기를 바꾸지 않는다. 정책은33축의 독립 Gaussian 분포를 학습한다. 공용 실행기와 연결하기 위한39열 행동 중 마지막 오른손6열은0이며 정책 출력·확률 계산의 학습 축에는 포함하지 않는다.

보상·종료 조건·접촉 계산·목표 스케줄·105축 제어기·준비 자세 복원·60Hz정책/240Hz물리·J공동 학습·PPO 업데이트는 기존 경로를 재사용한다. 최초 접촉/압현 유지 보상을 새로 정의하거나, 기존 성공 실험의 탐색값0.35를 자동 채택하지 않는다. 관측 변경의 정상 작동과 실제 학습 성능은 별도 검증 대상이다.

새 환경은 최근 손가락별 준비·전환 경로와 같은 E4(조기 목표 노출·준비 구간 대기 보상 해제·표면 접근 준비)를 사용한다. 기존 기본 J 진입점의 설정을 변경하는 것은 아니며, E4를 사용하지 않은 기본 경로와 완전히 동일한 보상 노출 조건이라고 해석하면 안 된다. 실제 접촉 판정·보상 계수·물리·제어는 상속한 환경의 계산을 유지한다.

## 실행

프로젝트 루트에서 Isaac Gym·Torch가 설치된 기존 런타임을 사용한다. 출력은 새 디렉토리로 지정한다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_press train \
  --num-envs 1024 --horizon 32 --updates 800 --size large \
  --checkpoint-every 100 --seed 7 --out runs/compact_press_443_v1
```

먼저 소규모 정상 동작을 확인하려면 `--num-envs 2 --updates 1`로 줄인다. 골반 관측을 추가하려면 새 학습에 `--include-pelvis`를 지정한다. 입력 차원이 달라지는 만큼443모델을452모델로 재개할 수 없다.

```bash
python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_press train \
  --resume runs/compact_press_443_v1/J/final.pt \
  --updates 100 --out runs/compact_press_443_resume_v1

python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_press evaluate \
  runs/compact_press_443_v1/J/final.pt \
  --num-envs 16 --out runs/compact_press_443_eval_v1

python scripts/tab2body.py run -m guitar_learning.tool.experiments.compact_press render \
  runs/compact_press_443_v1/J/final.pt \
  --num-envs 1 --out runs/compact_press_443_video_v1
```

재개 시 `--updates`는 추가 업데이트 수이며 원래 노출 계획·모델·optimizer·RNG·sampler 계약은 그대로 복원한다. 곡·size·환경 수·horizon·seed·골반 옵션 변경은 거부한다. 골반 옵션을 생략하면 저장된 값을 사용한다. 평가·영상의 환경 수 변경은 기존 평가 실행기에서 허용하는 범위를 따른다.

새 metadata는 `guitar_learning.compact_press_resume.v2`, 정책은 `guitar_learning.compact_press_policy.v2`이다. 소스·자산·설정 snapshot 검증과 PPO의 전체 identity 비교는 그대로 적용한다. 저장 후 소스를 편집하면 기존과 같이 엄격 재개/평가가 실패할 수 있으므로, 진행 중 학습의 소스는 편집하지 않는다.

## 코드와 검사

- 환경·입력 생성: `guitar_learning/gpu/compact_press.py`
- 독립 정책: `guitar_learning/training/compact_press.py`
- train/evaluate/render 진입점: `guitar_learning/tool/experiments/compact_press.py`
- CPU검사: `guitar_learning/tests/test_compact_press_*.py`

CPU 합성 관측 검사는 차원·정규화·마스크·checkpoint/소스 봉인의 동작을 확인한다. 실제 줄 접촉이나 연주 성공을 증명하지 않는다. GPU학습 결과가 생기면 별도 결과 디렉토리에 기록한다.

## 결합부 변경(v2)

사용자 요청으로 행동정책 결합부를768→512→256→33으로 확대했다. 가치망은768→256→256→가치2개를 유지한다. v1(256결합부)의 source·중단 checkpoint는 전곡학습_7시간_v1/보존소스 및 학습/J에 보존한다. v1 checkpoint는 v2로 암묵 재개하지 않는다. 새7시간 실행은 [결합512 실험](전곡학습_7시간_결합512_v2/README.md)을 따른다. 기존 검증/기록은 v1의 당시 증거이며 v2 실행 검증은 새 실험에 기록한다.
