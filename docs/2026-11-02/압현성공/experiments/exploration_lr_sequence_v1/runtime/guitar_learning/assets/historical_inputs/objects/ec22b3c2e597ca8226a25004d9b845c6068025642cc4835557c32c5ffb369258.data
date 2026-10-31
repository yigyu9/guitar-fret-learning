"""Read exterior plate arcs and body-depth dimensions from the original OM DXF."""
from pathlib import Path
import hashlib
import json
import sys
import ezdxf
import numpy as np
from scipy.optimize import minimize_scalar

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1'
OUT=ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_geometry_v1'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    paths=[SOURCE/'OM_acoustic_guitar.dxf',SOURCE/'outline_v2.json',Path(__file__).resolve(),ROOT/'stability_adapter_2/OM_BODY_GEOMETRY_PLAN_V1.md']
    paths += [Path(m.__file__) for n,m in sys.modules.items() if n.startswith('ezdxf') and getattr(m,'__file__',None)]
    before={str(p):sha(p) for p in paths};doc=ezdxf.readfile(paths[0]);assert doc.units==ezdxf.units.MM
    arcs={}
    for name,handle in [('front','2FCE'),('back','2EF2')]:
        e=doc.entitydb[handle];assert e.dxftype()=='ARC'
        arcs[name]={'handle':handle,'center_DXF_mm':list(e.dxf.center),'radius_mm':e.dxf.radius,'start_angle_deg':e.dxf.start_angle,'end_angle_deg':e.dxf.end_angle}
    ends={}
    for name,handle in [('tail','64'),('neck','63')]:
        e=doc.entitydb[handle];assert e.dxftype()=='LINE'
        a,b=np.asarray(e.dxf.start),np.asarray(e.dxf.end);assert abs(a[0]-b[0])<1e-9
        ends[name]={'handle':handle,'start_DXF_mm':a.tolist(),'end_DXF_mm':b.tolist(),'depth_mm':float(abs(a[1]-b[1]))}
    lo,hi=ends['tail']['start_DXF_mm'][0],ends['neck']['start_DXF_mm'][0]
    def depth(x):
        f,b=arcs['front'],arcs['back'];fc,bc=f['center_DXF_mm'],b['center_DXF_mm']
        top=fc[1]+np.sqrt(f['radius_mm']**2-(x-fc[0])**2)
        back=bc[1]-np.sqrt(b['radius_mm']**2-(x-bc[0])**2)
        return float(top-back)
    optimum=minimize_scalar(lambda x:-depth(x),bounds=(lo,hi),method='bounded')
    outline=json.loads(paths[1].read_text())
    notes={h:doc.entitydb[h].plain_text() for h in ['3134','3130','343A','343B','343C']}
    result={'passed':True,'source_units':'DXF millimetres','arcs':arcs,'end_sections':ends,'source_notes':notes,
        'side_axis_interval_mm':[lo,hi],'side_axis_length_mm':hi-lo,'plan_axis_length_mm':outline['body_length_m']*1000,
        'axis_length_difference_mm':outline['body_length_m']*1000-(hi-lo),
        'axis_mapping':'side_x_mm = tail_x + side_length * (body_y_m + plan_length_m/2) / plan_length_m; preserve plan XY, normalize side profile axis',
        'front_obscured_extension':'continue the same R7620 front arc beneath the fingerboard to the neck endpoint',
        'surface_rule':'spherical front/back surfaces use radius and center from longitudinal arcs; subtract body_x_mm squared inside each square root; transverse radii are also present in DXF',
        'transverse_front_arc_handles':['2DE0','2DE1','2DF7','2DFD'],'transverse_back_arc_handles':['2C35','2C3D','2C4D','2C5A'],
        'maximum_centerline_depth_mm':depth(optimum.x),'maximum_depth_side_x_mm':float(optimum.x),
        'depth_samples_mm':[[x,depth(x)] for x in [lo,100,200,275.5,400,500,hi]],'input_sha256':before,
        'scope':'outer envelope depth; wood-layer thickness and internal structures are excluded; 3D spherical continuation and normalized-axis alignment are documented reconstruction choices'}
    assert all(sha(p)==h for p,h in before.items())
    path=OUT/'depth_v1.json';assert not path.exists();path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'tail_mm':ends['tail']['depth_mm'],'neck_mm':ends['neck']['depth_mm'],'max_mm':result['maximum_centerline_depth_mm']}))


if __name__=='__main__':main()
