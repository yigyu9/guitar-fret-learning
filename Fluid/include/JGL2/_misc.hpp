//
//  misc.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__misc_h
#define JGL2__misc_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/SCMS.hpp>
#include <ww898/cp_utf8.hpp>
#include <ww898/cp_utf32.hpp>
#include <ww898/utf_converters.hpp>
#include <ww898/utf_sizes.hpp>

namespace JGL2 {

template<typename T> str_t to_str (const T & t) {
	std::ostringstream os;
	os.precision(7);
	os << t;
	return os.str ();
}

template<> inline str_t to_str<int> (const int & t) {
	std::ostringstream os;
	os << t;
	return os.str ();
}

inline str_t to_utf8str(char32_t c) {
	typedef ww898::utf::utf_selector_t<char32_t> utf_type;
	typedef ww898::utf::utf_selector_t<char> outf_type;		std::basic_string<char32_t> input;
	input+=c;
	std::basic_string<char> buf_tmp0;
	ww898::utf::convz<utf_type, outf_type>(input.data(), std::back_inserter(buf_tmp0));
	std::basic_string<char> str;
	ww898::utf::conv<utf_type, outf_type>(input.cbegin(), input.cend(), std::back_inserter(str));
	return str;
}

inline std::string toStr( float v, int prec=0 ) {
	float scale = powf(10,float(prec));
	int iv = int(roundf(v*scale));
	std::string ret = std::to_string(std::abs(iv));
	std::string pre = "";
	if( iv!=0 ) {
		if( prec > int(ret.length()) ) pre.resize( prec - int(ret.length()), '0' );
		if( abs(v)<1 ) pre+="0";
	}
	if( v<0 ) pre = "-"+pre;
	ret = pre+ret;
	if( prec>0 && iv!=0 )
		ret.insert(ret.end()-prec,'.');
	
	return ret;
}

//
//
// ******************** Simple Color conversion
//
//

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

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* misc_h */
