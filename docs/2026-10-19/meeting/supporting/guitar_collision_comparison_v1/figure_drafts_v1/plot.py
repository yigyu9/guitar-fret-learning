"""Scientific figure from paired native camera pixels, segmentation and depth."""
from pathlib import Path
import json
import hashlib
import numpy as np
from scipy.ndimage import binary_erosion, binary_dilation
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Patch
from PIL import Image

HERE = Path(__file__).resolve().parent
MEETING = HERE.parent.parent
RAW = MEETING/'result/images/guitar_collision_comparison_v1'
REPORT = json.loads((HERE/'capture.json').read_text())
A = np.load(HERE/'native_arrays.npz')
FONT = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
if not Path(FONT).exists():
    FONT = '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
plt.rcParams['font.family'] = FontProperties(fname=FONT).get_name()
plt.rcParams['axes.unicode_minus'] = False
EXCLUDED = [REPORT['shape_properties'][name]['segmentation_id']
            for name in REPORT['excluded_runtime_bodies']]
BODY_ID = REPORT['body_id']
MAGENTA = np.array([1.,.32,.72])
CYAN = np.array([.2,.88,1.])
stats = {}

def mask(view,kind,body=False):
    seg = A[view+'_'+kind+'_seg']
    return seg==BODY_ID if body else (seg>0)&~np.isin(seg,EXCLUDED)

def overlay(view):
    v,c = mask(view,'visual'),mask(view,'collision')
    rgb = np.full((*v.shape,3),.045)
    rgb[v&c] = [.4,.4,.4]
    rgb[v&~c] = MAGENTA
    rgb[c&~v] = CYAN
    # Fixed-width contour aid, not a physical thickness or enlarged geometry.
    v_edge = v&~binary_erosion(v)
    c_edge = c&~binary_erosion(c)
    rgb[binary_dilation(v_edge,iterations=1)] = MAGENTA
    rgb[binary_dilation(c_edge,iterations=1)] = CYAN
    return rgb

for view in ['whole_front','body_front','body_side']:
    common = binary_erosion(mask(view,'visual',True)&mask(view,'collision',True),iterations=3)
    d = np.zeros(common.shape,dtype=np.float32)
    # Native depths are negative; positive means collision is closer to camera.
    d[common] = (A[view+'_visual_depth'][common]-A[view+'_collision_depth'][common])*1000
    assert np.isfinite(d[common]).all()
    absolute = abs(d[common])
    stats[view] = {'shared_body_interior_pixels':int(common.sum()),
       'erosion_pixels':3,'absolute_depth_mm_median':float(np.median(absolute)),
       'absolute_depth_mm_p95':float(np.percentile(absolute,95)),
       'absolute_depth_mm_p99':float(np.percentile(absolute,99)),
       'absolute_depth_mm_max':float(absolute.max()),
       'signed_depth_mm_min':float(d[common].min()),'signed_depth_mm_max':float(d[common].max()),
       'scope':'Camera-axis depth difference on shared body pixels; not normal clearance, penetration, or 3D Hausdorff error'}

fig,axes = plt.subplots(2,4,figsize=(17,10),dpi=150)
fig.subplots_adjust(left=.025,right=.975,bottom=.15,top=.87,wspace=.05,hspace=.15)
for row,(view,label) in enumerate([('body_front','바디 정면 확대'),('body_side','바디 오른쪽 옆면 확대')]):
    for col,kind in enumerate(['visual','collision']):
        axes[row,col].imshow(Image.open(RAW/(view+'_'+kind+'.png')))
    axes[row,2].imshow(overlay(view))
    common = binary_erosion(mask(view,'visual',True)&mask(view,'collision',True),iterations=3)
    d = np.full(common.shape,np.nan)
    d[common]=(A[view+'_visual_depth'][common]-A[view+'_collision_depth'][common])*1000
    cmap=plt.get_cmap('coolwarm').copy();cmap.set_bad('#eeeeee')
    heat=axes[row,3].imshow(d,cmap=cmap,vmin=-.8,vmax=.8)
    axes[row,0].text(0,1.02,label,transform=axes[row,0].transAxes,fontsize=11)
    for ax in axes[row]:ax.set_axis_off()
    axes[row,3].text(.5,-.045,'공통 바디 |깊이 차이| 95%% ≤ %.3f mm'%stats[view]['absolute_depth_mm_p95'],
                      ha='center',transform=axes[row,3].transAxes,fontsize=10)
for ax,title in zip(axes[0],['보이는 시각 형상','native 충돌 형상 표시','같은 화면의 외곽선 겹침','카메라 깊이 차이 [mm]']):
    ax.set_title(title,fontsize=12,pad=30)
fig.suptitle('현재 OM v3 기타 · 시각 메시와 충돌 형상 비교',fontsize=18,y=.98)
fig.text(.5,.925,'같은 actor · 같은 카메라 · 배율 1 · 물리 진행 0 step',ha='center',fontsize=11)
fig.legend(handles=[Patch(color=MAGENTA,label='분홍: 시각 형상'),Patch(color=CYAN,label='청록: 충돌 형상'),
                    Patch(color='.4',label='회색: 겹치는 영역')],loc='lower center',bbox_to_anchor=(.41,.08),ncol=3,frameon=False)
bar=fig.colorbar(heat,cax=fig.add_axes([.79,.095,.16,.016]),orientation='horizontal',extend='both')
bar.set_label('양수: 충돌 표면이 카메라 쪽 / ±0.8 mm 바깥 색 포화',fontsize=8);bar.ax.tick_params(labelsize=8)
fig.text(.025,.055,'겹침 그림은 runtime 비활성 proxy/pluck 형상을 제외. 원본 충돌 카메라에는 이 보조 형상이 보일 수 있음.',fontsize=10)
fig.text(.025,.03,'윤곽선의 표시 두께는 실제 간격이 아님. 깊이 차이는 공통 바디 픽셀만 계산하며 접촉 offset·접촉력·3D 최단거리를 뜻하지 않음.',fontsize=9)
main=MEETING/'result/guitar_visual_vs_collision.png'
assert not main.exists();fig.savefig(main,facecolor='white');plt.close(fig)

fig,axes=plt.subplots(1,3,figsize=(14,6),dpi=150)
for ax,kind,title in zip(axes[:2],['visual','collision'],['시각 형상 · native','충돌 형상 표시 · native']):
    ax.imshow(Image.open(RAW/('whole_front_'+kind+'.png')));ax.set_title(title,fontsize=12)
axes[2].imshow(overlay('whole_front'));axes[2].set_title('분홍: 시각 / 청록: 충돌',fontsize=12)
for ax in axes:ax.set_axis_off()
fig.suptitle('OM v3 기타 전체 · 같은 모델과 카메라',fontsize=17)
fig.text(.5,.055,'충돌 카메라에는 비활성 보조 형상도 표시됨. 오른쪽 겹침에서는 해당 proxy/pluck 형상을 제외.',ha='center',fontsize=10)
fig.text(.5,.025,'명암·재질 차이와 형상 차이를 구분할 것. native 시각 로더의 프렛/현 표시 제한은 별도 문서에 기록.',ha='center',fontsize=9)
fig.subplots_adjust(left=.02,right=.98,top=.88,bottom=.12,wspace=.04)
whole=RAW/'whole_guitar_comparison.png'
assert not whole.exists();fig.savefig(whole,facecolor='white');plt.close(fig)
source=json.loads(Path(REPORT['asset']).with_name('manifest.json').read_text())
stats['source_XY_max_error_mm']=max(max(e['XY_inside_error_m'],e['XY_outside_error_m']) for e in source['collision_XY_error_checks'])*1000
stats['notes']=['Masks/depths from actual native cameras, no source mesh rasterizer.',
 'Boundary/tangent pixels can have large axial depth differences, especially from the side; not surface-normal gaps.',
 'Three-pixel common-mask erosion reduces edge artifacts but does not remove all grazing angles.',
 'Collision camera represents imported geometry, not a contact-offset inflated envelope.',
 'Raw native visual importer emitted six visual geom errors; color/brightness and missing visual frets/strings do not prove a hull gap.']
(HERE/'analysis.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(stats,ensure_ascii=False,indent=2))
