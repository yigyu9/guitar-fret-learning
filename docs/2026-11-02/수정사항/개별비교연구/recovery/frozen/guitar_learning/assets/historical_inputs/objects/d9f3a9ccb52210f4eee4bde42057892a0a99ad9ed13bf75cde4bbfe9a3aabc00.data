"""Read importer collision masks without a physics step."""
import json
from pathlib import Path

from .thigh_palm_support import SupportEnvironment, PHASE as SUPPORT_PHASE
from .build_fixed_lower_asset import read, sha
from .environment import ROOT

PHASE=ROOT/'docs/2026-10-12/stability_adapter_2/results/self_collision_v1'


class ImporterGym:
    def __init__(self,gym,owner):
        self.gym,self.owner=gym,owner

    def __getattr__(self,name):
        return getattr(self.gym,name)

    def create_actor(self,env,asset,pose,name,group,filter):
        actor=self.gym.create_actor(env,asset,pose,name,group,-1 if name=='human' else filter)
        if name=='human':
            self.owner.importer_filters=[int(p.filter) for p in self.gym.get_actor_rigid_shape_properties(env,actor)]
        return actor


class ProbeEnvironment(SupportEnvironment):
    def _create_scene(self):
        gym=self.gym
        self.gym=ImporterGym(gym,self)
        try:
            super()._create_scene()
        finally:
            self.gym=gym


def main():
    if (PHASE/'importer_probe.json').exists():
        raise FileExistsError('preserve importer audit')
    search=read(SUPPORT_PHASE/'search_near_touch.json')
    settings=Path(search['rows'][0]['settings_path'])
    inputs=[Path(__file__).resolve(),settings,SUPPORT_PHASE/'search_near_touch.json']
    inputs += [Path(p) for p in search['input_sha256']]
    hashes={str(p):sha(p) for p in inputs}
    env=ProbeEnvironment(read(settings),search['guitar_initial_translation_m'])
    try:
        ranges=env.gym.get_actor_rigid_body_shape_indices(env.env,env.human)
        masks={name:env.importer_filters[span.start:span.start+span.count] for name,span in zip(env.human_bodies,ranges)}
        report={'human_importer_filters':masks,'unique_masks':sorted(set(env.importer_filters)),
            'physics_steps':env.steps,'native_initializations':1,'input_sha256':hashes}
        if not all(sha(Path(p))==h for p,h in hashes.items()):raise ValueError('probe inputs changed')
        PHASE.mkdir(parents=True,exist_ok=True)
        (PHASE/'importer_probe.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps(masks,indent=2))
    finally:
        env.close()


if __name__=='__main__':main()
