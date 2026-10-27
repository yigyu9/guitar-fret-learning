"""Feasible source convex/quad interval; solver flag is not an optimum claim."""
from .environment import np
from scipy.spatial import ConvexHull
from scipy.optimize import minimize, LinearConstraint

def certified_distance(mesh, polygon):
    # Centered millimetres resolve the sub-micrometre gate without changing source meshes.
    center = (mesh.vertices.mean(axis=0) + polygon.mean(axis=0)) / 2
    vertices = (mesh.vertices - center) * 1000
    patch = (polygon - center) * 1000
    planes = ConvexHull(vertices).equations
    _, unique = np.unique(np.round(planes, 10), axis=0, return_index=True)
    planes = planes[unique]
    matrix = np.column_stack((planes[:, :3], np.zeros((len(planes), 4))))
    sum_row = np.r_[np.zeros(3), np.ones(4)][None, :]
    def objective(x):
        delta = x[:3] - x[3:] @ patch
        return float(delta @ delta), np.r_[2 * delta, -2 * patch @ delta]
    result = minimize(objective, np.r_[vertices.mean(axis=0), np.full(4, .25)], jac=True,
        method='SLSQP', bounds=[(None, None)] * 3 + [(0, 1)] * 4,
        constraints=[LinearConstraint(matrix, -np.inf, -planes[:, 3]), LinearConstraint(sum_row, 1, 1)],
        options={'ftol': 1e-13, 'maxiter': 1000})
    x = result.x
    if not np.isfinite(x).all() or np.any(x[3:] < 0) or x[3:].sum() <= 0:
        raise RuntimeError('invalid source patch witness')
    raw_violation = float(np.maximum(matrix @ x + planes[:, 3], 0).max())
    raw_weight_sum_error = float(abs(x[3:].sum() - 1))
    # A primal/dual interval needs feasible witnesses, not a solver success flag.
    # Move any boundary violation toward an interior convex vertex mean.
    interior = vertices.mean(axis=0)
    initial_witness = x[:3].copy()
    at_point = planes[:, :3] @ x[:3] + planes[:, 3]
    at_interior = planes[:, :3] @ interior + planes[:, 3]
    active = at_point > -1e-8
    if active.any():
        fraction = float(np.min((-1e-8 - at_interior[active]) / (at_point[active] - at_interior[active])))
        x[:3] = interior + min(1., fraction) * (x[:3] - interior)
    x[3:] /= x[3:].sum()
    violation = float(np.maximum(matrix @ x + planes[:, 3], 0).max())
    weight_sum_error = float(abs(x[3:].sum() - 1))
    if violation > 1e-10 or weight_sum_error > 1e-10:
        raise RuntimeError('source distance witness feasibility failed')
    delta = x[:3] - x[3:] @ patch
    upper_mm = float(np.linalg.norm(delta))
    direction = delta / upper_mm if upper_mm else np.zeros(3)
    lower_mm = max(0., float((vertices @ direction).min() - (patch @ direction).max()))
    return {'distance_m': upper_mm / 1000, 'distance_lower_bound_m': lower_mm / 1000,
        'primal_dual_gap_m': (upper_mm - lower_mm) / 1000, 'feasibility_error_mm': violation,
        'optimizer_success': bool(result.success), 'optimizer_message': result.message,
        'unadjusted_plane_feasibility_error_mm': raw_violation,
        'unadjusted_weight_sum_error': raw_weight_sum_error, 'weight_sum_error': weight_sum_error,
        'feasible_witness_adjustment_mm': float(np.linalg.norm(x[:3] - initial_witness)),
        'palm_witness_world_m': (x[:3] / 1000 + center).tolist(),
        'target_witness_world_m': ((x[3:] @ patch) / 1000 + center).tolist(),
        'scope': 'source convex distance witness upper bound and support-plane lower bound; not cooked geometry'}
