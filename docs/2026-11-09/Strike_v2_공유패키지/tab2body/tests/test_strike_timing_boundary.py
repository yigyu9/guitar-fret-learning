"""허용창 양끝 포함·바로 바깥 제외와 기존 오차 반환 의미를 CPU로 검사한다."""
from __future__ import annotations

from pathlib import Path
import sys

import torch


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from env.strike_events import strike_premature_release, strike_traversal_timing


def check_boundaries(dtype):
    # target=1, left=.05는 float32 오차 비교에서 -.0500000119로 탈락하던 사례다.
    # float64의 target=1, right=.05 역시 +.050000000000000044로 탈락했다.
    center = torch.tensor([1., 3., 34.7719, 1.], dtype=dtype)
    offsets = torch.tensor([[0.], [0.], [.007], [-.013]], dtype=dtype)
    left = torch.tensor([.05, .05, .017, .03], dtype=dtype)
    right = torch.tensor([.05, .05, .041, .08], dtype=dtype)
    expected = center[:, None] + offsets
    lower = expected - left[:, None]
    upper = expected + right[:, None]
    valid = torch.ones_like(expected, dtype=torch.bool)

    for release in (lower, upper):
        result = strike_traversal_timing(release, valid, valid, center, offsets, left, right)
        assert result['complete'].all()
        assert result['timing_ok'].all(), (dtype, release, result)
        assert not result['early'].any()
        assert not result['late'].any()
        # 부호 오차와 통계는 여전히 release - (center + offset)이다.
        error = release - expected
        assert torch.equal(result['per_string_error_s'], error)
        assert torch.equal(result['worst_error_s'], error[:, 0])
        assert torch.equal(result['rms_error_s'], error.abs()[:, 0])
        premature = strike_premature_release(valid, release, center, offsets, left)
        assert not premature['premature'].any()
        assert torch.equal(premature['signed_error_s'], error)

    below = torch.nextafter(lower, torch.full_like(lower, -float('inf')))
    above = torch.nextafter(upper, torch.full_like(upper, float('inf')))
    for release, early in ((below, True), (above, False)):
        result = strike_traversal_timing(release, valid, valid, center, offsets, left, right)
        assert not result['timing_ok'].any(), (dtype, release, result)
        assert bool(result['early'].all()) == early
        assert bool(result['late'].all()) != early
        premature = strike_premature_release(valid, release, center, offsets, left)
        assert bool(premature['premature'].all()) == early

    # 바로 안쪽 한 ULP도 정상 허용되며 epsilon 확대는 필요하지 않다.
    for release in (torch.nextafter(lower, upper), torch.nextafter(upper, lower)):
        result = strike_traversal_timing(release, valid, valid, center, offsets, left, right)
        assert result['timing_ok'].all()


def check_strum_masks_and_statistics(dtype):
    center = torch.tensor([1.], dtype=dtype)
    offsets = torch.tensor([[-.01, 0., .01, 0.]], dtype=dtype)
    traversal = torch.tensor([[True, True, True, False]])
    left = torch.tensor([.03], dtype=dtype)
    right = torch.tensor([.08], dtype=dtype)
    expected = center[:, None] + offsets
    # 서로 다른 현이 좌측 경계, 정시, 우측 경계에 닿은 완주다.
    release = expected.clone()
    release[:, 0] -= left
    release[:, 2] += right
    release[:, 3] = 100.  # traversal 밖의 유한 표본은 판정을 바꾸지 않는다.
    result = strike_traversal_timing(release, traversal, traversal, center, offsets, left, right)
    assert result['complete'].item() and result['timing_ok'].item()
    error = torch.where(traversal, release-expected, torch.zeros_like(release))
    assert torch.equal(result['per_string_error_s'], error)
    assert torch.equal(result['actual_duration_s'], release[:, 2]-release[:, 0])
    assert torch.equal(result['planned_duration_s'], offsets[:, 2]-offsets[:, 0])
    assert torch.equal(result['duration_error_s'],
                       (release[:, 2]-release[:, 0])-(offsets[:, 2]-offsets[:, 0]))
    assert torch.equal(result['rms_error_s'], (error.square().sum(-1)/3).sqrt())
    assert torch.equal(result['worst_error_s'], error[:, 2])

    missing = traversal.clone()
    missing[:, 2] = False
    incomplete = strike_traversal_timing(release, missing, traversal, center, offsets, left, right)
    assert not incomplete['complete'].item()
    assert not incomplete['timing_ok'].item()
    assert not incomplete['early'].item() and not incomplete['late'].item()
    assert incomplete['per_string_error_s'][0, 2] == 0
    assert incomplete['duration_error_s'].item() == 0

    accepted = torch.tensor([[True, False, False, False]])
    boundary = strike_premature_release(accepted, release, center, offsets, left)
    assert not boundary['premature'].item()
    just_before = release.clone()
    just_before[:, 0] = torch.nextafter(release[:, 0], torch.full_like(release[:, 0], -float('inf')))
    assert strike_premature_release(accepted, just_before, center, offsets, left)['premature'].item()
    ignored = release.clone()
    ignored[:, 3] = -100.
    assert not strike_premature_release(accepted, ignored, center, offsets, left)['premature'].item()


def check_nonfinite_rejected(dtype):
    valid = torch.tensor([[True]])
    for invalid in (float('nan'), float('inf'), -float('inf')):
        for field in ('release', 'center', 'offset', 'left', 'right'):
            values = dict(release=torch.tensor([[1.]], dtype=dtype),
                center=torch.tensor([1.], dtype=dtype), offset=torch.tensor([[0.]], dtype=dtype),
                left=torch.tensor([.05], dtype=dtype), right=torch.tensor([.05], dtype=dtype))
            values[field].fill_(invalid)
            try:
                strike_traversal_timing(values['release'], valid, valid, values['center'],
                    values['offset'], values['left'], values['right'])
            except ValueError:
                pass
            else:
                raise AssertionError('non-finite traversal input was accepted: '+field)
            if field != 'right':
                try:
                    strike_premature_release(valid, values['release'], values['center'],
                        values['offset'], values['left'])
                except ValueError:
                    pass
                else:
                    raise AssertionError('non-finite premature input was accepted: '+field)


def main():
    assert not torch.cuda.is_initialized(), 'CPU checks must not initialize CUDA'
    for dtype in (torch.float32, torch.float64):
        check_boundaries(dtype)
        check_strum_masks_and_statistics(dtype)
        check_nonfinite_rejected(dtype)
    assert not torch.cuda.is_initialized(), 'CPU checks initialized CUDA'
    print('PASS: inclusive timing boundaries, adjacent values, offsets, masks and finite inputs')


if __name__ == '__main__':
    main()
