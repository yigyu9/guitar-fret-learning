"""Avoid simultaneous native GPU simulators while final thumb tape finishes."""
import json,time,subprocess,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];report=P/'native_thumb_smooth_tape/report.json'
while not report.exists():time.sleep(5)
r=json.loads(report.read_text())
if not r['completed'] or not r.get('protocol_completed',False):raise SystemExit('Native tape did not complete; training remains blocked')
raise SystemExit(subprocess.run(['/home/ajou/miniconda3/envs/rl38/bin/python','-B',str(P/'support/run_v22_checks.py')],env=os.environ).returncode)
