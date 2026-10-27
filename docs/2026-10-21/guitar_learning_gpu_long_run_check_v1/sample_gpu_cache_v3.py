"""External read-only GPU telemetry during the bounded training check."""
import csv
import json
import subprocess
import time
from pathlib import Path
p = Path(__file__).resolve().parent
run = p/'train1024_large_64_cache_v3'
with (p/'gpu_resources_cache_v3.jsonl').open('x') as stream:
    while True:
        status = json.loads((run/'status.json').read_text())
        result = subprocess.check_output([
            'nvidia-smi', '--query-gpu=timestamp,memory.used,memory.free,utilization.gpu',
            '--format=csv,noheader,nounits'], text=True).strip()
        values = next(csv.reader([result], skipinitialspace=True))
        row = dict(timestamp=values[0], used_mib=int(values[1]), free_mib=int(values[2]),
                   utilization_percent=int(values[3]), update_index=status['update_index'],
                   phase=status['phase'], elapsed_s=status['elapsed_s'])
        stream.write(json.dumps(row)+'\n'); stream.flush()
        if (run/'report.json').exists() or not Path('/proc/%s'%status['parent_pid']).exists():
            break
        time.sleep(10)
