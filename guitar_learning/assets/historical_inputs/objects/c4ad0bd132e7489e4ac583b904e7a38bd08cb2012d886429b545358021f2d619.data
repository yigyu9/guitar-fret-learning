"""Single-note fretting quality from unchanged native contact evidence.

Body/cell attribution respects the original2mm wire margin. Uncertain features
are diagnostics, not convicted wrong presses. No pressure or sound is inferred.
"""
from dataclasses import asdict
import math
import numpy as np
from .fretting_v1 import FretContract
from .music_task import ScoreTarget

FINGERS = {1: 'index', 2: 'middle', 3: 'ring', 4: 'pinky'}
FRETTING_QUALITY_METADATA = dict(schema='guitar_learning.fretting_quality.v1',
    task='exactly one fretted ScoreTarget; original FretContract/contact evidence thresholds retained',
    positive='original target contact candidate and evidence preserved',
    clean='positive target without confirmed higher fret, wrong fret or wrong assignment',
    higher='qualified same-string higher fret forbidden; named body/cell attribution respects original wire margin',
    lower='simultaneous lower fret permitted with positive target; lower-only contact is wrong target position',
    assignment='other finger on same goal is wrong only when original designated target candidate is absent',
    other_string='diagnostic only; no blanket penalty',
    uncertain='unaligned witness, lane ambiguity or body/cell disagreement is diagnostic, not convicted error',
    root_attribution='target wire margin first; otherwise require an interior unambiguous geometric cell',
    target_string_contact='all qualified target-string finger2/3 neck features, including uncertain fret attribution, for separate release supervision',
    scope='native contact/body/cell evidence; no calibrated pressure, string vibration, pitch or sound')


def classify_fretting(geometry, target, evidence, contract):
    if (not isinstance(target, ScoreTarget) or type(target.fret) is not int or not 1 <= target.fret <= 22 or
            type(target.finger) is not int or target.finger not in FINGERS or type(target.string) is not int or target.string not in range(6) or
            not isinstance(contract, FretContract)):
        raise ValueError('single fretted ScoreTarget and explicit FretContract required')
    expected = dict(string_number=target.string+1, musical_fret=target.fret, finger=FINGERS[target.finger])
    if evidence.get('target') != expected or evidence.get('contract') != asdict(contract):
        raise ValueError('aligned original target/contact contract required')
    positive = evidence.get('fretting_contact_candidate')
    if type(positive) is not bool or positive != bool(evidence.get('valid_evidence_ids')):
        raise ValueError('original explicit candidate and valid evidence IDs required')
    starts, ends, wires = [np.asarray(geometry[k], dtype=float) for k in ('starts_G_m', 'ends_G_m', 'fret_markers_G_m')]
    if (starts.shape != (6,3) or ends.shape != (6,3) or wires.shape != (23,3) or
            not all(np.isfinite(a).all() for a in (starts, ends, wires)) or np.any(np.abs(ends[:,1]-starts[:,1]) < 1e-12)):
        raise ValueError('finite measured nonparallel string lines and23 fret markers required')
    intervals = [(min(a[1],b[1]),max(a[1],b[1])) for a,b in zip(wires[:-1],wires[1:])]
    lo, hi = intervals[target.fret-1]; margin = contract.fret_cell_margin_m
    desired = {'human/LH:'+FINGERS[target.finger]+str(n) for n in (2,3)}
    diagnostics=[];uncertain=[];incidental=[];lower=[];higher=[];other_goal_finger=[];target_string_contacts=[]
    for e in evidence['contact_evidence']:
        human, guitar, identity = e['human_body'], e['guitar_body'], e['evidence_id']
        if not any(human == 'human/LH:'+finger+str(n) for finger in ('thumb',*FINGERS.values()) for n in (2,3)):
            continue
        body_fret = None
        if guitar.startswith('guitar/G:fret') and guitar[len('guitar/G:fret'):].isdigit():
            body_fret = int(guitar[len('guitar/G:fret'):])
        if guitar != 'guitar/guitar' and body_fret not in range(1,23):
            continue
        value, gap = float(e['raw_lambda']), float(e['body_pair_witness_gap_m'])
        point = np.asarray(e['guitar_feature_G_m'], dtype=float)
        if not math.isfinite(value) or not math.isfinite(gap) or point.shape != (3,) or not np.isfinite(point).all():
            raise ValueError('finite original contact features required')
        if value <= 0:continue
        row = dict(evidence_id=identity,human_body=human,guitar_body=guitar,assigned_fret=None,
            nearest_string=None,geometric_cells=[],classification='uncertain',reason=None)
        diagnostics.append(row)
        if gap < 0 or gap > contract.witness_max_gap_m:
            row['reason']='unaligned_pair_witness';uncertain.append(identity);continue
        fraction = (point[1]-starts[:,1])/(ends[:,1]-starts[:,1])
        projected = starts+fraction[:,None]*(ends-starts)
        lateral = np.abs(projected[:,0]-point[0]);nearest = int(np.argmin(lateral))
        row.update(nearest_string=nearest+1,lateral_m=float(lateral[nearest]),
            height_m=float(point[2]-projected[nearest,2]))
        if (any(lateral[i] <= lateral[nearest]+1e-12 for i in range(6) if i != nearest) or
                not 0 <= fraction[nearest] <= 1 or lateral[nearest] > contract.lateral_max_m or
                abs(point[2]-projected[nearest,2]) > contract.height_abs_max_m):
            row['reason']='ambiguous_or_outside_string_geometry';uncertain.append(identity);continue
        if nearest == target.string:
            target_string_contacts.append(identity)
        cells = [i+1 for i,(a,b) in enumerate(intervals) if a <= point[1] <= b]
        row['geometric_cells'] = cells
        if body_fret is not None:
            a,b = intervals[body_fret-1]
            assigned = body_fret if a-margin <= point[1] <= b+margin else None
            row['attribution']='named_fret_body_with_its_wire_margin'
        elif lo-margin <= point[1] <= hi+margin:
            assigned = target.fret
            row['attribution']='original_target_wire_margin'
        else:
            # An unlabelled root feature near a wire cannot uniquely establish
            # which fret is being pressed. Require an interior geometric cell.
            assigned = cells[0] if len(cells)==1 and min(point[1]-intervals[cells[0]-1][0],
                intervals[cells[0]-1][1]-point[1]) > margin else None
            row['attribution']='interior_geometric_cell'
        if assigned is None:
            row['reason']='body_cell_disagreement_or_wire_ambiguity';uncertain.append(identity);continue
        row['assigned_fret']=assigned
        if nearest != target.string:
            row['classification']='incidental_other_string';incidental.append(identity)
        elif assigned > target.fret:
            row['classification']='forbidden_higher_fret';higher.append(identity)
        elif assigned < target.fret:
            row['classification']='lower_fret';lower.append(identity)
        elif human not in desired:
            row['classification']='other_finger_on_target';other_goal_finger.append(identity)
        else:
            row['classification']='target'
    wrong_assignment = other_goal_finger if not positive else []
    wrong_fret = higher+(lower if not positive else [])
    wrong = bool(wrong_fret or wrong_assignment)
    clean = bool(positive and not wrong)
    return dict(schema='guitar_learning.fretting_quality.v1',positive_target_candidate=positive,
        clean_target_candidate=clean,status='wrong' if wrong else 'correct' if clean else 'missing',
        wrong_finger=bool(wrong_assignment),wrong_assignment=bool(wrong_assignment),
        wrong_fret=bool(wrong_fret),higher_fret=bool(higher),
        incidental_other_string=bool(incidental),uncertain=bool(uncertain),
        positive_evidence_ids=list(evidence['valid_evidence_ids']),
        target_string_contact_evidence_ids=list(target_string_contacts),
        wrong_finger_evidence_ids=list(wrong_assignment),wrong_assignment_evidence_ids=list(wrong_assignment),
        wrong_fret_evidence_ids=list(wrong_fret),higher_fret_evidence_ids=list(higher),
        allowed_lower_fret_evidence_ids=list(lower) if positive else [],
        incidental_other_string_evidence_ids=list(incidental),uncertain_evidence_ids=list(uncertain),
        feature_diagnostics=diagnostics,
        scope='single fretted target; contact/body/cell evidence only; no pressure/audio or other-string blanket penalty')
