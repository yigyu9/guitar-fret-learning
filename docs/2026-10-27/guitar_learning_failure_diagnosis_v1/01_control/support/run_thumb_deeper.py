"""Explicit diagnostic goal-depth override; production physics/predicates unchanged."""
import hashlib
import json
from pathlib import Path
import sys


def main():
    import isaacgym
    from guitar_learning.tool.validation import thumb_contact_probe as probe
    out=Path(sys.argv[sys.argv.index('--out')+1]).resolve()
    source=Path(__file__).resolve();before=hashlib.sha256(source.read_bytes()).hexdigest()
    original=probe.approach_gap
    def diagnostic_gap(elapsed_s):
        return -.0001*min(max(int(elapsed_s/1.5),0),9)
    probe.approach_gap=diagnostic_gap
    try:
        probe.main()
    finally:
        probe.approach_gap=original
        if out.exists():
            metadata=dict(wrapper=str(source),wrapper_sha256=before,
                wrapper_unchanged=hashlib.sha256(source.read_bytes()).hexdigest()==before,
                change_scope='diagnostic requested witness gap only; no physical-property, force-cap, state or predicate change',
                original_minimum_requested_gap_m=-.0003,diagnostic_minimum_requested_gap_m=-.0009,
                schedule='minus0.1mm each1.5s, capped atminus0.9mm; original contact/hold/release controller preserved',
                interpretation='limited initial thumb targets+/-15deg; not proof about full native reachability')
            (out/'diagnostic_override.json').write_text(json.dumps(metadata,indent=2)+'\n')
            path=out/'report.json'
            if path.exists():
                raw=path.read_text();(out/'base_probe_report.json').write_text(raw)
                report=json.loads(raw);report['diagnostic_override']=metadata
                report['approach_gap_schedule']=metadata['schedule']
                path.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
