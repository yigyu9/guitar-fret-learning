"""왼손·오른손 보상 구현의 지연 로딩 공개 인터페이스."""
from importlib import import_module


_EXPORTS = {
    "FretReward": (".fret", "FretReward"),
    "PickGripReference": (".strike", "PickGripReference"),
    "StrikeReward": (".strike", "StrikeReward"),
}

__all__ = ["FretReward", "PickGripReference", "StrikeReward"]


def __getattr__(name):
    try:
        module_name, member_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(name) from exc
    value = getattr(import_module(module_name, __name__), member_name)
    globals()[name] = value
    return value
