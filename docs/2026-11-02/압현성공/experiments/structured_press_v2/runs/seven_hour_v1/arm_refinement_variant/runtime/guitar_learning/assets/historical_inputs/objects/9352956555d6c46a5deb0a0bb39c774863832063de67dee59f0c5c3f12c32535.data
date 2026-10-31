"""Allow mass/COM/inertia updates only in an explicit construction window."""
from .environment_guard_v2 import InitializationGuard

class ConstructionPropertyGuard(InitializationGuard):
    def __getattr__(self,name):
        if name!='set_actor_rigid_body_properties':return super().__getattr__(name)
        def construction_only(*args,**kwargs):
            if self.owner.initialization_complete or not self.owner.property_submission_allowed:
                self.owner.property_setter_rejections+=1
                self.owner.forbidden_calls.append(name)
                raise RuntimeError('rigid-body properties only allowed in construction window')
            self.owner.property_setter_calls+=1
            return self.gym.set_actor_rigid_body_properties(*args,**kwargs)
        return construction_only
