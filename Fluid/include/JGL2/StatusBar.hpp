//
//  StatusBar.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_StatusBar_h
#define JGL2_StatusBar_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Aligner.hpp>

namespace JGL2 {

struct StatusBar : public Aligner {
	StatusBar(float x,float y,float w,float h,const str_t& name="StatusBar");
	StatusBar(float x,float y,float w,const str_t& name="StatusBar");
	StatusBar(const pos_t& pos,const sz2_t& sz,const str_t& name="StatusBar");
	StatusBar(const pos_t& pos,float w,const str_t& name="StatusBar");
	
protected:
	virtual void drawBox(NVGcontext* vg, const rct_t& r ) override;
//	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t alignment) override;
};

inline StatusBar::StatusBar(float x,float y,float w,float h,const str_t& name)
:Aligner(x,y,w,h,name){
	padding( 7, 0 );
	spacing( 6 );
	alignment(align_t::ALL);
	labelColor(nvgRGBAf(0,0,0,.7f));
	labelPt(12.5);
	autoscale(autoscale_t::W);
}

inline StatusBar::StatusBar(float x,float y,float w, const str_t& name)
:Aligner(x,y,w,_size_statusbar_height(),name){
	padding( 7, 0 );
	spacing( 6 );
	alignment(align_t::ALL);
	labelColor(nvgRGBAf(0,0,0,.7f));
	labelPt(12.5);
	autoscale(autoscale_t::W);
}

inline StatusBar::StatusBar(const pos_t& pos,const sz2_t& sz, const str_t& name)
:Aligner(pos,sz,name){
	padding( 7, 0 );
	spacing( 6 );
	alignment(align_t::ALL);
	labelColor(nvgRGBAf(0,0,0,.7f));
	labelPt(12.5);
	autoscale(autoscale_t::W);
}

inline StatusBar::StatusBar(const pos_t& pos,float w, const str_t& name)
:Aligner(pos,sz2_t(w,_size_statusbar_height()),name){
	padding( 7, 0 );
	spacing( 6 );
	alignment(align_t::ALL);
	labelColor(nvgRGBAf(0,0,0,.7f));
	labelPt(12.5);
	autoscale(autoscale_t::W);
}
/*
inline void StatusBar::drawContents(NVGcontext* vg, const rct_t& r, align_t alignment) {
	Widget::drawContents(vg,r,align_t(int(align_t::LEFT)|int(align_t::TOP)));
}
*/
inline void StatusBar::drawBox(NVGcontext* vg, const rct_t& r ) {
	_draw_statusbar_box(vg, r, shadeState() );
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* StatusBar_h */
