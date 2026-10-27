#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
python -B -u "$phase/inspect_shape_order.py" --out "$phase/native_shape_order_v1" > "$phase/native_shape_order_v1.log" 2>&1
python -B -u "$phase/compound_probe.py" --mode replay --representation flat --closed-loop --envs 128 --steps 2400 --out "$phase/compound_closed_loop_n128_10s_v1" > "$phase/compound_closed_loop_n128_10s_v1.log" 2>&1
