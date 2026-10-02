//
//  View3D.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/6/24.
//

#ifndef JGL_View3D_hpp
#define JGL_View3D_hpp

#include <JGL2/Widget.hpp>
#include <JGL2/JR_Camera3D.hpp>
#include <JGL2/JR_Renderer.hpp>
#include <JGL2/_Picker3D.hpp>

namespace JGL2 {

struct View3D: Widget,  _Targettable, _Picker3D {
	View3D( float x, float y, float w, float h, const std::string& n );
	
	template<typename T, typename=std::enable_if_t<std::is_base_of_v<JR::Camera, T>>>
			inline	void				cameraType()		{ cameraType(new T()); }
	template<typename T, typename=std::enable_if_t<std::is_base_of_v<JR::Renderer, T>>>
			inline	void				rendererType()		{ renderer(new T()); }

	virtual inline	void				camera(JR::Camera* c);
	virtual inline	JR::Camera&			camera()			{ return *_camera; }
	virtual inline	const JR::Camera&	camera() const		{ return *_camera; }
	template<typename T> inline	T*		camera();

	virtual inline	void				renderer(JR::Renderer* c);
	virtual inline	JR::Renderer&		renderer()			{ return *_renderer; }
	virtual inline	const JR::Renderer&	renderer() const	{ return *_renderer; }
	template<typename T> inline T*		renderer();

	virtual inline	void				clearColor( const colora_t& c ) { _clearColor = c; }
	virtual inline	colora_t&			clearColor()		{ return _clearColor; }
	virtual inline	const colora_t&		clearColor() const	{ return _clearColor; }

	virtual inline	void				sceneCenter(const vec3& p, bool fix=false)	{ camera().sceneCenter(p,fix); }
	virtual inline	void				cameraPos(const vec3& p, bool fix=false) 	{ camera().cameraPos(p,fix); }

	virtual inline	const vec3&			sceneCenter() const { return camera().sceneCenter(); }
	virtual inline 	const vec3&			cameraPos() const	{ return camera().cameraPos(); }

	virtual inline	mat4				viewMat() const		{ return camera().viewMat(); }
	virtual inline	mat4				projMat()			{ return camera().projMat(size()); }
	
//	virtual inline 	void				setUniforms( GLuint prog )	{ camera().setUniforms( prog, size() ); }
	virtual inline 	void				drawContents(NVGcontext* vg, const rct_t&r, align_t a ) override {}

	virtual 		bool				handle( event_t e ) override;
	
	virtual 		void				drawGL() override;
	virtual inline	void				renderFunc(JR::RenderFunc f){ _renderer->renderFunc(f); }
	virtual inline	void				resetRenderFunc()			{ _renderer->resetRenderFunc(); }
	
	virtual inline	void				wireFunc(JR::RenderFunc f)	{ _renderer->wireFunc(f); }
	virtual inline	void				resetWireFunc()				{ _renderer->resetWireFunc(); }
	
protected:
	JR::Camera*		_camera = nullptr;
	JR::Renderer*	_renderer = nullptr;

	bool			_cameraMotion = false;
	pos_t			_cursorPt;
	colora_t		_clearColor = colora_t(0,0,0,0);
};

inline View3D::View3D( float x, float y, float w, float h, const std::string& n )
: _Picker3D(), Widget(x,y,w,h,n) {
	_camera = new JR::OrbitCamera();
	_renderer = new JR::NullRenderer();
}

inline void View3D::camera( JR::Camera* c ) {
	assert( c );
	if( _camera ) {
		c->copyFrom(_camera);
		delete _camera;
	}
	_camera = c;
}

inline void View3D::renderer(JR::Renderer* r) {
	if( _renderer ) {
		r->copyFrom(_renderer);
		delete _renderer;
	}
	_renderer = r;
}

inline void View3D::drawGL() {
	glClearColor(_clearColor.r,_clearColor.b,_clearColor.g,_clearColor.a);
	glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
	if( _renderer ) _renderer->render(size(),camera());
}

inline bool View3D::handle( event_t e ) {
	mat4 vp = projMat()*viewMat();
	bool ret = false;
	switch( e ) {
		case event_t::MOVE:
			ret = _Picker3D::handle(e,size(),vp,float(getWindowSize().h));
			break;
		case event_t::PUSH:
			_cursorPt = _JGL::eventPt();
			_cameraMotion = !_Picker3D::handle(e,size(),vp,float(getWindowSize().h));
			ret = true;
			break;
		case event_t::RELEASE:
			ret = _Picker3D::handle(e,size(),vp,float(getWindowSize().h));
			break;
		case event_t::DRAG:
			if( _cameraMotion ) {
				auto oldPt = _cursorPt;
				_cursorPt = _JGL::eventPt();
				camera().drag( _cursorPt-oldPt, _JGL::eventMods(mod_t::CONTROL) );
				redraw();
				ret = true;
			}
			else
				ret = _Picker3D::handle(e,size(),vp,float(getWindowSize().h));
			break;
		case event_t::ZOOM:
			camera().zoom(_JGL::eventZoom(), _JGL::eventMods(mod_t::CONTROL));
			ret = true;
			break;
		case event_t::SCROLL:
			camera().scroll( _JGL::eventScroll(),_JGL::eventMods(mod_t::CONTROL) );
			ret = true;
			break;
		default:
			break;
	}
	if( ret ) {
		redraw();
		return ret;
	}
	return Widget::handle(e);
}

template<typename T>
inline T* View3D::renderer() {
	T* r = dynamic_cast<T*>(renderer());
	return r;
}

template<typename T>
inline T* View3D::camera() {
	T* r = dynamic_cast<T*>(camera());
	return r;
}

template<typename T> using enable_if_renderer = std::enable_if_t<std::is_base_of_v<JR::Renderer, T>>;

template<typename T, typename=enable_if_renderer<T>>
struct Render3DView : View3D {
	Render3DView( float x, float y, float w, float h, const std::string& name )
	: View3D( x, y, w, h, name ) { rendererType<T>(); }
};

using PBRRenderView = Render3DView<JR::PBRRenderer>;

} // namespace JGL

#endif /* JGL_View3D_hpp */
