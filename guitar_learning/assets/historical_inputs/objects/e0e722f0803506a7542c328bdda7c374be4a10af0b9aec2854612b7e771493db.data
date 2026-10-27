"""Intercept only the preserved runner import, after its input snapshots."""
import runpy


def main():
    original_run = runpy.run_module
    def intercept(name, *args, **kwargs):
        if name != 'stability_adapter_2.run_fret_fingers_arm_hold':
            return original_run(name, *args, **kwargs)
        from . import run_fret_fingers_arm_hold as runner
        from .live_fret_recording_v2 import LiveFretRecordingV2
        old_record, old_create = runner.GymTrialRecording, runner.create_fret_view
        def attach(env, *positional, **named):
            view, payload = old_create(env, *positional, **named)
            env.live_diagnostic_view = view
            return view, payload
        runner.GymTrialRecording, runner.create_fret_view = LiveFretRecordingV2, attach
        try: return runner.main()
        finally: runner.GymTrialRecording, runner.create_fret_view = old_record, old_create
    runpy.run_module = intercept
    try: original_run('stability_adapter_2.fret_fingers_arm_hold_preserved_run', run_name='__main__')
    finally: runpy.run_module = original_run


if __name__ == '__main__': main()
