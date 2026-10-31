# 독립 seed17 fresh 분산 실험

봉인된 runtime과 기존 entry는 변경하지 않는다. 새 외부 bootstrap은 학습 완료 후 감사에서 비교할 `CONTROL`만 원본 seed17 initial.pt로 지정한다. 정책·설정·물리·난수 상태는 변경하지 않는다. 원본 checkpoint와 bootstrap은 입력으로 봉인하고 checkpoint 생성 계보로 기록한다. 재개 시점의 실제 model·두 Adam·업데이트·모든 저장 RNG도 기존 native 감사가 검증한다.

최초 import는 Isaac Gym → nested 경로 보정 → fresh entry 순서다. seed17을 명시하지 않으면 거부한다. A 가중치 이전은 없다. 모든 출력 경로는 새 경로여야 한다. 아래 명령은 검수 후 주 실행자가 GPU에서 수행한다.

```bash
study_dir=/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1
seed17_dir="$study_dir/fresh_variance_variant/seed17"
study_python=/home/ajou/miniconda3/envs/rl38/bin/python
cd "$study_dir/fresh_variance_variant/runtime"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap.py" train --seed 17 --updates 100 --out "$seed17_dir/100/train"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap.py" evaluate --seed 17 --checkpoint "$seed17_dir/100/train/J/final.pt" --out "$seed17_dir/100/evaluate_final"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap.py" train --seed 17 --updates 100 --resume "$seed17_dir/100/train/J/final.pt" --out "$seed17_dir/200/train"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap.py" evaluate --seed 17 --checkpoint "$seed17_dir/200/train/J/final.pt" --out "$seed17_dir/200/evaluate_final"
```

선택 초기 평가는 같은 evaluate 명령에 `100/train/J/initial.pt`와 `100/evaluate_initial`을 사용한다. 공식 평가는 latent-mean 결정 실행의 최초32환경이며 실패도 분모에 포함한다. variant 공식 평가는 q/hold32를 별도 캡처하지 않으므로 실제 초기 물리 상태 행별 exact 대응이라고 표현하지 않는다. 원본 seed17과 실제 초기 전체 모델/RNG 및 설정이 같은지 별도로 확인한다.

집계는 상위 `FRESH_VARIANCE_SEED17_ANALYSIS.py`를 CPU에서 실행한다. 자료/초기/재개 증거가 부족하면 효과 판단을 보류한다. bootstrap과 기존 helper를 수정하면 기존 입력 봉인이 달라지므로 검수·실행 후 편집을 멈춘다.
