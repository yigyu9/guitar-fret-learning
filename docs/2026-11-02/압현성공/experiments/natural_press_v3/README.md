# 자연스러운 압현 준비 v3 구현과 검증

[승인된 설계와 구현 체크리스트](../../../../plans/natural_press_preparation_v3_20261031.md)를 구현하는 새 실험이다. 이전 structured_press_v2의 Python·체크포인트·완료 결과는 수정하거나 import하지 않는다. 검증된 초기 상태 catalog만 새 assets에 복사하고 원본 SHA와 현재 물리 입력144개의 SHA를 실행 때 검증한다.

## 구현 범위

- E0: 기존 보상·목표 노출 비교군. 새 진단만 추가한다.
- E1: 첫 목표 묶음의 손가락별 관측·focus를 리셋부터 노출한다. 일반 악보4초 문맥은 유지한다.
- E2: 목표 손가락의 준비 중 대기 보상만 끈다. 기존 접근 활성 시각과 관측의 대기 gate는 유지하고 실제 지급 gate만 분리한다.
- E3: 준비 시기부터 줄 위4~8mm, 가로±3mm 준비 영역의 접근 potential을 적용한다. 기존 대기 보상은 유지한다.
- E4: E1+E2+E3 조합이다.

목표 선택과 관측 노출·보상 준비 마스크를 구분한다. 첫 목표는 선택 구간의 가장 빠른 압현 시각 묶음이며, 이후 음은 기존2초 준비 창을 사용한다. 현재 울리는 음이 미래 준비보다 우선한다. 목표 없는 손가락에 임의 압현 목표를 만들지 않는다.

E3/E4는 음 시작0.2초 전부터 quintic 가중치로 준비 potential을 기존 표면 potential에 연결한다. 기존30mm 거리 척도·방향 품질·손가락 가중치를 유지한다. 접근 보상은 기존60Hz의 `gamma*nextPhi-Phi` 한 항이며, 수집 H32 경계에서 초기화하지 않는다. 실제 종료에서만 nextPhi=0이다. 최초 접촉/압현 유지/달성 예산0.25/1/0.25, 오압현·수행 부족·종료 조건·물리·제어는 유지한다.

## 학습 초기 상태와 행동 범위

`--distribution aligned/v9`와 `--axes goal4/arm16/full33`를 명시적으로 조합한다. 모든 조건에서 단계별 팔 clamp는 없다. 단계44열은 기존 비교를 위한 관측·진단이며 행동 잠금 조건이 아니다. 기본557열에44열을 더한601열 정책이고, 기존 저장본과 호환을 가장하지 않는다.

- aligned+goal4: 검증된 정렬 자세에서 목표 손가락4축만 학습한다.
- v9+goal4: 실제 초기 상태는 v9이며 팔12축은 정렬 IK의 고정 목표로 이동한다. 비목표 손가락은 v9 유지 명령을 사용한다. 팔 이동 자체를 학습하는 조건은 아니다.
- v9+arm16: 같은 팔 목표에서 시작하되 팔12축과 목표 손가락4축을 학습한다.
- full33: 기존 왼손33축 전체를 활성화한다.

일반 기본 학습 명령의 보상은 자동 변경하지 않았다. 실험 효과가 확인된 뒤 기본 경로 채택을 판단한다.

## 실행

Isaac Gym을 사용할 수 있는 Python 환경에서 프로젝트 루트 기준이다. 로컬 cache 경로는 해당 PC에서 쓰기 가능한 로컬 디스크로 정한다. 새 출력 디렉토리를 사용한다.

```bash
python scripts/tab2body.py --cache-root /tmp/tab2body_natural_press_v3 run \
  -m guitar_learning.tool.experiments.natural_press train \
  --song virtual_finger_v9_middle_s3_f6 --condition E4 \
  --distribution aligned --axes goal4 \
  --size large --num-envs 64 --updates 100 --seed 7 \
  --out runs/natural_press_v3_middle_E4_100
```

먼저 E0~E3를 같은 예산으로 비교한 뒤 E4를 평가한다. 위 명령은 사용 예시이며100회 학습을 완료했다는 뜻은 아니다.

```bash
python scripts/tab2body.py --cache-root /tmp/tab2body_natural_press_v3 run \
  -m guitar_learning.tool.experiments.natural_press evaluate \
  --checkpoint runs/natural_press_v3_middle_E4_100/J/final.pt \
  --num-envs 32 --out runs/natural_press_v3_middle_E4_eval

python scripts/tab2body.py --cache-root /tmp/tab2body_natural_press_v3 run \
  -m guitar_learning.tool.experiments.natural_press evaluate \
  --checkpoint runs/natural_press_v3_middle_E4_100/J/final.pt \
  --free-v9 --num-envs 32 --out runs/natural_press_v3_middle_E4_free_eval
```

기본 평가는32환경의 첫 에피소드를 사용하고 실패도 분모에 포함한다. 환경 수를 별도로 줄이면 평가 분모도 줄어들므로 비교 실험에서는32를 유지한다. `--free-v9`는 새 v3 내에서 가중치만 엄격 검증해0업데이트로 v9/full33 모델을 만든 뒤 평가한다. 이를 추가 학습 성과로 부르지 않는다. `render`도 같은 checkpoint와 free-v9 옵션을 사용할 수 있다.

같은 조건에서100회 추가하려면 다음처럼 새 출력으로 재개한다. 원래 노출 전환 문턱·최적화기·난수 상태는 보존하며, 조건·초기 분포·활성 축은 체크포인트 설정을 따른다.

```bash
python scripts/tab2body.py --cache-root /tmp/tab2body_natural_press_v3 run \
  -m guitar_learning.tool.experiments.natural_press train \
  --resume runs/natural_press_v3_middle_E4_100/J/final.pt \
  --updates 100 --out runs/natural_press_v3_middle_E4_200
```

## 기록

기존 학습의 항별 로그·음별 원장과 `finger_control_trace.jsonl.gz`를 재사용한다. 상세 추적에 목표 ID, 노출/준비/실제 음 상태, 패드 표본 인덱스, 높이·가로·프렛 방향 초과 오차, 방향 품질, 내려가기 가중치, 대기/접근 가중치, 대기 보상률과 접근 potential, 손목 오차·속도를 추가했다. potential은 상태 품질이며 매240Hz 보상 지급액이 아니다. 접근 보상은60Hz 종료에서 정산한다.

에피소드에는 손가락별 준비 시간, 내려가기 전 준비 완료 시간과 최장 연속 시간, 준비 미완료 상태의 저속 손목 시간, 조기 접촉 후보 시간을 기록한다. 기존 요청각·적용각·실제각 기록과 같은 시간축으로 분석한다. 단순한 준비 완료 후 기다림은 나쁜 정체로 집계하지 않는다.

## 검증 상태

구현과 작동 검증을 완료했다. 신규 CPU19개·관련 회귀112개 통과, GPU의2회 학습→2회 재개, 정렬/v9의32환경 평가, v9 이동 시작1회 학습을 확인했다. [검증 결과와 한계](validation/RESULTS.md)에 실제 수치와 기존 검사3건의 실패 재현을 기록했다. 자연스러움·압현 학습 성능의 개선은 짧은 작동 검사만으로 선언하지 않는다.
