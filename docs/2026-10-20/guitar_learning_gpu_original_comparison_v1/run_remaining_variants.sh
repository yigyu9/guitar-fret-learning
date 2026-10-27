#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_original_comparison_v1
python -B -u "$phase/variant_probe.py" --variant no_contact --envs 1 --out "$phase/no_contact_n1" > "$phase/no_contact_n1.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant no_contact --out "$phase/no_contact_n1024" > "$phase/no_contact_n1024.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant cpu_physics --envs 1 --out "$phase/cpu_physics_n1" > "$phase/cpu_physics_n1.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant cpu_physics --out "$phase/cpu_physics_n1024" > "$phase/cpu_physics_n1024.log" 2>&1
