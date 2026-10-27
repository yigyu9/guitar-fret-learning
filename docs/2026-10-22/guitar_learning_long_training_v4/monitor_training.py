"""One read-only training/resource snapshot, appended outside the training run."""
import hashlib
import json
from pathlib import Path
import shutil
from datetime import datetime, timezone

PHASE = Path(__file__).resolve().parent
RUN = PHASE/'train2000'


def last_rows(path, size=65536):
    with path.open('rb') as stream:
        stream.seek(0, 2)
        end = stream.tell()
        stream.seek(max(0, end-size))
        rows = stream.read().decode().splitlines()
    return [json.loads(row) for row in rows[1:-1]] if len(rows) > 2 else []


def main():
    status = json.loads((RUN/'status.json').read_text())
    updates = sorted(RUN.glob('update_*.json'))
    metrics = None
    for path in reversed(updates[-2:]):
        try:
            metrics = json.loads(path.read_text())
            break
        except json.JSONDecodeError:
            pass  # This file may still be being written; use the prior commit.
    model = sorted(RUN.glob('checkpoint_*.pt'))
    events = [v for v in last_rows(RUN/'events.jsonl') if v.get('event') == 'cuda_cache_release']
    source = json.loads((PHASE/'training_source_manifest.json').read_text())['source']
    changed = [p for p,h in source.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    episodes = metrics['completed_episodes'] if metrics else []
    result = dict(utc=datetime.now(timezone.utc).isoformat(),
        elapsed_s=status.get('elapsed_s'), phase=status.get('phase'), pid=status.get('parent_pid'),
        optimizer_updates=metrics['optimizer_updates'] if metrics else 0,
        committed=metrics['journal']['committed'] if metrics else 0,
        latest_checkpoint=model[-1].name if model else None,
        disk_free_bytes=shutil.disk_usage(PHASE).free,
        run_bytes=sum(p.stat().st_size for p in RUN.rglob('*') if p.is_file()),
        latest_idle_cuda_free_bytes=events[-1]['after']['free_bytes'] if events else None,
        latest_update_episodes=len(episodes),
        latest_update_mean_achieved=(sum(e['song']['left_success_count'] for e in episodes)/len(episodes)) if episodes else None,
        current_stage=metrics.get('left_curriculum') if metrics else None,
        changed_sources=changed, report_exists=(RUN/'report.json').exists())
    with (PHASE/'progress.jsonl').open('a') as stream:
        stream.write(json.dumps(result, allow_nan=False)+'\n')
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
