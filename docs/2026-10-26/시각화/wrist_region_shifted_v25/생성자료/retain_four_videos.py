"""Keep only the selected 5cm front/top/bottom/rear videos in the requested folder."""
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
DEST = Path('/home/ajou/yigyu/3/docs/2026-11-02/손목')


def main():
    selected = {DEST/('thumb_head5_'+view+'.mp4'): DEST/(view+'.mp4')
                for view in ('front', 'top', 'bottom', 'rear')}
    before = list(DEST.iterdir())
    assert all(path.is_file() and path.suffix == '.mp4' for path in before)
    records = []
    for source, target in selected.items():
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height,nb_frames,avg_frame_rate,duration', '-of', 'json', str(source)]))['streams'][0]
        assert int(probe['nb_frames']) == 985 and probe['avg_frame_rate'] == '30/1'
        records.append(dict(previous_path=str(source), path=str(target), stream=probe,
                            sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
    removed = [path for path in before if path not in selected]
    for path in removed:
        path.unlink()
    for source, target in selected.items():
        source.rename(target)
    assert set(DEST.iterdir()) == set(selected.values())
    for record in records:
        assert hashlib.sha256(Path(record['path']).read_bytes()).hexdigest() == record['sha256']
    report = dict(completed=True, headward_offset_cm=5, videos=records,
                  removed_paths=[str(path) for path in removed], only_four_videos=True)
    (HERE/'retained_four_verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(remaining=[str(path) for path in selected.values()], removed_count=len(removed)), ensure_ascii=False))


if __name__ == '__main__':
    main()
