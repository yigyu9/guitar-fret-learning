//
//  JR_Material.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/13/24.
//

#ifndef _JR_Material_h
#define _JR_Material_h

#include <JGL2/JR_DrawGL.hpp>
#include <JGL2/JR_GLProgram.hpp>

namespace JR {

struct RenderableMesh;

typedef std::vector<std::filesystem::path> path_list;

struct Material {
	Material(){};
	Material(Material&& b);
	virtual inline			~Material() { clearGL(); }
	virtual void 			use( GLuint prog );
	static	void			unuse( GLuint prog );
	virtual void			clearGL();
	
	virtual void			diffTex ( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			armTex  ( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			normTex ( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			specTex ( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			roughTex( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			metalTex( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			alphaTex( const std::filesystem::path& fn, const path_list& plist={""} );
	virtual void			aOccTex ( const std::filesystem::path& fn, const path_list& plist={""} );

	virtual inline void 	diffTex ( GLuint id, bool ownership=false );
	virtual inline void 	armTex  ( GLuint id, bool ownership=false );
	virtual inline void 	normTex ( GLuint id, bool ownership=false );
	virtual inline void 	specTex ( GLuint id, bool ownership=false );
	virtual inline void 	roughTex( GLuint id, bool ownership=false );
	virtual inline void 	metalTex( GLuint id, bool ownership=false );
	virtual inline void 	alphaTex( GLuint id, bool ownership=false );
	virtual inline void 	aOccTex ( GLuint id, bool ownership=false );

	virtual inline GLuint 	diffTex ()	const	{ return _diffTex ; }
	virtual inline GLuint 	armTex  ()	const	{ return _armTex  ; }
	virtual inline GLuint 	normTex ()	const	{ return _normTex ; }
	virtual inline GLuint 	specTex ()	const	{ return _specTex ; }
	virtual inline GLuint 	roughTex()	const	{ return _roughTex; }
	virtual inline GLuint 	metalTex()	const	{ return _metalTex; }
	virtual inline GLuint 	alphaTex()	const	{ return _alphaTex; }
	virtual inline GLuint 	aOccTex ()	const	{ return _aOccTex   ; }

	virtual inline void		clearDiffTex ();
	virtual inline void		clearArmTex  ();
	virtual inline void		clearNormTex ();
	virtual inline void		clearSpecTex ();
	virtual inline void		clearRoughTex();
	virtual inline void		clearMetalTex();
	virtual inline void		clearAlphaTex();
	virtual inline void		clearAOccTex ();

	virtual inline void		roughness(float v) 		{ _roughness=v; }
	virtual inline void		metalness(float v) 		{ _metalness=v; }
	virtual inline void		color(const vec4& v)	{ _color=v; }
	virtual inline void		F0(const vec3& v) 		{ _F0=v; }
	virtual inline void		bumpMapped(bool v) 		{ _isBumpMapped=v; }
	virtual inline void		normMapDx(bool v)		{ _normMapDx=v; }
	virtual inline void		texMat(const mat3& v)	{ _texMat=v; }

	virtual inline float		roughness()	 const	{ return _roughness; }
	virtual inline float		metalness()	 const	{ return _metalness; }
	virtual inline const vec4&	color()		 const	{ return _color; }
	virtual inline const vec3&	F0()		 const	{ return _F0; }
	virtual inline bool			bumpMapped() const	{ return _isBumpMapped; }
	virtual inline bool			normMapDx()	 const	{ return _normMapDx; }
	virtual inline const mat3&	texMat()	 const	{ return _texMat; }

	virtual inline float&		roughness()			{ return _roughness; }
	virtual inline float&		metalness()			{ return _metalness; }
	virtual inline vec4&		color()				{ return _color; }
	virtual inline vec3&		F0()				{ return _F0; }
	virtual inline bool&		bumpMapped()		{ return _isBumpMapped; }
	virtual inline bool&		normMapDx()			{ return _normMapDx; }
	virtual inline mat3&		texMat()			{ return _texMat; }

protected:
	static GLuint			loadTexture( const std::filesystem::path& fn, bool sRGB=true );
	static GLuint			loadTex( const std::filesystem::path& fn, const path_list& plist, bool sRGB );
	static void				bindTexture( GLuint prog, int slot, const std::string& targetName, GLuint tex );
	
	vec4					_color = vec4(.8,.8,.8,1);
	float					_roughness=0.3f;
	float					_metalness=0.0f;
	vec3					_F0 = vec3(0.046);
	GLuint					_diffTex = 0;
	bool					_ownDiffTex = false;
	GLuint					_armTex  = 0;
	bool					_ownArmTex = false;
	GLuint					_normTex = 0;
	bool					_ownNormTex = false;
	bool					_isBumpMapped = false;
	bool					_normMapDx = false;
	GLuint					_alphaTex = 0;
	bool					_ownAlphaTex = false;
	GLuint					_roughTex = 0;
	bool					_ownRoughTex = false;
	GLuint					_specTex = 0;
	bool					_ownSpecTex = false;
	GLuint					_metalTex = 0;
	bool					_ownMetalTex = false;
	GLuint					_aOccTex = 0;
	bool					_ownAOccTex = false;
	mat3					_texMat = mat3(1);

private:
	Material(const Material& b);
	friend RenderableMesh;
};

inline Material::Material(const Material& b):
	_color(b._color), _roughness(b._roughness), _F0(b._F0), _isBumpMapped(b._isBumpMapped),
	_diffTex(b._diffTex), _ownDiffTex(b._ownDiffTex),
	_armTex(b._armTex), _ownArmTex(b._ownArmTex),
	_aOccTex(b._aOccTex), _ownAOccTex(b._ownAOccTex),
	_normTex(b._normTex), _ownNormTex(b._ownNormTex) {
}

inline Material::Material(Material&& b):
	_color(b._color), _roughness(b._roughness), _F0(b._F0), _isBumpMapped(b._isBumpMapped),
	_diffTex(b._diffTex), _ownDiffTex(b._ownDiffTex),
	_armTex(b._armTex), _ownArmTex(b._ownArmTex),
	_aOccTex(b._aOccTex), _ownAOccTex(b._ownAOccTex),
	_normTex(b._normTex), _ownNormTex(b._ownNormTex) {
	b._diffTex = b._armTex  = b._normTex = 0;
}

inline void Material::use( GLuint prog ) {
	setUniform (prog, "color",		 _color );
	setUniform (prog, "roughness",	 _roughness );
	setUniform (prog, "metalness",	 _metalness );
	setUniform (prog, "F0",			 _F0 );
	setUniform (prog, "bumpMapped",	 _isBumpMapped?1:0 );
	setUniform (prog, "normalMapDX", _normMapDx?1:0 );
	setUniform (prog, "texMat",	 	 _texMat );
	bindTexture(prog, 0, "diffTex",  _diffTex );
	bindTexture(prog, 1, "armTex",   _armTex );
	bindTexture(prog, 2, "normalTex",_normTex );
	bindTexture(prog, 3, "specTex",  _specTex );
	bindTexture(prog, 4, "metalTex", _metalTex );
	bindTexture(prog, 5, "roughTex", _roughTex );
	bindTexture(prog, 6, "alphaTex", _alphaTex );
	bindTexture(prog, 7, "ambOccTex",_aOccTex );
}

inline void Material::unuse( GLuint prog ) {
	bindTexture(prog, 0, "diffTex",  0 );
	bindTexture(prog, 1, "armTex",   0 );
	bindTexture(prog, 2, "normalTex",0 );
	bindTexture(prog, 3, "specTex",  0 );
	bindTexture(prog, 4, "metalTex", 0 );
	bindTexture(prog, 5, "roughTex", 0 );
	bindTexture(prog, 6, "alphaTex", 0 );
	bindTexture(prog, 7, "ambOccTex", 0 );
	setUniform (prog, "color",		vec4(1,.3,0,1) );
	setUniform (prog, "roughness",	0.3f );
	setUniform (prog, "metalness",	0.f );
	setUniform (prog, "F0",			vec3(0.046) );
	setUniform (prog, "bumpMapped",	0 );
	setUniform (prog, "normalMapDX",0 );
	setUniform (prog, "texMat",		mat3(1) );
}

inline void Material::clearDiffTex () { if( _ownDiffTex  && _diffTex >0 ) glDeleteTextures(1,&_diffTex ); _diffTex  =0; }
inline void Material::clearArmTex  () { if( _ownArmTex   && _armTex  >0 ) glDeleteTextures(1,&_armTex  ); _armTex   =0; }
inline void Material::clearNormTex () { if( _ownNormTex  && _normTex >0 ) glDeleteTextures(1,&_normTex ); _normTex  =0; }
inline void Material::clearSpecTex () { if( _ownSpecTex  && _specTex >0 ) glDeleteTextures(1,&_specTex ); _specTex  =0; }
inline void Material::clearRoughTex() { if( _ownRoughTex && _roughTex>0 ) glDeleteTextures(1,&_roughTex); _roughTex =0; }
inline void Material::clearMetalTex() { if( _ownMetalTex && _metalTex>0 ) glDeleteTextures(1,&_metalTex); _metalTex =0; }
inline void Material::clearAlphaTex() { if( _ownAlphaTex && _alphaTex>0 ) glDeleteTextures(1,&_alphaTex); _alphaTex =0; }
inline void Material::clearAOccTex () { if( _aOccTex     && _aOccTex >0 ) glDeleteTextures(1,&_aOccTex ); _aOccTex  =0; }

inline void Material::diffTex ( GLuint id, bool ownership ) { clearDiffTex();	 _diffTex  = id; _ownDiffTex =ownership; }
inline void Material::armTex  ( GLuint id, bool ownership ) { clearArmTex();	 _armTex   = id; _ownArmTex  =ownership;  }
inline void Material::normTex ( GLuint id, bool ownership ) { clearNormTex();	 _normTex  = id; _ownNormTex =ownership;  }
inline void Material::specTex ( GLuint id, bool ownership ) { clearSpecTex();	 _specTex  = id; _ownSpecTex =ownership;  }
inline void Material::roughTex( GLuint id, bool ownership ) { clearRoughTex();	 _roughTex = id; _ownRoughTex=ownership;  }
inline void Material::metalTex( GLuint id, bool ownership ) { clearMetalTex();	 _metalTex = id; _ownMetalTex=ownership;  }
inline void Material::alphaTex( GLuint id, bool ownership ) { clearAlphaTex();	 _alphaTex = id; _ownAlphaTex=ownership;  }
inline void Material::aOccTex ( GLuint id, bool ownership ) { clearAOccTex();	 _aOccTex  = id; _ownAOccTex =ownership;  }

inline void Material::clearGL() {
	clearDiffTex();
	clearArmTex();
	clearNormTex();
	clearSpecTex();
	clearRoughTex();
	clearMetalTex();
	clearAlphaTex();
	clearAOccTex();
}

inline void		Material::diffTex( const std::filesystem::path& fn, const path_list& plist ) {
	diffTex( loadTex( fn, plist, true ), false );
}

inline void		Material::armTex( const std::filesystem::path& fn, const path_list& plist ) {
	armTex( loadTex( fn, plist, false ), true );
}

inline void		Material::normTex( const std::filesystem::path& fn, const path_list& plist ) {
	normTex( loadTex( fn, plist, false ), true );
}

inline void		Material::specTex( const std::filesystem::path& fn, const path_list& plist ) {
	specTex( loadTex( fn, plist, false ), true );
}

inline void		Material::roughTex( const std::filesystem::path& fn, const path_list& plist ) {
	roughTex( loadTex( fn, plist, false ), true );
}

inline void		Material::metalTex( const std::filesystem::path& fn, const path_list& plist ) {
	metalTex( loadTex( fn, plist, false ), true );
}

inline void		Material::alphaTex( const std::filesystem::path& fn, const path_list& plist ) {
	alphaTex( loadTex( fn, plist, false ), true );
}

inline void		Material::aOccTex( const std::filesystem::path& fn, const path_list& plist ) {
	aOccTex( loadTex( fn, plist, true ), true );
}

inline GLuint 	Material::loadTexture( const std::filesystem::path& fn, bool sRGB ) {
	GLuint tex = 0;
	float aniso = 0.0f;
	int w,h,n;
	stbi_set_flip_vertically_on_load(true);
	unsigned char* buf = stbi_load(fn.string().c_str(),&w, &h, &n, 4);
	if( !buf ) return 0;
	glGenTextures(1, &tex);
	glBindTexture(GL_TEXTURE_2D, tex);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT);
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT);
	glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, &aniso);
	glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, aniso);
	if( sRGB )	glTexImage2D(GL_TEXTURE_2D, 0, GL_SRGB8_ALPHA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, buf);
	else		glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, buf);
	glGenerateMipmap(GL_TEXTURE_2D);
	stbi_image_free(buf);
	return tex;
}

inline GLuint Material::loadTex( const std::filesystem::path& fn, const path_list& plist, bool sRGB ) {
	for( auto& p: plist ) {
		GLuint id = loadTexture( p/fn, sRGB );
		if( id>0 ) return id;
	}
	return 0;
}

inline void Material::bindTexture( GLuint prog, int slot, const std::string& targetName, GLuint tex ) {
	if( tex>0 ) {
		glActiveTexture(GL_TEXTURE0+slot);
		glBindTexture(GL_TEXTURE_2D,tex);
		setUniform( prog, targetName.c_str(), slot);
		setUniform( prog, (targetName+"Enabled").c_str(), 1);
	}
	else
		setUniform( prog, (targetName+"Enabled").c_str(), 0);
}

} // namespace JR

#endif /* _JR_Material_h */
