# 재현과 파일 역할

모든 작업은 이 독립 복사본의 프로젝트 루트에서 수행한다. 실행 전 원래 `보존/study_seal.json`·`artifact_manifest.json` 검증이 통과해야 한다. 아래 분석은 기존 원문을 읽고 `로그분석/`의 파생 자료만 다시 생성한다. 기존 모델·평가·입력 SHA/identity를 바꾸지 않는다.

```bash
cd /home/yigyu/local-research/index_middle_transition_20261101_v1/project
PY=/home/yigyu/miniconda3/envs/rl38/bin/python
L=docs/2026-11-02/손가락전환실험/로그분석
export PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
"$PY" -X utf8 "$L/tools/identity_integrity.py"
"$PY" -X utf8 "$L/tools/learning.py"
"$PY" -X utf8 "$L/tools/analyze_raw.py"
"$PY" -X utf8 "$L/tools/trajectory.py"
"$PY" -X utf8 "$L/tools/axis_stats.py"
"$PY" -X utf8 "$L/tools/saturation.py"
"$PY" -X utf8 "$L/tools/potential_check.py"
"$PY" -X utf8 "$L/tools/finish_analysis.py"
"$PY" -X utf8 "$L/tools/extra_figures.py"
"$PY" -X utf8 -m unittest discover -s "$L/tests" -p 'test_*.py' -v
"$PY" -X utf8 -m unittest guitar_learning.tests.test_natural_preparation guitar_learning.tests.test_simplified_wrong_press guitar_learning.tests.test_gpu_press_surface -v
```

새 GPU 평가를 원하면 기존 `runs/` 이름을 재사용하지 않는다. GPU 비점유·동일 소스/입력·동일 모델 SHA를 검증한 뒤 새 출력명을 사용해야 한다. 아래 예시는 seed17/200회의 mean32 첫32episode이며 모델에서 seed/RNG를 엄격 복원한다. --seed를 다른 값으로 억지 바꾸지 않는다. 128환경은 --num-envs와 출력명만 변경한다. 최초6회 실행은 `tools/repeat.py`, `logs/repeat.log`, 실행별 로그와 `status.json`에 남아 있다. 이 runner는 기존 출력이 있으면 중단하므로 완료된 실험 위에 재실행하지 않는다.

```bash
"$PY" scripts/tab2body.py --cache-root /home/yigyu/.cache/tab2body run -u \
  "$L/tools/observe_evaluate.py" evaluate \
  --checkpoint docs/2026-11-02/손가락전환실험/모델/base_seed17_u200/J/final.pt \
  --action-mode mean --num-envs 32 --out "$L/runs/NEW_UNIQUE_mean32"
```

`tools/`는 관찰·분석 코드, `tests/`는 CPU 검사, `runs/`는 새 평가 원문, `logs/`는 실행/검사 기록, `tables/`는 비교 표, `figures/`는 그래프다. 원본9항 보상은 지급 자체이고 counter_delta는 float32 누적 차이이므로 서로 바꾸지 않는다. `analysis_ledger.json`은 원문 파일 SHA, `identity_integrity.json`은 원래 source/artifact 보존과 평가별 설정·입력 식별, `output_manifest.json`은 이번 분석 산출물 SHA를 가진다.

학습코드 변경안은 구현하지 않았다. 후속안은 REPORT.md의 최대3개 조건이며 현재 공유 기본 동작이나 기존 체크포인트의 계약을 바꾸지 않는다.
