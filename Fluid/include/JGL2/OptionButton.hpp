//
//  OptionButton.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_OptionButton_h
#define JGL2_OptionButton_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Button.hpp>
#include <JGL2/MenuPan.hpp>

namespace JGL2 {

struct OptionButton: public Button {
	OptionButton(float x, float y, float w, float h, const str_t& l="" );
	OptionButton(float x, float y, float w, const str_t& l="" );
	OptionButton(float x, float y, const str_t& l="" );
	OptionButton(const pos_t& pos, const sz2_t& sz, const str_t& l="" );
	OptionButton(const pos_t& pos, float w, const str_t& l="" );
	OptionButton(const pos_t& pos, const str_t& l="" );

	virtual void		add( const str_t& item );
	virtual void		clear();

	virtual const str_t&option(idx_t i) const { return _menuPan.item(i).label(); }
	virtual idx_t 		options() const { return int(_menuPan.items()); }
	virtual str_t&		option(idx_t i) { return _menuPan.item(i).label(); }
	virtual void		option(idx_t i,const str_t& s) { _menuPan.item(i).label(s); }
	virtual void		disable(idx_t i) { _menuPan.item(i).disable(); }
	virtual void		enable(idx_t i) { _menuPan.item(i).enable(); }
	virtual bool		disabled(idx_t i) { return _menuPan.item(i).disabled(); }

	virtual idx_t		optionValue() const { return _chosen; }
	virtual void		optionValue(const idx_t i);
	
	virtual void		optionCallback( Callback_t cb, void* ud = nullptr);
	
	virtual void		doOptionCallback();
	
protected:

	virtual void		drawBoxOver(NVGcontext* vg, const rct_t& r) override;
	virtual bool		handle( event_t event ) override;
	
	static  void		chosenCallback( Widget* w, void* ud, idx_t id );

	Callback_t			_optionCB	= nullptr;
	void*				_optionUD	= nullptr;
	
	idx_t				_chosen		= 0;
	MenuPan				_menuPan;
};

inline OptionButton::OptionButton(float x, float y, float w, float h, const str_t& l )
:Button(x,y,w,h,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline OptionButton::OptionButton(float x, float y, float w, const str_t& l )
:Button(x,y,w,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline OptionButton::OptionButton(float x, float y, const str_t& l )
:Button(x,y,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline OptionButton::OptionButton(const pos_t& pos, const sz2_t& sz, const str_t& l )
:Button(pos,sz,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline OptionButton::OptionButton(const pos_t& pos, float w, const str_t& l )
:Button(pos,w,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline OptionButton::OptionButton(const pos_t& pos, const str_t& l )
:Button(pos,l){
	_menuPan.parent(this);
	_menuPan.callback(chosenCallback,this);
}

inline void OptionButton::optionValue(const idx_t i) {
	if( _chosen!= i ) {
		_chosen = i;
		doOptionCallback();
	}
}
	
inline void OptionButton::add( const str_t& item ) {
	_menuPan.add( _MenuItem(item,options() ));
}

inline void OptionButton::clear() {
	_menuPan.clear();
}

inline void OptionButton::doOptionCallback() {
	if( _optionCB )
		_optionCB(this,_optionUD);
	doCallback();
}

	
inline void OptionButton::optionCallback( Callback_t cb, void* ud ) {
	_optionCB = cb;
	_optionUD = ud;
}

inline void OptionButton::drawBoxOver(NVGcontext* vg, const rct_t& r) {
	_draw_optionbox_arrow(vg, r, shadeState());
	Button::drawBoxOver(vg, r);
}

inline bool OptionButton::handle( event_t event ) {
	if( event==event_t::PUSH && _JGL::eventButton()==button_t::LBUTTON && options()>0 ) {
		pos_t pt = _JGL::eventPt();
		if( pt.x>w()-10 && pt.x<w() && pt.y>h()-10 && pt.y<h() ) {
			_menuPan.resize( pos_t( 0, h() ), sz2_t(w(), 2) );
			_menuPan.checkItem(optionValue());
			_JGL::startPopup( &_menuPan, this, pos_t( 0, h() ), pop_reason_t::TYPE_CASCADE_MENU );
			return true;
		}
	}
	return Button::handle(event);
}

inline void	OptionButton::chosenCallback( Widget* w, void* ud, idx_t id ) {
	OptionButton* optionButton = (OptionButton*)ud;
	optionButton->optionValue(id);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* OptionButton_h */
