#ifndef _JR_GL_PROGRAM_HPP_
#define _JR_GL_PROGRAM_HPP_

#include <string>
#include <filesystem>
#include <iostream>
#include <fstream>
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

#ifdef JR_USE_GLM
#include <glm/glm.hpp>
#include <glm/gtc/type_ptr.hpp>
#include <JGL2/glm_rect.hpp>
#else
#include <jm/jm.hpp>
#endif

namespace JR {

#ifdef JR_USE_GLM
using sz2_t		= glm::dim2;
using glm::vec2;
using glm::vec3;
using glm::vec4;
using glm::ivec2;
using glm::ivec3;
using glm::ivec4;
using glm::uvec2;
using glm::uvec3;
using glm::uvec4;

using glm::mat3;
using glm::mat2;
using glm::mat4;

using glm::value_ptr;
using glm::sign;
using glm::mix;
using glm::fract;
using glm::inverse;
using glm::normalize;
using glm::rotate;
using glm::translate;
using glm::scale;
using glm::lookAt;
using glm::perspective;
#else
using sz2_t		= jm::dim2;
using jm::vec2;
using jm::vec3;
using jm::vec4;
using jm::ivec2;
using jm::ivec3;
using jm::ivec4;
using jm::uvec2;
using jm::uvec3;
using jm::uvec4;

using jm::mat3;
using jm::mat2;
using jm::mat4;

using jm::value_ptr;
using jm::sign;
using jm::mix;
using jm::fract;
using jm::inverse;
using jm::normalize;
using jm::rotate;
using jm::translate;
using jm::scale;
using jm::lookAt;
using jm::perspective;
#endif

using str_t		= std::string;

inline void glErr( const std::string& str ) {
	GLenum err = glGetError();
	if( err != GL_NO_ERROR ) {
		std::string errorCode = "Unknown";
		switch( err ) {
			case 0x0500: errorCode = "GL_INVALID_ENUM"; break;
			case 0x0501: errorCode = "GL_INVALID_VALUE"; break;
			case 0x0502: errorCode = "GL_INVALID_OPERATION"; break;
			case 0x0503: errorCode = "GL_STACK_OVERFLOW"; break;
			case 0x0504: errorCode = "GL_STACK_UNDERFLOW"; break;
			case 0x0505: errorCode = "GL_OUT_OF_MEMORY"; break;
			case 0x0506: errorCode = "GL_INVALID_FRAMEBUFFER_OPERATION"; break;
			case 0x0507: errorCode = "GL_CONTEXT_LOST"; break;
			case 0x8031: errorCode = "GL_TABLE_TOO_LARGE1"; break;
		}
		fprintf(stderr,"GL error: 0x%04X (%s): %s\n", err, errorCode.c_str(), str.c_str());
	}
}

inline unsigned getGLCurProgram() {
	int prog = 0;
	glGetIntegerv(GL_CURRENT_PROGRAM,&prog);
	return (unsigned)prog;
}

inline std::string readText( const std::filesystem::path& fn ) {
	std::ifstream t(fn);
	if( !t.is_open() ) {
		std::cerr<<"[ERROR] Text file: "<<fn<<" is not found\n";
		return "";
	}
	std::string str((std::istreambuf_iterator<char>(t)), std::istreambuf_iterator<char>());
	return str;
}

inline void setUniform( GLuint prog, const str_t& loc, const int& v )				{ glUniform1i ( glGetUniformLocation( prog, loc.c_str() ), v ); }
inline void setUniform( GLuint prog, const str_t& loc, const int* v, int n )		{ glUniform1iv( glGetUniformLocation( prog, loc.c_str() ), n, (GLint*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<int>& v ) 	{ glUniform1iv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLint*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const ivec2& v )				{ glUniform2iv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const ivec2* v, int n )		{ glUniform2iv( glGetUniformLocation( prog, loc.c_str() ), n, (GLint*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<ivec2>& v)	{ glUniform2iv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLint*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const ivec3& v )				{ glUniform3iv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const ivec3* v, int n )		{ glUniform3iv( glGetUniformLocation( prog, loc.c_str() ), n, (GLint*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<ivec3>& v)	{ glUniform3iv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLint*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const ivec4& v )				{ glUniform4iv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const ivec4* v, int n )		{ glUniform4iv( glGetUniformLocation( prog, loc.c_str() ), n, (GLint*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<ivec4>& v)	{ glUniform4iv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLint*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const float& v )				{ glUniform1f ( glGetUniformLocation( prog, loc.c_str() ), v ); }
inline void setUniform( GLuint prog, const str_t& loc, const float* v, int n )		{ glUniform1fv( glGetUniformLocation( prog, loc.c_str() ), n, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<float>& v)	{ glUniform1fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const vec2& v )				{ glUniform2fv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const vec2* v, int n )		{ glUniform2fv( glGetUniformLocation( prog, loc.c_str() ), n, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<vec2>& v)	{ glUniform2fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const vec3& v )				{ glUniform3fv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const vec3* v, int n )		{ glUniform3fv( glGetUniformLocation( prog, loc.c_str() ), n, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<vec3>& v)	{ glUniform3fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const vec4& v )				{ glUniform4fv( glGetUniformLocation( prog, loc.c_str() ), 1, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const vec4* v, int n )		{ glUniform4fv( glGetUniformLocation( prog, loc.c_str() ), n, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<vec4>& v)	{ glUniform4fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const mat2& v )				{ glUniformMatrix2fv( glGetUniformLocation( prog, loc.c_str() ), 1, false, (GLfloat*)value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const mat2* v, int n )		{ glUniformMatrix2fv( glGetUniformLocation( prog, loc.c_str() ), n, false, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<mat2>& v)	{ glUniformMatrix2fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), false, (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const mat3& v )				{ glUniformMatrix3fv( glGetUniformLocation( prog, loc.c_str() ), 1, false, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const mat3* v, int n )		{ glUniformMatrix3fv( glGetUniformLocation( prog, loc.c_str() ), n, false, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<mat3>& v)	{ glUniformMatrix3fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), false, (GLfloat*)v.data() ); }

inline void setUniform( GLuint prog, const str_t& loc, const mat4& v )				{ glUniformMatrix4fv( glGetUniformLocation( prog, loc.c_str() ), 1, false, value_ptr(v) ); }
inline void setUniform( GLuint prog, const str_t& loc, const mat4* v, int n )		{ glUniformMatrix4fv( glGetUniformLocation( prog, loc.c_str() ), n, false, (GLfloat*)v ); }
inline void setUniform( GLuint prog, const str_t& loc, const std::vector<mat4>& v)	{ glUniformMatrix4fv( glGetUniformLocation( prog, loc.c_str() ), (int)v.size(), false, (GLfloat*)v.data() ); }


struct Program {
	Program(){};
	Program( Program&& pe ): progId( pe.progId ) { pe.progId = 0; }
	virtual ~Program() { clear(); }
	virtual void clear() {
		if( progId ) glDeleteProgram( progId );	progId = 0;
		if( vertId ) glDeleteShader( vertId );	vertId = 0;
		if( fragId ) glDeleteShader( fragId );	fragId = 0;
	}
	virtual bool isUsable() const { return progId>0; }
	virtual void use() const { if( progId>0 ) glUseProgram( progId ); }
	virtual void unuse() const { glUseProgram( 0 ); }

	GLuint progId = 0;
	GLuint vertId = 0;
	GLuint fragId = 0;

	virtual void create( const str_t& vertSrc, const str_t& fragSrc );
	virtual void load( const std::filesystem::path& vertFn, const std::filesystem::path& fragFn );
	
	void setUniform( const str_t& loc, const int& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const float& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const ivec2& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const ivec3& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const ivec4& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const vec2& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const vec3& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const vec4& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const mat2& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const mat3& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const mat4& v )	{ use(); JR::setUniform( progId, loc, v ); }

	void setUniform( const str_t& loc, const std::vector<int>& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<float>& v ){ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<ivec2>& v) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<ivec3>& v) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<ivec4>& v) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<vec2>& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<vec3>& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<vec4>& v ) { use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<mat2>& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<mat3>& v )	{ use(); JR::setUniform( progId, loc, v ); }
	void setUniform( const str_t& loc, const std::vector<mat4>& v )	{ use(); JR::setUniform( progId, loc, v ); }

	void setUniform( const str_t& loc, const int* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const float* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const ivec2* v, int n)	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const ivec3* v, int n)	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const ivec4* v, int n)	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const vec2* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const vec3* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const vec4* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const mat2* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const mat3* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }
	void setUniform( const str_t& loc, const mat4* v, int n )	{ use(); JR::setUniform( progId, loc, v, n ); }

protected:
	static GLuint compileShader( GLenum shaderType, const str_t& src);
};

inline GLuint Program::compileShader( GLenum shaderType, const str_t& src) {
	unsigned int shader = glCreateShader( shaderType );
	const char* src_c = src.c_str();
	glShaderSource( shader, 1, &src_c, nullptr );
	glCompileShader( shader );

	GLint  success;
	char infoLog[512];
	glGetShaderiv( shader, GL_COMPILE_STATUS, &success );
	if( !success ) {
		glGetShaderInfoLog( shader, 512, NULL, infoLog );
		fprintf( stderr, "%s", (shaderType ==GL_VERTEX_SHADER) ? "Vertex ":"Fragment " );
		fprintf( stderr, "error:\n" );
		fprintf( stderr, "%s\n", infoLog );
	}
	return shader;
}

inline void Program::create( const str_t& vertSrc, const str_t& fragSrc ) {
   vertId = compileShader( GL_VERTEX_SHADER, vertSrc );
   fragId = compileShader( GL_FRAGMENT_SHADER, fragSrc );

   progId = glCreateProgram();
   glAttachShader( progId, vertId );
   glAttachShader( progId, fragId );
   glLinkProgram( progId);

   int  success;
   char infoLog[512];
   glGetProgramiv( progId, GL_LINK_STATUS, &success );
   if(!success) {
	   glGetProgramInfoLog( progId, 512, NULL, infoLog);
	   fprintf( stderr, "Program error:\n" );
	   fprintf( stderr, "%s\n", infoLog );
   }
	else
		fprintf( stderr, "Program built successfully.");
}

inline void Program::load( const std::filesystem::path& vertFn, const std::filesystem::path& fragFn ) {
	std::string vertCode = readText( vertFn );
	std::string fragCode = readText( fragFn );
	create( vertCode, fragCode );
}


struct AutoBuildProgram : Program {
	str_t vertSrc;
	str_t fragSrc;
	AutoBuildProgram( const str_t& vSrc, const str_t& fSrc)
	: vertSrc(vSrc), fragSrc(fSrc){}
	virtual void use() {
		if( progId<1 ) create( vertSrc, fragSrc );
		Program::use();
	}
};

struct AutoLoadProgram : Program {
	std::filesystem::path vertFn;
	std::filesystem::path fragFn;
	AutoLoadProgram( const std::filesystem::path& vFile, const std::filesystem::path& fFile)
	: vertFn(vFile), fragFn(fFile){}
	virtual void use() {
		if( progId<1 ) load( vertFn, fragFn );
		Program::use();
	}
};

} // namespace JR

#endif

