#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_original_comparison_v1
python -B -u "$phase/variant_probe.py" --variant flat_state --out "$phase/flat_state" > "$phase/flat_state.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant import_human --out "$phase/import_human" > "$phase/import_human.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant cpu_tensor --out "$phase/cpu_tensor" > "$phase/cpu_tensor.log" 2>&1
