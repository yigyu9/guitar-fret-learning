"""Explicit E4 preparation condition; all physical control stays inherited."""
from pathlib import Path
import sys

BASE = Path(__file__).resolve().parents[2]/'학습_인접2지_v1'
sys.path.insert(0, str(BASE/'도구'))
from pair_environment import PairEnvironment


class ImprovedPairEnvironment(PairEnvironment):
    natural_preparation = dict(schema='guitar_learning.natural_preparation.v3', condition='E4')
