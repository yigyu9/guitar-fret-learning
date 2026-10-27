#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1
export TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_batch_v1
python -B -u -m guitar_learning.train --hand left --device cuda:0 --physics gpu --size large --num-envs 1024 --horizon 32 --updates 2 --out "$phase/n1024_large_v4" > "$phase/n1024_large_v4_console.log" 2>&1
python -B -u -m guitar_learning.train --hand left --device cuda:0 --physics gpu --size large --num-envs 1024 --horizon 32 --updates 1 --resume "$phase/n1024_large_v4/final.pt" --out "$phase/n1024_resume_v1" > "$phase/n1024_resume_v1_console.log" 2>&1
python -B -u -m guitar_learning.train --hand right --device cuda:0 --physics gpu --size small --num-envs 2 --horizon 8 --updates 1 --out "$phase/right_n2_v1" > "$phase/right_n2_v1_console.log" 2>&1
python -B -u -m guitar_learning.train --hand left --device cuda:0 --physics gpu --size medium --num-envs 128 --horizon 32 --updates 2 --out "$phase/n128_default_v1" > "$phase/n128_default_v1_console.log" 2>&1
