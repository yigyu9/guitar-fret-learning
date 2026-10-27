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
    python -B -u "$phase/compound_probe.py" --mode replay --representation flat --envs "$count" --tape /home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_force_replay_v1/reference_n1/tape.npz --out "$phase/compound_replay_n${count}_v3" > "$phase/compound_replay_n${count}_v3.log" 2>&1 || printf "%s\n" "$?" > "$phase/compound_replay_n${count}_v3.exitcode"
done
