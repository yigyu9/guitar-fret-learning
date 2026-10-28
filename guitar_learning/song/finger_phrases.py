"""원곡의 시각과 목표를 바꾸지 않는 불변 부분곡 보기를 구성한다.

읽는 순서: 구절·목록 자료형 → 겹침 그룹과 구절 목록 생성 → 손가락별 균형 표본 선택.
"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math


SCHEMA = 'guitar_learning.finger_phrases.v1'


def _sha(document):
    payload = json.dumps(document, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(payload.encode()).hexdigest()


@dataclass(frozen=True)
class FingerPhrase:
    phrase_id: str
    target_indices: tuple
    start_s: float
    end_s: float
    next_press_s: object
    duration_ticks: int
    score_offset_s: float
    opportunities: tuple  # 검지·중지·약지·소지의 음 개수

    @property
    def fingers(self):
        return tuple(i + 1 for i, count in enumerate(self.opportunities) if count)


@dataclass(frozen=True)
class FingerPhraseCatalog:
    phrases: tuple
    closed_groups: tuple
    source_targets: tuple
    source_provenance_json: str
    preparation_s: float
    tail_s: float
    control_hz: int

    @property
    def source_sha256(self):
        return _sha(dict(targets=self.source_targets,
                         provenance=json.loads(self.source_provenance_json)))

    def _document(self):
        return dict(schema=SCHEMA, preparation_s=self.preparation_s,
                    tail_s=self.tail_s, control_hz=self.control_hz,
                    source_targets=[dict(row) for row in self.source_targets],
                    source_provenance=json.loads(self.source_provenance_json),
                    source_sha256=self.source_sha256,
                    closed_groups=[list(group) for group in self.closed_groups],
                    recovery_gaps=list(self.recovery_gaps),
                    phrases=[asdict(phrase) for phrase in self.phrases])

    @property
    def recovery_gaps(self):
        """인위적으로 더한 준비 구간을 제외하고 원곡의 손가락별 양수 간격을 구한다."""
        targets = [dict(row) for row in self.source_targets]
        result = []
        for finger in range(1, 5):
            ordered = sorted((i for i, target in enumerate(targets) if target['finger'] == finger),
                             key=lambda i: (targets[i]['press_s'], i))
            if not ordered:
                continue
            owner = ordered[0]
            end = targets[owner]['end_s']
            for index in ordered[1:]:
                start = targets[index]['press_s']
                if start > end:
                    result.append(dict(finger=finger, previous_index=owner, next_index=index,
                                       end_s=end, next_press_s=start, gap_s=start - end))
                if targets[index]['end_s'] > end:
                    owner, end = index, targets[index]['end_s']
        return tuple(result)

    @property
    def fingerprint(self):
        return _sha(self._document())

    def document(self):
        return dict(self._document(), fingerprint=self.fingerprint)

    @classmethod
    def from_document(cls, document):
        """손상되지 않은 원래 목록만 복원하며 일정을 새로 해석하지 않는다."""
        expected = dict(document)
        fingerprint = expected.pop('fingerprint', None)
        if expected.get('schema') != SCHEMA or _sha(expected) != fingerprint:
            raise ValueError('phrase catalogue schema/fingerprint mismatch')
        phrases = tuple(FingerPhrase(**dict(row,
                            target_indices=tuple(row['target_indices']),
                            opportunities=tuple(row['opportunities'])))
                        for row in expected['phrases'])
        catalog = cls(phrases, tuple(tuple(g) for g in expected['closed_groups']),
                      tuple(tuple(sorted(row.items())) for row in expected['source_targets']),
                      json.dumps(expected['source_provenance'], sort_keys=True, allow_nan=False),
                      expected['preparation_s'], expected['tail_s'], expected['control_hz'])
        if catalog.document() != document:
            # JSON 배열과 파이썬 튜플은 비교 결과가 다르므로 체크포인트 계약이 쓰는
            # 표준 표현으로 비교한다.
            if _sha(catalog.document()) != _sha(document):
                raise ValueError('phrase catalogue is not canonical')
        return catalog


def build_phrase_catalog(task, *, preparation_s=3., tail_s=.5, control_hz=60):
    """겹침이 더 이어지지 않는 그룹을 유지하고 인접 그룹의 짧은 보기를 추가한다.
    
    음 하나뿐인 그룹은 이웃 그룹과 결합하고 큰 겹침 그룹은 나누지 않는다.
    마지막 종료와 다음 압현 사이에 유효한 로컬 제어 경계가 없으면 보기를
    늘린다. 보기끼리 겹칠 수 있으므로 길이의 합이 아닌 원 음표 ID의 합집합이
    원곡을 한 번씩 포함한다.
    """
    if (isinstance(preparation_s, bool) or not math.isfinite(preparation_s) or
            preparation_s < 0 or isinstance(tail_s, bool) or
            not math.isfinite(tail_s) or tail_s <= 0 or
            type(control_hz) is not int or control_hz < 1):
        raise ValueError('finite nonnegative preparation, positive tail and integer Hz required')
    targets = task.targets
    if not targets or any(t.finger not in (1, 2, 3, 4) for t in targets):
        raise ValueError('finger phrases require nonempty fretted targets')
    order = sorted(range(len(targets)), key=lambda i: (targets[i].press_s, i))
    groups = []
    group, end = [], -math.inf
    for index in order:
        target = targets[index]
        if group and target.press_s > end:
            groups.append(tuple(group))
            group = []
        group.append(index)
        end = max(end, target.end_s) if len(group) > 1 else target.end_s
    groups.append(tuple(group))

    def interval(first, last):
        indices = tuple(i for group in groups[first:last + 1] for i in group)
        start = min(targets[i].press_s for i in indices)
        end = max(targets[i].end_s for i in indices)
        offset = start - preparation_s
        next_press = targets[groups[last + 1][0]].press_s if last + 1 < len(groups) else None
        # 음 끝이 경계와 정확히 같으면 그다음 경계를 사용한다.
        # 마지막 음은 자연 종료 전에 끝나야 한다.
        minimum = math.floor((end - offset) * control_hz + 1e-9) + 1
        maximum = (math.floor((next_press - offset) * control_hz + 1e-9)
                   if next_press is not None else None)
        desired = math.ceil((end - offset + tail_s) * control_hz - 1e-9)
        ticks = min(desired, maximum) if maximum is not None else desired
        return indices, start, end, next_press, offset, minimum, ticks

    ranges = set()
    for first in range(len(groups)):
        last = first
        while sum(len(group) for group in groups[first:last + 1]) < 2 and last + 1 < len(groups):
            last += 1
        if first == last and len(groups[first]) == 1 and first > 0:
            first -= 1
        while True:
            *_, minimum, ticks = interval(first, last)
            if ticks >= minimum:
                break
            last += 1
        ranges.add((first, last))
        # 연속된 2~6음 문맥을 추가하되 겹침이 닫힌 그룹을 나누지 않는다.
        while last + 1 < len(groups):
            candidate = last + 1
            if sum(len(group) for group in groups[first:candidate + 1]) > 6:
                break
            while True:
                *_, minimum, ticks = interval(first, candidate)
                if ticks >= minimum:
                    break
                candidate += 1
            ranges.add((first, candidate))
            last = candidate

    phrases = []
    for first, last in sorted(ranges):
        indices, start, end, next_press, offset, _, ticks = interval(first, last)
        counts = tuple(sum(targets[i].finger == finger for i in indices) for finger in range(1, 5))
        phrases.append(FingerPhrase(f'phrase-{first:03d}-{last:03d}', indices,
                                    start, end, next_press, ticks, offset, counts))
    if {i for phrase in phrases for i in phrase.target_indices} != set(range(len(targets))):
        raise ValueError('phrase catalogue does not cover every original target')
    provenance = dict(task.provenance or {})
    source_rows = tuple(tuple(sorted(asdict(target).items())) for target in targets)
    return FingerPhraseCatalog(tuple(phrases), tuple(groups), source_rows,
                               json.dumps(provenance, sort_keys=True, allow_nan=False),
                               float(preparation_s), float(tail_s), control_hz)


class BalancedPhraseSampler:
    """다음 선택 상태를 체크포인트로 복원할 수 있는 손가락 묶음 순환 선택기다."""
    def __init__(self, catalog):
        self.catalog = catalog
        self.buckets = tuple(tuple(sorted(
            (i for i, p in enumerate(catalog.phrases) if p.opportunities[finger]),
            key=lambda i: (len(catalog.phrases[i].target_indices), catalog.phrases[i].phrase_id)))
            for finger in range(4))
        self.present = tuple(i for i, bucket in enumerate(self.buckets) if bucket)
        if not self.present:
            raise ValueError('phrase catalogue has no finger opportunities')
        self.reset_count = 0
        self.cursors = [0] * 4
        self.opportunities = [0] * 4

    def next(self):
        finger = self.present[self.reset_count % len(self.present)]
        bucket = self.buckets[finger]
        phrase = self.catalog.phrases[bucket[self.cursors[finger] % len(bucket)]]
        self.cursors[finger] += 1
        self.reset_count += 1
        self.opportunities = [a + b for a, b in zip(self.opportunities, phrase.opportunities)]
        return phrase

    def state_dict(self):
        return dict(schema='guitar_learning.balanced_phrase_sampler.v1',
                    catalog_fingerprint=self.catalog.fingerprint, reset_count=self.reset_count,
                    cursors=list(self.cursors), opportunities=list(self.opportunities))

    def load_state_dict(self, state):
        if (set(state) != set(self.state_dict()) or
                state['schema'] != self.state_dict()['schema'] or
                state['catalog_fingerprint'] != self.catalog.fingerprint):
            raise ValueError('phrase sampler contract mismatch')
        count, cursors, opportunities = state['reset_count'], state['cursors'], state['opportunities']
        if (type(count) is not int or count < 0 or len(cursors) != 4 or len(opportunities) != 4 or
                any(type(value) is not int or value < 0 for value in [*cursors, *opportunities]) or
                sum(cursors) != count or any(cursors[i] for i in range(4) if i not in self.present)):
            raise ValueError('invalid phrase sampler counters')
        for rank, finger in enumerate(self.present):
            if cursors[finger] != count // len(self.present) + (rank < count % len(self.present)):
                raise ValueError('phrase sampler counters violate round robin')
        expected_opportunities = [0] * 4
        for finger in self.present:
            bucket = self.buckets[finger]
            cycles, remainder = divmod(cursors[finger], len(bucket))
            for rank, index in enumerate(bucket):
                repetitions = cycles + (rank < remainder)
                for axis, notes in enumerate(self.catalog.phrases[index].opportunities):
                    expected_opportunities[axis] += repetitions * notes
        if list(opportunities) != expected_opportunities:
            raise ValueError('phrase sampler opportunity counters do not match its selections')
        self.reset_count, self.cursors, self.opportunities = count, list(cursors), list(opportunities)
