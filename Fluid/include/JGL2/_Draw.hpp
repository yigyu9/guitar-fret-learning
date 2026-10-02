//
//  _Draw.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__Draw_h
#define JGL2__Draw_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <sstream>
#include <nanovg/nanovg.h>

#include <JGL2/_MathTypes.hpp>
#include <JGL2/_misc.hpp>

namespace JGL2 {

inline colora_t toColorA( const NVGcolor& c ) {
	return colora_t(c.r,c.g,c.b,c.a);
}
inline color_t toColor( const NVGcolor& c ) {
	return color_t(c.r,c.g,c.b);
}
inline NVGcolor toNVGcolor( const colora_t& c ) {
	return nvgRGBAf(c.r,c.g,c.b,c.a);
}
inline NVGcolor toNVGcolor( const color_t& c, float a=1 ) {
	return nvgRGBAf(c.r,c.g,c.b,a);
}

inline void nvgTextAligned(NVGcontext* vg, const rct_t& r, const str_t& str, int aa ) {
	pos_t p = r.tl();
	if( aa& NVG_ALIGN_TOP ) p.y = r.y;
	else if( aa& NVG_ALIGN_BOTTOM ) p.y = r.y+r.h-1;
	else if( aa& NVG_ALIGN_MIDDLE ) p.y = r.y+r.h/2+1;
	
	if( aa& NVG_ALIGN_LEFT ) p.x = r.x;
	else if( aa& NVG_ALIGN_RIGHT  ) p.x = r.x+r.w-1;
	else if( aa& NVG_ALIGN_CENTER ) p.x = r.x+r.w/2;

	nvgTextAlign( vg, aa );
	nvgText( vg, p.x, p.y, str.c_str(), 0);
}

inline void nvgGlowBox(NVGcontext* vg, const rct_t& r, float sz, float radius, const NVGcolor& c) {
	nvgSave(vg);
	nvgResetScissor(vg);
	NVGpaint shadowPnt = nvgBoxGradient(vg, r.x-sz/2, r.y-sz/2, r.w+sz, r.h+sz,
										radius+sz/2, sz, c, nvgRGBAf(c.r,c.g,c.g,0));
	nvgBeginPath(vg);
	nvgRect(vg, r.x-sz, r.y-sz, r.w+sz*2,r.h+sz*2);
	nvgFillPaint(vg, shadowPnt);
	nvgFill(vg);
	
	nvgRestore(vg);
}

inline void drawDot( NVGcontext* ctx, const pos_t& pt, float r1, const NVGcolor& c1, float r2, const NVGcolor& c2) {
	nvgBeginPath( ctx );
	nvgCircle( ctx, pt.x, pt.y, r1);
	nvgFillColor( ctx, nvgRGBAf(c1.r,c1.g,c1.b,c1.a) );
	nvgFill( ctx );
	nvgBeginPath( ctx );
	nvgCircle( ctx, pt.x, pt.y, r2 );
	nvgFillColor( ctx, nvgRGBAf(c2.r,c2.g,c2.b,c2.a) );
	nvgFill( ctx );
}

inline void drawDot( NVGcontext* ctx, const pos_t& pt, float r1, const NVGcolor& c1) {
	nvgBeginPath( ctx );
	nvgCircle( ctx, pt.x, pt.y, r1);
	nvgFillColor( ctx, nvgRGBAf(c1.r,c1.g,c1.b,c1.a) );
	nvgFill( ctx );
}

inline void drawLine( NVGcontext* ctx, const pos_t& pt1, pos_t pt2, float width, const NVGcolor& c1) {
	nvgBeginPath(ctx);
	nvgMoveTo(ctx, pt1.x, pt1.y );
	nvgLineTo(ctx, pt2.x, pt2.y );
	nvgStrokeColor(ctx, nvgRGBAf(c1.r,c1.g,c1.b,c1.a));
	nvgStrokeWidth(ctx, width);
	nvgStroke(ctx);
}

inline void drawRect( NVGcontext* ctx, const rct_t& rect, float width, const NVGcolor& c1) {
	nvgBeginPath(ctx);
	nvgRect(ctx, rect.x, rect.y, rect.w, rect.h );
	nvgStrokeColor(ctx, nvgRGBAf(c1.r,c1.g,c1.b,c1.a));
	nvgStrokeWidth(ctx, width);
	nvgStroke(ctx);
}

inline void drawRoundBox(NVGcontext* ctx, const rct_t& rect, float r, const NVGcolor& fillColor, const NVGcolor& lineColor ) {
	nvgFillColor( ctx, fillColor );
	nvgBeginPath(ctx);
	nvgRoundedRect( ctx, rect.x,rect.y,rect.w,rect.h, r);
	nvgFill(ctx);

	nvgStrokeColor( ctx, lineColor );
	nvgStrokeWidth( ctx, 1.f );
	nvgBeginPath(ctx);
	nvgRoundedRect( ctx, rect.x,rect.y,rect.w,rect.h, r);
	nvgStroke(ctx);
}

inline void drawRoundBox(NVGcontext* ctx, const rct_t& rect, float r, const NVGcolor& fillColor ) {
	nvgFillColor( ctx, fillColor );
	nvgBeginPath(ctx);
	nvgRoundedRect( ctx, rect.x,rect.y,rect.w,rect.h, r);
	nvgFill(ctx);
}

inline void drawRoundBoxL(NVGcontext* ctx, const rct_t& rect, float r, const NVGcolor& lineColor ) {
	nvgStrokeColor( ctx, lineColor );
	nvgStrokeWidth( ctx, 1.f );
	nvgBeginPath(ctx);
	nvgRoundedRect( ctx, rect.x,rect.y,rect.w,rect.h, r);
	nvgStroke(ctx);
}

inline sz2_t nvgMeasureText(NVGcontext* vg, const str_t& str, float pt=-1, const char* font=nullptr ) {
	if( pt>0 )
		nvgFontSize( vg, pt );
	if( font )
		nvgFontFace( vg, font );
	float rect[4];
	nvgTextAlign(vg, NVG_ALIGN_TOP|NVG_ALIGN_LEFT);
	nvgTextBounds( vg, 0, 0, str.c_str(), 0, rect);
	return sz2_t(rect[2]-rect[0],rect[3]-rect[1]);
}

#define NVG_KAPPA90 0.5522847493f	// Length proportional to radius of a cubic bezier handle for 90deg arcs.

inline void nvgPathLeftRoundBox( NVGcontext* ctx, float x, float y, float w, float h, float R ) {
	float l=x, r=x+w, t=y, b=y+h;
	nvgMoveTo( ctx, r, b );
	nvgLineTo( ctx, r, t );
	nvgLineTo( ctx, l+R, t );
	nvgBezierTo( ctx, l+R*(1-NVG_KAPPA90), t, l, t+R*(1-NVG_KAPPA90), l, t+R );
	nvgLineTo( ctx, l, b-R );
	nvgBezierTo( ctx, l, b-R*(1-NVG_KAPPA90), l+R*(1-NVG_KAPPA90), b, l+R, b );
	nvgClosePath( ctx);
}

inline void nvgPathRightRoundBox( NVGcontext* ctx, float x, float y, float w, float h, float R ) {
	float l=x, r=x+w, t=y, b=y+h;
	nvgMoveTo( ctx, l, t );
	nvgLineTo( ctx, l, b );
	nvgLineTo( ctx, r-R, b );
	nvgBezierTo( ctx, r-R*(1-NVG_KAPPA90), b, r, b-R*(1-NVG_KAPPA90), r, b-R );
	nvgLineTo( ctx, r, t+R );
	nvgBezierTo( ctx, r, t+R*(1-NVG_KAPPA90), r-R*(1-NVG_KAPPA90), t, r-R, t );
	nvgClosePath( ctx);
}

inline void nvgPathTopRoundBox( NVGcontext* ctx, float x, float y, float w, float h, float R ) {
	float l=x, r=x+w, t=y, b=y+h;
	nvgMoveTo( ctx, l, b );
	nvgLineTo( ctx, r, b );
	nvgLineTo( ctx, r, t+R );
	nvgBezierTo( ctx, r, t+R*(1-NVG_KAPPA90), r-R*(1-NVG_KAPPA90), t, r-R, t );
	nvgLineTo( ctx, l+R, t );
	nvgBezierTo( ctx, l+R*(1-NVG_KAPPA90), t, l, t+R*(1-NVG_KAPPA90), l, t+R );
	nvgClosePath( ctx);
}

inline void nvgPathBottomRoundBox( NVGcontext* ctx, float x, float y, float w, float h, float R ) {
	float l=x, r=x+w, t=y, b=y+h;
	nvgMoveTo( ctx, r, t );
	nvgLineTo( ctx, l, t );
	nvgLineTo( ctx, l, b-R );
	nvgBezierTo( ctx, l, b-R*(1-NVG_KAPPA90), l+R*(1-NVG_KAPPA90), b, l+R, b );
	nvgLineTo( ctx, r-R, b );
	nvgBezierTo( ctx, r-R*(1-NVG_KAPPA90), b, r, b-R*(1-NVG_KAPPA90), r, b-R );
	nvgClosePath( ctx);
}

inline void nvgShadowRect(NVGcontext* vg, const rct_t& r, float sz, const pos_t& offset, float R ) {
	nvgSave(vg);
	nvgResetScissor(vg);
	
	NVGpaint shadowPaint = nvgBoxGradient(vg, r.x+offset.x,r.y+offset.y, r.w-offset.x, r.h-offset.y,
										  R, sz, nvgRGBAf(0,0,0,.12f), nvgRGBAf(0,0,0,0));
	nvgBeginPath(vg);
	nvgRect(vg, r.x-sz,r.y-sz, r.w+sz*2,r.h+sz*2);
	nvgFillPaint(vg, shadowPaint);
	nvgFill(vg);

	NVGpaint shadowPaint2 = nvgBoxGradient(vg, r.x+offset.x,r.y+offset.y, r.w-offset.x, r.h-offset.y,
										  R, sz*0.25f, nvgRGBAf(0,0,0,.24f), nvgRGBAf(0,0,0,0));
	nvgBeginPath(vg);
	nvgRect(vg, r.x-sz,r.y-sz, r.w+sz*2,r.h+sz*2);
	nvgFillPaint(vg, shadowPaint2);
	nvgFill(vg);

	nvgRestore(vg);
}

inline void nvgPathCheck(NVGcontext*vg, const rct_t& r) {
	nvgBeginPath(vg);
	nvgMoveTo(vg,r.x+r.w*.25f, r.y+r.h*.5f);
	nvgLineTo(vg,r.x+r.w*.4375f, r.y+r.h*.6875f);
	nvgLineTo(vg,r.x+r.w*.75f, r.y+r.h*.3125f);
}

inline void nvgPathHexagon(NVGcontext*vg, const rct_t& r, float arrowHeight) {
	pos_t cntr = pos_t( r.x+r.w/2, r.y+r.h/2 );
	float w2 = r.w/2;
	float h2 = r.h/2;
	nvgMoveTo(vg, cntr.x,  cntr.y+h2);
	nvgLineTo(vg, cntr.x+w2,cntr.y+h2-arrowHeight);
	nvgLineTo(vg, cntr.x+w2,cntr.y-h2+arrowHeight);
	nvgLineTo(vg, cntr.x,  cntr.y-h2);
	nvgLineTo(vg, cntr.x-w2,cntr.y-h2+arrowHeight);
	nvgLineTo(vg, cntr.x-w2,cntr.y+h2-arrowHeight);
	nvgClosePath(vg);
}

inline void nvgPathBalloon(NVGcontext*vg, const rct_t& rr, const pos_t& pointer, float R, const sz2_t& arrowSz ) {
	float RR=R*0.4477152507f;
	float l=rr.x, r=rr.x+rr.w, t=rr.y, b=rr.y+rr.h;
	float w2 = arrowSz.w/2;
	float h  = arrowSz.h;
	pos_t dd = pointer;
	nvgBeginPath(vg);
	nvgMoveTo(vg, l+R, t );
	nvgBezierTo(vg, l+RR, t, l, t+RR, l, t+R );
	if( dd.x<0 && dd.y-w2>=R && dd.y+w2<=rr.h-R ) {
		nvgLineTo(vg, l,   t+dd.y-w2 );
		nvgLineTo(vg, l-h, t+dd.y    );
		nvgLineTo(vg, l,   t+dd.y+w2 );
	}
	nvgLineTo(vg, l,b-R);

	nvgBezierTo(vg, l, b-RR, l+RR, b, l+R, b );
	if( dd.y>rr.h && dd.x>=R+w2 && dd.x<=rr.w-R-w2 ) {
		nvgLineTo(vg, l+dd.x-w2, b   );
		nvgLineTo(vg, l+dd.x,    b+h );
		nvgLineTo(vg, l+dd.x+w2, b   );
	}
	nvgLineTo(vg, r-R,b);
	nvgBezierTo(vg, r-RR, b, r, b-RR, r, b-R );
	if( dd.x>rr.w && dd.y>=R+w2 && dd.y<=rr.h-R-w2 ) {
		nvgLineTo(vg, r,   t+dd.y+w2 );
		nvgLineTo(vg, r+h, t+dd.y    );
		nvgLineTo(vg, r,   t+dd.y-w2 );
	}
	nvgLineTo(vg, r, t+R );
	nvgBezierTo(vg, r, t+RR, r-RR, t, r-R, t );
	if( dd.y<0 && dd.x>=R+w2 && dd.x<=rr.w-R-w2 ) {
		nvgLineTo(vg, l+dd.x+w2, t   );
		nvgLineTo(vg, l+dd.x,    t-h );
		nvgLineTo(vg, l+dd.x-w2, t   );
	}
	nvgClosePath(vg);
}

inline void nvgLine(NVGcontext* vg, const pos_t& s, const pos_t& e) {
	nvgMoveTo(vg,s.x,s.y);
	nvgLineTo(vg,e.x,e.y);
}

inline void nvgLineR(NVGcontext* vg, const pos_t& s, const pos_t& d) {
	nvgMoveTo(vg,s.x,s.y);
	nvgLineTo(vg,s.x+d.x,s.y+d.y);
}

inline void nvgPathLine(NVGcontext* vg, const pos_t& s, const pos_t& e) {
	nvgBeginPath(vg);
	nvgMoveTo(vg,s.x,s.y);
	nvgLineTo(vg,e.x,e.y);
}

inline void nvgPathLineR(NVGcontext* vg, const pos_t& s, const pos_t& d) {
	nvgBeginPath(vg);
	nvgMoveTo(vg,s.x,s.y);
	nvgLineTo(vg,s.x+d.x,s.y+d.y);
}

inline float nvgDashedLine(NVGcontext* vg, const pos_t& s, const pos_t& e, float fill, float gap, float phase) {
	float len = length( s-e );
	pos_t n = normalize( e-s );
	float cur = 0;
	if( phase<fill ) {
		float next = fill-phase;
		if( next>len ) next = len;
		pos_t ss = s;
		pos_t ee = s+next*n;
		nvgMoveTo(vg,ss.x,ss.y);
		nvgLineTo(vg,ee.x,ee.y);
		cur = fill+gap-phase;
	}
	else {
		cur = fill+gap-phase;
	}
	while( cur<len ) {
		float next = cur+fill;
		if( next>len ) next = len;
		pos_t ss = s+cur*n;
		pos_t ee = s+next*n;
		nvgMoveTo(vg,ss.x,ss.y);
		nvgLineTo(vg,ee.x,ee.y);
		cur += fill+gap;
	}
	return fill+gap-(cur-len);
}

inline const NVGcolor nvgColorA(const NVGcolor& c,float a) {
	return nvgRGBAf(c.r,c.g,c.b,c.a*a);
}

inline void drawCircularWait(NVGcontext* vg, const rct_t& r, float waitCount, int circleCount=12 ) {
	pos_t c = { r.w/2+r.x, r.h/2+r.y };
	const float dotR_ = 8;
	float radius = std::min( std::min(r.w,r.h)*0.3f-dotR_, dotR_*6);
	float dotR = std::min( (std::min(r.w,r.h)-radius)*0.8f, dotR_);
	for( int i=0; i<circleCount; i++ ) {
		float theta =i*2.f*3.141592f/circleCount;
		JGL2::pos_t p = radius*pos_t( sinf(theta), -cosf(theta) )+c;
		nvgBeginPath(vg);
		nvgCircle(vg, p.x, p.y, dotR);
		if( i==floorf(waitCount*circleCount) )
			nvgFillColor(vg,nvgRGBAf(1,1,1,0.4f));
		else
			nvgFillColor(vg,nvgRGBAf(1,1,1,0.2f));
		nvgFill(vg);
	}
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _Draw_h */
