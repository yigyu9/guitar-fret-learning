#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
for width in 0.5 0.1; do
    python -B -u "$phase/compound_probe.py" --mode replay --representation flat --closed-loop --envs 1024 --steps 480 --spacing "$width" --out "$phase/compound_closed_loop_spacing${width}_n1024_v1" > "$phase/compound_closed_loop_spacing${width}_n1024_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/compound_closed_loop_spacing${width}_n1024_v1.exitcode"
done
python -B -u "$phase/compound_probe.py" --mode replay --representation original --closed-loop --envs 1024 --steps 480 --spacing 0.1 --out "$phase/original_closed_loop_spacing0.1_n1024_v1" > "$phase/original_closed_loop_spacing0.1_n1024_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/original_closed_loop_spacing0.1_n1024_v1.exitcode"
