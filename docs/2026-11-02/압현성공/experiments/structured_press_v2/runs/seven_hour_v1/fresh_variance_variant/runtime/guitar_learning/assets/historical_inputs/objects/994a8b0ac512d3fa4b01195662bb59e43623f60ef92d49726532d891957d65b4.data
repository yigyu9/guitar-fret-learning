# 단음 해제·복귀 동작의 국소 학습

현재563상태·39행동 음악 품질 환경에 추가한 독립 경로다. 기존 단음 PPO가 압현·최초 타현에는 도달하지만 LH 음 종료 후 해제와 RH 추가 타현 억제에서 실패하는 문제를 다룬다. 보상과 성공 문턱을 낮추지 않고, 기존 정책의 앞부분을 유지하면서 실패하는 뒷부분의 행동을 보강한다.

이 구현은 성공을 보장하는 제어기가 아니다. **보조 동작의 native 성공 → Actor 적합 → 보조 동작 없는 정책의 native 성공 → 새 PPO 초기화**를 구분한다. 실제 실행 결과는 [실험 디렉토리](/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_local_skills_v1)에 보관한다.

## 구성

| 파일 | 역할 |
| --- | --- |
| [controls.py](/home/ajou/yigyu/3/guitar_learning/local_skills/controls.py) | LH 음 종료 후 기준 목표 복귀/손가락 굽힘 해제, RH 첫 인정 타현 후 명령/적용 목표 유지 후보 |
| [probe.py](/home/ajou/yigyu/3/guitar_learning/local_skills/probe.py) | 기존 정책·영행동 기준선과 보조 동작을 실제 환경에서 비교하고 행동 직전 관측을 수집 |
| [learning.py](/home/ajou/yigyu/3/guitar_learning/local_skills/learning.py) | 성공한 전체 실행 검증, 선택 Actor의 국소 행동 모방과 기존 구간 행동 보존, 명시적 BC 초기화 형식 |
| [evaluate.py](/home/ajou/yigyu/3/guitar_learning/local_skills/evaluate.py) | 보조 제어 없이 적합한 정책만 결정적으로 실행하고 원 품질·안전4/4 통과 시 평가 증거 발급 |
| [train.py](/home/ajou/yigyu/3/guitar_learning/local_skills/train.py) | 해당 모델·자료·계약과 실제 평가 증거를 확인한 후 기존 품질 PPO에 Actor만 이전 |

## 유지하는 조건

- Root 고정, 원 하체 유한 제어,105입력/97비영범위/8영범위 축을 유지한다. 기타는 자유 강체·중력ON·스트랩OFF다.
- 보조 동작도 기존39차원 정규화 행동·원 관절 범위·평활화·속도 제한을 통과한다. 직접 기타 힘, 부착, 실행 중 기타 상태 덮어쓰기는 사용하지 않는다.
- 실제 시간은 native정착0초+정책7초이며 처음2초에도 음악적 준비 행동과 안전 판정이 작동한다. 원240Hz 물리·60Hz 행동·stage1±0.5초 판정을 유지한다.
- LH는 원래 clean audible 비율과 최종 release, RH는 준비된 타현·wrong/blocked/extra 없음·최종 recovery를 함께 요구한다. 가슴 접촉 지속은 성공 필수조건이 아니다.
- 타현은 피크 표식의 기하 통과이고 압현은 native 접촉 근거다. 실제 현 압력·진동·음향 성공을 뜻하지 않는다.

## 학습 자료와 이전 범위

교사 실행도 처음부터 끝까지7초를 모두 수행해야 한다. 원 품질 성공, 물리 실패0, 입력SHA 불변, 금지 호출0, 정상 종료와 부모 탐색 결과의 최종 확정까지 확인한다. 진행 중 partial 결과와 실패 실행은 학습 자료로 받지 않는다.

`demonstration.npz`에는 행동 **직전**563상태와 이벤트/마스크, 실제 행동39, 원 정책 행동39, 개입 여부와 시간을420행 저장한다. 원 checkpoint를 다시 실행해 기록한 정책 행동과 일치하는지도 검사한다. 원 checkpoint와 자료·계약의 SHA를 초기화 모델에 연결한다.

BC는 해당 손의 Actor encoder/head만 수정한다. 손을 바꾸거나 critic·std·버퍼를 함께 학습하지 않는다. 손실은 개입 구간 교사 행동MSE와 비개입 구간 원 정책 행동MSE의 동등 가중 평균이다. 앞부분 보존 오차도 기록하지만, 오차 감소를 실제 안정성이나 정책 성공으로 해석하지 않는다. 단일 교사 궤적만으로 분포 이동에 견디는 정책이 되었다고 주장하지 않는다.

새 PPO는 선택 Actor와 원 std만 초기화하고 critic·Adam·학습 counter·RNG는 새로 시작한다. 기존 PPO의 strict resume 계약은 완화하지 않는다. 보조 제어 없는 실제 정책4회가 모두 전체 품질·안전을 통과해야 fresh PPO 진입이 가능하다. gate의 `passed` 값뿐 아니라 실제 결과·평가 지표·소비 입력과 정확한 모델SHA를 다시 확인한다.

## 실행 순서

아래 명령은 프로젝트 루트에서 `rl38` 환경을 활성화하고 실행한다. 각 출력은 존재하지 않는 새 디렉토리를 사용한다. 실제 native 실행 전에는 `LD_LIBRARY_PATH`에 `/home/ajou/miniconda3/envs/rl38/lib`가 필요하다. 실행기는 native 모듈을 torch보다 먼저 불러온다.

```bash
python -m guitar_learning.local_skills.probe \
  --settings <원563 품질 설정.json> --checkpoint <자체563 PPO.pt> \
  --out <새 native 탐색 디렉토리>

python -m guitar_learning.local_skills.learning \
  --capture <최종 성공 candidate 디렉토리> --out <새 BC 디렉토리> \
  --steps 1000 --learning-rate 0.0001 --batch-size 120 --device cpu

python -m guitar_learning.local_skills.evaluate \
  --settings <local BC 설정.json> --initialization <BC/actor_initialization.pt> \
  --out <새 정책 평가 디렉토리> --episodes 4

python -m guitar_learning.local_skills.train \
  --settings <통과 gate를 참조하는 local BC 설정.json> --out <새 PPO 디렉토리>
```

local BC 설정은 원 품질 설정을 복사해 `actor_initialization`을 새 BC 모델의 절대경로로, `actor_initialization_kind`를 `bc`로 지정하고 아래 항목을 추가한다. 평가 전에는 `evaluation_gate`를 생략하고, 평가가 통과한 뒤 새 PPO 설정에 실제 gate 절대경로를 넣는다. 원 역할·망 크기·음악 목표·타이밍·품질 메타데이터를 바꾸지 않는다.

```json
{
  "local_skills": {
    "schema": "guitar_learning.local_skills.v1",
    "evaluation_gate": "/absolute/path/to/passed_evaluation/local_skill_gate.json"
  }
}
```

probe는 CPU 정책·단일 native 환경에서 순차 후보를 실행한다. 평가도 한 번에 한 native 환경이며 시작 전8GiB, 실행 중6GiB 여유 메모리, case600초·평가 전체3000초 한도를 둔다. 이 값은 실행 자원 보호이며 물리/음악 품질 문턱이 아니다. 기존32개 학습 환경이 동작하는 동안 별도의 대규모 PPO는 추가로 시작하지 않는다.

## 검사와 보관

```bash
python -m unittest \
  guitar_learning.tests.test_local_skill_controls \
  guitar_learning.tests.test_local_skill_probe \
  guitar_learning.tests.test_local_skill_learning \
  guitar_learning.tests.test_local_skill_dispatch -v
```

실패 자료·기준선·중단 기록도 보존한다. 최초 native 탐색의 기록 압축 비용을 줄이기 전 probe와 검사는 [보관본](/home/ajou/yigyu/3/guitar_learning/archive/20261019_before_fast_local_probe)에 있다. gzip 압축 수준과 실행 시간 한도를 조절했으며 음악 성공·물리 조건은 변경하지 않았다. 기존 장기 학습과 두 음 확장 watcher의 봉인 소스는 수정하지 않았다.
