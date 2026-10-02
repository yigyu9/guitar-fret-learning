//
//  Options.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Options_h
#define JGL2_Options_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/MenuPan.hpp>
#include <JGL2/Property.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

struct Options: public Property, public _Valued<idx_t>, public _Targettable {

	Options(float x,float y,float w,float h, const str_t& label="" );
	Options(float x,float y,float w, const str_t& label="" );
	Options(const pos_t& pos, const sz2_t& sz, const str_t& label="" );
	Options(const pos_t& pos, float w, const str_t& label="" );

	virtual void		add( const str_t& item );
	virtual void		clear();
	virtual bool		handle(event_t event) override;

	virtual idx_t		value() const override { return _chosen; }
	virtual void		value(const idx_t& i) override;

	virtual const str_t& option(idx_t i) const { return _menuPan.item(i).label(); }
	virtual size_t 		options() const { return _menuPan.items(); }
	virtual str_t&		option(idx_t i) { return _menuPan.item(i).label(); }
	virtual void		option(idx_t i,const str_t& s) { _menuPan.item(i).label(s); }
	virtual void		disable(idx_t i) { _menuPan.item(i).disable(); }
	virtual void		enable(idx_t i) { _menuPan.item(i).enable(); }
	virtual bool		disabled(idx_t i) { return _menuPan.item(i).disabled(); }
	
protected:

	virtual sz2_t		minActionSize(NVGcontext*vg) const override;
//	virtual bool		actionScalableW() const override { return true; };
//	virtual bool		actionScalableH() const override { return true; }
	virtual void		drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) override;

	virtual float		boxHorzPadding() const { return _boxHorzPadding<0?_size_options_box_horz_padding():_boxHorzPadding; }
	static  void		chosenCallback( Widget* w, void* ud, idx_t id );
	
	idx_t				_chosen			= -1;
	MenuPan				_menuPan;
	float   			_boxHorzPadding = -1.f;
};

inline Options::Options( float x,float y,float w,float h, const str_t& label )
: Property(x,y,w,h,label), _menuPan("choiceMenu") {
	_chosen = -1;
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline Options::Options( float x,float y,float w, const str_t& label )
: Property(x,y,w,_size_button_height(),label), _menuPan("choiceMenu") {
	_chosen = -1;
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline Options::Options( const pos_t& pos, const sz2_t& sz, const str_t& label )
: Property(pos,sz,label), _menuPan("choiceMenu") {
	_chosen = -1;
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline Options::Options( const pos_t& pos, float w, const str_t& label )
: Property(pos,sz2_t(w,_size_button_height()),label), _menuPan("choiceMenu") {
	_chosen = -1;
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline void Options::add( const str_t& item ) {
	_menuPan.add( _MenuItem( item, (menu_data_t)options() ) );
	if( _chosen<0 ) _chosen = 0;
}
					   
inline void Options::clear() {
	_menuPan.clear();
}

inline void Options::drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) {
	_draw_options_box( vg, r, shadeState());
	
	if( _chosen>=0 ) {
		rct_t rr(r.x+boxHorzPadding(),r.y,
					 r.w-boxHorzPadding()-_size_options_button_width(r.wh()),r.h);

		_draw_options_text(vg,rr,option(_chosen),shadeState());
	}

	_draw_options_control(vg, r, shadeState());
}


inline bool Options::handle(event_t e) {
	if( e == event_t::PUSH ) {
		if( _actionBox.in(_JGL::eventPt()) && options()>0 ) {
			float xx = _actionBox.x+boxHorzPadding()-_menuPan.leftPadding();
			float yy = _actionBox.y-_menuPan.topPadding()
					+_actionBox.h/2.f-_size_menupan_menuitem_height()/2.f;
			_menuPan.resize( pos_t( xx, yy ), sz2_t(_actionBox.w, 2) );
			_menuPan.checkItem(value());
			_JGL::startPopup( &_menuPan, this, pos_t( xx, yy ), pop_reason_t::TYPE_CASCADE_MENU );
		}
		return true;
	}
	if( e == event_t::KEYDOWN ) {
		if( _JGL::eventKey()==GLFW_KEY_DOWN && value()<options()-1 )
			value(value()+1);
		else if( _JGL::eventKey()==GLFW_KEY_UP && value()>0 )
			value(value()-1);
	}
	return Property::handle(e);
}


inline void Options::chosenCallback( Widget* w, void* ud, idx_t id ) {
	Options* options = (Options*)ud;
	options->value(id);
}

inline void Options::value(const idx_t& i) {
	_chosen = i;
	updateAutoVal();
	_menuPan.checkItem(i);
	doCallback();
	damage();
}

inline sz2_t Options::minActionSize(NVGcontext* vg) const {
	sz2_t maxSz=_dim_options_action_min_size();
	{
		std::unique_lock<std::mutex> lock(_menuPan._itemMutex);
		for( size_t i=0; i<_menuPan.items(); i++ ) {
			maxSz = max( maxSz, _measure_menuitem(vg,_menuPan.item(idx_t(i)).label(),false) );
		}
	}
	maxSz.w+=horzPadding()+18+boxHorzPadding()*2;
	maxSz.h+=vertPadding();
	return maxSz;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Options_h */
