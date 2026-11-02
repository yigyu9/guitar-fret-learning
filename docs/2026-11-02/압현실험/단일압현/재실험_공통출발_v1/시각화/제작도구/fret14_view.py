"""현재 기타의 실제 충돌 형상과 프렛 마커를 정면 투영해 범위를 표시한다."""
import importlib.util
import json
from pathlib import Path
import sys
import numpy as np
from scipy.spatial import ConvexHull
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Patch
from matplotlib.font_manager import FontProperties

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
ROOT=next(p for p in HERE.parents if (p/'guitar_learning/train.py').exists())
spec=importlib.util.spec_from_file_location('range_shapes',BASE/'tools/fret_access_range.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
shapes,pins=m.load_shapes()
manifest=json.loads((ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json').read_text())
pins[str(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json')]=m.sha(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json')
bodies=dict(zip(manifest['logical_body_names'],manifest['logical_position_root_m']))
y=np.array([bodies['G:nut'][1]]+[bodies['G:fret%d'%i][1] for i in range(1,23)])
font=FontProperties(fname='/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
plt.rcParams.update({'font.family':font.get_name(),'axes.unicode_minus':False,'font.size':12})
fig,(a,z)=plt.subplots(2,1,figsize=(16,8),gridspec_kw={'height_ratios':[1.1,1]},layout='constrained')
colors=['#2cbd96' if i<=14 else '#ffc44d' if i<=16 else '#ef8b88' for i in range(1,23)]
for ax in (a,z):
 for s in sorted(shapes,key=lambda s:s['category']!='body'):
  if s['category']=='fret_or_nut':continue
  v=s['vertices'];p=np.column_stack((-v[:,1],v[:,0]))*1000
  h=ConvexHull(p);c={'body':'#b9a18b','neck':'#665d58','headstock':'#887768'}[s['category']]
  ax.add_patch(Polygon(p[h.vertices],facecolor=c,edgecolor='#544c46',linewidth=.35,zorder=1))
 for i in range(1,23):
  x0,x1=-y[i-1]*1000,-y[i]*1000
  ax.add_patch(Polygon([(x0,-26),(x1,-26),(x1,26),(x0,26)],facecolor=colors[i-1],alpha=.88,edgecolor='none',zorder=3))
  ax.plot([-y[i]*1000]*2,[-26,26],color='white',lw=1,zorder=5)
  if (ax is a and i in (1,3,5,7,9,12,14,16,19,22)) or (ax is z and i>=10):
   ax.text((x0+x1)/2,36,str(i),ha='center',va='bottom',fontsize=10 if ax is a else 12,fontweight='bold' if i==14 else 'normal',zorder=6,clip_on=True)
 for i in range(1,7):
  s=np.array(bodies['G:string%d'%i]);e=np.array(bodies['G:string%d_end'%i])
  ax.plot([-s[1]*1000,-e[1]*1000],[s[0]*1000,e[0]*1000],color='#eeeeeb',lw=.7,zorder=4)
 ax.axvline(-y[14]*1000,color='#087f60',lw=3,ls='--',zorder=7)
 ax.set_aspect('equal');ax.axis('off')
allv=np.concatenate([s['vertices'] for s in shapes]);a.set_xlim(-allv[:,1].max()*1000-25,-allv[:,1].min()*1000+25);a.set_ylim(-235,235)
a.set_title('현재 기타 모델 정면도 · 14프렛까지의 범위',fontsize=21,fontweight='bold',pad=15)
a.text(-y[0]*1000,75,'너트 · 1프렛 시작',ha='center',fontsize=12)
a.annotate('14프렛 끝 경계',xy=(-y[14]*1000,27),xytext=(-y[14]*1000-20,145),ha='center',fontsize=14,color='#087f60',fontweight='bold',arrowprops={'arrowstyle':'->','color':'#087f60','lw':2})
z.set_xlim(-y[9]*1000-10,-y[22]*1000+20);z.set_ylim(-65,110)
z.set_title('넥 안쪽 확대 · 숫자는 누르는 칸(프렛 셀)의 번호',fontsize=16,loc='left')
z.annotate('이 선까지가 1~14프렛',xy=(-y[14]*1000,-27),xytext=(-y[14]*1000-40,-58),ha='center',color='#087f60',fontsize=13,fontweight='bold',arrowprops={'arrowstyle':'->','color':'#087f60'})
fig.legend(handles=[Patch(color='#2cbd96',label='1~14: 학습 후보'),Patch(color='#ffc44d',label='15~16: 경계 검증'),Patch(color='#ef8b88',label='17~22: 학습 보류')],loc='outside lower center',ncol=3,frameon=False,fontsize=13)
fig.suptitle('실제 실행 자산의 형상·프렛 위치를 투영한 도식 (손가락 도달성 인증 아님)',fontsize=11,color='#555555')
out=HERE.parent/'기타_14프렛_범위.png';fig.savefig(out,dpi=160,facecolor='white');plt.close(fig)
(HERE.parent/'기타_14프렛_범위_근거.json').write_text(json.dumps({'coordinate':'top projection: horizontal=-G_y, vertical=G_x; mm','fret14_boundary_G_y_m':float(y[14]),'fret14_cell_G_y_m':[float(y[13]),float(y[14])],'source_sha256':pins,'manifest':str(ROOT/'guitar_learning/assets/gpu_rigid_guitar_v1/manifest.json')},ensure_ascii=False,indent=2)+'\n')
print(out)
