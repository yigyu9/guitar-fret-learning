"""XPBD 입자 체인 스트랩의 CPU 회귀 검사 (Isaac Gym 불필요)."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
import sys

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from env.strap_chain import (StrapChain, StrapChainCoupler, StrapChainParams,  # noqa: E402
                             polyline_length, resample_polyline)
from tools.strap_chain_preview import (ASSETS, hang_guitar,  # noqa: E402
                                       seated_body_frames, seated_strap_geometry)

FAST = dict(settle_steps=40)


def check_resample():
    line = torch.tensor([[[0.0, 0, 0], [1.0, 0, 0], [1.0, 1.0, 0]]])
    pts = resample_polyline(line, 5)
    assert torch.allclose(polyline_length(pts), torch.tensor([2.0]), atol=1e-5)
    assert torch.allclose(pts[0, 2], torch.tensor([1.0, 0.0, 0.0]), atol=1e-5)


def check_segment_cannot_tunnel():
    """Both particles outside a thin capsule while the segment between them cuts through
    it: particle-only contact misses this, segment contact must push the strap off."""
    params = StrapChainParams(num_particles=3, settle_steps=0, substeps=4, iterations=8)
    chain = StrapChain(1, [0.03], params)
    cap = torch.tensor([[[[0.0, -0.2, 0.0], [0.0, 0.2, 0.0]]]])     # axis along y
    route = torch.tensor([[[-0.1, 0.0, -0.01], [0.1, 0.0, 0.04], [0.3, 0.0, -0.01]]])
    radius = 0.03 + params.thickness
    assert (route[0, :, [0, 2]].norm(dim=-1) > radius).all()        # particles all outside
    assert float(chain.penetration(route, cap)) > 0.01              # ...the segment is not
    chain.initialize([0], route, cap)
    anchors = torch.stack([route[:, 0], route[:, -1]], 1)
    for _ in range(10):
        chain.step(1 / 60, anchors, anchors, cap, cap)
    assert float(chain.penetration(chain.x, cap)) < 2e-3
    assert chain.x[0, 1, 2] > 0.04                                   # lifted over the capsule


def check_slack_strap_only_hangs():
    params = StrapChainParams(num_particles=8, settle_steps=0)
    chain = StrapChain(1, [0.01], params)
    far = torch.tensor([[[[5.0, 5.0, 5.0], [5.0, 5.1, 5.0]]]])
    route = torch.tensor([[[0.0, 0.0, 0.0], [0.5, 0.0, 0.0]]])
    chain.initialize([0], route, far)
    near = torch.tensor([[[0.0, 0.0, 0.0], [0.3, 0.0, 0.0]]])        # ends move closer
    for _ in range(120):
        chain.step(1 / 60, near, near, far, far)
    # a slack strap hangs: the buttons only carry its own weight, it never pushes them apart
    total = chain.anchor_force[0].sum(0)
    weight = params.mass * 9.81
    assert abs(float(total[2]) + weight) < 0.2 * weight, total
    assert float(chain.anchor_force[0, 0, 0]) >= 0.0 and float(chain.anchor_force[0, 1, 0]) <= 0.0


def check_seated_route_wraps_under_right_arm():
    """end pin -> under the right armpit -> across the back -> over the left shoulder."""
    _, params, radii, caps, route, _ = seated_strap_geometry()
    chain = StrapChain(1, radii, replace(params, **FAST))
    chain.initialize([0], route, caps)
    x = chain.x[0]
    assert int((x[:, 1] < -0.24).sum()) >= 3, "strap must cross the back"
    top = int(x[:, 2].argmax())
    assert x[top, 0] < -0.03, "highest point must be on the left shoulder (+x right)"
    assert float(chain.penetration(chain.x, caps)) < 2e-3


def check_hanging_guitar_balance():
    hist = hang_guitar(2.0, 4.5, vertical_only=True)
    tail = slice(-30, None)
    weight = 4.5 * 9.81
    lift = float(np.mean(hist["lift"][tail]))
    body = float(np.mean(hist["body_down"][tail]))
    assert abs(lift - weight) < 0.03 * weight, (lift, weight)
    assert abs(body - (weight + 0.12 * 9.81)) < 0.05 * weight, body   # Newton 3: + strap weight
    assert hist["z0"] - hist["z"][-1] < 0.02, "strap should hold the guitar within 2 cm"
    assert np.ptp(hist["z"][tail]) < 1e-3, "no residual bounce"
    assert max(hist["pen"][tail]) < 2e-3
    assert not hist["nonfinite"]


def check_nonfinite_is_contained():
    _, params, radii, caps, route, _ = seated_strap_geometry()
    chain = StrapChain(2, radii, replace(params, **FAST))
    chain.initialize([0, 1], route.expand(2, -1, -1), caps.expand(2, -1, -1, -1))
    anchors = torch.stack([route[:, 0], route[:, -1]], 1).expand(2, -1, -1).clone()
    bad = anchors.clone()
    bad[1, 0, 0] = float("nan")
    caps2 = caps.expand(2, -1, -1, -1)
    chain.step(1 / 60, anchors, bad, caps2, caps2)
    assert chain.nonfinite.tolist() == [False, True]
    assert torch.isfinite(chain.x).all() and chain.anchor_force[1].abs().sum() == 0


def _matrix_to_quat_xyzw(m):
    """Shepperd: pick the largest of w,x,y,z first (the seated root is a 180 deg yaw, w=0)."""
    trace = np.trace(m)
    k = int(np.argmax([trace, m[0, 0], m[1, 1], m[2, 2]]))
    if k == 0:
        w = np.sqrt(1 + trace) / 2
        q = [(m[2, 1] - m[1, 2]) / (4 * w), (m[0, 2] - m[2, 0]) / (4 * w),
             (m[1, 0] - m[0, 1]) / (4 * w), w]
    else:
        i, j, l = k - 1, k % 3, (k + 1) % 3
        r = np.sqrt(1 + m[i, i] - m[j, j] - m[l, l]) / 2
        q = [0.0, 0.0, 0.0, (m[l, j] - m[j, l]) / (4 * r)]
        q[i], q[j], q[l] = r, (m[j, i] + m[i, j]) / (4 * r), (m[l, i] + m[i, l]) / (4 * r)
    return q


def _fake_env(num_envs=2):
    """Just enough of GuitarEnvBase for the coupler: seated FK body states, zero COM."""
    frames, (gpos, grot) = seated_body_frames()
    names = list(frames)
    states = [list(frames[n][0]) + _matrix_to_quat_xyzw(frames[n][1]) + [0] * 6 for n in names]
    states.append(list(gpos) + _matrix_to_quat_xyzw(grot) + [0] * 6)      # guitar root
    states.append([0, 0, 0.2, 0, 0, 0, 1] + [0] * 6)                       # chair
    bpe = len(states)
    body_state = torch.tensor(states, dtype=torch.float32).repeat(num_envs, 1)
    zero_com = SimpleNamespace(com=SimpleNamespace(x=0.0, y=0.0, z=0.0))
    gym = SimpleNamespace(
        get_actor_rigid_body_properties=lambda env, actor: [zero_com] * bpe,
        refresh_rigid_body_state_tensor=lambda sim: None)
    return SimpleNamespace(
        num_envs=num_envs, device="cpu", SIM_HZ=60, gym=gym, sim=None, envs=[None],
        h_actors=[0], g_actors=[1], body_state=body_state, _bpe=bpe,
        n_hbody=len(names), hbody_index={n: i for i, n in enumerate(names)},
        gbody_index={"guitar": 0})


def check_coupler_geometry_and_forces():
    env = _fake_env()
    coupler = StrapChainCoupler(env, ASSETS / "strap_chain.json",
                                ASSETS / "smpl_mpl_hands_body.xml")
    _, _, _, caps, route, _ = seated_strap_geometry()
    anchors = coupler.anchors_world()
    assert torch.allclose(anchors[0], torch.stack([route[0, 0], route[0, -1]]), atol=1e-4)
    assert torch.allclose(coupler.capsules_world()[0], caps[0], atol=1e-4)
    assert torch.allclose(coupler.route_world(torch.tensor([1]))[0], route[0], atol=1e-4)

    coupler.post_simulate()                                  # first: full cinch, no force yet
    assert coupler._template is not None and not coupler.pending.any()
    first = coupler.chain.x.clone()
    for _ in range(5):
        coupler.post_simulate()
    e, bpe = env.num_envs, env._bpe
    force = coupler.force.view(e, bpe, 3)
    g = coupler.guitar_body
    assert torch.allclose(force[:, g], coupler.chain.anchor_force.sum(1), atol=1e-5)
    assert force[:, g, 2].min() > 0, "a snug strap lifts the guitar"
    human = force[:, :env.n_hbody].sum(1)
    expected = coupler.params.mass * coupler.chain.gravity - force[:, g]
    assert torch.allclose(human, expected, atol=1e-3), "strap must not create momentum"

    coupler.reset(torch.tensor([1]))                         # later resets reuse the template
    assert coupler.force.view(e, bpe, 3)[1].abs().sum() == 0
    coupler.post_simulate()
    assert (coupler.chain.x[1] - first[1]).norm(dim=-1).max() < 0.03


def main():
    check_resample()
    check_segment_cannot_tunnel()
    check_slack_strap_only_hangs()
    check_seated_route_wraps_under_right_arm()
    check_hanging_guitar_balance()
    check_nonfinite_is_contained()
    check_coupler_geometry_and_forces()
    print("PASS: XPBD strap chain (contact, tension-only, seated wrap, hang balance, "
          "nonfinite isolation, Isaac coupler geometry/forces)")


if __name__ == "__main__":
    main()
