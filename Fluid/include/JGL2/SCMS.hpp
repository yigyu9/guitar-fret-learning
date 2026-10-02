//
//  SCMS.h
//  JGL2
//
//  Created by Hyun Joon Shin on 2022/07/25.
//

#ifndef SCMS_h
#define SCMS_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <functional>
#include <fstream>
#include <sstream>
#include <filesystem>
#include <vector>
#include <iostream>
#ifndef STBI_VERSION
#include <stb_image.h>
#endif
#include <cassert>

#ifdef SCMS_USE_GLM
#include <glm/glm.hpp>
using xy_t = glm::vec2;
using color_t = glm::vec3;
using colorMat_t = glm::mat3;
using glm::sign;
#else
#include <jm/jm.hpp>
using xy_t = jm::vec2;
using color_t = jm::vec3;
using colorMat_t = jm::mat3;
using colorh_t = jm::hvec3;
using jm::sign;
#endif

namespace SCMS {

const xy_t WHTPT_D50			= {0.34567f, 0.35850f};
const xy_t WHTPT_D55			= {0.33242f, 0.34743f};
const xy_t WHTPT_D60			= {0.32168f, 0.33767f};
const xy_t WHTPT_DCI			= {0.31400f, 0.35100f};
const xy_t WHTPT_D65			= {0.31271f, 0.32902f};
const xy_t WHTPT_A				= {0.44757f, 0.40745f};
const xy_t WHTPT_B				= {0.34842f, 0.35161f};
const xy_t WHTPT_C				= {0.31006f, 0.31616f};
const xy_t WHTPT_D75			= {0.29902f, 0.31485f};
const xy_t WHTPT_E				= {0.33333f, 0.33333f};
const xy_t WHTPT_F1				= {0.31310f, 0.33727f};
const xy_t WHTPT_F2				= {0.37208f, 0.37529f};
const xy_t WHTPT_F3				= {0.40910f, 0.39430f};
const xy_t WHTPT_F4				= {0.44018f, 0.40329f};
const xy_t WHTPT_F5				= {0.31379f, 0.34531f};
const xy_t WHTPT_F6				= {0.37790f, 0.38835f};
const xy_t WHTPT_F7				= {0.31292f, 0.32933f};
const xy_t WHTPT_F8				= {0.34588f, 0.35875f};
const xy_t WHTPT_F9				= {0.37417f, 0.37281f};
const xy_t WHTPT_F10			= {0.34609f, 0.35986f};
const xy_t WHTPT_F11			= {0.38052f, 0.37713f};
const xy_t WHTPT_F12			= {0.43695f, 0.40441f};

const xy_t PRIME_R_sRGB         ={ 0.6400f,0.3300f};
const xy_t PRIME_G_sRGB         ={ 0.3000f,0.6000f};
const xy_t PRIME_B_sRGB         ={ 0.1500f,0.0600f};

const xy_t PRIME_R_DisplayP3    ={ 0.680f, 0.320f };
const xy_t PRIME_G_DisplayP3    ={ 0.265f, 0.690f };
const xy_t PRIME_B_DisplayP3    ={ 0.150f, 0.060f };

const xy_t PRIME_R_AdobeRGB     ={0.6400f,0.3300f};
const xy_t PRIME_G_AdobeRGB     ={0.2100f,0.7100f};
const xy_t PRIME_B_AdobeRGB     ={0.1500f,0.0600f};

const xy_t PRIME_R_CIERGB       = { 0.735f, 0.265f };
const xy_t PRIME_G_CIERGB       = { 0.274f, 0.717f };
const xy_t PRIME_B_CIERGB       = { 0.167f, 0.009f };
const xy_t PRIME_R_P3_D65       = { 0.680f, 0.320f };
const xy_t PRIME_G_P3_D65       = { 0.265f, 0.690f };
const xy_t PRIME_B_P3_D65       = { 0.150f, 0.060f };
const xy_t PRIME_R_P3_DCI       = { 0.680f, 0.320f };
const xy_t PRIME_G_P3_DCI       = { 0.265f, 0.690f };
const xy_t PRIME_B_P3_DCI       = { 0.150f, 0.060f };
const xy_t PRIME_R_P3_D60       = { 0.680f, 0.320f };
const xy_t PRIME_G_P3_D60       = { 0.265f, 0.690f };
const xy_t PRIME_B_P3_D60       = { 0.150f, 0.060f };
const xy_t PRIME_R_BestRGB      = { 0.7347f, 0.2653f };
const xy_t PRIME_G_BestRGB      = { 0.2150f, 0.7750f };
const xy_t PRIME_B_BestRGB      = { 0.1300f, 0.0350f };
const xy_t PRIME_R_BetaRGB      = { 0.6888f, 0.3112f };
const xy_t PRIME_G_BetaRGB      = { 0.1986f, 0.7551f };
const xy_t PRIME_B_BetaRGB      = { 0.1265f, 0.0352f };
const xy_t PRIME_R_DonRGB4      = { 0.6960f, 0.3000f };
const xy_t PRIME_G_DonRGB4      = { 0.2150f, 0.7650f };
const xy_t PRIME_B_DonRGB4      = { 0.1300f, 0.0350f };
const xy_t PRIME_R_PAL_RGB      = { 0.6400f, 0.3300f };
const xy_t PRIME_G_PAL_RGB      = { 0.2900f, 0.6000f };
const xy_t PRIME_B_PAL_RGB      = { 0.1500f, 0.0600f };
const xy_t PRIME_R_AppleRGB     = { 0.6250f, 0.3400f };
const xy_t PRIME_G_AppleRGB     = { 0.2800f, 0.5950f };
const xy_t PRIME_B_AppleRGB     = { 0.1550f, 0.0700f };
const xy_t PRIME_R_BruceRGB     = { 0.6400f, 0.3300f };
const xy_t PRIME_G_BruceRGB     = { 0.2800f, 0.6500f };
const xy_t PRIME_B_BruceRGB     = { 0.1500f, 0.0600f };
const xy_t PRIME_R_NTSC_RGB     = { 0.6700f, 0.3300f };
const xy_t PRIME_G_NTSC_RGB     = { 0.2100f, 0.7100f };
const xy_t PRIME_B_NTSC_RGB     = { 0.1400f, 0.0800f };
const xy_t PRIME_R_ProPhotoRGB  = { 0.7347f, 0.2653f };
const xy_t PRIME_G_ProPhotoRGB  = { 0.1596f, 0.8404f };
const xy_t PRIME_B_ProPhotoRGB  = { 0.0366f, 0.0001f };
const xy_t PRIME_R_SMPTE_C_RGB  = { 0.6300f, 0.3400f };
const xy_t PRIME_G_SMPTE_C_RGB  = { 0.3100f, 0.5950f };
const xy_t PRIME_B_SMPTE_C_RGB  = { 0.1550f, 0.0700f };
const xy_t PRIME_R_WideGamutRGB = { 0.7347f, 0.2653f };
const xy_t PRIME_G_WideGamutRGB = { 0.1152f, 0.8264f };
const xy_t PRIME_B_WideGamutRGB = { 0.1566f, 0.0177f };
const xy_t PRIME_R_ColorMatchRGB= { 0.6300f, 0.3400f };
const xy_t PRIME_G_ColorMatchRGB= { 0.2950f, 0.6050f };
const xy_t PRIME_B_ColorMatchRGB= { 0.1500f, 0.0750f };

struct ColorProfile_xy {
	xy_t whtPt, r, g, b;
	color_t gamma;
};

struct ColorProfile_XYZ {
	color_t whtPt, r, g, b;
	color_t gamma;
	color_t blkPt;
};

const ColorProfile_xy PROF_sRGB				= { WHTPT_D65, PRIME_R_sRGB,		PRIME_G_sRGB,		PRIME_B_sRGB,		color_t(2.4f) };
const ColorProfile_xy PROF_AdobeRGB			= { WHTPT_D50, PRIME_R_AdobeRGB,	PRIME_G_AdobeRGB,	PRIME_B_AdobeRGB,	color_t(2.2f) };
const ColorProfile_xy PROF_DisplayP3		= { WHTPT_D65, PRIME_R_DisplayP3,	PRIME_G_DisplayP3,	PRIME_B_DisplayP3,	color_t(2.4f) };

const ColorProfile_xy PROF_AppleRGB			= { WHTPT_D65, PRIME_R_AppleRGB		, PRIME_G_AppleRGB		, PRIME_B_AppleRGB		,	color_t(1.8f) };
const ColorProfile_xy PROF_BestRGB			= { WHTPT_D50, PRIME_R_BestRGB		, PRIME_G_BestRGB		, PRIME_B_BestRGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_BetaRGB			= { WHTPT_D50, PRIME_R_BetaRGB		, PRIME_G_BetaRGB		, PRIME_B_BetaRGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_BruceRGB			= { WHTPT_D65, PRIME_R_BruceRGB		, PRIME_G_BruceRGB		, PRIME_B_BruceRGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_CIERGB			= { WHTPT_E,   PRIME_R_CIERGB		, PRIME_G_CIERGB		, PRIME_B_CIERGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_ColorMatchRGB	= { WHTPT_D50, PRIME_R_ColorMatchRGB, PRIME_G_ColorMatchRGB	, PRIME_B_ColorMatchRGB	,	color_t(1.8f) };
const ColorProfile_xy PROF_DonRGB4			= { WHTPT_D50, PRIME_R_DonRGB4		, PRIME_G_DonRGB4		, PRIME_B_DonRGB4		,	color_t(2.2f) };
const ColorProfile_xy PROF_NTSC_RGB			= { WHTPT_C,   PRIME_R_NTSC_RGB		, PRIME_G_NTSC_RGB		, PRIME_B_NTSC_RGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_PAL_RGB			= { WHTPT_D65, PRIME_R_PAL_RGB		, PRIME_G_PAL_RGB		, PRIME_B_PAL_RGB		,	color_t(2.2f) };
const ColorProfile_xy PROF_ProPhotoRGB		= { WHTPT_D50, PRIME_R_ProPhotoRGB	, PRIME_G_ProPhotoRGB	, PRIME_B_ProPhotoRGB	,	color_t(1.8f) };
const ColorProfile_xy PROF_SMPTE_C_RGB		= { WHTPT_D65, PRIME_R_SMPTE_C_RGB	, PRIME_G_SMPTE_C_RGB	, PRIME_B_SMPTE_C_RGB	,	color_t(2.2f) };
const ColorProfile_xy PROF_WideGamutRGB		= { WHTPT_D50, PRIME_R_WideGamutRGB	, PRIME_G_WideGamutRGB	, PRIME_B_WideGamutRGB	,	color_t(2.2f) };
const ColorProfile_xy PROF_P3_D65			= { WHTPT_D65, PRIME_R_P3_D65		, PRIME_G_P3_D65		, PRIME_B_P3_D65		,	color_t(2.6f) };
const ColorProfile_xy PROF_P3_DCI			= { WHTPT_DCI, PRIME_R_P3_DCI		, PRIME_G_P3_DCI		, PRIME_B_P3_DCI		,	color_t(2.6f) };
const ColorProfile_xy PROF_P3_D60			= { WHTPT_D60, PRIME_R_P3_D60		, PRIME_G_P3_D60		, PRIME_B_P3_D60		,	color_t(2.6f) };

inline color_t xyz(float x, float y) { return color_t(x,y,1-x-y); }
inline color_t xyz(const xy_t& c) { return color_t(c.x,c.y,1-c.x-c.y); }
inline colorMat_t MMM( const color_t& R, const color_t& G, const color_t& B) {
	return colorMat_t ( R.x/R.y,1.f,R.z/R.y, G.x/G.y,1.f,G.z/G.y, B.x/B.y,1.f,B.z/B.y);
}
inline color_t xyYToXYZ( float x, float y, float Y) { return color_t(x/y,1,(1-x-y)/y)*Y; }
inline color_t xyYToXYZ( const color_t& v) { return xyYToXYZ(v.x,v.y,v.z); }
inline color_t XYZToxyY( float X, float Y, float Z) { return color_t(X/(X+Y+Z),Y/(X+Y+Z),Y); }
inline color_t XYZToxyY( const color_t& v ) { return XYZToxyY(v.x,v.y,v.z); }

inline colorMat_t toXYZ( const xy_t& w, const xy_t& r, const xy_t& g, const xy_t& b ) {
// First compute Y for all primaries
	color_t xyz_r = xyz(r);
	color_t xyz_g = xyz(g);
	color_t xyz_b = xyz(b);
	color_t XYZ_w = xyYToXYZ(w.x,w.y,1);
	color_t Y = inverse(MMM(xyz_r,xyz_g,xyz_b))*XYZ_w;
// Now we have Y. Strait forward.
	colorMat_t c = { xyYToXYZ(r.x,r.y,Y.r), xyYToXYZ(g.x,g.y,Y.g), xyYToXYZ(b.x,b.y,Y.b) };
	return c;
}

enum class CHROMATIC_ADAPTATION_METHOD {
	XYZ_SCALING,
	BRADFORD,
	VON_KRIES,
};

inline colorMat_t getChromaticAdaptationMat( const color_t& srcWhiteXYZ, const color_t& dstWhiteXYZ,
											  CHROMATIC_ADAPTATION_METHOD method = CHROMATIC_ADAPTATION_METHOD::BRADFORD) {

	const colorMat_t ChromaticAdaptationMat_XYZ_Scaling_f = colorMat_t( color_t(1,0,0), color_t(0,1,0), color_t(0,0,1));
	const colorMat_t ChromaticAdaptationMat_XYZ_Scaling_i = colorMat_t( color_t(1,0,0), color_t(0,1,0), color_t(0,0,1));

	const colorMat_t ChromaticAdaptationMat_Bradford_f = colorMat_t( color_t(0.8951f,-0.7502f, 0.0389f), color_t( 0.2664f, 1.7135f,-0.0685f), color_t(-0.1614f, 0.0367f, 1.0296f));
	const colorMat_t ChromaticAdaptationMat_Bradford_i = colorMat_t( color_t(0.9870f, 0.4323f,-0.0085f), color_t(-0.1471f, 0.5184f, 0.0400f), color_t( 0.1600f, 0.0493f, 0.9695f));

	const colorMat_t ChromaticAdaptationMat_VonKries_f = colorMat_t( color_t(0.4002f,-0.2263f, 0.0000f), color_t( 0.7076f, 1.1653f, 0.0000f), color_t(-0.0808f, 0.0457f, 0.9182f));
	const colorMat_t ChromaticAdaptationMat_VonKries_i = colorMat_t( color_t(1.8599f, 0.3612f, 0.0000f), color_t(-1.1294f, 0.6388f, 0.0000f), color_t( 0.2199f, 0.0000f, 1.0891f));

	colorMat_t  ret;
	ret[0][1]=ret[0][2]=ret[1][0]=ret[1][2]=ret[2][0]=ret[2][1]=0;
	colorMat_t ma, mai;
	switch( method ) {
		case CHROMATIC_ADAPTATION_METHOD::BRADFORD:
			ma  = ChromaticAdaptationMat_Bradford_f;
			mai = ChromaticAdaptationMat_Bradford_i;
			break;
		case CHROMATIC_ADAPTATION_METHOD::VON_KRIES:
			ma  = ChromaticAdaptationMat_VonKries_f;
			mai = ChromaticAdaptationMat_VonKries_i;
			break;
		case CHROMATIC_ADAPTATION_METHOD::XYZ_SCALING:
			ma  = ChromaticAdaptationMat_XYZ_Scaling_f;
			mai = ChromaticAdaptationMat_XYZ_Scaling_i;
			break;
	}
	color_t rgb_s = ma*srcWhiteXYZ;
	color_t rgb_d = ma*dstWhiteXYZ;
	ret[0][0] = rgb_d.r/rgb_s.r;
	ret[1][1] = rgb_d.g/rgb_s.g;
	ret[2][2] = rgb_d.b/rgb_s.b;
	return mai*ret*ma;
}




inline colorMat_t toXYZ_D65( const ColorProfile_xy& prof ) {	return toXYZ( prof.whtPt, prof.r, prof.g, prof.b ); }

inline colorMat_t fromXYZ_D65( const ColorProfile_xy& prof ) { return inverse(toXYZ_D65( prof )); }

inline colorMat_t toXYZ_D65( const ColorProfile_XYZ& prof ) {
	return getChromaticAdaptationMat(prof.whtPt, xyYToXYZ({WHTPT_D65,1}))*colorMat_t(prof.r,prof.g,prof.b);
}
inline colorMat_t fromXYZ_D65( const ColorProfile_XYZ& prof ) {
	return inverse(toXYZ_D65( prof ))*getChromaticAdaptationMat(xyYToXYZ({WHTPT_D65,1}),prof.whtPt);
}

inline float invTonemap(float u, float gamma) {
	if( abs(gamma-2.4f)<0.0001f ) {
		float u_ = abs(u);
		return u_>0.04045f?(sign(u)*powf((u_+0.055f)/1.055f,2.4f)):(u/12.92f);
	}
	else
		return sign(u)*pow(abs(u),gamma);
}
inline float tonemap(float u, float gamma) {
	if( abs(gamma-2.4f)<0.0001f ) {
		float u_ = abs(u);
		return  u_>0.0031308f?( sign(u)*1.055f*powf( u_,0.41667f)-0.055f):(12.92f*u);
	}
	else
		return sign(u)*pow(abs(u),1/gamma);
}

inline color_t tonemap(const color_t& rgb, float gamma) {
	return color_t(tonemap(rgb.r, gamma),tonemap(rgb.g, gamma),tonemap(rgb.b, gamma));
}
inline color_t tonemap(const color_t& rgb, const color_t& gamma) {
	return color_t(tonemap(rgb.r, gamma.r),tonemap(rgb.g, gamma.g),tonemap(rgb.b, gamma.b));
}
inline color_t invTonemap(const color_t& rgb, float gamma) {
	return color_t(invTonemap(rgb.r, gamma),invTonemap(rgb.g, gamma),invTonemap(rgb.b, gamma));
}
inline color_t invTonemap(const color_t& rgb, const color_t& gamma) {
	return color_t(invTonemap(rgb.r, gamma.r),invTonemap(rgb.g, gamma.g),invTonemap(rgb.b, gamma.b));
}

const colorMat_t typicalBayerMat = colorMat_t(1/40.f,0,0, 0,1/98.f,0, 0,0,1/50.f )*98.f;

const colorMat_t imx183BayerMat = colorMat_t(6.519,4.195,0.561,6.477,10.703,3.541,2.698,2.139,12.385)*.05f;

}


#include <fstream>
#include <string>
#include <stdio.h>

namespace SCMS {

struct FOURC {
	char c[4];
	char operator[](int i)const{ return c[i]; }
	char& operator[](int i){ return c[i]; }
	bool compare( const char* d ) { return c[0]==d[0] && c[1]==d[1] && c[2]==d[2] && c[3]==d[3]; }
};

struct EIGHTC {
	char c[8];
	char operator[](int i)const{ return c[i]; }
	char& operator[](int i){ return c[i]; }
};

inline void print_( const char* fm, const FOURC d ) {
	std::string fmt = fm;
	size_t pos = fmt.find("%F");
	if( pos>fmt.size() ) printf("%s", fm);
	else {
		fmt.replace( pos, 2, "%c%c%c%c" );
		printf(fmt.c_str(), d[0], d[1], d[2], d[3]);
	}
}

inline void print_( const char* fm, const EIGHTC d ) {
	std::string fmt = fm;
	size_t pos = fmt.find("%E");
	if( pos>fmt.size() ) printf("%s", fm);
	else {
		fmt.replace( pos, 2, "%c%c%c%c%c%c%c%c" );
		printf(fmt.c_str(), d[0], d[1], d[2], d[3], d[4], d[5], d[6], d[7]);
	}
}

inline void print_( const char* fm, const color_t& c ) {
	std::string fmt = fm;
	size_t pos = fmt.find("%C");
	if( pos>fmt.size() ) printf("%s", fm);
	else {
		fmt.replace( pos, 2, "%f %f %f" );
		printf(fmt.c_str(), c.r, c.g, c.b);
	}
}

inline uint32_t getUint( uint8_t*& data ) {
	uint32_t val;
	uint8_t* pt = (uint8_t*)(&val);
	pt[0]=data[3]; pt[1]=data[2]; pt[2]=data[1]; pt[3]=data[0];
	data+=4;
	return val;
}

inline uint16_t getUint16( uint8_t*& data ) {
	uint16_t val;
	uint8_t* pt = (uint8_t*)(&val);
	pt[0]=data[1]; pt[1]=data[0];
	data+=2;
	return val;
}

inline float getFloat( uint8_t*& data ) {
	int16_t upper;
	uint16_t lower;
	float val;
	uint8_t* pt = (uint8_t*)(&upper);
	pt[0]=data[1]; pt[1]=data[0];
	pt = (uint8_t*)(&lower);
	pt[0]=data[3]; pt[1]=data[2];
	val = float(upper)+float(lower)/65536.f;
	data+=4;
	return val;
}

inline float getFloat16( uint8_t*& data ) {
	int8_t upper;
	uint8_t lower;
	float val;
	uint8_t* pt = (uint8_t*)(&upper);
	pt[0]=data[0];
	pt = (uint8_t*)(&lower);
	pt[0]=data[1];
	val = float(upper)+float(lower)/256.f;
	data+=2;
	return val;
}

inline float getUfloat( uint8_t*& data ) {
	uint16_t upper, lower;
	float val;
	uint8_t* pt = (uint8_t*)(&upper);
	pt[0]=data[1]; pt[1]=data[0];
	pt = (uint8_t*)(&lower);
	pt[0]=data[3]; pt[1]=data[2];
	val = float(upper)+float(lower)/65536.f;
	data+=4;
	return val;
}

inline float getUfloat16( uint8_t*& data ) {
	uint8_t upper, lower;
	float val;
	uint8_t* pt = (uint8_t*)(&upper);
	pt[0]=data[0];
	pt = (uint8_t*)(&lower);
	pt[0]=data[1];
	val = float(upper)+float(lower)/256.f;
	data+=2;
	return val;
}

inline color_t getXYZ( uint8_t*& data ) {
	color_t c;
	c.r = getFloat( data );
	c.g = getFloat( data );
	c.b = getFloat( data );
	return c;
}

inline FOURC getFourC( uint8_t*& data ) {
	FOURC val;
	val[0]=data[0]; val[1]=data[1]; val[2]=data[2]; val[3]=data[3];
	data+=4;
	return val;
}

inline EIGHTC getEightC( uint8_t*& data ) {
	EIGHTC val;
	val[0]=data[0];	val[1]=data[1];	val[2]=data[2];	val[3]=data[3];
	val[4]=data[4];	val[5]=data[5];	val[6]=data[6];	val[7]=data[7];
	data+=8;
	return val;
}

inline float recognizeTonemap( const std::vector<uint16_t>& gammaTable ) {
	int count = int( gammaTable.size() );
	// Check if it is sRGB
	{
		int offset = int( 0.3*(count-1)+0.999999999 );
		int n = 0;
		float sum1=0, sum2=0, sum3=0, sum4=0;
		for( int i = offset; i<count; i+=4 ) {
			n++;
			float x = log( 0.948f*i/(count-1.f)+0.052f );
			float y = log( gammaTable[i]/65535.f );
			sum1+= x*y;
			sum2+=x;
			sum3+=y;
			sum4+=x*x;
		}
		float gamma = (n*sum1-sum2*sum3)/(n*sum4-sum2*sum2);
		if( abs( gamma-2.4f)<0.01f ) return 2.4f;
	}
	// Check if it is Power curve of linear..
	{
		int n = 0;
		float sum1=0, sum2=0, sum3=0, sum4=0;
		for( int i = 0; i<count; i+=8 ) {
			n++;
			float x = log( i/(count-1.f) );
			float y = log( gammaTable[i]/65535.f );
			sum1+= x*y;
			sum2+=x;
			sum3+=y;
			sum4+=x*x;
		}
		float gamma = (n*sum1-sum2*sum3)/(n*sum4-sum2*sum2);
		if( abs( gamma-2.2f)<0.01f ) return 2.2f;
		if( abs( gamma-2.6f)<0.01f ) return 2.6f;
		if( abs( gamma-1.8f)<0.01f ) return 1.8f;
		if( abs( gamma-1.0f)<0.01f ) return 1.0f;
		// Unknown curve.. here we simply approximate the curve as Power function
		return gamma;
	}
}

struct TIME {
	uint32_t	year, month, day, hour, minute, second;
};
struct ICC_Header {
	uint32_t	profileSize         = 0;
	FOURC		CMMType             ={0,0,0,0};
	uint32_t	version             = 0;
	FOURC		profileDeviceClass  = {0,0,0,0};
	FOURC		colorSpace          = {0,0,0,0};
	FOURC		connectionSpace     = {0,0,0,0};
	TIME		creationTime        = TIME();
	FOURC		signature           = {0,0,0,0};
	FOURC		primPlatformTarget  = {0,0,0,0};
	uint32_t	flags               = 0;
	FOURC		manufacturer        = {0,0,0,0};
	FOURC		deviceModel         = {0,0,0,0};
	EIGHTC		deviceAttributes    = {0,0,0,0,0,0,0,0};
	uint32_t	renderIntent        = 0;
	color_t		illuminantXYZ       = color_t(0);	// Connection Space
	FOURC		creator             = {0,0,0,0};
	
	
	void read( uint8_t*& data) {
		profileSize			= getUint( data );
		CMMType				= getFourC( data );
		version				= getUint( data );
		profileDeviceClass	= getFourC( data );
		colorSpace			= getFourC( data );
		connectionSpace		= getFourC( data );

		FOURC creationData1 = getFourC( data );
		FOURC creationData2 = getFourC( data );
		FOURC creationData3 = getFourC( data );

		creationTime.year   = (uint32_t(creationData1[0]))*256+(uint32_t(creationData1[1]));
		creationTime.month  = (uint32_t(creationData1[2]))*256+(uint32_t(creationData1[3]));
		creationTime.day    = (uint32_t(creationData2[0]))*256+(uint32_t(creationData2[1]));
		creationTime.hour   = (uint32_t(creationData2[2]))*256+(uint32_t(creationData2[3]));
		creationTime.minute = (uint32_t(creationData3[0]))*256+(uint32_t(creationData3[1]));
		creationTime.second = (uint32_t(creationData3[2]))*256+(uint32_t(creationData3[3]));

		signature			= getFourC( data );
		primPlatformTarget	= getFourC( data );
		flags				= getUint( data );

		
		manufacturer		= getFourC( data );
		deviceModel			= getFourC( data );
		deviceAttributes	= getEightC( data );
		renderIntent		= getUint( data );
		illuminantXYZ		= getXYZ( data );
		creator				= getFourC( data );

	}
	void print() const {
		printf("Profile Size	: %X\n", profileSize );
		print_("CMM Type		: %F\n", CMMType);
		printf("Profile Version	: %d\n", version );
		print_("DeviceClass		: %F\n", profileDeviceClass);
		print_("Color Space Sig	: %F\n", colorSpace);
		print_("Prof Conn Space	: %F\n", connectionSpace);
		printf("Date			: %d/%d/%d %d:%d:%d\n", creationTime.year, creationTime.month, creationTime.day, creationTime.hour, creationTime.minute, creationTime.second );
		print_("Profile file Sig: %F\n", signature);
		print_("Platform Target	: %F\n", primPlatformTarget);
		printf("Profile Flags	: %d\n", flags);

		print_("Device Manuf	: %F\n", manufacturer);
		print_("Device Model	: %F\n", deviceModel);
		print_("DeviceAttributes: %E\n", deviceAttributes);
		printf("Rendering Intent: %d\n", renderIntent);
		print_("Illuminant XYZ	: %C\n", illuminantXYZ);
		print_("Illuminant xyY	: %C\n", XYZToxyY(illuminantXYZ));
		print_("Creator			: %F\n", creator);

	}
};
#if 0

#ifdef _MSC_VER
#ifdef _DEBUG
#pragma comment (lib,"zlibstaticd")
#else
#pragma comment (lib,"zlibstatic")
#endif
#endif

#include <zlib.h>
#define CHUNK 2048
template<typename T> std::vector<uint8_t> zinf(T& source,
	std::function<size_t(T&,unsigned char[],size_t)> read,
	std::function<bool(const T&)>error ) {
	int ret;
	unsigned have = 0;
	z_stream strm;
	unsigned char in[CHUNK], out[CHUNK];
	std::vector<uint8_t> data;
	strm.zalloc = Z_NULL;
	strm.zfree = Z_NULL;
	strm.opaque = Z_NULL;
	strm.avail_in = 0;
	strm.next_in = Z_NULL;
	ret = inflateInit(&strm);
	if (ret != Z_OK)
		return data;
	do {
		strm.avail_in = (int)read(source, in, CHUNK);
		if (error(source)) {
			(void)inflateEnd(&strm);
			return data;
		}
		if (strm.avail_in == 0)
			break;
		strm.next_in = in;
		do {
			strm.avail_out = CHUNK;
			strm.next_out = out;
			ret = inflate(&strm, Z_NO_FLUSH);
			assert(ret != Z_STREAM_ERROR);
			switch (ret) {
				case Z_NEED_DICT:
					ret = Z_DATA_ERROR;
					[[fallthrough]];
				case Z_DATA_ERROR:
					[[fallthrough]];
				case Z_MEM_ERROR:
					(void)inflateEnd(&strm);
					return data;
			}
			have = CHUNK - strm.avail_out;
			int last = (int)data.size();
			data.resize( last+have );
			for( unsigned int i=0; i<have; i++ ) data[i+last] = out[i];
		} while (strm.avail_out == 0);
	} while (ret != Z_STREAM_END);
	(void)inflateEnd(&strm);
	return data;
}

template<typename T> std::vector<uint8_t> zinf(T& f) {
	return zinf<std::istream>(f,
		[](auto& f, unsigned char* buf, size_t sz) { auto c = f.tellg(); f.read( (char*)buf, sz ); return (size_t)(f.tellg()-c); },
		[](const auto& f){ return (f.rdstate() & std::istream::failbit ) != 0; });
}
template<> inline std::vector<uint8_t> zinf<FILE*>(FILE*& f) {
	return zinf<FILE*>(f, [](auto& f, unsigned char* buf, size_t sz) { return (size_t)fread( buf, 1, sz, f ); },
					   [](const auto& f){ return ferror(f); });
}

#else
inline std::vector<uint8_t> zinf(std::istream& f,int sz=1024) {
	std::vector<char> ibuffer(sz);
	std::vector<char> obuffer(sz*4);
	int isz = sz;
	for( int i=0; i<sz; i++ ) {
		if( f.eof() ) {
			isz = i;
			break;
		}
		ibuffer[i] = f.get();
	}
	ibuffer.resize(isz);
	int osz = stbi_zlib_decode_buffer(obuffer.data(), sz*4, ibuffer.data(), (int)ibuffer.size());
	if( osz<=0 ) return std::vector<uint8_t>();
	std::vector<uint8_t> ret(osz);
	for( int i=0; i<osz; i++ ) ret[i] = obuffer[i];
	return ret;
}
inline std::vector<uint8_t> zinf(FILE*& f,int sz=1024) {
	char* ibuffer = new char[sz];
	char* obuffer = new char[sz*4];
	int isz = sz;
	for( int i=0; i<sz; i++ ) {
		if( feof(f) ) {
			isz = i;
			break;
		}
		ibuffer[i] = fgetc(f);
	}
	int osz = stbi_zlib_decode_buffer(obuffer, sz*4, ibuffer, isz);
	if( osz<=0 ) return std::vector<uint8_t>();
	std::vector<uint8_t> ret(osz);
	for( int i=0; i<osz; i++ ) ret[i] = obuffer[i];
	delete [] ibuffer;
	delete [] obuffer;
	return ret;
}
#endif

template<typename T> bool feedToICC_PNG( T& ifs, std::vector<uint8_t> code, std::function<void(T&,char*,size_t)> read,
	std::function<uint8_t(T&)> get, std::function<bool(const T&)> eof ) {
	int off = 0, state = 0;
	std::vector<uint8_t> buf(code.size(),0);
	int cursor = 0;
	while( !eof(ifs) ) {
		buf[cursor] = get(ifs);
		off++;
		bool found = true;
		for( int i=0; i<code.size(); i++) if( code[i]!=buf[i] ) { found=false; break; }
		if( found ) {
			state = 1;
			break;
		}
		cursor++;
		if( cursor>=code.size() ) {
			for( int i=0; i<code.size()-1; i++ ) buf[i]=buf[i+1];
			cursor = (int)code.size()-1;
		}
	}
	if( state==1 && !eof(ifs) ) {
		uint8_t name[80];
		for( int i=0; i<80; i++ ) {
			name[i] = get(ifs);
			if( name[i] == 0 ) break;
		}
		printf("PNG ICC name: %s\n", name);
		uint8_t compMethod = get(ifs);
		printf("Compression method: %d\n", compMethod);
		
		return false;
	}
	return true;
}

inline bool feedToICC_PNG(std::istream& ifs) {
	return feedToICC_PNG<std::istream>( ifs, {105,67,67,80},
		[](auto& ifs,char* buf,size_t sz) { ifs.read(buf,sz); },
		[](auto& ifs){ char tmp; ifs.read(&tmp,1); return tmp; },
		[](const auto& ifs){ return ifs.eof(); });
}
inline bool feedToICC_PNG( FILE*& f ) {
	return feedToICC_PNG<FILE*>( f,{105,67,67,80},
			[](auto& f, char* buf, size_t sz) { fread( buf, 1, sz, f ); },
			[](auto& f){ return fgetc(f); },
			[](const auto& f){ return feof(f); } );
}
inline bool feedToICC_PNG(uint8_t*& data, long totalSz) {
	std::istringstream iss( (const char*)data, std::ios_base::in );
	return feedToICC_PNG(iss);
}

template<typename T> std::vector<uint8_t> getICC_PNG( T& f ) {
	if( feedToICC_PNG( f ) ) return {};
	printf("ICC profile found\n");
	auto ret = zinf(f);
	return ret;
}
inline std::vector<uint8_t> getICC_PNG( const uint8_t* data, long totalSz ) {
	std::istringstream iss( (const char*)data, std::ios_base::in );
	return getICC_PNG(iss);
}

template<> inline std::vector<uint8_t> getICC_PNG( const std::filesystem::path& f ) {
	std::ifstream ifs( f, std::ios_base::binary );
	if( !ifs.is_open()) return {};
	auto ret = getICC_PNG( ifs );
	ifs.close();
	return ret;
}

template<> inline std::vector<uint8_t> getICC_PNG( uint8_t*& data ) {
	std::stringstream iss( (char*)data, std::ios_base::in );
	return getICC_PNG(iss);
}

template<typename T>
uint8_t* getICC_JPEG( T& ifs, size_t& sz, std::function<void(T&,char*,size_t)> read,
	std::function<uint8_t(T&)> get, std::function<bool(const T&)> eof) {
	sz = 0;
	int state = 0;
	char temp[100];
	while( !eof(ifs) ) {
		uint8_t c = get(ifs);
		if( c==0xFF )	state = 1;
		else if( state==1 && c==0xE2 )	break;
		else state = 0;
	}
	if( state!=1 || eof(ifs) ) return nullptr;

	uint8_t C1 = get(ifs), C2 = get(ifs);
	uint16_t iccSize = C1<<8|C2;

	read( ifs, temp, 14 );
	uint8_t* iccData = new uint8_t[iccSize+5];
	read( ifs, (char*)iccData, iccSize );
	sz = iccSize;
	return iccData;
}

inline uint8_t* getICC_JPEG( std::istream& ifs, size_t& sz ) {
	return getICC_JPEG<std::istream>( ifs, sz,
		[](auto& ifs, char* buf, size_t sz) { ifs.read( buf, sz ); },
		[](auto& ifs){ char tmp; ifs.read(&tmp,1); return tmp; },
		[](const auto& ifs){ return ifs.eof(); } );
}

inline uint8_t* getICC_JPEG( FILE* f, size_t& sz ) {
	return getICC_JPEG<FILE*>( f, sz,
		[](auto& f, char* buf, size_t sz) { fread( buf, 1, sz, f ); },
		[](auto& f){ return fgetc(f); },
		[](const auto& f){ return feof(f); } );
}

inline uint8_t* getICC_JPEG( const uint8_t* data, long totalSize, size_t& sz ) {
	std::istringstream iss( (const char*)data, std::ios_base::in );
	return getICC_JPEG(iss,sz);
}

inline uint8_t* getICC_JPEG( const std::filesystem::path& fn, size_t& sz ) {
	std::ifstream ifs( fn, std::ios_base::binary );
	if( !ifs.is_open()) return nullptr;
	uint8_t* ret = getICC_JPEG( ifs, sz );
	ifs.close();
	return ret;
}

struct ColorProfile_ICC : ColorProfile_XYZ {
	ColorProfile_ICC():ColorProfile_XYZ(){
		gamma = color_t(2.4f);
		colorMat_t m = toXYZ(WHTPT_D65,PRIME_R_sRGB,PRIME_G_sRGB,PRIME_B_sRGB);
		r = m[0];
		g = m[1];
		b = m[2];
		whtPt = xyYToXYZ(color_t(WHTPT_D65,1));
	}
	ColorProfile_ICC( const std::filesystem::path& f, bool verbose = false ) {
		gamma = color_t(2.4f);
		colorMat_t m = toXYZ(WHTPT_D65,PRIME_R_sRGB,PRIME_G_sRGB,PRIME_B_sRGB);
		r = m[0];
		g = m[1];
		b = m[2];
		whtPt = xyYToXYZ(color_t(WHTPT_D65,1));

		std::string ext = f.extension().string();
		for (auto & c: ext) c = std::tolower(c);
		if( ext.compare(".png")==0 ) initWithPNG( f, verbose );
		else if( ext.compare(".jpg")==0 ) initWithJPEG( f, verbose );
		else if( ext.compare(".jpeg")==0 ) initWithJPEG( f, verbose );
		else if( ext.compare(".icc")==0 ) initWithICC( f, verbose );
	}
	static float parseGamma( uint8_t*& data, std::string name, bool verbose ) {
		float gamma = 2.4f;
		uint32_t count = getUint( data );
		if( count==0 ) {
			gamma = 1.;
			if( verbose ) printf("  %s: Linear\n", name.c_str() );
		}
		else if( count==1 ){
			gamma = getFloat16( data );
			if( verbose ) printf("  %s: Gamma: %f\n", name.c_str() , gamma);
		}
		else if( count == 0x00030000 ){ // Type3
			gamma = getFloat( data );
			float a = getFloat( data ), b = getFloat( data ), c = getFloat( data ), d = getFloat( data );
			if( verbose ) printf("  %s: Type3: %f <%f %f %f %f>\n", name.c_str(), gamma, a, b, c, d);
		}
		else {
			std::vector<uint16_t> gammaTable;
			for( uint32_t i=0; i<count; i++) gammaTable.push_back( getUint16( data ) );
			gamma = recognizeTonemap( gammaTable );
			if( verbose ) printf("  %s: LUT with gamma: %f\n", name.c_str(), gamma );
		}
		return gamma;
	}
	void initializeProfile( uint8_t* d, bool verbose=false ) {
		uint8_t* data = d;
		ICC_Header header;
		header.read( data );
		if( verbose ) header.print();
		data+=44;
		int numTags = getUint( data );
		for( int i=0; i<numTags; i++ ) {
			FOURC tagSig = getFourC( data );
			uint32_t offset = getUint(data), dataSize = getUint(data)-8;
			uint8_t* data = d+offset+8;
			if( tagSig.compare( "cprt") ) {
				char temp[200];
				memcpy( temp, data, dataSize );
				for( uint32_t k=0; k<dataSize; k++) if( temp[k]=='\0' ) temp[k]=32;
				temp[dataSize]='\0';
				if( verbose ) printf("  Copyright: %s\n", temp );
			}
			if( tagSig.compare( "wtpt") ) {
				whtPt = getXYZ( data );
				if( verbose ) print_("  WTPT: %C\n", XYZToxyY(whtPt) );
				if( verbose ) print_("  WTPT<XYZ>: %C\n", whtPt );
			}
			if( tagSig.compare( "bkpt") ) {
				blkPt = getXYZ( data );
				if( verbose ) print_("  BKPT: %C\n", XYZToxyY(blkPt) );
			}
			if( tagSig.compare( "rTRC") ) {
				gamma.r = parseGamma( data, "rTRC", verbose );
			}
			if( tagSig.compare( "gTRC") ) {
				gamma.g = parseGamma( data, "gTRC", verbose );
			}
			if( tagSig.compare( "bTRC") ) {
				gamma.b = parseGamma( data, "bTRC", verbose );
			}
			if( tagSig.compare( "rXYZ") ) {
				r = getXYZ( data );
				if( verbose ) print_("  r: %C\n", XYZToxyY(r));
			}
			if( tagSig.compare( "gXYZ") ) {
				g = getXYZ( data );
				if( verbose ) print_("  g: %C\n", g);
			}
			if( tagSig.compare( "bXYZ") ) {
				b = getXYZ( data );
				if( verbose ) print_("  b: %C\n", XYZToxyY(b));
			}
		}
		whtPt = header.illuminantXYZ;
		if( verbose ) printf("\n");
	}
	void initWithJPEG( FILE* f, bool verbose = false ) {
		size_t iccSize;
		uint8_t* iccData = getICC_JPEG( f, iccSize );
		if( iccData != nullptr ) initializeProfile( iccData, verbose );
		delete iccData;
	}
	void initWithJPEG( std::istream& f, bool verbose = false ) {
		size_t iccSize;
		uint8_t* iccData = getICC_JPEG( f, iccSize );
		if( iccData != nullptr ) initializeProfile( iccData, verbose );
		delete iccData;
	}
	void initWithJPEG( const std::filesystem::path& f, bool verbose = false ) {
		size_t iccSize;
		uint8_t* iccData = getICC_JPEG( f, iccSize );
		if( iccData != nullptr ) initializeProfile( iccData, verbose );
		delete iccData;
	}
	void initWithJPEG( const uint8_t* f, long totalSz, bool verbose = false ) {
		size_t iccSize;
		uint8_t* iccData = getICC_JPEG( f, totalSz, iccSize );
		if( iccData != nullptr ) initializeProfile( iccData, verbose );
		delete iccData;
	}

	void initWithPNG( FILE* f, bool verbose = false ) {
		std::vector<uint8_t> iccData = getICC_PNG( f );
		if( iccData.size()>0 ) initializeProfile( iccData.data(), verbose );
	}
	void initWithPNG( std::istream& f, bool verbose = false ) {
		std::vector<uint8_t> iccData = getICC_PNG( f );
		if( iccData.size()>0 ) initializeProfile( iccData.data(), verbose );
	}
	void initWithPNG( const std::filesystem::path& f, bool verbose = false ) {
		std::vector<uint8_t> iccData = getICC_PNG( f );
		if( iccData.size()>0 ) initializeProfile( iccData.data(), verbose );
	}
	void initWithPNG( const uint8_t* f, long sz, bool verbose = false ) {
		std::vector<uint8_t> iccData = getICC_PNG( f, sz );
		if( iccData.size()>0 ) initializeProfile( iccData.data(), verbose );
	}
	void initWithICC( FILE* f, bool verbose = false ) {
		fseek(f,0,SEEK_END);
		size_t iccSize = ftell(f);
		fseek(f,0,SEEK_SET);
		uint8_t* iccData = new uint8_t[iccSize];
		fread((char*)iccData,1,iccSize,f);
		if( iccSize>0 ) initializeProfile( iccData, verbose );
		delete [] iccData;
	}
	void initWithICC( std::istream& f, bool verbose = false ) {
		f.seekg(f.end);
		size_t iccSize = f.tellg();
		f.seekg(f.beg);
		uint8_t* iccData = new uint8_t[iccSize];
		f.read((char*)iccData,iccSize);
		if( iccSize>0 ) initializeProfile( iccData, verbose );
		delete [] iccData;
	}
	void initWithICC( const std::filesystem::path& f, bool verbose = false ) {
		std::ifstream ifs(f,std::ios::binary);
		initWithICC(ifs,verbose);
		ifs.close();
	}
};

} // namespace SCMS

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* SCMS_h */
