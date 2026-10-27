# Guitar-neck contact-surface calibration

## Goal

Derive physically valid contact regions centred on acquisition grip G from the
environment's authored-vertex convex neck proxy and humanoid hand geometry.
Replace corner-biased point guides and reject failed-teacher pad coordinates as
the target basis.

## Method

- Reconstruct the environment collision proxy as the convex hull of vertices in
  `guitar_neck1.obj` / `guitar_neck2.obj`.
- Use the implemented 2/3-neck acquisition station as the axial origin.
- Classify faces using their local outward normals and the authored initial
  guitar quaternion: front=`+local z`, back=`-local z`, floor-facing side=the
  face whose world normal has the most negative vertical component.
- Map the actual humanoid `LH:index1..pinky1` base spacing onto guitar-local
  `y`, centred on acquisition G.
- Put thumb and finger target centres at lateral `x=0`; represent targets as
  surface patches rather than fixed bevel-adjacent points.
- Defer final distal collider-pad calibration until acquisition-centred IK is
  available; do not reuse failed-teacher calibration as target truth.
- Save a machine-readable contract and a cross-section visualization under
  `grip/contact_surface_calibration/`.

## Checklist

- [x] Verify guitar-local axis meaning in the initial world pose.
- [x] Identify front, back, and floor-facing convex-hull faces.
- [x] Audit whether the current targets lie on the collision proxy.
- [x] Derive acquisition-centred contact-region centres and normals.
- [x] Render the acquisition cross-section, axial layout, and initial scene.
- [x] Document implementation recommendations and complete review.

## Acceptance

- Every proposed center has negligible residual to its assigned proxy face
  plane and is not outside the convex proxy within numerical tolerance.
- Finger targets are inset from convex edges rather than placed at impossible
  `x=max, z=max` corners.
- Desired hand-pad normals oppose their guitar-surface normals; actual distal
  collider points are explicitly left for post-IK calibration.
- The report distinguishes geometry calibration from unverified controller
  reachability; no training change is implied by this analysis alone.
- Exact PhysX cooked vertices are not claimed; runtime contact still requires a
  collider-contact rollout.
