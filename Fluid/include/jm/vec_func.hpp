//
//  jm_vec_func.hpp
//  SystemCalib
//
//  Created by Hyun Joon Shin on 2023/08/24.
//

#ifndef jm_vec_func_h
#define jm_vec_func_h

#include "vec.hpp"
#include "scalar_func.hpp"

namespace jm {

#define GEN_UNARY_V__V_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T, typename = std::enable_if_t<TYPE_COND && is_vector_v<T>> > \
auto FUN_NAME ( const T& x ) { \
	if constexpr( vec_length<T> ==4 )		{ return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1]),FUN_NAME(x[2]),FUN_NAME(x[3])); } \
	else if constexpr( vec_length<T> ==3 )	{ return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1]),FUN_NAME(x[2])); } \
	else									{ return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1])); } \
}

#define GEN_BINARY_V_V__V_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T1,typename T2, typename=std::enable_if_t<TYPE_COND && is_vector_v<T1> && is_same_length_v<T1,T2> > > \
auto FUN_NAME ( const T1& x, const T2& y ) { \
	using scalar = common_element_type_t<T1,T2>; \
	if constexpr( vec_length<T1> == 4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2]),FUN_NAME(x[3],y[3])); } \
	else if constexpr( vec_length<T1> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2])); } \
	else									{ return vec_type_t<scalar,2>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1])); } \
}

#define GEN_BINARY_V_VS_V_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T1, typename T2, typename=std::enable_if_t<TYPE_COND&&is_vector_v<T1> && (!is_vector_v<T2>||is_same_length_v<T1,T2>)> > \
auto FUN_NAME ( const T1& x, const T2& y ) { \
	if constexpr ( is_vector_v<T2> ) { \
		using scalar = common_element_type_t<T1,T2>; \
		if constexpr( vec_length<T1> == 4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2]),FUN_NAME(x[3],y[3])); } \
		else if constexpr( vec_length<T1> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2])); } \
		else									{ return vec_type_t<scalar,2>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1])); } \
	} \
	else { \
 		using scalar = vec_element<T1>; \
		if constexpr( vec_length<T1> ==4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x[0],y),FUN_NAME(x[1],y),FUN_NAME(x[2],y),FUN_NAME(x[3],y)); } \
		else if constexpr( vec_length<T1> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x[0],y),FUN_NAME(x[1],y),FUN_NAME(x[2],y)); } \
		else									{ return vec_type_t<scalar,2>(FUN_NAME(x[0],y),FUN_NAME(x[1],y)); } \
	} \
}

#define GEN_BINARY_VS_VS_V_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T1,typename T2, \
typename=std::enable_if_t<(!is_vector_v<T1>||!is_vector_v<T2>||is_same_length_v<T1,T2>)&&(is_vector_v<T1>||is_vector_v<T2>)>> \
auto FUN_NAME ( const T1& x, const T2& y ) { \
	if constexpr ( is_vector_v<T1> ) { \
		if constexpr ( is_vector_v<T2> ) { \
			using scalar = common_element_type_t<T1,T2>; \
			if constexpr( vec_length<T1> ==4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2]),FUN_NAME(x[3],y[3])); } \
			else if constexpr( vec_length<T1> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2])); } \
			else									{ return vec_type_t<scalar,2>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1])); } \
		} \
		else { \
			using scalar = vec_element<T1>; \
			if constexpr( vec_length<T1> == 4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x[0],y),FUN_NAME(x[1],y),FUN_NAME(x[2],y),FUN_NAME(x[3],y)); } \
			else if constexpr( vec_length<T1> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x[0],y),FUN_NAME(x[1],y),FUN_NAME(x[2],y)); } \
			else 									{ return vec_type_t<scalar,2>(FUN_NAME(x[0],y),FUN_NAME(x[1],y)); } \
		} \
	} \
	else { \
		using scalar = vec_element<T2>; \
		if constexpr( vec_length<T2> == 4 )		{ return vec_type_t<scalar,4>(FUN_NAME(x,y[0]),FUN_NAME(x,y[1]),FUN_NAME(x,y[2]),FUN_NAME(x,y[3])); } \
		else if constexpr( vec_length<T2> ==3 )	{ return vec_type_t<scalar,3>(FUN_NAME(x,y[0]),FUN_NAME(x,y[1]),FUN_NAME(x,y[2])); } \
		else									{ return vec_type_t<scalar,2>(FUN_NAME(x,y[0]),FUN_NAME(x,y[1])); } \
	} \
}

#define GEN_BINARY_V__B_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T,typename=std::enable_if_t<TYPE_COND && is_vector_v<T>> > \
auto FUN_NAME ( const T& x ) { \
	if constexpr( vec_length<T> == 4 ) 		{ return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1]),FUN_NAME(x[2]),FUN_NAME(x[3])); } \
	else if constexpr( vec_length<T> == 3 ) { return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1]),FUN_NAME(x[2])); } \
	else									{ return comp_vec_type_t<T>(FUN_NAME(x[0]),FUN_NAME(x[1])); } \
}


// ********************************
//
// Angle and Trigonometry Functions
//
// ********************************
GEN_UNARY_V__V_FUNC( degrees, 		is_float_v<T> );
GEN_UNARY_V__V_FUNC( radians, 		is_float_v<T> );
GEN_UNARY_V__V_FUNC( sin, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( cos, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( tan, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( sinh, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( cosh, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( tanh, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( asin, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( acos, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( atan, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( asinh, 		is_float_v<T> );
GEN_UNARY_V__V_FUNC( acosh, 		is_float_v<T> );
GEN_UNARY_V__V_FUNC( atanh, 		is_float_v<T> );
GEN_BINARY_V_V__V_FUNC( atan, 		is_float_v<T1> && is_float_v<T2> );

// ********************************
//
// Exponentia Functions
//
// ********************************
GEN_BINARY_V_V__V_FUNC( pow,		is_floatd_v<T1> && is_floatd_v<T2> );

GEN_UNARY_V__V_FUNC( exp, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( log, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( exp2, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( log2, 			is_float_v<T> );
GEN_UNARY_V__V_FUNC( sqrt, 			is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( inversesqrt,	is_floatd_v<T> );

// ********************************
//
// Common Functions
//
// ********************************
GEN_UNARY_V__V_FUNC( abs,  			is_signed_v<T> );
GEN_UNARY_V__V_FUNC( sign, 			is_signed_v<T> );
GEN_UNARY_V__V_FUNC( floor,			is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( trunc,			is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( round,			is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( roundEven,		is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( ceil,			is_floatd_v<T> );
GEN_UNARY_V__V_FUNC( fract,			is_floatd_v<T> );

GEN_BINARY_V_VS_V_FUNC( mod,		is_floatd_v<T1> );

template<typename T,typename T2, typename = std::enable_if_t<is_vector_v<T> && is_same_length_v<T,T2> && is_floatd_v<T> && is_floatd_v<T2>> >
auto modf(const T& xx, T2& yy) {
	yy = floor(xx);
	return fract(xx);
}
GEN_BINARY_VS_VS_V_FUNC( min, is_number_v<T1> );
GEN_BINARY_VS_VS_V_FUNC( max, is_number_v<T1> );

template<typename T1,typename T2,typename T3, typename=std::enable_if_t<is_vector_v<T1> || is_vector_v<T2> || is_vector_v<T3>> >
auto clamp ( const T1& x, const T2& minVal, const T3& maxVal ) {
	return min(max(x, minVal), maxVal);
}

template<typename T1,typename T2,typename T3,
typename=std::enable_if_t<(is_vector_v<T1> || is_vector_v<T3>) && is_same_length_v<T1,T2> && is_floatd_v<T1>> >
auto mix ( const T1& x, const T2& y, const T3& a ) {
	if constexpr ( is_element_type_v<T3, bool> ) {
		if constexpr ( is_vector_v<T3> )	{
			if constexpr( vec_length<T3> ==4 )		return common_vec_type_t<T1,T2>(a[0]?y[0]:x[0],a[1]?y[1]:x[1],a[2]?y[2]:x[2],a[3]?y[3]:x[3]);
			else if constexpr( vec_length<T3> ==3 )	return common_vec_type_t<T1,T2>(a[0]?y[0]:x[0],a[1]?y[1]:x[1],a[2]?y[2]:x[2]);
			else									return common_vec_type_t<T1,T2>(a[0]?y[0]:x[0],a[1]?y[1]:x[1]);
		}
		else {
			return a?y:x;
		}
	}
	else {
		return x*(comp_vec_type_t<T3>(1)-a)+y*a;
	}
}

GEN_BINARY_VS_VS_V_FUNC( step, is_float_v<T1> );

template<typename T1,typename T2, typename T3,
typename=std::enable_if_t<(is_vector_v<T1> || is_vector_v<T2> || is_vector_v<T3>)
&& is_same_length_v<T2,T3>
&& ( !is_vector_v<T1> || !is_vector_v<T2> || is_same_length_v<T1,T2> )>>
auto smoothstep ( const T2& x1, const T3& x2, const T1& y ) { \
	if constexpr ( is_vector_v<T2> ) {
		using vecType = comp_vec_type_t<T2>;
		auto t = clamp((y-x1)/(x2-x1),vecType(0),vecType(1));
		return t*t*(3-2*t);
	}
	else if constexpr ( is_vector_v<T1> ) {
		using vecType = comp_vec_type_t<T1>;
		auto t = clamp((y-x1)/(x2-x1),vecType(0),vecType(1));
		return t*t*(3-2*t);
	}
	else {
		using vecType = comp_vec_type_t<T3>;
		auto t = clamp((y-x1)/(x2-x1),vecType(0),vecType(1));
		return t*t*(3-2*t);
	}
}

GEN_BINARY_V__B_FUNC( isnan, is_floatd_v<T> );
GEN_BINARY_V__B_FUNC( isinf, is_floatd_v<T> );


template<typename T, typename=std::enable_if_t<is_vector_v<T> && is_element_type_v<T,float> > >
auto floatBitsToInt(const T& v) {
	if constexpr( vec_length<T> ==4 )		return vec_type_t<int,vec_length<T>>(*(int*)(&(v[0])),*(int*)(&(v[1])),*(int*)(&(v[2])),*(int*)(&(v[3])));
	else if constexpr( vec_length<T> ==3 )	return vec_type_t<int,vec_length<T>>(*(int*)(&(v[0])),*(int*)(&(v[1])),*(int*)(&(v[2])));
	else									return vec_type_t<int,vec_length<T>>(*(int*)(&(v[0])),*(int*)(&(v[1])));
}
template<typename T, typename=std::enable_if_t<is_vector_v<T> && is_element_type_v<T,float>> >
auto floatBitsToUint(const T& v) {
	if constexpr( vec_length<T> ==4 )		return vec_type_t<uint,vec_length<T>>(*(uint*)(&(v[0])),*(uint*)(&(v[1])),*(uint*)(&(v[2])),*(uint*)(&(v[3])));
	else if constexpr( vec_length<T> ==3 )	return vec_type_t<uint,vec_length<T>>(*(uint*)(&(v[0])),*(uint*)(&(v[1])),*(uint*)(&(v[2])));
	else									return vec_type_t<uint,vec_length<T>>(*(uint*)(&(v[0])),*(uint*)(&(v[1])));
}
template<typename T, typename=std::enable_if_t<is_vector_v<T> && is_element_type_v<T,int> > >
auto intBitsToFloat(const T& v) {
	if constexpr( vec_length<T> ==4 )		return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])),*(float*)(&(v[2])),*(float*)(&(v[3])));
	else if constexpr( vec_length<T> ==3 )	return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])),*(float*)(&(v[2])));
	else									return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])));
}
template<typename T, typename=std::enable_if_t<is_vector_v<T> && is_element_type_v<T,uint> > >
auto uintBitsToFloat(const T& v) {
	if constexpr( vec_length<T> ==4 )		return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])),*(float*)(&(v[2])),*(float*)(&(v[3])));
	else if constexpr( vec_length<T> ==3 )	return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])),*(float*)(&(v[2])));
	else									return vec_type_t<float,vec_length<T>>(*(float*)(&(v[0])),*(float*)(&(v[1])));
}

template<typename T,typename T2, typename T3,
typename=std::enable_if_t<is_vector_v<T> && is_same_length_v<T,T2> && is_same_length_v<T,T3> && is_floatd_v<T> >>
auto fma(const T& a, const T2& b, const T3& c) {
	return a*b+c;
}

template<typename T,typename=std::enable_if_t<is_vector<T>::value> >
auto frexp(const T& x, vec_type_t<int,vec_length<T>>& expr) {
	if constexpr( vec_length<T> ==4 )		return comp_vec_type_t<T>(frexp(x[0],expr[0]),frexp(x[1],expr[1]),frexp(x[2],expr[2]),frexp(x[3],expr[3]));
	else if constexpr( vec_length<T> ==3 )	return comp_vec_type_t<T>(frexp(x[0],expr[0]),frexp(x[1],expr[1]),frexp(x[2],expr[2]));
	else									return comp_vec_type_t<T>(frexp(x[0],expr[0]),frexp(x[1],expr[1]));
}

template<typename T0, typename T1,typename=std::enable_if_t<is_vector_v<T0> && is_element_type_v<T1,int> && is_same_length_v<T0,T1> && 	is_floatd_v<T0>>>
auto ldexp(const T0& x, const T1& expr) {
	using scalar = vec_element<T0>;
	if constexpr ( vec_length<T0> ==4 ) {
		return comp_vec_type_t<T0>(x[0]*exp2(scalar(expr[0])),x[1]*exp2(scalar(expr[1])),x[2]*exp2(scalar(expr[2])),x[3]*exp2(scalar(expr[3])));
	}
	else if constexpr ( vec_length<T0> ==3 ) {
		return comp_vec_type_t<T0>(x[0]*exp2(scalar(expr[0])),x[1]*exp2(scalar(expr[1])),x[2]*exp2(scalar(expr[2])));
	}
	else {
		return comp_vec_type_t<T0>(x[0]*exp2(scalar(expr[0])),x[1]*exp2(scalar(expr[1])));
	}
}



// ********************************
//
// Floating-Point Pack and Unpack Functions
//
// ********************************






// ********************************
//
// Geometric Functions
//
// ********************************

template<typename T0,typename T1,typename=std::enable_if_t<is_same_length_v<T0,T1>>>
auto dot ( const T0& x, const T1& y ) {
	using scalar = common_element_type_t<T0,T1>;
	if constexpr ( is_vector_v<T0> ) {
		if constexpr( vec_length<T0> ==4 )		return scalar(x[0]*y[0]+x[1]*y[1]+x[2]*y[2]+x[3]*y[3]);
		else if constexpr( vec_length<T0> ==3 )	return scalar(x[0]*y[0]+x[1]*y[1]+x[2]*y[2]);
		else									return scalar(x[0]*y[0]+x[1]*y[1]);
	}
	else return x*y;
}

template<typename T,typename=std::enable_if_t<is_vector_v<T>> >
auto length(const T& x) {
	return sqrt(dot(x,x));
}

template<typename T0,typename T1,typename=std::enable_if_t<is_vector_v<T0> && is_same_length_v<T0,T1>>>
auto distance ( const T0& p0, const T1& p1 ) {
	return length(p1-p0);
}

template<typename T,typename=std::enable_if_t<is_vector<T>::value> >
auto normalize(const T& x) {
	return x/length(x);
}

template<typename T0,typename T1,typename=std::enable_if_t<is_length_v<T0,3> && is_length_v<T1,3>>>
auto cross(const T0& a, const T1& b) {
	using scalar = common_element_type_t<T0,T1>;
	return vec_type_t<scalar,3>(scalar(a[1]) * scalar(b[2]) - scalar(a[2]) * scalar(b[1]),
								scalar(a[2]) * scalar(b[0]) - scalar(a[0]) * scalar(b[2]),
								scalar(a[0]) * scalar(b[1]) - scalar(a[1]) * scalar(b[0]));
}

template<typename T1,typename T2,typename T3,typename=std::enable_if_t<is_vector_v<T2> && is_same_length_v<T2,T3>> >
comp_vec_type_t<T1> faceforward(const T1& N, const T2& I, const T3& ref) {
	comp_vec_type_t<T1> n=N;
	return dot(ref,I)<0?n:-n;
}

template<typename T1,typename T2,typename=std::enable_if_t<is_vector_v<T1> && is_same_length_v<T1,T2>>>
comp_vec_type_t<T1> reflect(const T1& I, const T2& N) {
	using scalar = std::common_type_t<vec_element<T1>,vec_element<T2>>;
	using vecType = vec_type_t<scalar,vec_length<T1>>;
	vecType n = N;
	return vecType(I-2*dot(n,I)*n);
}

template<typename T1,typename T2,typename T3,typename=std::enable_if_t<is_vector_v<T1> && is_same_length_v<T1,T2> && !is_vector_v<T3> && is_floatd_v<T3> >>
comp_vec_type_t<T1> refract(const T1& I, const T2& N, T3 eta) {
	using scalar = std::common_type_t<vec_element<T1>,vec_element<T2>,T3>;
	using vecType = vec_type_t<scalar,vec_length<T1>>;
	scalar NdotI =dot(N,I);
	scalar k = scalar(1) - eta*eta*( scalar(1)-NdotI*NdotI );
	if( k<0 ) return vecType(0);
	return vecType(eta*I-(eta*NdotI+sqrt(k))*N);
}


// ********************************
//
// Vector Relational Functions
//
// ********************************

#define GEN_BINARY_V_V__B_FUNC( FUN_NAME, TYPE_COND ) \
template<typename T0,typename T1,typename=std::enable_if_t<TYPE_COND && is_vector_v<T0> && is_same_length_v<T0,T1>>> \
auto FUN_NAME ( const T0& x, const T1& y ) { \
	if constexpr ( vec_length<T0> ==4 ) \
		return vec_type_t<bool,vec_length<T0>>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2]),FUN_NAME(x[3],y[3])); \
	else if constexpr ( vec_length<T0> ==3 ) \
		return vec_type_t<bool,vec_length<T0>>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1]),FUN_NAME(x[2],y[2])); \
	else \
		return vec_type_t<bool,vec_length<T0>>(FUN_NAME(x[0],y[0]),FUN_NAME(x[1],y[1])); \
}

GEN_BINARY_V_V__B_FUNC( lessThan,			is_number_v<T0> && is_number_v<T1> );
GEN_BINARY_V_V__B_FUNC( lessThanEqual,		is_number_v<T0> && is_number_v<T1> );
GEN_BINARY_V_V__B_FUNC( greaterThan,		is_number_v<T0> && is_number_v<T1> );
GEN_BINARY_V_V__B_FUNC( greaterThanEqual, 	is_number_v<T0> && is_number_v<T1> );
GEN_BINARY_V_V__B_FUNC( equal,				is_number_v<T0> && is_number_v<T1> );
GEN_BINARY_V_V__B_FUNC( notEqual,			is_number_v<T0> && is_number_v<T1> );

template<typename T,typename=std::enable_if_t<is_vector_v<T>&&is_element_type_v<T, bool>>>
auto any(const T& x) {
	if constexpr ( vec_length<T> ==4 )
		return x[0]||x[1]||x[2]||x[3];
	else if constexpr ( vec_length<T> ==3 )
		return x[0]||x[1]||x[2];
	else
		return x[0]||x[1];
}

template<typename T,typename=std::enable_if_t<is_vector_v<T>&&is_element_type_v<T, bool>>>
auto all(const T& x) {
	if constexpr ( vec_length<T> ==4 )		return x[0]&&x[1]&&x[2]&&x[3];
	else if constexpr ( vec_length<T> ==3 )	return x[0]&&x[1]&&x[2];
	else									return x[0]&&x[1];
}

template<typename T,typename=std::enable_if_t<is_vector_v<T>&&is_element_type_v<T, bool>>>
auto not_(const T& x) {
	if constexpr ( vec_length<T> ==4 )		return comp_vec_type_t<T>(!x[0],!x[1],!x[2],!x[3]);
	else if constexpr ( vec_length<T> ==3 )	return comp_vec_type_t<T>(!x[0],!x[1],!x[2]);
	else									return comp_vec_type_t<T>(!x[0],!x[1]);
}

template<typename T> auto min( const T& a ) { return a; }
template<typename T, typename... TYPES> auto min( const T& a, TYPES... bs ) {
	auto b = min(bs...);
	using btype = decltype(b);
	if constexpr ( is_vector_v<btype> ) {
		if constexpr ( is_vector_v<T> ) {
			static_assert( vec_length<T> == vec_length<btype>);
			if constexpr ( vec_length<T> == 4 )	return common_vec_type_t<T, btype>( a[0]<b[0]?a[0]:b[0], a[1]<b[1]?a[1]:b[1], a[2]<b[2]?a[2]:b[2], a[3]<b[3]?a[3]:b[3] );
			if constexpr ( vec_length<T> == 3 )	return common_vec_type_t<T, btype>( a[0]<b[0]?a[0]:b[0], a[1]<b[1]?a[1]:b[1], a[2]<b[2]?a[2]:b[2] );
			else								return common_vec_type_t<T, btype>( a[0]<b[0]?a[0]:b[0], a[1]<b[1]?a[1]:b[1] );
		}
		else {
			if constexpr ( vec_length<btype> == 4 )	return common_vec_type_t<btype,T>( a<b[0]?a:b[0], a<b[1]?a:b[1], a<b[2]?a:b[2], a<b[3]?a:b[3] );
			if constexpr ( vec_length<btype> == 3 )	return common_vec_type_t<btype,T>( a<b[0]?a:b[0], a<b[1]?a:b[1], a<b[2]?a:b[2] );
			else									return common_vec_type_t<btype,T>( a<b[0]?a:b[0], a<b[1]?a:b[1] );
		}
	}
	else {
		if constexpr ( is_vector_v<T> ) {
			static_assert( vec_length<T> == vec_length<btype>);
			if constexpr ( vec_length<T> == 4 )	return common_vec_type_t<T, btype>( a[0]<b?a[0]:b, a[1]<b?a[1]:b, a[2]<b?a[2]:b, a[3]<b?a[3]:b );
			if constexpr ( vec_length<T> == 3 )	return common_vec_type_t<T, btype>( a[0]<b?a[0]:b, a[1]<b?a[1]:b, a[2]<b?a[2]:b );
			else								return common_vec_type_t<T, btype>( a[0]<b?a[0]:b, a[1]<b?a[1]:b );
		}
		else {
			return std::common_type_t<T,btype>( a<b?a:b );
		}
	}
}

template<typename T> auto max( const T& a ) { return a; }
template<typename T, typename... TYPES> auto max( const T& a, TYPES... bs ) {
	auto b = max(bs...);
	using btype = decltype(b);
	if constexpr ( is_vector_v<btype> ) {
		if constexpr ( is_vector_v<T> ) {
			static_assert( vec_length<T> == vec_length<btype>);
			if constexpr ( vec_length<T> == 4 )	return common_vec_type_t<T, btype>( a[0]>b[0]?a[0]:b[0], a[1]>b[1]?a[1]:b[1], a[2]>b[2]?a[2]:b[2], a[3]>b[3]?a[3]:b[3] );
			if constexpr ( vec_length<T> == 3 )	return common_vec_type_t<T, btype>( a[0]>b[0]?a[0]:b[0], a[1]>b[1]?a[1]:b[1], a[2]>b[2]?a[2]:b[2] );
			else								return common_vec_type_t<T, btype>( a[0]>b[0]?a[0]:b[0], a[1]>b[1]?a[1]:b[1] );
		}
		else {
			if constexpr ( vec_length<btype> == 4 )	return common_vec_type_t<btype,T>( a>b[0]?a:b[0], a>b[1]?a:b[1], a>b[2]?a:b[2], a>b[3]?a:b[3] );
			if constexpr ( vec_length<btype> == 3 )	return common_vec_type_t<btype,T>( a>b[0]?a:b[0], a>b[1]?a:b[1], a>b[2]?a:b[2] );
			else									return common_vec_type_t<btype,T>( a>b[0]?a:b[0], a>b[1]?a:b[1] );
		}
	}
	else {
		if constexpr ( is_vector_v<T> ) {
			static_assert( vec_length<T> == vec_length<btype>);
			if constexpr ( vec_length<T> == 4 )	return common_vec_type_t<T, btype>( a[0]>b?a[0]:b, a[1]>b?a[1]:b, a[2]>b?a[2]:b, a[3]>b?a[3]:b );
			if constexpr ( vec_length<T> == 3 )	return common_vec_type_t<T, btype>( a[0]>b?a[0]:b, a[1]>b?a[1]:b, a[2]>b?a[2]:b );
			else								return common_vec_type_t<T, btype>( a[0]>b?a[0]:b, a[1]>b?a[1]:b );
		}
		else {
			return std::common_type_t<T,btype>( a>b?a:b );
		}
	}
}

}

#endif /* jm_vec_func_h */
