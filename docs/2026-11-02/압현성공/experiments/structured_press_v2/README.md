# 정렬 시작 → 오차 확장 → v9 압현 학습 구조 v2

2026-10-31 구현·소규모 실행 검증 완료. 생산 `guitar_learning`과 이전 비교 연구는 보존하고 이 디렉토리의 `runtime` 사본에서 실행한다. [구현 검증](analysis/IMPLEMENTATION.md) · [승인 계획](../../../../plans/press_learning_structure_v2_20261031.md).

직전 단독 검증에서는 사용자 요청에 따라 **검지3번 줄·4프렛 한 목표의 A단계만200회 학습**했다.100회·200회 모델 모두 안전 달성32/32이며, 유지율97.6%로 더 좋은100회 모델을 영상으로 선택했다. [학습 결과·영상·관절 기록](runs/index_s3_f4_A_v1/RESULTS.md). 이 단독 검증에서는 다른 손가락과 B/C로 확장하지 않았다.

후속 약7시간 자율 연구에서는 중지·약지·소지와 B·지원 제거 평가·독립 난수·탐색 폭·실행 방식을 확장했다. 결과·제약·실제 영상은 [추가 연구 보고서](runs/seven_hour_v1/RESEARCH_REPORT.md), 현재 완료 여부는 [진행 상태](runs/seven_hour_v1/progress.json)를 기준으로 읽는다. C50/75/100 승급 학습과 생산 전곡 기본값 변경을 완료했다는 뜻은 아니다.

## 바뀐 흐름

| 단계 | 시작 상태 | 학습 축 | 평가 |
|---|---|---|---|
| A | 실제 물리에서 확인한 정렬 자세 | 목표 손가락 4축 | 팔·나머지 손가락 유지 지원 조건 |
| B | 정렬 주변의 검증된 작은 위치·방향 오차 | 팔12 + 목표 손가락4 | 같은 오차·지원 조건 |
| C50 / C75 / C100 | v9 비중50 / 75 / 100% | 왼팔·손목·왼손33 | 원래 v9·33축·단계 지원 제거 |

목표 손가락은 이동·정렬·압현 모든 구간에서 자유롭다. 정렬 미달을 이유로 손가락에 행동0을 보내지 않는다. 행동0과 정규화 목표각은 단계 전체에서 원래 v9를 기준으로 한다. A의 팔 유지는 별도 실제 적용 목표를 유한 PD로 유지하는 방식이며 실제 관절각을 매 tick 덮어쓰지 않는다.

기존 실제 GPU 물리·자유 기타·중력·제어 한계·9보상·clean 판정·조기 종료·준비3초/목표2.5초/말미0.5초를 유지한다. 단계/타이머/실제 팔 유지 목표/준비 조건44열을 actor·critic에 함께 추가해 상태는601열이다.

## 코드와 결과 위치

| 경로 | 역할 |
|---|---|
| `runtime/guitar_learning/tool/experiments/structured_press.py` | 초기화·행동 권한·단계·정책·PPO·엄격 이전·평가·렌더 |
| `runtime/guitar_learning/tool/experiments/structured_geometry.py` | 팔만 조절한 FK 초기 후보와 도달 가능한 오차 후보 |
| `runtime/guitar_learning/assets/structured_press_v2/catalog.json` | 검증 결과를 붙인 실제 학습 입력. 학습 시작 뒤 수정 금지 |
| `tools/probe_native.py` / `tools/finalize_catalog.py` | GPU 유지 검사, 실제 초기 각도·유지 목표 식별 및 안전 후보 봉인 |
| `tools/run_curriculum.py` | 목표별100회 학습→평가→통과 시 다음 단계. 진행·모델·평가 근거 기록 |
| `geometry/` | CPU 후보와 중지 선접촉 원인 분석. CPU 결과만으로 학습 허용하지 않음 |
| `validation/` / `smoke/` | 검사 기록과 소규모 학습·평가·영상 생성 과정 |
| `video/` | 검증용 정책 영상만. 성공 영상으로 해석하지 않음 |
| `runs/` | 이전 검지 A 단독 결과와 `seven_hour_v1/` 추가 연구. 현재 범위·결론은 추가 연구 보고서 참조 |

중지·약지의 첫 후보에서는 소지가 줄 가까이에 있어 준비 중 오압현이 발생했다. 손가락 각도는 v9 그대로 두고 두 목표의 패드 높이를10→14mm로 조정했다. 약지는 팔 방향도 조정해 소지 패드를 최소14mm 띄웠다. 검지·소지 목표의 초기 각도는 유지했다. 오차 후보 중 선접촉·물리/손목 종료가 있는 것은 B 초기화에서 제외한다. 따라서 실제 사용 분포는 전체 ±10mm/±5도 상자의 균일 표본이 아니다.

## 실행 환경

이 PC의 `rl38` 환경에서 실행한다. 아래 환경을 준비한 뒤 같은 터미널에서 명령을 사용한다.

```bash
cd /home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runtime
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONPATH="$PWD:/home/ajou/yigyu/3/isaacgym/python"
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export TORCH_EXTENSIONS_DIR=/home/ajou/yigyu/3/docs/2026-11-02/압현성공/process/cache/torch
```

검지 A만100회 실행:

```bash
python -B -X utf8 -m guitar_learning.tool.experiments.structured_press train \
  --geometry "$PWD/guitar_learning/assets/structured_press_v2/catalog.json" \
  --song virtual_finger_v9_index_s3_f4 --stage A \
  --size large --num-envs 64 --updates 100 --seed 7 \
  --out "$PWD/../runs/index_A_100"
```

대표4목표의 자동 교육과정 실행:

```bash
python -B -X utf8 ../tools/run_curriculum.py --out "$PWD/../runs/curriculum_seed7"
```

목표별 A/B 각각 최대300회, C는 비율마다300회다.100회마다32환경 평가에서 A≥24회, B≥22회·실패≤1회, C≥16회·실패≤1회를 서로 다른 checkpoint로 연속2회 통과해야 다음 단계로 간다. C 승급은 지원 없는 v9 평가를 사용한다. 막힌 목표를 무한 연장하지 않는다. 실행 상태는 지정 출력의 `progress.json`, 각 블록의 로그·보고서·체크포인트에 남는다. 같은 출력으로 다시 실행하면 완료 블록의 근거를 확인하고 이어가며, 실패한 부분 실행은 덮어쓰지 않는다.

저장본의 원래 단계 평가·영상은 `evaluate` / `render --checkpoint 절대경로 --num-envs 4 --out 새절대경로`로 실행한다. 원래 v9·전체33축·팔 지원 제거 평가는 `evaluate-free-v9 --checkpoint 절대경로 --num-envs 32 --out 새절대경로`다. 출력은 이 연구의 `runs`, `smoke`, `rendering`, `validation` 아래에 둔다.

단계 변경은 `--initialize-from 이전/J/final.pt`로 가중치만 명시적으로 이전한다. 같은 단계 추가100회는 `--resume 이전/J/final.pt --updates 100`이며 새 출력이 필요하다. 입력·모델 SHA와 원래 계약을 엄격 검증하고 optimizer 재개와 단계 이전을 구분한다.

## 해석 범위

실행 검증은 학습 성공과 다르다. A/B는 지원 조건의 기술 진단이며 정식 J33 성과가 아니다. 최종 채택에는 도움 없는 v9 성공, 새 seed17 재현, 같은 총 학습 예산의 J33 대조군, 실제 손가락 굽힘·오압현·자연스러움의 영상 확인이 추가로 필요하다.
