"""Unassisted native reproduction using the common finalized capture probe."""
import argparse
import json
import os
from pathlib import Path


def evaluate(settings,args):
    from guitar_learning.tool.experiments.transition.probe import run
    args.controller='policy'
    return run(settings,args)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,required=True);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--checkpoint',type=Path)
    parser.add_argument('--episodes',type=int,default=1)
    args=parser.parse_args()
    for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='1'
    import isaacgym
    from guitar_learning.tool.experiments.transition.train import settings_document
    evaluate(settings_document(json.loads(args.settings.read_text())),args)


if __name__=='__main__':main()
