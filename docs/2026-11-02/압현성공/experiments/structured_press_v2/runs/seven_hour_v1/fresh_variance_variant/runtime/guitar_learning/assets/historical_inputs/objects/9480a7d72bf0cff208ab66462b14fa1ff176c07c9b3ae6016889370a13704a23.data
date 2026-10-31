"""The runtime property guard must reject before reaching a native backend."""
from types import SimpleNamespace
import pytest
from .construction_property_guard_v1 import ConstructionPropertyGuard

@pytest.mark.parametrize('initialized,allowed',[(False,False),(True,False),(True,True)])
def test_no_native_property_call_outside_construction(initialized,allowed):
    calls=[];native=SimpleNamespace(set_actor_rigid_body_properties=lambda *a,**k:calls.append(a));owner=SimpleNamespace(initialization_complete=initialized,property_submission_allowed=allowed,property_setter_rejections=0,property_setter_calls=0,forbidden_calls=[]);guard=ConstructionPropertyGuard(native,owner)
    with pytest.raises(RuntimeError):guard.set_actor_rigid_body_properties('dummy')
    assert not calls and owner.property_setter_rejections==1 and owner.property_setter_calls==0 and owner.forbidden_calls==['set_actor_rigid_body_properties']

def test_one_explicit_construction_window_is_forwarded():
    calls=[];native=SimpleNamespace(set_actor_rigid_body_properties=lambda *a,**k:calls.append(a));owner=SimpleNamespace(initialization_complete=False,property_submission_allowed=True,property_setter_rejections=0,property_setter_calls=0,forbidden_calls=[]);guard=ConstructionPropertyGuard(native,owner);guard.set_actor_rigid_body_properties('dummy')
    assert calls==[('dummy',)] and owner.property_setter_calls==1 and owner.property_setter_rejections==0 and not owner.forbidden_calls
