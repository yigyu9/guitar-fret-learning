"""Preserve v19 500/final3000 fixed evaluations before installing new sources."""
import importlib.util
from pathlib import Path
import sys

PHASE = Path(__file__).resolve().parents[1]
ROOT = PHASE.parents[2]
path = ROOT/'docs/2026-10-25/guitar_learning_long_training_v19_3000/support/evaluate_checkpoints.py'
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location('preserved_v19_evaluator', path)
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)
evaluator.CHECKPOINT_UPDATES = (500, 3000)
sys.argv = [str(path), '--out', str(PHASE/'baseline_v19'), '--checkpoints', '500', '3000']
evaluator.main()
