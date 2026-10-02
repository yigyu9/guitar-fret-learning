//
//  GLTools.cpp
//  SpringMass
//
//  Created by Hyun Joon Shin on 2021/05/09.
//

#include "GLTools.hpp"
#include <vector>
#include <tuple>

struct RenderableMesh {
	GLuint va=0;
	GLuint vBuf=0;
	GLuint nBuf=0;
	GLuint tBuf=0;
	GLuint eBuf=0;
	unsigned int nFaces=0;
	void create( const std::vector<jm::vec3>& vertices,
				const std::vector<jm::vec3>& normals,
				const std::vector<jm::vec2>& tcoords,
				const std::vector<jm::uvec3>& faces ) {
		if( !va ) {
			glGenVertexArrays(1, &va);
			glBindVertexArray( va );
			
			glGenBuffers(1, &vBuf);			
			glBindBuffer(GL_ARRAY_BUFFER, vBuf);
			glBufferData(GL_ARRAY_BUFFER, sizeof(jm::vec3)*vertices.size(), vertices.data(), GL_STATIC_DRAW);
			glEnableVertexAttribArray( 0 );
			glVertexAttribPointer(0, 3, GL_FLOAT, GL_FALSE, 0, nullptr);
			
			glGenBuffers(1, &nBuf);
			glBindBuffer(GL_ARRAY_BUFFER, nBuf);
			glBufferData(GL_ARRAY_BUFFER, sizeof(jm::vec3)*normals.size(), normals.data(), GL_STATIC_DRAW);
			glEnableVertexAttribArray( 1 );
			glVertexAttribPointer(1, 3, GL_FLOAT, GL_TRUE, 0, nullptr);
			
			glGenBuffers(1, &tBuf);
			glBindBuffer(GL_ARRAY_BUFFER, tBuf);
			glBufferData(GL_ARRAY_BUFFER, sizeof(jm::vec2)*tcoords.size(), tcoords.data(), GL_STATIC_DRAW);
			glEnableVertexAttribArray( 2 );
			glVertexAttribPointer(2, 2, GL_FLOAT, GL_TRUE, 0, nullptr);
			
			glGenBuffers(1, &eBuf);
			glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, eBuf);
			glBufferData(GL_ELEMENT_ARRAY_BUFFER, sizeof(jm::uvec3)*faces.size(), faces.data(), GL_STATIC_DRAW);
			
			glBindBuffer(GL_ARRAY_BUFFER,0);
			nFaces = (unsigned int)(faces.size())*3;
		}
	}
	void render() {
		glBindVertexArray( va );
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, eBuf );
		glDrawElements(GL_TRIANGLES, nFaces, GL_UNSIGNED_INT, 0);
		glBindVertexArray( 0 );
		glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, 0 );
	}
};


void drawQuad() {
	static RenderableMesh mesh;
	if( !mesh.va ) {
		const std::vector<jm::vec3> v = { {-1,1,0}, {-1,-1,0}, {1,1,0}, {1,-1,0} };
		const std::vector<jm::vec3> n = { {0,0,1}, {0,0,1}, {0,0,1}, {0,0,1} };
		const std::vector<jm::vec2> t = { {0,0}, {0,1}, {1,0}, {1,1} };
		const std::vector<jm::uvec3> e = { {0,1,2}, {2,1,3} };
		mesh.create( v, n, t, e );
	}
	mesh.render();
}

const int N_STRIP = 15;
const int N_SLICE = 30;
const float PI = 3.1415926535;
void drawSphere() {
	static RenderableMesh mesh;
	if( !mesh.va ) {
		std::vector<jm::vec3> v;
		std::vector<jm::vec2> t;
		std::vector<jm::uvec3> e;
		
		v.push_back({0,1,0});
		t.push_back({0.5,0});
		for( int s = 1; s<N_STRIP; s++ ) {
			float y = cosf( s*PI/N_STRIP );
			float r = sinf( s*PI/N_STRIP );
			for( int l=0; l<N_SLICE; l++ ) {
				v.push_back({sinf(l*PI*2/N_SLICE)*r,y,cosf(l*PI*2/N_SLICE)*r});
				t.push_back( {r/float(N_STRIP), (s+1)/float(N_STRIP+1)} );
			}
		}
		v.push_back({0,-1,0});
		t.push_back({0.5,1});
		{
			int s1 = 1;
			for( int l=0; l<N_SLICE; l++ )
				e.push_back({0,l+s1,((l+1)%N_SLICE)+s1});
		}
		for( int s = 1; s<N_STRIP; s++ ) {
			int s0 = (s-1)*N_SLICE+1;
			int s1 = s*N_SLICE+1;
			for( int l=0; l<N_SLICE; l++ ) {
				e.push_back({l+s0,l+s1,((l+1)%N_SLICE)+s0});
				e.push_back({((l+1)%N_SLICE)+s0,l+s1,((l+1)%N_SLICE)+s1});
			}
		}
		{
			int s0 = (N_STRIP-2)*N_SLICE+1;
			int s1 = (N_STRIP-1)*N_SLICE+1;
			for( int l=0; l<N_SLICE; l++ ) 
				e.push_back({s1,((l+1)%N_SLICE)+s0,l+s0});
		}
		mesh.create( v, v, t, e );
	}
	mesh.render();
}


void drawCylinder() {
	static RenderableMesh mesh;
	if( !mesh.va ) {
		std::vector<jm::vec3> v;
		std::vector<jm::vec3> n;
		std::vector<jm::vec2> t;
		std::vector<jm::uvec3> e;
		
		v.push_back({0,.5,0});
		t.push_back({.5,.5});
		n.push_back({0,1,0});
		for( int l=0; l<N_SLICE; l++ ) {
			v.push_back({sinf(l*PI*2/N_SLICE),.5,cosf(l*PI*2/N_SLICE)});
			t.push_back({sinf(l*PI*2/N_SLICE)*.5+.5,cosf(l*PI*2/N_SLICE)*.5+.5});
			n.push_back({0,1,0});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			jm::vec2 p = {sinf(l*PI*2/N_SLICE),cosf(l*PI*2/N_SLICE)}; 
			v.push_back({p.x,.5,p.y});
			t.push_back({l/float(N_SLICE),0});
			n.push_back({p.x,0,p.y});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			jm::vec2 p = {sinf(l*PI*2/N_SLICE),cosf(l*PI*2/N_SLICE)}; 
			v.push_back({p.x,-.5,p.y});
			t.push_back({l/float(N_SLICE),1});
			n.push_back({p.x,0,p.y});
		}
		for( int l=0; l<N_SLICE; l++ ) {
			v.push_back({sinf(l*PI*2/N_SLICE),-.5,cosf(l*PI*2/N_SLICE)});
			t.push_back({sinf(l*PI*2/N_SLICE)*.5+.5,cosf(l*PI*2/N_SLICE)*.5+.5});
			n.push_back({0,-1,0});
		}
		v.push_back({0,-.5,0});
		t.push_back({.5,.5});
		n.push_back({0,-1,0});
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

static inline GLuint getCurProgram() {
	GLint prog;
	glGetIntegerv(GL_CURRENT_PROGRAM, &prog);
	return prog;
}

void drawQuad( const jm::vec3& p, const jm::vec3& n, const jm::vec2& sz, const jm::vec4 color ) {
	jm::vec3 s = {sz.x,sz.y,1};
	jm::vec3 axis = cross(n,jm::vec3(0,0,1));
	float l = length(axis);
	float angle = atan2f(l,n.z);
	jm::mat4 modelMat;
	if( l>0.0000001 )
		modelMat = jm::translate(p)*jm::rotate( angle, axis )*jm::scale(s);
	else
		modelMat = jm::translate(p)*jm::scale(s);
	GLuint prog = getCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawQuad();
}
	
void drawSphere( const jm::vec3& p, float r, const jm::vec4 color ){
	jm::mat4 modelMat = jm::translate(p)*jm::scale(jm::vec3(r));
	GLuint prog = getCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawSphere();
}
void drawCylinder( const jm::vec3& p1, const jm::vec3& p2, float r, const jm::vec4 color ) {
	jm::vec3 s = {r,length(p1-p2),r};
	jm::vec3 axis = cross(jm::vec3(0,1,0),p1-p2);
	float l = length(axis);
	float angle = atan2f(l,(p1-p2).y);
	jm::mat4 modelMat;
	if( l>0.0000001 )
		modelMat = jm::translate((p1+p2)/2.f)*jm::rotate( angle, axis )*jm::scale(s);
	else
		modelMat = jm::translate((p1+p2)/2.f)*jm::scale(s);
	GLuint prog = getCurProgram();
	setUniform(prog, "modelMat", modelMat );
	setUniform(prog, "color", color );
	drawCylinder();
}

