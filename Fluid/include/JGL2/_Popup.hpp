//
//  _Popup.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__Popup_hpp
#define JGL2__Popup_hpp

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>

namespace JGL2 {

//* Special Widget wrapper to make it as a popup
//* It stores the information of popup
//*
//* Wrapped functions includes:
//*		bool changed() const;
//*		bool damaged() const;
//*		void rearrange();
//* Additional fields and functions are
//*		DismissReason _dismissReason=REASON_ALL;
//*			decide when the popup will be dismissed
//*
//*		Widget* _content = nullptr;
//*			The content widget, which can be virtually any Widget
//*			This is set by the contructor only for integraty
//*			That is why there is no setter and getter
//*
//*		Widget* _parent = nullptr;
//*			The parent Widget of the popup.
//*			The position of the popup will be computed based on the parent,
//*			and so does mouse position event.
//*			Moreover, "dismiss" will be propagate to the parent with
//*			the proper Reason.
//*
//*		bool    _mouseOnPopup = false;
//*			The flag corresponding to whether the mouse is on the popup
//*			This flag is used only for enter/leave event and auto dismissal.
//*
//*		bool	_mouseEverOnPopup = false;
//*			This flag is used only for auto dismissal.

struct _PopupHandler;
struct _JGL;

struct _Popup {
	bool			changed() const;
	bool			damaged() const;
	void			reform(NVGcontext*vg, autoscale_t scaling);
	void			size(const sz2_t& sz);
	bool			under() const;
	bool			under(const pos_t& pt) const;
	void			draw(NVGcontext* vg);

	void			dispatchEvent( event_t e );
	void			dismiss();
	
protected:

	_Popup(Widget* content=nullptr, Widget* parent=nullptr, pop_reason_t r=pop_reason_t::ALL);

	Widget*			underWidget(const pos_t& pt) const;
	Widget*			contents() const { return _content; }

	Widget*			_content = nullptr;
	Widget* 		_parent = nullptr;
	bool			_mouseOnPopup = false;
	bool			_mouseEverOnPopup = false;
	pop_reason_t	_dismissReason=pop_reason_t::ALL;
	
	friend 			_PopupHandler;
	friend			Window;
	friend			_JGL;
};

//* A supportive method set to handle (multiple/hierarchical) popups
//* This struct can be inherited by (virtual) any widget,
//* but in current implementaion of JGL::JGL (main runner),
//*  Window inherites PopupHandler and calls "draw(vg)" for it.
//* Also, JGL::JGL refers its list of "Windows" to find the right handler.
//*
//* The major functions of this handler are
//* 1. managing popup list
//*		std::vector<Popup> _popups;
//*			The real list of the popups
//*
//*		virtual bool hasPopup() const
//*			If the handler has one or more popups
//*
//*		virtual bool hasPopup(Popup* p) const
//*			If the handler has a particular popup
//*
//*		virtual Popup* matchingPopup(Widget* w)
//*			Find and return the popup that has the "w" as its "_content" if any.
//*
//*		virtual void addPopup( Popup p )
//*			Add new popup to the list.
//*			Of course only JGL::JGL should call it through "startPopup()"
//*
//*		virtual void removePopup( Popup* p )
//*			Remove the popup from the list.
//*			This function should be called only from "dismissPopup()"
//*
//*
//* Wrapped functions includes:
//*		virtual bool popupChanged() const;
//*		virtual bool popupDamaged() const;
//*		virtual void popupRearrange();
//*		virtual void popupDraw(NVGcontext*);
//*			Those functions calls the corresponding function of the
//*			content Widgets and collect the return values.
//*			with exception of "popupHandle()."
//*
//*		virtual bool popupHandle(int event) {
//*			"popupHandle()" actually handles events:
//*			a. check if the mouse is on the top most popup.
//*			b. if so, dispatch event to the popup
//*			c. produce enter/leave event
//*			d. detect the mouse click outside of the topmost widget for auto dismissal.
//*
//*		virtual void dismissPopup(Popup* p, DismissReason reason)
//*			The basic form of dismissal function.
//*			Try to dismiss the Popup with the given reason.
//*
//*			Internally, if there is sufficient reason, it dismiss the popup,
//*			and then, convert the reason to "child-" reason form to send
//*			to its parent, because some popups are affected (dismissed)
//*			by the child popup's dismissal.
//*
//*		virtual void dismissPopup(Widget* w, DismissReason reason)
//*			This variant is for "Widget" level dismissal.
//*			By sending "_content" widget as "w", the corresponding popup
//*			will be dismissed.
//*			This would be useful to dismiss a popup in "handle()" function.
//*
//*		virtual void dismissPopups(DismissReason reason)
//*			Try to dismiss each popup due to the window-wise event,
//*			such as "window-unfocused" or ESC key.
//*

struct _PopupHandler {
	
	virtual bool			hasPopup() const;
	virtual bool			hasPopup(_Popup* p) const;
	virtual const _Popup*	matchingPopup(Widget* w) const;
	virtual _Popup*			matchingPopup(Widget* w);

	virtual bool			popupChanged() const;
	virtual void			popupReform(NVGcontext* vg,autoscale_t scaling);
	virtual void			popupDraw(NVGcontext* vg);
	virtual bool			popupHandle(event_t event);
	virtual Widget*			popupUnderWidget(const pos_t& pt) const;

	virtual void			dismissPopup(_Popup* p, pop_reason_t reason);
	virtual void			dismissPopups(pop_reason_t reason);
	virtual void			dismissPopup(Widget* w, pop_reason_t reason);

protected:
	virtual void			addPopup( _Popup p );
	popup_list_t			_popups;

private:
	virtual void			removePopup( _Popup* p);
	
	friend _JGL;
};

} // namespace JGL2

#include <JGL2/Window.hpp>

namespace JGL2 {

inline _Popup::_Popup(Widget* content, Widget* parent, pop_reason_t r)
:_content(content), _parent(parent),
_dismissReason(r), _mouseOnPopup(false), _mouseEverOnPopup(false) {
	if( _content ) _content->parent(parent);
}

inline void _Popup::dispatchEvent( event_t e ) {
	_JGL::dispatchEvent(_content, e);
}

inline bool _Popup::changed() const {
	return _content?_content->changed():false;
}

inline void _Popup::reform(NVGcontext*vg,autoscale_t scaling) {
	_content->reform(vg,autoscale_t::ALL);
}

inline void _Popup::size(const sz2_t& sz) {
	_content->size(sz);
}

inline bool _Popup::under() const {
	return _content?_content->under():false;
}

inline bool _Popup::under(const pos_t& pt) const {
	return _content?_content->under(pt):false;
}

inline Widget* _Popup::underWidget(const pos_t& pt) const {
	if( _content ) {
		Group* g = dynamic_cast<Group*>(_content );
		if( g ) {
			Widget* ret = g->underWidget(pt);
			if( ret ) return ret;
		}
		if( _content->under(pt) )
			return _content;
	}
	return nullptr;
}

inline void _Popup::draw(NVGcontext* vg) {
	if( _content && !_content->hidden() ) {
		nvgSave(vg);
		pos_t dx(0,0);
		if( _parent )
			dx = _parent->abs_pos();
		nvgTranslate(vg, dx.x, dx.y);
		_JGL::drawAsChild(vg,_content);
		nvgRestore(vg);
	}
}

inline bool _PopupHandler::popupChanged() const{
	for( auto& p: _popups )
		if( p.changed() ) return true;
	return false;
}

inline void _PopupHandler::popupReform(NVGcontext* vg,autoscale_t scaling) {
	for( auto& p: _popups )
		p.reform(vg,scaling);
}

inline void _PopupHandler::addPopup( _Popup p ) {
	_popups.push_back(p);
}

inline void _PopupHandler::removePopup( _Popup* p) {
	auto pos = std::find_if(_popups.begin(), _popups.end(), [&](auto& pp){ return (&pp)==p; });
	_popups.erase(pos);
}

inline bool _PopupHandler::hasPopup() const {
	return _popups.size()>0;
}

inline bool _PopupHandler::hasPopup(_Popup* p) const {
	for( auto& pop :_popups ) {
		if( &pop == p ) return true;
	}
	return false;
}

inline _Popup* _PopupHandler::matchingPopup(Widget* w) {
	for( auto& pop :_popups ) {
		if( pop.contents()->containing(w) ) return &pop;
	}
	return nullptr;
}

inline const _Popup* _PopupHandler::matchingPopup(Widget* w) const {
	for( auto& pop :_popups ) {
		if( pop.contents()->containing(w) ) return &pop;
	}
	return nullptr;
}

inline void _PopupHandler::dismissPopups(pop_reason_t reason) {
	for(auto p = _popups.rbegin(); p!= _popups.rend(); ++p )
		dismissPopup( &(*p), reason );
}

inline void _PopupHandler::dismissPopup(Widget* w, pop_reason_t reason) {
	_Popup* p = matchingPopup(w);
	if( p ) dismissPopup( p, reason);
}

inline void _PopupHandler::dismissPopup(_Popup* p, pop_reason_t reason) {
	// Check if the popup is one of the handlees
	if( !hasPopup(p) ) return;
	
	// Check if the reason is sufficient to dismiss
	if( (int)p->_dismissReason & (int)reason ) {
		
		// Start dismissal
		Widget* parentWidget = p->_parent;
		p->dismiss();
		removePopup(p);
		Widget* handlerWidget = dynamic_cast<Widget*>(this);
		if( handlerWidget )
			handlerWidget->damage();
		
		// Then propagate the dismissal sequence to the parent
		//  for the popups that are eventually dismissed when a child get "ACTION".
		//  Ex. cascaded menu pan
		pop_reason_t reasonForParent=pop_reason_t::NONE;
		if( (int)reason & (int)pop_reason_t::CLICK_OUTSIDE )
			reasonForParent = pop_reason_t::CHILD_CANCEL;
		if( (int)reason & (int)pop_reason_t::POPUP_ACTION )
			reasonForParent = pop_reason_t::CHILD_ACTION;
		if( reasonForParent!=pop_reason_t::NONE ) {
			_Popup* parentPopup = matchingPopup(parentWidget);
			if( parentPopup )
				dismissPopup(parentPopup,reasonForParent);
		}
	}
}

inline Widget* _PopupHandler::popupUnderWidget(const pos_t& pt) const {
	for( auto p=_popups.rbegin(); p!=_popups.rend(); p++ ) {
		Widget* ret = p->underWidget(pt);
		if( ret ) return ret;
	}
	return nullptr;
}

inline void _PopupHandler::popupDraw(NVGcontext* vg) {
	for(auto& p : _popups )
		p.draw(vg);
}

inline bool _PopupHandler::popupHandle(event_t event) {
	for( idx_t i=idx_t(_popups.size())-1; i>=0; i-- ) {
		_Popup& p = _popups[i];
		if( p.under()) {
			// TODO: First send ENTER if needed
			if( event == event_t::MOVE || event == event_t::DRAG ) {
				if( !p._mouseOnPopup ) {
					p.dispatchEvent( event_t::ENTER );
				}
				p._mouseEverOnPopup = true;
			}
			p._mouseOnPopup = true;
			if( p._mouseEverOnPopup ) {
				_JGL::dispatchEvent( p._content, event );
				return true;
			}
			//if( ret ) return true;
		}
		else {
			if( p._mouseOnPopup )
				p.dispatchEvent( event_t::LEAVE );
			p._mouseOnPopup = false;
		}
		if( event == event_t::PUSH && !p._mouseOnPopup )
			dismissPopup(&p, pop_reason_t::CLICK_OUTSIDE);
		if( event == event_t::RELEASE && !p._mouseOnPopup && p._mouseEverOnPopup )
			dismissPopup(&p, pop_reason_t::CLICK_OUTSIDE);
	}
	return true;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _Popup_hpp */
