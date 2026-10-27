#!/usr/bin/env bash
set -eu
cd /home/ajou/yigyu/3
export PATH=/home/ajou/miniconda3/envs/rl38/bin:$PATH
export PYTHONDONTWRITEBYTECODE=1 TORCH_EXTENSIONS_DIR=/tmp/guitar_structure_torch_extensions
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
export PYTHONPATH=/home/ajou/yigyu/3/isaacgym/python:/home/ajou/yigyu/3
export LD_LIBRARY_PATH=/home/ajou/miniconda3/envs/rl38/lib
phase=/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1
python - <<'INNER'
from pathlib import Path
import numpy as np
p=Path('/home/ajou/yigyu/3/docs/2026-10-21/guitar_learning_gpu_contact_fix_v1')
a=np.load(str(p/'original_cpu_reference_480_v1/tape.npz'))
np.savez_compressed(str(p/'original_cpu_first128.npz'),**{k:a[k][:128] for k in ('targets','efforts')})
INNER
for count in 1 1024; do
    python -B -u /home/ajou/yigyu/3/docs/2026-10-20/guitar_learning_gpu_original_comparison_v1/variant_probe.py --variant cpu_physics --envs "$count" --tape "$phase/original_cpu_first128.npz" --out "$phase/cpu_own_tape_physics_n${count}" > "$phase/cpu_own_tape_physics_n${count}.log" 2>&1 || printf "%s\n" "$?" > "$phase/cpu_own_tape_physics_n${count}.exitcode"
done
