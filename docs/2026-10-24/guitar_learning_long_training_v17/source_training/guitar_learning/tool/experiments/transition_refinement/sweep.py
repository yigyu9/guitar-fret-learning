"""Independent native BC evaluation at matched seeds and explicit exploration levels."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)


def child_settings(base, std, repeat):
    if (isinstance(std, bool) or not math.isfinite(std) or std < 0
            or type(repeat) is not int or repeat < 0):
        raise ValueError('finite nonnegative std and integer repeat required')
    value = copy.deepcopy(base)
    config = value['refinement']
    if config['schema'] != 'guitar_learning.transition_refinement.v1':
        raise ValueError('explicit refinement schema required')
    config['evaluation_mode'] = 'stochastic' if std else 'deterministic'
    if std:
        value['initial_std'] = config['exploration']['initial_std'] = std
    if not 0 < value['initial_std'] == config['exploration']['initial_std']:
        raise ValueError('matching positive base exploration required for deterministic baseline')
    value['seed'] = base['seed']+repeat
    value['initialization']['gate_evaluations'] = []
    return value


def child_command(settings, out, supervisor=None):
    command = [sys.executable, '-m', 'guitar_learning.tool.experiments.transition_refinement.run', 'eval',
               '--settings', str(settings), '--out', str(out), '--episodes', '1']
    return ['gdb', '-q', '-nx', '-batch', '-x', str(supervisor), '--args', *command] if supervisor else command


def classify_case(out, returncode):
    """Closed physical failures remain in the denominator; runtime faults do not."""
    row = dict(classification='runtime_invalid', musical_success=False, physical_failure=False,
               returncode=returncode, sigfpe=returncode in (-8, 136))
    try:
        out = Path(out).resolve()
        parent = json.loads((out/'result.json').read_text())
        folder = out/'case_000'
        case = json.loads((folder/'result.json').read_text())
        if returncode != 0:
            raise ValueError('child process did not exit successfully')
        if (parent['schema'] != 'guitar_learning.transition_probe.v1'
                or case['schema'] != 'guitar_learning.transition_capture.v1'
                or parent['case_manifests'] != {str(folder):digest(folder/'result.json')}
                or case['parent_result_path'] != str(out/'result.json')):
            raise ValueError('one finalized case and its producer manifest required')
        for report in (parent, case):
            if (report.get('source_unchanged') is not True or report.get('physical_flags_ok') is not True
                    or report.get('failure') is not None or report.get('cleanup_error') is not None
                    or report.get('forbidden_calls') != [] or report.get('missing_import_pins') != []):
                raise ValueError('source, physical setup or runtime cleanup audit failed')
        episode = case['episode']
        if (episode['valid'] is not True or episode['reason'] not in ('timeline_complete', 'terminal_failure')
                or case.get('action_source') != 'policy' or case.get('teacher_intervention') is not False):
            raise ValueError('valid unassisted terminal episode required')
        physical = episode['reason'] == 'terminal_failure' or episode['transition']['safety_valid'] is False
        if not physical and (case['completed'] is not True or parent['completed'] is not True):
            raise ValueError('musical result lacks completed producer publication')
        success = not physical and case['success'] is True and episode['transition']['successful'] is True
        if (str(folder) in parent['successful_cases']) != success:
            raise ValueError('parent/case musical success mismatch')
        row.update(classification='evaluated', musical_success=success, physical_failure=physical,
                   episode_reason=episode['reason'], transition=episode['transition'])
    except (OSError, ValueError, KeyError, TypeError) as error:
        row['runtime_reason'] = str(error)
    return row


def run(settings_path, out, stds, repeats, supervisor=None, runner=subprocess.run):
    settings_path, out = Path(settings_path), Path(out)
    if (not settings_path.is_absolute() or not out.is_absolute() or type(repeats) is not int
            or repeats < 1 or not stds or len(set(stds)) != len(stds)):
        raise ValueError('absolute paths, positive repeats and distinct exploration levels required')
    settings_path, out = settings_path.resolve(), out.resolve()
    if supervisor is not None:
        supervisor = Path(supervisor)
        if not supervisor.is_absolute() or supervisor.suffix != '.gdb':
            raise ValueError('absolute .gdb supervisor input required')
    base = json.loads(settings_path.read_text())
    settings = [(std,repeat,child_settings(base,std,repeat)) for std in stds for repeat in range(repeats)]
    checkpoint = Path(base['initialization']['checkpoint'])
    if not checkpoint.is_absolute():
        raise ValueError('absolute fixed BC initialization checkpoint required')
    package = Path(__file__).resolve().parents[3]
    paths = [settings_path, checkpoint, *(path for path in package.rglob('*.py') if 'archive' not in path.parts)]
    if supervisor is not None:paths.append(supervisor)
    pins = {str(path):digest(path) for path in paths}
    out.mkdir(parents=True,exist_ok=False)
    # Prepare every generated configuration before sealing the sweep. Earlier
    # configurations stay pinned through the last child, just like the BC.
    for index,(_,_,value) in enumerate(settings):
        path = out/('settings_%03d.json'%index); write(path,value)
        pins[str(path)] = digest(path)
    write(out/'inputs_before.json',pins)
    rows = []
    for index,(std,repeat,value) in enumerate(settings):
        path = out/('settings_%03d.json'%index)
        native_out = out/('native_%03d'%index)
        command = child_command(path,native_out,supervisor)
        input_sha = pins[str(path)]
        try:
            if any(not Path(p).is_file() or digest(p) != sha for p,sha in pins.items()):
                raise RuntimeError('sweep inputs changed before child launch')
            with (out/('native_%03d.log'%index)).open('x') as stream:
                result = runner(command,stdout=stream,stderr=subprocess.STDOUT,check=False)
            row = classify_case(native_out,result.returncode)
        except (OSError,RuntimeError) as error:
            row = dict(classification='runtime_invalid',runtime_reason=str(error),musical_success=False,physical_failure=False)
        after_sha = digest(path) if path.is_file() else None
        if after_sha != input_sha:
            row.update(classification='runtime_invalid',runtime_reason='child settings changed',
                       musical_success=False,physical_failure=False)
        row.update(std=std,repeat=repeat,seed=value['seed'],settings_sha256=input_sha,
                   settings_sha256_after=after_sha,command=command,out=str(native_out))
        rows.append(row)
        print(json.dumps(row),flush=True)
    after_paths = set(pins) | {str(path.resolve()) for path in package.rglob('*.py') if 'archive' not in path.parts}
    after = {path:digest(path) if Path(path).is_file() else None for path in sorted(after_paths)}
    write(out/'inputs_after.json',after)
    unchanged = pins == after
    for index,row in enumerate(rows):
        if not unchanged:
            row.update(classification='runtime_invalid',runtime_reason='sweep inputs changed during comparison',
                       musical_success=False,physical_failure=False)
        write(out/('result_%03d.json'%index),row)
    summary = []
    for std in stds:
        group = [row for row in rows if row['std'] == std]
        valid = [row for row in group if row['classification'] == 'evaluated'] if unchanged else []
        summary.append(dict(std=std,attempted_cases=len(group),evaluated_cases=len(valid),
            musical_successes=sum(row['musical_success'] for row in valid),
            physical_failures=sum(row['physical_failure'] for row in valid),runtime_invalid_cases=len(group)-len(valid)))
    report = dict(schema='guitar_learning.transition_refinement_sweep.v1',source_unchanged=unchanged,
        summary=summary,cases=rows,scope='matched-seed BC exploration sensitivity; no automatic standard-deviation selection')
    write(out/'result.json',report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--settings',type=Path,required=True); parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--stds',type=float,nargs='+',default=[0.,.001,.003,.01,.02])
    parser.add_argument('--repeats',type=int,default=3); parser.add_argument('--supervisor',type=Path)
    args = parser.parse_args(); run(args.settings,args.out,args.stds,args.repeats,args.supervisor)


if __name__ == '__main__':main()
