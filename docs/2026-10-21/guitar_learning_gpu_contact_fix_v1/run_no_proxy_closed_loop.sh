#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
for representation in original flat; do
    python -B -u "$phase/compound_probe.py" --mode replay --representation "$representation" --closed-loop --no-proxy-collision --envs 1024 --steps 480 --out "$phase/${representation}_no_proxy_closed_loop_n1024_v1" > "$phase/${representation}_no_proxy_closed_loop_n1024_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/${representation}_no_proxy_closed_loop_n1024_v1.exitcode"
done
python -B -u "$phase/compound_probe.py" --mode replay --representation flat --closed-loop --no-proxy-collision --envs 128 --steps 2400 --out "$phase/flat_no_proxy_closed_loop_n128_10s_v1" > "$phase/flat_no_proxy_closed_loop_n128_10s_v1.log" 2>&1 || printf "%s\n" "$?" > "$phase/flat_no_proxy_closed_loop_n128_10s_v1.exitcode"
