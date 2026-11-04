"""기존 왼손 실행 경로를 바꾸지 않는 오른손 27축 전용 GPU 풀."""
import copy

from guitar_learning.training.rollout import GpuPool
from .control import Right27Controller
from .environment import Right27Environment


class Right27Pool(GpuPool):
    def __init__(self, settings, out):
        if settings['specialist']['role'] != 'right' or 'finger_skill' in settings:
            raise ValueError('Right27 requires right song settings, without finger_skill')
        super().__init__(settings, out)
        try:
            # 부모 초기화는 물리 step 없이 reset만 수행한다. 같은 scene을 재사용한다.
            self.controller = Right27Controller(self.scene, base=self.controller)
            metadata = copy.deepcopy(self.scene.metadata)
            metadata['action_contract'] = copy.deepcopy(self.controller.contract)
            self.environment = Right27Environment(metadata,
                bundle=settings['song_training']['bundle'], song=settings['song'],
                hand='right', device=settings['device'])
            native = copy.deepcopy(self.contract['native_backend'])
            native['control'] = copy.deepcopy(self.controller.contract)
            self.contract = copy.deepcopy(self.environment.contract)
            self.contract['native_backend'] = native
            self.observation = self.reset()[0]
        except BaseException:
            self.close()
            raise
