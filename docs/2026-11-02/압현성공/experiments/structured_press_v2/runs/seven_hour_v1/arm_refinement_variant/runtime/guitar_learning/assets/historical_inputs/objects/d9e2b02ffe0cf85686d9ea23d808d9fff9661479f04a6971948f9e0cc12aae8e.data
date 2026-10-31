"""Shared fixed-rate saved-pose rendering helpers; no simulation or policy."""
import json
import subprocess
from pathlib import Path
from guitar_learning.native.initial_pose_video60_v1.replay_v6 import sha

ROOT = Path(__file__).resolve().parents[2]
INITIAL = ROOT/'docs/2026-10-12/stability_adapter_2/results/free_guitar_fretting_v1/native_probe_v1/initial_values.json'
FONT = Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc')


def encoder(path):
    return subprocess.Popen(['ffmpeg', '-nostdin', '-n', '-loglevel', 'error',
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1280x720', '-r', '60',
        '-i', '-', '-an', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', str(path)],
        stdin=subprocess.PIPE)


def probe(path, frames):
    result = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0',
        '-show_entries', 'stream=width,height,avg_frame_rate,nb_read_frames,duration',
        '-of', 'json', str(path)], check=True, capture_output=True, text=True)
    stream = json.loads(result.stdout)['streams'][0]
    if (int(stream['nb_read_frames']) != frames or stream['avg_frame_rate'] != '60/1'
            or (stream['width'], stream['height']) != (1280, 720)
            or abs(float(stream['duration'])-frames/60.) > .002):
        raise ValueError('video coverage mismatch')
    return dict(path=str(path), sha256=sha(path), stream=stream)


