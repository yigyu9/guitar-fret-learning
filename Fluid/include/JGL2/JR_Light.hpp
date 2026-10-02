//
//  JR_Light.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/15/24.
//

#ifndef JR_Light_h
#define JR_Light_h

namespace JR {

struct PointLight {
	const float shadowZNear=100.f, shadowZFar=1000.f;
	const float shadowFov = 1.0f;
	
	PointLight( const vec3&	pos = {80,200,75}, const vec3& intensity = vec3(150000), float radius=3 )
	:_pos(pos), _intensity(intensity), _radius(radius){}
	
	virtual inline bool&		shadowing	() 				{ return _shadowing; }
	virtual inline vec3&		pos			() 				{ return _pos		; }
	virtual inline vec3&		intensity	() 				{ return _intensity; }
	virtual inline float&		radius		() 				{ return _radius	; }
	virtual inline bool&		enabled		() 				{ return _enabled  ; }

	virtual inline bool			shadowing	() const 		{ return _shadowing; }
	virtual inline const vec3&	pos			() const 		{ return _pos		; }
	virtual inline const vec3&	intensity	() const 		{ return _intensity; }
	virtual inline float		radius		() const 		{ return _radius	; }
	virtual inline bool			enabled		() const 		{ return _enabled  ; }

	virtual inline void			shadowing	(bool v) 		{ _shadowing=v; }
	virtual inline void			pos			(const vec3& v) { _pos		=v; }
	virtual inline void			intensity	(const vec3& v) { _intensity=v; }
	virtual inline void			radius		(float v)		{ _radius		=v; }
	virtual inline void			enabled		(bool v)		{ _enabled		=v; }

	virtual inline mat4			getShadowV(const vec3& c)	{ return lookAt(_pos, c, vec3(0,1,0)); }
	virtual inline mat4			getShadowP()				{ return perspective(shadowFov, 1.f, shadowZNear, shadowZFar); }
	
	virtual inline void			setUniforms(GLuint prog, int i, const vec3& c) {
		mat4 shadowV = getShadowV(c), shadowP = getShadowP();
		
		std::string lprefix = std::string("lights[")+std::to_string(i)+"].";
		setUniform(prog,lprefix+"enabled",		_enabled?1:0 );
		setUniform(prog,lprefix+"intensity",	_intensity );
		setUniform(prog,lprefix+"pos",			_pos );
		setUniform(prog,lprefix+"dir",			normalize( c-_pos ) );
		setUniform(prog,lprefix+"cosFov",		cosf(shadowFov/2) );
		
		std::string sprefix = std::string("shadowers[")+std::to_string(i)+"].";
		if( !_shadowing ) {
			setUniform(prog,sprefix+"shadowEnabled", 0);
		}
		else {
			_shadowMap.bindDepth(prog, sprefix+"map", 8+i);
			setUniform(prog,sprefix+"radius", 	_radius);
			setUniform(prog,sprefix+"enabled", 1);
			setUniform(prog,sprefix+"proj", shadowP );
			setUniform(prog,sprefix+"searchR", tanf(shadowFov/2)*shadowZNear );
			setUniform(prog,sprefix+"zNear", shadowZNear );
			setUniform(prog,sprefix+"zFar", shadowZFar );
			setUniform(prog,std::string("shadowBiasedVP[")+std::to_string(i)+"]",
					   translate(vec3(0.5))*scale(vec3(0.5))
					   *shadowP*shadowV);
		}
	}
	virtual inline void			prepareShadowMap(GLuint prog, const vec3& c, std::function<void()> renderFunc) {
		if( !_shadowing ) return;
		_shadowMap.create(2048,2048);
		_shadowMap.setToTarget();
		glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT);
		//		glEnable(GL_CULL_FACE);
		//		glCullFace(GL_FRONT);
		setUniform(prog,"modelMat", mat4(1));
		setUniform(prog,"projMat", getShadowP());
		setUniform(prog,"viewMat", getShadowV(c));
		renderFunc();
		_shadowMap.restoreVP();
		glDisable(GL_CULL_FACE);
	}
	bool	_enabled	= true;
	bool	_shadowing	= true;
	vec3	_pos		= {100,200,150};
	vec3	_intensity	= vec3(250000);
	float	_radius		= 1;
	FramebufferObj	_shadowMap;
};


struct AmbLight {
	virtual inline vec3*		coeff() { return _coeffs; }
	virtual inline const vec3*	coeff() const { return _coeffs; }
	virtual inline void			coeff(const vec3 v[]) {
		_coeffs[0]=v[0];	_coeffs[1]=v[1];	_coeffs[2]=v[2];
		_coeffs[3]=v[3];	_coeffs[4]=v[4];	_coeffs[5]=v[5];
		_coeffs[6]=v[6];	_coeffs[7]=v[7];	_coeffs[8]=v[8];
	}

	virtual inline float&		factor() { return _factor; }
	virtual inline const float&	factor() const { return _factor; }
	virtual inline void			factor(float v) { _factor=v; }

	virtual inline void			use(GLuint prog) {
		setUniform(prog,"ambCoeffs",	_coeffs, 9);
		setUniform(prog,"ambFactor",	_factor );
	}
	static  inline void			unuse(GLuint prog) {
		setUniform(prog,"ambFactor",	0 );
	}

protected:
	vec3 _coeffs[9] = {
		vec3( 2.136610,  2.136610,  2.136610),
		vec3( 1.200665,  1.200665,  1.200665),
		vec3(-0.319614, -0.319614, -0.319614),
		vec3(-0.718034, -0.718034, -0.718034),
		vec3(-0.101370, -0.101370, -0.101370),
		vec3(-0.183365, -0.183365, -0.183365),
		vec3(-0.191558, -0.191558, -0.191558),
		vec3( 0.387255,  0.387255,  0.387255),
		vec3(-0.021659, -0.021659, -0.02165)};
	float	_factor = 0.3f;
};

} // namespace JR

#endif /* JR_Light_h */
