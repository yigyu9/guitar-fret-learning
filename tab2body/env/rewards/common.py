"""보상 함수에서 공통으로 사용하는 작은 수치 유틸리티."""
from __future__ import annotations


def smoothstep01(value):
    value = value.clamp(0.0, 1.0)
    return value * value * (3.0 - 2.0 * value)
