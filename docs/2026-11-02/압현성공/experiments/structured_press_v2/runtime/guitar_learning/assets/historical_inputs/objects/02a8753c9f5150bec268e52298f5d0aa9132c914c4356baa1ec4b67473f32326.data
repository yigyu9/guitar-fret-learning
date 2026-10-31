import unittest

# Load Gym before MuJoCo to avoid shared-library symbol conflicts in discovery.
import isaacgym  # noqa: F401
from stability_adapter_2.initial_overlap import query_pairs, query_ground, mujoco


class StaticDistanceTests(unittest.TestCase):
    def test_ground_plane_gap_has_analytic_box_sign_and_units(self):
        for z,expected in ((.51,.01),(.5,0.),(.49,-.01)):
            model = mujoco.MjModel.from_xml_string(f'<mujoco><worldbody><geom type="plane" size="1 1 .1"/><geom type="box" size=".5 .5 .5" pos="0 0 {z}"/></worldbody></mujoco>')
            data = mujoco.MjData(model)
            mujoco.mj_forward(model,data)
            result = query_ground(model,data,[{'actor':'ground','geom_id':0},
                {'actor':'human','body':'box','geom_id':1}])
            self.assertAlmostEqual(result['minimum_gap_m'],expected,places=7)
            self.assertEqual(result['negative_gap_pair_count'],int(expected<0))

    def test_separation_contact_overlap_and_cutoff(self):
        shapes = [{'actor':'human', 'body':'human_box', 'geom_id':0},
                  {'actor':'guitar', 'body':'guitar_box', 'geom_id':1}]
        # MuJoCo 3.2.3 returns -0.05 for boxes with analytic overlap 0.1m.
        # Verify its sign/output without mislabeling that value as physical depth.
        for x, expected in [(2.01, .01), (2., 0.), (1.9, -.05), (3., None)]:
            xml = f'<mujoco><worldbody><geom type="box" size="1 1 1"/><geom type="box" size="1 1 1" pos="{x} 0 0"/></worldbody></mujoco>'
            model = mujoco.MjModel.from_xml_string(xml)
            data = mujoco.MjData(model)
            mujoco.mj_forward(model, data)
            result = query_pairs(model, data, shapes)
            if expected is None:
                self.assertEqual(result['pairs_within_limit'], [])
            else:
                self.assertAlmostEqual(result['pairs_within_limit'][0]['signed_gap_m'], expected, places=6)
                self.assertEqual(result['negative_gap_pair_count'], int(expected < 0))


if __name__ == '__main__':
    unittest.main()
