//
//  Group.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef Group_h
#define Group_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <mutex>
#include <functional>
#include <JGL2/Widget.hpp>
#include <JGL2/_Scrollable.hpp>

namespace JGL2 {

struct Group: public Widget, public _Scrollable {
	
	Group(float x, float y, float w, float h, const str_t& label="");
	Group(const pos_t& pos, const sz2_t& sz, const str_t& label="");
	
	inline size_t			children() const { return _children.size(); }
	inline Widget*			child(int i) const { return _children[i]; }
	virtual void			add( Widget* w );
	virtual void			add( Widget& w ) { add(&w); }
	virtual void			remove( Widget* w );
	virtual void			clear( bool erase=true );
	virtual void			end();
	
	virtual Widget*			underMouse();
	virtual Widget*			underWidget(const pos_t& pt);
	
	virtual	bool			changed() const override;
	
	virtual	bool			containing(const Widget* w) const override;
	virtual	void			forAllChild( std::function<void(Widget*)> func ) { for( auto c: _children) func(c); }


protected:
	
	virtual void			drawContents(NVGcontext* vg, const rct_t& r, align_t alignment) override;
	virtual void			drawBox(NVGcontext* vg, const rct_t& r) override;
	virtual void			drawBoxOver(NVGcontext* vg, const rct_t& r) override;
	virtual bool			handle( event_t event ) override;
	
	virtual void			updateContentsRect(NVGcontext* vg) override;
	virtual void			rearrange(NVGcontext* vg,autoscale_t scaling) override;
	
	
	virtual idx_t			searchChild( Widget* w ) const;
	
	virtual bool			propagateEvent( event_t event );
	virtual void			recursiveDrawGL();
	virtual void			rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling);

	widget_list_t			_children;
	mutable std::mutex		_childMutex;
	
	friend _JGL;
};

inline Group::Group(float x, float y, float w, float h, const str_t& label )
: Widget( x, y, w, h, label ) {
	_JGL::pushAddingGroup( this );
}

inline Group::Group(const pos_t& pos, const sz2_t& sz, const str_t& label )
: Widget( pos,sz, label ) {
	_JGL::pushAddingGroup( this );
}

inline idx_t Group::searchChild( Widget* w ) const {
	std::unique_lock<std::mutex> lock(_childMutex);
	for( size_t i=0; i<children(); i++ )
		if( _children[i] == w ) return idx_t(i);
	return -1;
}

inline void Group::add( Widget* w ) {
	if( searchChild( w ) <0 ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		_children.push_back( w );
		if( w ) w->parent( this );
		change();
	}
}

inline void Group::remove( Widget* w ) {
	std::unique_lock<std::mutex> lock(_childMutex);
	auto i = _children.begin();
	for( ; i<_children.end(); i++ )
		if( (*i) == w ) break;
	if( i<_children.end()) {
		_children.erase( i );
		change();
	}
}

inline void Group::clear( bool erase ) {
	if( erase ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto& c: _children ) if( c )
			delete c;
	}
	_children.clear();
	change();
}

inline void Group::end() {
	_JGL::popAddingGroupUntil( this );
}

inline bool Group::changed() const {
	if( _changed ) return true;
	for( auto c: _children ) if( c ) {
		if( c->changed() ) return true;
	}
	return false;
}

inline bool Group::containing(const Widget* w) const {
	if( Widget::containing(w) ) return true;
	std::unique_lock<std::mutex> lock(_childMutex);
	for( auto c: _children ) if( c ) {
		if( c->containing(w) ) return true;
	}
	return false;
}

inline Widget* Group::underMouse() {
	return underWidget( _JGL::eventWindowPt() );
}

inline Widget* Group::underWidget(const pos_t& pt) {
	if( under(pt) ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto& c: _children ) if( c ) {
			Group* g = dynamic_cast<Group*>(c);
			if( g ) {
				Widget* ret = g->underWidget(pt);
				if( ret )
					return ret;
			}
			if( c->under(pt) )
				return c;
		}
		return this;
	}
	return nullptr;
}

inline void Group::drawBox(NVGcontext* vg, const rct_t& r) {
	nvgSave( vg );
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
	std::unique_lock<std::mutex> lock(_childMutex);
	for( auto c : _children ) if( c && !c->hidden() ) {
		nvgSave( vg );
		nvgTranslate( vg, c->x(), c->y() );
		nvgIntersectScissor( vg, 0, 0, c->w(), c->h() );
		c->drawBox(vg,rct_t(0,0,c->w(), c->h()));
		nvgRestore(vg);
	}
	nvgRestore(vg);
}

inline void Group::drawBoxOver(NVGcontext* vg, const rct_t& r) {
	nvgSave( vg );
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
	std::unique_lock<std::mutex> lock(_childMutex);
	for( auto c : _children ) if( c && !c->hidden() ) {
		nvgSave( vg );
		nvgTranslate( vg, c->x(), c->y() );
		nvgIntersectScissor( vg, 0, 0, c->w(), c->h() );
		nvgSave( vg );
		c->drawBoxOver(vg,rct_t(0,0,c->w(), c->h()));
		nvgRestore(vg);
		_Scrollable* sc = dynamic_cast<_Scrollable*>(c);
		if( sc && sc->scrollDrawIndicators(vg) )
			animate();
		nvgRestore(vg);
	}
	nvgRestore(vg);
	Widget::drawBoxOver(vg,r);
}

inline void Group::drawContents(NVGcontext* vg, const rct_t& r, align_t align ) {
	std::unique_lock<std::mutex> lock(_childMutex);
	for( auto c : _children ) if( c && !c->hidden() ) {
		nvgSave( vg );
		nvgTranslate( vg, c->x(), c->y() );
		nvgIntersectScissor( vg, 0, 0, c->w(), c->h() );
		_Scrollable* sc = dynamic_cast<_Scrollable*>(c);
		if( sc )
			nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
		if( c->quickUIDraw(vg) ) c->animate();
		c->drawContents(vg,rct_t(0,0,c->w(), c->h()),c->alignment());
		nvgRestore(vg);
	}
//	Widget::drawContents(vg,r,align);
}

inline void Group::recursiveDrawGL() {
	preDrawGL();
	drawGL();
	postDrawGL();

	std::unique_lock<std::mutex> lock(_childMutex);
	for( auto c : _children ) if( c ){
		Group* g = dynamic_cast<Group*>(c);
		if( g ) {
			g->recursiveDrawGL();
		}
		else {
			c->preDrawGL();
			c->drawGL();
			c->postDrawGL();
		}
	}

}

inline bool Group::propagateEvent( event_t event ) {
//	if( _focused && JGL::dispatchEvent( _focused, event ) )
//		return true;

//	std::unique_lock lock(_childMutex);
	for( auto c: _children ) if( c ){
		if( !c->hidden() && c->active() && c->under() && _JGL::dispatchEvent( c, event ) ) {
//			focused(a);
			return true;
		}
	}
//	focused(nullptr);
	return false;
}

inline bool Group::handle( event_t event ) {
	return false;
}



inline void Group::rearrangeChildren(NVGcontext* vg,const rct_t& r, autoscale_t scaling) {
	std::unique_lock<std::mutex> lock(_childMutex);
	if( children()== 1 && child(0)->x()==r.x && child(0)->y()==r.y ) {
		sz2_t sz = child(0)->size();
		if( contains(alignment(),align_t::LEFT) && contains(alignment(),align_t::RIGHT))
			sz.w = r.w-horzPadding();
		if( contains(alignment(),align_t::TOP ) && contains(alignment(),align_t::BOTTOM))
			sz.h = r.h-vertPadding();
		child(0)->resize( pos_t(leftPadding(),topPadding()), sz );
		child(0)->reform(vg,autoscale_t::NONE);
	}
}

inline void Group::updateContentsRect(NVGcontext* vg) {
	if( children()<1 ) {
		Widget::updateContentsRect(vg);
		return;
	}
	
	rct_t b(0,0,-1,-1);
	{
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c : _children ) if(c && !c->hidden() ){
			if( b.h<0 ) b = c->bound();
			else b.increase( c->bound() );
		}
	}
	b.x-=leftPadding();
	b.y-=topPadding();
	b.w+=horzPadding();
	b.h+=vertPadding();
	_contentsRect = b;
}

inline void Group::rearrange(NVGcontext* vg, autoscale_t scaling) {
	{
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			if( c->changed() ) c->reform(vg,autoscale_t::ALL);
		}
	}
	if( changed() ) {
		rearrangeChildren(vg, paddedRect(),scaling );
		Widget::rearrange(vg,scaling);
	}
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Group_h */
