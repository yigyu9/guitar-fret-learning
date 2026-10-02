//
//  Check.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Check_h
#define JGL2_Check_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Property.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

struct Check: public Property, public _Targettable, public _Valued<bool> {
	Check(float x, float y, float w, float h, const str_t& label="" );
	Check(float x, float y, float w, const str_t& label="" );
	Check(const pos_t& pos, const sz2_t& sz, const str_t& label="" );
	Check(const pos_t& pos, float w, const str_t& label="" );

	virtual bool		value			() const override { return _checked; }
	virtual void		value			(const bool& i) override;
	
protected:
	virtual bool 		handle			(event_t event) override;

	virtual sz2_t		minActionSize	(NVGcontext*vg) const override;

	virtual void		drawAction		(NVGcontext* vg, const rct_t& r, align_t alignment) override;
	virtual shade_state_t	shadeState		() const override;

	bool				_checked		= false;
	bool				_pressed		= false;
};

inline Check::Check(float x, float y, float w, float h, const str_t& label )
:Property(x, y, w, h, label){
}

inline Check::Check(float x, float y, float w, const str_t& label )
:Property(x, y, w,_size_button_height(), label){
}

inline Check::Check(const pos_t& pos, const sz2_t& sz, const str_t& label )
:Property(pos,sz, label){
}

inline Check::Check(const pos_t& pos, float w, const str_t& label )
:Property(pos, sz2_t(w,_size_button_height()), label){
}

inline shade_state_t  Check::shadeState() const {
	shade_state_t ret = Widget::shadeState();
	if( _pressed )
		ret = ret | shade_state_t::PRESSED;
	return ret;
}

inline bool Check::handle(event_t event) {
	if( event == event_t::PUSH && _JGL::eventButton() == button_t::LBUTTON ) {
		_pressed = true;
		damage();
		return true;
	}
	else if( event == event_t::RELEASE && _JGL::eventButton() == button_t::LBUTTON ) {
		value(!_checked );
		damage();
		_pressed = false;
		return true;
	}
	else if( event == event_t::KEYDOWN && _JGL::eventKey() == GLFW_KEY_SPACE ) {
		value(!_checked );
		damage();
		_pressed = false;
		return true;
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
	return Property::handle(event);
;
}

inline void Check::value(const bool& i) {
	if( _checked!=i ) {
		_checked = i;
		updateAutoVal();
		doCallback();
		damage();
	}
}
	
inline sz2_t Check::minActionSize(NVGcontext*vg) const {
	return _dim_check_action_size();
}

inline void Check::drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) {
	pos_t p = alignRect( r, _dim_check_action_size(), alignment );

	_draw_check_box(vg,rct_t(p,_dim_check_action_size()),shadeState());
	if( _checked )
		_draw_check_checked(vg,rct_t(p,_dim_check_action_size()),shadeState());
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Check_h */
