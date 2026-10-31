"""Native self collision with importer exclusions and separate left/right hands."""
from functools import reduce
from operator import or_

from .self_collision_probe import ProbeEnvironment


class SelfCollisionEnvironment(ProbeEnvironment):
    def _create_scene(self):
        super()._create_scene()
        human=self.gym.get_actor_rigid_shape_properties(self.env,self.human)
        spans=self.gym.get_actor_rigid_body_shape_indices(self.env,self.human)
        masks=self.importer_filters.copy()
        occupied=reduce(or_,masks,0)
        spare=iter(1<<i for i in range(31) if not occupied&(1<<i))
        guitar_bit=next(spare)
        left_elbow=masks[spans[self.human_bodies.index('L_Elbow')].start]
        right_elbow=masks[spans[self.human_bodies.index('R_Elbow')].start]
        if not left_elbow or not right_elbow or left_elbow&right_elbow:
            raise ValueError('importer elbow masks cannot be separated')
        for name,span in zip(self.human_bodies,spans):
            for i in range(span.start,span.start+span.count):
                if name=='L_Wrist' or name.startswith('LH:'):
                    masks[i]&=~right_elbow
                elif name=='R_Wrist' or name.startswith('RH:'):
                    masks[i]&=~left_elbow
                if name!='LH:thumb_pad' and not masks[i]:
                    # Unique bits keep all formerly-zero pairs allowed, while
                    # allowing excluded proxy masks to block these shapes.
                    masks[i]=next(spare)
        blocked=reduce(or_,masks,guitar_bit)
        for name,span in zip(self.human_bodies,spans):
            for i in range(span.start,span.start+span.count):
                human[i].filter=blocked if name=='LH:thumb_pad' else masks[i]
        self.gym.set_actor_rigid_shape_properties(self.env,self.human,human)
        guitar=self.gym.get_actor_rigid_shape_properties(self.env,self.guitar)
        ranges=self.gym.get_actor_rigid_body_shape_indices(self.env,self.guitar)
        for name,span in zip(self.guitar_bodies,ranges):
            for i in range(span.start,span.start+span.count):
                guitar[i].filter=blocked if name in ('G:thumb_support_proxy','G:pluck_range') else guitar_bit
        self.gym.set_actor_rigid_shape_properties(self.env,self.guitar,guitar)
        self.self_collision_policy={'guitar_reserved_bit':guitar_bit,'proxy_exclusion_mask':blocked,
            'left_elbow_mask':left_elbow,'right_elbow_mask':right_elbow,
            'scope':'Importer exclusions preserved except opposite hand/elbow group separation; within-hand exclusions retained.'}
        self.collision_filters={}
        for actor,names,ranges in ((self.human,self.human_bodies,spans),(self.guitar,self.guitar_bodies,ranges)):
            props=self.gym.get_actor_rigid_shape_properties(self.env,actor)
            self.collision_filters.update({name:[int(props[i].filter) for i in range(span.start,span.start+span.count)]
                for name,span in zip(names,ranges)})
