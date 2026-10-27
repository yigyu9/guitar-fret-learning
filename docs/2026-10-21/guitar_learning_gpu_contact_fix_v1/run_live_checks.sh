#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
python -B -u "$phase/check_live_reset.py" --out "$phase/live_reset_v1" > "$phase/live_reset_v1.log" 2>&1
python -B -u "$phase/capture_live.py" --case gpu128_zero --controls 120 --out "$phase/live_gpu128_zero_2s_v1" > "$phase/live_gpu128_zero_2s_v1.log" 2>&1
python -B -u "$phase/capture_live.py" --case gpu1024_zero --controls 120 --out "$phase/live_gpu1024_zero_2s_v1" > "$phase/live_gpu1024_zero_2s_v1.log" 2>&1
