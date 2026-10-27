#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
for count in 1 1024; do
    python -B -u "$phase/contact_probe.py" --variant frictionless_hg --envs "$count" --out "$phase/frictionless_hg_n${count}" > "$phase/frictionless_hg_n${count}.log" 2>&1 || printf "%s\n" "$?" > "$phase/frictionless_hg_n${count}.exitcode"
done
for variant in friction_correlation_small friction_offset_small; do
    python -B -u "$phase/contact_probe.py" --variant "$variant" --envs 1024 --out "$phase/${variant}_n1024" > "$phase/${variant}_n1024.log" 2>&1 || printf "%s\n" "$?" > "$phase/${variant}_n1024.exitcode"
done
