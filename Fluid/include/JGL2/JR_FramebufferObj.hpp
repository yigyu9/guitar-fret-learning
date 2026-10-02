//
//  JR_FramebufferObj.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/6/24.
//

#ifndef _JR_FramebufferObj_hpp
#define _JR_FramebufferObj_hpp

#ifdef __APPLE__
#define GL_SILENCE_DEPRECATION
#include <OpenGL/gl3.h>
#elif defined _MSC_VER
#include <gl/glew.h>
#endif

namespace JR {

struct FramebufferObj {
	static void setTexParam( GLuint minFilter = GL_LINEAR, GLuint warp = GL_CLAMP_TO_EDGE ) {
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, minFilter);
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, warp );
		glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, warp );
	}
	virtual size_t w() const { return _w; }
	virtual size_t h() const { return _h; }
	virtual bool   valid() const { return fbo>0; }

	virtual void clearGL() {
		if( color ) glDeleteTextures( 1, &color ); color = 0;
		if( depth ) glDeleteTextures( 1, &depth ); depth = 0;
		if( fbo   ) glDeleteFramebuffers( 1, &fbo ); fbo = 0;
	}
	virtual void create( int ww, int hh ) {
		if( ww == _w && hh == _h ) return;
		_w = (unsigned long)ww;
		_h = (unsigned long)hh;
		clearGL();
		glGenTextures( 1, &color );
		glBindTexture( GL_TEXTURE_2D, color );
		glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA, ww, hh, 0, GL_RGBA, GL_UNSIGNED_BYTE, 0);
		setTexParam();
		
		glGenTextures( 1, &depth );
		glBindTexture( GL_TEXTURE_2D, depth );
		glTexImage2D( GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT32F, ww, hh, 0, GL_DEPTH_COMPONENT, GL_FLOAT, 0);
		setTexParam();
		
		glGenFramebuffers( 1, &fbo );
		glGetIntegerv(GL_FRAMEBUFFER_BINDING, &oldFB );
		glBindFramebuffer(GL_FRAMEBUFFER, fbo);
		
		glFramebufferTexture( GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, color, 0);
		glFramebufferTexture( GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, depth, 0 );
		if(glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE)
			std::cerr<<"FBO is incomplete";
		
		glBindFramebuffer(GL_FRAMEBUFFER, oldFB);
	}
	virtual void setToTarget() {
		glGetIntegerv(GL_VIEWPORT, oldVP );
		oldSc = glIsEnabled(GL_SCISSOR_TEST);
		glGetIntegerv(GL_DRAW_FRAMEBUFFER_BINDING, &oldFB );
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, fbo);
		glViewport(0,0,(int)_w,(int)_h);
		glDisable(GL_SCISSOR_TEST);
	}
	virtual void restoreVP() {
		glViewport(oldVP[0], oldVP[1], oldVP[2], oldVP[3] );
		glBindFramebuffer(GL_DRAW_FRAMEBUFFER, oldFB);
		if( oldSc )
			glEnable(GL_SCISSOR_TEST);
	}
	virtual void bindColor( GLuint prog, const std::string& name, GLuint slot ) {
		glActiveTexture( GL_TEXTURE0+slot );
		glBindTexture( GL_TEXTURE_2D, color );
		glUniform1i( glGetUniformLocation(prog,name.c_str()), (int)slot );
	}
	virtual void bindDepth( GLuint prog, const std::string& name, GLuint slot ) {
		glActiveTexture( GL_TEXTURE0+slot );
		glBindTexture( GL_TEXTURE_2D, depth );
		glUniform1i( glGetUniformLocation(prog,name.c_str()), (int)slot );
	}
protected:
	size_t _w = 0;
	size_t _h = 0;
	GLuint fbo = 0;
	GLuint color = 0;
	GLuint depth = 0;
	
	GLint oldVP[4];
	GLint oldFB, oldSc;
};

} // namespace JR

#endif /* _JR_FramebufferObj_hpp */
