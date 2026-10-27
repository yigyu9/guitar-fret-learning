#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_original_comparison_v1
python -B -u "$phase/variant_probe.py" --variant cpu_tensor --envs 1 --trace-contacts --out "$phase/contact_trace_n1" --tape "$phase/first16.npz" > "$phase/contact_trace_n1.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant cpu_tensor --trace-contacts --out "$phase/contact_trace_n1024" --tape "$phase/first16.npz" > "$phase/contact_trace_n1024.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant origin_far --envs 1 --out "$phase/origin_far_n1" > "$phase/origin_far_n1.log" 2>&1
python -B -u "$phase/variant_probe.py" --variant indexed_control --out "$phase/indexed_control" > "$phase/indexed_control.log" 2>&1
