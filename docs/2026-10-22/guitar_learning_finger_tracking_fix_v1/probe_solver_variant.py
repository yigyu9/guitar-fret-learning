"""Root-only N6 probe: change only native position solver iterations4 to16."""
import importlib.util
from pathlib import Path
import sys

BASE = Path(__file__).with_name('probe_multiaxis.py')
BASE_SHA = 'e77455e706cf002aadfca949c10b3830aa25904e1d9053d429f74f807458c919'
SCHEMA = 'guitar_learning.multiaxis_solver_variant.v1'
spec = importlib.util.spec_from_file_location('multiaxis_solver_base', BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def parameters(params):
    return dict(position_iterations=int(params.physx.num_position_iterations),
        velocity_iterations=int(params.physx.num_velocity_iterations),
        dt_s=float(params.dt), substeps=int(params.substeps))


class GymProxy:
    def __init__(self, gym, records):
        self.gym, self.records = gym, records

    def __getattr__(self, name):
        return getattr(self.gym, name)

    def create_sim(self, compute, graphics, engine, params):
        before = parameters(params)
        base.require(before['position_iterations'] == 4 and before['velocity_iterations'] == 2 and
            abs(before['dt_s']-1/240.) < 1e-9 and before['substeps'] == 1,
            'Expected original4/2 solver at240Hz/substep1 before override')
        base.require(not self.records, 'Exactly one simulator permitted')
        record = dict(requested_before=before, actual_readback=None)
        self.records.append(record)
        params.physx.num_position_iterations = 16
        sim = self.gym.create_sim(compute, graphics, engine, params)
        base.require(sim is not None, 'Variant simulator construction failed')
        try:
            actual = parameters(self.gym.get_sim_params(sim))
            record['actual_readback'] = actual
            base.require(actual['position_iterations'] == 16 and actual['velocity_iterations'] == 2 and
                abs(actual['dt_s']-1/240.) < 1e-9 and actual['substeps'] == 1,
                'Actual native readback is not16/2 at240Hz/substep1')
        except BaseException:
            self.gym.destroy_sim(sim)
            raise
        return sim


def main():
    base.require(base.sha(BASE) == BASE_SHA, 'Closed base probe SHA changed')
    # SDK first: base import above loads only stdlib and pure JSON serialization.
    from isaacgym import gymapi
    acquire, write = gymapi.acquire_gym, base.write
    records, pins = [], {}
    planned = dict(schema=SCHEMA, field='physx.num_position_iterations', original=4, variant=16,
        source_probe=str(BASE.resolve()), source_probe_sha256=BASE_SHA,
        scope='Runtime native override; original source contract is comparison reference only, not the actual solver contract.')

    def variant_write(path, value):
        if path.name == 'settings.json':
            value = dict(value, runtime_override=planned)
        elif path.name == 'inputs_before.json':
            value = dict(value)
            value[str(Path(__file__).resolve())] = base.sha(Path(__file__).resolve())
            value[str(BASE.resolve())] = BASE_SHA
            pins.update(value)
        elif path.name == 'training_contract.json':
            value = dict(schema=SCHEMA, source_training_contract=value,
                runtime_override=dict(planned, native_create_sim_records=records))
        elif path.name == 'report.json':
            actual = records[0]['actual_readback'] if len(records) == 1 else None
            changed = [p for p,h in pins.items() if not Path(p).is_file() or base.sha(p) != h]
            after = {p:base.sha(p) if Path(p).is_file() else None for p in pins}
            write(path.with_name('inputs_after.json'), after)
            value['runtime_override'] = dict(planned, native_create_sim_records=records)
            value['schema'] = SCHEMA
            value['changed_inputs'] = sorted(set(value['changed_inputs']) | set(changed))
            value['completed'] = bool(value['completed'] and actual and actual['position_iterations'] == 16 and not changed)
            write(path.with_name('runtime_override_contract.json'), dict(schema=SCHEMA,
                runtime_override=value['runtime_override'], source_training_contract_reference_only=True,
                settings_sha256=base.sha(path.with_name('settings.json')),
                inputs_before_sha256=base.sha(path.with_name('inputs_before.json')),
                inputs_after_sha256=base.sha(path.with_name('inputs_after.json'))))
        write(path, value)

    gymapi.acquire_gym = lambda: GymProxy(acquire(), records)
    base.write = variant_write
    try:
        return base.main()
    finally:
        base.write = write
        gymapi.acquire_gym = acquire


if __name__ == '__main__':
    sys.exit(main())
