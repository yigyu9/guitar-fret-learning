import unittest
import torch
torch.set_num_threads(1)
from guitar_learning.training.policy import Policy


def policy():
    return Policy(5,24,'small',contract={'schema':'guitar_learning.training.v1', 'observation':{'dimension':5}, 'action':{'dimension':39}, 'task':{'source':'synthetic_cpu_test'}, 'reward':{}, 'termination':{}})


class PolicyTests(unittest.TestCase):
    def test_architecture_sizes_and_required_contract(self):
        contract=policy().architecture['contract']
        counts=[]
        for size in ('small','medium','large'):
            model=Policy(450,24,size,contract=contract)
            counts.append(sum(p.numel() for p in model.parameters()))
            self.assertEqual(model.architecture['state_layers'],(256,256))
        self.assertTrue(counts[0] < counts[1] < counts[2])
        self.assertTrue(1_500_000 < counts[1] < 3_000_000)
        with self.assertRaises(ValueError): Policy(5,contract={'schema':'invalid'})

    def test_39_and_zero_initial_mean(self):
        model=policy()
        result=model.act(torch.randn(2,5),torch.randn(2,4,24),torch.ones(2,4,dtype=torch.bool),torch.zeros(2,2,24),torch.ones(2,2,dtype=torch.bool),True)
        self.assertEqual(result['action'].shape,(2,39))
        self.assertTrue(torch.equal(result['action'],torch.zeros(2,39)))
        self.assertEqual(model.role_sizes,(33,6))
        self.assertTrue(torch.equal(model.log_std,torch.full((39,),-3.)))

    def test_padding_invariance_including_nan_and_all_masked(self):
        model=policy()
        state=torch.randn(2,5)
        events=torch.randn(2,2,24)
        mask=torch.ones(2,2,dtype=torch.bool)
        priority=torch.randn(2,2,24)
        priority_mask=torch.ones(2,2,dtype=torch.bool)
        expected=model(state,events,mask,priority,priority_mask)
        padded=torch.cat((events,torch.full((2,3,24),float('nan'))),1)
        padded_mask=torch.cat((mask,torch.zeros(2,3,dtype=torch.bool)),1)
        actual=model(state,padded,padded_mask,priority,priority_mask)
        for key in expected:
            self.assertTrue(torch.allclose(expected[key],actual[key],atol=1e-7),key)
        output=model(state,padded,torch.zeros(2,5,dtype=torch.bool),priority,priority_mask)
        self.assertTrue(all(torch.isfinite(value).all() for value in output.values()))
        with self.assertRaises(ValueError):
            model(state,padded,torch.ones(2,5,dtype=torch.bool),priority,priority_mask)

    def test_value_optimizer_cannot_change_actor(self):
        model=policy()
        before=[p.detach().clone() for p in model.actor_parameters()]
        optimizer=torch.optim.Adam(model.value_parameters(),lr=.01)
        result=model(torch.randn(4,5),torch.randn(4,2,24),torch.ones(4,2,dtype=torch.bool),torch.zeros(4,2,24),torch.ones(4,2,dtype=torch.bool))
        (result['reward_value'].square().mean()+result['cost_value'].square().mean()).backward()
        optimizer.step()
        for parameter,old in zip(model.actor_parameters(),before):
            self.assertTrue(torch.equal(parameter,old))


if __name__=='__main__':
    unittest.main()
