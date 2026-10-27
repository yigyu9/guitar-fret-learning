#!/usr/bin/env bash
set -euo pipefail
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python -B -u docs/2026-10-21/guitar_learning_gpu_long_training_v2/contact_reset_probe.py --variant baseline > /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v2/contact_baseline.log 2>&1
python -B -u docs/2026-10-21/guitar_learning_gpu_long_training_v2/contact_reset_probe.py --variant aggregate > /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v2/contact_aggregate.log 2>&1
