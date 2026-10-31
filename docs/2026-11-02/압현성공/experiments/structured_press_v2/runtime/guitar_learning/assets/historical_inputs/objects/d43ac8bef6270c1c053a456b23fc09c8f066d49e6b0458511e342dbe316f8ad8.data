"""Pure target composition after source task postprocessing; no simulator."""
import torch


class PlayingTargetBridge:
    """One float32 target and final-target histories for the 81/66 layout.

    Source dictionaries contain names, lower/upper tensors, scale and alpha.
    Task-specific stage/synergy/grip transforms must run before this bridge;
    additional task envelopes must be checked before physical adoption.
    """

    def __init__(self, names, main_names, hold, native_lower, native_upper,
                 sources):
        self.names = tuple(names)
        self.main_names = tuple(main_names)
        if (len(self.names) != 81 or len(set(self.names)) != 81
                or len(self.main_names) != 66
                or len(set(self.main_names)) != 66
                or not set(self.main_names) <= set(self.names)):
            raise ValueError("expected unique native81/main66 names")
        self.hold = self._vector(hold, 81, "hold").clone()
        self.lower = self._vector(native_lower, 81, "native lower").clone()
        self.upper = self._vector(native_upper, 81, "native upper").clone()
        if bool((self.lower >= self.upper).any()):
            raise ValueError("native limits must increase")
        self.main = [self.names.index(n) for n in self.main_names]
        self.held = [j for j in range(81) if j not in self.main]
        if set(sources) != {"fret", "strike"}:
            raise ValueError("both source contracts are required")
        self.sources = {}
        used = set()
        alphas = set()
        for task, config in sources.items():
            local_names = tuple(config["names"])
            if (len(local_names) != 30 or len(set(local_names)) != 30
                    or not set(local_names) <= set(self.main_names)
                    or used & set(local_names)):
                raise ValueError("source30 ownership must be disjoint in main66")
            used.update(local_names)
            lo = self._vector(config["lower"], 30, "source lower").clone()
            hi = self._vector(config["upper"], 30, "source upper").clone()
            if bool((lo >= hi).any()):
                raise ValueError("source limits must increase")
            scale = float(config["scale"])
            alpha = float(config["alpha"])
            if not 0.0 < scale < float("inf") or not 0.0 <= alpha <= 1.0:
                raise ValueError("invalid source scale/alpha")
            alphas.add(alpha)
            mid = (lo + hi) * 0.5
            half = (hi - lo) * 0.5
            idx = [self.names.index(n) for n in local_names]
            self.lower[idx] = torch.maximum(
                self.lower[idx], torch.maximum(lo, mid - scale * half))
            self.upper[idx] = torch.minimum(
                self.upper[idx], torch.minimum(hi, mid + scale * half))
            self.sources[task] = dict(names=local_names, idx=idx,
                                      mid=mid, half=half, scale=scale)
        extras = set(self.main_names) - used
        expected = {side + "_Thorax_" + axis for side in ("L", "R")
                    for axis in "xyz"}
        if extras != expected or len(alphas) != 1:
            raise ValueError("expected Thorax6 and a common source EMA alpha")
        self.alpha = alphas.pop()
        if (bool((self.lower >= self.upper).any())
                or bool((self.hold < native_lower).any())
                or bool((self.hold > native_upper).any())):
            raise ValueError("empty intersection or invalid native hold")

    def _tensor(self, value, shape, label):
        if (not isinstance(value, torch.Tensor) or value.dtype != torch.float32
                or tuple(value.shape) != tuple(shape)
                or not bool(torch.isfinite(value).all())):
            raise ValueError(label + " must be a finite float32 tensor of " + str(shape))
        if hasattr(self, "hold") and value.device != self.hold.device:
            raise ValueError(label + " device mismatch")
        return value

    def _vector(self, value, size, label):
        return self._tensor(value, (size,), label)

    def source_history(self, targets):
        if not isinstance(targets, torch.Tensor) or targets.ndim != 2:
            raise ValueError("targets must have shape [N,81]")
        self._tensor(targets, (targets.shape[0], 81), "targets")
        return {task: (targets[:, c["idx"]] - c["mid"])
                / (c["scale"] * c["half"])
                for task, c in self.sources.items()}

    def compose(self, processed_actions, residual_rad, previous_targets,
                residual_limit_rad):
        """Return final targets, histories and the mask of final clipping.

        Previous targets must already be in the effective source/native range.
        Out-of-profile physical warm starts require a separate verified design.
        """
        histories = self.source_history(previous_targets)
        batch = previous_targets.shape[0]
        self._tensor(residual_rad, (batch, 66), "residual")
        cap = self._vector(residual_limit_rad, 66, "residual limit")
        if (bool((cap < 0).any()) or bool((residual_rad.abs() > cap).any())
                or set(processed_actions) != set(self.sources)
                or bool((previous_targets < self.lower).any())
                or bool((previous_targets > self.upper).any())
                or not torch.equal(previous_targets[:, self.held],
                                   self.hold[self.held].expand(batch, -1))):
            raise ValueError("invalid residual, history range, ownership or held targets")
        delta = torch.zeros_like(previous_targets)
        delta[:, self.main] = residual_rad
        candidate = self.hold.expand(batch, -1).clone()
        candidate[:, self.main] = (
            self.alpha * previous_targets[:, self.main]
            + (1 - self.alpha) * (candidate[:, self.main] + residual_rad))
        for task, c in self.sources.items():
            action = self._tensor(processed_actions[task], (batch, 30), task)
            if bool((action.abs() > 1).any()):
                raise ValueError("processed source actions must lie in [-1,1]")
            combined = action + delta[:, c["idx"]] / (c["scale"] * c["half"])
            ema = self.alpha * histories[task] + (1 - self.alpha) * combined
            candidate[:, c["idx"]] = c["mid"] + c["scale"] * ema * c["half"]
        final = torch.maximum(self.lower, torch.minimum(self.upper, candidate))
        return final, self.source_history(final), final != candidate
