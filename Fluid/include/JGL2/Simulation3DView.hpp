//
//  Simulation3DView.hpp
//  SpringMass
//
//  Created by Hyun Joon Shin on 2021/05/12.
//

#ifndef JGL_Simulation3DView_hpp
#define JGL_Simulation3DView_hpp

#include "View3D.hpp"

namespace JGL2 {

typedef std::function<void()> InitCB_t;
typedef std::function<void(float)> FrameCB_t;

extern inline void draw_simulation_triangle_button( NVGcontext* vg, const rct_t&r, const NVGcolor& c, const pos_t& p1, const pos_t& p2, const pos_t& p3 );
extern inline void draw_simulation_vert_bar_button( NVGcontext* vg, const rct_t&r, const NVGcolor& c, const pos_t& p1, const pos_t& p2 );
extern inline void draw_simulation_prev_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);
extern inline void draw_simulation_play_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);
extern inline void draw_simulation_pause_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);

template<typename T=JR::PBRRenderer, typename=enable_if_renderer<T>>
struct Simulation3DView: public Render3DView<T> {
	Simulation3DView(float x, float y, float w, float h, const std::string& name="")
	: Render3DView<T>(x,y,w,h,name){}
	
	virtual inline void			initCB ( InitCB_t f)  { _initCB  = f; }
	virtual inline void			frameCB( FrameCB_t f) { _frameCB = f; }
	
	virtual inline void			resetInitCB()  { _initCB  = defInitCB; }
	virtual inline void			resetFrameCB() { _frameCB = defFrameCB; }
	
	virtual inline const bool&	animating() const	{ return _animating; }
	virtual inline bool&		animating() 		{ return _animating; }
	virtual inline void			animating(bool t)	{
		_animating=t;
		if( _animating ) {
			_lastT = glfwGetTime();
			Render3DView<T>::animate();
		}
	}
	virtual inline bool handle(event_t e) override {
		if( e == event_t::KEYDOWN ) {
			if( _JGL::eventKey() == ' ' ) {
				animating(!animating());
				return true;
			}
			else if( _JGL::eventKey() == '0' ) {
				animating(false);
				_initCB();
				Render3DView<T>::redraw();
				return true;
			}
		}
		else if( e == event_t::MOVE ) {
			pos_t pt = eventPt();
			bool oldPlay = _mouseOverPlayButton;
			bool oldPrev = _mouseOverPrevButton;
			_mouseOverPlayButton = playBtnRect().in(pt);
			_mouseOverPrevButton = prevBtnRect().in(pt);
			if( oldPlay!=_mouseOverPlayButton || oldPrev!=_mouseOverPrevButton )
				Render3DView<T>::redraw();
		}
		else if( e == event_t::PUSH ) {
			pos_t pt = eventPt();
			if( playBtnRect().in(pt) ) {
				animating(!animating());
				_mouseOnButton = true;
				return true;
			}
			if( prevBtnRect().in(pt) ) {
				animating(false);
				_initCB();
				Render3DView<T>::redraw();
				_mouseOnButton = true;
				return true;
			}
		}
		else if( e == event_t::RELEASE ) {
			if( _mouseOnButton ) {
				_mouseOnButton = false;
				return true;
			}
		}
		else if( e == event_t::DRAG ) {
			if( _mouseOnButton ) return true;
		}
		return Render3DView<T>::handle( e );
	}
	virtual inline void drawGL() override {
		if( !_inited ) {
			_initCB();
			_inited = true;
		}
		if( _animating ) {
			float t = glfwGetTime();
			_frameCB(t-_lastT);
			Render3DView<T>::animate();
			_lastT = t;
		}
		Render3DView<T>::drawGL();
	}
	virtual inline void		drawContents(NVGcontext* vg, const rct_t& r, align_t a) override {
		draw_simulation_prev_button(vg, prevBtnRect(), nvgRGBAf(.6,.6,.6,_mouseOverPrevButton?.8:.5));
		if( !animating() )
			draw_simulation_play_button(vg, playBtnRect(), nvgRGBAf(.6,.6,.6,_mouseOverPlayButton?.8:.5));
		else
			draw_simulation_pause_button(vg, playBtnRect(), nvgRGBAf(.6,.6,.6,_mouseOverPlayButton?.8:.5));
	}

protected:
	const InitCB_t	defInitCB	= [](){};
	const FrameCB_t	defFrameCB 	= [](float){};
	
	float			_lastT		= 0;
	bool			_animating	= false;
	
	InitCB_t		_initCB		= defInitCB;
	FrameCB_t		_frameCB	= defFrameCB;
	bool			_inited		= false;
	
	bool			_mouseOnButton = false;
	bool			_mouseOverPlayButton = false;
	bool			_mouseOverPrevButton = false;
	const float		__margin = 12;
	const float		__btnW = 38;
	const float		__btnH = 40;
	inline	rct_t	playBtnRect() const { return rct_t(__margin+__btnW,Render3DView<T>::h()-__btnH,__btnW,__btnH); }
	inline	rct_t	prevBtnRect() const { return rct_t(__margin,Render3DView<T>::h()-__btnH,__btnW,__btnH); }
};

inline void draw_simulation_triangle_button( NVGcontext* vg, const rct_t&r, const NVGcolor& c, const pos_t& p1, const pos_t& p2, const pos_t& p3 ) {
	nvgBeginPath(vg);
	nvgMoveTo(vg,r.x+r.w*p1.x,r.y+r.h*p1.y);
	nvgLineTo(vg,r.x+r.w*p2.x,r.y+r.h*p2.y);
	nvgLineTo(vg,r.x+r.w*p3.x,r.y+r.h*p3.y);
	nvgClosePath(vg);
	nvgFillColor(vg,c);
	nvgFill(vg);
}

inline void draw_simulation_vert_bar_button( NVGcontext* vg, const rct_t&r, const NVGcolor& c, const pos_t& p1, const pos_t& p2 ) {
	nvgBeginPath(vg);
	nvgRoundedRect(vg, r.x+r.w*p1.x, r.y+r.h*p1.y, (p2.x-p1.x)*r.w, (p2.y-p1.y)*r.h, (p2.x-p1.x)*r.w*0.25 );
	nvgFillColor(vg,c);
	nvgFill(vg);
}

inline void draw_simulation_prev_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_simulation_vert_bar_button(vg,r,c,{0.35,0.3},{0.5,0.7});
	draw_simulation_triangle_button(vg,r,c,{0.8f,0.3f},{0.5f,0.5f},{0.8f,0.7f});
}

inline void draw_simulation_play_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_simulation_triangle_button(vg,r,c,{0.3f,0.25f},{0.8f,0.5f},{0.3f,0.75f});
}

inline void draw_simulation_pause_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_simulation_vert_bar_button(vg,r,c,{0.3,0.3},{0.45,0.7});
	draw_simulation_vert_bar_button(vg,r,c,{0.55,0.3},{0.7,0.7});
}

} // namespace JGL2

#endif /* JGL_Simulation3DView_hpp */
