//
//  JR_Renderer.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/14/24.
//

#ifndef _JR_Renderer_h
#define _JR_Renderer_h

#include "JR_FramebufferObj.hpp"
#include "JR_Light.hpp"
#include <functional>

namespace JR {

typedef std::function<void()> RenderFunc;

struct Renderer {
	virtual void render(const sz2_t& sz,Camera& c)=0;
	virtual ~Renderer(){}
	
	virtual inline void	renderFunc(RenderFunc f) { _renderFunc = f; }
	virtual inline void resetRenderFunc() { _renderFunc = defRenderFunc; }
	
	virtual inline void	wireFunc(RenderFunc f) { _wireFunc = f; }
	virtual inline void resetWireFunc() { _wireFunc = defRenderFunc; }
	virtual inline void copyFrom(const Renderer& r);
	virtual inline void copyFrom(const Renderer* r) { copyFrom(*r); }
	
	const RenderFunc defRenderFunc = [](){};
	RenderFunc _renderFunc = defRenderFunc;
	RenderFunc _wireFunc   = defRenderFunc;
};
inline void Renderer::copyFrom(const Renderer& r) {
	_renderFunc = r._renderFunc;
	_wireFunc = r._wireFunc;
}

struct NullRenderer: Renderer {
	virtual inline void render(const sz2_t& sz,Camera& c) override {
		_renderFunc();
	}
};



extern const std::string __const_frag_code__;
extern const std::string __const_vert_code__;
extern const std::string __shader_frag_code__;
extern const std::string __shader_vert_code__;

extern const std::string __shader_frag_header__;
extern const std::string __shader_frag_main__;
extern const std::string __shader_frag_shadow_header__;
extern const std::string __shader_frag_lighting_point_header__;

extern const std::string __shader_frag_tonemap__;
extern const std::string __shader_frag_normal__;
extern const std::string __shader_frag_material__;

extern const std::string __shader_frag_lighting_point_Lambertian__;
extern const std::string __shader_frag_lighting_point_Phong__;
extern const std::string __shader_frag_lighting_point_PBR__;

extern const std::string __shader_frag_shadow_null__;
extern const std::string __shader_frag_shadow_PCF__;
extern const std::string __shader_frag_shadow_PCSS__;

extern const std::string __shader_frag_ambOcc_null__;
extern const std::string __shader_frag_ambient_const__;
extern const std::string __shader_frag_ambient_spherical__;



struct PBRRenderer: Renderer {
	PBRRenderer();
	virtual 		void			render(const sz2_t& sz, Camera& c);
	static	inline	Program&		getRenderProg();
	static	inline	Program&		getConstProg();
	virtual inline	float			ambientFactor() const { return _ambientLight.factor(); }
	virtual inline	void			ambientFactor(float v) { _ambientLight.factor(v); }
	virtual inline	AmbLight&		ambientLight() { return _ambientLight; }
	virtual inline	const AmbLight&	ambientLight() const { return _ambientLight; }
	virtual inline	void			addPointLight(PointLight&& l);
	virtual inline	void			addPointLight(const PointLight& l);
	virtual inline	size_t			pointLights() const { return _pointLights.size(); }
	virtual inline	PointLight&		pointLight(size_t i) { return _pointLights[i]; }
	virtual inline	const PointLight&	pointLight(size_t i) const { return _pointLights[i]; }

protected:
	std::vector<PointLight>	_pointLights;
	AmbLight				_ambientLight;
	vec3					_screenGamma = vec3(2.4);
	mat3					_sRGB2Screen = mat3(1);
	
	virtual inline	void	shadowPass(const Camera& c);
	virtual inline	void	mainPass(const Camera& c);
	virtual inline	void	wirePass(const Camera& c);
};

inline PBRRenderer::PBRRenderer(): Renderer() {
	addPointLight({});
}

inline void PBRRenderer::shadowPass(const Camera& camera) {
	Program& const_Prog = getConstProg();
	const_Prog.use();
	for( int i=0; i<_pointLights.size(); i++)
		_pointLights[i].prepareShadowMap(const_Prog.progId, camera.sceneCenter(),_renderFunc);
}

inline void PBRRenderer::wirePass(const Camera& camera) {
	Program& const_Prog = getConstProg();
	glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);
	glLineWidth(.2f);
	const_Prog.use();
	const_Prog.setUniform("color", vec4(0,0,0,.2));
	const_Prog.setUniform("modelMat", mat4(1));
	camera.setUniforms(const_Prog.progId);
	_wireFunc();
	glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
}

inline void PBRRenderer::mainPass(const Camera& camera) {
	Program& renderProg = getRenderProg();
	renderProg.use();
	camera.setUniforms(renderProg.progId);
	renderProg.setUniform("color",		vec4(.8,.8,.8,1) );
	renderProg.setUniform("modelMat",	mat4(1));
	renderProg.setUniform("sRGB2ScreenRGB", _sRGB2Screen );
	renderProg.setUniform("screenGamma", _screenGamma);
	_ambientLight.use( renderProg.progId );
	
	for( int i=0; i<_pointLights.size(); i++)
		_pointLights[i].setUniforms( renderProg.progId, i, camera.sceneCenter() );
	_renderFunc();
}

inline void PBRRenderer::render(const sz2_t& sz, Camera& camera) {
	glEnable(GL_DEPTH_TEST);
	glDepthFunc(GL_LEQUAL);
	camera.viewport(sz);
	shadowPass(camera);
	mainPass(camera);
	wirePass(camera);
}

inline Program& PBRRenderer::getRenderProg() {
	static AutoBuildProgram _renderProg = {__shader_vert_code__, __shader_frag_code__};
	_renderProg.use();
	return _renderProg;
}
inline Program& PBRRenderer::getConstProg() {
	static AutoBuildProgram _const_Prog = {__const_vert_code__, __const_frag_code__};
	_const_Prog.use();
	return _const_Prog;
}

inline	void PBRRenderer::addPointLight(PointLight&& l) {
	_pointLights.push_back(l);
}
inline	void PBRRenderer::addPointLight(const PointLight& l) {
	_pointLights.push_back(l);
}


const std::string __const_vert_code__ =
"#version 410 core\n"
"layout(location=0) in vec3 in_Position;\n"
"uniform mat4 viewMat = mat4(1);\n"
"uniform mat4 projMat = mat4(1);\n"
"uniform mat4 modelMat = mat4(1);\n"
"void main(void) {\n"
"	vec4 worldPos4 = modelMat* vec4( in_Position, 1. );\n"
"	gl_Position= projMat*viewMat* worldPos4;\n"
"}\n";

const std::string __const_frag_code__ =
"#version 410 core\n"
"uniform vec4 color = vec4(1);\n"
"uniform mat4 viewMat = mat4(1);\n"
"out vec4 out_Color;\n"
"void main(void) {\n"
"	out_Color = vec4( pow(color.rgb,vec3(1/2.2)), color.a);\n"
"//	out_Color = vec4( vec3(gl_FragCoord.z), color.a);\n"
"}\n";

const std::string __shader_vert_code__ =
"#version 410 core\n"
"layout(location=0) in vec3 in_Position;\n"
"layout(location=1) in vec3 in_Normal;\n"
"layout(location=2) in vec2 in_TexCoord;\n"
"#define MAX_N_LIGHTS 1\n"
"uniform mat4 viewMat = mat4(1);\n"
"uniform mat4 projMat = mat4(1);\n"
"uniform mat4 modelMat = mat4(1);\n"
"uniform mat3 texMat = mat3(1);\n"
"uniform mat4 shadowBiasedVP[MAX_N_LIGHTS];\n"
"out vec3 normal;\n"
"out vec4 shadowCoord[MAX_N_LIGHTS];\n"
"out vec3 worldPos;\n"
"out vec2 texCoord;\n"
"void main(void) {\n"
"	vec4 worldPos4 = modelMat* vec4( in_Position, 1. );\n"
"	normal    = normalize( (modelMat* vec4(in_Normal,0)).xyz );\n"
"	for( int i=0; i<MAX_N_LIGHTS; i++ ) shadowCoord[i] = shadowBiasedVP[i] * worldPos4;\n"
"	gl_Position= projMat*viewMat* worldPos4;\n"
"	worldPos = worldPos4.xyz;\n"
"	texCoord = vec2(texMat*vec3(in_TexCoord,1));\n"
"}\n";










const std::string __shader_frag_header__ =
"#version 410 core\n"
"const float PI = 3.1415926;\n"
"in vec3 worldPos;\n"
"in vec3 normal;\n"
"in vec2 texCoord;\n"
"out vec4 out_Color;\n"
"uniform vec3  cameraPos;\n";

const std::string __shader_frag_shadow_header__ =
"struct Shadower {\n"
"	float radius;\n"
"	int   enabled;\n"
"	float zNear;\n"
"	float zFar;\n"
"	float searchR;\n"
"	mat4  proj;\n"
"	sampler2D map;\n"
"};\n"
"uniform Shadower shadowers[MAX_N_LIGHTS];\n"
"in vec4 shadowCoord[MAX_N_LIGHTS];\n"
"float rand(vec2 co){ return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453); }\n"
"vec2 vogelSample( int i, int cnt, float offset) {\n"
"	const float GoldenAngle = 2.4;\n"
"	float idx = float(i);\n"
"	float theta = idx*GoldenAngle+offset;\n"
"	return vec2( cos(theta), sin( theta ) ) * pow((sqrt(idx+0.1)/sqrt(float(cnt))),1);\n"
"}\n";

const std::string __shader_frag_lighting_point_header__ =
"struct Light {\n"
"	vec3  pos;\n"
"	vec3  dir;\n"
"	vec3  intensity;\n"
"	float cosFov;\n"
"};\n"
"#define MAX_N_LIGHTS 1\n"
"uniform Light lights[MAX_N_LIGHTS];"
"uniform int nLights = 1;\n";

const std::string __shader_frag_main__ =
"void main(void) {\n"
"	vec3 N = computeNormal();\n"
"	vec3 V = normalize(cameraPos-worldPos);\n"
"	vec3 f0, arm, c = vec3(0);\n"
"	vec4 color = computeMaterial( arm, f0 );\n"
"	for( int i=0; i<nLights; i++ ) {\n"
"		float shadowing = computeShadowing( i, normalize(lights[i].pos-worldPos), normal );\n"
"		c += computePointLighting(N, V, color.rgb, arm, f0, i ) * shadowing;\n"
"	}\n"
"	float ambOcc = computeAmbOcc()*arm.r;\n"
"	vec3 am = computeAmbient( color.rgb, arm, N )*ambOcc;\n"
"	out_Color = vec4( computeTonemap( c+am ), color.a);\n"
"}\n";













const std::string __shader_frag_tonemap__ =
"uniform int useAdvancedTonemap=1;\n"
"uniform vec3 screenGamma=vec3(2.4);\n"
"uniform mat3 sRGB2ScreenRGB=mat3(1);\n"
"float tonemap_sRGB(float u) {\n"
"	float u_ = abs(u);\n"
"	return  u_>0.0031308?( sign(u)*1.055*pow( u_,0.41667)-0.055):(12.92*u);\n"
"}\n"
"float tonemap(float c, float g) {\n"
"	if( abs( g-2.4) <0.01 ) return tonemap_sRGB(c);\n"
"	else						return sign(c)*pow(abs(c),1/g);\n"
"}\n"
"vec3 tonemap( vec3 rgb, mat3 csc, vec3 gamma ){\n"
"	vec3 rgb_ = csc*rgb;\n"
"	return vec3(tonemap(rgb.r,gamma.r),tonemap(rgb.g,gamma.g),tonemap(rgb.b,gamma.b));\n"
"}\n"
"float inverseTonemap_sRGB(float u) {\n"
"	float u_ = abs(u);\n"
"	return u_>0.04045?(sign(u)*pow((u_+0.055)/1.055,2.4)):(u/12.92);\n"
"}\n"
"float inverseTonemap(float c, float g) {\n"
"	if( abs( g-2.4) <0.01 ) return inverseTonemap_sRGB(c);\n"
"	else						return sign(c)*pow(abs(c),g);\n"
"}\n"
"vec3 inverseTonemap( vec3 rgb, mat3 csc, vec3 gamma ){\n"
"	return csc*vec3(inverseTonemap(rgb.r,gamma.r),inverseTonemap(rgb.g,gamma.g),inverseTonemap(rgb.b,gamma.b));\n"
"}\n"
"vec3 computeTonemap( vec3 c) {\n"
"	if( useAdvancedTonemap> 0 )	return tonemap(c,sRGB2ScreenRGB,screenGamma);\n"
"	else						return pow(c,vec3(1/2.2));\n"
"}\n";











const std::string __shader_frag_normal__ =
"uniform sampler2D normalTex;\n"
"uniform int   normalTexEnabled=0;\n"
"uniform int   bumpMapped=0;\n"
"uniform int   normalMapDX=0;\n"
"\n"
"float difTex( sampler2D tex, vec2 x, vec2 dv) {\n"
"	return (texture(tex,x+dv).r-texture(tex,x-dv).r)*10.;\n"
"}\n"
"mat3 getTBN( vec3 N ) {\n"
"	vec3 Q1 = dFdx(worldPos), Q2 = dFdy(worldPos);\n"
"	vec2 st1 = dFdx(texCoord), st2 = dFdy(texCoord);\n"
"	float D = st1.s*st2.t-st2.s*st1.t;\n"
"	return mat3(normalize( ( Q1*st2.t - Q2*st1.t )*D),\n"
"				normalize( (-Q1*st2.s + Q2*st1.s )*D), N);\n"
"}\n"
"vec3 computeNormal() {"
"	vec3 N = normalize( normal );\n"
"	N = sign( dot( cross( dFdx(worldPos), dFdy(worldPos) ), N) )*N;"
"	if( normalTexEnabled>0 ) {\n"
"		vec3 normalMapCorrection = vec3(1,1,1);\n"
"		if( normalMapDX>0 ) normalMapCorrection = vec3(1,-1,1);\n"
"		if( bumpMapped>0 )	N = normalize( getTBN(N)*vec3(-difTex(normalTex,texCoord,vec2(0.0001,0)),-difTex(normalTex,texCoord,vec2(0,0.0001)),1) );\n"
"		else				N = normalize( getTBN(N)*(normalMapCorrection*(texture(normalTex,texCoord).rgb*2-vec3(1))));\n"
"	}\n"
"	return N;\n"
"}\n";












const std::string __shader_frag_lighting_point_Lambertian__ =
__shader_frag_lighting_point_header__+
"vec3 computePointLighting( vec3 N, vec3 V, vec3 color, vec3 arm, vec3 f0, int i ) {\n"
"	vec3 l = lights[i].pos-worldPos;\n"
"	vec3 L = normalize( l );\n"
"	float spotFactor = smoothstep( lights[i].cosFov, lights[i].cosFov+.05f, dot( normalize( -L ), lights[i].dir ));\n"
"	vec3 Li = lights[i].intensity/dot(l,l)*spotFactor;\n"
"	return max(dot(L,N),0)/PI*color*Li;\n"
"}\n";

const std::string __shader_frag_lighting_point_Phong__ =
__shader_frag_lighting_point_header__+
"vec3 BRDF(vec3 n, vec3 l, vec3 v, float percRough, vec3 color, float metal, vec3 f0 ) {\n"
"	vec3 albedo = mix( color, vec3(0), metal );"
"	vec3 F0 = mix( f0, color, metal );"
"	float a = percRough * percRough;\n"
"	float sh = 2/(a*a)-2;\n"
"	float ks = pow(10,0.2391*log(sh)/log(10)-1.4907)/0.04;\n"
"	vec3 r = reflect(-l,n);\n"
"	vec3 Fr = F0*pow(max(0,dot(r,v)),sh)*ks;\n"
"	// diffuse BRDF\n"
"	vec3 Fd = albedo * 1/PI * max(0,dot(n,l));\n"
"	return Fr+Fd;\n"
"}\n"
"vec3 computePointLighting( vec3 N, vec3 V, vec3 color, vec3 arm, vec3 f0, int i ) {\n"
"	vec3 l = lights[i].pos-worldPos;\n"
"	vec3 L = normalize( l );\n"
"	float spotFactor = smoothstep( lights[i].cosFov, lights[i].cosFov+.05f, dot( normalize( -L ), lights[i].dir ));\n"
"	vec3 Li = lights[i].intensity/dot(l,l)*spotFactor;\n"
"	return BRDF( N, L, V, arm.g, color, arm.b, f0 )*Li;\n"
"}\n";

const std::string __shader_frag_lighting_point_PBR__ =
__shader_frag_lighting_point_header__+
"float D_GGX(float NoH, float a2) {\n"
"	float f = (NoH * a2 - NoH) * NoH + 1.0;\n"
"	return a2 / (PI * f * f);\n"
"}\n"
"vec3 F_Schlick(float u, vec3 f0) {\n"
"	return mix( f0, vec3(1), pow(1.0 - u, 5.0) );\n"
"}\n"
"float V_SmithGGXCorrelated(float NoV, float NoL, float a2) {\n"
"	float GGXL = NoV * sqrt((-NoL * a2 + NoL) * NoL + a2);\n"
"	float GGXV = NoL * sqrt((-NoV * a2 + NoV) * NoV + a2);\n"
"	return min(1, 0.5 / (GGXV + GGXL));\n"
"}\n"
"float V_CookTorrance(float NoV, float NoL, float a2, float NoH, float VoH) {\n"
"	return min(1, 2*NoH/VoH*min(NoV,NoL));\n"
"}\n"
"float Fd_Lambert() { return 1.0 / PI; }\n"
"vec3 BRDF(vec3 n, vec3 l, vec3 v, float percRough, vec3 color, float metal, vec3 f0 ) {\n"
"	vec3 h = normalize(v + l);\n"
"	float NoV = clamp(dot(n, v), 0.001, 1.0);\n"
"	float NoL = clamp(dot(n, l), 0., 1.0);\n"
"	float NoH = clamp(dot(n, h), 0.0, 1.0);\n"
"	float VoH = clamp(dot(v, h), 0.0, 1.0);\n"
"	vec3 albedo = mix( color, vec3(0), metal );"
"	vec3 F0 = mix( f0, color, metal );"
"	// perceptually linear roughness to roughness\n"
"	float a = percRough * percRough;\n"
"	float a2 = a*a;\n"
"	// specular BRDF\n"
"	float D = D_GGX(NoH, a2);\n"
"	vec3  F = F_Schlick(VoH, F0);\n"
//"	float V = V_SmithGGXCorrelated(NoV, NoL, a2);\n"
"	float V = V_CookTorrance(NoV,NoL,a2,NoH,VoH);\n"
"	vec3 Fr = clamp( (D * V), 0, 1 ) * F/(NoV*4*max(0.001,NoL));\n"
"	// diffuse BRDF\n"
"	vec3 Fd = albedo * Fd_Lambert();\n"
"	return (Fr+Fd)*NoL;\n"
"}\n"
"vec3 computePointLighting( vec3 N, vec3 V, vec3 color, vec3 arm, vec3 f0, int i ) {\n"
"	vec3 l = lights[i].pos-worldPos;\n"
"	vec3 L = normalize( l );\n"
"	float spotFactor = smoothstep( lights[i].cosFov, lights[i].cosFov+.05f, dot( normalize( -L ), lights[i].dir ));\n"
"	vec3 Li = lights[i].intensity/dot(l,l)*spotFactor;\n"
"	return BRDF( N, L, V, arm.g, color, arm.b, f0 )*Li;\n"
"}\n";














const std::string __shader_frag_shadow_null__ =
"float computeShadowing( int i, vec3 n, vec3 l ) { return 1; }\n";

const std::string __shader_frag_shadow_PCF__ =
__shader_frag_shadow_header__+
"const int N_SHADOW_SAMPLE = 64;\n"
"float sampleShadow(vec3 sCoord, float rad, float bias, sampler2D map, float randomNumber ) {\n"
"	const float sampleVis = 1./float(N_SHADOW_SAMPLE);\n"
"	float vis = 1;\n"
"	float r = max( rad, 0.0001 );\n"
"	for (int i=0;i<N_SHADOW_SAMPLE;i++) {\n"
"		vec2 offset = vogelSample( i, N_SHADOW_SAMPLE, randomNumber );\n"
"		if( texture( map, sCoord.xy+ r*offset ).x < sCoord.z-bias ) vis -= sampleVis;\n"
"	}\n"
"	return vis;\n"
"}\n"
"float PCF( vec3 sCoord, float radius, float bias, sampler2D map, vec3 n, vec3 l ) {\n"
"	float randomNumber = rand( gl_FragCoord.xy )*PI;\n"
"	float tbias = clamp(tan(acos(dot(n,l))),0,1)*bias+bias;\n"
"	return sampleShadow( sCoord, radius*0.0005, tbias, map, randomNumber );\n"
"}\n"
"float computeShadowing( int i, vec3 n, vec3 l ) {\n"
"	if( shadowers[i].enabled <1 ) return 1;\n"
"	return PCF( shadowCoord[i].xyz/shadowCoord[i].w, shadowers[i].radius, 0.0005, shadowers[i].map, n, l );\n"
"}\n";

const std::string __shader_frag_shadow_PCSS__ =
__shader_frag_shadow_header__+
"const int N_SHADOW_SAMPLE = 64;\n"
"const int N_BLOCKER_SAMPLE = 32;\n"
"float linearDepth( float d, float near, float far ) { return -2.0 * near * far / (far + near - (2.0 * d - 1.0) * (far - near)); }\n"
"vec3 project( mat4 proj, vec3 p ) { vec4 pos = proj*vec4(p,1); return pos.xyz/pos.w; }\n"
"float sampleShadow(vec3 sCoord, float rad, float bias, sampler2D map, float randomNumber ) {\n"
"	const float sampleVis = 1./float(N_SHADOW_SAMPLE);\n"
"	float vis = 1;\n"
"	float r = max( rad, 0.0001 );\n"
"	for (int i=0;i<N_SHADOW_SAMPLE;i++) {\n"
"		vec2 offset = vogelSample( i, N_SHADOW_SAMPLE, randomNumber );\n"
"		if( texture( map, sCoord.xy+ r*offset ).x < sCoord.z-bias ) vis -= sampleVis;\n"
"	}\n"
"	return smoothstep(0.0f,0.8f,vis);\n"
//"	return vis;\n"
"}\n"
"float blockerSearch( vec3 sCoord, float searchR, float bias, sampler2D map, float randomNumber ) {\n"
"	float blockerDepth = 0.;\n"
"	int numBlockers = 0;\n"
"	for( int i = 0; i < N_BLOCKER_SAMPLE; ++i ) {\n"
"		vec2 offset = vogelSample( i, N_BLOCKER_SAMPLE, randomNumber );\n"
"		float shadowMapDepth = texture( map, sCoord.xy + searchR*offset ).r;\n"
"		if ( shadowMapDepth < sCoord.z-bias ) {\n"
"			blockerDepth += shadowMapDepth;\n"
"			numBlockers++;\n"
"		}\n"
"	}\n"
"	if (numBlockers < 1 ) return 0.001;\n"
"	return blockerDepth / float(numBlockers);\n"
"}\n"
"float PCSS( vec3 sCoord, float radius, float sr, float bias, float near, float far, mat4 proj, sampler2D map, vec3 n, vec3 l ) {\n"
"	float tbias = clamp(tan(acos(dot(n,l))),0,2)*bias+bias;\n"
"	float randomNumber = rand( gl_FragCoord.xy )*PI;\n"
"	float zEye = -linearDepth( sCoord.z, near, far );\n"
"	float searchR = radius*(zEye - near) / zEye/sr *.5;\n"
"	float blockerDepth = blockerSearch( sCoord, searchR, bias*2, map, randomNumber );\n"
"	blockerDepth = -linearDepth( blockerDepth, near, far );\n"
"	float penum = radius * (zEye - blockerDepth) / blockerDepth / sr *.5;\n"
"	return sampleShadow( sCoord, penum, tbias, map, randomNumber );\n"
"}\n"
"float computeShadowing( int i, vec3 n, vec3 l ) {\n"
"	if( shadowers[i].enabled <1 ) return 1;\n"
"	return PCSS( shadowCoord[i].xyz/shadowCoord[i].w, shadowers[i].radius, shadowers[i].searchR, 0.0005,\n"
"				shadowers[i].zNear, shadowers[i].zFar, shadowers[i].proj, shadowers[i].map, n, l );\n"
"}\n";











const std::string __shader_frag_ambient_const__ =
"uniform vec3  ambCoeffs[9];\n"
"uniform float ambFactor = .25;\n"
"vec3 computeAmbient( vec3 color, vec3 arm, vec3 N ) {\n"
"	return color*mix(1.f,0.2f,arm.b)*ambCoeffs[0]*ambFactor/PI*2;\n"
"}\n";

const std::string __shader_frag_ambient_spherical__ =
"vec3 evalSphericalHarmonic( vec3 N, vec3 coeff[9] ) {\n"
"	const float iblRotationTheta = 0.;\n"
"	float c = cos( iblRotationTheta ), s = sin( iblRotationTheta );\n"
"	vec2 rr= mat2(c, -s, s, c)*N.xz;\n"
"	vec3 v = vec3( rr.x, N.y, rr.y );\n"
"	vec3 col= coeff[0]\n"
"		+ coeff[1]*v.y     + coeff[2]*v.z               + coeff[3]*v.x\n"
"		+ coeff[4]*v.x*v.y + coeff[5]*v.y*v.z           + coeff[6]*(v.z*v.z-0.3333328848)\n"
"		+ coeff[7]*v.x*v.z + coeff[8]*(v.x*v.x-v.y*v.y);\n"
"	return col;\n"
"}\n"
"uniform vec3  ambCoeffs[9];\n"
"uniform float ambFactor = .25;\n"
"vec3 computeAmbient( vec3 color, vec3 arm, vec3 N ) {\n"
"	return color*mix(1.f,0.2f,arm.b)*evalSphericalHarmonic(N,ambCoeffs).rgb*ambFactor/PI*2;\n"
"}\n";

const std::string __shader_frag_ambOcc_null__ =
"float computeAmbOcc() {\n"
"	return 1;\n"
"}\n";


const std::string __shader_frag_material__ =
"uniform vec4  color = vec4(1);\n"
"uniform float roughness = .3;\n"
"uniform float metalness = 0;\n"
"uniform vec3  F0=vec3(0.046);\n"
"uniform sampler2D diffTex;\n"
"uniform sampler2D armTex;\n"
"uniform sampler2D roughTex;\n"
"uniform sampler2D alphaTex;\n"
"uniform sampler2D specTex;\n"
"uniform sampler2D metalTex;\n"
"uniform sampler2D ambOccTex;\n"
"uniform int   diffTexEnabled=0;\n"
"uniform int   armTexEnabled=0;\n"
"uniform int   roughTexEnabled=0;\n"
"uniform int   alphaTexEnabled=0;\n"
"uniform int   specTexEnabled=0;\n"
"uniform int   metalTexEnabled=0;\n"
"uniform int   ambOccTexEnabled=0;\n"
"\n"
"vec4 computeMaterial(out vec3 arm, out vec3 f0) {\n"
"	vec4 diffColor = color;\n"
"	f0 = F0;\n"
"	arm = vec3(1,roughness,metalness);\n"
"	if( diffTexEnabled  >0 ) diffColor 		= texture(diffTex,  texCoord);\n"
"	if( ambOccTexEnabled>0 ) arm.r			= texture(ambOccTex,texCoord).r;\n"
"	if( roughTexEnabled >0 ) arm.g			= texture(roughTex, texCoord).r;\n"
"	if( alphaTexEnabled >0 ) diffColor.a	= texture(alphaTex, texCoord).r;\n"
"	if( specTexEnabled  >0 ) f0				= texture(specTex,  texCoord).rgb;\n"
"	if( metalTexEnabled >0 ) arm.b			= texture(metalTex, texCoord).r;\n"
"	if( armTexEnabled   >0 ) arm			= texture(armTex,   texCoord).rgb;\n"
"	return diffColor;\n"
"}\n"
"\n";



const std::string __shader_frag_code__ =
__shader_frag_header__
+ __shader_frag_tonemap__
+ __shader_frag_normal__
+ __shader_frag_ambient_spherical__
+ __shader_frag_lighting_point_PBR__
+ __shader_frag_shadow_PCSS__
//+ __shader_frag_shadow_null__
+ __shader_frag_ambOcc_null__
+ __shader_frag_material__
+ __shader_frag_main__;


const std::string __shader_frag_code1__ =
__shader_frag_header__
+ __shader_frag_tonemap__
+ __shader_frag_normal__
+ __shader_frag_ambient_spherical__
+ __shader_frag_lighting_point_Lambertian__
+ __shader_frag_shadow_PCF__
+ __shader_frag_ambOcc_null__
+ __shader_frag_material__
+ __shader_frag_main__;
























/*
const std::string __shader_frag_code__ =
"#version 410 core\n"
"const float PI = 3.1415926;\n"
"\n"
"in vec3 worldPos;\n"
"in vec3 normal;\n"
"in vec2 texCoord;\n"
"in vec3 viewNormal;\n"
"out vec4 out_Color;\n"
"uniform vec3  cameraPos;\n"
"\n"
"\n"
"\n"
"\n"
"uniform int useAdvancedTonemap=1;\n"
"uniform vec3 screenGamma=vec3(2.4);\n"
"uniform mat3 sRGB2ScreenRGB=mat3(1);\n"
"float tonemap_sRGB(float u) {\n"
"	float u_ = abs(u);\n"
"	return  u_>0.0031308?( sign(u)*1.055*pow( u_,0.41667)-0.055):(12.92*u);\n"
"}\n"
"float tonemap(float c, float g) {\n"
"	if( abs( g-2.4) <0.01 ) return tonemap_sRGB(c);\n"
"	else						return sign(c)*pow(abs(c),1/g);\n"
"}\n"
"vec3 tonemap( vec3 rgb, mat3 csc, vec3 gamma ){\n"
"	vec3 rgb_ = csc*rgb;\n"
"	return vec3(tonemap(rgb.r,gamma.r),tonemap(rgb.g,gamma.g),tonemap(rgb.b,gamma.b));\n"
"}\n"
"float inverseTonemap_sRGB(float u) {\n"
"	float u_ = abs(u);\n"
"	return u_>0.04045?(sign(u)*pow((u_+0.055)/1.055,2.4)):(u/12.92);\n"
"}\n"
"float inverseTonemap(float c, float g) {\n"
"	if( abs( g-2.4) <0.01 ) return inverseTonemap_sRGB(c);\n"
"	else						return sign(c)*pow(abs(c),g);\n"
"}\n"
"vec3 inverseTonemap( vec3 rgb, mat3 csc, vec3 gamma ){\n"
"	return csc*vec3(inverseTonemap(rgb.r,gamma.r),inverseTonemap(rgb.g,gamma.g),inverseTonemap(rgb.b,gamma.b));\n"
"}\n"
"vec3 computeTonemap( vec3 c) {\n"
"	if( useAdvancedTonemap> 0 )	return tonemap(c,sRGB2ScreenRGB,screenGamma);\n"
"	else						return pow(c,vec3(1/2.2));\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"struct Light {\n"
"	vec3  pos;\n"
"	vec3  dir;\n"
"	vec3  intensity;\n"
"	float cosFov;\n"
"	vec2  radius;\n"
"	int   shadowEnabled;\n"
"	float zNear;\n"
"	float zFar;\n"
"	mat4  proj;\n"
"	sampler2D shadowMap;\n"
"};\n"
"#define MAX_N_LIGHTS 1\n"
"uniform Light lights[MAX_N_LIGHTS];"
"uniform int nLights = 1;\n"
"in vec4 shadowCoord[MAX_N_LIGHTS];\n"
"\n"
"float D_GGX(float NoH, float a2) {\n"
"	float f = (NoH * a2 - NoH) * NoH + 1.0;\n"
"	return a2 / (PI * f * f);\n"
"}\n"
"vec3 F_Schlick(float u, vec3 f0) {\n"
"	return mix( f0, vec3(1), pow(1.0 - u, 5.0) );\n"
"}\n"
"float V_SmithGGXCorrelated(float NoV, float NoL, float a2) {\n"
"	float GGXL = NoV * sqrt((-NoL * a2 + NoL) * NoL + a2);\n"
"	float GGXV = NoL * sqrt((-NoV * a2 + NoV) * NoV + a2);\n"
"	return min(1, 0.5 / (GGXV + GGXL));\n"
"}\n"
"float Fd_Lambert() { return 1.0 / PI; }\n"
"vec3 BRDF(vec3 n, vec3 l, vec3 v, float percRough, vec3 color, float metal, vec3 f0 ) {\n"
"	vec3 h = normalize(v + l);\n"
"	float NoV = clamp(dot(n, v), 0.01, 1.0);\n"
"	float NoL = clamp(dot(n, l), 0.0, 1.0);\n"
"	float NoH = clamp(dot(n, h), 0.0, 1.0);\n"
"	float LoH = clamp(dot(l, h), 0.0, 1.0);\n"
"	vec3 albedo = mix( color, vec3(0), metal );"
"	vec3 F0 = mix( f0, color, metal );"
"	// perceptually linear roughness to roughness\n"
"	float a = percRough * percRough;\n"
"	float a2 = a*a;\n"
"	// specular BRDF\n"
"	float D = D_GGX(NoH, a2);\n"
"	vec3  F = F_Schlick(LoH, F0);\n"
"	float V = V_SmithGGXCorrelated(NoV, NoL, a2);\n"
"	vec3 Fr = clamp( (D * V) * F, vec3(0), vec3(1) )/(NoV*4*max(0.0001,NoL))*NoL;\n"
"	// diffuse BRDF\n"
"	vec3 Fd = albedo * Fd_Lambert() * NoL;\n"
"	return Fr+Fd;\n"
"}\n"
"vec3 computePointLighting( vec3 N, vec3 V, vec3 color, vec3 arm, vec3 f0, int i ) {\n"
"	vec3 l = lights[i].pos-worldPos;\n"
"	vec3 L = normalize( l );\n"
"	float spotFactor = smoothstep( lights[i].cosFov, lights[i].cosFov+.05, dot( normalize( -L ), lights[i].dir ));\n"
"	vec3 Li = lights[i].intensity/dot(l,l)*spotFactor;\n"
"	return BRDF( N, L, V, arm.g, color, arm.b, f0 )*Li;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"const int N_SHADOW_SAMPLE = 64;\n"
"const int N_BLOCKER_SAMPLE = 32;\n"
"float rand(vec2 co){ return fract(sin(dot(co.xy ,vec2(12.9898,78.233))) * 43758.5453); }\n"
"float linearDepth( float d, float near, float far ) { return -2.0 * near * far / (far + near - (2.0 * d - 1.0) * (far - near)); }\n"
"vec3 project( mat4 proj, vec3 p ) { vec4 pos = proj*vec4(p,1); return pos.xyz/pos.w; }\n"
"vec2 vogelSample( int i, int cnt, float offset) {\n"
"	const float GoldenAngle = 2.4;\n"
"	float idx = float(i);\n"
"	float theta = idx*GoldenAngle+offset;\n"
"	return vec2( cos(theta), sin( theta ) ) * (sqrt(idx+0.5)/sqrt(float(cnt)));\n"
"}\n"
"float sampleShadow(vec3 sCoord, vec2 rad, float bias, sampler2D map, float randomNumber ) {\n"
"	const float sampleVis = 1./float(N_SHADOW_SAMPLE);\n"
"	float vis = 1;\n"
"	vec2 r = max( rad, vec2(0.002) );\n"
"	for (int i=0;i<N_SHADOW_SAMPLE;i++) {\n"
"		vec2 offset = vogelSample( i, N_SHADOW_SAMPLE, randomNumber );\n"
"		if( texture( map, sCoord.xy+ r*offset ).x < sCoord.z-bias ) vis -= sampleVis;\n"
"	}\n"
"	return vis;\n"
"}\n"
"float blockerSearch( vec3 sCoord, vec2 searchR, float bias, sampler2D map, float randomNumber ) {\n"
"	float blockerDepth = 0.;\n"
"	int numBlockers = 0;\n"
"	for( int i = 0; i < N_BLOCKER_SAMPLE; ++i ) {\n"
"		vec2 offset = vogelSample( i, N_BLOCKER_SAMPLE, randomNumber );\n"
"		float shadowMapDepth = texture( map, sCoord.xy + searchR*offset ).r;\n"
"		if ( shadowMapDepth < sCoord.z-bias ) {\n"
"			blockerDepth += shadowMapDepth;\n"
"			numBlockers++;\n"
"		}\n"
"	}\n"
"	if (numBlockers < 1 ) return 1.0;\n"
"	return blockerDepth / float(numBlockers);\n"
"}\n"
"float PCSS( vec3 sCoord, vec2 radius, float bias, float near, float far, mat4 proj, sampler2D map ) {\n"
"	float randomNumber = rand( gl_FragCoord.xy )*PI;\n"
"	float zEye = linearDepth( sCoord.z, near, far );\n"
"	vec2 searchR = radius*(zEye - near) / zEye*0.01;\n"
"	float blockerDepth = blockerSearch( sCoord, searchR, bias, map, randomNumber );\n"
"	if( sCoord.z<blockerDepth ) return 1.;\n"
"	blockerDepth = linearDepth( blockerDepth, near, far );\n"
"	vec2 radiusInWorld = radius * (zEye - blockerDepth) / blockerDepth;\n"
"	vec2 filterRadius = project( proj, vec3( radiusInWorld, -near) ).xy*.5;\n"
"	return sampleShadow( sCoord, filterRadius, bias, map, randomNumber );\n"
"}\n"
"float computeShadowing( int i) {\n"
"	if( lights[i].shadowEnabled <1 ) return 1;\n"
"	return PCSS( shadowCoord[i].xyz/shadowCoord[i].w, lights[i].radius, 0.0001,\n"
"				lights[i].zNear, lights[i].zFar, lights[i].proj, lights[i].shadowMap );\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"uniform sampler2D normalTex;\n"
"uniform int   normalTexEnabled=0;\n"
"uniform int   bumpMapped=0;\n"
"\n"
"float difTex( sampler2D tex, vec2 x, vec2 dv) {\n"
"	return (texture(tex,x+dv).r-texture(tex,x-dv).r)*10.;\n"
"}\n"
"mat3 getTBN( vec3 N ) {\n"
"	vec3 Q1 = dFdx(worldPos), Q2 = dFdy(worldPos);\n"
"	vec2 st1 = dFdx(texCoord), st2 = dFdy(texCoord);\n"
"	float D = st1.s*st2.t-st2.s*st1.t;\n"
"	return mat3(normalize(( Q1*st2.t - Q2*st1.t )*D),\n"
"				normalize((-Q1*st2.s + Q2*st1.s )*D), N);\n"
"}\n"
"vec3 computeNormal() {"
"	vec3 N = normalize( normal );\n"
"	N = sign( dot( cross( dFdx(worldPos), dFdy(worldPos) ), N) )*N;\n"
"	if( normalTexEnabled>0 ) {\n"
"		if( bumpMapped>0 )	N = normalize( getTBN(N)*vec3(-difTex(normalTex,texCoord,vec2(0.0001,0)),-difTex(normalTex,texCoord,vec2(0,0.0001)),1) );\n"
"		else				N = normalize( getTBN(N)*(texture(normalTex,texCoord).rgb*2-vec3(1)));\n"
"	}\n"
"	return N;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"vec3 evalSphericalHarmonic( vec3 N, vec3 coeff[9] ) {\n"
"	const float iblRotationTheta = 0.;\n"
"	float c = cos( iblRotationTheta ), s = sin( iblRotationTheta );\n"
"	vec2 rr= mat2(c, -s, s, c)*N.xz;\n"
"	vec3 v = vec3( rr.x, N.y, rr.y );\n"
"	vec3 col=\n"
"		+ coeff[0]\n"
"		+ coeff[1]*v.y\n"
"		+ coeff[2]*v.z\n"
"		+ coeff[3]*v.x\n"
"		+ coeff[4]*v.x*v.y\n"
"		+ coeff[5]*v.y*v.z\n"
"		+ coeff[6]*(v.z*v.z-0.3333328848)\n"
"		+ coeff[7]*v.x*v.z\n"
"		+ coeff[8]*(v.x*v.x-v.y*v.y);\n"
"	return col;\n"
"}\n"
"\n"
"uniform vec3  ambCoeffs[9];\n"
"uniform float ambFactor = .25;\n"
"\n"
"vec3 computeAmbient( vec3 color, vec3 arm, vec3 N ) {\n"
"	return color*mix(1,0.2,arm.b)*evalSphericalHarmonic(N,ambCoeffs).rgb*ambFactor*arm.r/(PI*2);\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"uniform vec4  color = vec4(1);\n"
"uniform float roughness = 0.3;\n"
"uniform float metalness = 0;\n"
"uniform vec3  F0=vec3(0.046);\n"
"uniform sampler2D diffTex;\n"
"uniform sampler2D armTex;\n"
"uniform sampler2D roughTex;\n"
"uniform sampler2D alphaTex;\n"
"uniform sampler2D specTex;\n"
"uniform sampler2D metalTex;\n"
"uniform int   diffTexEnabled=0;\n"
"uniform int   armTexEnabled=0;\n"
"uniform int   roughTexEnabled=0;\n"
"uniform int   alphaTexEnabled=0;\n"
"uniform int   specTexEnabled=0;\n"
"uniform int   metalTexEnabled=0;\n"
"\n"
"vec4 computeMaterial(out vec3 arm, out vec3 f0) {\n"
"	vec4 diffColor = color;\n"
"	f0 = F0;\n"
"	arm = vec3(1,roughness,metalness);\n"
"	if( diffTexEnabled  >0 ) diffColor 		= texture(diffTex, texCoord);\n"
"	if( roughTexEnabled >0 ) arm.g			= texture(roughTex,texCoord).r;\n"
"	if( alphaTexEnabled >0 ) diffColor.a	= texture(alphaTex,texCoord).r;\n"
"	if( specTexEnabled  >0 ) f0				= texture(specTex, texCoord).rgb;\n"
"	if( metalTexEnabled >0 ) arm.b			= texture(metalTex,texCoord).r;\n"
"	if( armTexEnabled   >0 ) arm			= texture(armTex,  texCoord).rgb;\n"
"	return diffColor;\n"
"}\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"\n"
"void main(void) {\n"
"	vec3 N = computeNormal();\n"
"	vec3 V = normalize(cameraPos-worldPos);\n"
"	vec3 f0, arm, c = vec3(0);\n"
"	vec4 color = computeMaterial( arm, f0 );\n"
"\n"
"\n"
"	for( int i=0; i<nLights; i++ ) {\n"
"		float shadowing = computeShadowing( i );\n"
"		c += computePointLighting(N, V, color.rgb, arm, f0, i ) * shadowing;\n"
"	}\n"
"\n"
"\n"
"	vec3 am = computeAmbient( color.rgb, arm, N );\n"
"\n"
"\n"
"	out_Color = vec4( computeTonemap( c+am ), color.a);\n"
"}\n";
*/
} // namespace JR

#endif /* _JR_Renderer_h */
