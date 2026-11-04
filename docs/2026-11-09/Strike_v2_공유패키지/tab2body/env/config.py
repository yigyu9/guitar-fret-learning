"""생성자와 설정 딕셔너리를 안전하게 연결한다."""
from __future__ import annotations

from inspect import Parameter, signature


def configured_kwargs(component_type, config, /, **overrides):
    """생성자와 이름이 같은 설정만 선택하고 명시적 값을 덮어쓴다."""
    parameters = signature(component_type).parameters
    unknown = sorted(set(overrides) - set(parameters))
    if unknown:
        raise TypeError(f"unknown constructor arguments: {unknown}")

    kwargs = {name: config[name] for name in parameters if name in config}
    kwargs.update(overrides)
    missing = [
        name for name, parameter in parameters.items()
        if parameter.default is Parameter.empty
        and parameter.kind not in (Parameter.VAR_POSITIONAL,
                                   Parameter.VAR_KEYWORD)
        and name not in kwargs
    ]
    if missing:
        raise KeyError(f"missing required configuration: {missing}")
    return kwargs
