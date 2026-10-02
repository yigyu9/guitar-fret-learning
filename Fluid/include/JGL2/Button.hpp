//
//  Button.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Button_h
#define JGL2_Button_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Widget.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

struct ButtonGroup;
struct RadioButtonGroup;

struct Button: public Widget, public _Valued<bool>, public _Targettable {
	enum class actionType_t {
		PUSH = 0,
		TOGGLE = 1,
	};
	enum class onType_t {
		SHADE = 0,
		CHECK = 1,
	};
	Button(float x, float y, float w, float h, const str_t& l="" );
	Button(float x, float y, float w, const str_t& l="" );
	Button(float x, float y, const str_t& l="" );
	Button(const pos_t& pos, const sz2_t& sz, const str_t& l="" );
	Button(const pos_t& pos, float w, const str_t& l="" );
	Button(const pos_t& pos, const str_t& l="" );
	
	virtual bool			value() const override { return _on; }
	virtual void			value(const bool& i) override;

	virtual bool			pressed() const { return _pressed; }
	
	virtual void			actionType( actionType_t t );
	virtual actionType_t	actionType() const { return _actionType; }

	virtual void			onType( onType_t t );
	virtual onType_t		onType() const { return _onType; }
	
protected:

	virtual void			drawBox(NVGcontext* vg, const rct_t& r) override;
	virtual void			drawImageLabel(NVGcontext* vg, const rct_t& r,align_t align) override;
	virtual void			drawBoxOver(NVGcontext* vg, const rct_t& r) override;
	virtual void			updateContentsRect(NVGcontext*) override;
	virtual bool			handle( event_t event ) override;
	virtual shade_state_t 	shadeState() const override;
	virtual void			boxType( box_type_t t ) { _boxType = t; damage(); }
	virtual void			pressed(bool p) { _pressed=p; damage(); }
	
	actionType_t			_actionType		= actionType_t::PUSH;
	bool					_pressed		= false;
	bool					_on				= false;

	box_type_t				_boxType		= box_type_t::BOX_IND;
	onType_t				_onType			= onType_t::SHADE;

	friend ButtonGroup;
	friend RadioButtonGroup;
};

} // namespace JGL2

namespace JGL2 {

inline Button::Button(float x, float y, float w, float h, const str_t& l )
: Widget( x, y, w, h, l ) {
	alignment(align_t::ALL);
}

inline Button::Button(float x, float y, float w, const str_t& l )
: Widget( x, y, w, _size_button_height(), l ) {
	alignment(align_t::ALL);
}

inline Button::Button(float x, float y, const str_t& l )
: Widget( x, y, _size_button_width(), _size_button_height(), l ) {
	alignment(align_t::ALL);
}

inline Button::Button(const pos_t& pos, const sz2_t& sz, const str_t& l )
: Widget( pos, sz, l ) {
	alignment(align_t::ALL);
}

inline Button::Button(const pos_t& pos, float w, const str_t& l )
: Widget( pos, sz2_t(w,_size_button_height()), l ) {
	alignment(align_t::ALL);
}

inline Button::Button(const pos_t& pos, const str_t& l )
: Widget( pos, sz2_t(_size_button_width(),_size_button_height()), l ) {
	alignment(align_t::ALL);
}

inline void Button::actionType( actionType_t t ) {
	_actionType = t;
	if( t == actionType_t::PUSH )
		_on = false;
}

inline void Button::onType( onType_t t ) {
	if( _onType != t ) {
		_onType = t;
		if( _on )
			damage();
	}
}

inline shade_state_t Button::shadeState() const {
	shade_state_t ret = Widget::shadeState();
	if( _pressed )
		ret = ret | shade_state_t::PRESSED;
	if( value() )
		ret = ret | shade_state_t::ENGAGED;
	return ret;
}

inline void Button::drawBoxOver(NVGcontext* vg,const rct_t& r) {
	shade_state_t s = shadeState();
	if( _on && _onType == onType_t::CHECK ) {
		_draw_button_group_check(vg,r,s);
		if( _pressed )
			_draw_button_box_over(vg, r, s, _boxType);
	}
	else
		_draw_button_box_over(vg, r, s, _boxType);
}

inline void Button::drawImageLabel(NVGcontext* vg, const rct_t& r, align_t align) {
	_draw_button_box_image(vg, r, getImagePaint(vg,r,align), shadeState(), _boxType);
}

inline void Button::drawBox(NVGcontext* vg,const rct_t& r) {
	_draw_button_box(vg, r, shadeState(), _boxType);
}

inline bool Button::handle( event_t event ) {
	switch( _actionType ) {
	case actionType_t::PUSH:
			if( event == event_t::PUSH && _JGL::eventButton() == button_t::LBUTTON ) {
				damage();
				_pressed = true;
				return true;
			}
			else if( event == event_t::RELEASE && _JGL::eventButton() == button_t::LBUTTON ) {
				if( _pressed ) {
					damage();
					doCallback();
					_pressed = false;
					return true;
				}
			}
			else if( event == event_t::CANCEL ) {
				damage();
				_pressed = false;
			}
			else if( event == event_t::LEAVE ) {
				if( _pressed ) {
					_pressed=false;
					damage();
				}
			}
			else if( event == event_t::KEYDOWN && _JGL::eventKey() == GLFW_KEY_SPACE ) {
				damage();
				_pressed = true;
				return true;
			}
			else if( event == event_t::KEYUP && _JGL::eventKey() == GLFW_KEY_SPACE ) {
				if( _pressed ) {
					damage();
					doCallback();
					_pressed = false;
				}
				return true;
			}
			break;
	case actionType_t::TOGGLE:
			if( event == event_t::PUSH && _JGL::eventButton() == button_t::LBUTTON ) {
				_pressed = true;
				damage();
				return true;
			}
			else if( event == event_t::RELEASE && _JGL::eventButton() == button_t::LBUTTON ) {
				if( _pressed ) {
					value(!_on );
					damage();
					_pressed = false;
					return true;
				}
			}
			else if( event == event_t::CANCEL ) {
				if( _pressed ) {
					_pressed=false;
					damage();
				}
			}
			else if( event == event_t::LEAVE ) {
				if( _pressed ) {
					_pressed=false;
					damage();
				}
			}
			else if( event == event_t::KEYDOWN && _JGL::eventKey() == GLFW_KEY_SPACE ) {
				_pressed = true;
				damage();
				return true;
			}
			else if( event == event_t::KEYUP && _JGL::eventKey() == GLFW_KEY_SPACE ) {
				if( _pressed ) {
					value(!_on );
					damage();
					_pressed = false;
					return true;
				}
			}
			break;
	}
	return Widget::handle(event);
}

inline void Button::value(const bool& i) {
	if( _on!=i ) {
		_on=i;
		updateAutoVal();
		doCallback();
		damage();
	}
}

inline void Button::updateContentsRect(NVGcontext* vg) {
	Widget::updateContentsRect(vg);
//	_contentsRect.tl() = vec2(0);
//	_contentsRect.wh() = measureTextLabel(vg)+dim2(horzPadding(),vertPadding());
//	syncScroller();
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Button_h */
