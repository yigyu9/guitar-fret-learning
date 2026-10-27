"""Read-only song/model-contract audit. No simulator, training or source edits."""
import sys
sys.dont_write_bytecode = True
import argparse
from collections import Counter
from dataclasses import asdict
import hashlib
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def quantiles(values):
    ordered = sorted(values)
    def at(p):
        index = p*(len(ordered)-1)
        low = int(index)
        return ordered[low]+(ordered[min(low+1,len(ordered)-1)]-ordered[low])*(index-low)
    return {str(p):at(p) for p in (0,.1,.25,.5,.75,.9,1)}


def target_row(event,target):
    onset = event.score_time_s+target.traversal_offset_s
    release = min(target.sustain_until_s,target.release_s if target.release_s is not None else target.sustain_until_s)
    return dict(event_id=event.event_id,canonical_event_index=event.event_index,
                string_index_zero_based=target.string,user_string_number=target.string+1,
                fret=target.fret,finger=target.finger,source_note_on_s=target.note_on_s,
                canonical_crossing_s=onset,audible_end_s=release,audible_hold_s=release-onset,
                source_press_start_s=target.press_start_s,source_release_s=target.release_s,
                source_sustain_until_s=target.sustain_until_s,
                source_preparation_lead_s=onset-target.press_start_s if target.press_start_s is not None else None)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('/home/ajou/yigyu/3'))
    parser.add_argument('--out',type=Path,default=Path(__file__).with_suffix('.json'))
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0,str(root))
    bundle = root/'data/song_bundles/05_BN2-131-B_solo'
    sources = ['stability_adapter_2/fresh_music_v1/events.py',
               'stability_adapter_2/fresh_music_v1/environment.py',
               'stability_adapter_2/fresh_music_v1/environment_v2.py',
               'stability_adapter_2/fresh_music_v1/environment_v3.py',
               'stability_adapter_2/environment_contract_v1.py',
               'stability_adapter_2/learning_scene_v2.py',
               'stability_adapter_2/fresh_learning_v1/environment_v5.py',
               'stability_adapter_2/PLAYABLE_ENVELOPE_CONTRACT.md',
               'tab2body/__init__.py','tab2body/env/__init__.py',
               'tab2body/env/strike_goal_compiler.py','tab2body/full/events.py']
    paths = {p.resolve() for p in bundle.rglob('*') if p.is_file()}
    paths |= {root/p for p in sources}
    paths.add(Path(__file__).resolve())
    before = {str(p):digest(p) for p in sorted(paths)}
    from stability_adapter_2.fresh_music_v1.events import _compiler,load_music_task
    timeline = _compiler().compile_song_bundle_events(bundle,fail_on_unsupported=False)
    all_events = list(timeline.events)
    supported = [event for event in all_events if event.supported]
    targets = [(event,target) for event in supported for target in event.string_targets]
    rows = [target_row(event,target) for event,target in targets]
    transitions = []
    for index,(event,target) in enumerate(targets):
        previous = [(e,t) for e,t in targets[:index] if t.string==target.string]
        if not previous: continue
        prior,prior_target = previous[-1]
        if (prior_target.fret,prior_target.finger)==(target.fret,target.finger): continue
        end = min(prior_target.sustain_until_s,prior_target.release_s if prior_target.release_s is not None else prior_target.sustain_until_s)
        transitions.append(dict(previous=target_row(prior,prior_target),next=target_row(event,target),
                                free_interval_before_next_crossing_s=event.score_time_s+target.traversal_offset_s-end))
    density = {}
    for label in ('audible','source_preparation_window'):
        def interval(e,t):
            row = target_row(e,t)
            return (row['canonical_crossing_s'] if label=='audible' else row['source_press_start_s'],row['audible_end_s'])
        bounds = sorted({v for e,t in targets for v in interval(e,t)})
        hist = Counter()
        max_count,max_strings,max_example = 0,0,None
        for a,b in zip(bounds,bounds[1:]):
            midpoint = (a+b)/2
            active = [(e,t) for e,t in targets if interval(e,t)[0]<=midpoint<interval(e,t)[1]]
            hist[len(active)] += b-a
            if len(active)>max_count:
                max_count,max_example = len(active),dict(start_s=a,end_s=b,targets=[target_row(e,t) for e,t in active])
            max_strings = max(max_strings,len({t.string for e,t in active}))
        density[label] = dict(interval_definition='[canonical crossing, min(sustain,release))' if label=='audible' else '[source press_start, min(sustain,release))',
                              supported_targets_only=True,max_simultaneous_target_records=max_count,
                              max_simultaneous_distinct_strings=max_strings,duration_by_record_count_s=dict(hist),max_example=max_example)
    lookahead = {}
    for name,events in [('all_canonical_66_including_unsupported',all_events),('supported_only_65',supported)]:
        onsets = [e.score_time_s for e in events]
        spans = [onsets[i+3]-onsets[i] for i in range(len(onsets)-3)]
        next_four = [onsets[i+4]-onsets[i] for i in range(len(onsets)-4)]
        lookahead[name] = dict(current_onset_to_fourth_slot_onset_s=quantiles(spans),
            sample_count=len(spans),fraction_current_to_fourth_less_than_one_second=sum(s<1 for s in spans)/len(spans),
            just_after_previous_onset_to_next_fourth_onset_s=quantiles(next_four),
            semantics='at exact single-pick onset current event occupies slot1; immediately after it the next4 events occupy slots; original tempo seconds')
    selections = {}
    for stage in 'BCD':
        task = load_music_task(bundle,stage=stage)
        selections[stage] = dict(task=task.content_document(),source_origin_s=task.source_origin_s,
            preparation_physics_s=2.,task_preroll_s=task.preroll_s,score_duration_s=task.duration_s,
            physical_duration_s=2+task.duration_s,
            first_four=[dict(**target_row(e,t),task_crossing_s=task.task_time(e.score_time_s+t.traversal_offset_s),
                            physics_crossing_s=2+task.task_time(e.score_time_s+t.traversal_offset_s))
                        for e in task.events[:4] for t in e.string_targets])
    plan = json.loads((bundle/'training/strike_plan.json').read_text())
    hand = json.loads((bundle/'training/hand_position_targets.json').read_text())
    unsupported = [asdict(e) for e in all_events if not e.supported]
    report = dict(schema='fresh_music_pipeline_song_audit.v2',song_id=bundle.name,
        reproduction='PYTHONDONTWRITEBYTECODE=1 python '+str(Path(__file__).resolve()),
        scope='CPU source/data analysis only; no native simulation, model training, initial-pose certification or physical feasibility claim',
        definitions=dict(string_numbering='user1=high-e through6=low-E; canonical zero-based=user-1',
            supported='canonical event.supported true; unsupported event042 and both its target records excluded',
            changed_same_string_transition='current target and most recent earlier supported target on same canonical string; (fret,finger) differs; gap=next canonical crossing minus previous min(sustain,release)',
            hold='canonical crossing to min(source sustain,source release); not full source preparation window',
            final_timing_standard_s=.05,diagnostic_timing_standard_s=.1),
        inventory=dict(canonical_events=len(all_events),supported_canonical_events=len(supported),
            canonical_target_records=sum(len(e.string_targets) for e in all_events),supported_target_records=len(rows),
            first_canonical_onset_s=all_events[0].score_time_s,last_canonical_onset_s=all_events[-1].score_time_s,
            last_source_sustain_s=max(t.sustain_until_s for e in all_events for t in e.string_targets),
            inter_onset_gap_s=quantiles([b.score_time_s-a.score_time_s for a,b in zip(all_events,all_events[1:])]),
            fret_min=min(t.fret for e,t in targets),fret_max=max(t.fret for e,t in targets),
            supported_user_string_counts=dict(Counter(t.string+1 for e,t in targets)),
            source_preparation_lead_s=quantiles([r['source_preparation_lead_s'] for r in rows]),
            audible_hold_s=quantiles([r['audible_hold_s'] for r in rows])),
        selected_curricula=selections,lookahead4=lookahead,concurrency=density,
        short_audible_holds=dict(strictly_below_100ms_count=sum(r['audible_hold_s']<.1-1e-9 for r in rows),
            targets=[r for r in rows if r['audible_hold_s']<.1-1e-9],
            current_contract_issue='max(.1,.8*required_seconds) credited only in audible interval is impossible for these records'),
        changed_same_string_transitions=dict(total=len(transitions),
            gap_strictly_below_100ms_count=sum(r['free_interval_before_next_crossing_s']<.1-1e-9 for r in transitions),
            gap_strictly_below_50ms_count=sum(r['free_interval_before_next_crossing_s']<.05-1e-9 for r in transitions),
            all_records=transitions),
        unsupported=dict(events=unsupported,explanation='source notes42/43 at15.7547/15.778s share string4(user), frets11/9. Gap23.3ms<physical_min_gap50ms and group span<50ms: grouping produces alternate_restrike, canonical builder explicitly unsupported_alternate_restrike. Not a chord or missing finger.',
            physical_min_gap_s=plan['timeline']['physical_min_gap_s'],grouping_max_span_s=.05),
        timing_mode_audit=dict(current_label_at_tempo1='easy_training',actual_used_schedule='canonical score_time_s from original_times_s; stored easy_times_s is not used by MusicTask.task_time',
            original_event10_s=plan['timeline']['original_times_s'][10],stored_easy_event10_s=plan['timeline']['easy_times_s'][10]),
        hand_anchor_source=dict(first_frame=hand['frames'][0],last_frame_time_s=hand['frames'][-1]['t'],frames=len(hand['frames']),
            consumed_by_current_music_observation=False,scope='source suggested wrist anchor, not a physical reachability certificate'),
        current_observation_audit=dict(total_dimension=744,native_dimension=548,
            native_relative_geometry='15 body-origin markers positions and velocities in moving guitar G, including LH finger3 proxies and RH:pick; two palm rotation6 blocks; q/qdot/previous target/limits; world guitar pose/twist; pelvis-relative chest rotation',
            music_dimension=186,music_fields='6 current requested target rows x5 plus4 event slots x39; requested pressing/sounding are schedule flags, not measured contacts/sound',
            contact_dimension=4,contact_scope='aggregate left/right/trunk/head guitar-contact counts, no per-finger force',
            readiness_dimension=6,readiness_scope='one owner per string, distal3 origin geometry+contact+dwell; not verified string force',
            not_observed=['assigned target point_G or tip-to-target vector explicitly','per-finger/target contact validity and continuous dwell age','past matched/missed target identities and release-history state','pending crossing/rearm state','actual acoustic or physical string-vibration state']),
        design_findings=[
            dict(kind='evidence',claim='fixed4 event slots do not imply fixed seconds; dense passages reduce anticipation below1s for nearly half of supported event-index samples'),
            dict(kind='evidence',claim='current one-owner/string sounding-first selection suppresses future distinct fret/finger readiness while current note sounds; first fret7->5 same-string transition has zero free interval'),
            dict(kind='recommendation',claim='track assigned finger/target preparation candidates separately from currently sounding winner, hold ownership, and event matching; expose dwell/ownership and target-relative errors to model'),
            dict(kind='hypothesis',claim='a lower-fret different finger may physically prepare beneath a currently sounding higher fret; geometry/contact feasibility must be measured after initial-pose work, not assumed'),
            dict(kind='recommendation',claim='use actual audible duration as short-note hold denominator, keep preparation dwell separate, and audit release-before-next-target accounting'),
            dict(kind='recommendation',claim='make50ms the primary independent matching ledger and100ms a separate diagnostic ledger; do not derive final score merely by filtering100ms greedy matches'),
            dict(kind='recommendation',claim='retain event slots plus explicit time horizon/phase masks; select anticipation horizon from measured reachable preparation time after pose work, not arbitrary fixed4 semantic seconds')])
    after = {str(p):digest(p) for p in sorted(paths)}
    report.update(input_sha256_before=before,input_sha256_after=after,inputs_unchanged=before==after)
    with args.out.open('x') as stream: json.dump(report,stream,indent=2,ensure_ascii=False,allow_nan=False)
    print(json.dumps(dict(out=str(args.out),inputs_unchanged=before==after,supported_events=len(supported),
                         short_holds=report['short_audible_holds']['strictly_below_100ms_count'],changed_transitions=len(transitions))))


if __name__=='__main__': main()
