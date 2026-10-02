//
//  Window.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Window_h
#define JGL2_Window_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
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

#undef NANOVG_GL3
#define NANOVG_GL3 1
#include <nanovg/nanovg.h>
#include <nanovg/nanovg_gl.h>
#include <GLFW/glfw3.h>

#include <JGL2/_MathTypes.hpp>
#include <JGL2/Group.hpp>
#include <JGL2/_Popup.hpp>
#include <JGL2/SCMS.hpp>
#include <JGL2/MenuPan.hpp>

namespace JGL2 {

struct Window : public Group, public _PopupHandler {
	Window( float width, float height, const str_t& title );
	Window( const sz2_t& sz, const str_t& title );
	virtual void		enableHDR();
	virtual color_t		windowGamma() const;
	virtual colorMat_t	windowColorMat() const;

	virtual void		show() override;
	virtual void		hide() override;
	virtual void		close();
	virtual void		label( const str_t& l ) override;
	virtual void		damage() override { _damaged = true; }
	virtual void		animate() override { _animated = true; }
	virtual void		clearDamaged() { _damaged = false; }
	virtual void		clearAnimated() { _animated = false; }

	virtual void		targetWidget( Widget* w );
	virtual void		clearTargetWidget();
	virtual bool		moveToNextTargetWidget();
	virtual bool		moveToPrevTargetWidget();

	GLFWwindow*			glfwWindow() const { return _glfwWindow; }
	GLFWwindow*			nativeWindow() const { return _glfwWindow; }
	NVGcontext*			nvgContext() const { return _vg; }
	float				pxRatio() const { return _pxRatio; }
	float				uiRatio() const { return _uiRatio; }

	virtual bool		isFocused() const { return _isFocused; }
	virtual bool		animated() const { return _animated; }
	virtual bool		damaged() const { return _damaged; }
	virtual bool		destroyed() const { return _destroyed; }

	virtual float		abs_x() const override { return 0; }
	virtual float		abs_y() const override { return 0; }
	virtual isz_t		getWindowSize() const override;


	virtual bool		shoudClosed() { return glfwWindowShouldClose( _glfwWindow ); }
	virtual void		reform(NVGcontext* vg, autoscale_t scaling) override;

	virtual Widget*		underWidget(const pos_t& pt) override;
	virtual float		underWidgetChangedTimestamp() const { return _underWidgetChangedTimestamp; }
	
	virtual Widget* 	targetWidget() const;
	virtual void		uiRatio(float ratio, bool changePhysicalWindowSize=false);

protected:
	
	virtual void		destory();
	virtual void		updateUnderWidget(const pos_t& pt,float timestamp);
	virtual void		dismissTooltip();
	virtual void		startTooltip();
	virtual bool		handle(event_t event) override;

	
	virtual void		draw(NVGcontext* vg) override;
	virtual void		render();
	virtual void		isFocused(bool a) { _isFocused = a; }
	
	bool				_enableHDR		= false;
	color_t				_windowGamma	= color_t(2.4f);
	colorMat_t			_windowColorMat	= colorMat_t(1);
	float				_windowsHDRGain = 3.2f;
		
	GLFWwindow* 		_glfwWindow		= nullptr;
	GLFWcursor*			_currentCursor	= nullptr;
	bool				_destroyed		= true;
	bool				_isFocused		= false;
	bool				_animated		= false;
	bool				_damaged		= false;
	
	NVGcontext*			_vg				= nullptr;
	float				_pxRatio		= 1.f;
	float				_uiRatio		= 1.f;
		
	Widget*				_currentTarget	= nullptr;
	
	rct_t				_tooltipBox;
	float				_tooltipDx		= 0;
	str_t				_tooltipString	= "";
	bool				_tooltipEngaged	= false;
	float				_tooltipAlpha	= 0.f;
	const Widget*		_underWidget	= nullptr;
	float				_underWidgetChangedTimestamp = 0;
	
	sz2_t				_lastRenderSz   = sz2_t(0,0);
	friend _JGL;
	
	static void			nvgRegisterDefaultFonts( NVGcontext* vg, const str_t& path );

};

inline void	_Popup::dismiss() {
	_JGL::sendEvent(_content, event_t::POPUP_DISMISSED);
	if( _content ) {
		if( dynamic_cast<MenuPan*>(_content) ) dynamic_cast<MenuPan*>(_content)->clearSelection();
		Window* win = _content->window();
		if( !win )
			win = _parent->window();
		if( win && _content->containing( win->targetWidget() ) ) {
			win->clearTargetWidget();
		}
	}
}

} // namespace JGL2

#include "_Draw.hpp"
#include "PopupBox.hpp"

namespace JGL2 {


const float _def_time_tooltip_hold_to_start = 1.f;
const float _def_time_tooltip_delayed_dismissal = .4f;

inline idx_t findWidgetIndex( Group* prnt, Widget* w ) {
	idx_t idx = -1;
	for( idx_t i=0; i<prnt->children(); i++ ) {
		if( prnt->child(i)==w) { idx = i; break; }
	}
	return idx;
}

inline Widget* findFirstTargettable( const Group* g, int start=0 ) {
	for(int i=start; i<g->children(); i++ ) {
		Widget* c = g->child(i);
		_Targettable* t = dynamic_cast<_Targettable*>(c);
		if( t && t->targettable() && c->active() && t->navigatable() ) return c;
		Group* gg = dynamic_cast<Group*>(c);
		if( gg ) {
			Widget* ret = findFirstTargettable( gg );
			if( ret ) return ret;
		}
	}
	return nullptr;
}

inline Widget* findNextTargettable( Widget* w) {
	Group* prnt = dynamic_cast<Group*>(w->parent());
	if( !prnt ) return nullptr;
	idx_t idx = findWidgetIndex( prnt, w );
	if( idx<0 ) return nullptr;

	while( true ) {
		Widget* t = findFirstTargettable( prnt, idx+1 );
		if( t ) return t;
		Widget* oldP = prnt;
		prnt = dynamic_cast<Group*>(prnt->parent());
		if( !prnt ) return nullptr;
		idx = findWidgetIndex( prnt, oldP );
	}
}

inline Widget* findLastTargettable( const Group* g, int start=1000000000 ) {
	if( start>=(int)g->children() ) start = idx_t(g->children())-1;
	for(int i=start; i>=0; i-- ) {
		Widget* c = g->child(i);
		_Targettable* t = dynamic_cast<_Targettable*>(c);
		if( t && t->targettable() && c->active() && t->navigatable() ) return c;
		Group* gg = dynamic_cast<Group*>(c);
		if( gg ) {
			Widget* ret = findLastTargettable( gg );
			if( ret ) return ret;
		}
	}
	return nullptr;
}

inline Widget* findPrevTargettable( Widget* w) {
	Group* prnt = dynamic_cast<Group*>(w->parent());
	if( !prnt ) return nullptr;
	idx_t idx = findWidgetIndex( prnt, w );
	if( idx<0 ) return nullptr;

	while( true ) {
		Widget* t = findLastTargettable( prnt, idx-1 );
		if( t ) return t;
		Widget* oldP = prnt;
		prnt = dynamic_cast<Group*>(prnt->parent());
		if( !prnt ) return nullptr;
		idx = findWidgetIndex( prnt, oldP );
	}
}


inline Window::Window( float width, float height, const str_t& title )
: Group( 0, 0, width, height, title ){
	_JGL::registerWindow( this );
}

inline Window::Window( const sz2_t& sz, const str_t& title )
: Group( pos_t(0,0), sz, title ){
	_JGL::registerWindow( this );
}


inline void Window::enableHDR() {
	_enableHDR = true;
}
inline color_t Window::windowGamma() const {
	return _windowGamma;
}
inline colorMat_t Window::windowColorMat() const {
	return _windowColorMat;
}

#ifdef _MSC_VER
#define WIN32_STYLE_UI_SCALE
#endif

inline void Window::show() {
	if( !_glfwWindow ) {
		glfwInit();
#ifdef __glfw3_joony_custom__
		glfwSetOpenDocumentCallback(_JGL::sOpenDocumentCB);
#endif
#ifdef __APPLE__
#ifdef GL2
		glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 2);
		glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
#else
		glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
		glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
		glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);
		glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, true);
		glfwWindowHint(GLFW_COCOA_CHDIR_RESOURCES, true);
		glfwWindowHint(GLFW_COCOA_MENUBAR, true);
#endif
#endif
		if( _enableHDR ) {
			glfwWindowHint(GLFW_RED_BITS, 16);
			glfwWindowHint(GLFW_GREEN_BITS, 16);
			glfwWindowHint(GLFW_BLUE_BITS, 16);
		}
		glfwWindowHint(GLFW_SAMPLES, 4);

		_bound.wh() = _setSize;
		_bound.tl() = pos_t(0,0);

#ifdef WIN32_STYLE_UI_SCALE
		GLFWmonitor* mon = glfwGetPrimaryMonitor();
		float scaleX, scaleY;
		glfwGetMonitorContentScale(mon, &scaleX, &scaleY);
		printf("Monitor scale: %f %f\n", scaleX, scaleY);
		_uiRatio = std::min(scaleX, scaleY);
#endif
		int windowW = int(ceil(size().w*_uiRatio));
		int windowH = int(ceil(size().h*_uiRatio));
		_glfwWindow = glfwCreateWindow( windowW, windowH, _label.c_str(),
									   0, _JGL::getShaderableContext() );
		_JGL::registerWindowCallbacks(this);
		glfwMakeContextCurrent(_glfwWindow);
#ifdef _MSC_VER
		glewInit();
		glEnable(GL_FRAMEBUFFER_SRGB);
#endif

#ifdef GL2
		_vg = nvgCreateGL2(NVG_ANTIALIAS|NVG_STENCIL_STROKES | NVG_DEBUG);
#else
//		_vg = nvgCreateGL3(NVG_ANTIALIAS|NVG_STENCIL_STROKES | NVG_DEBUG);
		_vg = nvgCreateGL3(NVG_ANTIALIAS|NVG_DEBUG);
#endif
//		_vg = nvgCreateGL3(NVG_DEBUG);
		nvgRegisterDefaultFonts( _vg, "Res");

		_hidden = false;
		_destroyed = false;
		end();
		damage();
		glfwFocusWindow(_glfwWindow);
		_JGL::windowFocusCallback( _glfwWindow, GLFW_FOCUSED );
		glfwSwapInterval(1);
	}
	else if( _hidden ) {
		glfwShowWindow(_glfwWindow);
	}
	Widget* target = findFirstTargettable(this);
	if( target ) targetWidget( target );
}

inline void Window::close() {
	glfwSetWindowShouldClose(_glfwWindow, true);
}

inline void Window::destory() {
	_destroyed = true;
	glfwMakeContextCurrent(_glfwWindow);
	glfwDestroyWindow( _glfwWindow );
	glfwPollEvents();
	_glfwWindow = nullptr;
}

inline color_t windowColor( Widget* widget, const color_t& color ) {
	Window* win = widget->window();
	if( win ) return tonemap( win->windowColorMat()*invTonemap(color,2.4f), win->windowGamma() );
	else printf("Window is null!!\n");
	return color;
}

inline colora_t windowColor( Widget* widget, const NVGcolor& c ) {
	return colora_t( windowColor( widget, color_t(c.r,c.g,c.b) ), c.a );
}



inline void Window::render() {
	_windowColorMat = colorMat_t(1);
	_windowGamma = color_t(2.4f);
#ifdef _WIN32
	_windowGamma = color_t(1);
	if( _enableHDR )
		_windowColorMat = colorMat_t(_windowsHDRGain);
#endif
	glfwMakeContextCurrent( _glfwWindow );
	_JGL::setCurrentDrawWindow( this );
	colora_t clearColor = windowColor(this,_color_panel());
	glClearColor( clearColor.r, clearColor.g, clearColor.b, clearColor.a );
	glClear(GL_DEPTH_BUFFER_BIT|GL_COLOR_BUFFER_BIT);
	int fbw, fbh, ww, wh;
	glfwGetFramebufferSize( _glfwWindow, &fbw, &fbh );
	glfwGetWindowSize( _glfwWindow, &ww, &wh );
	_pxRatio = round(fbw/float(ww));
	glViewport( 0, 0, fbw, fbh );

	clearDamaged();
#ifdef _WIN32
		nvgBeginFrame( _vg, ww/_uiRatio, wh/_uiRatio, _pxRatio*_uiRatio );
		nvgOutputGamma(_vg,value_ptr(_windowGamma));
		nvgOutputColorMat(_vg,value_ptr(_windowColorMat));
		nvgBeginPath(_vg);
		nvgRect(_vg,0.f,0.f,float(ww),float(wh));
		nvgFillColor(_vg,_color_panel());
		nvgFill(_vg);
		nvgEndFrame(_vg);
#endif
	recursiveDrawGL();

	nvgBeginFrame( _vg, ww/_uiRatio, wh/_uiRatio, _pxRatio*_uiRatio );
	nvgOutputGamma(_vg,value_ptr(_windowGamma));
	nvgOutputColorMat(_vg,value_ptr(_windowColorMat));
	draw( _vg );
	popupDraw(_vg);
	if( _tooltipEngaged ) {
		_tooltipAlpha+=0.2f;
		if( _tooltipAlpha>1) _tooltipAlpha=1;
		else animate();
		_draw_tooltip(_vg, _tooltipBox, _tooltipDx, _tooltipString, _tooltipAlpha);
	}
	else if( _tooltipAlpha>0.f ) {
		_tooltipAlpha -=0.1f;
		if(_tooltipAlpha<0 ) _tooltipAlpha = 0.f;
		else {
			_draw_tooltip(_vg, _tooltipBox, _tooltipDx, _tooltipString, _tooltipAlpha);
			animate();
		}
	}
	nvgEndFrame( _vg );

	glfwSwapBuffers( _glfwWindow );
}
inline void Window::hide() {
	if( _glfwWindow && !_hidden )
		glfwHideWindow(_glfwWindow);
}

inline void Window::draw(NVGcontext* vg) {
	Group::draw(vg);
}

inline void Window::reform(NVGcontext* vg, autoscale_t scaling) {
	if( changed() ) {
		popupReform(vg,autoscale_t::ALL);
		Group::reform(vg,autoscale_t::NONE);
		for( auto& p: _popups ) {
			PopupBox* box = dynamic_cast<PopupBox*>(p.contents());
			if( box ) {
				box->position(PopupBox::popupPos(box, this));
				box->change();
			}
		}
	}
}

inline void Window::uiRatio(float ratio, bool changePhysicalWindowSize) {
	int windowW, windowH;
	glfwGetWindowSize( _glfwWindow, &windowW, &windowH );
	if( changePhysicalWindowSize ) {
		float prevScale = uiRatio();
		_uiRatio = ratio;
		int newW = int(round(windowW/prevScale*ratio));
		int newH = int(round(windowH/prevScale*ratio));
		glfwSetWindowSize(_glfwWindow, newW, newH);
	}
	else {
		_uiRatio = ratio;
		size( sz2_t(float(windowW),float(windowH))/uiRatio() );
	}
}


inline void Window::label( const str_t& l ) {
	Group::label( l );
	if( _glfwWindow )
		glfwSetWindowTitle( _glfwWindow, Group::label().c_str() );
}


inline isz_t Window::getWindowSize() const {
	return isz_t( int(w()), int(h()) );
}


inline Widget*	Window::underWidget(const pos_t& pt) {
	
	if( under(pt) ) {
/*		for( auto& p: _popups ) if( p.contents() ) {
			Group* g = dynamic_cast<Group*>(p.contents());
			if( g ) {
				Widget* ret = g->underWidget(pt);
				if( ret )
					return ret;
			}
			if( p.contents()->under(pt) )
				return p.contents();
		}
*/
		Widget* w = popupUnderWidget(pt);
		if( w ) return w;
	}
	return Group::underWidget(pt);
}

inline void Window::dismissTooltip() {
	_tooltipEngaged = false;
	_underWidgetChangedTimestamp = 1e10;
	damage();
}

inline void Window::updateUnderWidget(const pos_t& pt,float timestamp) {
	const Widget* currentUnderWidget = underWidget(pt);

	// first test the underWidget has tooltip.
	bool isTooltipAvailable = currentUnderWidget && currentUnderWidget->tooltip().length()>0;

	if( _underWidget!= currentUnderWidget ) {
		_underWidget = currentUnderWidget;
		_underWidgetChangedTimestamp = timestamp;
		if( _tooltipEngaged || _tooltipAlpha>0 ) {
			if( isTooltipAvailable )
				startTooltip();
		}
	}
	else {	// If mouse is staying on a Widget,
		if( !_tooltipEngaged ) {
			if( isTooltipAvailable && timestamp-_underWidgetChangedTimestamp>_def_time_tooltip_hold_to_start )
				startTooltip();
		}
		else if( !isTooltipAvailable && timestamp-_underWidgetChangedTimestamp>_def_time_tooltip_delayed_dismissal )
//		else if( !isTooltipAvailable )
			dismissTooltip();
	}
}

inline void Window::startTooltip() {
	const Widget* ww = _underWidget;
	if( ww ) {
		_tooltipString = ww->tooltip();
		if( _tooltipString.length()>0 ){
			_tooltipEngaged = true;
			_tooltipAlpha = std::max( _tooltipAlpha, 0.1f );
			_tooltipBox.tl() = ww->abs_pos()+ww->size()*scl2_t(.5,1)+_vec_tooltip_offset();
			glfwMakeContextCurrent(glfwWindow());
			_tooltipBox.wh() = _measure_tooltip_text(_vg, _tooltipString);
			_tooltipBox.w+=_size_tooltip_padding()*2;
			_tooltipBox.h+=_size_tooltip_padding()*2;
			if( _tooltipBox.br().x>w()-5 )
				_tooltipBox.x-= _tooltipBox.br().x-w()+5;
			if( _tooltipBox.br().y>h()-5 )
				_tooltipBox.y-= _tooltipBox.br().y-h()+5;
			if( _tooltipBox.tl().x<5 )
				_tooltipBox.x+= -_tooltipBox.tl().x+5;
			if( _tooltipBox.tl().y<5 )
				_tooltipBox.y+= -_tooltipBox.tl().y+5;
			_tooltipDx = ww->abs_pos().x+ww->size().w/2-_tooltipBox.x;
			damage();
		}
	}
}







inline Widget* Window::targetWidget() const {
	return _currentTarget;
}

inline void Window::targetWidget( Widget* w ) {
	_Targettable* target = dynamic_cast<_Targettable*>(w);
	if( target ) {
		_currentTarget = w;
		if( _currentTarget ) _JGL::dispatchEvent( _currentTarget, event_t::TARGETTED );
		target->setTarget();
	}
}

inline void Window::clearTargetWidget() {
	_Targettable* oldTarget = dynamic_cast<_Targettable*>(_currentTarget);
	if( oldTarget ) {
		if( oldTarget->targetted() )
			_JGL::dispatchEvent( _currentTarget, event_t::UNTARGETTED );
		oldTarget->clearTarget();
	}
	_currentTarget = nullptr;
}

inline bool Window::moveToNextTargetWidget() {
	if( _currentTarget ) {
		Widget* w = findNextTargettable( _currentTarget );
		if( !w ) w = findFirstTargettable( this );
		if( w ) {
			clearTargetWidget();
			targetWidget( w );
			return true;
		}
	}
	else {
		Widget* w = findFirstTargettable( this );
		if( w ) {
			targetWidget( w );
			return true;
		}
	}
	return false;
}

inline bool Window::moveToPrevTargetWidget() {
	if( _currentTarget ) {
		Widget* w = findPrevTargettable( _currentTarget );
		if( !w ) w = findLastTargettable( this );
		if( w ) {
			clearTargetWidget();
			targetWidget( w );
			return true;
		}
	}
	else {
		Widget* w = findLastTargettable( this );
		if( w ) {
			targetWidget( w );
			return true;
		}
	}
	return false;
}

inline bool	Window::handle(event_t event) {
	if( event == event_t::KEYDOWN && _JGL::eventKey()==GLFW_KEY_TAB ) {
		if( _JGL::eventMods(mod_t::SHIFT) )
			moveToPrevTargetWidget();
		else
			moveToNextTargetWidget();
		return true;
	}
#ifdef _WIN32
	else if( event == event_t::SCROLL && _JGL::eventMods(mod_t::CONTROL) && _JGL::eventMods(mod_t::SHIFT) ) {
		_windowsHDRGain *= powf(1.01f,_JGL::eventScrollY());
		if( _windowsHDRGain > 4 ) _windowsHDRGain = 4;
		if( _windowsHDRGain < 1 ) _windowsHDRGain = 1;
		animate();
	}
#endif
	return false;
}

inline void Window::nvgRegisterDefaultFonts( NVGcontext* vg, const str_t& path ) {
	str_t ppp = path+((path.length()>0)?"/":"");
	//	int fontNormal = nvgCreateFont(vg, "system", (ppp+"SF-Pro.ttf").c_str());
#ifdef __APPLE__
	int fontNormal = nvgCreateFont(vg, "system", str_t("/System/Library/Fonts/SFNS.ttf").c_str());
//	int fontNormal = nvgCreateFont(vg, "system", str_t("/System/Library/Fonts/AppleSDGothicNeo.ttc").c_str());
#endif
	
#ifdef _MSC_VER
	int fontNormal = nvgCreateFont(vg, "system", str_t("C:/Windows/Fonts/segoeui.ttf").c_str());
#endif
	int fontSans   = nvgCreateFont(vg, "sans", (ppp+"Roboto-Regular.ttf").c_str());
	int fontBold =   nvgCreateFont(vg, "sans-bold", (ppp+"Roboto-Bold.ttf").c_str());
	int fontEmoji =  nvgCreateFont(vg, "emoji", (ppp+"NotoEmoji-Regular.ttf").c_str());
	nvgCreateFont(vg, "icons", (ppp+"entypo.ttf").c_str());
	
	nvgAddFallbackFontId(vg, fontNormal, fontEmoji);
	nvgAddFallbackFontId(vg, fontSans, fontEmoji);
	nvgAddFallbackFontId(vg, fontBold, fontEmoji);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Window_h */
