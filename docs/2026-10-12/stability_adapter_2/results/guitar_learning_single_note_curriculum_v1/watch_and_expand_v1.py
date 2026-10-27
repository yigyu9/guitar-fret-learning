"""Finish the authorized single-note run, evaluate, then conditionally expand."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

ROOT = Path('/home/ajou/yigyu/3')
PYTHON = '/home/ajou/miniconda3/envs/rl38/bin/python'


def stamp():
    return datetime.now(timezone.utc).isoformat()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(str(temp), str(path))


def verify_pins(path):
    return [name for name, sha in read(path).items()
            if not Path(name).is_file() or hashlib.sha256(Path(name).read_bytes()).hexdigest() != sha]


def recent_gate(rows, role, window=64, minimum_rate=.9):
    # Invalid/physical terminal episodes remain in the denominator. Open prefixes do not.
    closed = [row for row in rows if row.get('episode') is not None]
    selected = closed[-window:]
    successes = 0
    unsafe = 0
    for row in selected:
        episode, metric = row['episode'], row['metrics']
        if metric['role'] != role:
            raise ValueError('episode role differs from advancement role')
        safe = (metric['complete'] and metric['valid'] and not metric['physical_failure']
                and episode['reason'] == 'timeline_complete' and episode['steps'] == 420
                and abs(episode['task_time_s'] - 7.) < 1e-9)
        unsafe += not safe
        successes += bool(safe and metric['quality_stage_success'])
    rate = successes / len(selected) if selected else None
    return dict(required_episodes=window, evaluated_episodes=len(selected), successes=successes,
                unsafe_episodes=unsafe, success_rate=rate, minimum_rate=minimum_rate,
                passed=len(selected) == window and unsafe == 0 and rate >= minimum_rate)


def evaluation_gate(result, required):
    episodes = result.get('episodes', [])
    safe = (len(episodes) == required and all(e.get('valid') is True
            and e.get('reason') == 'timeline_complete' and e.get('steps') == 420
            and abs(e.get('task_time_s', -1) - 7.) < 1e-9 for e in episodes))
    quality = sum(e.get('musical_quality', {}).get('stage_success') is True for e in episodes)
    return dict(requested_episodes=required, evaluated_episodes=len(episodes),
                quality_successes=quality, safe_complete=safe,
                source_unchanged=result.get('source_unchanged') is True,
                passed=result.get('completed') is True and safe and quality == required
                       and result.get('source_unchanged') is True)


class Progression:
    def __init__(self, plan, out):
        self.plan, self.out = plan, Path(out)
        self.children = []
        self.state = dict(schema='guitar_learning.single_note_progression.v1', pid=os.getpid(),
                          started_utc=stamp(), phase='waiting_single_note', hands={}, execution_errors=[])
        self.environment = dict(os.environ, PATH='/home/ajou/miniconda3/envs/rl38/bin:' + os.environ.get('PATH', ''),
                                LD_LIBRARY_PATH='/home/ajou/miniconda3/envs/rl38/lib', PYTHONUNBUFFERED='1')

    def save(self):
        self.state['updated_utc'] = stamp()
        self.state['children'] = [dict(pid=c['process'].pid, returncode=c['process'].poll(),
                                      label=c['label']) for c in self.children]
        write(self.out / 'status.json', self.state)

    def pins(self):
        changed = []
        for path in self.plan['pin_manifests']:
            changed.extend(verify_pins(path))
        if changed:
            raise RuntimeError('pinned code/settings changed: ' + repr(changed))

    def start(self, label, command):
        self.pins()
        free = next(int(s.split()[1])*1024 for s in Path('/proc/meminfo').read_text().splitlines()
                    if s.startswith('MemAvailable:')) / 2**30
        if free < self.plan['minimum_start_memory_gib']:
            raise RuntimeError('insufficient host memory before new native stage: %.3f GiB' % free)
        stream = (self.out / (label + '.log')).open('x')
        try:
            process = subprocess.Popen(command, cwd=str(ROOT), env=self.environment,
                stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
        except BaseException:
            stream.close()
            raise
        child = dict(label=label, process=process, stream=stream, started=time.monotonic())
        self.children.append(child)
        self.save()
        return child

    def wait(self, children, timeout):
        while any(c['process'].poll() is None for c in children):
            if any(c['process'].poll() is None and time.monotonic()-c['started'] > timeout for c in children):
                raise TimeoutError('native stage exceeded bounded execution budget')
            self.save()
            time.sleep(5)
        for child in children:
            child['stream'].close()
        self.save()
        return all(c['process'].returncode == 0 for c in children)

    def run(self):
        original = Path(self.plan['original_supervisor'])
        deadline = datetime.fromisoformat(self.plan['original_deadline_utc']).timestamp()
        while not (original / 'result.json').is_file():
            self.pins()
            if time.time() > deadline:
                raise TimeoutError('single-note supervisor did not finalize within its allowed margin')
            self.save()
            time.sleep(30)
        self.state['original_result'] = read(original / 'result.json')
        self.state['phase'] = 'evaluating_single_note'
        qualified = []
        for job in self.plan['jobs']:
            role, run = job['role'], Path(job['single_run'])
            record = self.state['hands'][role] = dict(single_run=str(run), advanced=False)
            report = read(run / 'report.json')
            if report.get('completed') is not True or report.get('failure') is not None:
                self.state['execution_errors'].append(role + ': single_note_execution_failed')
                record['reason'] = 'single_note_execution_failed'
                self.save()
                continue
            rows = [json.loads(line) for line in (run/'episodes.jsonl').read_text().splitlines()]
            record['training_gate'] = recent_gate(rows, role, self.plan['training_window'], self.plan['minimum_training_rate'])
            evaluation = self.out / ('single_' + role + '_evaluation_v1')
            command = [PYTHON, '-m', 'guitar_learning.evaluate_musical_quality', '--run', str(run),
                       '--settings', job['single_settings'], '--out', str(evaluation),
                       '--episodes', str(self.plan['evaluation_episodes'])]
            child = self.start('single_' + role + '_evaluation_v1', command)
            if not self.wait([child], 1500):
                self.state['execution_errors'].append(role + ': single_note_evaluation_execution_failed')
                record['reason'] = 'single_note_evaluation_execution_failed'
                self.save()
                continue
            record['evaluation_gate'] = evaluation_gate(read(evaluation/'musical_quality_result.json'),
                                                        self.plan['evaluation_episodes'])
            write(self.out / ('single_' + role + '_gate_v1.json'), record)
            if not (record['training_gate']['passed'] and record['evaluation_gate']['passed']):
                record['reason'] = 'single_note_quality_not_mastered'
                self.save()
                continue
            # Exercise both different goals, native reset, and explicit actor transfer before PPO.
            self.state['phase'] = 'preflight_two_note_' + role
            preflight = self.out / ('pool_' + role + '_preflight_v1')
            child = self.start('pool_' + role + '_preflight_v1', [PYTHON, '-m',
                'guitar_learning.curriculum.evaluate', '--initialization', str(run/'final.pt'),
                '--settings', job['expanded_settings'], '--out', str(preflight), '--episodes', '2'])
            if not self.wait([child], 1500):
                self.state['execution_errors'].append(role + ': pool_native_preflight_execution_failed')
                record['reason'] = 'pool_native_preflight_execution_failed'
                self.save()
                continue
            test = read(preflight/'result.json')
            # Novel goals need safe valid execution here; their musical success is to be learned.
            record['pool_preflight'] = dict(result=str(preflight/'result.json'), completed=test.get('completed'),
                source_unchanged=test.get('source_unchanged'), covered_event_indices=test.get('covered_event_indices'),
                safe_complete=all(e.get('valid') is True and e.get('reason') == 'timeline_complete'
                    and e.get('steps') == 420 and abs(e.get('task_time_s', -1)-7.) < 1e-9
                    for e in test.get('episodes', [])))
            ok = (test.get('completed') is True and test.get('source_unchanged') is True
                  and len(test.get('episodes', [])) == 2 and record['pool_preflight']['safe_complete']
                  and set(test.get('covered_event_indices', [])) == set(self.plan['goal_event_indices']))
            if not ok:
                record['reason'] = 'pool_native_preflight_not_safe_or_incomplete'
                self.save()
                continue
            qualified.append(job)
            self.save()
        self.state['phase'] = 'training_two_note_pool' if qualified else 'single_note_not_mastered'
        children = []
        for job in qualified:
            role = job['role']
            child = self.start('pool_' + role + '_train_v1', [PYTHON, '-m',
                'guitar_learning.curriculum.train', '--settings', job['expanded_settings'],
                '--out', job['expanded_run']])
            children.append(child)
            self.state['hands'][role].update(advanced=True, reason='both_gates_and_native_preflight_passed',
                                            expanded_run=job['expanded_run'])
        if children:
            trainers_ok = self.wait(children, 8400)
            for job in qualified:
                report_path = Path(job['expanded_run'])/'report.json'
                report = read(report_path) if report_path.is_file() else {}
                self.state['hands'][job['role']]['expanded_execution'] = dict(
                    completed=report.get('completed'), failure=report.get('failure'),
                    transitions=report.get('transitions'), final_checkpoint=report.get('final_checkpoint'))
                if report.get('completed') is not True or report.get('failure') is not None:
                    self.state['execution_errors'].append(job['role'] + ': expanded_report_failed_or_missing')
                    trainers_ok = False
            self.state['phase'] = 'two_note_budget_finished' if trainers_ok else 'expanded_execution_failed'
            if not trainers_ok and not self.state['execution_errors']:
                self.state['execution_errors'].append('expanded_trainer_nonzero_exit')
        self.state['execution_ok'] = not self.state['execution_errors']
        if self.state['execution_errors'] and not children:
            self.state['phase'] = 'single_note_execution_failed'
        self.state['finished_utc'] = stamp()
        self.save()
        write(self.out/'result.json', self.state)
        return 0 if self.state['execution_ok'] else 2

    def cleanup(self):
        # Only sessions created by this watcher are eligible for escalation.
        notes = self.state['cleanup'] = []
        for sig, grace in ((signal.SIGINT, 300), (signal.SIGTERM, 20), (signal.SIGKILL, 5)):
            active = [c for c in self.children if c['process'].poll() is None]
            if not active:
                break
            for child in active:
                process = child['process']
                try:
                    if os.getpgid(process.pid) != process.pid:
                        notes.append(dict(pid=process.pid, error='owned session identity changed; no signal sent'))
                        continue
                    os.killpg(process.pid, sig)
                    notes.append(dict(pid=process.pid, signal=int(sig)))
                except ProcessLookupError:
                    pass  # Child exited between poll and signal.
                except OSError as error:
                    notes.append(dict(pid=process.pid, error=str(error)))
            deadline = time.monotonic() + grace
            while any(c['process'].poll() is None for c in active) and time.monotonic() < deadline:
                try:
                    self.save()
                except OSError as error:
                    if not any(note.get('component') == 'cleanup_status' for note in notes):
                        notes.append(dict(component='cleanup_status', error=str(error)))
                time.sleep(1)
        self.state['surviving_owned_children'] = [c['process'].pid for c in self.children
                                                 if c['process'].poll() is None]
        for child in self.children:
            try:
                child['stream'].close()
            except OSError as error:
                notes.append(dict(label=child['label'], error=str(error)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    runner = Progression(read(args.plan), args.out)
    def interrupt(signum, frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, interrupt)
    try:
        return runner.run()
    except BaseException as error:
        runner.state.update(phase='stopped_with_error', error=dict(type=type(error).__name__, message=str(error)))
        try:
            runner.cleanup()
        except BaseException as cleanup_error:
            runner.state['cleanup_error'] = dict(type=type(cleanup_error).__name__, message=str(cleanup_error))
        for persist in (runner.save, lambda: write(args.out/'result.json', runner.state)):
            try:
                persist()
            except OSError as secondary:
                print('secondary error preserving failure record: ' + str(secondary), file=sys.stderr, flush=True)
        raise


if __name__ == '__main__':
    sys.exit(main())
