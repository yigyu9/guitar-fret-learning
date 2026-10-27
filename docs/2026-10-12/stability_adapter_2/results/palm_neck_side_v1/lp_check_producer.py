import isaacgym
import json
import trimesh
import numpy as np
from stability_adapter_2.palm_side_source_checks import intersection
from stability_adapter_2.thigh_palm_support import intersection as old_intersection

def box(center, size):
 m=trimesh.creation.box(extents=[size]*3);m.apply_translation(center);return m
rows=[]
for center in ((0,0,0),(1000,-3000,4000)):
 for dx,expected in ((0,.001),(.001,.0005),(.002,0),(.00201,0),(.00199,.000005)):
  a=box(center,.002);b=box(np.array(center)+[dx,0,0],.002)
  measured=intersection(a,b)
  assert abs(measured-expected)<2e-9,(center,dx,expected,measured)
  rows.append({'center_m':center,'offset_m':dx,'expected_radius_m':expected,'measured_radius_m':measured})
for dx in (0,.001,.0015):
 a=box([-.1,.2,.7],.002);b=box([-.1+dx,.2,.7],.002)
 assert abs(intersection(a,b)-old_intersection(a,b))<1e-9
print(json.dumps({'checks':{'known_box_overlap_disjoint_touch_near_contact':True,'large_translation_invariance':True,'matches_previous_well_conditioned_lp':True},'rows':rows},indent=2))
