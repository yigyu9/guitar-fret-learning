"""관측을 인코딩하여 공동·손별·손가락 정책의 행동 분포와 가치를 출력한다.

공유 인코더와 정책별 출력부를 정의하며, 가중치 전이와 고정 지지 정책의 입력 계약도 검증한다."""
import math
import copy
import torch
from torch import nn
from torch.distributions import Normal
import torch.nn.functional as F
from pathlib import Path
from guitar_learning.core.control import ACTIVE_NAMES


class Encoder(nn.Module):
    def __init__(self, state_dim, event_dim, fusion, priority_count=2):
        super().__init__()
        if type(priority_count) is not int or priority_count < 1:
            raise ValueError('positive integer priority_count required')
        self.state = nn.Sequential(nn.Linear(state_dim, 256), nn.Tanh(), nn.Linear(256, 256), nn.Tanh())
        self.event = nn.Sequential(nn.Linear(event_dim, 128), nn.Tanh(), nn.Linear(128, 128), nn.Tanh())
        self.query = nn.Linear(256, 128, bias=False)
        layers = []
        width = 256 + 128 + priority_count * 128
        for output in fusion:
            layers.extend((nn.Linear(width, output), nn.Tanh()))
            width = output
        self.output = nn.Sequential(*layers)

    def forward(self, state, events, mask, priority_events, priority_mask):
        hidden = self.state(state)
        tokens = self.event(torch.where(mask[..., None], events, torch.zeros_like(events)))
        logits = (tokens * self.query(hidden)[:, None]).sum(-1) / math.sqrt(128)
        logits = logits.masked_fill(~mask, -torch.inf)
        null = torch.where(mask.any(-1, keepdim=True), -torch.inf, 0.)
        weights = torch.cat((logits, null), -1).softmax(-1)[:, :-1]
        context = (weights[..., None] * tokens).sum(1)
        priority = self.event(torch.where(priority_mask[..., None], priority_events, torch.zeros_like(priority_events)))
        priority = priority * priority_mask[..., None]
        return self.output(torch.cat((hidden, context, priority.flatten(1)), -1))


class Policy(nn.Module):
    """공용 39축 정책 기반. 기본 J 학습은 아래 FingerSkillPolicy를 사용한다."""
    role_sizes = (33, 6)

    def __init__(self, state_dim, event_dim=24, size="medium", contract=None):
        super().__init__()
        if min(state_dim, event_dim) < 1:
            raise ValueError('positive explicit dimensions required')
        if not isinstance(contract, dict) or not contract:
            raise ValueError('explicit nonempty input/control contract required')
        sizes = dict(small=(256, 256, 256), medium=(512, 512, 256), large=(1024, 1024, 512))
        if size not in sizes or event_dim != 24:
            raise ValueError('size must be small/medium/large and event_dim must be 24')
        fusion = sizes[size]
        if contract.get('schema') != 'guitar_learning.training.v1' or any(
                not isinstance(contract.get(key), dict) for key in ('observation', 'action', 'task', 'reward', 'termination')):
            raise ValueError('training schema and observation/action/task/reward/termination dictionaries required')
        self.architecture = dict(schema='guitar_attention39_v1', state_dim=state_dim, event_dim=event_dim,
                                 size=size, state_layers=(256,256), event_layers=(128,128), fusion=fusion,
                                 normalization='fixed_observation_scaling_no_running_updates',
                                 roles=self.role_sizes, priority_slots=('current','nearest_strict_deadline'),
                                 contract=copy.deepcopy(contract))
        self.actor_encoder = Encoder(state_dim,event_dim,fusion)
        self.value_encoder = Encoder(state_dim,event_dim,fusion)
        self.actor_heads = nn.ModuleList(nn.Linear(fusion[-1],n) for n in self.role_sizes)
        for head in self.actor_heads:
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        self.log_std = nn.Parameter(torch.full((39,),-3.))
        self.reward_critic = nn.Linear(fusion[-1],1)
        self.cost_critic = nn.Linear(fusion[-1],1)

    def actor_parameters(self):
        return [*self.actor_encoder.parameters(),*self.actor_heads.parameters(),self.log_std]

    def value_parameters(self):
        return [*self.value_encoder.parameters(),*self.reward_critic.parameters(),*self.cost_critic.parameters()]

    def _validate(self,state,events,mask,priority_events,priority_mask):
        if state.ndim!=2 or state.shape[-1]!=self.architecture['state_dim']:
            raise ValueError('state must be [B,state_dim]')
        if events.ndim!=3 or events.shape[0]!=state.shape[0] or events.shape[-1]!=self.architecture['event_dim']:
            raise ValueError('events must be [B,K,event_dim]')
        if mask.shape!=events.shape[:2] or mask.dtype!=torch.bool:
            raise ValueError('mask must be bool [B,K]')
        priority_count = len(self.architecture['priority_slots'])
        if priority_events.shape!=(state.shape[0],priority_count,self.architecture['event_dim']) or priority_mask.shape!=(state.shape[0],priority_count) or priority_mask.dtype!=torch.bool:
            raise ValueError('priority events[B,%d,E] and bool priority_mask[B,%d] required' % (priority_count, priority_count))
        if not torch.isfinite(priority_events[priority_mask]).all():
            raise ValueError('nonfinite valid priority event')
        if not torch.isfinite(state).all() or not torch.isfinite(events[mask]).all():
            raise ValueError('nonfinite valid policy input')

    @staticmethod
    def log_probability(mean,log_std,latent):
        correction=2*(math.log(2)-latent-F.softplus(-2*latent))
        return (Normal(mean,log_std.exp()).log_prob(latent)-correction).sum(-1)

    def forward(self,state,events,mask,priority_events,priority_mask):
        self._validate(state,events,mask,priority_events,priority_mask)
        actor=self.actor_encoder(state,events,mask,priority_events,priority_mask)
        value=self.value_encoder(state,events,mask,priority_events,priority_mask)
        mean=torch.cat([head(actor) for head in self.actor_heads],-1)
        log_std=self.log_std.clamp(-5,2).expand_as(mean)
        return dict(mean=mean,log_std=log_std,reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def act(self,state,events,mask,priority_events,priority_mask,deterministic=False):
        result=self(state,events,mask,priority_events,priority_mask)
        latent=result['mean'] if deterministic else Normal(result['mean'],result['log_std'].exp()).sample()
        result.update(action=latent.tanh(),latent=latent,
                      logp=self.log_probability(result['mean'],result['log_std'],latent))
        return result

    def evaluate(self,state,events,mask,priority_events,priority_mask,latent):
        if latent.shape!=(state.shape[0],39) or not torch.isfinite(latent).all():
            raise ValueError('finite latent[B,39] required')
        result=self(state,events,mask,priority_events,priority_mask)
        result.update(logp=self.log_probability(result['mean'],result['log_std'],latent),
                      entropy=Normal(result['mean'],result['log_std'].exp()).entropy().sum(-1))
        return result


class SpecialistPolicy(nn.Module):
    """기존 song 경로의 left/right/joint 정책. 기본 J 학습은 FingerSkillPolicy를 사용한다."""
    role_sizes = (33, 6)
    role_slices = {'left': slice(0, 33), 'right': slice(33, 39)}
    schema = 'guitar_specialists39_v1'

    def __init__(self, state_dim, event_dim=24, size='medium', contract=None,
                 role='left', frozen_partner=False):
        super().__init__()
        if min(state_dim, event_dim) < 1 or event_dim != 24:
            raise ValueError('positive explicit dimensions and event_dim=24 required')
        sizes = dict(small=(256, 256, 256), medium=(512, 512, 256), large=(1024, 1024, 512))
        if size not in sizes or role not in ('left', 'right', 'joint'):
            raise ValueError('small/medium/large size and left/right/joint role required')
        if not isinstance(frozen_partner, bool) or (role == 'joint' and frozen_partner):
            raise ValueError('frozen partner is only available for single-hand stages')
        if not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1' or any(
                not isinstance(contract.get(key), dict)
                for key in ('observation', 'action', 'task', 'reward', 'termination')):
            raise ValueError('explicit training observation/action/task/reward/termination contract required')
        reward_schema = contract['reward'].get('schema')
        current_hand = reward_schema in ('guitar_learning.gpu_tensor_song_reward.v21', 'guitar_learning.gpu_tensor_song_reward.v22')
        finger_state_dim = 552 if reward_schema == 'guitar_learning.gpu_tensor_song_reward.v22' else 551 if current_hand else 544
        thumb_schema = 'guitar_learning.gpu_thumb_rear_support.v2' if finger_state_dim == 552 else 'guitar_learning.gpu_thumb_rear_support.v1'
        if current_hand and contract['observation'].get('thumb_support', {}).get('schema') != thumb_schema:
            raise ValueError('Current reward version requires its explicit thumb support observation contract')
        priority_slots = ('current', 'nearest_strict_deadline')
        observation = contract['observation']
        priority_count = observation.get('priority_slots', 2)
        if type(priority_count) is not int:
            raise ValueError('integer observation priority_slots required')
        if priority_count != 2 or 'finger_targets' in observation:
            targets = observation.get('finger_targets')
            expected_slots = [finger+'_'+kind for finger in ('index', 'middle', 'ring', 'pinky')
                              for kind in ('tracking', 'next')]
            if (role != 'left' or not isinstance(contract.get('native_backend'), dict) or
                    contract['native_backend'].get('pipeline') != 'gpu' or
                    state_dim != finger_state_dim or observation.get('dimension') != finger_state_dim or priority_count != 8 or
                    not isinstance(targets, dict) or targets.get('schema') != 'guitar_learning.left_finger_targets.v1' or
                    targets.get('slots') != expected_slots):
                raise ValueError('GPU left state dimension must match its reward version and eight finger-target priority slots')
            priority_slots = tuple(targets['slots'])
        finger_actor = contract['reward'].get('schema') in (
            'guitar_learning.gpu_tensor_song_reward.v8', 'guitar_learning.gpu_tensor_song_reward.v9',
            'guitar_learning.gpu_tensor_song_reward.v10', 'guitar_learning.gpu_tensor_song_reward.v11',
            'guitar_learning.gpu_tensor_song_reward.v12', 'guitar_learning.gpu_tensor_song_reward.v13', 'guitar_learning.gpu_tensor_song_reward.v14', 'guitar_learning.gpu_tensor_song_reward.v15', 'guitar_learning.gpu_tensor_song_reward.v16', 'guitar_learning.gpu_tensor_song_reward.v17', 'guitar_learning.gpu_tensor_song_reward.v18', 'guitar_learning.gpu_tensor_song_reward.v19', 'guitar_learning.gpu_tensor_song_reward.v20', 'guitar_learning.gpu_tensor_song_reward.v21', 'guitar_learning.gpu_tensor_song_reward.v22')
        if finger_actor:
            if role != 'left' or priority_count != 8 or state_dim != finger_state_dim:
                raise ValueError('Finger actor requires matching GPU left state/eight-slot contract')
            fields = observation.get('fields')
            if (not isinstance(fields, list) or len(fields) != finger_state_dim or
                    any(not isinstance(field, str) for field in fields) or len(set(fields)) != finger_state_dim or
                    contract['action'].get('names') != list(ACTIVE_NAMES)):
                raise ValueError('Finger actor requires unique named state and exact active action order')
            local_fields = {}
            for finger in ('index', 'middle', 'ring', 'pinky'):
                gate_field = ('standby_gate' if contract['reward']['schema'] in (
                              'guitar_learning.gpu_tensor_song_reward.v20',
                              'guitar_learning.gpu_tensor_song_reward.v21', 'guitar_learning.gpu_tensor_song_reward.v22') else 'idle_weight')
                joints = ['LH:'+finger+suffix for suffix in ('1_x', '1_z', '2', '3')]
                local_fields[finger] = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error')
                                        for joint in joints]
                local_fields[finger] += ['finger_posture.'+finger+'.'+joint+'.'+trig
                                        for joint in ('MCP', 'PIP', 'DIP') for trig in ('sin', 'cos')]
                local_fields[finger] += ['finger_posture.'+finger+'.'+field for field in ('valid', gate_field)]
            if any(field not in fields for names in local_fields.values() for field in names):
                raise ValueError('v8 finger actor named local joint/posture state missing')
        fusion = sizes[size]
        self.role = role
        self.frozen_partner = frozen_partner
        self.trainable_roles = ('left', 'right') if role == 'joint' else (role,)
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=event_dim,
                                 size=size, state_layers=(256, 256), event_layers=(128, 128),
                                 fusion=fusion, normalization='fixed_observation_scaling_no_running_updates',
                                 roles=self.role_sizes, priority_slots=priority_slots,
                                 role=role, frozen_partner=frozen_partner,
                                 likelihood='trainable_channels_only_v1',
                                 inactive_action='deterministic_partner_or_zero_residual',
                                 contract=copy.deepcopy(contract))
        self.actor_encoders = nn.ModuleDict({name: Encoder(state_dim, event_dim, fusion, priority_count=priority_count)
                                            for name in self.role_slices})
        self.actor_heads = nn.ModuleDict({name: nn.Linear(fusion[-1], count)
                                         for name, count in zip(self.role_slices, self.role_sizes)})
        for name, head in self.actor_heads.items():
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
            if name not in self.trainable_roles:
                self.actor_encoders[name].requires_grad_(False)
                head.requires_grad_(False)
        self.value_encoder = Encoder(state_dim, event_dim, fusion, priority_count=priority_count)
        self.reward_critic = nn.Linear(fusion[-1], 1)
        self.cost_critic = nn.Linear(fusion[-1], 1)
        self.log_std = nn.Parameter(torch.full((39,), -3.))
        # 체크포인트 상태이므로, 고정 상대 정책을 재개할 때 완전한 행동 정책을 가져왔다는
        # 사실을 유지해야 하며, 출력부를 조용히 0으로 대체해서는 안 된다.
        self.register_buffer('partner_initialized', torch.zeros(2, dtype=torch.bool))
        # 기존 경로에는 모듈을 추가하지 않는다. 상태 키·초기화 순서·난수 소비 순서가
        # 엄격한 체크포인트 계약에 포함되기 때문이다.
        if finger_actor:
            self.architecture['finger_actor'] = dict(
                schema='guitar_learning.targeted_finger_actor.v1',
                fingers=tuple(local_fields), shared_action_names=tuple(ACTIVE_NAMES[:17]),
                local_fields=local_fields,
                local_indices={finger: [fields.index(field) for field in names]
                               for finger, names in local_fields.items()},
                priority_slots_per_finger=2, token_width=128, local_width=20,
                context_width=fusion[-1], hidden=(128,), activation='Tanh',
                output_per_finger=4, final_initialization='zero',
                inputs='shared actor context; same actor event encoder masked tracking/next; own scaled state')
            self.actor_heads['left'] = nn.Linear(fusion[-1], 17)
            nn.init.zeros_(self.actor_heads['left'].weight)
            nn.init.zeros_(self.actor_heads['left'].bias)
            self.finger_heads = nn.ModuleDict({finger: nn.Sequential(
                nn.Linear(fusion[-1]+2*128+20, 128), nn.Tanh(), nn.Linear(128, 4))
                for finger in local_fields})
            for head in self.finger_heads.values():
                nn.init.zeros_(head[-1].weight)
                nn.init.zeros_(head[-1].bias)

    def actor_parameters(self):
        parameters = []
        for name in self.trainable_roles:
            parameters.extend(self.actor_encoders[name].parameters())
            parameters.extend(self.actor_heads[name].parameters())
        if hasattr(self, 'finger_heads'):
            parameters.extend(self.finger_heads.parameters())
        return [*parameters, self.log_std]

    # 공통 가치망의 매개변수 선택을 재사용한다.
    value_parameters = Policy.value_parameters

    _validate = Policy._validate

    def _active_mask(self):
        if self.role == 'joint':
            return torch.ones(39, dtype=torch.bool, device=self.log_std.device)
        mask = torch.zeros(39, dtype=torch.bool, device=self.log_std.device)
        mask[self.role_slices[self.role]] = True
        return mask

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        inputs = (state, events, mask, priority_events, priority_mask)
        means = []
        for index, name in enumerate(self.role_slices):
            if name in self.trainable_roles:
                context = self.actor_encoders[name](*inputs)
                mean = self.actor_heads[name](context)
                if name == 'left' and hasattr(self, 'finger_heads'):
                    priority = self.actor_encoders[name].event(torch.where(
                        priority_mask[..., None], priority_events, torch.zeros_like(priority_events)))
                    priority = priority * priority_mask[..., None]
                    finger_means = []
                    for finger_index, (finger, head) in enumerate(self.finger_heads.items()):
                        indices = self.architecture['finger_actor']['local_indices'][finger]
                        local = state[:, indices]
                        tokens = priority[:, 2*finger_index:2*finger_index+2].flatten(1)
                        finger_means.append(head(torch.cat((context, tokens, local), -1)))
                    mean = torch.cat((mean, *finger_means), -1)
                means.append(mean)
            elif self.frozen_partner:
                if not bool(self.partner_initialized[index]):
                    raise ValueError('frozen partner requires a transferred actor or strict checkpoint resume')
                with torch.no_grad():
                    means.append(self.actor_heads[name](self.actor_encoders[name](*inputs)))
            else:
                means.append(state.new_zeros((state.shape[0], self.role_sizes[index])))
        mean = torch.cat(means, -1)
        # 고정 대체값으로 비활성 채널의 기존 39차원 해석적 KL을 정확히 0으로 만든다.
        # 이 값은 해당 관절에서 실제로 표본을 뽑는 분포가 아니다.
        log_std = torch.where(self._active_mask(), self.log_std.clamp(-5, 2),
                              torch.full_like(self.log_std, -3.)).expand_as(mean)
        value = self.value_encoder(*inputs)
        return dict(mean=mean, log_std=log_std,
                    reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        mean, log_std, latent = mean[..., active], log_std[..., active], latent[..., active]
        correction = 2 * (math.log(2) - latent - F.softplus(-2 * latent))
        return (Normal(mean, log_std.exp()).log_prob(latent) - correction).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            latent[..., active] = Normal(result['mean'][..., active], result['log_std'][..., active].exp()).sample()
        result.update(action=latent.tanh(), latent=latent,
                      logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (state.shape[0], 39) or not torch.isfinite(latent).all():
            raise ValueError('finite latent[B,39] required')
        result = self(state, events, mask, priority_events, priority_mask)
        active = self._active_mask()
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
                      entropy=Normal(result['mean'][..., active], result['log_std'][..., active].exp()).entropy().sum(-1))
        return result

    def transfer_actor(self, checkpoint, role):
        """완전한 손별 행동 정책으로 초기화하며, 가치망·최적화기·난수 상태는 가져오지 않는다.

        단계 메타데이터는 task.specialist 아래에 둔다. 나머지 과제·관측·행동·종료 의미는
        정확히 같아야 하며, 원본은 요청한 한 손 단계의 갱신을 완료한 상태여야 한다.
        """
        if role not in self.role_slices:
            raise ValueError('left/right source role required')
        payload = (torch.load(Path(checkpoint), map_location='cpu', weights_only=False)
                   if isinstance(checkpoint, (str, Path)) else checkpoint)
        if not isinstance(payload, dict):
            raise ValueError('PPO specialist checkpoint dictionary required')
        identity = payload.get('identity', {})
        if not isinstance(identity, dict):
            raise ValueError('own PPO checkpoint identity required')
        source = identity.get('architecture', {})
        if identity.get('schema') != 'guitar_learning_ppo_v1' or not isinstance(identity.get('config'), dict):
            raise ValueError('own PPO checkpoint identity required')
        if not isinstance(source, dict) or source.get('schema') != self.schema or source.get('role') != role:
            raise ValueError('requested single-hand specialist source required; shared/joint actors cannot be spliced')
        updates = payload.get('updates')
        if isinstance(updates, bool) or not isinstance(updates, int) or updates < 1:
            raise ValueError('source specialist must have completed a PPO update')
        for key in ('state_dim', 'event_dim', 'size', 'state_layers', 'event_layers', 'fusion',
                    'normalization', 'roles', 'priority_slots', 'likelihood', 'inactive_action'):
            if source.get(key) != self.architecture[key]:
                raise ValueError('source specialist architecture mismatch: ' + key)
        if source.get('finger_actor') != self.architecture.get('finger_actor'):
            raise ValueError('source specialist architecture mismatch: finger_actor')
        source_contract = source.get('contract', {})
        target_contract = self.architecture['contract']
        if not isinstance(source_contract, dict) or any(
                not isinstance(source_contract.get(key), dict)
                for key in ('observation', 'action', 'task', 'reward', 'termination')):
            raise ValueError('source specialist training contract required')
        for key in ('schema', 'observation', 'action', 'termination'):
            if source_contract.get(key) != target_contract[key]:
                raise ValueError('source specialist contract mismatch: ' + key)
        source_task = copy.deepcopy(source_contract.get('task', {}))
        target_task = copy.deepcopy(target_contract['task'])
        source_task.pop('specialist', None)
        target_task.pop('specialist', None)
        if source_task != target_task:
            raise ValueError('source specialist task mismatch')
        model = payload.get('model')
        expected = self.state_dict()
        if not isinstance(model, dict) or model.keys() != expected.keys() or any(
                not isinstance(value, torch.Tensor) or value.shape != expected[key].shape
                or value.dtype != expected[key].dtype or not torch.isfinite(value).all()
                for key, value in model.items()):
            raise ValueError('source specialist finite model/shape/dtype mismatch')
        # 대상 텐서를 바꾸기 전에 모든 검증을 마친다.
        with torch.no_grad():
            prefixes = ['actor_encoders.' + role + '.', 'actor_heads.' + role + '.']
            if role == 'left' and hasattr(self, 'finger_heads'):
                prefixes.append('finger_heads.')
            for prefix in prefixes:
                for key, value in model.items():
                    if key.startswith(prefix):
                        expected[key].copy_(value)
            selection = self.role_slices[role]
            self.log_std[selection].copy_(model['log_std'][selection])
            self.partner_initialized[tuple(self.role_slices).index(role)] = True
        return dict(role=role, source_updates=updates, source_architecture=copy.deepcopy(source),
                    source_config=copy.deepcopy(identity['config']), source_metadata=copy.deepcopy(payload.get('metadata')))


FINGERS = ('index', 'middle', 'ring', 'pinky')
SKILL_FIELDS = ('finger_skill.remaining_s',)
WRIST_TERMINATION_FIELDS = ('wrist_termination.active', 'wrist_termination.elapsed_s',
                           'wrist_termination.preparation_remaining_s',
                           'wrist_termination.severe_elapsed_s')


class FingerSkillPolicy(nn.Module):
    """지지 17축과 네 손가락 16축을 모두 학습하는 J 전용 독립 Gaussian 정책."""
    schema = 'guitar_learning.finger_skill_policy.v2'
    phase = 'J'
    exploration = 'independent'

    def __init__(self, state_dim, event_dim=24, size='medium', contract=None):
        super().__init__()
        sizes = dict(small=(256, 256, 256), medium=(512, 512, 256), large=(1024, 1024, 512))
        if size not in sizes:
            raise ValueError('explicit small/medium/large size required')
        if event_dim != 24 or not isinstance(contract, dict) or contract.get('schema') != 'guitar_learning.training.v1':
            raise ValueError('explicit training contract and 24 event columns required')
        if any(not isinstance(contract.get(key), dict) for key in
               ('observation', 'action', 'task', 'reward', 'termination', 'native_backend')):
            raise ValueError('complete GPU training contract required')
        observation = contract['observation']
        fields = observation.get('fields')
        spec = contract['task'].get('finger_skill', {})
        tail = SKILL_FIELDS+WRIST_TERMINATION_FIELDS
        if state_dim != 557:
            raise ValueError('joint finger skill requires557 states')
        slots = [finger+'_'+kind for finger in FINGERS for kind in ('tracking', 'next')]
        if (not isinstance(fields, list) or len(fields) != state_dim or
                any(not isinstance(field, str) for field in fields) or len(set(fields)) != state_dim or
                observation.get('dimension') != state_dim or tuple(fields[-len(tail):]) != tail or
                observation.get('priority_slots') != 8 or
                observation.get('finger_targets', {}).get('slots') != slots or
                observation.get('finger_targets', {}).get('schema') != 'guitar_learning.left_finger_targets.v1' or
                contract['action'].get('names') != list(ACTIVE_NAMES) or
                contract['native_backend'].get('pipeline') != 'gpu' or
                not isinstance(spec, dict) or spec.get('schema') != 'guitar_learning.finger_skill.v3' or
                spec.get('phase') != self.phase or spec.get('exploration') != self.exploration or
                type(spec.get('hold_ticks')) is not int or spec['hold_ticks'] != 1):
            raise ValueError('named finger-skill state, exact action order, GPU, phase and exploration contract required')
        local_fields = {}
        for finger in FINGERS:
            joints = ['LH:'+finger+suffix for suffix in ('1_x', '1_z', '2', '3')]
            local_fields[finger] = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error') for joint in joints]
            local_fields[finger] += ['finger_posture.'+finger+'.'+joint+'.'+trig
                                    for joint in ('MCP', 'PIP', 'DIP') for trig in ('sin', 'cos')]
            local_fields[finger] += ['finger_posture.'+finger+'.'+name for name in ('valid', 'standby_gate')]
        required = [name for names in local_fields.values() for name in names]
        required += [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error', 'previous_action')
                     for joint in ACTIVE_NAMES[:17]]
        if any(name not in fields for name in required):
            raise ValueError('named support and local finger fields missing')

        # 지지 인코더는 명시된 몸통·팔·엄지·손목 정보만 받는다.
        # 손가락의 세부 압현 상태는 손가락 인코더와 각 손가락 출력부가 담당한다.
        support_fields = [block+'.'+joint for block in ('q_offset', 'q_velocity', 'target_error', 'previous_action')
                          for joint in ACTIVE_NAMES[:17]]
        support_fields += [field for field in fields if field.startswith((
            'guitar_in_pelvis.', 'guitar_reset_delta.', 'feet_reset_delta.',
            'L_Wrist_in_guitar.', 'LH:thumb3_in_guitar.', 'thumb_support.',
            'contact_loss_s.', 'wrist_region.delta_')) or field in (
                'contact.chest', 'contact.right_upper_arm', 'contact.right_thigh',
                'contact.thumb', 'contact.left_foot', 'contact.right_foot')]
        support_fields += list(WRIST_TERMINATION_FIELDS)
        self.architecture = dict(schema=self.schema, state_dim=state_dim, event_dim=event_dim,
            size=size, fusion=sizes[size], priority_slots=tuple(slots), phase=self.phase,
            exploration=self.exploration, normalization='fixed_observation_scaling_no_running_updates',
            support_fields=support_fields, support_event_columns=tuple(range(9)),
            local_fields=local_fields,
            local_indices={finger: [fields.index(field) for field in names] for finger, names in local_fields.items()},
            likelihood='joint33_independent_physical_tanh_latent_v1',
            contract=copy.deepcopy(contract))
        self.register_buffer('support_indices', torch.tensor([fields.index(field) for field in support_fields]))
        self.register_buffer('support_event_columns', torch.tensor(list(range(9))))
        fusion = sizes[size]
        self.support_encoder = Encoder(len(support_fields), 9, fusion, priority_count=8)
        self.support_head = nn.Linear(fusion[-1], 17)
        self.finger_encoder = Encoder(state_dim, event_dim, fusion, priority_count=8)
        self.finger_heads = nn.ModuleDict({finger: nn.Sequential(
            nn.Linear(fusion[-1]+256+20, 128), nn.Tanh(), nn.Linear(128, 4)) for finger in FINGERS})
        for head in (self.support_head, *(head[-1] for head in self.finger_heads.values())):
            nn.init.zeros_(head.weight)
            nn.init.zeros_(head.bias)
        self.support_log_std = nn.Parameter(torch.full((17,), -3.))
        self.finger_log_std = nn.Parameter(torch.full((16,), -3.))
        self.value_encoder = Encoder(state_dim, event_dim, fusion, priority_count=8)
        self.reward_critic = nn.Linear(fusion[-1], 1)
        self.cost_critic = nn.Linear(fusion[-1], 1)

    _validate = Policy._validate

    def actor_parameters(self):
        groups = (self.support_encoder, self.support_head, self.finger_encoder, self.finger_heads)
        return [parameter for group in groups for parameter in group.parameters()] + [
            self.support_log_std, self.finger_log_std]

    # 공통 가치망의 매개변수 선택을 재사용한다.
    value_parameters = Policy.value_parameters

    def _active_mask(self):
        mask = torch.zeros(39, dtype=torch.bool, device=self.support_log_std.device)
        mask[:33] = True
        return mask

    def forward(self, state, events, mask, priority_events, priority_mask):
        self._validate(state, events, mask, priority_events, priority_mask)
        support = self.support_encoder(state[:, self.support_indices],
            events[..., self.support_event_columns], mask,
            priority_events[..., self.support_event_columns], priority_mask)
        support_mean = self.support_head(support)
        context = self.finger_encoder(state, events, mask, priority_events, priority_mask)
        priority_tokens = self.finger_encoder.event(torch.where(
            priority_mask[..., None], priority_events, torch.zeros_like(priority_events),
        ))
        priority_tokens = priority_tokens * priority_mask[..., None]
        # 손가락마다 공통 문맥 + tracking/next 두 토큰 + 자기 관절·자세 20열을 받아 4축을 출력한다.
        finger_means = []
        for finger_index, finger in enumerate(FINGERS):
            finger_tokens = priority_tokens[:, 2*finger_index:2*finger_index+2].flatten(1)
            local_state = state[:, self.architecture['local_indices'][finger]]
            finger_input = torch.cat((context, finger_tokens, local_state), -1)
            finger_means.append(self.finger_heads[finger](finger_input))
        finger_mean = torch.cat(finger_means, -1)
        # 지지 17 + 손가락 16 + 비활성 오른손 6으로 공용 39축 출력 형식을 유지한다.
        mean = torch.cat((support_mean, finger_mean, state.new_zeros((state.shape[0], 6))), -1)
        active_log_std = torch.cat((
            self.support_log_std,
            self.finger_log_std,
            self.support_log_std.new_full((6,), -3.),
        )).clamp(-5, 2)
        log_std = torch.where(
            self._active_mask(), active_log_std, active_log_std.new_full((39,), -3.),
        ).expand_as(mean)
        value = self.value_encoder(state, events, mask, priority_events, priority_mask)
        return dict(mean=mean, log_std=log_std, reward_value=self.reward_critic(value).squeeze(-1),
                    cost_value=self.cost_critic(value).squeeze(-1))

    def log_probability(self, mean, log_std, latent):
        active = self._active_mask()
        bm, bz = mean[..., active], latent[..., active]
        correction = 2*(math.log(2)-latent[..., active]-F.softplus(-2*latent[..., active]))
        return (Normal(bm, log_std[..., active].exp()).log_prob(bz)-correction).sum(-1)

    def analytic_kl(self, old_mean, old_log_std, mean, log_std):
        active = self._active_mask()
        difference = (old_mean-mean)[..., active]
        previous_log_std, current_log_std = old_log_std[..., active], log_std[..., active]
        return (
            current_log_std-previous_log_std
            +(previous_log_std.mul(2).exp()+difference.square())/(2*current_log_std.mul(2).exp())
            -.5
        ).sum(-1)

    def act(self, state, events, mask, priority_events, priority_mask, deterministic=False):
        result = self(state, events, mask, priority_events, priority_mask)
        latent = result['mean'].clone()
        active = self._active_mask()
        if not deterministic:
            noise = torch.zeros_like(latent)
            noise[..., active] = Normal(torch.zeros_like(latent[..., active]),
                                         result['log_std'][..., active].exp()).sample()
            latent = latent+noise
        result.update(action=latent.tanh(), latent=latent,
                      logp=self.log_probability(result['mean'], result['log_std'], latent))
        return result

    def evaluate(self, state, events, mask, priority_events, priority_mask, latent):
        if latent.shape != (state.shape[0], 39) or not torch.isfinite(latent).all():
            raise ValueError('finite latent[B,39] required')
        result = self(state, events, mask, priority_events, priority_mask)
        active = self._active_mask()
        result.update(logp=self.log_probability(result['mean'], result['log_std'], latent),
                      entropy=Normal(torch.zeros_like(result['mean'][..., active]),
                                     result['log_std'][..., active].exp()).entropy().sum(-1))
        return result
