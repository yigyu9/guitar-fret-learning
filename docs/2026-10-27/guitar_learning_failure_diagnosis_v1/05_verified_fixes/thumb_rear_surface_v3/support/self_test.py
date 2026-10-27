"""CPU-only output preservation, ownership and one-job dry-plan checks."""
import builtins
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
from unittest import mock

import run_regression as driver
from guitar_learning.tool.validation import thumb_contact_probe
from guitar_learning.gpu.thumb_support import load_thumb_support
from guitar_learning.gpu.episode_diagnostics import DIAGNOSTIC_CONTRACT


def main():
    original_import = builtins.__import__
    native_attempts = []
    def no_native(name, *args, **kwargs):
        if name == 'isaacgym' or name.startswith('isaacgym.'):
            native_attempts.append(name)
            raise AssertionError('CPU guard reached native import')
        return original_import(name, *args, **kwargs)

    checks = {}
    with tempfile.TemporaryDirectory(dir=str(driver.HERE), prefix='cpu-') as temp:
        root = Path(temp)
        for name in ('raw_base', 'production_regression'):
            out = root/name
            out.mkdir()
            (out/'nested').mkdir()
            (out/'report.json').write_bytes(b'original report\x00\xff')
            (out/'physics_env0000.npz').write_bytes(b'original raw\x00\xff')
            (out/'production_regression.json').write_bytes(b'original wrapper\x00\xff')
            (out/'nested/marker').write_bytes(bytes(range(256)))
            before = {str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            with mock.patch.object(sys, 'argv', ['driver', '--out', str(out), '--video']), \
                    mock.patch.object(builtins, '__import__', side_effect=no_native), \
                    mock.patch.object(thumb_contact_probe, 'main') as base_call:
                try:
                    driver.main()
                except FileExistsError:
                    pass
                else:
                    raise AssertionError('Existing output accepted')
                base_call.assert_not_called()
            after = {str(p.relative_to(out)): p.read_bytes() for p in out.rglob('*') if p.is_file()}
            assert before == after
            checks[name+'_unchanged_before_native_or_base'] = True
        out = root/'not_created'
        with mock.patch.object(sys, 'argv', ['driver', '--out', str(out), '--video', '--dry-plan']), \
                mock.patch.object(builtins, '__import__', side_effect=no_native), \
                mock.patch.object(thumb_contact_probe, 'main') as base_call, \
                contextlib.redirect_stdout(io.StringIO()) as output:
            driver.main()
            base_call.assert_not_called()
        plan = json.loads(output.getvalue())
        assert len(plan['jobs']) == 1 and not plan['GPU_executed'] and not out.exists()
        assert plan['jobs'][0]['args'][-1] == '--video'
        checks['one_job_dry_plan_no_output_or_native'] = True
        owner = root/'owner'
        owner.mkdir()
        stat = owner.stat()
        identity = (stat.st_dev, stat.st_ino)
        assert driver.owned(owner, identity)
        owner.rename(root/'old_owner')
        owner.mkdir()
        assert not driver.owned(owner, identity)
        assert not driver.owned(owner, None)
        checks['replacement_inode_rejected'] = True
    assert not native_attempts and 'isaacgym' not in sys.modules
    assert driver.ROOT == Path('/home/ajou/yigyu/3')
    patch = load_thumb_support()
    assert patch['contract']['schema'] == 'guitar_learning.gpu_thumb_rear_support.v3'
    assert DIAGNOSTIC_CONTRACT['schema'] == 'guitar_learning.gpu_left_episode_diagnostics.v6'
    assert abs(float(patch['plane'][2])+1) < 1e-12
    assert abs(float(patch['plane'][3])+.008) < 1e-12
    assert abs(min(thumb_contact_probe.approach_gap(i/60) for i in range(900))+.0003) < 1e-15
    checks['production_contracts_and_original_schedule'] = True
    # Only source bytes are sealed here; no native call or scene construction.
    paths = [driver.HERE/'run_regression.py', driver.HERE/'self_test.py', driver.HERE/'README.md']
    paths += [driver.ROOT/'guitar_learning'/name for name in (
        'tool/validation/thumb_contact_probe.py', 'tool/validation/hand_contact_probe.py',
        'gpu/thumb_support.py', 'gpu/episode_diagnostics.py', 'gpu/scene.py')]
    pins = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (driver.HERE/'precommit.json').write_text(json.dumps(dict(source_pins=pins,
        scope='Current production helper fixed-guitar regression; root GPU handoff required, not additional user approval'), indent=2)+'\n')
    (driver.HERE/'cpu_verification.json').write_text(json.dumps(dict(completed=True, GPU_used=False,
        checks=checks, native_import_attempts=native_attempts, base_probe_called=False,
        source_pins=pins), indent=2)+'\n')
    (driver.HERE/'dry_plan.json').write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps(dict(completed=True, checks=checks, GPU_used=False), indent=2))


if __name__ == '__main__':
    main()
