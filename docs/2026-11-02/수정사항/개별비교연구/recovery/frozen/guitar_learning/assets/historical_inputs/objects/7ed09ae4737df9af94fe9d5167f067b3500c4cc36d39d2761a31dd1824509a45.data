"""JSON/native tuple-list equivalence must not relax substantive contracts."""
import copy
import unittest
import torch
from guitar_learning.imitation import save_initialization
from guitar_learning.imitation_v2 import apply_actor_initialization, canonical_contract
from guitar_learning.tests import test_imitation as fixtures


class ImitationContractV2Tests(unittest.TestCase):
    setUp = fixtures.ImitationTests.setUp
    tearDown = fixtures.ImitationTests.tearDown
    capture = fixtures.ImitationTests.capture
    model = fixtures.ImitationTests.model
    snapshot = fixtures.ImitationTests.snapshot
    assert_unchanged = fixtures.ImitationTests.assert_unchanged

    def initialization(self):
        data = self.capture()
        source, target = self.model(), self.model()
        source.architecture['contract']['action']['limits'] = [[-.25, .25], [-.5, .5]]
        target.architecture['contract']['action']['limits'] = ((-.25, .25), (-.5, .5))
        source.architecture['contract']['termination']['axes'] = ['a', 'b']
        target.architecture['contract']['termination']['axes'] = ('a', 'b')
        with torch.no_grad():
            source.actor_heads['left'].bias.fill_(.25)
            source.log_std[:33].fill_(-2.)
            target.log_std.fill_(-4.)
        path = self.out/'initialization.pt'
        save_initialization(source, path, dataset_manifest=data['manifest'], fit_result=dict(steps=100))
        return source, target, path

    def test_tuple_list_contract_equivalence_copies_only_active_actor_without_metadata_mutation(self):
        source, target, path = self.initialization()
        metadata = copy.deepcopy(target.architecture)
        before = self.snapshot(target)
        result = apply_actor_initialization(target, path)
        self.assertEqual(target.architecture, metadata)
        self.assertIsInstance(target.architecture['contract']['action']['limits'], tuple)
        self.assertIsInstance(target.architecture['contract']['termination']['axes'], tuple)
        for key, value in target.state_dict().items():
            if key.startswith(('actor_encoders.left.', 'actor_heads.left.')):
                self.assertTrue(torch.equal(value, source.state_dict()[key]), key)
            elif key != 'log_std':
                self.assertTrue(torch.equal(value, before[key]), key)
        self.assertTrue(torch.equal(target.log_std[:33], source.log_std[:33]))
        self.assertTrue(torch.equal(target.log_std[33:], before['log_std'][33:]))
        self.assertNotIn('updates', result)

    def test_value_range_size_and_role_changes_rejected_before_mutation(self):
        source, target, path = self.initialization()
        payload = torch.load(path, map_location='cpu', weights_only=False)
        candidates = []
        changed = copy.deepcopy(payload); changed['architecture']['contract']['action']['limits'][0][1] = .3; candidates.append(changed)
        changed = copy.deepcopy(payload); changed['architecture']['size'] = 'medium'; candidates.append(changed)
        changed = copy.deepcopy(payload); changed['architecture']['contract']['task']['specialist']['skill'] = 'contact'; candidates.append(changed)
        changed = copy.deepcopy(payload); changed['role'] = 'right'; candidates.append(changed)
        changed = copy.deepcopy(payload); changed['architecture']['roles'] = list(changed['architecture']['roles']); candidates.append(changed)
        changed = copy.deepcopy(payload); changed['model']['cost_critic.weight'].fill_(float('nan')); candidates.append(changed)
        before, metadata = self.snapshot(target), copy.deepcopy(target.architecture)
        for index, candidate in enumerate(candidates):
            bad = self.out/('bad%d.pt'%index); torch.save(candidate, bad)
            with self.subTest(index=index), self.assertRaises(ValueError):
                apply_actor_initialization(target, bad)
            self.assert_unchanged(target, before)
            self.assertEqual(target.architecture, metadata)

    def test_nonfinite_or_nonstring_key_contracts_rejected(self):
        self.assertEqual(canonical_contract(dict(a=(1., 2.))), dict(a=[1., 2.]))
        for value in (dict(a=float('nan')), dict(a=float('inf')), {1: 'not a JSON field name'}):
            with self.assertRaises(ValueError): canonical_contract(value)


if __name__ == '__main__': unittest.main()
