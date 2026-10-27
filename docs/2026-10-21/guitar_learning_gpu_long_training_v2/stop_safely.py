"""Request SIGINT for this task's running native preflight only."""
from pathlib import Path
import json
import os
import signal
import time
p = Path(__file__).resolve().parent
run = p/'train1024_large_2000'
started = time.monotonic()
while True:
    if (run/'report.json').exists():
        print('Run already stopped; no signal sent')
        break
    status = json.loads((run/'status.json').read_text())
    if status['phase'] == 'collecting' and 0 <= status['ticks'] <= 24:
        os.kill(status['parent_pid'], signal.SIGINT)
        record = dict(reason='Memory remains stable but on-policy episodes collapse toward early physical termination; preserve this trial before objective correction',
                      signal='SIGINT', status_at_request=status)
        (p/'intentional_stop.json').write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps(dict(signal_sent=True, pid=status['parent_pid'],
                             update_index=status['update_index'], ticks=status['ticks'])))
        break
    if time.monotonic()-started > 40:
        raise RuntimeError('No safe collection observation within40s; no signal sent')
    time.sleep(.1)
