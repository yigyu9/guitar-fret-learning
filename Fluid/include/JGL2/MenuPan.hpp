//
//  MenuPan.h
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_MenuPan_hpp
#define JGL2_MenuPan_hpp

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <mutex>

#include <JGL2/Widget.hpp>
#include <JGL2/_MenuItem.hpp>

namespace JGL2 {

struct Options;

typedef void (*MenuPanCallback)(Widget* w, void* ud, menu_data_t data);

struct MenuPan: public Widget {
	MenuPan( const str_t& label="MenuPan" );

	virtual void			set( const menuitem_list_t& items );
	virtual void			add( const _MenuItem& i );
	virtual void			add( const menuitem_list_t& items );
	virtual void			clear();

	virtual void			rearrange(NVGcontext* vg,autoscale_t scaling) override;

	virtual idx_t 			checkedItem() const { return _checkedItem; }
	virtual void			checkItem(int i);
	virtual bool			isItemExpandable(int i);
	virtual void			clearSelection();
	virtual void			callback( MenuPanCallback cb, void* ud=nullptr);
	virtual size_t			items() const { return _items.size(); }
	virtual _MenuItem&		item(idx_t i) { return _items[i]; }
	virtual const _MenuItem&item(idx_t i) const { return _items[i]; }

	
	virtual float			topPadding		() const override { return _topPadding<0?_size_menupan_padding_vert():_topPadding; }
	virtual float			bottomPadding	() const override { return _bottomPadding<0?_size_menupan_padding_vert():_bottomPadding; }
	virtual float			leftPadding		() const override { return _leftPadding<0?_size_menupan_padding_horz():_leftPadding; }
	virtual float			rightPadding	() const override { return _rightPadding<0?_size_menupan_padding_horz():_rightPadding; }

	virtual ilst_t			selectedItem() const;
protected:

	virtual void			updateContentsRect(NVGcontext* vg) override;
	
	virtual bool			handle			(event_t event) override;
	virtual void			drawBox			(NVGcontext* vg, const rct_t& r) override;
	virtual void			draw			(NVGcontext* vg) override;
	virtual int 			itemUnder		(const pos_t& pt) const;
	
	virtual bool			under			(const pos_t& pt) const override;
	
	virtual void			expandCascade	();
	virtual void			clearCascade	();
	virtual menu_data_t		selectedItemData() const;
		
	idx_t					_underMouseItem	= -1;
	idx_t					_checkedItem	= -1;
	MenuPanCallback			_menuCallback	= nullptr;
	menuitem_list_t			_items;
	mutable std::mutex		_itemMutex;
	MenuPan*				_cascadePan		= nullptr;
	idx_t					_cascadeParent	= -1;
	
	friend					Options;

};

inline MenuPan::MenuPan( const str_t& label )
:Widget(0,0,10,10,label) {
	padding(-1,-1);
}

inline void MenuPan::set( const menuitem_list_t& items ) {
	_items = items;
	change();
}

inline void MenuPan::add( const _MenuItem& i ) {
	std::unique_lock<std::mutex> lock(_itemMutex);
	_items.push_back( i );
	change();
}

inline void MenuPan::add( const menuitem_list_t& items ) {
	for( auto i: items )
		add(i);
}

inline void MenuPan::clear() {
	std::unique_lock<std::mutex> lock(_itemMutex);
	clearSelection();
	_items.clear();
}

inline void MenuPan::updateContentsRect(NVGcontext* vg) {
	sz2_t ssz = sz2_t(_setSize.w-horzPadding(),topPadding() );
	{
		std::unique_lock<std::mutex> lock(_itemMutex);
		for( auto i: _items ) {
			sz2_t s = i.measure(_JGL::getCurrentNVGContext());
			ssz.w  = std::max( s.w, ssz.w );
			ssz.h += s.h;
		}
	}
	ssz.h+=bottomPadding();
	ssz.w+=horzPadding();
	_contentsRect.wh() = ssz;
}

inline void MenuPan::rearrange(NVGcontext* vg,autoscale_t scaling) {
	if( changed() ) {
		updateContentsRect(vg);
		_setSize = contentsRect().wh();
		Widget::rearrange(vg,scaling);
	}
}

inline bool MenuPan::isItemExpandable( idx_t i ) {
	if( i>=0 && i<_items.size() && _items[i].items()>0 ) return true;
	else return false;
}

inline bool MenuPan::under( const pos_t& pt ) const {
	bool ret = Widget::under(pt);
	if( _cascadePan )
		ret|=_cascadePan->under(pt);
	return ret;
}

inline ilst_t MenuPan::selectedItem() const {
	ilst_t ret;
	ret.push_back( _underMouseItem );
	if( _cascadePan && _cascadeParent==_underMouseItem ) {
		auto sub = _cascadePan->selectedItem();
		ret.insert(ret.end(), sub.begin(), sub.end() );
	}
	return ret;
}

inline idx_t MenuPan::itemUnder( const pos_t& pt ) const {
	if( _cascadePan && _cascadePan->under( pt+abs_pos() ) )
		return _cascadeParent;

	if( pt.x<0 || pt.x>=w() )
		return -1;
	
	float yy = topPadding();
	idx_t count = -1;
	if( pt.y<yy )
		return count;
	
	std::unique_lock<std::mutex> lock(_itemMutex);
	for( auto i: _items ) {
		count++;
		sz2_t s = i.measure(nullptr);
		if( pt.y<yy+s.h ) {
			if( !i.disabled() )
				return count;
			return -1;
		}
		yy+=s.h;
	}
	return -1;
}

inline void MenuPan::clearCascade	() {
	if( _cascadePan )
		delete _cascadePan;
	_cascadePan = nullptr;
	_cascadeParent = -1;
}

inline void	MenuPan::clearSelection() {
	_underMouseItem = -1;
	clearCascade();
}

inline void MenuPan::expandCascade() {
	clearCascade();
	_cascadePan = new MenuPan();
	_cascadePan->parent( this );
	_cascadePan->_items = item(_underMouseItem)._items;
	_cascadeParent = _underMouseItem;
	float yy = 0;
	for( idx_t i=0; i<_underMouseItem; i++ ) {
		sz2_t sz = item(i).measure(nullptr);
		yy+=sz.h;
	}
	_cascadePan->position( pos_t(w()-2.f, yy) );
	_cascadePan->updateContentsRect(_JGL::getCurrentNVGContext());
	_cascadePan->reform(_JGL::getCurrentNVGContext(), autoscale_t::NONE);
}

inline idx_t MenuPan::selectedItemData() const {
	if( _cascadePan && _underMouseItem==_cascadeParent ) {
		if( _cascadePan->_underMouseItem>=0 )
		return _cascadePan->selectedItemData();
	}
	return _items[_underMouseItem].data();
}


inline bool MenuPan::handle(event_t event) {
	if( event == event_t::DRAG || event == event_t::MOVE ) {
		idx_t oldUnderMouse = _underMouseItem;
		_underMouseItem = itemUnder( _JGL::eventPt() );
		if( _underMouseItem!=oldUnderMouse ) {
			if( _underMouseItem!=_cascadeParent )
				clearCascade();
			if( _underMouseItem>=0 && isItemExpandable(_underMouseItem) )
				expandCascade();
			damage();
		}
	}
	else if( event == event_t::LEAVE ) {
		idx_t oldUnderMouse = _underMouseItem;
		_underMouseItem = -1;
		if( _underMouseItem!=oldUnderMouse ) {
			clearSelection();
			damage();
		}
	}
	else if( event == event_t::RELEASE ) {
		if( _underMouseItem>=0 ) {
			if( _menuCallback )
				_menuCallback( this, userdata(), selectedItemData() );
			_JGL::dismissPopup(this, pop_reason_t::POPUP_ACTION);
		}
		else {
			_JGL::dismissPopup(this, pop_reason_t::CLICK_OUTSIDE);
		}
	}
	if( _cascadePan )
		_JGL::dispatchEvent(_cascadePan,event);
	return Widget::handle(event);;
}


inline void MenuPan::drawBox(NVGcontext* vg, const rct_t& r) {
	_draw_menupan_box(vg,r);
}

inline void MenuPan::draw(NVGcontext* vg) {
	drawBox(vg,rct_t(0,0,w(),h()));
	float yy = topPadding();
	idx_t count = 0;
	{
		std::unique_lock<std::mutex> lock(_itemMutex);
		for( auto i: _items ) {
			sz2_t sz = i.measure(vg);
			rct_t itemRect = rct_t(0,yy,w(),sz.h);

			if( !i.isSeparator() ) {
				if( count == _underMouseItem || count == _cascadeParent )
					_draw_menupan_under_item_fill(vg, itemRect );

				nvgSave(vg);
				rct_t r( 0, 0, w()-horzPadding(), sz.h );
				nvgTranslate(vg,leftPadding(),yy);
				nvgScissor(vg, 0, 0, r.w, r.h);
				i.draw(vg, r, align_t::LEFT|align_t::TOP_BOTTOM, count == _underMouseItem);
				nvgRestore(vg);

				if( isItemExpandable(count) )
					_draw_menuitem_expandable_arrow(vg, itemRect, count == _underMouseItem, i.disabled() );

				if( count == _checkedItem ) {
					_draw_menupan_checked_item_check(vg, itemRect, count == _underMouseItem);
				}
				yy+=sz.h;
			}
			else {
				_draw_menupan_separator( vg, itemRect );
				yy+=sz.h;
			}
			count++;
		}
	}
	_draw_menupan_box_over( vg, rct_t(0,0,w(),h()) );
	if( _cascadePan ) {
		_JGL::drawAsChild(vg, _cascadePan );
	}
}


inline void MenuPan::callback( MenuPanCallback cb, void* ud) {
	_menuCallback = cb;
	_userdata = ud;
}

inline void  MenuPan::checkItem( idx_t i ) {
	_checkedItem = i;
	damage();
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* MenuPan_hpp */
