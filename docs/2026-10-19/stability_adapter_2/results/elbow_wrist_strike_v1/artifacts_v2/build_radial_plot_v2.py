#!/usr/bin/env python3
"""Plot only the saved radial-bound JSON fields; not a simulator renderer."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path

os.environ.setdefault('MPLCONFIGDIR','/tmp/elbow_wrist_strike_v1_mplconfig_v2')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties

ROOT=Path('/home/ajou/yigyu/3')
P=ROOT/'docs/2026-10-19/stability_adapter_2/results/elbow_wrist_strike_v1'
ART=P/'artifacts_v2'
SOURCE=P/'radial_bound_v1.json'
FONT=Path('/usr/share/fonts/truetype/nanum/NanumGothic.ttf')
SCRIPT=ART/'build_radial_plot_v2.py'
PIN=ART/'preflight_pin_v2.json'
OUTPUT=ART/'radial_reach_bound_v2.png'
PROVENANCE=ART/'provenance_v2.json'


def sha(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def main()->None:
    if OUTPUT.exists() or PROVENANCE.exists():
        raise FileExistsError('refusing to overwrite an existing plot or provenance')
    pin=json.loads(PIN.read_text(encoding='utf-8'))
    if pin.get('schema')!='elbow_wrist_radial_plot_preflight_v2':
        raise ValueError('unsupported preflight pin')
    if pin['producer']['path']!=str(SCRIPT):raise ValueError('preflight producer path mismatch')
    for item in pin['inputs']:
        p=Path(item['path'])
        if not p.is_file() or sha(p)!=item['sha256_before']:
            raise ValueError(f'input missing or differs from saved before pin: {p}')
    if sha(SCRIPT)!=pin['producer']['sha256_before']:
        raise ValueError('producer differs from saved before pin')

    data=json.loads(SOURCE.read_text(encoding='utf-8'))
    radius_mm=data['maximum_fixed_elbow_pick_radius_m']*1000.0
    times=sorted({row['time_s'] for row in data['rows']})
    if times!=[0.0,2.0,5.0]:raise ValueError(f'unexpected actual times: {times}')
    rows_by_time={t:sorted((row for row in data['rows'] if row['time_s']==t),key=lambda row:row['lane_G_y_m']) for t in times}
    lanes=[row['lane_G_y_m'] for row in rows_by_time[0.0]]
    if len(lanes)!=27 or any([row['lane_G_y_m'] for row in rows_by_time[t]]!=lanes for t in times):
        raise ValueError('expected 27 identical lane positions at actual t=0,2,5')
    for t in times:
        if any(len(row['distance_elbow_to_each_string_m'])!=6 or len(row['unavoidable_position_error_lower_bound_each_string_m'])!=6 for row in rows_by_time[t]):
            raise ValueError(f'expected six raw string values per lane at t={t}')
    colors=['#0072B2','#D55E00','#009E73','#CC79A7','#E69F00','#56B4E9']
    font=FontProperties(fname=str(FONT))
    plt.rcParams['axes.unicode_minus']=False
    fig,axes=plt.subplots(1,2,figsize=(15.5,8.4),constrained_layout=False)
    fig.subplots_adjust(left=.075,right=.985,top=.70,bottom=.24,wspace=.25)
    ax=axes[0]
    ax.axvspan(-.355,-.295,color='#7AAE8B',alpha=.20,label='선호 Y 구간 [-0.355, -0.295] m')
    ax.axvline(-.325,color='#555555',linestyle=':',linewidth=1.8,label='default lane -0.325 m')
    for i,color in enumerate(colors):
        ys=[row['lane_G_y_m'] for row in rows_by_time[0.0]]
        distances=[row['distance_elbow_to_each_string_m'][i]*1000.0 for row in rows_by_time[0.0]]
        ax.plot(ys,distances,color=color,linewidth=2.0,marker='o',markersize=2.8,label=f'줄 index {i+1} (JSON 배열 순서)')
    ax.axhline(radius_mm,color='#B22222',linestyle='--',linewidth=2.2,label=f'최대 고정 Elbow 반경 {radius_mm:.3f} mm')
    ax.set_title('① t=0 · Elbow→각 현 거리',fontproperties=font,fontsize=15,pad=12)
    ax.set_xlabel('기타 lane_G_y_m (m)',fontproperties=font,fontsize=12)
    ax.set_ylabel('Elbow-to-string 거리 (mm)',fontproperties=font,fontsize=12)
    ax.grid(True,color='#B8B8B8',linewidth=.7,alpha=.55)
    ax.legend(prop=font,fontsize=8.2,loc='lower center',bbox_to_anchor=(.5,1.025),framealpha=.94,ncol=3,borderaxespad=0.0)
    ax=axes[1]
    for t,color,marker in [(0.0,'#0072B2','o'),(2.0,'#D55E00','s'),(5.0,'#009E73','^')]:
        ys=[row['lane_G_y_m'] for row in rows_by_time[t]]
        max_error_mm=[max(row['unavoidable_position_error_lower_bound_each_string_m'])*1000.0 for row in rows_by_time[t]]
        ax.plot(ys,max_error_mm,color=color,linewidth=2.2,marker=marker,markersize=3.1,label=f't={t:g} s · 6현 중 최댓값')
    ax.axvspan(-.355,-.295,color='#7AAE8B',alpha=.20,label='선호 Y 구간 [-0.355, -0.295] m')
    ax.axvline(-.325,color='#555555',linestyle=':',linewidth=1.8,label='default lane -0.325 m')
    ax.set_title('② 저장 pose · 6현 중 radial 오차 하한 최댓값',fontproperties=font,fontsize=15,pad=12)
    ax.set_xlabel('기타 lane_G_y_m (m)',fontproperties=font,fontsize=12)
    ax.set_ylabel('필요 위치 오차 하한 (mm)',fontproperties=font,fontsize=12)
    ax.grid(True,color='#B8B8B8',linewidth=.7,alpha=.55)
    ax.legend(prop=font,fontsize=9,loc='lower center',bbox_to_anchor=(.5,1.025),framealpha=.94,ncol=3,borderaxespad=0.0)
    fig.suptitle('고정 Elbow + 기준 손가락 준비 자세의 6현 radial reach bound',fontproperties=font,fontsize=18,y=.97)
    fig.text(.5,.115,'저장된 native pose의 기하학적 분석 그래프, 시뮬레이션 렌더/타현 성공 아님',ha='center',fontproperties=font,fontsize=13,color='#8B1A1A')
    fig.text(.5,.065,'반경 안쪽도 관절 한계·충돌·타현 성공을 보장하지 않음 · 거리/위치오차는 원 JSON 실제 field(m)를 mm로 변환',ha='center',fontproperties=font,fontsize=10.5,color='#333333')
    if OUTPUT.exists():raise FileExistsError(OUTPUT)
    fig.savefig(OUTPUT,dpi=180,format='png',facecolor='white')
    plt.close(fig)

    input_after={item['path']:sha(Path(item['path'])) for item in pin['inputs']}
    changed=[item['path'] for item in pin['inputs'] if input_after[item['path']]!=item['sha256_before']]
    producer_after=sha(SCRIPT)
    if changed or producer_after!=pin['producer']['sha256_before']:
        raise RuntimeError(f'input/producer changed during plot generation: {changed}')
    record={
      'schema':'elbow_wrist_radial_plot_provenance_v2',
      'method':'V2 presentation-only legend placement change; plot actual rows/arrays from radial_bound_v1.json; meters-to-millimeters unit conversion only; no interpolation, pose synthesis, native render, or simulation claim',
      'figure':{'path':str(OUTPUT),'sha256':sha(OUTPUT),'bytes':OUTPUT.stat().st_size,'dpi':180,'panels':2,'data_rows':len(data['rows']),'lanes_per_time':len(lanes),'times_s':times,'strings_per_lane':6,'maximum_fixed_elbow_pick_radius_m':data['maximum_fixed_elbow_pick_radius_m'],'preferred_lane_y_m':[-0.355,-0.295],'default_lane_y_m':-0.325,'legend_placement':'outside each plot axis, above panel'},
      'inputs':[{'path':item['path'],'sha256_before':item['sha256_before'],'sha256_after':input_after[item['path']],'unchanged':input_after[item['path']]==item['sha256_before']} for item in pin['inputs']],
      'producer':{'path':str(SCRIPT),'sha256_before':pin['producer']['sha256_before'],'sha256_after':producer_after,'unchanged':producer_after==pin['producer']['sha256_before']},
      'scope':data['scope'],
    }
    if PROVENANCE.exists():raise FileExistsError(PROVENANCE)
    with PROVENANCE.open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2);f.write('\n')

if __name__=='__main__':main()
