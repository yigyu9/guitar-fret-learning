#!/usr/bin/env bash
set -euo pipefail
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3${PYTHONPATH:+:$PYTHONPATH}
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
python -B -u -m guitar_learning.train --hand left --physics gpu --device cuda:0 --size large --num-envs 512 --horizon 32 --updates 1 --checkpoint-every 50 --resume /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/train512_large_128_v5/failure_last_valid.pt --out /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/resume512_after_inspection > /home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_long_run_check_v1/resume512_after_inspection.log 2>&1
