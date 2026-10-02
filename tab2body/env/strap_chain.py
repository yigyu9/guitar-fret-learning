"""Cloth-style XPBD particle-chain guitar strap (1D cloth).

The strap is a chain of ``N`` particles.  The two ends are pinned to the guitar's strap
buttons (end pin, neck heel) and the interior particles are moved by gravity,
tension-only distance constraints, body capsule contact and Coulomb friction.  The
strap therefore wraps the torso and shoulder, slides on it, and carries the guitar's
weight to the shoulder.

Coupling (explicit, one control step of delay):
  ``post_simulate``  advance the strap from t-dt to t while the anchors and body capsules
                     are interpolated from their previous to their current poses, then
                     turn the strap tension into button and body forces.
  ``apply``          apply those forces to the guitar root (strap buttons) and to the human
                     body (contact points) during the next ``simulate``.

``StrapChain`` uses torch only, so it can be tested on CPU without Isaac Gym.
"""
from __future__ import annotations

import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass, fields

import torch


@dataclass(frozen=True)
class StrapChainParams:
    num_particles: int = 24
    mass: float = 0.12                 # total strap mass (kg)
    axial_stiffness: float = 2500.0    # EA (N). Effective stiffness including foam padding and soft tissue
    thickness: float = 0.003           # collision margin added to capsule radius (m)
    friction: float = 0.6              # strap-to-clothing Coulomb coefficient
    damping: float = 4.0               # particle velocity damping (1/s)
    substeps: int = 6
    iterations: int = 4
    rest_length_scale: float = 0.99    # rest length = settled length * scale (<1 is slightly snug)
    settle_steps: int = 60             # steps to cinch the strap onto the body (first reset)
    reset_settle_steps: int = 4        # steps to adapt the cached draped strap at later resets
    anchor_damping: float = 60.0       # strap damping, T += c * d(stretch)/dt (N*s/m)
    max_anchor_force: float = 300.0    # safety clip per button (N)
    gravity: tuple = (0.0, 0.0, -9.81)

    @classmethod
    def from_dict(cls, values):
        known = {f.name for f in fields(cls)}
        unknown = sorted(set(values) - known)
        if unknown:
            raise KeyError(f"unknown strap params: {unknown}")
        values = dict(values)
        if "gravity" in values:
            values["gravity"] = tuple(float(v) for v in values["gravity"])
        params = cls(**values)
        if params.num_particles < 3:
            raise ValueError("num_particles must be >= 3")
        if params.substeps < 1:
            raise ValueError("substeps must be >= 1")
        if params.iterations < 3:
            raise ValueError("iterations must be >= 3 (contact/length alternation)")
        if params.mass <= 0.0 or params.axial_stiffness <= 0.0:
            raise ValueError("mass and axial_stiffness must be positive")
        return params


def resample_polyline(points, count):
    """Resample a polyline ``[B,K,3]`` to ``count`` points at uniform arc length."""
    seg = points[:, 1:] - points[:, :-1]
    seg_len = seg.norm(dim=-1)
    cum = torch.cat([torch.zeros_like(seg_len[:, :1]), seg_len.cumsum(-1)], dim=-1)
    total = cum[:, -1:]
    target = torch.linspace(0.0, 1.0, count, device=points.device,
                            dtype=points.dtype)[None] * total
    idx = torch.searchsorted(cum.contiguous(), target.contiguous(), right=True) - 1
    idx = idx.clamp(0, seg.shape[1] - 1)
    start = torch.gather(cum, 1, idx)
    length = torch.gather(seg_len, 1, idx).clamp_min(1e-9)
    frac = ((target - start) / length).clamp(0.0, 1.0)[..., None]
    gather = idx[..., None].expand(-1, -1, 3)
    return torch.gather(points[:, :-1], 1, gather) + frac * torch.gather(seg, 1, gather)


def polyline_length(points):
    return (points[:, 1:] - points[:, :-1]).norm(dim=-1).sum(-1)


class StrapChain:
    """Batched XPBD strap. Particle 0 = end-pin anchor, particle N-1 = heel anchor.

    anchors:  ``[E,2,3]`` world positions of the two strap buttons.
    capsules: ``[E,C,2,3]`` world endpoints of the body collision capsules.

    Collision is segment-vs-capsule (not particle-vs-capsule): particle spacing (~5 cm) is
    larger than the shoulder radius, so particle-only contact lets segments cut through
    the shoulder and the strap loop slips off the body.
    """

    def __init__(self, num_envs, capsule_radii, params=None, device="cpu"):
        self.p = params or StrapChainParams()
        self.num_envs = int(num_envs)
        self.device = torch.device(device)
        n = self.p.num_particles
        self.radius = (torch.as_tensor(capsule_radii, dtype=torch.float32,
                                       device=self.device) + self.p.thickness)
        self.num_capsules = int(self.radius.numel())
        self.particle_mass = self.p.mass / n
        inv = torch.full((n,), 1.0 / self.particle_mass, device=self.device)
        inv[0] = inv[-1] = 0.0
        self.inv_mass = inv
        self.gravity = torch.tensor(self.p.gravity, dtype=torch.float32, device=self.device)
        seg = torch.arange(n - 1, device=self.device)
        self._parity = (seg[0::2], seg[1::2])

        e = self.num_envs
        self.x = torch.zeros(e, n, 3, device=self.device)
        self.v = torch.zeros_like(self.x)
        self.rest = torch.ones(e, device=self.device)   # per-segment rest length
        self.end_tension = torch.zeros(e, 2, device=self.device)  # undamped, for dT/dt
        self.anchor_force = torch.zeros(e, 2, 3, device=self.device)   # force ON the guitar
        self.body_force = torch.zeros(e, self.num_capsules, 3, device=self.device)  # ON the body
        self.body_point = torch.zeros_like(self.body_force)
        self.tension = torch.zeros(e, n - 1, device=self.device)
        self.contact = torch.zeros(e, n - 1, dtype=torch.bool, device=self.device)
        self.nonfinite = torch.zeros(e, dtype=torch.bool, device=self.device)

    # ------------------------------------------------------------------ public
    def initialize(self, env_ids, route, capsules, dt=1.0 / 60.0):
        """Place the strap along ``route [B,K,3]`` (first/last = anchors), cinch it onto the
        body with the anchors held (short, soft, frictionless rest length), then fix the rest
        length to the cinched length x ``rest_length_scale``.  The strap therefore starts
        snug on the torso/shoulder and the reset injects (almost) no tension."""
        env_ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.device).reshape(-1)
        if env_ids.numel() == 0:
            return
        n = self.p.num_particles
        x = resample_polyline(route.to(self.device, torch.float32), n)
        v = torch.zeros_like(x)
        cinch = polyline_length(x) / (n - 1) * 0.8
        anchors = torch.stack([route[:, 0], route[:, -1]], dim=1).to(x)
        caps = capsules.to(x)
        for _ in range(self.p.settle_steps):
            x, v, _ = self._advance(x, v, cinch, dt, anchors, anchors, caps, caps,
                                    stiffness=0.05 * self.p.axial_stiffness, friction=0.0)
        self._store_reset(env_ids, x, polyline_length(x) / (n - 1) * self.p.rest_length_scale)

    def warm_start(self, env_ids, x, rest, capsules, dt=1.0 / 60.0):
        """Reset from an already draped strap ``x [B,N,3]`` (ends = current anchors) with a
        known per-segment ``rest [B]``; only ``reset_settle_steps`` steps adapt it to the
        current body pose.  Much cheaper than ``initialize`` when many envs reset."""
        env_ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.device).reshape(-1)
        if env_ids.numel() == 0:
            return
        x = x.to(self.device, torch.float32)
        v = torch.zeros_like(x)
        anchors = torch.stack([x[:, 0], x[:, -1]], dim=1)
        caps = capsules.to(x)
        for _ in range(self.p.reset_settle_steps):
            x, v, _ = self._advance(x, v, rest, dt, anchors, anchors, caps, caps)
        self._store_reset(env_ids, x, rest)

    def _store_reset(self, env_ids, x, rest):
        self.x[env_ids] = x
        self.v[env_ids] = 0.0
        self.end_tension[env_ids] = 0.0
        self.rest[env_ids] = rest
        self.anchor_force[env_ids] = 0.0
        self.body_force[env_ids] = 0.0
        self.body_point[env_ids] = 0.0
        self.tension[env_ids] = 0.0
        self.contact[env_ids] = False
        self.nonfinite[env_ids] = False

    def step(self, dt, anchors_prev, anchors, capsules_prev, capsules):
        x, v, info = self._advance(self.x, self.v, self.rest, dt, anchors_prev, anchors,
                                   capsules_prev, capsules)
        # Tension = substep-averaged XPBD multiplier of the global chain solve (-lambda/h^2).
        # The solve converges every substep, so this is the physical tension.  It is not read
        # from the final stretch: the last non-penetration pass leaves an alternating
        # 20/90 N stretch artefact on segments wrapped around a capsule.
        tension = info["tension"]
        # Kelvin-Voigt damping, T += c * d(stretch)/dt, written per button as tau * dT/dt
        # with tau = c * L / EA (the strap's relaxation time).  It damps the guitar-on-strap
        # bounce that the explicit control-rate coupling would otherwise keep alive.  Rate of
        # *tension*, not of polyline length: a slack strap changes length while swinging
        # without stretching, and must stay force-free.
        end_tension = torch.stack([tension[:, 0], tension[:, -1]], dim=1)
        if self.p.anchor_damping > 0.0:
            total_rest = self.rest * (self.p.num_particles - 1)
            tau = (self.p.anchor_damping * total_rest / self.p.axial_stiffness)[:, None]
            rate = (end_tension - self.end_tension) / dt
            raw = end_tension
            end_tension = (end_tension + tau * rate * (end_tension > 0)).clamp_min(0.0)
            self.end_tension = raw
        end_tension = end_tension.clamp(max=self.p.max_anchor_force)
        direction = torch.stack([x[:, 1] - x[:, 0], x[:, -2] - x[:, -1]], dim=1)
        direction = direction / direction.norm(dim=-1, keepdim=True).clamp_min(1e-9)
        # force ON the guitar; the pinned end particles' weight hangs on the buttons directly
        force = end_tension[..., None] * direction + self.particle_mass * self.gravity
        # The body carries what the strap takes off the guitar plus the strap's own weight
        # (quasi-static balance, so the strap never creates momentum).  It is split over the
        # touching capsules in proportion to their contact impulse.
        share = info["body_force"].norm(dim=-1)
        share = share / share.sum(-1, keepdim=True).clamp_min(1e-12)
        total = self.p.mass * self.gravity - force.sum(1)
        touching = info["contact"].any(-1, keepdim=True)
        body_force = share[..., None] * (total * touching)[:, None]

        bad = ~(torch.isfinite(x).flatten(1).all(1) & torch.isfinite(v).flatten(1).all(1)
                & torch.isfinite(force).flatten(1).all(1)
                & torch.isfinite(body_force).flatten(1).all(1))
        self.nonfinite |= bad
        keep = (~bad)[:, None, None]
        self.x = torch.where(keep, x, self.x)
        self.end_tension = torch.where(keep[..., 0], self.end_tension,
                                       torch.zeros_like(self.end_tension))
        self.v = torch.where(keep, v, torch.zeros_like(self.v))
        self.anchor_force = torch.where(keep, force, torch.zeros_like(force))
        self.body_force = torch.where(keep, body_force, torch.zeros_like(body_force))
        self.body_point = torch.where(keep, info["body_point"], self.body_point)
        self.tension = torch.where(keep[..., 0], tension, torch.zeros_like(tension))
        self.contact = info["contact"] & keep[..., 0]
        return self.anchor_force

    def penetration(self, x, capsules):
        """Deepest segment-capsule penetration per env (m), for diagnostics."""
        p, q = x[:, :-1], x[:, 1:]
        _, _, _, pen = self._segment_contacts(p, q, capsules)
        return pen.flatten(1).max(1).values

    # ----------------------------------------------------------------- solver
    def _advance(self, x, v, rest, dt, a0, a1, c0, c1, stiffness=None, friction=None):
        p_ = self.p
        stiffness = p_.axial_stiffness if stiffness is None else stiffness
        mu = p_.friction if friction is None else friction
        s_count = p_.substeps
        h = dt / s_count
        inv_h2 = 1.0 / (h * h)
        inv = self.inv_mass
        interior = (inv > 0)[None, :, None]
        alpha_t = (rest / stiffness) * inv_h2                     # XPBD compliance / h^2, [B]
        m = self.particle_mass
        b, n = x.shape[0], x.shape[1]
        c = self.num_capsules
        dev = x.device
        tension = torch.zeros(b, n - 1, device=dev)
        body_imp = torch.zeros(b, c, 3, device=dev)
        body_pt = torch.zeros(b, c, 3, device=dev)
        body_w = torch.zeros(b, c, device=dev)
        contact = torch.zeros(b, n - 1, dtype=torch.bool, device=dev)
        decay = 1.0 / (1.0 + p_.damping * h)

        for s in range(s_count):
            f0, f1 = s / s_count, (s + 1) / s_count
            anchors = a0 + (a1 - a0) * f1
            cap_prev = c0 + (c1 - c0) * f0
            cap = c0 + (c1 - c0) * f1
            v = (v + self.gravity * h * interior) * decay
            x_old = x
            pos = x + v * h
            pos = torch.cat([anchors[:, :1], pos[:, 1:-1], anchors[:, 1:]], dim=1)
            lam = torch.zeros(b, n - 1, device=dev)
            depth = torch.zeros(b, n - 1, c, device=dev)          # accumulated push-out per contact
            moved = torch.zeros(b, c, 3, device=dev)              # sum m*dp the body gave the strap
            # contacts first, then the global length solve, so each iteration ends on a
            # converged chain and its multipliers are the physical tension
            for _ in range(p_.iterations):
                for seg in self._parity:
                    i, j = seg, seg + 1
                    u, _, normal, pen = self._segment_contacts(pos[:, i], pos[:, j], cap)
                    dpi, dpj = self._split(normal * pen[..., None], u, inv[i], inv[j])
                    depth[:, seg] += pen
                    moved += m * (dpi + dpj).sum(1)
                    pos = pos.index_add(1, i, dpi.sum(2))
                    pos = pos.index_add(1, j, dpj.sum(2))
                pos, lam = self._solve_distance(pos, rest, lam, alpha_t)

            # Coulomb friction once per substep: each segment against its deepest contact
            in_contact = depth.max(-1).values > 0
            if mu > 0.0:
                for seg in self._parity:
                    i, j = seg, seg + 1
                    seg_depth = depth[:, seg]                       # [B,S,C]
                    best = seg_depth.argmax(-1, keepdim=True)       # [B,S,1]
                    best_depth = seg_depth.gather(2, best)          # [B,S,1]
                    u, t, normal, _ = self._segment_contacts(pos[:, i], pos[:, j], cap)
                    u = u.gather(2, best)
                    t = t.gather(2, best)
                    normal = normal.gather(2, best[..., None].expand(-1, -1, 1, 3))
                    sel = best[..., None, None].expand(-1, -1, 1, 2, 3)
                    cap_now = cap[:, None].expand(-1, seg.numel(), -1, -1, -1).gather(2, sel)
                    cap_old = cap_prev[:, None].expand(-1, seg.numel(), -1, -1, -1).gather(2, sel)
                    surf_now = cap_now[..., 0, :] + t[..., None] * (cap_now[..., 1, :] - cap_now[..., 0, :])
                    surf_old = cap_old[..., 0, :] + t[..., None] * (cap_old[..., 1, :] - cap_old[..., 0, :])
                    disp_i = (pos[:, i] - x_old[:, i])[:, :, None]
                    disp_j = (pos[:, j] - x_old[:, j])[:, :, None]
                    rel = disp_i + u[..., None] * (disp_j - disp_i) - (surf_now - surf_old)
                    tangential = rel - (rel * normal).sum(-1, keepdim=True) * normal
                    t_len = tangential.norm(dim=-1).clamp_min(1e-12)
                    limit = (mu * best_depth / t_len).clamp(max=1.0)
                    dpi, dpj = self._split(-tangential * limit[..., None], u, inv[i], inv[j])
                    dsum = m * (dpi + dpj)                          # [B,S,1,3]
                    moved.scatter_add_(1, best.expand(-1, -1, 3), dsum[:, :, 0])
                    pos = pos.index_add(1, i, dpi[:, :, 0])
                    pos = pos.index_add(1, j, dpj[:, :, 0])
            pos, lam = self._solve_distance(pos, rest, lam, alpha_t)
            # final non-penetration pass.  It leaves ~2 mm of stretch on wrapped segments,
            # which is why tension is read from the multipliers, not from the stretch.
            for seg in self._parity:
                i, j = seg, seg + 1
                u, _, normal, pen = self._segment_contacts(pos[:, i], pos[:, j], cap)
                dpi, dpj = self._split(normal * pen[..., None], u, inv[i], inv[j])
                moved += m * (dpi + dpj).sum(1)
                pos = pos.index_add(1, i, dpi.sum(2))
                pos = pos.index_add(1, j, dpj.sum(2))

            v = (pos - x_old) / h
            x = pos

            tension += -lam * inv_h2
            # the body pushed the strap with m*dp/h^2, so the strap pushes the body back
            body_imp += -moved * inv_h2
            mid = 0.5 * (x[:, 1:] + x[:, :-1])                     # [B,N-1,3]
            body_pt += (depth[..., None] * mid[:, :, None]).sum(1)
            body_w += depth.sum(1)
            contact |= in_contact

        tension /= s_count
        body_force = body_imp / s_count
        body_point = body_pt / body_w[..., None].clamp_min(1e-12)
        body_point = torch.where(body_w[..., None] > 0, body_point,
                                 0.5 * (c1[:, :, 0] + c1[:, :, 1]))
        return x, v, {"tension": tension,
                      "body_force": body_force, "body_point": body_point,
                      "contact": contact}

    def _solve_distance(self, pos, rest, lam, alpha_t):
        """One global XPBD step for all distance constraints of the chain at once.

        Gauss-Seidel moves tension only a few segments per sweep, so a 24-particle chain never
        converges in a handful of iterations; the leftover gravity stretch then reads as tens
        of newtons of phantom tension.  The chain's constraint matrix J W J^T + alpha/h^2 is
        tridiagonal (S x S, S = N-1), so solve it exactly (batched dense solve; S ~ 23).
        Tension only: a segment takes part if it is stretched or already carries tension
        (C > 0 or lambda < 0); the others release their multiplier.  Deciding the active set
        up front is stable; a solve-then-drop second pass injected energy into a slack strap."""
        inv = self.inv_mass
        d = pos[:, 1:] - pos[:, :-1]                              # [B,S,3]
        length = d.norm(dim=-1).clamp_min(1e-9)
        nrm = d / length[..., None]
        constraint = length - rest[:, None]
        active = (constraint > 0) | (lam < 0)
        a = active.to(pos.dtype)
        rhs = torch.where(active, -constraint - alpha_t[:, None] * lam, -lam)
        diag = (inv[:-1] + inv[1:])[None] + alpha_t[:, None]     # [B,S]
        off = -inv[1:-1][None] * (nrm[:, :-1] * nrm[:, 1:]).sum(-1)   # [B,S-1]
        off = off * a[:, :-1] * a[:, 1:]
        mat = (torch.diag_embed(diag * a + (1 - a))
               + torch.diag_embed(off, 1) + torch.diag_embed(off, -1))
        dl = torch.linalg.solve(mat, rhs.unsqueeze(-1))[..., 0]
        new = (lam + dl).clamp(max=0.0)
        dl = new - lam
        step = dl[..., None] * nrm                                 # [B,S,3]
        delta = torch.zeros_like(pos)
        delta[:, :-1] -= inv[:-1, None] * step
        delta[:, 1:] += inv[1:, None] * step
        return pos + delta, new

    @staticmethod
    def _split(delta, u, wi, wj):
        """Distribute a correction of the point at parameter ``u`` on segment (i,j) to its
        endpoints by inverse mass (pinned ends take none).  delta [B,S,C,3], u [B,S,C]."""
        wi = wi[None, :, None]
        wj = wj[None, :, None]
        a, b = (1.0 - u) * wi, u * wj
        denom = ((1.0 - u) * a + u * b).clamp_min(1e-12)
        return (a / denom)[..., None] * delta, (b / denom)[..., None] * delta

    def _segment_contacts(self, p, q, cap):
        """Closest points between strap segments p->q [B,S,3] and capsule axes [B,C,2,3].

        Returns u (param on the strap segment), t (param on the capsule axis), outward
        normal and penetration depth, each per (segment, capsule): [B,S,C(,3)]."""
        d1 = (q - p)[:, :, None]                                  # [B,S,1,3]
        a = cap[:, None, :, 0]                                    # [B,1,C,3]
        d2 = cap[:, None, :, 1] - a
        r = p[:, :, None] - a                                     # [B,S,C,3]
        aa = (d1 * d1).sum(-1).clamp_min(1e-12)
        ee = (d2 * d2).sum(-1).clamp_min(1e-12)
        bb = (d1 * d2).sum(-1)
        cc = (d1 * r).sum(-1)
        ff = (d2 * r).sum(-1)
        denom = aa * ee - bb * bb
        u = torch.where(denom > 1e-12, ((bb * ff - cc * ee) / denom.clamp_min(1e-12)),
                        torch.zeros_like(denom)).clamp(0.0, 1.0)
        t = (bb * u + ff) / ee
        u = torch.where(t < 0, (-cc / aa).clamp(0.0, 1.0),
                        torch.where(t > 1, ((bb - cc) / aa).clamp(0.0, 1.0), u))
        t = t.clamp(0.0, 1.0)
        diff = (r + u[..., None] * d1) - t[..., None] * d2
        dist = diff.norm(dim=-1)
        fallback = torch.tensor([0.0, 0.0, 1.0], device=p.device)
        normal = torch.where(dist[..., None] > 1e-9,
                             diff / dist[..., None].clamp_min(1e-9), fallback)
        pen = (self.radius - dist).clamp_min(0.0)
        return u, t, normal, pen


# ======================================================================= Isaac adapter
def load_strap_config(path):
    with open(path) as handle:
        cfg = json.load(handle)
    for key in ("guitar_anchors", "route", "colliders"):
        if key not in cfg:
            raise KeyError(f"strap config missing '{key}'")
    return cfg


def mjcf_capsules(xml_path, body_names):
    """First capsule geom (fromto, radius) of each named MJCF body, in body-local frame."""
    root = ET.parse(xml_path).getroot()
    result = {}
    for name in body_names:
        body = root.find(f".//body[@name='{name}']")
        if body is None:
            raise KeyError(f"body '{name}' not in {xml_path}")
        geom = next((g for g in body.findall("geom") if g.get("type") == "capsule"), None)
        if geom is None or geom.get("fromto") is None:
            raise ValueError(f"body '{name}' has no fromto capsule geom")
        values = [float(v) for v in geom.get("fromto").split()]
        result[name] = (values[:3], values[3:], float(geom.get("size").split()[0]))
    return result


def resolve_colliders(cfg, xml_path):
    """Collider entries -> [(body, from_local, to_local, radius)].

    An entry is either a body name (its MJCF capsule is used) or an explicit
    ``{"body", "from", "to", "radius"}`` capsule, e.g. for the box-shaped pelvis."""
    named = [c for c in cfg["colliders"] if isinstance(c, str)]
    caps = mjcf_capsules(xml_path, named) if named else {}
    result = []
    for entry in cfg["colliders"]:
        if isinstance(entry, str):
            result.append((entry, *caps[entry]))
        else:
            result.append((entry["body"], list(entry["from"]), list(entry["to"]),
                           float(entry["radius"])))
    return result


def _quat_conjugate(q):
    return torch.cat([-q[..., :3], q[..., 3:4]], dim=-1)


def _quat_rotate(q, v):
    """Rotate ``v [...,3]`` by quaternion ``q [...,4]`` (xyzw), broadcasting."""
    qv, v = torch.broadcast_tensors(q[..., :3], v)
    qw = q[..., 3:4]
    t = 2.0 * torch.cross(qv, v, dim=-1)
    return v + qw * t + torch.cross(qv, t, dim=-1)


class StrapChainCoupler:
    """Connects ``StrapChain`` to ``GuitarEnvBase`` tensors and the Isaac force API."""

    def __init__(self, env, config_path, xml_path):
        cfg = load_strap_config(config_path)
        self.env = env
        self.config_path = os.path.abspath(config_path)
        self.params = StrapChainParams.from_dict(cfg.get("params", {}))
        d = env.device
        self.dt = 1.0 / env.SIM_HZ
        self.guitar_body = env.n_hbody + env.gbody_index[cfg.get("guitar_body", "guitar")]
        anchors = cfg["guitar_anchors"]
        self.anchor_local = torch.tensor([anchors["end_pin"], anchors["heel"]],
                                         dtype=torch.float32, device=d)
        colliders = resolve_colliders(cfg, xml_path)
        self.capsule_body = torch.tensor([env.hbody_index[c[0]] for c in colliders],
                                         dtype=torch.long, device=d)
        self.capsule_local = torch.tensor([[c[1], c[2]] for c in colliders],
                                          dtype=torch.float32, device=d)
        radii = [c[3] for c in colliders]
        self.route_body = torch.tensor([env.hbody_index[p["body"]] for p in cfg["route"]],
                                       dtype=torch.long, device=d)
        self.route_local = torch.tensor([p["local"] for p in cfg["route"]],
                                        dtype=torch.float32, device=d)
        self.chain = StrapChain(env.num_envs, radii, self.params, device=d)
        n_total = env.body_state.shape[0]
        self.force = torch.zeros(n_total, 3, device=d)
        self.torque = torch.zeros(n_total, 3, device=d)
        # forces are applied at the centre of mass, so torques need each body's COM offset
        com = []
        for actor, index in [(env.h_actors[0], int(i)) for i in self.capsule_body.tolist()] + \
                [(env.g_actors[0], self.guitar_body - env.n_hbody)]:
            props = env.gym.get_actor_rigid_body_properties(env.envs[0], actor)
            com.append([props[index].com.x, props[index].com.y, props[index].com.z])
        com = torch.tensor(com, dtype=torch.float32, device=d)
        self.capsule_com_local, self.guitar_com_local = com[:-1], com[-1]
        self.pending = torch.ones(env.num_envs, dtype=torch.bool, device=d)
        self._anchors_prev = None
        self._caps_prev = None
        # draped strap cached in the Chest frame after the first full cinch; later resets
        # start from it (see StrapChain.warm_start)
        self.template_body = env.hbody_index[cfg.get("template_body", "Chest")]
        self._template = None

    # world-space geometry from the rigid-body state tensor (env space, same as the force API)
    def _bodies(self):
        return self.env.body_state.view(self.env.num_envs, self.env._bpe, 13)

    def anchors_world(self):
        g = self._bodies()[:, self.guitar_body]
        return g[:, None, :3] + _quat_rotate(g[:, None, 3:7], self.anchor_local[None])

    def capsules_world(self):
        b = self._bodies()[:, self.capsule_body]                  # [E,C,13]
        pos, quat = b[:, :, None, :3], b[:, :, None, 3:7]
        return pos + _quat_rotate(quat, self.capsule_local[None].expand(b.shape[0], -1, -1, -1))

    def route_world(self, env_ids):
        b = self._bodies()[env_ids][:, self.route_body]           # [B,K,13]
        guide = b[:, :, :3] + _quat_rotate(b[:, :, 3:7], self.route_local[None])
        anchors = self.anchors_world()[env_ids]
        return torch.cat([anchors[:, :1], guide, anchors[:, 1:]], dim=1)

    def reset(self, env_ids):
        """Body transforms are stale until the next simulate, so the strap is re-draped in the
        first ``post_simulate`` after the reset; it applies no force for that one step."""
        env_ids = torch.as_tensor(env_ids, dtype=torch.long, device=self.env.device)
        self.pending[env_ids] = True
        self.chain.anchor_force[env_ids] = 0.0
        self.chain.body_force[env_ids] = 0.0
        self._write_forces()

    def apply(self):
        from isaacgym import gymapi, gymtorch
        self.env.gym.apply_rigid_body_force_tensors(
            self.env.sim, gymtorch.unwrap_tensor(self.force),
            gymtorch.unwrap_tensor(self.torque), gymapi.ENV_SPACE)

    def post_simulate(self):
        self.env.gym.refresh_rigid_body_state_tensor(self.env.sim)
        anchors = self.anchors_world()
        caps = self.capsules_world()
        if self._anchors_prev is not None:
            self.chain.step(self.dt, self._anchors_prev, anchors, self._caps_prev, caps)
        ids = torch.nonzero(self.pending | self.chain.nonfinite).flatten()
        if ids.numel():
            frame = self._bodies()[ids, self.template_body]
            if self._template is None:
                self.chain.initialize(ids, self.route_world(ids), caps[ids], self.dt)
                local = _quat_rotate(_quat_conjugate(frame[:, None, 3:7]),
                                     self.chain.x[ids] - frame[:, None, :3])
                self._template = (local[0].clone(), self.chain.rest[ids[0]].clone())
            else:
                local, rest = self._template
                x = frame[:, None, :3] + _quat_rotate(frame[:, None, 3:7], local[None])
                x[:, 0] = anchors[ids, 0]
                x[:, -1] = anchors[ids, 1]
                self.chain.warm_start(ids, x, rest.expand(ids.numel()), caps[ids], self.dt)
            self.pending[ids] = False
        self._anchors_prev, self._caps_prev = anchors, caps
        self._write_forces(anchors)

    def _write_forces(self, anchors=None):
        """Strap forces -> per-body force at COM + torque about COM (env space)."""
        e, bpe = self.env.num_envs, self.env._bpe
        force = self.force.view(e, bpe, 3)
        torque = self.torque.view(e, bpe, 3)
        force.zero_()
        torque.zero_()
        if anchors is None:
            anchors = self.anchors_world()
        bodies = self._bodies()
        g = bodies[:, self.guitar_body]
        g_com = g[:, :3] + _quat_rotate(g[:, 3:7], self.guitar_com_local[None])
        f_anchor = self.chain.anchor_force                       # [E,2,3]
        force[:, self.guitar_body] = f_anchor.sum(1)
        torque[:, self.guitar_body] = torch.cross(
            anchors - g_com[:, None], f_anchor, dim=-1).sum(1)
        b = bodies[:, self.capsule_body]
        b_com = b[..., :3] + _quat_rotate(b[..., 3:7], self.capsule_com_local[None])
        f_body = self.chain.body_force                           # [E,C,3]
        t_body = torch.cross(self.chain.body_point - b_com, f_body, dim=-1)
        for k in range(self.capsule_body.numel()):               # several capsules may share a body
            index = int(self.capsule_body[k])
            force[:, index] += f_body[:, k]
            torque[:, index] += t_body[:, k]
        off = (self.chain.nonfinite | self.pending)[:, None, None]
        force.masked_fill_(off, 0.0)
        torque.masked_fill_(off, 0.0)

    def tension_summary(self):
        t = self.chain.tension
        return {"max_tension": t.max(dim=1).values,
                "end_pin_force": self.chain.anchor_force[:, 0].norm(dim=-1),
                "heel_force": self.chain.anchor_force[:, 1].norm(dim=-1),
                "contact_fraction": self.chain.contact.float().mean(dim=1)}
