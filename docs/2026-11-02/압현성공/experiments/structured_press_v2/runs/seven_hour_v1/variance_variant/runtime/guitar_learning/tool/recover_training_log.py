"""Summarize a CRC-verified log prefix into a new directory; never resume PPO."""
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import hashlib
import json
from guitar_learning.training.training_log_io import write
from guitar_learning.training.training_log_io import iter_transitions
from guitar_learning.training.training_metrics import LearningMetrics


def recover(run, out):
    run, out = Path(run).resolve(), Path(out).resolve()
    path = run/'transitions.jsonl.gz'
    if not path.is_file():raise FileNotFoundError(str(path))
    settings_path = run/'settings.json'
    settings = json.loads(settings_path.read_text()) if settings_path.is_file() else {}
    out.mkdir(parents=True, exist_ok=False)
    metrics, diagnostics = LearningMetrics(settings), {}
    with (out/'episodes.jsonl').open('x') as stream:
        for row in iter_transitions(path, strict=False, diagnostics=diagnostics):
            closed=metrics.observe(row)
            for episode in closed:
                stream.write(json.dumps(episode, allow_nan=False)+'\n')
            if closed:metrics.update_summary()
        for episode in metrics.close_incomplete('recovered_prefix_end'):
            stream.write(json.dumps(episode, allow_nan=False)+'\n')
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):digest.update(chunk)
    report_path = run/'report.json'
    original_accounting = json.loads(report_path.read_text()).get('accounting') if report_path.is_file() else None
    result = dict(schema='guitar_learning.recovered_log.v1', source=str(path), source_sha256=digest.hexdigest(),
        recovery=diagnostics, measured_prefix=metrics.summary(), original_run_accounting=original_accounting,
        scope='verified completed gzip members only; no inferred PPO commit, checkpoint validity or music success for incomplete episodes')
    write(out/'recovered_summary.json', result)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args=parser.parse_args()
    result=recover(args.run,args.out)
    print(json.dumps(dict(verified_rows=result['recovery']['valid_prefix_rows'],
        complete_log=result['recovery']['complete'],error=result['recovery']['error'])))


if __name__=='__main__':main()
