"""학습 구성요소의 지연 로딩 공개 인터페이스."""
from importlib import import_module


_EXPORTS = {
    "ActorCritic": (".models", "ActorCritic"),
    "configure_finger_flexion_policy": (
        ".models", "configure_finger_flexion_policy"),
    "PPOConfig": (".ppo", "PPOConfig"),
    "PPOTrainer": (".ppo", "PPOTrainer"),
    "FingertipApproachCurriculum": (
        ".curriculum", "FingertipApproachCurriculum"),
    "FingertipApproachCurriculumConfig": (
        ".curriculum", "FingertipApproachCurriculumConfig"),
    "StrikeCurriculum": (".strike_curriculum", "StrikeCurriculum"),
    "StrikeCurriculumConfig": (
        ".strike_curriculum", "StrikeCurriculumConfig"),
    "strike_evaluation_gate_summary": (
        ".strike_evaluation", "strike_evaluation_gate_summary"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module_name, member_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), member_name)
    globals()[name] = value
    return value
