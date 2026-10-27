"""Two native scene lifecycles, using the same construction path as GUI reset."""
from pathlib import Path
from unittest.mock import patch
import json
import hashlib
import isaacgym
from stability_adapter_2.current_pose_test_v1 import run_v2 as run
from stability_adapter_2.initial_pose_noise_v1 import read,save,sha

P=Path(__file__).resolve().parent

def check():
    out=P/'recreation_check_v1';out.mkdir(exist_ok=False)
    before={str(Path(__file__).resolve()):sha(__file__)}
    save(out/'producer_before.json',before)
    for number in range(2):assert not run.episode(out/('trial_%03d'%number),True)
    initial=[read(out/('trial_%03d'%n)/'initial_values.json') for n in range(2)]
    final=[read(out/('trial_%03d'%n)/'final_state.json') for n in range(2)]
    assert initial[0]==initial[1] and final[0]==final[1]
    for number in range(2):
        report=read(out/('trial_%03d'%number)/'report.json');assert report['completed'] and report['physics_steps']==48 and not report['forbidden_calls']
    assert all(sha(path)==h for path,h in before.items())
    save(out/'verification.json',{'passed':True,'fresh_scene_count':2,'initial_exact_between_recreations':True,'final_state_exact_between_recreations':True,'physics_steps_each':48,'scope':'fresh simulator lifecycle used by R, not desktop key dispatch/GUI integration','producer_inputs':before})
    print('two fresh simulator lifecycles and states matched',flush=True)

with patch.object(run,'main',check):run.launch()
