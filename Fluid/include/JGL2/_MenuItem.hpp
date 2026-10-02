//
//  _MenuItem.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__MenuItem_h
#define JGL2__MenuItem_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Widget.hpp>

namespace JGL2 {

struct MenuPan;
struct _MenuItem;

struct _MenuItem {
	_MenuItem(const str_t& label, menu_data_t data, bool disabled=false);
	
	virtual sz2_t				measure(NVGcontext* vg);
	virtual void				draw(NVGcontext* vg, const rct_t& r, align_t align, bool state);
		
	virtual bool				disabled		() const { return _disabled; }
	virtual void				enable			() { _disabled=false; }
	virtual void				disable			() { _disabled=true; }
	virtual bool				isSeparator		() { return _label.compare("----")==0; }
		
	// Submenu control functions
	virtual void				add				(const _MenuItem& item);
	virtual void				add				(const str_t& name, menu_data_t data, bool disabled=false);
	virtual void				add				(const menuitem_list_t& items);
	virtual void				clear			();
	virtual void				disable			(idx_t idx);
	virtual void				enable			(idx_t idx);
	virtual _MenuItem&			item			(idx_t idx);
	virtual const _MenuItem&	item			(idx_t idx) const;
	virtual size_t				items			() const { return _items.size(); }
	
	virtual str_t&				label			() { return _label; }
	virtual const str_t&		label			() const { return _label; }
	virtual void				label			(const str_t& s) { _label=s; }
	virtual menu_data_t			data			() { return _data; }
	virtual const int&			data			() const { return _data; }
	virtual void				data			(menu_data_t d) { _data=d; }
protected:
	str_t						_label			= "----";
	menu_data_t					_data			= 0;
	bool						_disabled		= false;
	menuitem_list_t				_items;
	
	friend						MenuPan;
};

} // namespace JGL2

namespace JGL2 {

inline _MenuItem::_MenuItem(const str_t& label, int data, bool disabled)
:_label(label),_data(data), _disabled(false) {
}

inline sz2_t _MenuItem::measure(NVGcontext* vg ){
	return _measure_menuitem(vg, _label, isSeparator() );
}

inline void _MenuItem::draw(NVGcontext* vg, const rct_t& r, align_t align, bool state ) {
	_draw_menuitem(vg, r, _label, align, state, _disabled, isSeparator() );
}

inline void _MenuItem::add( const _MenuItem& item ) {
	_items.push_back(item);
}

inline void _MenuItem::add( const str_t& name, int data, bool disabled ) {
	add(_MenuItem(name,data,disabled));
}

inline void _MenuItem::add( const menuitem_list_t& items ) {
	_items.insert(_items.end(),items.begin(),items.end());
}

inline void _MenuItem::clear() {
	_items.clear();
}

inline void _MenuItem::disable(idx_t idx) {
	item(idx).disable();
}

inline void _MenuItem::enable(idx_t idx) {
	item(idx).enable();
}

inline _MenuItem& _MenuItem::item(idx_t idx) {
	return _items[idx];
}

inline const _MenuItem& _MenuItem::item(idx_t idx) const {
	return _items[idx];
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _MenuItem_h */
