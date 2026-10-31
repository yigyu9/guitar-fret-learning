"""선택한 실제 정책의 손·전신 영상을 만든다. 학습 물리·관절 상태는 바꾸지 않는다."""
import isaacgym  # torch보다 먼저 native 라이브러리를 로드한다.
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths

ROOT = Path(__file__).resolve().parent
PUBLIC = ROOT.parents[3]/'video/seven_hour_v1'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--checkpoint', required=True, type=Path)
    parser.add_argument('--label', required=True)
    args = parser.parse_args()
    if Path(args.label).name != args.label or args.label in ('.', '..'):
        raise ValueError('label must be one directory name')
    out = ROOT/'renders'/args.label
    out.parent.mkdir(exist_ok=True)
    checkpoint = args.checkpoint.resolve()
    before = digest(checkpoint)
    with nested_input_paths():
        import torch
        from guitar_learning.portability import localize
        from guitar_learning.tool.experiments.structured_press import structured_runtime
        from guitar_learning.tool.demonstration import render_finger_skill as renderer
        payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
        config = localize(payload['metadata']['settings'])['structured_press']
        renderer.CAMERAS['fullbody'] = ((-.10, 3.4, 1.1), (-.15, -.10, .65))
        with structured_runtime(config):
            renderer.render(checkpoint, out, num_envs=4, scope='full_song')
    report = json.loads((out/'report.json').read_text())
    if not report['completed'] or before != digest(checkpoint):
        raise RuntimeError('render incomplete or selected policy changed')
    PUBLIC.mkdir(parents=True, exist_ok=True)
    videos = []
    for kind in ('hand', 'fullbody'):
        source, target = out/(kind+'.mp4'), PUBLIC/(args.label+'_'+kind+'.mp4')
        if target.exists():
            raise FileExistsError(str(target))
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams',
            '-show_format', '-of', 'json', str(source)]))
        if float(probe['format']['duration']) <= 0:
            raise ValueError('video has no frames')
        shutil.copyfile(source, target)
        if digest(source) != digest(target):
            raise ValueError('public copy differs')
        videos.append(dict(kind=kind, path=str(target), sha256=digest(target), probe=probe))
    (out/'publication.json').write_text(json.dumps(dict(checkpoint=str(checkpoint),
        checkpoint_sha256=before, videos=videos, cameras=renderer.CAMERAS,
        image_source='native camera pixels, actual deterministic policy',
        physics_or_policy_modified=False), ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    main()
