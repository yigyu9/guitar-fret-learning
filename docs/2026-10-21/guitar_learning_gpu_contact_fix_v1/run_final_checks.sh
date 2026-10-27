#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
python -B -u "$phase/check_live_reset.py" --out "$phase/live_reset_final" > "$phase/live_reset_final.log" 2>&1
python -B -u "$phase/capture_live.py" --case gpu128_zero --controls 120 --out "$phase/live_gpu128_zero_2s_final" > "$phase/live_gpu128_zero_2s_final.log" 2>&1
python -B -u "$phase/capture_live.py" --case gpu1024_zero --controls 120 --out "$phase/live_gpu1024_zero_2s_final" > "$phase/live_gpu1024_zero_2s_final.log" 2>&1
python -B -u -m guitar_learning.train --hand left --physics gpu --device cuda:0 --num-envs 128 --horizon 32 --updates 2 --size medium --out "$phase/train128_final" > "$phase/train128_final.log" 2>&1
python -B -u -m guitar_learning.train --hand left --physics gpu --device cuda:0 --num-envs 128 --horizon 32 --updates 1 --size medium --resume "$phase/train128_final/checkpoint.pt" --out "$phase/resume128_final" > "$phase/resume128_final.log" 2>&1
