#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
for variant in original_guitar_filter no_human_guitar no_human_chair no_guitar_chair no_human_self; do
    for count in 1 1024; do
        python -B -u "$phase/contact_probe.py" --variant "$variant" --envs "$count" --out "$phase/${variant}_n${count}" > "$phase/${variant}_n${count}.log" 2>&1
    done
done
