#!/usr/bin/env bash
set -euo pipefail
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python -B -u -m guitar_learning.train --hand left --physics gpu --device cuda:0 --size large --num-envs 1024 --horizon 32 --updates 2 --checkpoint-every 50 --out /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/aggregate_smoke_2 > /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_training_v3/aggregate_smoke_2.log 2>&1
