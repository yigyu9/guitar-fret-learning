"""Read one committed update; never read or modify the running simulation."""
import json
from pathlib import Path

phase = Path(__file__).resolve().parent
run = phase/'resume1700'
files = sorted(run.glob('update_*.json'))
row = None
for path in reversed(files):
    try:
        row = json.loads(path.read_text())
    except json.JSONDecodeError:
        continue  # A new update file can still be inside json.dump.
    break
if row is None:
    print('No committed update yet')
else:
    curriculum = row['left_curriculum']
    print(json.dumps(dict(updates=row['optimizer_updates'], target=2000,
        committed_transitions=300*32*1024+row['journal']['committed'], discarded=row['journal']['discarded'],
        progress=curriculum['progress'], recent_episodes=curriculum['recent_episodes'],
        recent_safe=round(curriculum['recent_safe_fraction'], 4),
        near=[round(f['near_fraction'], 4) for f in curriculum['recent_fingers']],
        contact=[round(f['contact_fraction'], 4) for f in curriculum['recent_fingers']],
        success=[round(f['success_fraction'], 4) for f in curriculum['recent_fingers']]), allow_nan=False))
if (run/'report.json').is_file():
    report = json.loads((run/'report.json').read_text())
    print(json.dumps(dict(final=True, completed=report['completed'], stopped=report['stopped'],
        failure=report['failure'], wall_s=report['wall_s'])))
