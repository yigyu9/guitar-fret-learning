"""선택한 실제 정책을 렌더한다. 전신 카메라는 발끝까지 담도록 뒤로 옮긴다."""
import isaacgym
import json
from pathlib import Path
from guitar_learning.tool.experiments.structured_geometry import nested_input_paths

ROOT = Path(__file__).resolve().parent

with nested_input_paths():
    import torch
    from guitar_learning.portability import localize
    from guitar_learning.tool.experiments.structured_press import structured_runtime
    from guitar_learning.tool.demonstration import render_finger_skill as renderer

    summary = json.loads((ROOT/'summary.json').read_text())
    checkpoint = Path(summary['selected_checkpoint'])
    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    config = localize(payload['metadata']['settings'])['structured_press']
    # 카메라 구도만 실행 중 바꾼다. 봉인된 학습 소스·물리·행동은 그대로다.
    renderer.CAMERAS['fullbody'] = ((-.10, 3.4, 1.1), (-.15, -.10, .65))
    with structured_runtime(config):
        renderer.render(checkpoint, ROOT/'render_selected', num_envs=4, scope='full_song')
    (ROOT/'render_selected/camera_config.json').write_text(json.dumps(dict(
        cameras=renderer.CAMERAS, checkpoint=str(checkpoint),
        source='native camera pixels; deterministic actual learned policy',
        physics_or_policy_modified=False), indent=2)+'\n')
