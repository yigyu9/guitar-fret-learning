"""Selective LH inter-finger collision masks, preserving every other pair."""
import copy
import hashlib
import itertools
import json


FINGERS = ('thumb', 'index', 'middle', 'ring', 'pinky')
FINGER_MASKS = {finger: 1 << (20 + i) for i, finger in enumerate(FINGERS)}
SEGMENT_FINGER = {'LH:' + finger + str(segment): finger
                  for finger in FINGERS for segment in (1, 2, 3)}
NEW_BITS = sum(FINGER_MASKS.values())
SCHEMA = 'guitar_learning.left_inter_finger_collision.v1'


def _rows(shapes):
    return [(name, index, row['filter']) for name, values in shapes.items()
            for index, row in enumerate(values)]


def left_hand_collision_properties(human_shapes):
    """Replace the common LH bit with five disjoint finger bits.

    Same-finger segments and all previously excluded palm/arm/proxy pairs
    remain excluded. Only the 90 distinct-finger segment pairs change.
    Physical geometry, friction, offsets and source input stay unchanged.
    """
    before = _rows(human_shapes)
    if any(type(mask) is not int or mask < 0 or mask >= (1 << 20)
           for _, _, mask in before):
        raise ValueError('Pinned low-20-bit human collision masks required')
    if any(len(human_shapes.get(name, [])) != 1 or
           human_shapes[name][0]['filter'] != 128 for name in SEGMENT_FINGER):
        raise ValueError('Pinned 15 physical LH segments with common filter128 required')
    result = copy.deepcopy(human_shapes)
    for name, values in result.items():
        for row in values:
            if name in SEGMENT_FINGER:
                row['filter'] = FINGER_MASKS[SEGMENT_FINGER[name]]
            elif row['filter'] & 128:
                row['filter'] |= NEW_BITS
    after = _rows(result)
    changed, matrix = [], []
    for i, j in itertools.combinations(range(len(before)), 2):
        a, b = before[i], before[j]
        was_enabled = (a[2] & b[2]) == 0
        enabled = (after[i][2] & after[j][2]) == 0
        expected_change = (a[0] in SEGMENT_FINGER and b[0] in SEGMENT_FINGER and
                           SEGMENT_FINGER[a[0]] != SEGMENT_FINGER[b[0]])
        if enabled != (True if expected_change else was_enabled):
            raise ValueError('Selective LH collision pair invariant failed')
        matrix.append([a[0], a[1], b[0], b[1], enabled])
        if was_enabled != enabled:
            changed.append([a[0], b[0]])
    if len(changed) != 90:
        raise ValueError('Exactly 90 distinct-finger pairs must become enabled')
    encoded = json.dumps(matrix, separators=(',', ':')).encode()
    contract = dict(schema=SCHEMA, native_rule='enabled iff (filterA & filterB) == 0',
        finger_masks=FINGER_MASKS.copy(), enabled_distinct_finger_pairs=len(changed),
        preserved_other_human_shape_pairs=len(matrix)-len(changed),
        human_pair_matrix_sha256=hashlib.sha256(encoded).hexdigest(),
        changed_filters=[dict(body=a[0], shape=a[1], before=a[2], after=b[2])
                         for a, b in zip(before, after) if a[2] != b[2]],
        external_pair_preservation='Checked against actual compound-guitar and chair filters; '
            'the two source guitar proxies have no physical shape in the GPU compound asset.')
    return result, contract


def verify_external_filter_preservation(before, after, external_filters):
    """Check the actual guitar/chair filters before native submission."""
    if any(type(mask) is not int or mask < 0 or mask >= (1 << 20)
           for mask in external_filters):
        raise ValueError('External filter overlaps reserved LH finger bits')
    for old, new in zip(_rows(before), _rows(after)):
        for mask in external_filters:
            if ((old[2] & mask) == 0) != ((new[2] & mask) == 0):
                raise ValueError('External collision pair changed')
