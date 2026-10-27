#!/usr/bin/env bash
set -euo pipefail
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python -B - <<'PY_VERIFY_MAIN'
import json
from pathlib import Path
r=json.loads(Path('/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/train1024_large_2000/report.json').read_text())
assert r['completed'] and r['optimizer_updates']==2000 and r['transitions']==65_536_000
PY_VERIFY_MAIN
python -B -u -m guitar_learning.train --hand left --physics gpu --device cuda:0 --size large --num-envs 1024 --horizon 32 --updates 1 --checkpoint-every 50 --resume /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/train1024_large_2000/final.pt --out /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_after_long_1 > /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/resume_after_long_1.log 2>&1
