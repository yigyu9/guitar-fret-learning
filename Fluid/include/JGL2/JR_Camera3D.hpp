//
//  JR_Camera3D.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/14/24.
//

#ifndef _JR_Camera3D_h
#define _JR_Camera3D_h

#include <JGL2/JR_DrawGL.hpp>
#include <functional>

namespace JR {

struct Camera {
	Camera(){};
	virtual ~Camera(){};

	virtual inline mat4			projMat(const sz2_t& s) { viewport(s); return _projMat; }

	virtual inline void			setUniforms( GLuint prog, const sz2_t& sz, const str_t& viewName="viewMat", const str_t& projName="projMat", const str_t& cameraPosName="cameraPos" );
	virtual inline void			setUniforms( GLuint prog, const str_t& viewName="viewMat", const str_t& projName="projMat", const str_t& cameraPosName="cameraPos" ) const;

	virtual inline void			sceneCenter(const vec3& v, bool fix=false);
	virtual inline const vec3&	sceneCenter() const	{ return _sceneCenter; }
	virtual inline void			cameraPos(const vec3& v, bool fix=false);
	virtual inline const vec3&	cameraPos() const	{ return _cameraPos; }

	virtual inline const sz2_t&	viewport() const	{ return _viewport; }
	virtual inline const mat4&	viewMat() const		{ return _viewMat; }
	virtual inline const mat4&	projMat() const		{ return _projMat; }

	virtual inline void			viewport(const sz2_t& s) { _viewport = s; updateProj(); }
	virtual inline void			projMat(const mat4& m) { _projMat = m; }
	virtual inline void			viewMat(const mat4& m) { _viewMat = m; }
	
	// Functions to override for specific camera model
	virtual inline void			updateView(){};
	virtual inline void			updateProj(){};


	virtual inline void			drag(const vec2& delta, bool modded ){}
	virtual inline void			scroll(const vec2& delta, bool modded ){}
	virtual inline void			zoom(float d, bool modded){}

	virtual inline void			copyFrom(const Camera& c);
	virtual inline void			copyFrom(const Camera* c) { copyFrom(*c); }

protected:
	vec3	_sceneCenter	= {0,30,0};
	sz2_t	_viewport;
	mat4	_projMat;
	mat4	_viewMat;
	vec3	_cameraPos		= {0,30,40};
};




inline void Camera::copyFrom(const Camera& c) {
	sceneCenter( c._sceneCenter );
	cameraPos( c._cameraPos, true );
}

inline void Camera::setUniforms( GLuint prog, const sz2_t& sz, const str_t& viewName, const str_t& projName, const str_t& cameraPosName ) {
	viewport(sz);
	setUniforms(prog, viewName, projName,cameraPosName);
}

inline void Camera::setUniforms( GLuint prog, const str_t& viewName, const str_t& projName, const str_t& cameraPosName ) const {
	setUniform(prog, projName, projMat());
	setUniform(prog, viewName, viewMat());
	setUniform(prog, cameraPosName, cameraPos());
}

inline void	Camera::sceneCenter(const vec3& p, bool fix) {
	vec3 d = cameraPos() - sceneCenter();
	_sceneCenter = p;
	if( !fix ) _cameraPos = _sceneCenter+d;
	updateView();
}

inline void		Camera::cameraPos(const vec3& p, bool fix) {
	vec3 d = cameraPos() - sceneCenter();
	_cameraPos = p;
	if( !fix ) _sceneCenter = _cameraPos-d;
	updateView();
}






struct OrbitCamera : Camera {
	OrbitCamera(){
		updateView();
		updateProj();
	}
	virtual ~OrbitCamera(){};
	
	virtual void	cameraPos( const vec3& p, bool fix=false ) override;
	virtual void	sceneCenter( const vec3& p, bool fix=false ) override;

	virtual float	fov()			const { return _fov; }
	virtual float	dist()			const { return _dist; }
	virtual float	yaw()			const { return _yaw; }
	virtual float	pitch()			const { return _pitch; }
	
	virtual void	fov(float v)		 { _fov=v; updateProj(); }
	virtual void	dist(float v)		 { _dist=v; updateView(); }
	virtual void	yaw(float v)		 { _yaw=v; updateView();}
	virtual void	pitch(float v)		 { _pitch=v; updateView(); }

	virtual void	drag(const vec2& delta, bool modded ) override;
	virtual void	scroll(const vec2& delta, bool modded ) override;
	virtual void	zoom(float d, bool modded) override;

	virtual	void	updateView() override;
	virtual	void	updateProj() override;

protected:
	float _dist			= 320.f;
	float _yaw			= 0.f;
	float _pitch		= 0.2f;
	float _fov			= 0.5f;
};




inline void OrbitCamera::updateView() {
	_cameraPos = vec3(rotate(_yaw,vec3(0,-1,0))*rotate(_pitch,vec3(-1,0,0))*vec4(0,0,_dist,1)) + _sceneCenter;
	_viewMat = lookAt(_cameraPos,_sceneCenter,vec3(0,1,0));
}

inline void	OrbitCamera::updateProj() {
	_projMat = perspective( _fov, _viewport.w/_viewport.h, 10.f, 10000.f );
}

inline void OrbitCamera::drag(const vec2& delta, bool modded ) {
	if( !modded ) {
		_yaw   += delta.x/_viewport.w*3.141592f;
		_pitch += delta.y/_viewport.h*3.141592f;
		updateView();
	}
	else {
		vec4 p1 = inverse(projMat()*viewMat())*vec4(0,0,.75,1);
		vec4 p2 = inverse(projMat()*viewMat())*vec4(delta/vec2(-_viewport.w,_viewport.h)*2,.75,1);
		cameraPos( _cameraPos+(p2.xyz/p2.w-p1.xyz/p1.w),false);
	}
}

inline void	OrbitCamera::scroll(const vec2& delta, bool modded ) {
	if( !modded ) {
		_yaw   +=-delta.x/_viewport.w*3.141592f*2;
		_pitch +=-delta.y/_viewport.h*3.141592f*2;
		updateView();
	}
	else {
		_dist*=powf(0.97f, delta.y);
		updateView();
	}
}

inline void	OrbitCamera::zoom(float d, bool modded) {
	_dist*=powf(0.8f, d);
	updateView();
}

inline void OrbitCamera::sceneCenter(const vec3& p, bool fix) {
	auto oldP = _cameraPos;
	Camera::sceneCenter(p, fix);
	if( fix ) {
		vec3 d = oldP-_sceneCenter;
		_dist = length( d );
		_pitch = atan2f( d.y, length(d.xz) );
		_yaw = -atan2f( d.x, d.z );
	}
	updateView();
}

inline void OrbitCamera::cameraPos(const vec3& p, bool fix) {
	auto oldP = _sceneCenter;
	Camera::cameraPos(p, fix);
	if( fix ) {
		vec3 d = _cameraPos - oldP;
		_dist = length( d );
		_pitch = atan2f( d.y, length(d.xz) );
		_yaw = -atan2f( d.x, d.z);
	}
	updateView();
}

} // namespace JR

#endif /* _JR_Camera3D_h */
