//
//  JR_RenderableMesh.hpp
//  SpringMass
//
//  Created by Hyun Joon Shin on 2021/05/09.
//

#ifndef _JR_RenderableMesh_hpp
#define _JR_RenderableMesh_hpp

#include "JR_Material.hpp"
#include <fstream>

namespace JR {

struct RenderableMesh : public RenderableMeshBase {
	RenderableMesh():RenderableMeshBase(){}
	RenderableMesh( RenderableMesh&& b);
	virtual inline 				~RenderableMesh() { clearGL(); }
	virtual void				clearGL() override;
	virtual void				render(const mat4& m=mat4(1)) override;
	virtual inline const mat4&	modelMat() const	{ return _modelMat; }
	virtual inline mat4&		modelMat() 			{ return _modelMat; }
	virtual inline void			modelMat(const mat4& m) { _modelMat = m; }
	
	virtual inline void			diffTex ( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.diffTex (fn, plist); }
	virtual inline void			armTex  ( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.armTex  (fn, plist); }
	virtual inline void			normTex ( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.normTex (fn, plist); }
	virtual inline void			specTex ( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.specTex (fn, plist); }
	virtual inline void			metalTex( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.metalTex(fn, plist); }
	virtual inline void			roughTex( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.roughTex(fn, plist); }
	virtual inline void			alphaTex( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.alphaTex(fn, plist); }
	virtual inline void			aOccTex ( const std::filesystem::path& fn, const path_list& plist={""} ) { _material.aOccTex (fn, plist); }

	virtual inline void 		diffTex ( GLuint id, bool ownership=false ) { _material.diffTex (id,ownership); }
	virtual inline void 		armTex  ( GLuint id, bool ownership=false ) { _material.armTex  (id,ownership); }
	virtual inline void 		normTex ( GLuint id, bool ownership=false ) { _material.normTex (id,ownership); }
	virtual inline void 		specTex ( GLuint id, bool ownership=false ) { _material.specTex (id,ownership); }
	virtual inline void 		metalTex( GLuint id, bool ownership=false ) { _material.metalTex(id,ownership); }
	virtual inline void 		roughTex( GLuint id, bool ownership=false ) { _material.roughTex(id,ownership); }
	virtual inline void 		alphaTex( GLuint id, bool ownership=false ) { _material.alphaTex(id,ownership); }
	virtual inline void 		aOccTex ( GLuint id, bool ownership=false ) { _material.aOccTex (id,ownership); }

	virtual inline GLuint		diffTex () 	const	{ return _material.diffTex (); }
	virtual inline GLuint		armTex  () 	const	{ return _material.armTex  () ; }
	virtual inline GLuint		normTex () 	const	{ return _material.normTex (); }
	virtual inline GLuint		specTex () 	const	{ return _material.specTex (); }
	virtual inline GLuint		metalTex() 	const	{ return _material.metalTex(); }
	virtual inline GLuint		roughTex() 	const	{ return _material.roughTex(); }
	virtual inline GLuint		alphaTex() 	const	{ return _material.alphaTex(); }
	virtual inline GLuint		aOccTex() 	const	{ return _material.aOccTex(); }

	virtual inline float		roughness()  const	{ return _material.roughness(); }
	virtual inline float		metalness()  const	{ return _material.metalness(); }
	virtual inline const vec4&	color()		 const	{ return _material.color(); }
	virtual inline const vec3&	F0()		 const	{ return _material.F0(); }
	virtual inline bool			bumpMapped() const	{ return _material.bumpMapped(); }
	virtual inline bool			normMapDx()	 const	{ return _material.normMapDx(); }
	virtual inline const mat3&	texMat()	 const	{ return _material.texMat(); }

	virtual inline float&		roughness()			{ return _material.roughness(); }
	virtual inline float&		metalness()			{ return _material.metalness(); }
	virtual inline vec4&		color()				{ return _material.color(); }
	virtual inline vec3&		F0()				{ return _material.F0(); }
	virtual inline bool&		bumpMapped()		{ return _material.bumpMapped(); }
	virtual inline bool&		normMapDx()			{ return _material.normMapDx(); }
	virtual inline mat3&		texMat()			{ return _material.texMat(); }

	virtual inline void			roughness(float v) 	{ _material.roughness(v); }
	virtual inline void			metalness(float v) 	{ _material.metalness(v); }
	virtual inline void			color(const vec4& v){ _material.color(v); }
	virtual inline void			F0(const vec3& v)	{ _material.F0(v); }
	virtual inline void			bumpMapped(bool v) 	{ _material.bumpMapped(v); }
	virtual inline void			normMapDx(bool v)	{ _material.normMapDx(v); }
	virtual inline void			texMat(const mat3& v){_material.texMat(v); }


protected:
	Material	_material;
	mat4		_modelMat = mat4(1);
private:
	RenderableMesh( const RenderableMesh& b);
};











inline RenderableMesh::RenderableMesh( RenderableMesh&& b ):
	RenderableMeshBase(std::move(b)),_material(std::move(b._material)),_modelMat(b._modelMat) {}

inline RenderableMesh::RenderableMesh( const RenderableMesh& b ):
	RenderableMeshBase(b),_material(b._material),_modelMat(b._modelMat) {}

inline void RenderableMesh::clearGL() {
	RenderableMeshBase::clearGL();
	_material.clearGL();
}

inline void RenderableMesh::render(const mat4& m) {
	GLuint prog = getGLCurProgram();
	setUniform(prog, "modelMat", m*_modelMat );
	_material.use( prog );
	RenderableMeshBase::render();
	Material::unuse( prog );
}








inline float shininessToRoughness(float s) {
	return powf(2/(s+2),0.25f);
}

inline std::string readString( std::istream& ifs ) {
	std::string ret = "";
	std::getline(ifs, ret, '\"');
	std::getline(ifs, ret, '\"');
	return ret;
}

inline std::vector<RenderableMesh> loadJ3A( const std::filesystem::path& fn ) {
	std::vector<RenderableMesh> ret;
	int nObjects;
	std::ifstream ifs( fn );
	if( !ifs.is_open() ) {
		printf("J3A file cannot be open.. maybe file not found?\n");
		return ret;
	}
	
	ifs>>nObjects;
	printf("Number of objects: %d\n", nObjects );
		
	for( int i=0; i<nObjects; i++ ) {
		int bumpMapped=0;
		vec4 color = vec4(1,.3,0,1);
		vec3 f0 = vec3(0.046);
		float shininess = 10;
		std::string diffMap="", normMap="", specMap="", ambMap="";
		int nVertices=0, nTriangles=0;
		std::vector<vec3> vertices;
		std::vector<vec3> normals;
		std::vector<vec2> texCoords;
		std::vector<uvec3> faces;
		
		
		ifs>>color.r>>color.g>>color.b>>color.a;
		ifs>>f0.r>>f0.g>>f0.b>>shininess;
		diffMap = readString( ifs );
		normMap = readString( ifs );
		ifs>>bumpMapped;
		specMap = readString( ifs );
		ambMap  = readString( ifs );

		ifs>>nVertices;
		vertices. resize(nVertices);
		normals.  resize(nVertices);
		texCoords.resize(nVertices);
		
		for( int j=0; j<nVertices; j++ )	ifs>>vertices[j].x>>vertices[j].y>>vertices[j].z;
		for( int j=0; j<nVertices; j++ )	ifs>>normals[j].x>>normals[j].y>>normals[j].z;
		for( int j=0; j<nVertices; j++ )	ifs>>texCoords[j].x>>texCoords[j].y;
		
		ifs>>nTriangles;
		printf("Number of triangles: %d (of object: %d)\n", nTriangles, i );
		faces.resize(nTriangles);
		for( int j=0; j<nTriangles; j++ ) {
			ifs>>faces[j].x>>faces[j].y>>faces[j].z;
			if( ifs.eof() ) printf("EOF\n");
		}
		int xxx;
		ifs>>xxx;
		if( ifs.eof() ) printf("EOF\n");
		ret.emplace_back();
		RenderableMesh& mesh = ret.back();
		mesh.create(vertices, normals, texCoords, faces);
		if( diffMap.length()>0 ) mesh.diffTex(diffMap, {fn.parent_path(),""});
		if( normMap.length()>0 ) mesh.normTex(normMap, {fn.parent_path(),""});
		mesh.color(color);
		mesh.roughness(shininessToRoughness(shininess));
		mesh.F0(vec3(0.1));
		mesh.metalness(0);
		mesh.bumpMapped(bumpMapped);
	}
	ifs.close();
	return ret;
}

} // namespace JR

#endif /* JR_RenderableMesh_hpp */
