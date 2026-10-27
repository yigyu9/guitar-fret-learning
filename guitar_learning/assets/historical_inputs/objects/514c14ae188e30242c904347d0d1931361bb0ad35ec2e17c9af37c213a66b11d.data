"""Extract the OM plan's closed body rim and compare exterior outlines in metres."""
from pathlib import Path
import hashlib
import json
import sys
import ezdxf
from ezdxf.path import make_path
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'docs/2026-10-12/stability_adapter_2/results/om_body_outline_v1'
DXF = OUT/'OM_acoustic_guitar.dxf'
CURRENT = ROOT/'stability_adapter_2/assets/acoustic_appearance_v3/visual_body.obj'
HANDLES = ['AE','AF','B0','7BC','B1','B2','B3','B4','2F6','2F5','2F4','2F3','2F2','2F1','2F0','2EF']
FONT = Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    dependencies = [Path(module.__file__) for name,module in sys.modules.items()
                    if name.startswith('ezdxf') and getattr(module,'__file__',None)]
    paths = [DXF, CURRENT, FONT, Path(__file__).resolve(),
             ROOT/'stability_adapter_2/OM_BODY_OUTLINE_PLAN_V1.md', OUT/'download.json'] + dependencies
    before = {str(p):sha(p) for p in paths}
    doc = ezdxf.readfile(DXF)
    assert doc.units == ezdxf.units.MM
    parts, gaps, entities = [], [], []
    for handle in HANDLES:
        entity = doc.entitydb[handle]
        assert entity.dxftype() == 'SPLINE' and entity.dxf.layer == '0'
        points = np.asarray(list(make_path(entity).flattening(.02)))[:,:2]
        if handle.startswith('2'):points = points[::-1]
        if parts:gaps.append(float(np.linalg.norm(parts[-1][-1]-points[0])))
        parts.append(points)
        entities.append({'handle':handle,'type':entity.dxftype(),'layer':entity.dxf.layer,
            'reversed':handle.startswith('2'),'control_points_DXF_mm':list(map(list,entity.control_points)),
            'degree':entity.dxf.degree,'knots':list(entity.knots),'sample_points_DXF_mm':points.tolist()})
    source = np.concatenate(parts)
    closure_gap = float(np.linalg.norm(source[-1]-source[0]))
    assert max(gaps)<1e-8 and closure_gap<.02
    lo,hi = source.min(0),source.max(0)
    center = (lo+hi)/2
    # DXF neck points toward +X. In the guitar frame it points toward +Y.
    contour = np.c_[(source[:,1]-center[1])/1000,(source[:,0]-center[0])/1000]
    contour = np.vstack([contour,contour[0]])
    signed_area = float(.5*np.sum(contour[:-1,0]*contour[1:,1]-contour[1:,0]*contour[:-1,1]))
    assert abs(signed_area)>.1 and np.isfinite(contour).all()
    vertices = np.array([[float(s) for s in line.split()[1:4]] for line in CURRENT.read_text().splitlines() if line.startswith('v ')])
    current = vertices[np.isclose(vertices[:,2],.0205,atol=1e-10),:2]
    # The front fan has one center vertex; the remaining vertices form its outline.
    current = current[np.linalg.norm(current,axis=1)>1e-9]
    current = np.vstack([current,current[0]])
    fp = FontProperties(fname=str(FONT))
    fig,ax = plt.subplots(figsize=(10.5,8.2))
    ax.plot(current[:,0]*100,current[:,1]*100,color='#969696',lw=2,ls='--',label='현재 바디 시각 윤곽')
    ax.plot(contour[:,0]*100,contour[:,1]*100,color='#222222',lw=2,label='OM 제작 도면 외곽')
    ax.set_aspect('equal');ax.set_xlim(-23,23);ax.set_ylim(-29,29);ax.grid(alpha=.2)
    ax.set_xlabel('바디 좌우 (cm)',fontproperties=fp);ax.set_ylabel('넥 방향 (cm)',fontproperties=fp)
    ax.set_title('바디 외곽만 비교 — 같은 cm 축척·바디 중심 정렬',fontproperties=fp,pad=16)
    ax.legend(prop=fp,loc='center left',bbox_to_anchor=(1.02,.5));fig.subplots_adjust(bottom=.19,right=.72)
    fig.text(.13,.07,'DXF 외곽 추출 그림입니다. Isaac Gym 렌더나 접촉 검증이 아닙니다.\n실물 도면 치수를 유지했고, 시뮬레이션 모델은 아직 변경하지 않았습니다.',fontproperties=fp,fontsize=10)
    image = OUT/'body_outline_comparison_v2.png';assert not image.exists();fig.savefig(image,dpi=160);plt.close(fig)
    assert all(sha(p)==value for p,value in before.items())
    result = {'passed':True,'units':'metres','source_units':'DXF millimetres','ezdxf_version':ezdxf.__version__,
        'source_view':'upper body plan rim around the bracing layout; only outer rim curves selected',
        'source_handle_order':HANDLES,'source_entities':entities,'flattening_distance_mm':.02,
        'max_join_gap_mm':max(gaps),'source_closure_gap_mm':closure_gap,
        'closure_rule':'append first point; only bridge the documented 0.016934mm tail seam',
        'DXF_bounds_mm':[lo.tolist(),hi.tolist()],'DXF_center_mm':center.tolist(),
        'body_length_m':float(hi[0]-lo[0])/1000,'body_width_m':float(hi[1]-lo[1])/1000,
        'current_visual_length_m':float(np.ptp(current,axis=0)[1]),'current_visual_width_m':float(np.ptp(current,axis=0)[0]),
        'area_m2':abs(signed_area),'outline_body_xy_m':contour.tolist(),
        'input_sha256':before,'output_image_sha256':sha(image),
        'native_runs':0,'asset_changes':0,'scope':'exterior outline extraction, not a product scan or physical/contact validation'}
    output = OUT/'outline_v2.json';assert not output.exists();output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('passed','body_length_m','body_width_m','current_visual_length_m','current_visual_width_m','source_closure_gap_mm')}))


if __name__ == '__main__':
    main()
