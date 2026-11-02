"""CPU 정책 비교로 최초 bias 한 축만 바뀌며 학습·저장 의미가 유지됨을 검사한다."""
import copy
import importlib.util
import io
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('initial_cap_runtime_test',HERE/'runtime.py')
runtime=importlib.util.module_from_spec(spec);spec.loader.exec_module(runtime)
torch=runtime.torch
torch.set_num_threads(1)


def contract(settings):
    from guitar_learning.training.policy import ACTIVE_NAMES,FINGERS,SKILL_FIELDS,WRIST_TERMINATION_FIELDS
    fields=[]
    def add(names):
        for name in names:
            if name not in fields:fields.append(name)
    for finger in FINGERS:
        joints=['LH:'+finger+suffix for suffix in ('1_x','1_z','2','3')]
        add([block+'.'+joint for block in ('q_offset','q_velocity','target_error') for joint in joints])
        add(['finger_posture.'+finger+'.'+joint+'.'+trig for joint in ('MCP','PIP','DIP') for trig in ('sin','cos')])
        add(['finger_posture.'+finger+'.'+name for name in ('valid','standby_gate')])
    add([block+'.'+joint for block in ('q_offset','q_velocity','target_error','previous_action') for joint in ACTIVE_NAMES[:17]])
    tail=list(SKILL_FIELDS+WRIST_TERMINATION_FIELDS)
    fields += ['unused_test_field_'+str(i) for i in range(557-len(tail)-len(fields))]
    fields += tail
    fields += runtime.parent.natural.EXTRA_FIELDS
    return dict(schema='guitar_learning.training.v1',natural_press=settings['natural_press'],transition=settings['transition'],
        observation=dict(fields=fields,dimension=len(fields),scales=[1.]*len(fields),priority_slots=8,
            finger_targets=dict(schema='guitar_learning.left_finger_targets.v1',slots=[f+'_'+k for f in FINGERS for k in ('tracking','next')])),
        action=dict(names=list(ACTIVE_NAMES)),task=dict(finger_skill=dict(schema='guitar_learning.finger_skill.v3',phase='J',exploration='independent',hold_ticks=1)),
        reward={},termination={},native_backend=dict(pipeline='gpu'))


def make_policy(cls,settings,seed=7):
    torch.manual_seed(seed)
    return cls(557+runtime.parent.natural.EXTRA_DIM,size='large',contract=contract(settings),
        natural_press=settings['natural_press'],transition=settings['transition'])


def inputs():
    return (torch.zeros(1,557+runtime.parent.natural.EXTRA_DIM),torch.zeros(1,1,24),torch.ones(1,1,dtype=torch.bool),
            torch.zeros(1,8,24),torch.ones(1,8,dtype=torch.bool))


class InitialBiasTests(unittest.TestCase):
    def setUp(self):self.settings=runtime.build_settings(updates=19)

    def test_one_parameter_element_changes_same_seed(self):
        for seed in (7,17):
            old=make_policy(runtime.OriginalPolicy,self.settings,seed)
            new=make_policy(runtime.TransitionPolicy,self.settings,seed)
            changed={name:(a!=new.state_dict()[name]).nonzero().tolist() for name,a in old.state_dict().items() if not torch.equal(a,new.state_dict()[name])}
            self.assertEqual(changed,{'core.support_head.bias':[[1]]})
            self.assertEqual(runtime.parent.natural.ACTIVE_NAMES[1],'L_Thorax_y')
            self.assertAlmostEqual(float(new.core.support_head.bias[1]),math.atanh(.9),places=6)
            self.assertTrue(torch.equal(old.finger_log_std,new.finger_log_std))
            self.assertTrue(torch.equal(old.support_log_std,new.support_log_std))

    def test_initial_action_angle_and_full_unrestricted_range(self):
        old=make_policy(runtime.OriginalPolicy,self.settings)
        new=make_policy(runtime.TransitionPolicy,self.settings)
        with torch.no_grad():
            old_action=old.act(*inputs(),deterministic=True)['action'][0]
            new_action=new.act(*inputs(),deterministic=True)['action'][0]
        self.assertEqual((old_action!=new_action).nonzero().tolist(),[[1]])
        self.assertAlmostEqual(float(new_action[1]),.9,places=6)
        catalog,_=runtime.parent.natural.catalog_goal(self.settings['natural_press'])
        ref=torch.tensor(catalog['reference105'])[torch.tensor(catalog['action_indices'])]
        lower=torch.tensor(catalog['action_lower']);upper=torch.tensor(catalog['action_upper'])
        decode=lambda a:ref+torch.where(a>=0,upper-ref,ref-lower)*a
        delta=float((decode(new_action)[1]-decode(old_action)[1])*180/math.pi)
        self.assertAlmostEqual(delta,-.1,delta=.015)
        # 학습으로 평균을 바꾸면 .9를 넘어 양쪽 전체 범위를 계속 요청할 수 있다.
        for bias,expected in ((8.,1.),(-8.,-1.)):
            with torch.no_grad():new.core.support_head.bias[1]=bias
            actual=new.act(*inputs(),deterministic=True)['action'][0,1]
            self.assertAlmostEqual(float(actual),expected,places=5)
        self.assertEqual(runtime.TransitionPolicy.forward,runtime.OriginalPolicy.forward)

    def test_load_preserves_learned_weights_without_reinitialization(self):
        learned=make_policy(runtime.TransitionPolicy,self.settings)
        with torch.no_grad():learned.core.support_head.bias[1]=4.
        stream=io.BytesIO();torch.save(learned.state_dict(),stream);stream.seek(0)
        restored=make_policy(runtime.TransitionPolicy,self.settings,seed=17)
        restored.load_state_dict(torch.load(stream,map_location='cpu',weights_only=False))
        self.assertEqual(float(restored.core.support_head.bias[1]),4.)
        self.assertTrue(all(torch.equal(v,restored.state_dict()[k]) for k,v in learned.state_dict().items()))
        self.assertEqual(runtime.TransitionPolicy.load_state_dict,runtime.OriginalPolicy.load_state_dict)

    def test_settings_only_initialization_contract_added(self):
        old=runtime._original_build('b_only',updates=19)
        settings=copy.deepcopy(self.settings);settings.pop('policy_initialization')
        self.assertEqual(settings,old)
        new=make_policy(runtime.TransitionPolicy,self.settings)
        self.assertEqual(new.architecture['policy_initialization'],self.settings['policy_initialization'])
        self.assertNotEqual(new.architecture['schema'],runtime.OriginalPolicy.schema)

    def test_old_checkpoint_or_changed_contract_rejected(self):
        with self.assertRaises(ValueError):runtime.validate(runtime._original_build('b_only'))
        wrong=copy.deepcopy(self.settings);wrong['policy_initialization']['normalized_limit']=.95
        with self.assertRaises(ValueError):runtime.validate(wrong)
        for condition in ('gap150','gap100','gap075'):
            with self.assertRaises(ValueError):runtime.build_settings(condition)
        with self.assertRaises(ValueError):runtime.build_settings(thumb_active=True)

    def test_checkpoint_metadata_keeps_initialization_and_parent_contract(self):
        from guitar_learning.training import finger_skill_runner as runner
        with mock.patch.object(runner,'checkpoint_metadata',side_effect=lambda *a,**kw:kw):
            with runtime.transition_runtime(self.settings):
                metadata=runner.checkpoint_metadata()
        self.assertEqual(metadata['policy_initialization'],runtime.initialization_contract())
        self.assertEqual(metadata['transition'],self.settings['transition'])
        self.assertEqual(metadata['transition_runtime_sha256'],runtime.parent.natural.digest(runtime.PARENT_PATH))

    def test_parent_globals_restored_and_both_sources_pinned(self):
        from guitar_learning.training import finger_skill_runner as runner
        base=runtime.parent.BASE;policy=runtime.parent.TransitionPolicy;original_pins=runner._pins
        with tempfile.TemporaryDirectory(prefix='bias_cap_pins_',dir=runtime.ROOT/'.runtime/cache') as d:
            out=Path(d);(out/'settings.json').write_text(json.dumps(self.settings))
            with runtime.transition_runtime(self.settings):
                pins=runner._pins(self.settings,out)
                self.assertIs(runtime.parent.TransitionPolicy,runtime.TransitionPolicy)
                self.assertEqual(runtime.parent.BASE,base)
            for path in (HERE/'runtime.py',runtime.PARENT_PATH):
                self.assertEqual(pins[str(path.resolve())],runtime.parent.natural.digest(path))
        self.assertIs(runtime.parent.TransitionPolicy,policy)
        self.assertIs(runner._pins,original_pins)
        self.assertEqual(runtime.parent.BASE,base)


if __name__=='__main__':unittest.main()
