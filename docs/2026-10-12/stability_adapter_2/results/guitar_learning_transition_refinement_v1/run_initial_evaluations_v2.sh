#!/usr/bin/env bash
set -eu
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd /home/ajou/yigyu/3
REFINEMENT_PHASE=/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_refinement_v1
for CASE_NUMBER in 2 3 4 5; do
 CASE_OUT="$REFINEMENT_PHASE/native_init_v${CASE_NUMBER}"
 gdb -q -batch -x "$REFINEMENT_PHASE/gdb_supervisor_v1.gdb" --args python -m guitar_learning.transition_refinement.run eval --settings /home/ajou/yigyu/3/guitar_learning/transition_refinement/configs/baseline_eval.json --out "$CASE_OUT" --episodes 1 > "${CASE_OUT}.log" 2>&1
 python - "$CASE_OUT" <<'CHECK'
from pathlib import Path
import json,sys
p=Path(sys.argv[1]);d=json.loads((p/'result.json').read_text())
assert d['completed'] and d['source_unchanged'] and len(d['successful_cases'])==1,d
print('Verified initial policy',p.name,flush=True)
CHECK
done
