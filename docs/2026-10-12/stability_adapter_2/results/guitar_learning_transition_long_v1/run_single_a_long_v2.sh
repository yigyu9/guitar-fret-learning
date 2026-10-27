#!/usr/bin/env bash
set -u
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib:${LD_LIBRARY_PATH:-}
export PYTHONFAULTHANDLER=1
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
cd /home/ajou/yigyu/3 || exit 1
TRANSITION_PHASE=/home/ajou/yigyu/3/docs/2026-10-12/stability_adapter_2/results/guitar_learning_transition_long_v1
if ! test -f "$TRANSITION_PHASE/ppo_gate_v1.json"; then exit 2; fi
python -m guitar_learning.transition.train_with_teacher_proof --settings "$TRANSITION_PHASE/single_a_ppo_settings_v1.json" --out "$TRANSITION_PHASE/training_v2" > "$TRANSITION_PHASE/training_v2.log" 2>&1
TRAIN_STATUS=$?
EVAL_STATUS=-1
if test "$TRAIN_STATUS" -eq 0; then
  python -m guitar_learning.transition.evaluate --settings "$TRANSITION_PHASE/single_a_ppo_settings_v1.json" --out "$TRANSITION_PHASE/final_policy_eval_v2" --checkpoint "$TRANSITION_PHASE/training_v2/final.pt" --episodes 4 > "$TRANSITION_PHASE/final_policy_eval_v2.log" 2>&1
  EVAL_STATUS=$?
fi
python - "$TRANSITION_PHASE" "$TRAIN_STATUS" "$EVAL_STATUS" <<'PY'
import json,sys
from pathlib import Path
from datetime import datetime,timezone
p=Path(sys.argv[1])/'launcher_exit_v2.json'
with p.open('x') as f:
 json.dump(dict(train_exit_code=int(sys.argv[2]),eval_exit_code=int(sys.argv[3]),finished_utc=datetime.now(timezone.utc).isoformat(),scope='Launcher exit codes only; consult producer reports for completion, physical audit and musical success'),f,indent=2);f.write('\n')
PY
if test "$TRAIN_STATUS" -ne 0; then exit "$TRAIN_STATUS"; fi
exit "$EVAL_STATUS"
