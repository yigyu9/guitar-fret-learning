# seed17 v2 실행 경로

기존 `fresh_variance_variant/seed17`의 첫 시도는 입력 핀 단계에서 경로를 재접두하여 실패했다. 그 자료·원본 bootstrap은 보존한다. 학습 전이0인 준비 실패이며 모델 성능 실패로 집계하지 않는다.

v2는 이미 허용된 `variant/runs` 아래에 bootstrap·출력·감사 CP 사본을 둔다. `control_initial.pt`는 원본 `full33_seed17/100/train/J/initial.pt`의 바이트 동일 복사이며 가중치 이전 입력이 아니다. 종료 후 감사 비교에만 사용한다. 원본/사본 SHA를 전후 확인한다. 정책·설정·RNG 소비는 기존 fresh entry가 수행하며 변경하지 않는다.

GPU 실행 전 CPU 검사에서 실제 예정 settings 경로와 bootstrap·감사 CP에 대해 native resolver, sha, pin 및 checkpoint_inputs의 settings snapshot/creation lineage가 모두 통과했다. 검사용 출력 디렉토리는 제거했다. 최초 Isaac Gym import와 nested 경로 context, 정상/예외 factory 복구도 확인했다.

```bash
study_dir=/home/ajou/yigyu/3/docs/2026-11-02/압현성공/experiments/structured_press_v2/runs/seven_hour_v1
seed17_dir="$study_dir/fresh_variance_variant/runs/seed17"
study_python=/home/ajou/miniconda3/envs/rl38/bin/python
cd "$study_dir/fresh_variance_variant/runtime"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap_v2.py" train --seed 17 --updates 100 --out "$seed17_dir/100/train"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap_v2.py" evaluate --seed 17 --checkpoint "$seed17_dir/100/train/J/final.pt" --out "$seed17_dir/100/evaluate_final"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap_v2.py" train --seed 17 --updates 100 --resume "$seed17_dir/100/train/J/final.pt" --out "$seed17_dir/200/train"
PYTHONPATH="$PWD" "$study_python" -B "$seed17_dir/bootstrap_v2.py" evaluate --seed 17 --checkpoint "$seed17_dir/200/train/J/final.pt" --out "$seed17_dir/200/evaluate_final"
```

검수 후 주 실행자가 GPU에서 실행한다. optional initial 평가는 `100/train/J/initial.pt`를 `100/evaluate_initial`로 평가한다. 기존 봉인 runtime/helper와 첫 시도는 수정하지 않는다. 상위 `FRESH_VARIANCE_SEED17_ANALYSIS.py`가 원본 seed17과 초기 모델/전체 RNG, strict 재개 및 원시32 실패 포함 결과를 검증한다.
