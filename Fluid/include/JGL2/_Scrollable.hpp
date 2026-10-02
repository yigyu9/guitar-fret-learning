//
//  _Scrollable.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__Scrollable_h
#define JGL2__Scrollable_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>
#include <JGL2/_Theme.hpp>
namespace JGL2 {

struct _Scrollable {
	virtual void		scrollRange( const sz2_t& screen, const rct_t& content, align_t align );
	virtual void		scrollOffset(const pos_t& d);
	virtual pos_t		scrollOffset() const;
	virtual bool		scrollHandle(event_t event);
	virtual bool		scrollDrawIndicators(NVGcontext* vg);
	virtual bool		scrollEnabled() const { return _scrollEnabled; }
	virtual void		enableScroll() { _scrollEnabled = true; }
	virtual void		disableScroll() { _scrollEnabled = false; }

protected:
	float				_just_scrolled_x = -1.f;
	float				_just_scrolled_y = -1.f;
	float				_on_scroll_bar_x = 0.f;
	float				_on_scroll_bar_y = 0.f;
	pos_t				_scrollOffset = pos_t(0,0);
	bool				_mouseOnHorzScroller = false;
	bool				_mouseOnVertScroller = false;
	pos_t				_scrollClicked;
	rct_t				_scrollWidgetBound;
	rct_t				_scrollContentsBound;
	pos_t				_scrollRange;
	pos_t				_scrollLengthes;
	align_t				_align = align_t::NONE;
	bool				_scrollEnabled = true;
	

	virtual bool		horzScrollerable()const;
	virtual bool		vertScrollerable()const;
	virtual bool		mouseOnVScroller(const pos_t& pt)const;
	virtual bool		mouseOnHScroller(const pos_t& pt)const;
	virtual float		horzScrollerPos(float x)const;
	virtual float		vertScrollerPos(float y)const;
	virtual float		ptToHorzScrollVal(float y) const;
	virtual float		ptToVertScrollVal(float y) const;
	
	
	virtual void		fixScrolledAmount() ;
	virtual void		drawVertIndicators(NVGcontext* vg, const rct_t& r)const;
	virtual void		drawHorzIndicators(NVGcontext* vg, const rct_t& r)const;
	virtual bool		drawVertScrollBar(NVGcontext* vg, const rct_t& r);
	virtual bool		drawHorzScrollBar(NVGcontext* vg, const rct_t& r);
};

} // namespace JGL2

namespace JGL2 {

inline bool _Scrollable::horzScrollerable() const {
	return scrollEnabled() && _scrollWidgetBound.w<_scrollContentsBound.w-.5;
}

inline bool _Scrollable::vertScrollerable() const {
	return scrollEnabled() && _scrollWidgetBound.h<_scrollContentsBound.h-.5;
}

inline void _Scrollable::scrollRange( const sz2_t& screen, const rct_t& content, align_t align ) {
	_scrollWidgetBound = rct_t(0,0,screen.w,screen.h);
	_scrollContentsBound = content;
	_scrollRange.x  = _scrollWidgetBound.w-_size_scroller_offset()*2;
	if( _scrollContentsBound.w>0 )
		_scrollLengthes.x = _scrollRange.x*(_scrollWidgetBound.w/_scrollContentsBound.w);

	_scrollRange.y  = _scrollWidgetBound.h-_size_scroller_offset()*2;
	if( _scrollContentsBound.y>0 )
		_scrollLengthes.y = _scrollRange.y*(_scrollWidgetBound.h/_scrollContentsBound.h);
	
	_align = align;
	
	if( horzScrollerable() ) {
		_just_scrolled_x = 1.f;
	}
	if( vertScrollerable() ) {
		_just_scrolled_y = 1.f;
	}
	fixScrolledAmount();
}

inline float _Scrollable::horzScrollerPos(float x) const {
	return _scrollRange.x*(x/_scrollContentsBound.w)+_size_scroller_offset();
}

inline float _Scrollable::vertScrollerPos(float y) const {
	return _scrollRange.y*(y/_scrollContentsBound.h)+_size_scroller_offset();
}

inline float _Scrollable::ptToHorzScrollVal(float x) const {
	return (x-_size_scroller_offset())*_scrollContentsBound.w/_scrollRange.x;
}

inline float _Scrollable::ptToVertScrollVal(float y) const {
	return (y-_size_scroller_offset())*_scrollContentsBound.h/_scrollRange.y;
}

inline bool _Scrollable::mouseOnHScroller(const pos_t& pt)const {
	return _test_scrollbar_horz(_scrollWidgetBound, pt);
}

inline bool _Scrollable::mouseOnVScroller(const pos_t& pt)const {
	return _test_scrollbar_vert(_scrollWidgetBound, pt);
}

inline bool _Scrollable::scrollHandle(event_t event) {
	static size_t count = 0;
	bool ret = false;
	switch( event ) {
		case event_t::SCROLL:
			if( _JGL::eventMods(mod_t::CONTROL) ) return false;
			if( _scrollWidgetBound.in( _JGL::eventPt() ) ) {
				bool changed = false;
				if( horzScrollerable() && abs(_JGL::eventScroll().x)>0.01 ) { // Horizontally scrollable
					float oldScrolledx = _scrollOffset.x;
					_scrollOffset.x = _scrollOffset.x+_JGL::eventScroll().x*3.f;
					_just_scrolled_x = 1.f;
					fixScrolledAmount();
					if( oldScrolledx!=_scrollOffset.x )
						changed = true;
				}
				if( vertScrollerable() && abs(_JGL::eventScroll().y)>0.01 ) {
					float oldScrolledy = _scrollOffset.y;
					_scrollOffset.y = _scrollOffset.y+_JGL::eventScroll().y*3.f;
					_just_scrolled_y = 1.f;
					fixScrolledAmount();
					if( oldScrolledy!=_scrollOffset.y )
						changed = true;
				}
				ret|=changed;
			}	break;
			
			
		case event_t::MOVE: {
			_mouseOnHorzScroller = false;
			_mouseOnVertScroller = false;
			if( horzScrollerable() && _just_scrolled_x>0.f && mouseOnHScroller(_JGL::eventPt() ) ) {
				_mouseOnHorzScroller = true;
				ret|=true;
			}
			if( vertScrollerable() && _just_scrolled_y>0.f && mouseOnVScroller(_JGL::eventPt() ) ) {
				_mouseOnVertScroller = true;
				ret|=true;
			}
		}	break;
		case event_t::PUSH: {
			count = 0;
			if( _JGL::eventButton() == button_t::LBUTTON) {
				if( _mouseOnHorzScroller ) {
					_scrollClicked.x=ptToHorzScrollVal(_JGL::eventPt().x);
					ret|=true;
				}
				if( _mouseOnVertScroller ) {
					_scrollClicked.y=ptToVertScrollVal(_JGL::eventPt().y);
					ret|=true;
				}
			}
		}	break;
		case event_t::DRAG: {
			if( _JGL::eventMods(mod_t::LBUTTON) ) {
				if( _mouseOnHorzScroller ) {
					float newScrollX = ptToHorzScrollVal(_JGL::eventPt().x);
					_scrollOffset.x+=newScrollX-_scrollClicked.x;
					_scrollClicked.x = newScrollX;
					fixScrolledAmount();
					ret|=true;
				}
				if( _mouseOnVertScroller ) {
					float newScrollY = ptToVertScrollVal(_JGL::eventPt().y);
					_scrollOffset.y+=newScrollY-_scrollClicked.y;
					_scrollClicked.y = newScrollY;
					fixScrolledAmount();
					ret|=true;
				}
			}
		}	break;
		case event_t::CANCEL: {
			if( _mouseOnHorzScroller ) {
				_mouseOnHorzScroller = false;
				ret|=true;
			}
			if( _mouseOnVertScroller ) {
				_mouseOnVertScroller = false;
				ret|=true;
			}
		} break;
		case event_t::LEAVE: {
			if( !_JGL::eventMods(mod_t::LBUTTON) ) {
				if( _mouseOnHorzScroller ) {
					_mouseOnHorzScroller = false;
					ret|=true;
				}
				if( _mouseOnVertScroller ) {
					_mouseOnVertScroller = false;
					ret|=true;
				}
			}
		} break;
		case event_t::RELEASE: {
			if( _JGL::eventButton()==button_t::LBUTTON ) {
				if( _mouseOnHorzScroller ) {
					_mouseOnHorzScroller = false;
					ret|=true;
				}
				if( _mouseOnVertScroller ) {
					_mouseOnVertScroller = false;
					ret|=true;
				}
			}
		} break;
		default:
			break;
	}
	return ret;
}

inline void _Scrollable::drawHorzIndicators(NVGcontext* vg, const rct_t& r)const {
	if( _scrollOffset.x<_scrollContentsBound.w-_scrollWidgetBound.w) {
		_draw_scroll_indicator_left(vg, r);
	}
	if( _scrollOffset.x >0 ) {
		_draw_scroll_indicator_right(vg, r);
	}
}

inline void _Scrollable::drawVertIndicators(NVGcontext* vg, const rct_t& r)const {
	if( _scrollOffset.y<_scrollContentsBound.h-_scrollWidgetBound.h) {
		_draw_scroll_indicator_top(vg, r);
	}
	if( _scrollOffset.y >0 ) {
		_draw_scroll_indicator_bottom(vg,r);
	}
}

inline bool _Scrollable::drawHorzScrollBar(NVGcontext* vg, const rct_t& r) {
	if( _just_scrolled_x>0 ) {
		if( _mouseOnHorzScroller ) {
			_just_scrolled_x = 1.f;
			_on_scroll_bar_x+=0.25f;
		}
		else
			_on_scroll_bar_x-=0.25f;
		float sz = std::clamp( _on_scroll_bar_x, 0.f, 1.f );
		float alpha = std::clamp(_just_scrolled_x*2.f,0.f,1.f);

		_draw_scrollbar_horz(vg, r, alpha, sz, _scrollContentsBound.w, _scrollOffset.x);

		if( _on_scroll_bar_x<0.01 )
			_just_scrolled_x-=.025f;
		if( sz==_on_scroll_bar_x ) return true;
		_on_scroll_bar_x = sz;
		if( _just_scrolled_x>0.f ) return true;
	}
	return false;
}

inline bool _Scrollable::drawVertScrollBar(NVGcontext* vg, const rct_t& r) {
	if( _just_scrolled_y>0 ) {
		if( _mouseOnVertScroller ) {
			_just_scrolled_y = 1.f;
			_on_scroll_bar_y+=0.25f;
		}
		else
			_on_scroll_bar_y-=0.25f;
		float sz = std::clamp( _on_scroll_bar_y, 0.f, 1.f );
		float alpha = std::clamp(_just_scrolled_y*2.f,0.f,1.f);

		_draw_scrollbar_vert(vg, r, alpha, sz, _scrollContentsBound.h, _scrollOffset.y);
		
		if( _on_scroll_bar_y<0.01 )
			_just_scrolled_y-=.025f;
		if( sz==_on_scroll_bar_y ) return true;
		_on_scroll_bar_y = sz;
		if( _just_scrolled_y>0.f ) return true;
	}
	return false;
}

inline bool _Scrollable::scrollDrawIndicators(NVGcontext* vg) {
	bool ret = false;
	if( horzScrollerable() ) {
		// Draw scroll indicator
		ret|=drawHorzScrollBar(vg, _scrollWidgetBound);
		drawHorzIndicators(vg, _scrollWidgetBound);
	}
	if( vertScrollerable() ) {
		ret|=drawVertScrollBar(vg, _scrollWidgetBound);
		drawVertIndicators(vg, _scrollWidgetBound);
	}
	return ret;
}

inline void _Scrollable::scrollOffset(const pos_t& d) {
	_scrollOffset = d;
	fixScrolledAmount();
}

inline pos_t _Scrollable::scrollOffset() const {
	return _scrollOffset + _scrollContentsBound.tl();
}

inline void _Scrollable::fixScrolledAmount() {
	if( horzScrollerable() ) {
		_scrollOffset.x = std::max(0.f,std::min( float(_scrollContentsBound.w-_scrollWidgetBound.w), _scrollOffset.x ));
	}
	else {
		_scrollOffset.x = -alignRect(_scrollWidgetBound, _scrollContentsBound.wh(), _align).x;
	}
	if( vertScrollerable() )
		_scrollOffset.y = std::max(0.f,std::min( float(_scrollContentsBound.h-_scrollWidgetBound.h), _scrollOffset.y ));
	else {
		_scrollOffset.y = -alignRect(_scrollWidgetBound, _scrollContentsBound.wh(), _align).y;
	}
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _Scrollable_h */
