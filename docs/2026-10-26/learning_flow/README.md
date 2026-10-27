# 기본 왼손 finger-skill 학습 흐름

현재 `python -m guitar_learning.train`은 GPU 왼손 finger-skill v2(v25)를 실행한다. `--learning-family finger-skill`은 생략해도 같다. 기존 song·CPU·오른손·v24는 별도 도구로 분리했다. 이 문서는 실행과 저장 흐름을 설명하며, 이번 정리에서 새 학습을 수행했다는 뜻은 아니다.

## 실행 명령

```bash
cd /home/ajou/yigyu/3
conda activate rl38
export PYTHONPATH="$PWD/isaacgym/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}

python -m guitar_learning.train \
  --song 05_BN2-131-B_solo \
  --size large --num-envs 1024 --horizon 32 --updates 3000 \
  --checkpoint-every 250 --seed 7 \
  --out /home/ajou/yigyu/3/runs/left_finger_skill_default_01
```

`--out`은 새 경로여야 한다. 손·장치·family 기본값은 left·cuda:0·finger-skill이다. 물리 기본 `auto`는 이 경로에서 GPU를 선택하며, 크기·환경 수·반복 기본값은 medium·128·100이다. CPU fallback은 없다. 위 3000회 예산은 98,304,000전이이며 실행 시간이나 곡 성공 횟수를 보장하지 않는다.

## 호출되는 코드와 초기화

| 순서 | 파일 | 역할 |
| --- | --- | --- |
| 1 | [train.py](/home/ajou/yigyu/3/guitar_learning/train.py) | 사용자 진입점 |
| 2 | [training/start.py](/home/ajou/yigyu/3/guitar_learning/training/start.py) | 왼손 GPU v2 옵션 확인·직접 runner 호출 |
| 3 | [training/launch_settings.py](/home/ajou/yigyu/3/guitar_learning/training/launch_settings.py) | 곡 입력·설정·계약 생성 |
| 4 | [training/finger_skill_runner.py](/home/ajou/yigyu/3/guitar_learning/training/finger_skill_runner.py) | 입력 봉인·새 모델 또는 엄격 재개·학습과 저장 |
| 5 | [training/gpu_pool.py](/home/ajou/yigyu/3/guitar_learning/training/gpu_pool.py) | 하나의 GPU simulator에 여러 환경 생성 |
| 6 | [gpu/simplified_finger_environment.py](/home/ajou/yigyu/3/guitar_learning/gpu/simplified_finger_environment.py) | 561상태·9개 보상·물리/손목 종료 |
| 7 | [skills/finger_skill_policy.py](/home/ajou/yigyu/3/guitar_learning/skills/finger_skill_policy.py) | 지지17·손가락16을 함께 학습하는 J33 정책 |
| 8 | [training/finger_decisions.py](/home/ajou/yigyu/3/guitar_learning/training/finger_decisions.py) · [decision_ppo.py](/home/ajou/yigyu/3/guitar_learning/training/decision_ppo.py) | K1 결정 수집·PPO 갱신 |

각 환경은 합의한 035/v14 초기 상태에서 시작한다. native 대기 없이 첫 tick부터 정책 행동·물리·보상·종료를 계산한다. Root 고정·하체 유한 제어, 자유 기타·중력 ON·스트랩 OFF를 유지한다. 왼팔·손목·손가락 33축을 함께 학습하고 오른손 6축 행동은 0이다. 전문가·BC·R/F 단계 통과는 요구하지 않는다.

물리는 240Hz, 정책은 60Hz다. 한 정책 행동으로 물리 4단계를 진행하며, 독립 K1은 매 정책 tick에 새 행동을 결정한다. 손가락은 native 전체 범위·목표 변화율 4rad/s·기존 PD/힘 상한을 유지하고 직접 움직임 비용은 0이다. 움직임 비용 0이 대기·엄지·음악 목표의 정책 영향을 없애는 것은 아니다.

## 구간에서 전곡으로

새 실행의 원래 예산 `updates × horizon × num_envs`와 그 25% 문턱을 저장한다. 처음에는 선택된 곡 구간을 학습하며, 누적 committed 전이가 문턱에 도달하면 이후 초기화되는 환경부터 전곡을 사용한다. 이미 진행 중인 구간은 원래 끝/실패까지 이어간다. 따라서 정확히 25%의 전이가 구간이고 나머지가 전곡이라는 뜻은 아니다. 실제 비율은 로그의 `exposure_transitions`에서 확인한다.

전곡은 원곡 67음·정책 준비 3초·말미 0.5초를 포함하며 1969 control tick, 약 32.8167초다. 구간의 분모와 종료 시간은 선택된 구간을 따른다. 실패·부분 구간을 전곡 성공으로 세지 않는다. 재개는 원래 예산·문턱과 누적 노출을 복원하고 추가 반복 수로 문턱을 재설정하지 않는다.

## 한 번의 학습 반복

1. H32 정책 tick을 각 환경에서 수집한다. 1024환경이면 반복당 32,768전이다.
2. 각 tick의 물리 표본으로 접촉·보상·종료를 계산한다. 끝난 환경의 종료 관측·원장을 먼저 기록하고 그 환경만 초기화한다.
3. H32 수집 자료로 PPO를 갱신한다. reward/cost를 결합한 advantage와 고정 비용 가중치 1을 쓴다.
4. 갱신에 반영한 자료를 committed로 기록하고, 누적 노출과 다음 reset의 구간/전곡 선택을 갱신한다.
5. 반복 로그·주기 checkpoint를 저장한 뒤 다음 H32를 수집한다.

H32는 약 0.533초 수집 경계이며 에피소드 종료가 아니다. 이 경계에서 장면·곡 시계·음별 예산·손목 타이머·손가락 제어 목표를 지우지 않는다. 오류로 PPO에 반영하지 못한 부분 수집은 discarded로 구분한다.

## 보상과 조기 종료

9개 항은 **목표 패드 접근, 최초 접촉, 압현 유지, 압현 달성, 오압현, 음 수행 부족, 대기 자세, 엄지 안내, 행동 변화**다. 이번 기본 경로 전환에서는 수식·계수·측정·오압현 판정을 바꾸지 않았다. [현재 보상·종료 문서](/home/ajou/yigyu/3/docs/2026-10-26/왼손보상구조/12_v25보상단순화와종료.md)에 지급 시점과 계산식이 있다.

손목은 안내 영역 밖 3cm 초과의 순누적 시간이 1.5초에 도달하면 종료하고, 2cm 이내에서 이탈 상태를 해제한다. 초기 3초는 일반 조건의 유예이며, 10cm 이상 심각 이탈이 0.10초 지속되는 조건은 유예 중에도 적용한다. 240Hz로 타이머를 측정하고 60Hz 경계에서 종료한다. 기존 기타 이탈·회전·접지·제어 무효 등의 물리 종료 문턱은 유지한다.

물리 또는 손목 실패 비용은 한 번만 `5 + 2 × 남은 로컬 시간(초) + 남은 미관측 음 감점 예산`이다. 두 실패가 겹쳐도 중복 지급하지 않는다. 실패한 환경만 reset하며 소스 변조·비유한 값·입력 계약·자원/저장 오류는 실행 자체의 중단 사유로 구분한다.

## 저장 위치와 항목별 분석

최상위 출력에는 `settings.json`, `report.json`이 있고, 실제 공동 학습 결과는 `J/` 아래에 있다.

| 파일 | 확인할 내용 |
| --- | --- |
| `J/initial.pt`, `J/final.pt` | 시작·최종 모델·optimizer·난수·학습 진행 |
| `J/checkpoint_*.pt` | 지정 간격의 중간 저장본; 마지막 반복은 final로 저장 |
| `J/failure_last_valid.pt` | 오류 시 유효 복구 상태를 저장할 수 있을 때만 생성 |
| `J/learning_metrics.jsonl` | 반복별 PPO, `reward_component_means`, 구간/전곡 실제 노출 수 |
| `J/episodes.jsonl` | 종료 에피소드의 항목별 누적 보상·비용·음별 수행 원장 |
| `J/episode_metadata.json` | 에피소드 공통 메타데이터; 종료 에피소드가 생긴 뒤 생성 |
| `J/transitions.jsonl.gz`, `J/decisions.jsonl.gz` | 제어·결정별 합산 보상/비용과 학습 반영 상태 |
| `J/checkpoint_manifest.jsonl` | 저장본 크기·SHA·시점 |
| `J/inputs_before.json`, `J/training_contract.json` | 원본 입력 SHA·실제 실행 계약 |
| `J/status.json`, `J/resources.jsonl`, `J/events.jsonl` | 진행·자원·사건 기록 |
| `J/report.json`, `J/gpu_scene_initial.json`, `J/gpu_scene_final.json` | 학습 완료·소스/장면 종료 감사 |

`reward_component_means`는 해당 반복의 모든 환경·control 전이에 대한 평균이다. 에피소드 `reward_components`는 초기화부터 종료까지 항목별 누적값이며 실패 비용은 `cost_components`로 분리한다. 매 60Hz 시점의 기록은 합산값이므로 개별 환경의 시간별 9항목 곡선을 그대로 재구성할 수는 없다.

학습 완료 여부는 최상위와 `J/report.json`을 함께 확인한다. 완료는 실행 계약·저장·종료 검사를 뜻하며 연주 수렴을 의미하지 않는다. checkpoint만 생긴 상태나 수집된 전이 수만으로 학습 반영·전곡 성과를 추정하지 않는다.

## 재개·평가·영상과 이전 실행

[현행 README](/home/ajou/yigyu/3/guitar_learning/README.md)에 `J/final.pt`를 사용하는 재개·전곡 평가·손/전신 영상 명령이 있다. 같은 소스·자산·전체 계약끼리 엄격히 복원하며, 물리 장면은 초기 자세의 새 에피소드로 시작한다. 이번 경로 정리 이전 checkpoint는 소스 SHA 차이로 재개·평가·렌더가 거부될 수 있다. 검사 완화나 자동 모델 이전은 하지 않는다.

기존 song·오른손·CPU·v24는 [별도 도구](/home/ajou/yigyu/3/guitar_learning/tool/README.md)의 `tool.training.train_legacy`에서 실행한다. 변경 전 긴 실행 이력·문서는 [이전 학습 흐름](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/docs/2026-10-26/learning_flow/README.md)과 [보관 manifest](/home/ajou/yigyu/3/guitar_learning/archive/20261026_before_finger_skill_default/manifest.json)에 보존했다. 이전 봉인 결과는 수정하지 않으며 새 기본 구조의 성능으로 상속하지 않는다.

2026-10-27 손목 종료v2: 활성 상태에서 안내 상자 밖 추가2~3cm 복귀 구간은 누적 시간을 초당1초 차감하고,2cm 이내에서 초기화한다. 일반 종료1.5초는 연속 이탈이 아니라 위 규칙의 순누적 시간이다. 영역 크기·심각이탈·물리 기준·실패 비용은 유지한다. [보정 검증](/home/ajou/yigyu/3/docs/2026-10-27/guitar_learning_wrist_recovery_v2/README.md).
