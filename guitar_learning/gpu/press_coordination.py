"""선택된 발음 목표 집합이 일정한 동시 압현 구간을 구성한다."""


def audible_sections(targets, selected):
    """발음 목표가2개 이상인 구간만 반환한다. 준비 시간은 제외한다."""
    chosen = [index for index, keep in enumerate(selected) if keep]
    boundaries = sorted({time for index in chosen
                         for time in (targets[index].onset_s, targets[index].end_s)})
    result = []
    for start, end in zip(boundaries, boundaries[1:]):
        active = tuple(index for index in chosen
                       if targets[index].onset_s <= start and targets[index].end_s >= end)
        if len(active) < 2 or end <= start:
            continue
        if result and result[-1]['target_indices'] == active and result[-1]['end_s'] == start:
            result[-1]['end_s'] = end
        else:
            result.append(dict(start_s=start, end_s=end, target_indices=active))
    return result


def validate_assignments(targets):
    for index, target in enumerate(targets):
        if target.end_s <= target.onset_s:
            raise ValueError('Compact press v3 requires positive audible note durations')
        for other in targets[index+1:]:
            if (max(target.onset_s, other.onset_s) < min(target.end_s, other.end_s) and
                    (target.string == other.string or target.finger == other.finger)):
                raise ValueError('Overlapping audible targets require distinct strings and fingers; barre unsupported')
