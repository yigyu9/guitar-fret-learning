"""Summarize saved per-control event pulses, distinct from full-episode metrics."""
from pathlib import Path
import hashlib
import json

P=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    out=P/'event_analysis';out.mkdir(exist_ok=False)
    source=P/'native/data/controls.json'
    hashes={str(p):sha(p) for p in (Path(__file__).resolve(),source)}
    (out/'inputs_before.json').write_text(json.dumps(hashes,indent=2)+'\n')
    rows=[r for r in json.loads(source.read_text()) if r['actor_used']]
    fields=('target_hit','physical_target_hit','physical_release','miss','wrong_crossing_count')
    totals={key:sum(r['info'][key][0] for r in rows) for key in fields}
    accepted=sum(sum(r['info']['accepted_release_mask'][0]) for r in rows)
    region_outside=[r['time_s'] for r in rows if not r['guitar_in_playable_region']]
    last=rows[-1]
    summary={'policy_samples':len(rows),'source_per_control_pulse_totals':totals,
        'accepted_release_mask_true_total':accepted,'running_strike_f1_last':last['info']['strike_f1'][0],
        'running_tip_ready_success_rate_last':last['info']['tip_ready_success_rate'][0],
        'source_song_time_after_last_s':last['source_song_time_after_s'],
        'source_event_index_after_last':last['info']['event_index_after_step'][0],
        'source_motor_phases_observed':sorted(set(r['info']['motor_phase'][0] for r in rows)),
        'outside_region_policy_samples':len(region_outside),
        'first_outside_region_policy_sample_s':min(region_outside) if region_outside else None,
        'last_control_tip_target_distance_m':last['info']['tip_target_distance'][0],
        'full_episode_finished':bool(last.get('done')),
        'full_episode_metrics_available':bool(last['info'].get('strike_episode_f1')),
        'interpretation':'Counts are saved step pulses over 3s of policy, not complete-song TP/FP/FN or episode F1. Readiness motor phase 0 remained active.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    changed=[p for p,h in hashes.items() if sha(Path(p))!=h]
    (out/'inputs_after.json').write_text(json.dumps({'unchanged':not changed,'changed':changed},indent=2)+'\n')
    assert not changed

if __name__=='__main__':main()
