//
//  Widget.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Widget_h
#define JGL2_Widget_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <string>
#include <functional>
#include <filesystem>

#ifdef JGL2_IMPLEMENTATION
#define NANOVG_IMPLEMENTATION
#define NANOVG_GL3_IMPLEMENTATION
#define FONTSTASH_IMPLEMENTATION
#define STB_IMAGE_IMPLEMENTATION
#define STB_IMAGE_RESIZE_IMPLEMENTATION
#endif

#ifdef __APPLE__
#define GL_SILENCE_DEPRECATION
#include <opengl/gl3.h>
#endif

#ifdef _MSC_VER
#define GLEW_STATIC
#include <gl/glew.h>
#pragma comment (lib,"glew32s")
#pragma comment (lib,"opengl32.lib")
#pragma comment (lib,"glfw3.lib")
#endif

#include <JGL2/_MathTypes.hpp>
#include <nanovg/nanovg.h>

#include <JGL2/_Theme.hpp>

#include <JGL2/_MenuItem.hpp>
#include <JGL2/nanoUI.hpp>

namespace JGL2 {

struct Widget;
struct Window;
struct Group;
struct _Scrollable;
struct ButtonGroup;
struct _JGL;
struct MenuPan;
struct _MenuItem;
struct _Popup;
enum class event_t;
enum class button_t;

typedef unsigned char byte;
typedef int idx_t;

typedef std::function<void(Widget*,void*)> Callback_t;
typedef std::function<void(Widget*,void*,const slst_t&)> DNDCallback_t;
typedef std::function<void(Widget*,void*,menu_data_t)> CtxMenuCallback_t;

typedef std::function<void(NVGcontext*,const rct_t&, align_t)> DrawContCallback_t;
typedef std::function<void(const rct_t&)>		DrawGLCallback_t;

typedef std::function<bool(event_t event)>	EventCallback_t;
typedef std::function<bool(int)>			KeyCallback_t;
typedef std::function<bool(const pos_t&)>	MoveCallback_t;
typedef std::function<bool(const pos_t&)>	DragCallback_t;
typedef std::function<bool(button_t)>		PushCallback_t;
typedef std::function<bool(button_t)>		ReleaseCallback_t;
typedef std::function<bool(const pos_t&)>	ScrollCallback_t;
typedef std::function<bool(float)>			ZoomCallback_t;


struct Widget {

// This make the widget matches to the desiredRect
	virtual void		reform(NVGcontext* vg, autoscale_t scaling);
	virtual void		minSize(const sz2_t& sz);

// Following function can be called to change the properties of the Widget
	//! \brief Setting Top Padding
	//!
	virtual void		topPadding(float v);
	virtual void		bottomPadding(float v);
	virtual void		leftPadding(float v);
	virtual void		rightPadding(float v);
	virtual void		horzPadding(float v){ leftPadding(v); rightPadding(v); }
	virtual void		horzPadding(float l,float r){ leftPadding(l); rightPadding(r); }
	virtual void		vertPadding(float v){ topPadding(v); bottomPadding(v); }
	virtual void		vertPadding(float t,float b){ topPadding(t); bottomPadding(b); }
	virtual void		padding(float v){ horzPadding(v); vertPadding(v); }
	virtual void		padding(float h, float v){ horzPadding(h); vertPadding(v); }
	virtual void		padding(float l, float r, float t, float b){ leftPadding(l); rightPadding(r); topPadding(t); bottomPadding(b); }

	virtual void		alignment(align_t a);
	virtual void		autoscale(autoscale_t b);

	virtual void		labelColor(const NVGcolor& c);
	virtual void		label(const str_t& s);
	virtual void		tooltip(const str_t& s);
	virtual void		labelPt(float pt);
	
	virtual void		image(const str_t& fn);
	virtual void		image(byte* ud, int w, int h);
	virtual void		imageFit(bool b);
	virtual void		fitImage();
	virtual void		fillImage();

	
// This does not change the size of widget directly
	virtual void		resize(const pos_t& p,const sz2_t& sz);
	virtual void		resize(const rct_t& r) { resize(r.tl(),r.wh() ); }
	virtual void		size(const sz2_t& sz);
	virtual void		position(const pos_t& p);
	virtual void		x(float v){ position(pos_t(v,y())); }
	virtual void		y(float v){ position(pos_t(x(),v)); }
	virtual void		w(float v){ size(sz2_t(v,h())); }
	virtual void		h(float v){ size(sz2_t(w(),v)); }
	
// Action settings
	virtual void		activate();
	virtual void		deactivate();
	virtual void		hide();
	virtual void		show();

// animated flag is not set to the widget
// calling animate() will notify the window so it should be animated
	virtual void		animate();
	virtual void		change();
	virtual void		damage();
	virtual void		redraw() { damage(); }

	virtual void		callback( Callback_t callback, void* userdata=nullptr );
	virtual void		dndCallback( DNDCallback_t cb, void* ud=nullptr );

	virtual void 		parent( Widget* g );
	virtual Window*		window();
	virtual bool		containing(const Widget* w) const { return w==this; }
	
	
	
// Information retrival functions
// Those functions are to be used in the enclousers or subclasses
	virtual rct_t		bound() const { return rct_t(position(),size()); }
	virtual rct_t		contentsRect() const { return _contentsRect; }
	virtual sz2_t		size() const { return changed()?_setSize:_bound.wh(); }
	virtual pos_t		position() const { return _bound.tl(); }
	virtual float		x() const { return _bound.x; }
	virtual float		y() const { return _bound.y; }
	virtual float		w() const { return size().w; }
	virtual float		h() const { return size().h; }

	virtual sz2_t		minSize() const { return _minSize; }
	virtual align_t		alignment() const { return _alignment; }
	virtual float		topPadding() const { return _topPadding; }
	virtual float		bottomPadding() const { return _bottomPadding; }
	virtual float		leftPadding() const { return _leftPadding; }
	virtual float		rightPadding() const { return _rightPadding; }
	virtual float		horzPadding() const { return leftPadding()+rightPadding(); }
	virtual float		vertPadding() const { return topPadding()+bottomPadding(); }

	virtual rct_t	 	paddedRect() const { return rct_t(leftPadding(),topPadding(),w()-horzPadding(),h()-vertPadding()); }

	virtual NVGcolor	labelColor() const { return _labelColor.a>0.001?_labelColor:_color_label(); }
	virtual str_t		label() const { return _label; }
	virtual float		labelPt() const { return _labelPt>0?_labelPt:_pt_label(); }
	virtual str_t		tooltip() const { return _tooltip; }

	virtual int			labelImage() const { return _labelImage; }
	virtual size_t		labelImageWidth() const { return _labelImageSize.w; }
	virtual size_t		labelImageHeight() const { return _labelImageSize.h; }
	virtual isz_t		labelImageSize() const { return _labelImageSize; }
	virtual bool		labelImageFit() const { return _labelImageFit; }
	virtual sz2_t		measureTextLabel(NVGcontext* vg) const;

	virtual bool		active() const { return !_deactivated; }
	virtual bool		changed() const { return _changed; }
	virtual bool		hidden() const { return _hidden; }
	virtual autoscale_t	autoscale() const { return _autoscale; }

	virtual Callback_t	callback() const { return _callback; }
	virtual void*		userdata() const { return _userdata; }
	virtual DNDCallback_t	dndCallback() const { return _dndCallback; }
	virtual void*		dndUserdata() const { return _dndUserdata; }
	virtual Widget*		parent() const { return _parent; }


// Those function is used by the enclouser and the JGL
	
	virtual bool		under( const pos_t& pt ) const;
	virtual bool		under() const;
	virtual float		abs_x() const { return abs_pos().x; }
	virtual float		abs_y() const { return abs_pos().y; }
	virtual pos_t		abs_pos() const;
	virtual rct_t		abs_rect() const {return rct_t( abs_pos(), size() ); }

	virtual ~Widget();
	
	virtual irct_t		prevViewport() const { return _prevViewport; }
	virtual irct_t		prevScissor() const { return _prevScrissor; }
	
	virtual void		preDrawGL();
	virtual void		postDrawGL();
	virtual void 		setViewport() const;

	Widget(float x, float y, float width, float height, const str_t& label="" );
	Widget(const pos_t& p, const sz2_t& sz, const str_t& label="" );

	virtual void		drawCB  (DrawContCallback_t f) { _drawCB=f; }
	virtual void		unsetDrawCB() { _drawCB=defDrawCB; }

	virtual void		drawGLCB(DrawGLCallback_t f) { _drawGLCB=f; }
	virtual void		unsetDrawGLCB() { _drawGLCB=defDrawGLCB; }

// Context menu ...
	virtual void		contextMenu( MenuPan* menuPan );
	virtual void		addContextMenu( const str_t& name, menu_data_t data );
	virtual void		addContextMenu( const menuitem_list_t& menuItems );
	virtual MenuPan*	contextMenu();
	virtual ilst_t		selectedContextMenuItem() const;

	virtual void		clearContextMenu();
	virtual void		contextMenuCallback(CtxMenuCallback_t cb,void* ud=nullptr);
	virtual void		dismissContextMenu();
	virtual void		startContextMenu(const pos_t& pt);
	
	
// Callbacks
	virtual void		eventCB  (EventCallback_t f) { _eventCB=f; }
	virtual void		unsetEventCB() { _eventCB=defEventCB; }

	virtual void		moveCB  (MoveCallback_t f) { _moveCB=f; }
	virtual void		unsetMoveCB() { _moveCB=defMoveCB; }

	virtual void		dragCB  (DragCallback_t f) { _dragCB=f; }
	virtual void		unsetDragCB() { _dragCB=defDragCB; }

	virtual void		pushCB  (PushCallback_t f) { _pushCB=f; }
	virtual void		unsetPushCB() { _pushCB=defPushCB; }

	virtual void		releaseCB  (ReleaseCallback_t f) { _releaseCB=f; }
	virtual void		unsetReleaseCB() { _releaseCB=defReleaseCB; }

	virtual void		scrollCB  (ScrollCallback_t f) { _scrollCB=f; }
	virtual void		unsetScrollCB() { _scrollCB=defScrollCB; }

	virtual void		zoomCB  (ZoomCallback_t f) { _zoomCB=f; }
	virtual void		unsetZoomCB() { _zoomCB=defZoomCB; }

// Utility functions
	virtual isz_t		getWindowSize() const;

	
// NanoUI integration
	virtual bool				quickUIHandle(event_t e) { return nanoWidget::nanoUIHandle(e,quickUI()); }
	virtual bool				quickUIDraw(NVGcontext* vg) { return nanoWidget::nanoUIRender(vg,w(),h(),quickUI()); }
	virtual nanoGroup&			quickUI() { return _quickUI; }
	virtual const nanoGroup&	quickUI() const { return _quickUI; }
	virtual void				addQuickUI(nanoWidget* widget) { quickUI().add( widget ); }

// Waiting function
	virtual bool		waiting() const { return _waiting; }
	virtual void		startWaiting() { _waiting = true; _waitingCount = 0; }
	virtual void		stopWaiting() { _waiting = false; }
	
protected:
	
	virtual void		createContextMenuPan();
	virtual void		doMenuCallback(idx_t i);

	virtual bool		doCallback();
	virtual bool		doDNDCallback();
	virtual int			nvgImage(NVGcontext* vg);
	virtual NVGpaint	getImagePaint(NVGcontext* vg,const rct_t& rect,align_t align);

// Functions to override
	virtual void		drawGL();
	virtual bool		handle( event_t event );
	virtual void		drawBoxOver(NVGcontext* vg, const rct_t& r);
	virtual void		drawBox(NVGcontext* vg, const rct_t& r);
	virtual void		drawContents(NVGcontext* vg, const rct_t& r, align_t align );

// This make the widget matches to the desiredRect
	virtual void		rearrange(NVGcontext* vg, autoscale_t scaling);
	virtual void		updateContentsRect(NVGcontext* vg);

	virtual shade_state_t	shadeState() const;
	virtual void		drawImageLabel(NVGcontext* vg, const rct_t& r, align_t align );
	virtual void		drawTextLabel(NVGcontext* vg, const rct_t& r, align_t align );
	virtual void		draw(NVGcontext* vg);
	
// Geometric configuration
	rct_t						_bound;
	rct_t						_contentsRect;
	
	sz2_t						_setSize;
	sz2_t						_minSize			= sz2_t(10,10);
	float						_topPadding			= 0;
	float						_bottomPadding		= 0;
	float						_rightPadding		= 0;
	float						_leftPadding		= 0;
	autoscale_t					_autoscale			= autoscale_t::NONE;
	align_t						_alignment			= align_t::NONE;
				
// Label state
	NVGcolor					_labelColor			= {0,0,0,0};
	float						_labelPt			= -1.f;
	str_t						_label				= "";
	str_t						_tooltip			= "";
	
// Image label state
	int							_labelImage			= -1;
	str_t						_labelImageFilename	= "";
	isz_t						_labelImageSize		= isz_t(0,0);
	byte*						_labelImageData		= nullptr;
	bool						_labelImageChanged	= false;
	bool						_labelImageFit		= false;

// Action states
	bool						_deactivated		= false;
	bool						_hidden				= false;
	bool						_changed			= false;
	
// Async waiting
	bool						_waiting			= false;
	float						_waitingCount		= 0;
	
// Callbacks
	Callback_t 					_callback			= nullptr;
	void*						_userdata 			= nullptr;

	const DrawContCallback_t	defDrawCB			= [](NVGcontext*,const rct_t&,align_t){};
	const DrawGLCallback_t 		defDrawGLCB			= [](const rct_t&){};
		
	const EventCallback_t		defEventCB			= [](event_t e){ return false; };
	const MoveCallback_t		defMoveCB			= [](const pos_t& pt){ return false; };
	const DragCallback_t		defDragCB			= [](const pos_t& pt){ return false; };
	const PushCallback_t		defPushCB			= [](button_t b){ return false; };
	const ReleaseCallback_t		defReleaseCB		= [](button_t b){ return false; };
	const ScrollCallback_t		defScrollCB			= [](const pos_t& d){ return false; };
	const ZoomCallback_t		defZoomCB			= [](float f){ return false; };
	
	DrawContCallback_t			_drawCB				= defDrawCB;
	DrawGLCallback_t			_drawGLCB			= defDrawGLCB;
		
	EventCallback_t				_eventCB			= defEventCB;
	MoveCallback_t				_moveCB				= defMoveCB;
	DragCallback_t				_dragCB				= defDragCB;
	PushCallback_t				_pushCB				= defPushCB;
	ReleaseCallback_t			_releaseCB			= defReleaseCB;
	ScrollCallback_t			_scrollCB			= defScrollCB;
	ZoomCallback_t				_zoomCB				= defZoomCB;

	DNDCallback_t				_dndCallback		= nullptr;
	void*						_dndUserdata 		= nullptr;
	
	
// Hierarchial model system
	Widget*						_parent				= nullptr;

	irct_t						_prevViewport;
	irct_t						_prevScrissor;
	int							_scissorEnabled		= false;

// Context menu
	MenuPan*					_contextMenu		= nullptr;
	CtxMenuCallback_t			_contextMenuCB		= nullptr;
	void*						_contextMenuUD		= nullptr;
	
// NanoUI support
	nanoGroup					_quickUI;

	static void staticMenuCallback( Widget* w, void* ud, idx_t i) { ((Widget*)ud)->doMenuCallback(i); }

	friend		_JGL;
	friend		Group;
	friend		ButtonGroup;
	friend		_Popup;
};

struct _Targettable {
	_Targettable( bool nav=true ): _navigatable(nav) {}
	virtual bool			navigatable() const { return _navigatable; }
	virtual shade_state_t 	targettableShadeState() const;
	virtual bool			targetted() const { return _targetted; }
	virtual void			setTarget();
	virtual void			clearTarget();
	virtual void			preventTargetted() { _preventTargetted=true; }
	virtual void			allowTargetted() { _preventTargetted=false; }
	virtual bool			targettable() { return !_preventTargetted; }
	
	virtual void			keyCB  (KeyCallback_t f) { _keyCB=f; }
	virtual void			unsetKeyCB() { _keyCB=defKeyCB; }

protected:
	bool					_preventTargetted = false;
	bool					_targetted = false;
	bool					_navigatable = true;
	const KeyCallback_t		defKeyCB	= [](int code){ return false; };
	KeyCallback_t			_keyCB		= defKeyCB;
	friend Widget;
};

} // namespace JGL2

#include <JGL2/_JGL.hpp>
#include <JGL2/Window.hpp>
#include <JGL2/_Scrollable.hpp>
#include <JGL2/MenuPan.hpp>
#include <JGL2/nanoUI_impl.hpp>

namespace JGL2 {

inline Widget::Widget(float x, float y, float width, float height, const str_t& label )
: _setSize(width,height), _label(label), _bound(x,y,width,height) {
	if( _JGL::getCurrentAddingGroup() ) _JGL::addToCurrentGroup( this );
	if( parent() ) parent()->change();
	change();
}

inline Widget::Widget(const pos_t& pos, const sz2_t& sz, const str_t& label )
: _setSize(sz), _label(label), _bound(pos,sz) {
	if( _JGL::getCurrentAddingGroup() ) _JGL::addToCurrentGroup( this );
	if( parent() ) parent()->change();
	change();
}

inline Widget::~Widget() {
	if( _labelImage>=0 ) {
		NVGcontext* vg = _JGL::getCurrentNVGContext();
		if( vg ) nvgDeleteImage( vg, _labelImage );
		_labelImage = -1;
	}
}

inline void Widget::topPadding(float v) {
	if( _topPadding!=v ) {
		_topPadding = v;
		if( parent() ) parent()->change();
		change();
	}
}

inline void Widget::bottomPadding(float v) {
	if( _bottomPadding!= v ) {
		_bottomPadding = v;
		if( parent() ) parent()->change();
		change();
	}
}

inline void Widget::leftPadding(float v) {
	if( _leftPadding!=v ) {
		_leftPadding = v;
		if( parent() ) parent()->change();
		change();
	}
}

inline void Widget::rightPadding(float v) {
	if( _rightPadding!=v ) {
		_rightPadding = v;
		if( parent() ) parent()->change();
		change();
	}
}

inline void Widget::alignment(align_t a) {
	if( _alignment!=a ) {
		_alignment = a;
		change();
		damage();
	}
}
	
inline void Widget::autoscale(autoscale_t s) {
	if( _autoscale!=s ) {
		_autoscale = s;
		if( parent() ) parent()->change();
		change();
	}
}

inline void Widget::labelColor(const NVGcolor& c) {
	_labelColor = c;
	damage();
}

inline void Widget::label(const str_t& s) {
	_label = s;
	if( parent() ) parent()->change();
	change();
	damage();
}

inline void Widget::tooltip(const str_t& s) {
	_tooltip = s;
	if( parent() ) parent()->change();
	change();
	damage();
}

inline void Widget::labelPt(float pt) {
	if( _labelPt!= pt ) {
		_labelPt = pt;
		if( parent() ) parent()->change();
		change();
		damage();
	}
}

inline void Widget::image(const str_t& fn) {
	_labelImageFilename = fn;
	if( _labelImageData ) delete _labelImageData;
	_labelImageData = nullptr;
	_labelImageSize = isz_t(0,0);
	_labelImageChanged = true;
	damage();
}

inline void Widget::image(byte* ud, int w, int h) {
	if( _labelImageData ) delete _labelImageData;
	_labelImageData = new byte[w*h*4];
	for( int i=0; i<h; i++ ) memcpy( &_labelImageData[i*w*4], &ud[i*w*4], w*4);
	_labelImageSize = isz_t(int(w),int(h));
	_labelImageFilename = "";
	_labelImageChanged = true;
	damage();
}

inline void Widget::imageFit(bool b) {
	if( _labelImageFit != b ) {
		_labelImage = b;
		damage();
	}
}

inline void Widget::fitImage() {
	if( !_labelImageFit ) {
		_labelImageFit = true;
		damage();
	}
}

inline void Widget::fillImage() {
	if( _labelImageFit ) {
		_labelImageFit = false;
		damage();
	}
}

inline void Widget::position(const pos_t& p) {
	if( position().x!=p.x || position().y!=p.y ) {
		_bound.tl() = p;
		if( parent() ) parent()->change();
	}
}

inline void Widget::size(const sz2_t& sz) {
	if( size()!=sz ) {
		_setSize = sz;
		change();
	}
}

inline void Widget::resize(const pos_t& p,const sz2_t& sz) {
	position(p);
	size(sz);
}


inline void Widget::minSize(const sz2_t& sz) {
	if( _minSize!=sz ) {
		_minSize = sz;
		if( parent() ) parent()->change();
	}
}


inline void Widget::activate() {
	if( _deactivated ) {
		_deactivated = false;
		damage();
	}
}


inline void Widget::deactivate() {
	if( !_deactivated ) {
		_deactivated = true;
		damage();
	}
}

inline void Widget::hide() {
	if( !_hidden ) {
		_hidden = true;
		change();
		if( parent() ) parent()->change();
		damage();
	}
}

inline void Widget::show() {
	if( _hidden ) {
		_hidden = false;
		change();
		if( parent() ) parent()->change();
		damage();
	}
}

inline void Widget::animate() {
	if( parent() )
		parent()->animate();
}

inline void Widget::change() {
	_changed = true;
}

inline void Widget::damage() {
	if( parent() )
		parent()->damage();
}

inline void Widget::callback( Callback_t callback, void* userdata ) {
	_callback = callback;
	_userdata = userdata;
}
inline void Widget::dndCallback( DNDCallback_t cb, void* ud ) {
	_dndCallback = cb;
	_dndUserdata = ud;
}

inline void Widget::parent( Widget* w ) {
	if( parent() && parent()!=w ) {
		Group* g = dynamic_cast<Group*>(parent());
		if( g )
			g->remove( this );
	}
	_parent = w;
}

inline Window* Widget::window() {
	if( dynamic_cast<Window*>(this) )
		return dynamic_cast<Window*>(this);
	else if( parent() )
		return parent()->window();
	return nullptr;
}
	
inline bool Widget::under( const pos_t& pt ) const {
	return abs_rect().in( pt );
}

inline bool Widget::under() const {
	return under( _JGL::eventWindowPt() );
}

inline pos_t Widget::abs_pos() const {
	if( parent() ) {
		_Scrollable* scroller = dynamic_cast<_Scrollable*>(parent());
		if( scroller )
			return parent()->abs_pos()-scroller->scrollOffset()+position();
		else
			return parent()->abs_pos()+position();
	}
	return position();
}

inline shade_state_t Widget::shadeState() const {
	shade_state_t ret = shade_state_t::NORMAL;
	if( !_JGL::getCurrentDrawWindowFocused() )
		ret = ret | shade_state_t::WINDOW_UNFOCUSED;
	if( !active() )
		ret = ret | shade_state_t::INACTIVE;
	if( dynamic_cast<const _Targettable*>(this) )
		ret = ret | dynamic_cast<const _Targettable*>(this)->targettableShadeState();
	return ret;
}

inline void Widget::drawImageLabel(NVGcontext* vg, const rct_t& r, align_t align ) {
	_draw_imagelabel(vg,r,getImagePaint(vg,r,align),shadeState());
}

inline sz2_t Widget::measureTextLabel(NVGcontext* vg) const {
	return _measure_text_label(vg, label(), labelPt());
}
	
inline void Widget::drawTextLabel(NVGcontext* vg, const rct_t& r, align_t align ) {
	_draw_text_label( vg, r, labelColor(), label(), labelPt(), align, shadeState() );
}

inline NVGpaint Widget::getImagePaint(NVGcontext* vg,const rct_t& rect,align_t align) {
	float scaleX = rect.w/float(_labelImageSize.w);
	float scaleY = rect.h/float(_labelImageSize.h);
	float ww = rect.w;
	float hh = rect.h;
	float xx=0, yy=0;

	int aa = _alignment_to_NVGAlign( align );

	if( _labelImageFit ) {
		float scale = std::min( scaleX, scaleY );
		ww = _labelImageSize.w*scale;
		hh = _labelImageSize.h*scale;
		if( aa & NVG_ALIGN_CENTER )
			xx+= (rect.w-ww)*0.5f;
		else if( aa & NVG_ALIGN_RIGHT )
			xx+= (rect.w-ww);
		if( aa & NVG_ALIGN_MIDDLE )
			yy+= (rect.h-hh);
		else if( aa & NVG_ALIGN_BOTTOM )
			yy+= (rect.h-hh)*0.5f;
	}
	else {
		float scale = std::max( scaleX, scaleY );
		ww = _labelImageSize.w*scale;
		hh = _labelImageSize.h*scale;
		xx+= (rect.w-ww)*0.5f;
		yy+= (rect.h-hh)*0.5f;
	}
	return nvgImagePattern(vg, xx, yy, ww, hh, 0.0f/180.0f*NVG_PI, nvgImage(vg), 1.f);
}

inline isz_t Widget::getWindowSize() const {
	if( parent() )
		return parent()->getWindowSize();
	sz2_t sz;
	if( _JGL::eventWindow() )
		sz = _JGL::eventWindow()->size();
	else
		sz = _JGL::currentDrawWindow()->size();
	return isz_t(int(ceil(sz.w)),int(ceil(sz.h)));
}

inline bool Widget::doCallback() {
	if( callback() ) {
		callback()( this, userdata() );
		return true;
	}
	return false;
}

inline bool Widget::doDNDCallback() {
	if( dndCallback() ) {
		dndCallback()( this, dndUserdata(), _JGL::eventDND() );
		return true;
	}
	return false;
}

inline int Widget::nvgImage(NVGcontext* vg) {
	if( _labelImageChanged ) {
		if( _labelImage>=0 ) {
			nvgDeleteImage( vg, _labelImage );
			_labelImage = -1;
		}
		int image = -1;
		if( _labelImageFilename.length()>0 ) {
			image = nvgCreateImage(vg, _labelImageFilename.c_str(), 0 );
			int w, h;
			nvgImageSize(vg, image, &w, &h);
			_labelImageSize = isz_t( w, h );
		}
		else if( _labelImageSize.h>0 && _labelImageSize.w>0 && _labelImageData ) {
			image = nvgCreateImageRGBA( vg, _labelImageSize.w, _labelImageSize.h, 0, _labelImageData );
			delete _labelImageData;
			_labelImageData = nullptr;
		}
		_labelImage = image;
		_labelImageChanged = false;
	}
	return _labelImage;
}

inline void Widget::preDrawGL() {
	glGetIntegerv( GL_VIEWPORT, value_ptr(_prevViewport) );
	glGetIntegerv( GL_SCISSOR_BOX, value_ptr(_prevScrissor) );
	glGetIntegerv( GL_SCISSOR_TEST, &_scissorEnabled );

	setViewport();
}

inline void Widget::setViewport() const {
	float uiRatio = _JGL::getCurrentDrawWindowUIRatio();
	float pxRatio = _JGL::getCurrentDrawWindowPxRatio();
	int xx = int(floor(abs_x()*pxRatio*uiRatio));
	int yy = int(floor((getWindowSize().h - abs_y() - h())*pxRatio*uiRatio));
	int ww = int(ceil(w()*pxRatio*uiRatio));
	int hh = int(ceil(h()*pxRatio*uiRatio));
	
	glEnable( GL_SCISSOR_TEST );
	glViewport( xx, yy, ww, hh );
	glScissor ( xx, yy, ww, hh );
}
	
inline void Widget::postDrawGL() {
	glViewport( _prevViewport[0], _prevViewport[1], _prevViewport[2], _prevViewport[3] );
	glScissor( _prevScrissor[0], _prevScrissor[1], _prevScrissor[2], _prevScrissor[3] );
	if( _scissorEnabled )
		glEnable( GL_SCISSOR_TEST );
	else
		glDisable( GL_SCISSOR_TEST );
}

inline void Widget::draw(NVGcontext* vg) {
	rct_t r(0,0,w(),h());
	drawBox(vg,r);
	nvgSave(vg);
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
	drawContents(vg,r,alignment());
	nvgRestore(vg);
	drawBoxOver(vg,r);
	if( sc && sc->scrollDrawIndicators(vg) )
		animate();
}

inline void Widget::drawGL() {
	_drawGLCB(rct_t(x(),y(),w(),h()));
}

inline bool Widget::handle( event_t event ) {
	if( event == event_t::PUSH && _JGL::eventButton() == button_t::RBUTTON ) {
		if( _contextMenu ) {
			startContextMenu(_JGL::eventPt() );
			return true;
		}
	}
	if( _eventCB( event) ) return true;
	_Targettable* targettable = dynamic_cast<_Targettable*>(this);
	if( targettable && ( event == event_t::KEYDOWN || event == event_t::REPEAT ) )
		if( targettable->_keyCB( _JGL::eventKey() ) ) return true;
	if( event == event_t::MOVE ) 	if( _moveCB( _JGL::eventPt() ) ) return true;
	if( event == event_t::DRAG )	if( _dragCB( _JGL::eventPt() ) ) return true;
	if( event == event_t::PUSH ) 	if( _pushCB( _JGL::eventButton() ) ) return true;
	if( event == event_t::RELEASE )	if( _releaseCB( _JGL::eventButton() ) ) return true;
	if( event == event_t::SCROLL )	if( _scrollCB( _JGL::eventScroll() ) ) return true;
	if( event == event_t::ZOOM )	if( _zoomCB( _JGL::eventZoom() ) ) return true;

	return false;
}

inline void Widget::drawBoxOver(NVGcontext* vg, const rct_t& r) {
	if( waiting() ) {
		JGL2::drawCircularWait(vg, r, _waitingCount );
		_waitingCount+=1/60.f;
		if( _waitingCount>=1) _waitingCount = 0;
		animate();
	}
}

inline void Widget::drawBox(NVGcontext* vg, const rct_t& r) {
}

inline void Widget::drawContents(NVGcontext* vg, const rct_t& r, align_t a ) {
	if( nvgImage(vg)>=0 )
		drawImageLabel(vg,r,a);
	else
		drawTextLabel(vg,r,a);
	_drawCB(vg,r,a);
}

inline void Widget::reform(NVGcontext* vg, autoscale_t scaling) {
	rearrange(vg, scaling);
	_changed = false;
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		sc->scrollRange(bound().wh(), contentsRect(), alignment() );
}

inline void Widget::rearrange(NVGcontext* vg, autoscale_t scaling ) {
	if( changed() ) {
		autoscale_t sc = scaling&autoscale();
		updateContentsRect(vg);
		if( (sc & autoscale_t::W)!=autoscale_t::NONE ) {
			_setSize.w = contentsRect().w;
		}
		if( (sc & autoscale_t::H)!=autoscale_t::NONE ) {
			_setSize.h = contentsRect().h;
		}
		_bound.wh() = max(_setSize, minSize() );
	}
}

inline void Widget::updateContentsRect(NVGcontext* vg) {
//	if( autoscale() )
//		_contentsRect.wh() = measureTextLabel(vg)+dim2(horzPadding(),vertPadding());
//	else
//		_contentsRect.wh() = size();
	rct_t r;
	r.tl()=pos_t(0,0);
	if( nvgImage(vg)>=0 ) {
		float scaleX = labelImageWidth()/paddedRect().w;
		float scaleY = labelImageHeight()/paddedRect().h;
		float scale;
		if( _labelImageFit )
			scale = std::min( scaleX, scaleY );
		else
			scale = std::max( scaleX, scaleY );
		r.wh() = sz2_t(float(labelImageWidth()),float(labelImageHeight()))*scale;
	}
	else {
		r.wh() = measureTextLabel(vg);
	}
	r.w+=horzPadding();
	r.h+=vertPadding();
	_contentsRect = r;
}

inline void Widget::createContextMenuPan() {
	if( _contextMenu ) return;
	_contextMenu = new MenuPan();
	_contextMenu->parent(nullptr);
	_contextMenu->callback( staticMenuCallback, this );
}

inline void Widget::contextMenuCallback( CtxMenuCallback_t cb, void* ud ) {
	_contextMenuCB = cb;
	_contextMenuUD = ud;
}

inline void Widget::contextMenu( MenuPan* menuPan ){
	_contextMenu = menuPan;
}

inline void	Widget::addContextMenu( const str_t& name, int data ) {
	if( !_contextMenu ) createContextMenuPan();
	_contextMenu->add( _MenuItem(name,data) );
}

inline void	Widget::addContextMenu( const menuitem_list_t& menuItems ){
	if( !_contextMenu ) createContextMenuPan();
	_contextMenu->add( menuItems );
}

inline MenuPan* Widget::contextMenu() {
	if( !_contextMenu ) createContextMenuPan();
	return _contextMenu;
}

inline void Widget::clearContextMenu() {
	dismissContextMenu();
	delete _contextMenu;
	_contextMenu = nullptr;
}

inline ilst_t Widget::selectedContextMenuItem() const {
	if( !_contextMenu ) return {};
	return _contextMenu->selectedItem();
}

inline void Widget::doMenuCallback(int i) {
	if( _contextMenuCB ) _contextMenuCB( this, _contextMenuUD, i );
}

inline void Widget::dismissContextMenu() {
	if( !_contextMenu ) return;
	_JGL::dismissPopup( window(), pop_reason_t::ALL );
	_contextMenu->clearSelection();
}

inline void Widget::startContextMenu( const pos_t& pt ) {
	if( !_contextMenu ) return;
	_JGL::startPopup(_contextMenu, this, pt+pos_t(2,2));
}


inline void _Targettable::setTarget() {
	_targetted = true;
	Widget* w = dynamic_cast<Widget*>(this);
	if( w ) w->damage();
}

inline void _Targettable::clearTarget() {
	_targetted = false;
	Widget* w = dynamic_cast<Widget*>(this);
	if( w ) w->damage();
}

inline shade_state_t _Targettable::targettableShadeState() const {
	if( _targetted )	return shade_state_t::TARGETTED;
	else				return shade_state_t::NORMAL;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Widget_h */
