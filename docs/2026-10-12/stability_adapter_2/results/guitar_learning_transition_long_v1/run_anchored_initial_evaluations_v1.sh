#!/usr/bin/env bash
set -eu
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd /home/ajou/yigyu/3
TRANSITION_PHASE=/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1
for CASE_NUMBER in 1 2 3 4; do
  CASE_OUT="$TRANSITION_PHASE/single_a_anchored_init_eval_v${CASE_NUMBER}"
  python -m guitar_learning.transition.anchored_run eval --settings "$TRANSITION_PHASE/single_a_anchored_eval_settings_v1.json" --out "$CASE_OUT" --episodes 1 > "${CASE_OUT}.log" 2>&1
  python - "$CASE_OUT" <<'CHECK'
import json,sys
from pathlib import Path
p=Path(sys.argv[1]); d=json.loads((p/'result.json').read_text())
assert d['completed'] and d['source_unchanged'] and len(d['successful_cases'])==1,d
print('Verified initial policy:',p.name,flush=True)
CHECK
done
