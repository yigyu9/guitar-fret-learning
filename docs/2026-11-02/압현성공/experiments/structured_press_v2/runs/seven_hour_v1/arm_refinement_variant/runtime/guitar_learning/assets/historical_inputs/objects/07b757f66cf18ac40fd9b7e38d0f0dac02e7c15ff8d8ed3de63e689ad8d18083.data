import numpy as np
import pytest

from stability_adapter_2.joint_hold_residual import JointHoldResidual


def test_persistent_error_cannot_wind_up_at_delta_cap():
    controller = JointHoldResidual(np.zeros(24),np.full(24,-.3),np.full(24,.3))
    for _ in range(120):
        target,record = controller.update(np.full(24,-1.),1/60)
        assert np.abs(target).max()<=.15+1e-12
    assert np.array_equal(controller.integral,np.zeros(24))
    assert all(record['integral_blocked'])


def test_final_limit_blocks_integration_but_allows_reversal():
    controller = JointHoldResidual(np.full(24,.3),np.full(24,-.3),np.full(24,.3))
    for _ in range(120):
        target,_ = controller.update(np.full(24,.29),1/60)
    assert np.array_equal(target,np.full(24,.3))
    assert np.array_equal(controller.integral,np.zeros(24))
    target,record = controller.update(np.full(24,.31),1/60)
    assert (target<.3).all() and (controller.integral<0).all()
    assert not any(record['integral_blocked'])


def test_variable_error_remains_inside_both_asymmetric_limits():
    reference = np.linspace(-.2,.2,24)
    controller = JointHoldResidual(reference,reference-.04,reference+.07)
    rng = np.random.RandomState(0)
    for _ in range(240):
        target,_ = controller.update(reference+rng.normal(0,.1,24),1/60)
        assert np.isfinite(target).all()
        assert (target>=reference-.04-1e-12).all() and (target<=reference+.07+1e-12).all()
        assert (np.abs(target-reference)<=.15+1e-12).all()


def test_invalid_observation_does_not_poison_integral():
    controller = JointHoldResidual(np.zeros(24),np.full(24,-.3),np.full(24,.3))
    controller.update(np.full(24,.01),1/60)
    before = controller.integral.copy()
    for actual,dt in ((np.full(24,np.nan),1/60),(np.zeros(23),1/60),(np.zeros(24),0)):
        with pytest.raises(ValueError):
            controller.update(actual,dt)
        assert np.array_equal(controller.integral,before)
