"""Precommit actual score goals, then reuse the current source-FK search."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/ajou/yigyu/3')
BASE = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('select', 'geometry'))
    parser.add_argument('--group', type=int, choices=(16,24), default=24)
    parser.add_argument('--max-nfev', type=int, default=160)
    args = parser.parse_args()
    from guitar_learning.tool.validation import press_acquisition as old
    from guitar_learning.song.task import make_task
    task = make_task(old.DEFAULT_BUNDLE)
    selection = BASE/'selection_precommitted.json'
    if args.command == 'select':
        if selection.exists():
            raise FileExistsError(selection)
        first = old.select_targets(task)
        count = Counter((t.string,t.fret,t.finger) for t in task.targets)
        expanded = []
        for finger in range(1,5):
            chosen = [(g['string'],g['fret'],g['finger']) for g in first if g['finger']==finger]
            keys = [k for k in count if k[2]==finger]
            while len(chosen)<6:
                remaining = [k for k in keys if k not in chosen]
                strings = {k[0] for k in chosen}
                pick = min(remaining,key=lambda k:(-(k[0] not in strings),
                    -min(abs(k[1]-g[1]) for g in chosen),-count[k],k[1],k[0]))
                chosen.append(pick)
            for k in chosen:
                source = next(i for i,t in enumerate(task.targets) if (t.string,t.fret,t.finger)==k)
                expanded.append(dict(row=len(expanded),string=k[0],physical_string=k[0]+1,
                    fret=k[1],finger=k[2],frequency=count[k],source_note_index=source,
                    target_id=task.targets[source].target_id))
        payload = dict(schema='guitar_learning.contact_diagnosis_selection.v1',
            bundle=str(old.DEFAULT_BUNDLE), goals16=first, goals24=expanded,
            trace_rows16=[0,4,8,12,1,15], trace_rows24=[0,6,12,18,1,21],
            rules='retain original four/finger, then unrepresented string, maximum minimum fret separation, frequency and deterministic fret/string order',
            case_scope='predeclared before geometry or GPU outcomes; original source notes only',
            source_note_intervals=[dict(index=i,onset_s=t.onset_s,end_s=t.end_s,press_s=t.press_s)
                                   for i,t in enumerate(task.targets)],
            source_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
        selection.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
        print('precommitted16and24',selection)
        return
    payload = json.loads(selection.read_text())
    goals, trace = payload['goals'+str(args.group)], payload['trace_rows'+str(args.group)]
    original_select, original_rows = old.select_targets, old.REPRESENTATIVE_ROWS
    old.select_targets = lambda current_task: goals
    old.REPRESENTATIVE_ROWS = tuple(trace)
    try:
        old.search_geometry(old.DEFAULT_BUNDLE,BASE/('geometry%d'%args.group),max_nfev=args.max_nfev)
    finally:
        old.select_targets,old.REPRESENTATIVE_ROWS = original_select,original_rows
    out = BASE/('geometry%d'%args.group)
    (out/'diagnostic_adapter.json').write_text(json.dumps(dict(
        group=args.group,selection=str(selection),selection_sha256=hashlib.sha256(selection.read_bytes()).hexdigest(),
        script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        scope='same source FK/optimizer/patch/action bounds; explicit goal selection override only; no GPU physics',
        training_success=False),indent=2)+'\n')


if __name__=='__main__':
    main()
