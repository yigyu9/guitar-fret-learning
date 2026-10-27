"""Read-only native evaluation of saved overnight checkpoints."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import time

ROOT = Path('/home/ajou/yigyu/3')
RUN = ROOT/'docs/2026-10-27/guitar_learning_large_until0900_v1'

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('label')
    parser.add_argument('checkpoint')
    parser.add_argument('--render', action='store_true')
    args = parser.parse_args()
    os.chdir(ROOT)
    manifest = json.loads((RUN/'source_manifest.json').read_text())
    changed = [p for p, sha in manifest.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != sha]
    if changed:
        raise RuntimeError('Source changed: '+repr(changed))
    checkpoint = RUN/'run_01/J'/args.checkpoint
    import isaacgym
    if args.render:
        from guitar_learning.tool.demonstration.render_finger_skill import render
        report = render(checkpoint, RUN/'analysis'/('video_'+args.label), scope='full_song', num_envs=128)
    else:
        from guitar_learning.training.finger_skill_runner import evaluate_checkpoint
        report, _ = evaluate_checkpoint(checkpoint, RUN/'analysis'/('evaluation_'+args.label),
            num_envs=128, scope='full_song', max_batches=1, max_episodes=128, deadline=time.monotonic()+1200)
    print(json.dumps(dict(label=args.label, completed=report['completed'], summary=report.get('summary'), wall_s=report['wall_s']), ensure_ascii=False), flush=True)

if __name__ == '__main__':
    main()
