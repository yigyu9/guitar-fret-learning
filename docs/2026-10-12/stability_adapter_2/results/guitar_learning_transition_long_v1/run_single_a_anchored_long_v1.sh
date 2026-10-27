#!/usr/bin/env bash
set -eu
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd /home/ajou/yigyu/3
TRANSITION_PHASE=/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1
set +e
python -m guitar_learning.transition.anchored_run train --settings "$TRANSITION_PHASE/single_a_anchored_ppo_settings_v1.json" --out "$TRANSITION_PHASE/anchored_training_v1" > "$TRANSITION_PHASE/anchored_training_v1.log" 2>&1
TRAIN_STATUS=$?
EVAL_STATUS=-1
if test "$TRAIN_STATUS" -eq 0; then
  EVAL_STATUS=0
  for CASE_NUMBER in 1 2 3 4; do
    CASE_OUT="$TRANSITION_PHASE/anchored_final_eval_v${CASE_NUMBER}"
    python -m guitar_learning.transition.anchored_run eval --settings "$TRANSITION_PHASE/single_a_anchored_ppo_settings_v1.json" --out "$CASE_OUT" --checkpoint "$TRANSITION_PHASE/anchored_training_v1/final.pt" --episodes 1 > "${CASE_OUT}.log" 2>&1
    EVAL_STATUS=$?
    if test "$EVAL_STATUS" -ne 0; then break; fi
  done
fi
python - "$TRANSITION_PHASE" "$TRAIN_STATUS" "$EVAL_STATUS" <<'RECORD'
import json,sys
from pathlib import Path
from datetime import datetime,timezone
with (Path(sys.argv[1])/'anchored_launcher_exit_v1.json').open('x') as f:
 json.dump(dict(train_exit_code=int(sys.argv[2]),evaluation_process_exit_code=int(sys.argv[3]),finished_utc=datetime.now(timezone.utc).isoformat(),scope='Process exit codes only. Inspect producer reports for success; exit0 does not imply musical success.'),f,indent=2);f.write('\n')
RECORD
if test "$TRAIN_STATUS" -ne 0; then exit "$TRAIN_STATUS"; fi
exit "$EVAL_STATUS"
