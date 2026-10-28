"""CPU safety skeleton checks; never import active runtime or native extension."""
import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from common import HERE, ROOT, OLD, reused, sha, write, owned
import run_probe


def check():
    plan = run_probe.jobs()
    original = reused().jobs()[:4]
    assert len(plan) == 4
    for job, prior in zip(plan, original):
        restored = copy.deepcopy(job)
        restored['out'] = restored['out'].replace(str(HERE/'runs'), str(OLD/'runs'))
        index = restored['args'].index(str(HERE/'child.py'))
        restored['args'][index:index+1] = ['-m', reused().MODULE]
        restored['args'] = [v.replace(str(HERE/'runs'), str(OLD/'runs')) for v in restored['args']]
        assert restored == prior
    environment = os.environ.copy(); environment['PYTHONPATH'] = str(ROOT)
    with tempfile.TemporaryDirectory(prefix='wrist_v2_output_') as temp:
        out = Path(temp)/'existing'; out.mkdir(); sentinel = out/'preserved'; sentinel.write_bytes(b'preserve')
        stat = out.stat(); identity = (stat.st_dev, stat.st_ino)
        assert owned(out, identity) and not owned(out, (identity[0], identity[1]+1))
        command = plan[1]['args'][plan[1]['args'].index(str(HERE/'child.py')):]
        for path in (out, Path(temp)/'dangling'):
            if path != out:
                path.symlink_to(Path(temp)/'absent')
            command[command.index('--out')+1] = str(path)
            result = subprocess.run([sys.executable, '-v', *command], env=environment, capture_output=True, text=True)
            assert result.returncode != 0 and 'FileExistsError' in result.stderr
            assert "import 'isaacgym" not in result.stderr
            assert "import 'guitar_learning.tool.experiments.short_finger_learning.runner" not in result.stderr
        assert sentinel.read_bytes() == b'preserve' and list(out.iterdir()) == [sentinel]
        assert (out.stat().st_dev, out.stat().st_ino) == identity
    for path in HERE.glob('*.py'):
        ast.parse(path.read_text(), feature_version=(3, 8))
    return dict(CPU_only=True, GPU_executed=False, active_runtime_imported=False,
        jobs4_original_exact_except_child_and_run_paths=True, original_teacher_reference_paths=True,
        own_fresh_initial_only=True, existing_output_unchanged=True, dangling_symlink_rejected=True,
        guard_before_native_and_runner_import=True, dev_inode_ownership=True, python38_syntax=True)


def main():
    result = check()
    write(HERE/'safety_verification.json', result)
    write(HERE/'dry_run.json', dict(jobs=run_probe.jobs(), GPU_executed=False))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
