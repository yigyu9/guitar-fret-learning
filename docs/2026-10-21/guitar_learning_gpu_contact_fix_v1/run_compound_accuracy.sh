#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
python -B -u "$phase/solver_probe.py" --position-iterations 8 --mode replay --representation flat --closed-loop --no-proxy-collision --envs 1024 --steps 480 --out "$phase/flat89_iterations8_n1024_2s_v1" > "$phase/flat89_iterations8_n1024_2s_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/flat89_iterations8_n1024_2s_v1.exitcode"
python -B -u "$phase/solver_probe.py" --substeps 2 --mode replay --representation flat --closed-loop --no-proxy-collision --envs 1024 --steps 480 --out "$phase/flat89_substeps2_n1024_2s_v1" > "$phase/flat89_substeps2_n1024_2s_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/flat89_substeps2_n1024_2s_v1.exitcode"
