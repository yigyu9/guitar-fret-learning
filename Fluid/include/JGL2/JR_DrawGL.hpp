//
//  JR_DrawGL.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/30.
//

#ifndef _JR_DrawGL_h
#define _JR_DrawGL_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/JR_GLProgram.hpp>
#include <assert.h>

namespace JR {

using v3list_t = std::vector<vec3>;
using v2list_t = std::vector<vec2>;
using tri_list_t = std::vector<uvec3>;

const str_t __blit_vert_code =
"#version 330\n"
"layout(location=0) in vec3 in_VertPos;\n"
"layout(location=1) in vec3 in_Normals;\n"
"layout(location=2) in vec2 in_TexCoord;\n"
"out vec2 texCoord;\n"
"uniform int flip;\n"
"uniform mat4 modelMat;\n"
"void main() {\n"
"	gl_Position = modelMat * vec4(in_VertPos, 1.0);\n"
"	if( flip==0 )	texCoord = vec2( in_TexCoord.x , in_TexCoord.y );\n"
"	else			texCoord = vec2( in_TexCoord.x , 1.-in_TexCoord.y );\n"
"}\n";

const str_t __blit_frag_code =
"#version 330\n"
"out vec4 fragColor;\n"
"in vec2 texCoord;\n"
"uniform sampler2D tex;\n"
"uniform vec3 inputGamma;\n"
"uniform vec3 outputGamma = vec3(2.2);\n"
"uniform int limitedDynamicRange = 0;\n"
"uniform mat3 rgbToPCS = mat3(1);\n"
"uniform mat3 PCSToDisplay = mat3(1);\n"
"uniform int singleChannel;\n"
"uniform int isBayer=0;\n"
"uniform float factor=1.;\n"
"float tonemap(float u, float gamma) {\n"
"	float ret = u;\n"
"	if( abs(gamma-2.4)<0.0001 ) {\n"
"		float u_ = abs(u);\n"
"		ret = u_>0.0031308?( sign(u)*1.055*pow( u_,0.41667)-0.055):(12.92*u);\n"
"	}\n"
"	else ret = sign(u)*pow(abs(u),1/gamma);\n"
"	if( limitedDynamicRange>0 )	return clamp(ret,0,factor);\n"
"	else						return ret;\n"
"}\n"
"float invTonemap(float u, float gamma) {\n"
"	if( abs(gamma-2.4)<0.0001 ) {\n"
"		float u_ = abs(u);\n"
"		return u_>0.04045?(sign(u)*pow((u_+0.055)/1.055,2.4)):(u/12.92);\n"
"	}\n"
"	else return sign(u)*pow(abs(u),gamma);\n"
"}\n"
"vec3 tonemap( vec3 c, vec3 g ){ return vec3(tonemap(c.r,g.r),tonemap(c.g,g.g),tonemap(c.b,g.b)); }\n"
"vec3 invTonemap( vec3 c, vec3 g ){ return vec3(invTonemap(c.r,g.r),invTonemap(c.g,g.g),invTonemap(c.b,g.b)); }\n"
"void main() {\n"
"	vec4 color = texture( tex, texCoord );\n"
"	if( singleChannel>0 ) color.rgb = color.rrr;\n"
"	color.rgb = rgbToPCS*invTonemap(color.rgb,inputGamma);\n"
"	color.rgb = PCSToDisplay*color.rgb* factor;\n"
"	color.rgb = tonemap(color.rgb,outputGamma);\n"
"	fragColor = color;\n"
"}\n";



struct RenderableMeshBase {
	RenderableMeshBase() {}
	RenderableMeshBase(RenderableMeshBase&& b);
	RenderableMeshBase(const RenderableMeshBase& b);
	virtual inline 		~RenderableMeshBase(){ clearGL(); }
	
	virtual inline bool	created() { return _va>0; }
	
	virtual void clearGL();
	virtual void create(const v3list_t& vertices, const v3list_t& normals, const tri_list_t& faces ) { create( vertices, normals, {}, faces ); }
	virtual void create(const v3list_t& vertices, const v3list_t& normals, const v2list_t& txCoords, const tri_list_t& faces );
	virtual void				render();
	virtual void				render(const mat4& m);
	template<typename T> void	updateBuffer( GLuint buf, const std::vector<T>& array );
	virtual void				updateVertices( const v3list_t& vertices );
	static v3list_t				generateNormal( const v3list_t& vertices, const tri_list_t& faces );
	
protected:
	GLuint		_va		=0;
	GLuint		_vBuf	=0;
	GLuint		_tBuf	=0;
	GLuint		_nBuf	=0;
	GLuint		_eBuf	=0;
	unsigned	_nFaces	=0;
	static void		drawArrays( GLuint vertId, GLuint normId, GLuint tcooId, GLuint vaId, GLuint type, GLuint cnt );
	static void		drawElements( GLuint vertId, GLuint normId, GLuint tcooId, GLuint vaId, GLuint faceId, GLuint type, GLuint cnt );
};












inline RenderableMeshBase::RenderableMeshBase(RenderableMeshBase&& b):
_va(b._va),_vBuf(b._vBuf),_tBuf(b._tBuf),_nBuf(b._nBuf),_eBuf(b._eBuf),_nFaces(b._nFaces) {
	b._va=b._vBuf=b._tBuf=b._nBuf=b._eBuf=0;
	b._nFaces=0;
}

inline RenderableMeshBase::RenderableMeshBase(const RenderableMeshBase& b):
_va(b._va),_vBuf(b._vBuf),_tBuf(b._tBuf),_nBuf(b._nBuf),_eBuf(b._eBuf),_nFaces(b._nFaces) {
}

inline void RenderableMeshBase::clearGL() {
	if( _va  >0 ) glDeleteVertexArrays(1, &_va);_va = 0;
	if( _vBuf>0 ) glDeleteBuffers(1, &_vBuf);	_vBuf = 0;
	if( _tBuf>0 ) glDeleteBuffers(1, &_tBuf);	_tBuf = 0;
	if( _nBuf>0 ) glDeleteBuffers(1, &_nBuf);	_nBuf = 0;
	if( _eBuf>0 ) glDeleteBuffers(1, &_eBuf);	_eBuf = 0;
	_nFaces = 0;
}

inline void RenderableMeshBase::create( const v3list_t& vertices, const v3list_t& normals, const v2list_t& txCoords, const tri_list_t& faces ) {
	if( !created() ) {
		glGenVertexArrays(1, &_va);
		glBindVertexArray( _va );
		
		glGenBuffers(1, &_vBuf);
		glBindBuffer(GL_ARRAY_BUFFER, _vBuf);
		glBufferData(GL_ARRAY_BUFFER, sizeof(vec3)*vertices.size(), vertices.data(), GL_STATIC_DRAW);
		glEnableVertexAttribArray( 0 );
		glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, nullptr);
		
		glGenBuffers(1, &_nBuf);
		glBindBuffer(GL_ARRAY_BUFFER, _nBuf);
		glBufferData(GL_ARRAY_BUFFER, sizeof(vec3)*normals.size(), normals.data(), GL_STATIC_DRAW);
		glEnableVertexAttribArray( 1 );
		glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 0, nullptr);

		if( txCoords.size()>0 ) {
			glGenBuffers(1, &_tBuf);
			glBindBuffer(GL_ARRAY_BUFFER, _tBuf);
			glBufferData(GL_ARRAY_BUFFER, sizeof(vec2)*txCoords.size(), txCoords.data(), GL_STATIC_DRAW);
			glEnableVertexAttribArray( 2 );
			glVertexAttribPointer(2, 2, GL_FLOAT, GL_TRUE, 0, nullptr);
		}
		glGenBuffers(1, &_eBuf);
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, _eBuf);
		glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(uvec3)*faces.size(), faces.data(), GL_STATIC_DRAW);
		
		glBindBuffer(GL_ARRAY_BUFFER,0);
		glBindVertexArray(0);
		_nFaces = (unsigned int)(faces.size())*3;
	}
}
inline void RenderableMeshBase::render() {
	drawElements( _vBuf, _nBuf, _tBuf, _va, _eBuf, GL_TRIANGLES, _nFaces);
}

inline void RenderableMeshBase::render(const mat4& m) {
	GLuint prog = getGLCurProgram();
	setUniform(prog,"modelMat",m);
	render();
}

template<typename T> inline void RenderableMeshBase::updateBuffer( GLuint buf, const std::vector<T>& array ) {
	assert( created() );
	glBindBuffer(GL_ARRAY_BUFFER, buf);
	glBufferSubData(GL_ARRAY_BUFFER, 0, sizeof(T)*array.size(), array.data());
	glBindBuffer(GL_ARRAY_BUFFER, 0);
}

inline void RenderableMeshBase::updateVertices( const v3list_t& vertices ) {
	updateBuffer( _vBuf, vertices);
}

inline v3list_t RenderableMeshBase::generateNormal( const v3list_t& vertices, const tri_list_t& faces ) {
	v3list_t normals( vertices.size(), vec3(0) );
	for( const auto& f: faces ) {
		vec3 n = cross( vertices[f[1]]-vertices[f[0]], vertices[f[2]]-vertices[f[0]] );
		normals[f[0]]+= n;
		normals[f[1]]+= n;
		normals[f[2]]+= n;
	}
	for( auto& n: normals ) n = normalize(n);
	return normals;
}

inline void RenderableMeshBase::drawArrays( GLuint vertId, GLuint normId, GLuint tcooId, GLuint vaId,
										   GLuint type, GLuint cnt ) {
#ifdef GL2
	glBindBuffer( GL_ARRAY_BUFFER, vertId );
	glEnableVertexAttribArray(0);
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, nullptr );
	
	glBindBuffer( GL_ARRAY_BUFFER, normId );
	glEnableVertexAttribArray(1);
	glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, nullptr );

	glBindBuffer( GL_ARRAY_BUFFER, tcooId );
	glEnableVertexAttribArray(2);
	glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, nullptr );
#else
	glBindVertexArray( vaId );
#endif
	glDrawArrays( type, 0, cnt );
#ifdef GL2
	glBindBuffer( GL_ARRAY_BUFFER, 0 );
#else
	glBindVertexArray( 0 );
#endif
}

inline void RenderableMeshBase::drawElements( GLuint vertId, GLuint normId, GLuint tcooId, GLuint vaId,
											 GLuint faceId, GLuint type, GLuint cnt ) {
#ifdef GL2
	glBindBuffer( GL_ARRAY_BUFFER, vertId );
	glEnableVertexAttribArray(0);
	glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, nullptr );
	
	glBindBuffer( GL_ARRAY_BUFFER, normId );
	glEnableVertexAttribArray(1);
	glVertexAttribPointer(1, 3, GL_FLOAT, GL_FALSE, 0, nullptr );

	glBindBuffer( GL_ARRAY_BUFFER, tcooId );
	glEnableVertexAttribArray(2);
	glVertexAttribPointer(2, 2, GL_FLOAT, GL_FALSE, 0, nullptr );
#else
	glBindVertexArray( vaId );
#endif
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, faceId );
	glDrawElements( type, cnt, GL_UNSIGNED_INT, 0 );
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0 );
#ifdef GL2
	glBindBuffer( GL_ARRAY_BUFFER, 0 );
#else
	glBindVertexArray( 0 );
#endif
}




inline mat4 getOrthoTransform(float winW, float winH) {
	return translate(vec3(-1,1,0))*scale(vec3(2.f/winW,-2.f/winH,1));
}

inline Program& blitProgram() {
	static Program blitProgram;
	if( !blitProgram.isUsable() ) blitProgram.create( __blit_vert_code, __blit_frag_code );
	return blitProgram;
}







inline void drawScreenQuad() {
	static RenderableMeshBase mesh;
	if( !mesh.created() ) {
		const std::vector<vec3>  v = { {0,1,0}, {0,0,0}, {1,1,0}, {1,0,0} };
		const std::vector<vec3>  n = { {0,0,1}, {0,0,1}, {0,0,1}, {0,0,1} };
		const std::vector<vec2>  t = { {0,0}, {0,1}, {1,0}, {1,1} };
		const std::vector<uvec3> e = { {0,1,2}, {2,1,3} };
		mesh.create( v, n, t, e );
	}
	mesh.render();
}

inline void drawQuad() {
	static RenderableMeshBase mesh;
	if( !mesh.created() ) {
		const std::vector<vec3>  v = { {-1,1,0}, {-1,-1,0}, {1,1,0}, {1,-1,0} };
		const std::vector<vec3>  n = { {0,0,1}, {0,0,1}, {0,0,1}, {0,0,1} };
		const std::vector<vec2>  t = { {0,0}, {0,1}, {1,0}, {1,1} };
		const std::vector<uvec3> e = { {0,1,2}, {2,1,3} };
		mesh.create( v, n, t, e );
	}
	mesh.render();
}

const int N_STRIP = 15;
const int N_SLICE = 30;

inline void drawSphere() {
	const float PI = 3.14159265f;
	static RenderableMeshBase mesh;
	if( !mesh.created() ) {
		std::vector<vec3> v;
		std::vector<vec2> t;
		std::vector<uvec3> e;
		
		for( int l=0; l<N_SLICE; l++ ) {
			v.push_back({0,1,0});
			t.push_back({l/float(N_SLICE-1),0});
		}
		for( int s = 1; s<N_STRIP; s++ ) {
			float phi = s*PI/N_STRIP;
			float y = cosf( phi );
			float r = sinf( phi );
			for( int l=0; l<N_SLICE; l++ ) {
				float theta = l*PI*2/(N_SLICE-1);
				v.push_back({sinf(theta)*r,y,cosf(theta)*r});
				t.push_back({l/float(N_SLICE-1),s/float(N_STRIP)});
			}
		}
		for( int l=0; l<N_SLICE; l++ ) {
			v.push_back({0,-1,0});
			t.push_back({l/float(N_SLICE-1),1});
		}
		{
//			int s0 = 0;
			int s1 = N_SLICE;
			for( int l=0; l<N_SLICE; l++ )
				e.push_back({l+0,l+s1,(l+1)+s1});
		}
		for( int s = 1; s<N_STRIP; s++ ) {
			int s0 = s*N_SLICE;
			int s1 = (s+1)*N_SLICE;
			for( int l=0; l<N_SLICE-1; l++ ) {
				e.push_back({l+s0,l+s1,((l+1)%N_SLICE)+s0});
				e.push_back({((l+1)%N_SLICE)+s0,l+s1,((l+1)%N_SLICE)+s1});
			}
		}
		{
			int s0 = (N_STRIP-1)*N_SLICE;
			int s1 = (N_STRIP)*N_SLICE;
			for( int l=0; l<N_SLICE-1; l++ )
				e.push_back({s1+l,((l+1)%N_SLICE)+s0,l+s0});
		}
		mesh.create( v, v, t, e );
	}
	mesh.render();
}

inline void drawCylinder() {
	const float PI = 3.14159265f;
	static RenderableMeshBase mesh;
	if( !mesh.created() ) {
		std::vector<vec3> v;
		std::vector<vec3> n;
		std::vector<vec2> t;
		std::vector<uvec3> e;
		
		v.push_back({0,.5,0});
		n.push_back({0,1,0});
		t.push_back({0,0});
		for( int l=0; l<N_SLICE; l++ ) {
			float theta = l*PI*2/N_SLICE;
			v.push_back({sinf(theta),.5f,cosf(theta)});
			n.push_back({0,1,0});
			t.push_back({l/float(N_SLICE),0});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			float theta = l*PI*2/N_SLICE;
			vec2 p = {sinf(theta),cosf(theta)};
			v.push_back({p.x,.5,p.y});
			n.push_back({p.x,0,p.y});
			t.push_back({l/float(N_SLICE),0});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			float theta = l*PI*2/N_SLICE;
			vec2 p = {sinf(theta),cosf(theta)};
			v.push_back({p.x,-.5,p.y});
			n.push_back({p.x,0,p.y});
			t.push_back({l/float(N_SLICE),1});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			float theta = l*PI*2/N_SLICE;
			v.push_back({sinf(theta),-.5f,cosf(theta)});
			n.push_back({0,-1,0});
			t.push_back({l/float(N_SLICE),1});
		}
		v.push_back({0,-.5,0});
		n.push_back({0,-1,0});
		t.push_back({0,1});
		{
			int s1 = 1;
			for( int l=0; l<N_SLICE; l++ )
				e.push_back({0,l+s1,((l+1)%N_SLICE)+s1});
		}
		{
			int s0 = N_SLICE+1;
			int s1 = N_SLICE*2+1;
			for( int l=0; l<N_SLICE; l++ ) {
				e.push_back({l+s0,l+s1,((l+1)%N_SLICE)+s0});
				e.push_back({((l+1)%N_SLICE)+s0,l+s1,((l+1)%N_SLICE)+s1});
			}
		}
		{
			int s0 = N_SLICE*3+1;
			int s1 = N_SLICE*4+1;
			for( int l=0; l<N_SLICE; l++ )
				e.push_back({s1,((l+1)%N_SLICE)+s0,l+s0});
		}
		mesh.create( v, n, t, e );
	}
	mesh.render();
}

inline void drawQuad( const vec3& p, const vec3& n, const vec2& sz, const vec4& color ) {
	vec3 s = {sz.x,sz.y,1};
	vec3 axis = cross(vec3(0,0,1),n);
	float l = length(axis);
	float angle = atan2f(l,n.z);
	mat4 modelMat;
	if( l>0.0000001 )
		modelMat = translate(p)*rotate( angle, axis )*scale(s);
	else
		modelMat = translate(p)*scale(s);
	GLuint prog = getGLCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawQuad();
}
	
inline void drawSphere( const vec3& p, float r, const vec4& color ){
	mat4 modelMat = translate(p)*scale(vec3(r));
	GLuint prog = getGLCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawSphere();
}

inline void drawCylinder( const vec3& p1, const vec3& p2, float r, const vec4& color ) {
	vec3 s = {r,length(p1-p2),r};
	vec3 axis = cross(vec3(0,1,0),p1-p2);
	float l = length(axis);
	float angle = atan2f(l,(p1-p2).y);
	mat4 modelMat;
	if( l>0.0000001 )
		modelMat = translate((p1+p2)/2.f)*rotate( angle, axis )*scale(s);
	else
		modelMat = translate((p1+p2)/2.f)*scale(s);
	GLuint prog = getGLCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawCylinder();
}

} // namespace JR

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* JR_DrawGL_h */
