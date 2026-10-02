//
//  _Picker3D.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/16/24.
//

#ifndef _Picker3D_h
#define _Picker3D_h

namespace JGL2 {

using JR::vec2;
using JR::vec3;
using JR::vec4;
using JR::mat4;

typedef std::function<bool(const vec3&)> Motion3DCallback_t;
typedef std::function<bool(button_t,const vec3&)> Button3DCallback_t;

struct _Picker3D {
	virtual inline vec3		eventPt3D() { return _cursorPt3; }
	
	virtual inline void		move3DCB  (Motion3DCallback_t f) { _move3DCB=f; }
	virtual inline void		unsetMove3DCB() { _move3DCB=defMotion3DCB; }
	
	virtual inline void		drag3DCB  (Motion3DCallback_t f) { _drag3DCB=f; }
	virtual inline void		unsetDrag3DCB() { _drag3DCB=defMotion3DCB; }
	
	virtual inline void		push3DCB  (Button3DCallback_t f) { _push3DCB=f; }
	virtual inline void		unsetPush3DCB() { _push3DCB=defButton3DCB; }
	
	virtual inline void		release3DCB  (Button3DCallback_t f) { _release3DCB=f; }
	virtual inline void		unsetRelease3DCB() { _release3DCB=defButton3DCB; }
	
	virtual bool			handle(event_t e, const sz2_t& sz, const mat4& vp, float windowH);
	virtual pos_t			getFramebufferCursorPos(float windowH);
	
	virtual std::tuple<vec3,float> getNCCursorPos(const sz2_t& sz, float windowH);
	virtual std::tuple<vec3,float> get3DCursorPos(const sz2_t& sz, const mat4& vp, float windowH);
	
	virtual vec3			getNCCursorPos(float d, const sz2_t& sz, float windowH);
	virtual vec3			get3DCursorPos(float d, const sz2_t& sz, const mat4& vp, float windowH);
	
	virtual inline void		lockCursorDepth() { _cursorDepthLocked = true; }
	virtual inline void		releaseCursorDepth() { _cursorDepthLocked = false; }

	virtual inline void		autoLockCursorDepth(bool t) { _autoLockCursorDepth = t; }

protected:
	const Motion3DCallback_t defMotion3DCB = [](const vec3&){ return false; };
	const Button3DCallback_t defButton3DCB = [](button_t,const vec3&){ return false; };
	
	Motion3DCallback_t	_move3DCB = defMotion3DCB;
	Motion3DCallback_t	_drag3DCB = defMotion3DCB;
	Button3DCallback_t	_push3DCB = defButton3DCB;
	Button3DCallback_t	_release3DCB = defButton3DCB;
	bool				_autoLockCursorDepth = true;
	bool				_cursorDepthLocked = false;
	vec3				_cursorPt3;
	float				_cursorD;
};

inline bool _Picker3D::handle(event_t e, const sz2_t& sz, const mat4& vp, float windowH) {
	switch( e ) {
		case event_t::MOVE:
			std::tie(_cursorPt3,_cursorD) = get3DCursorPos(sz,vp,windowH);
			if( _move3DCB(_cursorPt3) ) return true;
			break;
		case event_t::PUSH:
			if( _push3DCB(_JGL::eventButton(),eventPt3D()) ) {
				if( _autoLockCursorDepth ) lockCursorDepth();
				return true;
			}
			return false;
		case event_t::DRAG: {
			vec3 oldPt3 = _cursorPt3;
			if( _cursorDepthLocked )	_cursorPt3 = get3DCursorPos(_cursorD,sz,vp,windowH);
			else						std::tie(_cursorPt3,_cursorD) = get3DCursorPos(sz,vp,windowH);
			return _drag3DCB(_cursorPt3-oldPt3);
		}
		case event_t::RELEASE: {
			bool ret = _release3DCB( _JGL::eventButton(), eventPt3D() );
			if( _autoLockCursorDepth ) releaseCursorDepth();
			return ret;
		}
		default:
			break;
	}
	return false;
}

inline pos_t _Picker3D::getFramebufferCursorPos(float windowH) {
	pos_t pt = _JGL::eventWindowPt();
	pt.y = windowH-pt.y;
	return pt*_JGL::getCurrentDrawWindowPxRatio();
}

inline std::tuple<vec3,float> _Picker3D::getNCCursorPos(const sz2_t& sz, float windowH) {
	pos_t pt = getFramebufferCursorPos(windowH);
	float d = 0;
	glReadPixels(int(round(pt.x)), int(round(pt.y)), 1, 1, GL_DEPTH_COMPONENT, GL_FLOAT, &d);
	auto pt3 = vec3( pt/(vec2(sz.w,sz.h)*_JGL::getCurrentDrawWindowPxRatio()), d)*2-1;
	return std::make_tuple(pt3,d);
}

inline vec3 _Picker3D::getNCCursorPos(float d, const sz2_t& sz, float windowH) {
	pos_t pt = getFramebufferCursorPos(windowH);
	auto pt3 = vec3( pt/(vec2(sz.w,sz.h)*_JGL::getCurrentDrawWindowPxRatio()), d)*2-1;
	return pt3;
}

inline std::tuple<vec3,float> _Picker3D::get3DCursorPos(const sz2_t& sz, const mat4& vp,float windowH) {
	auto [ptNC,d] = getNCCursorPos(sz,windowH);
	vec4 ptWC = inverse(vp)*vec4(ptNC,1);
	return std::make_tuple( ptWC.xyz/ptWC.w, d);
}

inline vec3 _Picker3D::get3DCursorPos(float d, const sz2_t& sz, const mat4& vp,float windowH) {
	auto ptNC = getNCCursorPos(d,sz,windowH);
	vec4 ptWC = inverse(vp)*vec4(ptNC,1);
	return ptWC.xyz/ptWC.w;
}

} // namespace JGL

#endif /* _Picker3D_h */
