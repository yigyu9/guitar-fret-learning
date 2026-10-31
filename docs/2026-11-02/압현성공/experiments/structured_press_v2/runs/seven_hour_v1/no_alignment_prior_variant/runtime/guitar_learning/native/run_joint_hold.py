"""Read actual native body and DOF state without stepping the simulation."""
from isaacgym import gymapi
from .native_contacts import plain

def native_state(env):
    return {'physics_step':env.steps,'human_body_states':plain(env.bodies(env.human)),
        'guitar_body_states':plain(env.bodies(env.guitar)),
        'human_dof_states':plain(env.gym.get_actor_dof_states(env.env,env.human,gymapi.STATE_ALL))}
