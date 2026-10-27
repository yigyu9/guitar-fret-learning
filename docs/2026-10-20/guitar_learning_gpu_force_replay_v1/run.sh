#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_force_replay_v1
python -B -u "$phase/probe.py" --out "$phase/reference_n1" --steps 128 > "$phase/reference_n1.log" 2>&1
python -B -u "$phase/probe.py" --out "$phase/replay_n1" --envs 1 --tape "$phase/reference_n1/tape.npz" > "$phase/replay_n1.log" 2>&1
python -B -u "$phase/probe.py" --out "$phase/replay_n1024" --envs 1024 --tape "$phase/reference_n1/tape.npz" > "$phase/replay_n1024.log" 2>&1
