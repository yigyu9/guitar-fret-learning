//
//  RadioButtonGroup.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_RadioButtonGroup_h
#define JGL2_RadioButtonGroup_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/ButtonGroup.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

struct RadioButtonGroup: public ButtonGroup, public _Valued<int>, public _Targettable {
	RadioButtonGroup(float x,float y,float w,float h, const str_t& label="" );
	RadioButtonGroup(const pos_t& pos, const sz2_t& sz, const str_t& label="" );
	virtual void	end() override;
	virtual void	add(Widget* w) override;

	virtual int		value() const override { return _selected; }
	virtual void	value(const int& k) override;
	virtual void	drawBox(NVGcontext* vg, const rct_t& r) override;

protected:
	virtual bool	handle(event_t e) override;
	virtual void	buttonValueChanged( Widget* );
	static  void	buttonValueChangedCB( Widget*, void* );

	int				_selected = 0;
};

inline RadioButtonGroup::RadioButtonGroup( float x,float y,float w,float h, const str_t& label )
:ButtonGroup(x,y,w,h,label){}

inline RadioButtonGroup::RadioButtonGroup( const pos_t& pos, const sz2_t& sz, const str_t& label )
:ButtonGroup(pos,sz,label){}

inline void RadioButtonGroup::end() {
	ButtonGroup::end();
	for( auto c: _children ) {
		Button* b = dynamic_cast<Button*>(c);
		if( b ) {
			b->actionType(Button::actionType_t::TOGGLE);
			b->onType(Button::onType_t::CHECK);
		}
	}
	value(_selected);

	for( auto c: _children ) {
		Button* b = dynamic_cast<Button*>(c);
		if( b ) {
			b->callback(buttonValueChangedCB, this);
			((_Targettable*)b)->preventTargetted();
		}
	}
}

inline void RadioButtonGroup::add( Widget* w) {
	ButtonGroup::add(w);
	Button* b = dynamic_cast<Button*>(w);
	if( b ) {
		b->actionType(Button::actionType_t::TOGGLE);
		b->onType(Button::onType_t::CHECK);
		b->callback(buttonValueChangedCB, this);
	}
}

inline void RadioButtonGroup::value(const int& k) {
	int cnt = 0;
	{
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) {
			Button* b = dynamic_cast<Button*>(c);
			if( b ) {
				if( cnt != k && b->value() ) {
					b->_on = false;
					b->pressed(false);
				}
				if( cnt == k ) {
					b->_on = true;
//					b->pressed(true);
					b->pressed(false);
				}
				cnt++;
			}
		}
	}
	if( k!=_selected) {
		_selected = k;
		updateAutoVal();
		doCallback();
	}
	damage();
}

inline void RadioButtonGroup::buttonValueChanged( Widget* w ) {
	int cnt = 0;
	int found = -1;
	// Note: this function should not call value() function to prevent "deadlock".
	// Note: this function is called in event thread, so children is well locked, before.
	for( auto c: _children ) {
		Button* b = dynamic_cast<Button*>(c);
		if( b ) {
			if( b!=w && b->value() ) {
				b->_on = false;
				b->pressed(false);
			}
			if( b==w) {
				b->_on = true;
//				b->pressed(true);
				b->pressed(false);
				found = cnt;
			}
			cnt++;
		}
	}
	if( found>=0 && found!=_selected) {
		_selected = found;
		updateAutoVal();
		doCallback();
	}
}

inline void RadioButtonGroup::buttonValueChangedCB( Widget* w, void* ud ) {
	((RadioButtonGroup*)ud)->buttonValueChanged( w );
}

inline void	RadioButtonGroup::drawBox(NVGcontext* vg, const rct_t& r) {
	nvgSave( vg );
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
	nvgSave( vg );
	nvgTranslate( vg, child(0)->x(), child(0)->y() );
	auto b = contentsRect();
	_draw_radio_button_group_box(vg, b, shadeState());
	nvgRestore(vg);
	nvgRestore(vg);
	
	ButtonGroup::drawBox(vg, r);
}

inline bool RadioButtonGroup::handle(event_t e) {
	if( e==event_t::KEYDOWN ) {
		switch( _JGL::eventKey() ) {
			case GLFW_KEY_LEFT :
				if( value()>0 ) value(value()-1);
				return true;
			case GLFW_KEY_RIGHT : {
				int cnt = 0;
				for( auto c: _children ) {
					Button* b = dynamic_cast<Button*>(c);
					if( b ) cnt++;
				}
				if( value()<cnt-1 ) value(value()+1);
				return true;
			}
		}
	}
	return ButtonGroup::handle(e);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* RadioButtonGroup_h */
