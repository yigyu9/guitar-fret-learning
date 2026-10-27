#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
runtime=/home/ajou/miniconda3/envs/rl38
export PATH="$runtime/bin:$PATH"
export TORCH_EXTENSIONS_DIR=/tmp/strike_live_guitar_torch_extensions
export PYTHONPATH="$project_dir/isaacgym/python:$project_dir"
export LD_LIBRARY_PATH="$runtime/lib"
export VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/lvp_icd.x86_64.json
export MUJOCO_GL=disable OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
cd "$project_dir"
exec "$runtime/bin/python" -X faulthandler -m stability_adapter_2.run_live_fret_diagnostic "$@"
