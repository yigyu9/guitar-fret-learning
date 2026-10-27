"""Native capture with a wider fullbody camera; package and policy are unchanged."""
import hashlib
import json
import os
from pathlib import Path
ROOT=Path('/home/ajou/yigyu/3')
RUN=ROOT/'docs/2026-10-27/guitar_learning_large_until0900_v1'
def main():
    os.chdir(ROOT)
    manifest=json.loads((RUN/'source_manifest.json').read_text())
    changed=[p for p,sha in manifest.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest()!=sha]
    if changed:
        raise RuntimeError('Source changed: '+repr(changed))
    import isaacgym
    from guitar_learning.tool.demonstration import render_finger_skill
    original=render_finger_skill.CAMERAS['fullbody']
    override=((-0.10,3.4,1.1),(-0.15,-0.10,0.65))
    render_finger_skill.CAMERAS['fullbody']=override
    documentation=dict(reason='include full head and feet with margin',
        original_fullbody_camera=original,override_fullbody_camera=override,
        change_scope='runtime graphics camera position only; package source, physics and policy unchanged',
        wrapper=str(Path(__file__).resolve()),wrapper_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (RUN/'support/final_framed_camera_override.json').write_text(json.dumps(documentation,indent=2)+'\n')
    report=render_finger_skill.render(RUN/'run_01/J/final.pt',RUN/'analysis/video_final_framed',scope='full_song',num_envs=128)
    (RUN/'analysis/video_final_framed/camera_override.json').write_text(json.dumps(documentation,indent=2)+'\n')
    print(json.dumps(dict(completed=report['completed'],wall_s=report['wall_s'],episode=report['episode']['song']),ensure_ascii=False),flush=True)
if __name__=='__main__':
    main()
