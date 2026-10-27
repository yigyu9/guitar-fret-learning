"""Use fresh native source admission for one thumb-base initial candidate."""
from pathlib import Path

from . import near_contact_initial_audit as admission
from . import run_small_wrist_recorded_diagnostic as runner
from .run_source_hand_initial import audit_initial


def main():
    original_audit, original_save = admission.audit_initial, runner.save

    def save_direct(path, value):
        if Path(path).name in ('attempt.json', 'initial_values.json', 'report.json'):
            value = dict(value)
            value['inherited_scope'] = value.get('scope')
            value['scope'] = 'One thumb1 base axis initial/held angle changed from source-hand5 baseline; fresh actual native direct source gate; same free guitar/LA/PD/root/lower/body9 hold and small wrist command; no post-start pose writes'
            if 'checks' in value:
                value['checks'] = dict(value['checks'])
                old = value['checks'].pop('initial_grip_source_and_FK_gate', None)
                if old is not None:
                    value['checks']['direct_native_source_gate'] = old
            if value.get('failure', {}):
                value['inherited_failure'] = value['failure']
                if value['failure']['message'].startswith('initial grip source/FK gate rejected'):
                    value['failure'] = dict(type=value['failure']['type'], message='fresh direct native source gate rejected; t0 partial video saved')
        original_save(path, value)

    admission.audit_initial, runner.save = audit_initial, save_direct
    try:
        runner.main()
    finally:
        admission.audit_initial, runner.save = original_audit, original_save


if __name__ == '__main__': main()
