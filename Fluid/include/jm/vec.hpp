//
//  jm_vec.hpp
//  SystemCalib
//
//  Created by Hyun Joon Shin on 2023/08/22.
//

#ifndef jm_vec_h
#define jm_vec_h

#include <cmath>
#include <type_traits>
#include "half.hpp"

namespace jm {

typedef float scalar_t;
typedef unsigned int uint;
typedef unsigned short ushort;
typedef unsigned char uchar;


template<typename T> struct mvec2_t;
template<typename T> struct mvec3_t;
template<typename T> struct mvec4_t;

template<typename A> 		struct _type_{ typedef A type; };
template<typename A> 		struct _elmt_: _type_<A>{};
template<int N>  	   		struct _cnt_ { static const int n=N; };
template<typename A> 		struct _lngt_: _cnt_<1>{};
template<typename A,int N>	struct _mvec_: _type_<A>{};


#define ELEMENT_TYPE_EXTRACTOR( NAME ) \
template<> struct _elmt_< NAME <float >>: _type_<float> {}; \
template<> struct _elmt_< NAME <half>>  : _type_<half> {}; \
template<> struct _elmt_< NAME <double>>: _type_<double>{}; \
template<> struct _elmt_< NAME <bool>>  : _type_<bool>  {}; \
template<> struct _elmt_< NAME <char>>  : _type_<char>  {}; \
template<> struct _elmt_< NAME <uchar>> : _type_<uchar> {}; \
template<> struct _elmt_< NAME <short>> : _type_<short> {}; \
template<> struct _elmt_< NAME <ushort>>: _type_<ushort>{}; \
template<> struct _elmt_< NAME <int>>   : _type_<int>   {}; \
template<> struct _elmt_< NAME <uint>>  : _type_<uint>  {};

#define ELEMENT_COUNT_EXTRACTOR( NAME, N ) \
template<> struct _lngt_< NAME<float> > : _cnt_<N> {}; \
template<> struct _lngt_< NAME<half> >  : _cnt_<N> {}; \
template<> struct _lngt_< NAME<double> >: _cnt_<N> {}; \
template<> struct _lngt_< NAME<bool> >  : _cnt_<N> {}; \
template<> struct _lngt_< NAME<char> >  : _cnt_<N> {}; \
template<> struct _lngt_< NAME<uchar> > : _cnt_<N> {}; \
template<> struct _lngt_< NAME<short> > : _cnt_<N> {}; \
template<> struct _lngt_< NAME<ushort> >: _cnt_<N> {}; \
template<> struct _lngt_< NAME<int> >   : _cnt_<N> {}; \
template<> struct _lngt_< NAME<uint> >  : _cnt_<N> {};

#define VECTOR_GENERATOR( NAME, N ) \
template<> struct _mvec_<float, N>: _type_< NAME <float> > {}; \
template<> struct _mvec_<half,  N>: _type_< NAME <half> > {}; \
template<> struct _mvec_<double,N>: _type_< NAME <double> > {}; \
template<> struct _mvec_<bool,  N>: _type_< NAME <bool> > {}; \
template<> struct _mvec_<char,  N>: _type_< NAME <char> > {}; \
template<> struct _mvec_<uchar, N>: _type_< NAME <uchar> > {}; \
template<> struct _mvec_<short, N>: _type_< NAME <short> > {}; \
template<> struct _mvec_<ushort,N>: _type_< NAME <ushort> > {}; \
template<> struct _mvec_<int,   N>: _type_< NAME <int> > {}; \
template<> struct _mvec_<uint,  N>: _type_< NAME <uint> > {};

template<> struct _elmt_<float >: _type_<float >{};
template<> struct _elmt_<half  >: _type_<half  >{};
template<> struct _elmt_<double>: _type_<double>{};
template<> struct _elmt_<bool  >: _type_<bool  >{};
template<> struct _elmt_<char  >: _type_<char  >{};
template<> struct _elmt_<uchar >: _type_<uchar >{};
template<> struct _elmt_<short >: _type_<float >{};
template<> struct _elmt_<ushort>: _type_<ushort>{};
template<> struct _elmt_<int   >: _type_<int   >{};
template<> struct _elmt_<uint  >: _type_<uint  >{};

template<> struct _mvec_<float ,1>:_type_<float > {};
template<> struct _mvec_<half  ,1>:_type_<half  > {};
template<> struct _mvec_<double,1>:_type_<double> {};
template<> struct _mvec_<bool  ,1>:_type_<bool  > {};
template<> struct _mvec_<char  ,1>:_type_<char  > {};
template<> struct _mvec_<uchar ,1>:_type_<uchar > {};
template<> struct _mvec_<short ,1>:_type_<short > {};
template<> struct _mvec_<ushort,1>:_type_<ushort> {};
template<> struct _mvec_<int   ,1>:_type_<int   > {};
template<> struct _mvec_<uint  ,1>:_type_<uint  > {};

template<typename T0,typename T1> struct is_same_length : std::integral_constant<bool,_lngt_<T0>::n==_lngt_<T1>::n> {};
template<typename T0,typename T1> inline constexpr bool is_same_length_v = is_same_length<T0,T1>::value;

template<typename T> inline constexpr int vec_length = _lngt_<T>::n;
template<typename T> using vec_element = typename _elmt_<T>::type;

template<typename T0,typename T1> struct is_same_element : std::integral_constant<bool,std::is_same<typename _elmt_<T0>::type, typename _elmt_<T1>::type>::value> {};
template<typename T0,typename T1> inline constexpr bool is_same_element_v = is_same_element<T0,T1>::value;

template<typename T0,typename T1> struct is_element_type : std::integral_constant<bool,std::is_same<typename _elmt_<T0>::type, T1>::value> {};
template<typename T0,typename T1> inline constexpr bool is_element_type_v = is_element_type<T0,T1>::value;

template<typename T,int N> struct is_length : std::integral_constant<bool,_lngt_<T>::n==N> {};
template<typename T,int N> inline constexpr bool is_length_v = is_length<T,N>::value;


template<typename T0, typename T1> using common_element_type = std::common_type<typename _elmt_<T0>::type, typename _elmt_<T1>::type>;
template<typename T0, typename T1> using common_element_type_t = typename common_element_type<T0,T1>::type;

template<typename T> struct is_float : std::integral_constant< bool,std::is_same<float, typename _elmt_<T>::type>::value> {};
template<typename T> inline constexpr bool is_float_v = is_float<T>::value;

template<typename T> struct is_floatd : std::integral_constant< bool,
std::is_same<float, typename _elmt_<T>::type>::value
||std::is_same<half, typename _elmt_<T>::type>::value
||std::is_same<double, typename _elmt_<T>::type>::value> {};
template<typename T> inline constexpr bool is_floatd_v = is_floatd<T>::value;

template<typename T> struct is_signed : std::integral_constant< bool,
std::is_same<float, typename _elmt_<T>::type>::value
||std::is_same<half, typename _elmt_<T>::type>::value
||std::is_same<double, typename _elmt_<T>::type>::value
||std::is_same<int, typename _elmt_<T>::type>::value
> {};
template<typename T> inline constexpr bool is_signed_v = is_signed<T>::value;

template<typename T> struct is_number : std::integral_constant< bool,
std::is_same<float, typename _elmt_<T>::type>::value
||std::is_same<half, typename _elmt_<T>::type>::value
||std::is_same<double, typename _elmt_<T>::type>::value
||std::is_same<int, typename _elmt_<T>::type>::value
||std::is_same<uint, typename _elmt_<T>::type>::value
> {};
template<typename T> inline constexpr bool is_number_v = is_number<T>::value;

template<typename T> struct is_vector : std::integral_constant< bool, _lngt_<T>::n!=1 > {};
template<typename T> inline constexpr bool is_vector_v = is_vector<T>::value;

template<typename T> struct comp_vec_type :_type_<typename _mvec_<typename _elmt_<T>::type,_lngt_<T>::n>::type>{};
template<typename T> using comp_vec_type_t = typename comp_vec_type<T>::type;
template<typename T,int n> using vec_type_t = typename _mvec_<T,n>::type;

template<typename T0, typename T1> struct common_vec_type : _type_<typename _mvec_<common_element_type_t<T0,T1>,_lngt_<T0>::n>::type>{};
template<typename T0, typename T1> using common_vec_type_t = typename common_vec_type<T0,T1>::type;

#define SET_TYPE_VECTOR(BASENAME) \
//template<typename T> struct is_vector<BASENAME<T>>:std::integral_constant<bool,true> {}


SET_TYPE_VECTOR			(mvec2_t);
ELEMENT_TYPE_EXTRACTOR	(mvec2_t);
ELEMENT_COUNT_EXTRACTOR	(mvec2_t,2);
VECTOR_GENERATOR		(mvec2_t,2);

SET_TYPE_VECTOR			(mvec3_t);
ELEMENT_TYPE_EXTRACTOR	(mvec3_t);
ELEMENT_COUNT_EXTRACTOR	(mvec3_t,3);
VECTOR_GENERATOR		(mvec3_t,3);

SET_TYPE_VECTOR			(mvec4_t);
ELEMENT_TYPE_EXTRACTOR	(mvec4_t);
ELEMENT_COUNT_EXTRACTOR	(mvec4_t,4);
VECTOR_GENERATOR		(mvec4_t,4);

#define GEN_SWIZZLE_DEF_2_(TYPENAME,SRCN,N0,N1) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[2]={N0,N1}; \
	T v[SRCN]; \
	operator mvec2_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]]; } \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,2);

#define GEN_SWIZZLE_DEF_3_(TYPENAME,SRCN,N0,N1,N2) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[3]={N0,N1,N2}; \
	T v[SRCN]; \
	operator mvec3_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]];} \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,3);

#define GEN_SWIZZLE_DEF_4_(TYPENAME,SRCN,N0,N1,N2,N3) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[4]={N0,N1,N2,N3}; \
	T v[SRCN]; \
	operator mvec4_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]];} \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,4);

#define GEN_SWIZZLE_DEF_2C(TYPENAME,SRCN,N0,N1) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[2]={N0,N1}; \
	T v[SRCN]; \
	operator mvec2_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]];} \
	template<typename F,typename=std::enable_if_t<vec_length<F> ==2>> mvec2_t<T> operator=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==2>> mvec2_t<T> operator+=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==2>> mvec2_t<T> operator-=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==2>> mvec2_t<T> operator*=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==2>> mvec2_t<T> operator/=(const F&); \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,2);

#define GEN_SWIZZLE_DEF_3C(TYPENAME,SRCN,N0,N1,N2) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[3]={N0,N1,N2}; \
	T v[SRCN]; \
	operator mvec3_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]];} \
	template<typename F,typename=std::enable_if_t<vec_length<F> ==3>> mvec3_t<T> operator=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==3>> mvec3_t<T> operator+=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==3>> mvec3_t<T> operator-=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==3>> mvec3_t<T> operator*=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==3>> mvec3_t<T> operator/=(const F&); \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,3);

#define GEN_SWIZZLE_DEF_4C(TYPENAME,SRCN,N0,N1,N2,N3) \
template<typename T> struct TYPENAME { \
	static constexpr int idx[4]={N0,N1,N2,N3}; \
	T v[SRCN]; \
	operator mvec4_t<T>() const; \
	T& operator[](int i){return v[idx[i]];} \
	const T& operator[](int i)const{return v[idx[i]];} \
	template<typename F,typename=std::enable_if_t<vec_length<F> ==4>> mvec4_t<T> operator=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==4>> mvec4_t<T> operator+=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==4>> mvec4_t<T> operator-=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==4>> mvec4_t<T> operator*=(const F&); \
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || vec_length<F> ==4>> mvec4_t<T> operator/=(const F&); \
}; \
SET_TYPE_VECTOR			(TYPENAME); \
ELEMENT_TYPE_EXTRACTOR	(TYPENAME); \
ELEMENT_COUNT_EXTRACTOR	(TYPENAME,4);


GEN_SWIZZLE_DEF_2_(mvec2_xx,2,0,0);		GEN_SWIZZLE_DEF_2C(mvec2_xy,2,0,1);		GEN_SWIZZLE_DEF_2C(mvec2_yx,2,1,0);		GEN_SWIZZLE_DEF_2_(mvec2_yy,2,1,1);

GEN_SWIZZLE_DEF_2_(mvec3_xx,3,0,0);		GEN_SWIZZLE_DEF_2C(mvec3_xy,3,0,1);		GEN_SWIZZLE_DEF_2C(mvec3_xz,3,0,2);
GEN_SWIZZLE_DEF_2C(mvec3_yx,3,1,0);		GEN_SWIZZLE_DEF_2_(mvec3_yy,3,1,1);		GEN_SWIZZLE_DEF_2C(mvec3_yz,3,1,2);
GEN_SWIZZLE_DEF_2C(mvec3_zx,3,2,0);		GEN_SWIZZLE_DEF_2C(mvec3_zy,3,2,1);		GEN_SWIZZLE_DEF_2_(mvec3_zz,3,2,2);

GEN_SWIZZLE_DEF_2_(mvec4_xx,4,0,1);		GEN_SWIZZLE_DEF_2C(mvec4_xy,4,0,1);		GEN_SWIZZLE_DEF_2C(mvec4_xz,4,0,2);		GEN_SWIZZLE_DEF_2C(mvec4_xw,4,0,3);
GEN_SWIZZLE_DEF_2C(mvec4_yx,4,1,0);		GEN_SWIZZLE_DEF_2_(mvec4_yy,4,1,1);		GEN_SWIZZLE_DEF_2C(mvec4_yz,4,1,2);		GEN_SWIZZLE_DEF_2C(mvec4_yw,4,1,3);
GEN_SWIZZLE_DEF_2C(mvec4_zx,4,2,0);		GEN_SWIZZLE_DEF_2C(mvec4_zy,4,2,1);		GEN_SWIZZLE_DEF_2_(mvec4_zz,4,2,2);		GEN_SWIZZLE_DEF_2C(mvec4_zw,4,2,3);
GEN_SWIZZLE_DEF_2C(mvec4_wx,4,3,0);		GEN_SWIZZLE_DEF_2C(mvec4_wy,4,3,1);		GEN_SWIZZLE_DEF_2C(mvec4_wz,4,3,2);		GEN_SWIZZLE_DEF_2_(mvec4_ww,4,3,3);



GEN_SWIZZLE_DEF_3_(mvec2_xxx,2,0,0,0);	GEN_SWIZZLE_DEF_3_(mvec2_xxy,2,0,0,1);	GEN_SWIZZLE_DEF_3_(mvec2_xyx,2,0,1,0);	GEN_SWIZZLE_DEF_3_(mvec2_xyy,2,0,1,1);
GEN_SWIZZLE_DEF_3_(mvec2_yxx,2,1,0,0);	GEN_SWIZZLE_DEF_3_(mvec2_yxy,2,1,0,1);	GEN_SWIZZLE_DEF_3_(mvec2_yyx,2,1,1,0);	GEN_SWIZZLE_DEF_3_(mvec2_yyy,2,1,1,1);

GEN_SWIZZLE_DEF_3_(mvec3_xxx,3,0,0,0);	GEN_SWIZZLE_DEF_3_(mvec3_xxy,3,0,0,1);	GEN_SWIZZLE_DEF_3_(mvec3_xxz,3,0,0,2);
GEN_SWIZZLE_DEF_3_(mvec3_xyx,3,0,1,0);	GEN_SWIZZLE_DEF_3_(mvec3_xyy,3,0,1,1);	GEN_SWIZZLE_DEF_3C(mvec3_xyz,3,0,1,2);
GEN_SWIZZLE_DEF_3_(mvec3_xzx,3,0,2,0);	GEN_SWIZZLE_DEF_3C(mvec3_xzy,3,0,2,1);	GEN_SWIZZLE_DEF_3_(mvec3_xzz,3,0,2,2);
GEN_SWIZZLE_DEF_3_(mvec3_yxx,3,1,0,0);	GEN_SWIZZLE_DEF_3_(mvec3_yxy,3,1,0,1);	GEN_SWIZZLE_DEF_3C(mvec3_yxz,3,1,0,2);
GEN_SWIZZLE_DEF_3_(mvec3_yyx,3,1,1,0);	GEN_SWIZZLE_DEF_3_(mvec3_yyy,3,1,1,1);	GEN_SWIZZLE_DEF_3_(mvec3_yyz,3,1,1,2);
GEN_SWIZZLE_DEF_3C(mvec3_yzx,3,1,2,0);	GEN_SWIZZLE_DEF_3_(mvec3_yzy,3,1,2,1);	GEN_SWIZZLE_DEF_3_(mvec3_yzz,3,1,2,2);
GEN_SWIZZLE_DEF_3_(mvec3_zxx,3,2,0,0);	GEN_SWIZZLE_DEF_3C(mvec3_zxy,3,2,0,1);	GEN_SWIZZLE_DEF_3_(mvec3_zxz,3,2,0,2);
GEN_SWIZZLE_DEF_3C(mvec3_zyx,3,2,1,0);	GEN_SWIZZLE_DEF_3_(mvec3_zyy,3,2,1,1);	GEN_SWIZZLE_DEF_3_(mvec3_zyz,3,2,1,2);
GEN_SWIZZLE_DEF_3_(mvec3_zzx,3,2,2,0);	GEN_SWIZZLE_DEF_3_(mvec3_zzy,3,2,2,1);	GEN_SWIZZLE_DEF_3_(mvec3_zzz,3,2,2,2);

GEN_SWIZZLE_DEF_3_(mvec4_xxx,4,0,0,0);		GEN_SWIZZLE_DEF_3_(mvec4_xxy,4,0,0,1);		GEN_SWIZZLE_DEF_3_(mvec4_xxz,4,0,0,2);		GEN_SWIZZLE_DEF_3_(mvec4_xxw,4,0,0,3);
GEN_SWIZZLE_DEF_3_(mvec4_xyx,4,0,1,0);		GEN_SWIZZLE_DEF_3_(mvec4_xyy,4,0,1,1);		GEN_SWIZZLE_DEF_3C(mvec4_xyz,4,0,1,2);		GEN_SWIZZLE_DEF_3C(mvec4_xyw,4,0,1,3);
GEN_SWIZZLE_DEF_3_(mvec4_xzx,4,0,2,0);		GEN_SWIZZLE_DEF_3C(mvec4_xzy,4,0,2,1);		GEN_SWIZZLE_DEF_3_(mvec4_xzz,4,0,2,2);		GEN_SWIZZLE_DEF_3C(mvec4_xzw,4,0,2,3);
GEN_SWIZZLE_DEF_3_(mvec4_xwx,4,0,3,0);		GEN_SWIZZLE_DEF_3C(mvec4_xwy,4,0,3,1);		GEN_SWIZZLE_DEF_3C(mvec4_xwz,4,0,3,2);		GEN_SWIZZLE_DEF_3_(mvec4_xww,4,0,3,3);
GEN_SWIZZLE_DEF_3_(mvec4_yxx,4,1,0,0);		GEN_SWIZZLE_DEF_3_(mvec4_yxy,4,1,0,1);		GEN_SWIZZLE_DEF_3C(mvec4_yxz,4,1,0,2);		GEN_SWIZZLE_DEF_3C(mvec4_yxw,4,1,0,3);
GEN_SWIZZLE_DEF_3_(mvec4_yyx,4,1,1,0);		GEN_SWIZZLE_DEF_3_(mvec4_yyy,4,1,1,1);		GEN_SWIZZLE_DEF_3_(mvec4_yyz,4,1,1,2);		GEN_SWIZZLE_DEF_3_(mvec4_yyw,4,1,1,3);
GEN_SWIZZLE_DEF_3C(mvec4_yzx,4,1,2,0);		GEN_SWIZZLE_DEF_3_(mvec4_yzy,4,1,2,1);		GEN_SWIZZLE_DEF_3_(mvec4_yzz,4,1,2,2);		GEN_SWIZZLE_DEF_3C(mvec4_yzw,4,1,2,3);
GEN_SWIZZLE_DEF_3C(mvec4_ywx,4,1,3,0);		GEN_SWIZZLE_DEF_3_(mvec4_ywy,4,1,3,1);		GEN_SWIZZLE_DEF_3C(mvec4_ywz,4,1,3,2);		GEN_SWIZZLE_DEF_3_(mvec4_yww,4,1,3,3);
GEN_SWIZZLE_DEF_3_(mvec4_zxx,4,2,0,0);		GEN_SWIZZLE_DEF_3C(mvec4_zxy,4,2,0,1);		GEN_SWIZZLE_DEF_3_(mvec4_zxz,4,2,0,2);		GEN_SWIZZLE_DEF_3C(mvec4_zxw,4,2,0,3);
GEN_SWIZZLE_DEF_3C(mvec4_zyx,4,2,1,0);		GEN_SWIZZLE_DEF_3_(mvec4_zyy,4,2,1,1);		GEN_SWIZZLE_DEF_3_(mvec4_zyz,4,2,1,2);		GEN_SWIZZLE_DEF_3C(mvec4_zyw,4,2,1,3);
GEN_SWIZZLE_DEF_3_(mvec4_zzx,4,2,2,0);		GEN_SWIZZLE_DEF_3_(mvec4_zzy,4,2,2,1);		GEN_SWIZZLE_DEF_3_(mvec4_zzz,4,2,2,2);		GEN_SWIZZLE_DEF_3_(mvec4_zzw,4,2,2,3);
GEN_SWIZZLE_DEF_3C(mvec4_zwx,4,2,3,0);		GEN_SWIZZLE_DEF_3C(mvec4_zwy,4,2,3,1);		GEN_SWIZZLE_DEF_3_(mvec4_zwz,4,2,3,2);		GEN_SWIZZLE_DEF_3_(mvec4_zww,4,2,3,3);
GEN_SWIZZLE_DEF_3_(mvec4_wxx,4,3,0,0);		GEN_SWIZZLE_DEF_3C(mvec4_wxy,4,3,0,1);		GEN_SWIZZLE_DEF_3C(mvec4_wxz,4,3,0,2);		GEN_SWIZZLE_DEF_3_(mvec4_wxw,4,3,0,3);
GEN_SWIZZLE_DEF_3C(mvec4_wyx,4,3,1,0);		GEN_SWIZZLE_DEF_3_(mvec4_wyy,4,3,1,1);		GEN_SWIZZLE_DEF_3C(mvec4_wyz,4,3,1,2);		GEN_SWIZZLE_DEF_3_(mvec4_wyw,4,3,1,3);
GEN_SWIZZLE_DEF_3C(mvec4_wzx,4,3,2,0);		GEN_SWIZZLE_DEF_3C(mvec4_wzy,4,3,2,1);		GEN_SWIZZLE_DEF_3_(mvec4_wzz,4,3,2,2);		GEN_SWIZZLE_DEF_3_(mvec4_wzw,4,3,2,3);
GEN_SWIZZLE_DEF_3_(mvec4_wwx,4,3,3,0);		GEN_SWIZZLE_DEF_3_(mvec4_wwy,4,3,3,1);		GEN_SWIZZLE_DEF_3_(mvec4_wwz,4,3,3,2);		GEN_SWIZZLE_DEF_3_(mvec4_www,4,3,3,3);



GEN_SWIZZLE_DEF_4_(mvec2_xxxx,2,0,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec2_xxxy,2,0,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec2_xxyx,2,0,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec2_xxyy,2,0,0,1,1);
GEN_SWIZZLE_DEF_4_(mvec2_xyxx,2,0,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec2_xyxy,2,0,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec2_xyyx,2,0,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec2_xyyy,2,0,1,1,1);
GEN_SWIZZLE_DEF_4_(mvec2_yxxx,2,1,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec2_yxxy,2,1,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec2_yxyx,2,1,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec2_yxyy,2,1,0,1,1);
GEN_SWIZZLE_DEF_4_(mvec2_yyxx,2,1,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec2_yyxy,2,1,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec2_yyyx,2,1,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec2_yyyy,2,1,1,1,1);

GEN_SWIZZLE_DEF_4_(mvec3_xxxx,3,0,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_xxxy,3,0,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_xxxz,3,0,0,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_xxyx,3,0,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_xxyy,3,0,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_xxyz,3,0,0,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_xxzx,3,0,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_xxzy,3,0,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_xxzz,3,0,0,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_xyxx,3,0,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_xyxy,3,0,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_xyxz,3,0,1,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_xyyx,3,0,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_xyyy,3,0,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_xyyz,3,0,1,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_xyzx,3,0,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_xyzy,3,0,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_xyzz,3,0,1,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_xzxx,3,0,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_xzxy,3,0,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_xzxz,3,0,2,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_xzyx,3,0,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_xzyy,3,0,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_xzyz,3,0,2,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_xzzx,3,0,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_xzzy,3,0,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_xzzz,3,0,2,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_yxxx,3,1,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_yxxy,3,1,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_yxxz,3,1,0,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_yxyx,3,1,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_yxyy,3,1,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_yxyz,3,1,0,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_yxzx,3,1,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_yxzy,3,1,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_yxzz,3,1,0,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_yyxx,3,1,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_yyxy,3,1,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_yyxz,3,1,1,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_yyyx,3,1,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_yyyy,3,1,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_yyyz,3,1,1,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_yyzx,3,1,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_yyzy,3,1,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_yyzz,3,1,1,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_yzxx,3,1,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_yzxy,3,1,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_yzxz,3,1,2,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_yzyx,3,1,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_yzyy,3,1,2,1,1)	GEN_SWIZZLE_DEF_4_(mvec3_yzyz,3,1,2,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_yzzx,3,1,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_yzzy,3,1,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_yzzz,3,1,2,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_zxxx,3,2,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_zxxy,3,2,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_zxxz,3,2,0,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_zxyx,3,2,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_zxyy,3,2,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_zxyz,3,2,0,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_zxzx,3,2,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_zxzy,3,2,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_zxzz,3,2,0,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_zyxx,3,2,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_zyxy,3,2,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_zyxz,3,2,1,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_zyyx,3,2,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_zyyy,3,2,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_zyyz,3,2,1,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_zyzx,3,2,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_zyzy,3,2,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_zyzz,3,2,1,2,2);
GEN_SWIZZLE_DEF_4_(mvec3_zzxx,3,2,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec3_zzxy,3,2,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec3_zzxz,3,2,2,0,2);
GEN_SWIZZLE_DEF_4_(mvec3_zzyx,3,2,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec3_zzyy,3,2,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec3_zzyz,3,2,2,1,2);
GEN_SWIZZLE_DEF_4_(mvec3_zzzx,3,2,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec3_zzzy,3,2,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec3_zzzz,3,2,2,2,2);


GEN_SWIZZLE_DEF_4_(mvec4_xxxx,4,0,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_xxxy,4,0,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_xxxz,4,0,0,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_xxxw,4,0,0,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_xxyx,4,0,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_xxyy,4,0,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_xxyz,4,0,0,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_xxyw,4,0,0,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_xxzx,4,0,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_xxzy,4,0,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_xxzz,4,0,0,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_xxzw,4,0,0,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_xxwx,4,0,0,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_xxwy,4,0,0,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_xxwz,4,0,0,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_xxww,4,0,0,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_xyxx,4,0,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_xyxy,4,0,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_xyxz,4,0,1,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_xyxw,4,0,1,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_xyyx,4,0,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_xyyy,4,0,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_xyyz,4,0,1,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_xyyw,4,0,1,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_xyzx,4,0,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_xyzy,4,0,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_xyzz,4,0,1,2,2);	GEN_SWIZZLE_DEF_4C(mvec4_xyzw,4,0,1,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_xywx,4,0,1,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_xywy,4,0,1,3,1);	GEN_SWIZZLE_DEF_4C(mvec4_xywz,4,0,1,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_xyww,4,0,1,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_xzxx,4,0,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_xzxy,4,0,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_xzxz,4,0,2,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_xzxw,4,0,2,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_xzyx,4,0,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_xzyy,4,0,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_xzyz,4,0,2,1,2);	GEN_SWIZZLE_DEF_4C(mvec4_xzyw,4,0,2,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_xzzx,4,0,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_xzzy,4,0,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_xzzz,4,0,2,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_xzzw,4,0,2,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_xzwx,4,0,2,3,0);	GEN_SWIZZLE_DEF_4C(mvec4_xzwy,4,0,2,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_xzwz,4,0,2,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_xzww,4,0,2,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_xwxx,4,0,3,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_xwxy,4,0,3,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_xwxz,4,0,3,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_xwxw,4,0,3,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_xwyx,4,0,3,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_xwyy,4,0,3,1,1);	GEN_SWIZZLE_DEF_4C(mvec4_xwyz,4,0,3,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_xwyw,4,0,3,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_xwzx,4,0,3,2,0);	GEN_SWIZZLE_DEF_4C(mvec4_xwzy,4,0,3,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_xwzz,4,0,3,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_xwzw,4,0,3,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_xwwx,4,0,3,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_xwwy,4,0,3,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_xwwz,4,0,3,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_xwww,4,0,3,3,3);

GEN_SWIZZLE_DEF_4_(mvec4_yxxx,4,1,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_yxxy,4,1,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_yxxz,4,1,0,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_yxxw,4,1,0,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_yxyx,4,1,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_yxyy,4,1,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_yxyz,4,1,0,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_yxyw,4,1,0,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_yxzx,4,1,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_yxzy,4,1,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_yxzz,4,1,0,2,2);	GEN_SWIZZLE_DEF_4C(mvec4_yxzw,4,1,0,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_yxwx,4,1,0,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_yxwy,4,1,0,3,1);	GEN_SWIZZLE_DEF_4C(mvec4_yxwz,4,1,0,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_yxww,4,1,0,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_yyxx,4,1,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_yyxy,4,1,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_yyxz,4,1,1,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_yyxw,4,1,1,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_yyyx,4,1,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_yyyy,4,1,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_yyyz,4,1,1,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_yyyw,4,1,1,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_yyzx,4,1,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_yyzy,4,1,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_yyzz,4,1,1,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_yyzw,4,1,1,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_yywx,4,1,1,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_yywy,4,1,1,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_yywz,4,1,1,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_yyww,4,1,1,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_yzxx,4,1,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_yzxy,4,1,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_yzxz,4,1,2,0,2);	GEN_SWIZZLE_DEF_4C(mvec4_yzxw,4,1,2,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_yzyx,4,1,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_yzyy,4,1,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_yzyz,4,1,2,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_yzyw,4,1,2,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_yzzx,4,1,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_yzzy,4,1,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_yzzz,4,1,2,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_yzzw,4,1,2,2,3);
GEN_SWIZZLE_DEF_4C(mvec4_yzwx,4,1,2,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_yzwy,4,1,2,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_yzwz,4,1,2,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_yzww,4,1,2,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_ywxx,4,1,3,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_ywxy,4,1,3,0,1);	GEN_SWIZZLE_DEF_4C(mvec4_ywxz,4,1,3,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_ywxw,4,1,3,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_ywyx,4,1,3,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_ywyy,4,1,3,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_ywyz,4,1,3,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_ywyw,4,1,3,1,3);
GEN_SWIZZLE_DEF_4C(mvec4_ywzx,4,1,3,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_ywzy,4,1,3,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_ywzz,4,1,3,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_ywzw,4,1,3,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_ywwx,4,1,3,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_ywwy,4,1,3,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_ywwz,4,1,3,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_ywww,4,1,3,3,3);

GEN_SWIZZLE_DEF_4_(mvec4_zxxx,4,2,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_zxxy,4,2,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_zxxz,4,2,0,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_zxxw,4,2,0,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_zxyx,4,2,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_zxyy,4,2,0,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_zxyz,4,2,0,1,2);	GEN_SWIZZLE_DEF_4C(mvec4_zxyw,4,2,0,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_zxzx,4,2,0,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_zxzy,4,2,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_zxzz,4,2,0,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_zxzw,4,2,0,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_zxwx,4,2,0,3,0);	GEN_SWIZZLE_DEF_4C(mvec4_zxwy,4,2,0,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_zxwz,4,2,0,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_zxww,4,2,0,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_zyxx,4,2,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_zyxy,4,2,1,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_zyxz,4,2,1,0,2);	GEN_SWIZZLE_DEF_4C(mvec4_zyxw,4,2,1,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_zyyx,4,2,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_zyyy,4,2,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_zyyz,4,2,1,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_zyyw,4,2,1,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_zyzx,4,2,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_zyzy,4,2,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_zyzz,4,2,1,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_zyzw,4,2,1,2,3);
GEN_SWIZZLE_DEF_4C(mvec4_zywx,4,2,1,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_zywy,4,2,1,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_zywz,4,2,1,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_zyww,4,2,1,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_zzxx,4,2,2,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_zzxy,4,2,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_zzxz,4,2,2,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_zzxw,4,2,2,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_zzyx,4,2,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_zzyy,4,2,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_zzyz,4,2,2,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_zzyw,4,2,2,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_zzzx,4,2,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_zzzy,4,2,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_zzzz,4,2,2,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_zzzw,4,2,2,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_zzwx,4,2,2,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_zzwy,4,2,2,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_zzwz,4,2,2,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_zzww,4,2,2,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_zwxx,4,2,3,0,0);	GEN_SWIZZLE_DEF_4C(mvec4_zwxy,4,2,3,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_zwxz,4,2,3,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_zwxw,4,2,3,0,3);
GEN_SWIZZLE_DEF_4C(mvec4_zwyx,4,2,3,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_zwyy,4,2,3,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_zwyz,4,2,3,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_zwyw,4,2,3,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_zwzx,4,2,3,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_zwzy,4,2,3,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_zwzz,4,2,3,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_zwzw,4,2,3,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_zwwx,4,2,3,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_zwwy,4,2,3,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_zwwz,4,2,3,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_zwww,4,2,3,3,3);

GEN_SWIZZLE_DEF_4_(mvec4_wxxx,4,3,0,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_wxxy,4,3,0,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_wxxz,4,3,0,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_wxxw,4,3,0,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_wxyx,4,3,0,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_wxyy,4,3,0,1,1);	GEN_SWIZZLE_DEF_4C(mvec4_wxyz,4,3,0,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_wxyw,4,3,0,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_wxzx,4,3,0,2,0);	GEN_SWIZZLE_DEF_4C(mvec4_wxzy,4,3,0,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_wxzz,4,3,0,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_wxzw,4,3,0,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_wxwx,4,3,0,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_wxwy,4,3,0,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_wxwz,4,3,0,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_wxww,4,3,0,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_wyxx,4,3,1,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_wyxy,4,3,1,0,1);	GEN_SWIZZLE_DEF_4C(mvec4_wyxz,4,3,1,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_wyxw,4,3,1,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_wyyx,4,3,1,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_wyyy,4,3,1,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_wyyz,4,3,1,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_wyyw,4,3,1,1,3);
GEN_SWIZZLE_DEF_4C(mvec4_wyzx,4,3,1,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_wyzy,4,3,1,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_wyzz,4,3,1,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_wyzw,4,3,1,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_wywx,4,3,1,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_wywy,4,3,1,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_wywz,4,3,1,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_wyww,4,3,1,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_wzxx,4,3,2,0,0);	GEN_SWIZZLE_DEF_4C(mvec4_wzxy,4,3,2,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_wzxz,4,3,2,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_wzxw,4,3,2,0,3);
GEN_SWIZZLE_DEF_4C(mvec4_wzyx,4,3,2,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_wzyy,4,3,2,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_wzyz,4,3,2,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_wzyw,4,3,2,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_wzzx,4,3,2,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_wzzy,4,3,2,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_wzzz,4,3,2,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_wzzw,4,3,2,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_wzwx,4,3,2,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_wzwy,4,3,2,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_wzwz,4,3,2,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_wzww,4,3,2,3,3);
GEN_SWIZZLE_DEF_4_(mvec4_wwxx,4,3,3,0,0);	GEN_SWIZZLE_DEF_4_(mvec4_wwxy,4,3,3,0,1);	GEN_SWIZZLE_DEF_4_(mvec4_wwxz,4,3,3,0,2);	GEN_SWIZZLE_DEF_4_(mvec4_wwxw,4,3,3,0,3);
GEN_SWIZZLE_DEF_4_(mvec4_wwyx,4,3,3,1,0);	GEN_SWIZZLE_DEF_4_(mvec4_wwyy,4,3,3,1,1);	GEN_SWIZZLE_DEF_4_(mvec4_wwyz,4,3,3,1,2);	GEN_SWIZZLE_DEF_4_(mvec4_wwyw,4,3,3,1,3);
GEN_SWIZZLE_DEF_4_(mvec4_wwzx,4,3,3,2,0);	GEN_SWIZZLE_DEF_4_(mvec4_wwzy,4,3,3,2,1);	GEN_SWIZZLE_DEF_4_(mvec4_wwzz,4,3,3,2,2);	GEN_SWIZZLE_DEF_4_(mvec4_wwzw,4,3,3,2,3);
GEN_SWIZZLE_DEF_4_(mvec4_wwwx,4,3,3,3,0);	GEN_SWIZZLE_DEF_4_(mvec4_wwwy,4,3,3,3,1);	GEN_SWIZZLE_DEF_4_(mvec4_wwwz,4,3,3,3,2);	GEN_SWIZZLE_DEF_4_(mvec4_wwww,4,3,3,3,3);


template<typename T> struct mvec2_t {
	union {
		struct { T x, y; };
		struct { T r, g; };
		struct { T s, t; };
		struct { T v[2]; };
		mvec2_xx<T>   xx, rr, ss;
		mvec2_xy<T>   xy, rg, st;
		mvec2_yx<T>   yx, gr, ts;
		mvec2_yy<T>   yy, gg, tt;
		
		mvec2_xxx<T>  xxx, rrr, sss;
		mvec2_xxy<T>  xxy, rrg, sst;
		mvec2_xyx<T>  xyx, rgr, sts;
		mvec2_xyy<T>  xyy, rgg, stt;
		mvec2_yxx<T>  yxx, grr, tss;
		mvec2_yxy<T>  yxy, grg, tst;
		mvec2_yyx<T>  yyx, ggr, tts;
		mvec2_yyy<T>  yyy, ggg, ttt;
		
		mvec2_xxxx<T> xxxx, rrrr, ssss;
		mvec2_xxxy<T> xxxy, rrrg, ssst;
		mvec2_xxyx<T> xxyx, rrgr, ssts;
		mvec2_xxyy<T> xxyy, rrgg, sstt;
		mvec2_xyxx<T> xyxx, rgrr, stss;
		mvec2_xyxy<T> xyxy, rgrg, stst;
		mvec2_xyyx<T> xyyx, rggr, stts;
		mvec2_xyyy<T> xyyy, rggg, sttt;
		mvec2_yxxx<T> yxxx, grrr, tsss;
		mvec2_yxxy<T> yxxy, grrg, tsst;
		mvec2_yxyx<T> yxyx, grgr, tsts;
		mvec2_yxyy<T> yxyy, grgg, tstt;
		mvec2_yyxx<T> yyxx, ggrr, ttss;
		mvec2_yyxy<T> yyxy, ggrg, ttst;
		mvec2_yyyx<T> yyyx, gggr, ttts;
		mvec2_yyyy<T> yyyy, gggg, tttt;
	};
	using TYPE = mvec2_t<T>;
	
	mvec2_t(): x(0),y(0) {}
	template<typename T1>
	mvec2_t(const T1& v);
	
	template<typename T1,typename T2,typename=std::enable_if_t<!is_vector_v<T1>&&!is_vector_v<T2>>>
	mvec2_t(T1 _x, T2 _y): x(T(_x)), y(T(_y)) {}
	
	T& operator [] (int n) { return v[n]; }
	const T& operator [] (int n) const { return v[n]; }
	size_t length() const { return 2; }

	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==2 && is_same_element_v<TYPE,F>)>>
	TYPE& operator+=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x+=f[0]; y+=f[1]; return *this; }
		else							{ x+=f; y+=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==2 && is_same_element_v<TYPE,F>)>>
	TYPE& operator-=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x-=f[0]; y-=f[1]; return *this; }
		else							{ x-=f; y-=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==2 && is_same_element_v<TYPE,F>)>>
	TYPE& operator*=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x*=f[0]; y*=f[1]; return *this; }
		else							{ x*=f; y*=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==2 && is_same_element_v<TYPE,F>)>>
	TYPE& operator/=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x/=f[0]; y/=f[1]; return *this; }
		else							{ x/=f; y/=f; return *this; }
	}
	
	TYPE& operator++() { x+=1; y+=1; return *this; }
	TYPE& operator--() { x-=1; y-=1; return *this; }
	TYPE operator++(int) { TYPE a=*this; operator++(); return a; }
	TYPE operator--(int) { TYPE a=*this; operator--(); return a; }
};

template<typename T> struct mvec3_t {
	union {
		struct { T x,y,z; };
		struct { T r,g,b; };
		struct { T s,t,p; };
		struct { T v[3]; };
		
		mvec3_xx<T> xx, rr, ss;
		mvec3_xy<T> xy, rg, st;
		mvec3_xz<T> xz, rb, sp;
		mvec3_yx<T> yx, gr, ts;
		mvec3_yy<T> yy, gg, tt;
		mvec3_yz<T> yz, gb, tp;
		mvec3_zx<T> zx, br, ps;
		mvec3_zy<T> zy, bg, pt;
		mvec3_zz<T> zz, bb, pp;
		
		mvec3_xxx<T> xxx, rrr, sss;
		mvec3_xxy<T> xxy, rrg, sst;
		mvec3_xxz<T> xxz, rrb, ssp;
		mvec3_xyx<T> xyx, rgr, sts;
		mvec3_xyy<T> xyy, rgg, stt;
		mvec3_xyz<T> xyz, rgb, stp;
		mvec3_xzx<T> xzx, rbr, sps;
		mvec3_xzy<T> xzy, rbg, spt;
		mvec3_xzz<T> xzz, rbb, spp;
		mvec3_yxx<T> yxx, grr, tss;
		mvec3_yxy<T> yxy, grg, tst;
		mvec3_yxz<T> yxz, grb, tsp;
		mvec3_yyx<T> yyx, ggr, tts;
		mvec3_yyy<T> yyy, ggg, ttt;
		mvec3_yyz<T> yyz, ggb, ttp;
		mvec3_yzx<T> yzx, gbr, tps;
		mvec3_yzy<T> yzy, gbg, tpt;
		mvec3_yzz<T> yzz, gbb, tpp;
		mvec3_zxx<T> zxx, brr, pss;
		mvec3_zxy<T> zxy, brg, pst;
		mvec3_zxz<T> zxz, brb, psp;
		mvec3_zyx<T> zyx, bgr, pts;
		mvec3_zyy<T> zyy, bgg, ptt;
		mvec3_zyz<T> zyz, bgb, ptp;
		mvec3_zzx<T> zzx, bbr, pps;
		mvec3_zzy<T> zzy, bbg, ppt;
		mvec3_zzz<T> zzz, bbb, ppp;
		
		mvec3_xxxx<T> xxxx, rrrr, ssss;
		mvec3_xxxy<T> xxxy, rrrg, ssst;
		mvec3_xxxz<T> xxxz, rrrb, sssp;
		mvec3_xxyx<T> xxyx, rrgr, ssts;
		mvec3_xxyy<T> xxyy, rrgg, sstt;
		mvec3_xxyz<T> xxyz, rrgb, sstp;
		mvec3_xxzx<T> xxzx, rrbr, ssps;
		mvec3_xxzy<T> xxzy, rrbg, sspt;
		mvec3_xxzz<T> xxzz, rrbb, sspp;
		mvec3_xyxx<T> xyxx, rgrr, stss;
		mvec3_xyxy<T> xyxy, rgrg, stst;
		mvec3_xyxz<T> xyxz, rgrb, stsp;
		mvec3_xyyx<T> xyyx, rggr, stts;
		mvec3_xyyy<T> xyyy, rggg, sttt;
		mvec3_xyyz<T> xyyz, rggb, sttp;
		mvec3_xyzx<T> xyzx, rgbr, stps;
		mvec3_xyzy<T> xyzy, rgbg, stpt;
		mvec3_xyzz<T> xyzz, rgbb, stpp;
		mvec3_xzxx<T> xzxx, rbrr, spss;
		mvec3_xzxy<T> xzxy, rbrg, spst;
		mvec3_xzxz<T> xzxz, rbrb, spsp;
		mvec3_xzyx<T> xzyx, rbgr, spts;
		mvec3_xzyy<T> xzyy, rbgg, sptt;
		mvec3_xzyz<T> xzyz, rbgb, sptp;
		mvec3_xzzx<T> xzzx, rbbr, spps;
		mvec3_xzzy<T> xzzy, rbbg, sppt;
		mvec3_xzzz<T> xzzz, rbbb, sppp;
		mvec3_yxxx<T> yxxx, grrr, tsss;
		mvec3_yxxy<T> yxxy, grrg, tsst;
		mvec3_yxxz<T> yxxz, grrb, tssp;
		mvec3_yxyx<T> yxyx, grgr, tsts;
		mvec3_yxyy<T> yxyy, grgg, tstt;
		mvec3_yxyz<T> yxyz, grgb, tstp;
		mvec3_yxzx<T> yxzx, grbr, tsps;
		mvec3_yxzy<T> yxzy, grbg, tspt;
		mvec3_yxzz<T> yxzz, grbb, tspp;
		mvec3_yyxx<T> yyxx, ggrr, ttss;
		mvec3_yyxy<T> yyxy, ggrg, ttst;
		mvec3_yyxz<T> yyxz, ggrb, ttsp;
		mvec3_yyyx<T> yyyx, gggr, ttts;
		mvec3_yyyy<T> yyyy, gggg, tttt;
		mvec3_yyyz<T> yyyz, gggb, tttp;
		mvec3_yyzx<T> yyzx, ggbr, ttps;
		mvec3_yyzy<T> yyzy, ggbg, ttpt;
		mvec3_yyzz<T> yyzz, ggbb, ttpp;
		mvec3_yzxx<T> yzxx, gbrr, tpss;
		mvec3_yzxy<T> yzxy, gbrg, tpst;
		mvec3_yzxz<T> yzxz, gbrb, tpsp;
		mvec3_yzyx<T> yzyx, gbgr, tpts;
		mvec3_yzyy<T> yzyy, gbgg, tptt;
		mvec3_yzyz<T> yzyz, gbgb, tptp;
		mvec3_yzzx<T> yzzx, gbbr, tpps;
		mvec3_yzzy<T> yzzy, gbbg, tppt;
		mvec3_yzzz<T> yzzz, gbbb, tppp;
		mvec3_zxxx<T> zxxx, brrr, psss;
		mvec3_zxxy<T> zxxy, brrg, psst;
		mvec3_zxxz<T> zxxz, brrb, pssp;
		mvec3_zxyx<T> zxyx, brgr, psts;
		mvec3_zxyy<T> zxyy, brgg, pstt;
		mvec3_zxyz<T> zxyz, brgb, pstp;
		mvec3_zxzx<T> zxzx, brbr, psps;
		mvec3_zxzy<T> zxzy, brbg, pspt;
		mvec3_zxzz<T> zxzz, brbb, pspp;
		mvec3_zyxx<T> zyxx, bgrr, ptss;
		mvec3_zyxy<T> zyxy, bgrg, ptst;
		mvec3_zyxz<T> zyxz, bgrb, ptsp;
		mvec3_zyyx<T> zyyx, bggr, ptts;
		mvec3_zyyy<T> zyyy, bggg, pttt;
		mvec3_zyyz<T> zyyz, bggb, pttp;
		mvec3_zyzx<T> zyzx, bgbr, ptps;
		mvec3_zyzy<T> zyzy, bgbg, ptpt;
		mvec3_zyzz<T> zyzz, bgbb, ptpp;
		mvec3_zzxx<T> zzxx, bbrr, ppss;
		mvec3_zzxy<T> zzxy, bbrg, ppst;
		mvec3_zzxz<T> zzxz, bbrb, ppsp;
		mvec3_zzyx<T> zzyx, bbgr, ppts;
		mvec3_zzyy<T> zzyy, bbgg, pptt;
		mvec3_zzyz<T> zzyz, bbgb, pptp;
		mvec3_zzzx<T> zzzx, bbbr, ppps;
		mvec3_zzzy<T> zzzy, bbbg, pppt;
		mvec3_zzzz<T> zzzz, bbbb, pppp;
	};
	
	using TYPE = mvec3_t<T>;
		
	mvec3_t(): x(0),y(0),z(0) {}
	template<typename T1,typename=std::enable_if_t<!is_vector_v<T1>||vec_length<T1> ==3||vec_length<T1> ==4 >>
	mvec3_t(const T1& a);
	
	template<typename T1,typename T2,typename=std::enable_if_t<vec_length<T1>+vec_length<T2> == 3>>
	mvec3_t(const T1& a, const T2& b);
	
	template<typename T1,typename T2,typename T3,typename=std::enable_if_t<!is_vector_v<T1>&&!is_vector_v<T2>&&!is_vector_v<T3>>>
	mvec3_t(T1 _x, T2 _y, T3 _z): x(T(_x)), y(T(_y)), z(T(_z)) {}


	T& operator [] (int n) { return v[n]; }
	const T& operator [] (int n) const { return v[n]; }
	size_t length() const { return 3; }

	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==3 && is_same_element_v<TYPE,F>)>>
	TYPE& operator+=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x+=f[0]; y+=f[1]; z+=f[2]; return *this; }
		else							{ x+=f; y+=f; z+=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==3 && is_same_element_v<TYPE,F>)>>
	TYPE& operator-=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x-=f[0]; y-=f[1]; z-=f[2]; return *this; }
		else							{ x-=f; y-=f; z-=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==3 && is_same_element_v<TYPE,F>)>>
	TYPE& operator*=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x*=f[0]; y*=f[1]; z*=f[2]; return *this; }
		else							{ x*=f; y*=f; z*=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==3 && is_same_element_v<TYPE,F>)>>
	TYPE& operator/=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x/=f[0]; y/=f[1]; z/=f[2]; return *this; }
		else							{ x/=f; y/=f; z/=f; return *this; }
	}

	TYPE& operator++() { x+=1; y+=1; z+=1; return *this; }
	TYPE& operator--() { x-=1; y-=1; z-=1; return *this; }
	TYPE operator++(int) { TYPE a=*this; operator++(); return a; }
	TYPE operator--(int) { TYPE a=*this; operator--(); return a; }
};

template<typename T> struct mvec4_t {
	union {
		struct { T x,y,z,w; };
		struct { T r,g,b,a; };
		struct { T s,t,p,q; };
		struct { T v[4]; };
		mvec4_xx<T> xx, rr, ss;
		mvec4_xy<T> xy, rg, st;
		mvec4_xz<T> xz, rb, sp;
		mvec4_xw<T> xw, ra, sq;
		mvec4_yx<T> yx, gr, ts;
		mvec4_yy<T> yy, gg, tt;
		mvec4_yz<T> yz, gb, tp;
		mvec4_yw<T> yw, ga, tq;
		mvec4_zx<T> zx, br, ps;
		mvec4_zy<T> zy, bg, pt;
		mvec4_zz<T> zz, bb, pp;
		mvec4_zw<T> zw, ba, pq;
		mvec4_wx<T> wx, ar, qs;
		mvec4_wy<T> wy, ag, qt;
		mvec4_wz<T> wz, ab, qp;
		mvec4_ww<T> ww, aa, qq;
		mvec4_xxx<T> xxx, rrr, sss;
		mvec4_xxy<T> xxy, rrg, sst;
		mvec4_xxz<T> xxz, rrb, ssp;
		mvec4_xxw<T> xxw, rra, ssq;
		mvec4_xyx<T> xyx, rgr, sts;
		mvec4_xyy<T> xyy, rgg, stt;
		mvec4_xyz<T> xyz, rgb, stp;
		mvec4_xyw<T> xyw, rga, stq;
		mvec4_xzx<T> xzx, rbr, sps;
		mvec4_xzy<T> xzy, rbg, spt;
		mvec4_xzz<T> xzz, rbb, spp;
		mvec4_xzw<T> xzw, rba, spq;
		mvec4_xwx<T> xwx, rar, sqs;
		mvec4_xwy<T> xwy, rag, sqt;
		mvec4_xwz<T> xwz, rab, sqp;
		mvec4_xww<T> xww, raa, sqq;
		mvec4_yxx<T> yxx, grr, tss;
		mvec4_yxy<T> yxy, grg, tst;
		mvec4_yxz<T> yxz, grb, tsp;
		mvec4_yxw<T> yxw, gra, tsq;
		mvec4_yyx<T> yyx, ggr, tts;
		mvec4_yyy<T> yyy, ggg, ttt;
		mvec4_yyz<T> yyz, ggb, ttp;
		mvec4_yyw<T> yyw, gga, ttq;
		mvec4_yzx<T> yzx, gbr, tps;
		mvec4_yzy<T> yzy, gbg, tpt;
		mvec4_yzz<T> yzz, gbb, tpp;
		mvec4_yzw<T> yzw, gba, tpq;
		mvec4_ywx<T> ywx, gar, tqs;
		mvec4_ywy<T> ywy, gag, tqt;
		mvec4_ywz<T> ywz, gab, tqp;
		mvec4_yww<T> yww, gaa, tqq;
		mvec4_zxx<T> zxx, brr, pss;
		mvec4_zxy<T> zxy, brg, pst;
		mvec4_zxz<T> zxz, brb, psp;
		mvec4_zxw<T> zxw, bra, psq;
		mvec4_zyx<T> zyx, bgr, pts;
		mvec4_zyy<T> zyy, bgg, ptt;
		mvec4_zyz<T> zyz, bgb, ptp;
		mvec4_zyw<T> zyw, bga, ptq;
		mvec4_zzx<T> zzx, bbr, pps;
		mvec4_zzy<T> zzy, bbg, ppt;
		mvec4_zzz<T> zzz, bbb, ppp;
		mvec4_zzw<T> zzw, bba, ppq;
		mvec4_zwx<T> zwx, bar, pqs;
		mvec4_zwy<T> zwy, bag, pqt;
		mvec4_zwz<T> zwz, bab, pqp;
		mvec4_zww<T> zww, baa, pqq;
		mvec4_wxx<T> wxx, arr, qss;
		mvec4_wxy<T> wxy, arg, qst;
		mvec4_wxz<T> wxz, arb, qsp;
		mvec4_wxw<T> wxw, ara, qsq;
		mvec4_wyx<T> wyx, agr, qts;
		mvec4_wyy<T> wyy, agg, qtt;
		mvec4_wyz<T> wyz, agb, qtp;
		mvec4_wyw<T> wyw, aga, qtq;
		mvec4_wzx<T> wzx, abr, qps;
		mvec4_wzy<T> wzy, abg, qpt;
		mvec4_wzz<T> wzz, abb, qpp;
		mvec4_wzw<T> wzw, aba, qpq;
		mvec4_wwx<T> wwx, aar, qqs;
		mvec4_wwy<T> wwy, aag, qqt;
		mvec4_wwz<T> wwz, aab, qqp;
		mvec4_www<T> www, aaa, qqq;
		
		mvec4_xxxx<T> xxxx, rrrr, ssss;
		mvec4_xxxy<T> xxxy, rrrg, ssst;
		mvec4_xxxz<T> xxxz, rrrb, sssp;
		mvec4_xxxw<T> xxxw, rrra, sssq;
		mvec4_xxyx<T> xxyx, rrgr, ssts;
		mvec4_xxyy<T> xxyy, rrgg, sstt;
		mvec4_xxyz<T> xxyz, rrgb, sstp;
		mvec4_xxyw<T> xxyw, rrga, sstq;
		mvec4_xxzx<T> xxzx, rrbr, ssps;
		mvec4_xxzy<T> xxzy, rrbg, sspt;
		mvec4_xxzz<T> xxzz, rrbb, sspp;
		mvec4_xxzw<T> xxzw, rrba, sspq;
		mvec4_xxwx<T> xxwx, rrar, ssqs;
		mvec4_xxwy<T> xxwy, rrag, ssqt;
		mvec4_xxwz<T> xxwz, rrab, ssqp;
		mvec4_xxww<T> xxww, rraa, ssqq;
		mvec4_xyxx<T> xyxx, rgrr, stss;
		mvec4_xyxy<T> xyxy, rgrg, stst;
		mvec4_xyxz<T> xyxz, rgrb, stsp;
		mvec4_xyxw<T> xyxw, rgra, stsq;
		mvec4_xyyx<T> xyyx, rggr, stts;
		mvec4_xyyy<T> xyyy, rggg, sttt;
		mvec4_xyyz<T> xyyz, rggb, sttp;
		mvec4_xyyw<T> xyyw, rgga, sttq;
		mvec4_xyzx<T> xyzx, rgbr, stps;
		mvec4_xyzy<T> xyzy, rgbg, stpt;
		mvec4_xyzz<T> xyzz, rgbb, stpp;
		mvec4_xyzw<T> xyzw, rgba, stpq;
		mvec4_xywx<T> xywx, rgar, stqs;
		mvec4_xywy<T> xywy, rgag, stqt;
		mvec4_xywz<T> xywz, rgab, stqp;
		mvec4_xyww<T> xyww, rgaa, stqq;
		mvec4_xzxx<T> xzxx, rbrr, spss;
		mvec4_xzxy<T> xzxy, rbrg, spst;
		mvec4_xzxz<T> xzxz, rbrb, spsp;
		mvec4_xzxw<T> xzxw, rbra, spsq;
		mvec4_xzyx<T> xzyx, rbgr, spts;
		mvec4_xzyy<T> xzyy, rbgg, sptt;
		mvec4_xzyz<T> xzyz, rbgb, sptp;
		mvec4_xzyw<T> xzyw, rbga, sptq;
		mvec4_xzzx<T> xzzx, rbbr, spps;
		mvec4_xzzy<T> xzzy, rbbg, sppt;
		mvec4_xzzz<T> xzzz, rbbb, sppp;
		mvec4_xzzw<T> xzzw, rbba, sppq;
		mvec4_xzwx<T> xzwx, rbar, spqs;
		mvec4_xzwy<T> xzwy, rbag, spqt;
		mvec4_xzwz<T> xzwz, rbab, spqp;
		mvec4_xzww<T> xzww, rbaa, spqq;
		mvec4_xwxx<T> xwxx, rarr, sqss;
		mvec4_xwxy<T> xwxy, rarg, sqst;
		mvec4_xwxz<T> xwxz, rarb, sqsp;
		mvec4_xwxw<T> xwxw, rara, sqsq;
		mvec4_xwyx<T> xwyx, ragr, sqts;
		mvec4_xwyy<T> xwyy, ragg, sqtt;
		mvec4_xwyz<T> xwyz, ragb, sqtp;
		mvec4_xwyw<T> xwyw, raga, sqtq;
		mvec4_xwzx<T> xwzx, rabr, sqps;
		mvec4_xwzy<T> xwzy, rabg, sqpt;
		mvec4_xwzz<T> xwzz, rabb, sqpp;
		mvec4_xwzw<T> xwzw, raba, sqpq;
		mvec4_xwwx<T> xwwx, raar, sqqs;
		mvec4_xwwy<T> xwwy, raag, sqqt;
		mvec4_xwwz<T> xwwz, raab, sqqp;
		mvec4_xwww<T> xwww, raaa, sqqq;
		mvec4_yxxx<T> yxxx, grrr, tsss;
		mvec4_yxxy<T> yxxy, grrg, tsst;
		mvec4_yxxz<T> yxxz, grrb, tssp;
		mvec4_yxxw<T> yxxw, grra, tssq;
		mvec4_yxyx<T> yxyx, grgr, tsts;
		mvec4_yxyy<T> yxyy, grgg, tstt;
		mvec4_yxyz<T> yxyz, grgb, tstp;
		mvec4_yxyw<T> yxyw, grga, tstq;
		mvec4_yxzx<T> yxzx, grbr, tsps;
		mvec4_yxzy<T> yxzy, grbg, tspt;
		mvec4_yxzz<T> yxzz, grbb, tspp;
		mvec4_yxzw<T> yxzw, grba, tspq;
		mvec4_yxwx<T> yxwx, grar, tsqs;
		mvec4_yxwy<T> yxwy, grag, tsqt;
		mvec4_yxwz<T> yxwz, grab, tsqp;
		mvec4_yxww<T> yxww, graa, tsqq;
		mvec4_yyxx<T> yyxx, ggrr, ttss;
		mvec4_yyxy<T> yyxy, ggrg, ttst;
		mvec4_yyxz<T> yyxz, ggrb, ttsp;
		mvec4_yyxw<T> yyxw, ggra, ttsq;
		mvec4_yyyx<T> yyyx, gggr, ttts;
		mvec4_yyyy<T> yyyy, gggg, tttt;
		mvec4_yyyz<T> yyyz, gggb, tttp;
		mvec4_yyyw<T> yyyw, ggga, tttq;
		mvec4_yyzx<T> yyzx, ggbr, ttps;
		mvec4_yyzy<T> yyzy, ggbg, ttpt;
		mvec4_yyzz<T> yyzz, ggbb, ttpp;
		mvec4_yyzw<T> yyzw, ggba, ttpq;
		mvec4_yywx<T> yywx, ggar, ttqs;
		mvec4_yywy<T> yywy, ggag, ttqt;
		mvec4_yywz<T> yywz, ggab, ttqp;
		mvec4_yyww<T> yyww, ggaa, ttqq;
		mvec4_yzxx<T> yzxx, gbrr, tpss;
		mvec4_yzxy<T> yzxy, gbrg, tpst;
		mvec4_yzxz<T> yzxz, gbrb, tpsp;
		mvec4_yzxw<T> yzxw, gbra, tpsq;
		mvec4_yzyx<T> yzyx, gbgr, tpts;
		mvec4_yzyy<T> yzyy, gbgg, tptt;
		mvec4_yzyz<T> yzyz, gbgb, tptp;
		mvec4_yzyw<T> yzyw, gbga, tptq;
		mvec4_yzzx<T> yzzx, gbbr, tpps;
		mvec4_yzzy<T> yzzy, gbbg, tppt;
		mvec4_yzzz<T> yzzz, gbbb, tppp;
		mvec4_yzzw<T> yzzw, gbba, tppq;
		mvec4_yzwx<T> yzwx, gbar, tpqs;
		mvec4_yzwy<T> yzwy, gbag, tpqt;
		mvec4_yzwz<T> yzwz, gbab, tpqp;
		mvec4_yzww<T> yzww, gbaa, tpqq;
		mvec4_ywxx<T> ywxx, garr, tqss;
		mvec4_ywxy<T> ywxy, garg, tqst;
		mvec4_ywxz<T> ywxz, garb, tqsp;
		mvec4_ywxw<T> ywxw, gara, tqsq;
		mvec4_ywyx<T> ywyx, gagr, tqts;
		mvec4_ywyy<T> ywyy, gagg, tqtt;
		mvec4_ywyz<T> ywyz, gagb, tqtp;
		mvec4_ywyw<T> ywyw, gaga, tqtq;
		mvec4_ywzx<T> ywzx, gabr, tqps;
		mvec4_ywzy<T> ywzy, gabg, tqpt;
		mvec4_ywzz<T> ywzz, gabb, tqpp;
		mvec4_ywzw<T> ywzw, gaba, tqpq;
		mvec4_ywwx<T> ywwx, gaar, tqqs;
		mvec4_ywwy<T> ywwy, gaag, tqqt;
		mvec4_ywwz<T> ywwz, gaab, tqqp;
		mvec4_ywww<T> ywww, gaaa, tqqq;
		mvec4_zxxx<T> zxxx, brrr, psss;
		mvec4_zxxy<T> zxxy, brrg, psst;
		mvec4_zxxz<T> zxxz, brrb, pssp;
		mvec4_zxxw<T> zxxw, brra, pssq;
		mvec4_zxyx<T> zxyx, brgr, psts;
		mvec4_zxyy<T> zxyy, brgg, pstt;
		mvec4_zxyz<T> zxyz, brgb, pstp;
		mvec4_zxyw<T> zxyw, brga, pstq;
		mvec4_zxzx<T> zxzx, brbr, psps;
		mvec4_zxzy<T> zxzy, brbg, pspt;
		mvec4_zxzz<T> zxzz, brbb, pspp;
		mvec4_zxzw<T> zxzw, brba, pspq;
		mvec4_zxwx<T> zxwx, brar, psqs;
		mvec4_zxwy<T> zxwy, brag, psqt;
		mvec4_zxwz<T> zxwz, brab, psqp;
		mvec4_zxww<T> zxww, braa, psqq;
		mvec4_zyxx<T> zyxx, bgrr, ptss;
		mvec4_zyxy<T> zyxy, bgrg, ptst;
		mvec4_zyxz<T> zyxz, bgrb, ptsp;
		mvec4_zyxw<T> zyxw, bgra, ptsq;
		mvec4_zyyx<T> zyyx, bggr, ptts;
		mvec4_zyyy<T> zyyy, bggg, pttt;
		mvec4_zyyz<T> zyyz, bggb, pttp;
		mvec4_zyyw<T> zyyw, bgga, pttq;
		mvec4_zyzx<T> zyzx, bgbr, ptps;
		mvec4_zyzy<T> zyzy, bgbg, ptpt;
		mvec4_zyzz<T> zyzz, bgbb, ptpp;
		mvec4_zyzw<T> zyzw, bgba, ptpq;
		mvec4_zywx<T> zywx, bgar, ptqs;
		mvec4_zywy<T> zywy, bgag, ptqt;
		mvec4_zywz<T> zywz, bgab, ptqp;
		mvec4_zyww<T> zyww, bgaa, ptqq;
		mvec4_zzxx<T> zzxx, bbrr, ppss;
		mvec4_zzxy<T> zzxy, bbrg, ppst;
		mvec4_zzxz<T> zzxz, bbrb, ppsp;
		mvec4_zzxw<T> zzxw, bbra, ppsq;
		mvec4_zzyx<T> zzyx, bbgr, ppts;
		mvec4_zzyy<T> zzyy, bbgg, pptt;
		mvec4_zzyz<T> zzyz, bbgb, pptp;
		mvec4_zzyw<T> zzyw, bbga, pptq;
		mvec4_zzzx<T> zzzx, bbbr, ppps;
		mvec4_zzzy<T> zzzy, bbbg, pppt;
		mvec4_zzzz<T> zzzz, bbbb, pppp;
		mvec4_zzzw<T> zzzw, bbba, pppq;
		mvec4_zzwx<T> zzwx, bbar, ppqs;
		mvec4_zzwy<T> zzwy, bbag, ppqt;
		mvec4_zzwz<T> zzwz, bbab, ppqp;
		mvec4_zzww<T> zzww, bbaa, ppqq;
		mvec4_zwxx<T> zwxx, barr, pqss;
		mvec4_zwxy<T> zwxy, barg, pqst;
		mvec4_zwxz<T> zwxz, barb, pqsp;
		mvec4_zwxw<T> zwxw, bara, pqsq;
		mvec4_zwyx<T> zwyx, bagr, pqts;
		mvec4_zwyy<T> zwyy, bagg, pqtt;
		mvec4_zwyz<T> zwyz, bagb, pqtp;
		mvec4_zwyw<T> zwyw, baga, pqtq;
		mvec4_zwzx<T> zwzx, babr, pqps;
		mvec4_zwzy<T> zwzy, babg, pqpt;
		mvec4_zwzz<T> zwzz, babb, pqpp;
		mvec4_zwzw<T> zwzw, baba, pqpq;
		mvec4_zwwx<T> zwwx, baar, pqqs;
		mvec4_zwwy<T> zwwy, baag, pqqt;
		mvec4_zwwz<T> zwwz, baab, pqqp;
		mvec4_zwww<T> zwww, baaa, pqqq;
		mvec4_wxxx<T> wxxx, arrr, qsss;
		mvec4_wxxy<T> wxxy, arrg, qsst;
		mvec4_wxxz<T> wxxz, arrb, qssp;
		mvec4_wxxw<T> wxxw, arra, qssq;
		mvec4_wxyx<T> wxyx, argr, qsts;
		mvec4_wxyy<T> wxyy, argg, qstt;
		mvec4_wxyz<T> wxyz, argb, qstp;
		mvec4_wxyw<T> wxyw, arga, qstq;
		mvec4_wxzx<T> wxzx, arbr, qsps;
		mvec4_wxzy<T> wxzy, arbg, qspt;
		mvec4_wxzz<T> wxzz, arbb, qspp;
		mvec4_wxzw<T> wxzw, arba, qspq;
		mvec4_wxwx<T> wxwx, arar, qsqs;
		mvec4_wxwy<T> wxwy, arag, qsqt;
		mvec4_wxwz<T> wxwz, arab, qsqp;
		mvec4_wxww<T> wxww, araa, qsqq;
		mvec4_wyxx<T> wyxx, agrr, qtss;
		mvec4_wyxy<T> wyxy, agrg, qtst;
		mvec4_wyxz<T> wyxz, agrb, qtsp;
		mvec4_wyxw<T> wyxw, agra, qtsq;
		mvec4_wyyx<T> wyyx, aggr, qtts;
		mvec4_wyyy<T> wyyy, aggg, qttt;
		mvec4_wyyz<T> wyyz, aggb, qttp;
		mvec4_wyyw<T> wyyw, agga, qttq;
		mvec4_wyzx<T> wyzx, agbr, qtps;
		mvec4_wyzy<T> wyzy, agbg, qtpt;
		mvec4_wyzz<T> wyzz, agbb, qtpp;
		mvec4_wyzw<T> wyzw, agba, qtpq;
		mvec4_wywx<T> wywx, agar, qtqs;
		mvec4_wywy<T> wywy, agag, qtqt;
		mvec4_wywz<T> wywz, agab, qtqp;
		mvec4_wyww<T> wyww, agaa, qtqq;
		mvec4_wzxx<T> wzxx, abrr, qpss;
		mvec4_wzxy<T> wzxy, abrg, qpst;
		mvec4_wzxz<T> wzxz, abrb, qpsp;
		mvec4_wzxw<T> wzxw, abra, qpsq;
		mvec4_wzyx<T> wzyx, abgr, qpts;
		mvec4_wzyy<T> wzyy, abgg, qptt;
		mvec4_wzyz<T> wzyz, abgb, qptp;
		mvec4_wzyw<T> wzyw, abga, qptq;
		mvec4_wzzx<T> wzzx, abbr, qpps;
		mvec4_wzzy<T> wzzy, abbg, qppt;
		mvec4_wzzz<T> wzzz, abbb, qppp;
		mvec4_wzzw<T> wzzw, abba, qppq;
		mvec4_wzwx<T> wzwx, abar, qpqs;
		mvec4_wzwy<T> wzwy, abag, qpqt;
		mvec4_wzwz<T> wzwz, abab, qpqp;
		mvec4_wzww<T> wzww, abaa, qpqq;
		mvec4_wwxx<T> wwxx, aarr, qqss;
		mvec4_wwxy<T> wwxy, aarg, qqst;
		mvec4_wwxz<T> wwxz, aarb, qqsp;
		mvec4_wwxw<T> wwxw, aara, qqsq;
		mvec4_wwyx<T> wwyx, aagr, qqts;
		mvec4_wwyy<T> wwyy, aagg, qqtt;
		mvec4_wwyz<T> wwyz, aagb, qqtp;
		mvec4_wwyw<T> wwyw, aaga, qqtq;
		mvec4_wwzx<T> wwzx, aabr, qqps;
		mvec4_wwzy<T> wwzy, aabg, qqpt;
		mvec4_wwzz<T> wwzz, aabb, qqpp;
		mvec4_wwzw<T> wwzw, aaba, qqpq;
		mvec4_wwwx<T> wwwx, aaar, qqqs;
		mvec4_wwwy<T> wwwy, aaag, qqqt;
		mvec4_wwwz<T> wwwz, aaab, qqqp;
		mvec4_wwww<T> wwww, aaaa, qqqq;
	};
	using TYPE = mvec4_t<T>;
	
	mvec4_t(): x(0),y(0),z(0),w(0) {}
	template<typename T1,typename=std::enable_if_t<!is_vector_v<T1>||vec_length<T1> ==4>>
	mvec4_t(const T1& a);
	
	template<typename T1,typename T2,typename=std::enable_if_t<vec_length<T1>+vec_length<T2> ==4 >>
	mvec4_t(const T1& a, const T2& b);
	
	template<typename T1,typename T2,typename T3, typename=std::enable_if_t<vec_length<T1>+vec_length<T2>+vec_length<T3> ==4 >>
	mvec4_t(const T1& a, const T2& b, const T3& c );
	
	template<typename T1,typename T2,typename T3,typename T4,typename=std::enable_if_t<!is_vector_v<T1>&&!is_vector_v<T2>&&!is_vector_v<T3>&&!is_vector_v<T4>>>
	inline mvec4_t(T1 _x, T2 _y, T3 _z, T4 _w): x(T(_x)), y(T(_y)), z(T(_z)), w(T(_w))  {}

	
//	template<typename T2> mvec4_t(const mvec4_t<T2>& a):x(static_cast<T>(a.x)),y(static_cast<T>(a.y)),z(static_cast<T>(a.z)),w(static_cast<T>(a.w)){}
	
	T& operator [] (int n) { return v[n]; }
	const T& operator [] (int n) const { return v[n]; }
	size_t length() const { return 4; }
	
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==4 && is_same_element_v<TYPE,F>)>>
	TYPE& operator+=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x+=f[0]; y+=f[1]; z+=f[2]; w+=f[3]; return *this; }
		else							{ x+=f; y+=f; z+=f; w+=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==4 && is_same_element_v<TYPE,F>)>>
	TYPE& operator-=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x-=f[0]; y-=f[1]; z-=f[2]; w-=f[3]; return *this; }
		else							{ x-=f; y-=f; z-=f; w-=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==4 && is_same_element_v<TYPE,F>)>>
	TYPE& operator*=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x*=f[0]; y*=f[1]; z*=f[2]; w*=f[3]; return *this; }
		else							{ x*=f; y*=f; z*=f; w*=f; return *this; }
	}
	template<typename F,typename=std::enable_if_t<!is_vector_v<F> || (vec_length<F> ==4 && is_same_element_v<TYPE,F>)>>
	TYPE& operator/=(const F& f) {
		if constexpr( is_vector_v<F> )	{ x/=f[0]; y/=f[1]; z/=f[2]; w/=f[3]; return *this; }
		else							{ x/=f; y/=f; z/=f; w/=f; return *this; }
	}

	TYPE& operator++() { x+=1; y+=1; z+=1; w+=1; return *this; }
	TYPE& operator--() { x-=1; y-=1; z-=1; w-=1; return *this; }
	TYPE operator++(int) { TYPE a=*this; operator++(); return a; }
	TYPE operator--(int) { TYPE a=*this; operator--(); return a; }
};


template<typename T> template<typename T1>
inline mvec2_t<T>::mvec2_t(const T1& a) {
	if constexpr ( !is_vector_v<T1> ) {
		x = T(a); y = T(a);
	}
	else {
		x = T(a[0]); y = T(a[1]);
	}
}
template<typename T> template<typename T1,typename>
inline mvec3_t<T>::mvec3_t(const T1& a){
	if constexpr ( !is_vector_v<T1> ) {
		x = T(a); y = T(a); z = T(a);
	}
	else {
		x = T(a[0]); y = T(a[1]); z = T(a[2]);
	}
}

template<typename T> template<typename T1, typename T2, typename>
inline mvec3_t<T>::mvec3_t(const T1& a, const T2& b){
	if constexpr ( !is_vector_v<T1> ) {
		x = T(a); y = T(b[0]); z = T(b[1]);
	}
	else {
		x = T(a[0]); y = T(a[1]); z = T(b);
	}
}

template<typename T> template<typename T1,typename>
inline mvec4_t<T>::mvec4_t(const T1& a){
	if constexpr ( !is_vector_v<T1> ) {
		x = T(a); y = T(a); z = T(a); w = T(a);
	}
	else {
		x = T(a[0]); y = T(a[1]); z = T(a[2]); w = T(a[3]);
	}
}

template<typename T> template<typename T1, typename T2,typename>
inline mvec4_t<T>::mvec4_t(const T1& a, const T2& b){
	if constexpr ( !is_vector_v<T1> ) {
		x = T(a); y = T(b[0]); z = T(b[1]); w = T(b[2]);
	}
	else if constexpr ( vec_length<T1> == 2) {
		x = T(a[0]); y = T(a[1]); z = T(b[0]); w = T(b[1]);
	}
	else {
		x = T(a[0]); y = T(a[1]); z = T(a[2]); w = T(b);
	}
}

template<typename T> template<typename T1, typename T2, typename T3,typename>
inline mvec4_t<T>::mvec4_t(const T1& a, const T2& b, const T3& c){
	if constexpr ( !is_vector_v<T1> ) {
		if constexpr ( !is_vector_v<T2> ) {
			x = T(a); y = T(b); z = T(c[0]); w = T(c[1]);
		}
		else {
			x = T(a); y = T(b[0]); z = T(b[1]); w = T(c);
		}
	}
	else {
		x = T(a[0]); y = T(a[1]); z = T(b); w = T(c);
	}
}




#define GEN_SWIZZLE_FUN_2_(NAME) \
template<typename T> NAME<T>::operator mvec2_t<T>() const { return mvec2_t<T>(v[idx[0]],v[idx[1]]); } \

#define GEN_SWIZZLE_FUN_3_(NAME) \
template<typename T> NAME<T>::operator mvec3_t<T>() const { return mvec3_t<T>(v[idx[0]],v[idx[1]],v[idx[2]]); } \

#define GEN_SWIZZLE_FUN_4_(NAME) \
template<typename T> NAME<T>::operator mvec4_t<T>() const { return mvec4_t<T>(v[idx[0]],v[idx[1]],v[idx[2]],v[idx[3]]); } \

#define GEN_SWIZZLE_FUN_2C(NAME) \
template<typename T> NAME<T>::operator mvec2_t<T>() const { \
	return mvec2_t<T>(v[idx[0]],v[idx[1]]); \
} \
template<typename T> template<typename F,typename> \
mvec2_t<T> NAME<T>::operator =(const F& a) { \
	v[idx[0]] =a.x;v[idx[1]] =a.y;v[idx[2]] =a.z;v[idx[3]] =a.w; \
	return static_cast<mvec2_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec2_t<T> NAME<T>::operator+=( const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]+=a;  v[idx[1]]+=a;  } \
	else 							{ v[idx[0]]+=a.x;v[idx[1]]+=a.y;} \
	return static_cast<mvec2_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec2_t<T> NAME<T>::operator-=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]-=a;  v[idx[1]]-=a;  } \
	else 							{ v[idx[0]]-=a.x;v[idx[1]]-=a.y;} \
	return static_cast<mvec2_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec2_t<T> NAME<T>::operator*=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]*=a;  v[idx[1]]*=a;  } \
	else 							{ v[idx[0]]*=a.x;v[idx[1]]*=a.y;} \
	return static_cast<mvec2_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec2_t<T> NAME<T>::operator/=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]/=a;  v[idx[1]]/=a;  } \
	else 							{ v[idx[0]]/=a.x;v[idx[1]]/=a.y;} \
	return static_cast<mvec2_t<T>>(*this); \
} \

#define GEN_SWIZZLE_FUN_3C(NAME) \
template<typename T> NAME<T>::operator mvec3_t<T>() const { \
	return mvec3_t<T>(v[idx[0]],v[idx[1]],v[idx[2]]); \
} \
template<typename T> template<typename F,typename> \
mvec3_t<T> NAME<T>::operator =(const F& a) { \
	v[idx[0]] =a.x;v[idx[1]] =a.y;v[idx[2]] =a.z; \
	return static_cast<mvec3_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec3_t<T> NAME<T>::operator+=( const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]+=a;  v[idx[1]]+=a;  v[idx[2]]+=a;  } \
	else 							{ v[idx[0]]+=a.x;v[idx[1]]+=a.y;v[idx[2]]+=a.z;} \
	return static_cast<mvec3_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec3_t<T> NAME<T>::operator-=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]-=a;  v[idx[1]]-=a;  v[idx[2]]-=a;  } \
	else 							{ v[idx[0]]-=a.x;v[idx[1]]-=a.y;v[idx[2]]-=a.z;} \
	return static_cast<mvec3_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec3_t<T> NAME<T>::operator*=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]*=a;  v[idx[1]]*=a;  v[idx[2]]*=a;  } \
	else 							{ v[idx[0]]*=a.x;v[idx[1]]*=a.y;v[idx[2]]*=a.z;} \
	return static_cast<mvec3_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec3_t<T> NAME<T>::operator/=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]/=a;  v[idx[1]]/=a;  v[idx[2]]/=a;  } \
	else 							{ v[idx[0]]/=a.x;v[idx[1]]/=a.y;v[idx[2]]/=a.z;} \
	return static_cast<mvec3_t<T>>(*this); \
} \


#define GEN_SWIZZLE_FUN_4C(NAME) \
template<typename T> NAME<T>::operator mvec4_t<T>() const { \
	return mvec4_t<T>(v[idx[0]],v[idx[1]],v[idx[2]],v[idx[3]]); \
} \
template<typename T> template<typename F,typename> \
mvec4_t<T> NAME<T>::operator =(const F& a) { \
	v[idx[0]] =a.x;v[idx[1]] =a.y;v[idx[2]] =a.z;v[idx[3]] =a.w; \
	return static_cast<mvec4_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec4_t<T> NAME<T>::operator+=( const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]+=a;  v[idx[1]]+=a;  v[idx[2]]+=a;  v[idx[3]]+=a; } \
	else 							{ v[idx[0]]+=a.x;v[idx[1]]+=a.y;v[idx[2]]+=a.z;v[idx[3]]+=a.w; } \
	return static_cast<mvec4_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec4_t<T> NAME<T>::operator-=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]-=a;  v[idx[1]]-=a;  v[idx[2]]-=a;  v[idx[3]]-=a; } \
	else 							{ v[idx[0]]-=a.x;v[idx[1]]-=a.y;v[idx[2]]-=a.z;v[idx[3]]-=a.w; } \
	return static_cast<mvec4_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec4_t<T> NAME<T>::operator*=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]*=a;  v[idx[1]]*=a;  v[idx[2]]*=a;  v[idx[3]]*=a; } \
	else 							{ v[idx[0]]*=a.x;v[idx[1]]*=a.y;v[idx[2]]*=a.z;v[idx[3]]*=a.w; } \
	return static_cast<mvec4_t<T>>(*this); \
} \
template<typename T> template<typename F,typename> \
mvec4_t<T> NAME<T>::operator/=(const F& a) { \
	if constexpr ( !is_vector_v<F> ){ v[idx[0]]/=a;  v[idx[1]]/=a;  v[idx[2]]/=a;  v[idx[3]]/=a; } \
	else 							{ v[idx[0]]/=a.x;v[idx[1]]/=a.y;v[idx[2]]/=a.z;v[idx[3]]/=a.w; } \
	return static_cast<mvec4_t<T>>(*this); \
}



GEN_SWIZZLE_FUN_2_(mvec2_xx);	GEN_SWIZZLE_FUN_2C(mvec2_xy);	GEN_SWIZZLE_FUN_2C(mvec2_yx);	GEN_SWIZZLE_FUN_2_(mvec2_yy);

GEN_SWIZZLE_FUN_2_(mvec3_xx);	GEN_SWIZZLE_FUN_2C(mvec3_xy);	GEN_SWIZZLE_FUN_2C(mvec3_xz);
GEN_SWIZZLE_FUN_2C(mvec3_yx);	GEN_SWIZZLE_FUN_2_(mvec3_yy);	GEN_SWIZZLE_FUN_2C(mvec3_yz);
GEN_SWIZZLE_FUN_2C(mvec3_zx);	GEN_SWIZZLE_FUN_2C(mvec3_zy);	GEN_SWIZZLE_FUN_2_(mvec3_zz);

GEN_SWIZZLE_FUN_2_(mvec4_xx);	GEN_SWIZZLE_FUN_2C(mvec4_xy);	GEN_SWIZZLE_FUN_2C(mvec4_xz);	GEN_SWIZZLE_FUN_2C(mvec4_xw);
GEN_SWIZZLE_FUN_2C(mvec4_yx);	GEN_SWIZZLE_FUN_2_(mvec4_yy);	GEN_SWIZZLE_FUN_2C(mvec4_yz);	GEN_SWIZZLE_FUN_2C(mvec4_yw);
GEN_SWIZZLE_FUN_2C(mvec4_zx);	GEN_SWIZZLE_FUN_2C(mvec4_zy);	GEN_SWIZZLE_FUN_2_(mvec4_zz);	GEN_SWIZZLE_FUN_2C(mvec4_zw);
GEN_SWIZZLE_FUN_2C(mvec4_wx);	GEN_SWIZZLE_FUN_2C(mvec4_wy);	GEN_SWIZZLE_FUN_2C(mvec4_wz);	GEN_SWIZZLE_FUN_2_(mvec4_ww);



GEN_SWIZZLE_FUN_3_(mvec2_xxx);	GEN_SWIZZLE_FUN_3_(mvec2_xxy);	GEN_SWIZZLE_FUN_3_(mvec2_xyx);	GEN_SWIZZLE_FUN_3_(mvec2_xyy);
GEN_SWIZZLE_FUN_3_(mvec2_yxx);	GEN_SWIZZLE_FUN_3_(mvec2_yxy);	GEN_SWIZZLE_FUN_3_(mvec2_yyx);	GEN_SWIZZLE_FUN_3_(mvec2_yyy);

GEN_SWIZZLE_FUN_3_(mvec3_xxx);	GEN_SWIZZLE_FUN_3_(mvec3_xxy);	GEN_SWIZZLE_FUN_3_(mvec3_xxz);
GEN_SWIZZLE_FUN_3_(mvec3_xyx);	GEN_SWIZZLE_FUN_3_(mvec3_xyy);	GEN_SWIZZLE_FUN_3C(mvec3_xyz);
GEN_SWIZZLE_FUN_3_(mvec3_xzx);	GEN_SWIZZLE_FUN_3C(mvec3_xzy);	GEN_SWIZZLE_FUN_3_(mvec3_xzz);
GEN_SWIZZLE_FUN_3_(mvec3_yxx);	GEN_SWIZZLE_FUN_3_(mvec3_yxy);	GEN_SWIZZLE_FUN_3C(mvec3_yxz);
GEN_SWIZZLE_FUN_3_(mvec3_yyx);	GEN_SWIZZLE_FUN_3_(mvec3_yyy);	GEN_SWIZZLE_FUN_3_(mvec3_yyz);
GEN_SWIZZLE_FUN_3C(mvec3_yzx);	GEN_SWIZZLE_FUN_3_(mvec3_yzy);	GEN_SWIZZLE_FUN_3_(mvec3_yzz);
GEN_SWIZZLE_FUN_3_(mvec3_zxx);	GEN_SWIZZLE_FUN_3C(mvec3_zxy);	GEN_SWIZZLE_FUN_3_(mvec3_zxz);
GEN_SWIZZLE_FUN_3C(mvec3_zyx);	GEN_SWIZZLE_FUN_3_(mvec3_zyy);	GEN_SWIZZLE_FUN_3_(mvec3_zyz);
GEN_SWIZZLE_FUN_3_(mvec3_zzx);	GEN_SWIZZLE_FUN_3_(mvec3_zzy);	GEN_SWIZZLE_FUN_3_(mvec3_zzz);

GEN_SWIZZLE_FUN_3_(mvec4_xxx);	GEN_SWIZZLE_FUN_3_(mvec4_xxy);	GEN_SWIZZLE_FUN_3_(mvec4_xxz);	GEN_SWIZZLE_FUN_3_(mvec4_xxw);
GEN_SWIZZLE_FUN_3_(mvec4_xyx);	GEN_SWIZZLE_FUN_3_(mvec4_xyy);	GEN_SWIZZLE_FUN_3C(mvec4_xyz);	GEN_SWIZZLE_FUN_3C(mvec4_xyw);
GEN_SWIZZLE_FUN_3_(mvec4_xzx);	GEN_SWIZZLE_FUN_3C(mvec4_xzy);	GEN_SWIZZLE_FUN_3_(mvec4_xzz);	GEN_SWIZZLE_FUN_3C(mvec4_xzw);
GEN_SWIZZLE_FUN_3_(mvec4_xwx);	GEN_SWIZZLE_FUN_3C(mvec4_xwy);	GEN_SWIZZLE_FUN_3C(mvec4_xwz);	GEN_SWIZZLE_FUN_3_(mvec4_xww);
GEN_SWIZZLE_FUN_3_(mvec4_yxx);	GEN_SWIZZLE_FUN_3_(mvec4_yxy);	GEN_SWIZZLE_FUN_3C(mvec4_yxz);	GEN_SWIZZLE_FUN_3C(mvec4_yxw);
GEN_SWIZZLE_FUN_3_(mvec4_yyx);	GEN_SWIZZLE_FUN_3_(mvec4_yyy);	GEN_SWIZZLE_FUN_3_(mvec4_yyz);	GEN_SWIZZLE_FUN_3_(mvec4_yyw);
GEN_SWIZZLE_FUN_3C(mvec4_yzx);	GEN_SWIZZLE_FUN_3_(mvec4_yzy);	GEN_SWIZZLE_FUN_3_(mvec4_yzz);	GEN_SWIZZLE_FUN_3C(mvec4_yzw);
GEN_SWIZZLE_FUN_3C(mvec4_ywx);	GEN_SWIZZLE_FUN_3_(mvec4_ywy);	GEN_SWIZZLE_FUN_3C(mvec4_ywz);	GEN_SWIZZLE_FUN_3_(mvec4_yww);
GEN_SWIZZLE_FUN_3_(mvec4_zxx);	GEN_SWIZZLE_FUN_3C(mvec4_zxy);	GEN_SWIZZLE_FUN_3_(mvec4_zxz);	GEN_SWIZZLE_FUN_3C(mvec4_zxw);
GEN_SWIZZLE_FUN_3C(mvec4_zyx);	GEN_SWIZZLE_FUN_3_(mvec4_zyy);	GEN_SWIZZLE_FUN_3_(mvec4_zyz);	GEN_SWIZZLE_FUN_3C(mvec4_zyw);
GEN_SWIZZLE_FUN_3_(mvec4_zzx);	GEN_SWIZZLE_FUN_3_(mvec4_zzy);	GEN_SWIZZLE_FUN_3_(mvec4_zzz);	GEN_SWIZZLE_FUN_3_(mvec4_zzw);
GEN_SWIZZLE_FUN_3C(mvec4_zwx);	GEN_SWIZZLE_FUN_3C(mvec4_zwy);	GEN_SWIZZLE_FUN_3_(mvec4_zwz);	GEN_SWIZZLE_FUN_3_(mvec4_zww);
GEN_SWIZZLE_FUN_3_(mvec4_wxx);	GEN_SWIZZLE_FUN_3C(mvec4_wxy);	GEN_SWIZZLE_FUN_3C(mvec4_wxz);	GEN_SWIZZLE_FUN_3_(mvec4_wxw);
GEN_SWIZZLE_FUN_3C(mvec4_wyx);	GEN_SWIZZLE_FUN_3_(mvec4_wyy);	GEN_SWIZZLE_FUN_3C(mvec4_wyz);	GEN_SWIZZLE_FUN_3_(mvec4_wyw);
GEN_SWIZZLE_FUN_3C(mvec4_wzx);	GEN_SWIZZLE_FUN_3C(mvec4_wzy);	GEN_SWIZZLE_FUN_3_(mvec4_wzz);	GEN_SWIZZLE_FUN_3_(mvec4_wzw);
GEN_SWIZZLE_FUN_3_(mvec4_wwx);	GEN_SWIZZLE_FUN_3_(mvec4_wwy);	GEN_SWIZZLE_FUN_3_(mvec4_wwz);	GEN_SWIZZLE_FUN_3_(mvec4_www);




GEN_SWIZZLE_FUN_4_(mvec2_xxxx);	GEN_SWIZZLE_FUN_4_(mvec2_xxxy);	GEN_SWIZZLE_FUN_4_(mvec2_xxyx);	GEN_SWIZZLE_FUN_4_(mvec2_xxyy);
GEN_SWIZZLE_FUN_4_(mvec2_xyxx);	GEN_SWIZZLE_FUN_4_(mvec2_xyxy);	GEN_SWIZZLE_FUN_4_(mvec2_xyyx);	GEN_SWIZZLE_FUN_4_(mvec2_xyyy);
GEN_SWIZZLE_FUN_4_(mvec2_yxxx);	GEN_SWIZZLE_FUN_4_(mvec2_yxxy);	GEN_SWIZZLE_FUN_4_(mvec2_yxyx);	GEN_SWIZZLE_FUN_4_(mvec2_yxyy);
GEN_SWIZZLE_FUN_4_(mvec2_yyxx);	GEN_SWIZZLE_FUN_4_(mvec2_yyxy);	GEN_SWIZZLE_FUN_4_(mvec2_yyyx);	GEN_SWIZZLE_FUN_4_(mvec2_yyyy);

GEN_SWIZZLE_FUN_4_(mvec3_xxxx);	GEN_SWIZZLE_FUN_4_(mvec3_xxxy);	GEN_SWIZZLE_FUN_4_(mvec3_xxxz);
GEN_SWIZZLE_FUN_4_(mvec3_xxyx);	GEN_SWIZZLE_FUN_4_(mvec3_xxyy);	GEN_SWIZZLE_FUN_4_(mvec3_xxyz);
GEN_SWIZZLE_FUN_4_(mvec3_xxzx);	GEN_SWIZZLE_FUN_4_(mvec3_xxzy);	GEN_SWIZZLE_FUN_4_(mvec3_xxzz);
GEN_SWIZZLE_FUN_4_(mvec3_xyxx);	GEN_SWIZZLE_FUN_4_(mvec3_xyxy);	GEN_SWIZZLE_FUN_4_(mvec3_xyxz);
GEN_SWIZZLE_FUN_4_(mvec3_xyyx);	GEN_SWIZZLE_FUN_4_(mvec3_xyyy);	GEN_SWIZZLE_FUN_4_(mvec3_xyyz);
GEN_SWIZZLE_FUN_4_(mvec3_xyzx);	GEN_SWIZZLE_FUN_4_(mvec3_xyzy);	GEN_SWIZZLE_FUN_4_(mvec3_xyzz);
GEN_SWIZZLE_FUN_4_(mvec3_xzxx);	GEN_SWIZZLE_FUN_4_(mvec3_xzxy);	GEN_SWIZZLE_FUN_4_(mvec3_xzxz);
GEN_SWIZZLE_FUN_4_(mvec3_xzyx);	GEN_SWIZZLE_FUN_4_(mvec3_xzyy);	GEN_SWIZZLE_FUN_4_(mvec3_xzyz);
GEN_SWIZZLE_FUN_4_(mvec3_xzzx);	GEN_SWIZZLE_FUN_4_(mvec3_xzzy);	GEN_SWIZZLE_FUN_4_(mvec3_xzzz);
GEN_SWIZZLE_FUN_4_(mvec3_yxxx);	GEN_SWIZZLE_FUN_4_(mvec3_yxxy);	GEN_SWIZZLE_FUN_4_(mvec3_yxxz);
GEN_SWIZZLE_FUN_4_(mvec3_yxyx);	GEN_SWIZZLE_FUN_4_(mvec3_yxyy);	GEN_SWIZZLE_FUN_4_(mvec3_yxyz);
GEN_SWIZZLE_FUN_4_(mvec3_yxzx);	GEN_SWIZZLE_FUN_4_(mvec3_yxzy);	GEN_SWIZZLE_FUN_4_(mvec3_yxzz);
GEN_SWIZZLE_FUN_4_(mvec3_yyxx);	GEN_SWIZZLE_FUN_4_(mvec3_yyxy);	GEN_SWIZZLE_FUN_4_(mvec3_yyxz);
GEN_SWIZZLE_FUN_4_(mvec3_yyyx);	GEN_SWIZZLE_FUN_4_(mvec3_yyyy);	GEN_SWIZZLE_FUN_4_(mvec3_yyyz);
GEN_SWIZZLE_FUN_4_(mvec3_yyzx);	GEN_SWIZZLE_FUN_4_(mvec3_yyzy);	GEN_SWIZZLE_FUN_4_(mvec3_yyzz);
GEN_SWIZZLE_FUN_4_(mvec3_yzxx);	GEN_SWIZZLE_FUN_4_(mvec3_yzxy);	GEN_SWIZZLE_FUN_4_(mvec3_yzxz);
GEN_SWIZZLE_FUN_4_(mvec3_yzyx);	GEN_SWIZZLE_FUN_4_(mvec3_yzyy);	GEN_SWIZZLE_FUN_4_(mvec3_yzyz);
GEN_SWIZZLE_FUN_4_(mvec3_yzzx);	GEN_SWIZZLE_FUN_4_(mvec3_yzzy);	GEN_SWIZZLE_FUN_4_(mvec3_yzzz);
GEN_SWIZZLE_FUN_4_(mvec3_zxxx);	GEN_SWIZZLE_FUN_4_(mvec3_zxxy);	GEN_SWIZZLE_FUN_4_(mvec3_zxxz);
GEN_SWIZZLE_FUN_4_(mvec3_zxyx);	GEN_SWIZZLE_FUN_4_(mvec3_zxyy);	GEN_SWIZZLE_FUN_4_(mvec3_zxyz);
GEN_SWIZZLE_FUN_4_(mvec3_zxzx);	GEN_SWIZZLE_FUN_4_(mvec3_zxzy);	GEN_SWIZZLE_FUN_4_(mvec3_zxzz);
GEN_SWIZZLE_FUN_4_(mvec3_zyxx);	GEN_SWIZZLE_FUN_4_(mvec3_zyxy);	GEN_SWIZZLE_FUN_4_(mvec3_zyxz);
GEN_SWIZZLE_FUN_4_(mvec3_zyyx);	GEN_SWIZZLE_FUN_4_(mvec3_zyyy);	GEN_SWIZZLE_FUN_4_(mvec3_zyyz);
GEN_SWIZZLE_FUN_4_(mvec3_zyzx);	GEN_SWIZZLE_FUN_4_(mvec3_zyzy);	GEN_SWIZZLE_FUN_4_(mvec3_zyzz);
GEN_SWIZZLE_FUN_4_(mvec3_zzxx);	GEN_SWIZZLE_FUN_4_(mvec3_zzxy);	GEN_SWIZZLE_FUN_4_(mvec3_zzxz);
GEN_SWIZZLE_FUN_4_(mvec3_zzyx);	GEN_SWIZZLE_FUN_4_(mvec3_zzyy);	GEN_SWIZZLE_FUN_4_(mvec3_zzyz);
GEN_SWIZZLE_FUN_4_(mvec3_zzzx);	GEN_SWIZZLE_FUN_4_(mvec3_zzzy);	GEN_SWIZZLE_FUN_4_(mvec3_zzzz);

GEN_SWIZZLE_FUN_4_(mvec4_xxxx);	GEN_SWIZZLE_FUN_4_(mvec4_xxxy);	GEN_SWIZZLE_FUN_4_(mvec4_xxxz);	GEN_SWIZZLE_FUN_4_(mvec4_xxxw);
GEN_SWIZZLE_FUN_4_(mvec4_xxyx);	GEN_SWIZZLE_FUN_4_(mvec4_xxyy);	GEN_SWIZZLE_FUN_4_(mvec4_xxyz);	GEN_SWIZZLE_FUN_4_(mvec4_xxyw);
GEN_SWIZZLE_FUN_4_(mvec4_xxzx);	GEN_SWIZZLE_FUN_4_(mvec4_xxzy);	GEN_SWIZZLE_FUN_4_(mvec4_xxzz);	GEN_SWIZZLE_FUN_4_(mvec4_xxzw);
GEN_SWIZZLE_FUN_4_(mvec4_xxwx);	GEN_SWIZZLE_FUN_4_(mvec4_xxwy);	GEN_SWIZZLE_FUN_4_(mvec4_xxwz);	GEN_SWIZZLE_FUN_4_(mvec4_xxww);
GEN_SWIZZLE_FUN_4_(mvec4_xyxx);	GEN_SWIZZLE_FUN_4_(mvec4_xyxy);	GEN_SWIZZLE_FUN_4_(mvec4_xyxz);	GEN_SWIZZLE_FUN_4_(mvec4_xyxw);
GEN_SWIZZLE_FUN_4_(mvec4_xyyx);	GEN_SWIZZLE_FUN_4_(mvec4_xyyy);	GEN_SWIZZLE_FUN_4_(mvec4_xyyz);	GEN_SWIZZLE_FUN_4_(mvec4_xyyw);
GEN_SWIZZLE_FUN_4_(mvec4_xyzx);	GEN_SWIZZLE_FUN_4_(mvec4_xyzy);	GEN_SWIZZLE_FUN_4_(mvec4_xyzz);	GEN_SWIZZLE_FUN_4C(mvec4_xyzw);
GEN_SWIZZLE_FUN_4_(mvec4_xywx);	GEN_SWIZZLE_FUN_4_(mvec4_xywy);	GEN_SWIZZLE_FUN_4C(mvec4_xywz);	GEN_SWIZZLE_FUN_4_(mvec4_xyww);
GEN_SWIZZLE_FUN_4_(mvec4_xzxx);	GEN_SWIZZLE_FUN_4_(mvec4_xzxy);	GEN_SWIZZLE_FUN_4_(mvec4_xzxz);	GEN_SWIZZLE_FUN_4_(mvec4_xzxw);
GEN_SWIZZLE_FUN_4_(mvec4_xzyx);	GEN_SWIZZLE_FUN_4_(mvec4_xzyy);	GEN_SWIZZLE_FUN_4_(mvec4_xzyz);	GEN_SWIZZLE_FUN_4C(mvec4_xzyw);
GEN_SWIZZLE_FUN_4_(mvec4_xzzx);	GEN_SWIZZLE_FUN_4_(mvec4_xzzy);	GEN_SWIZZLE_FUN_4_(mvec4_xzzz);	GEN_SWIZZLE_FUN_4_(mvec4_xzzw);
GEN_SWIZZLE_FUN_4_(mvec4_xzwx);	GEN_SWIZZLE_FUN_4C(mvec4_xzwy);	GEN_SWIZZLE_FUN_4_(mvec4_xzwz);	GEN_SWIZZLE_FUN_4_(mvec4_xzww);
GEN_SWIZZLE_FUN_4_(mvec4_xwxx);	GEN_SWIZZLE_FUN_4_(mvec4_xwxy);	GEN_SWIZZLE_FUN_4_(mvec4_xwxz);	GEN_SWIZZLE_FUN_4_(mvec4_xwxw);
GEN_SWIZZLE_FUN_4_(mvec4_xwyx);	GEN_SWIZZLE_FUN_4_(mvec4_xwyy);	GEN_SWIZZLE_FUN_4C(mvec4_xwyz);	GEN_SWIZZLE_FUN_4_(mvec4_xwyw);
GEN_SWIZZLE_FUN_4_(mvec4_xwzx);	GEN_SWIZZLE_FUN_4C(mvec4_xwzy);	GEN_SWIZZLE_FUN_4_(mvec4_xwzz);	GEN_SWIZZLE_FUN_4_(mvec4_xwzw);
GEN_SWIZZLE_FUN_4_(mvec4_xwwx);	GEN_SWIZZLE_FUN_4_(mvec4_xwwy);	GEN_SWIZZLE_FUN_4_(mvec4_xwwz);	GEN_SWIZZLE_FUN_4_(mvec4_xwww);

GEN_SWIZZLE_FUN_4_(mvec4_yxxx);	GEN_SWIZZLE_FUN_4_(mvec4_yxxy);	GEN_SWIZZLE_FUN_4_(mvec4_yxxz);	GEN_SWIZZLE_FUN_4_(mvec4_yxxw);
GEN_SWIZZLE_FUN_4_(mvec4_yxyx);	GEN_SWIZZLE_FUN_4_(mvec4_yxyy);	GEN_SWIZZLE_FUN_4_(mvec4_yxyz);	GEN_SWIZZLE_FUN_4_(mvec4_yxyw);
GEN_SWIZZLE_FUN_4_(mvec4_yxzx);	GEN_SWIZZLE_FUN_4_(mvec4_yxzy);	GEN_SWIZZLE_FUN_4_(mvec4_yxzz);	GEN_SWIZZLE_FUN_4C(mvec4_yxzw);
GEN_SWIZZLE_FUN_4_(mvec4_yxwx);	GEN_SWIZZLE_FUN_4_(mvec4_yxwy);	GEN_SWIZZLE_FUN_4C(mvec4_yxwz);	GEN_SWIZZLE_FUN_4_(mvec4_yxww);
GEN_SWIZZLE_FUN_4_(mvec4_yyxx);	GEN_SWIZZLE_FUN_4_(mvec4_yyxy);	GEN_SWIZZLE_FUN_4_(mvec4_yyxz);	GEN_SWIZZLE_FUN_4_(mvec4_yyxw);
GEN_SWIZZLE_FUN_4_(mvec4_yyyx);	GEN_SWIZZLE_FUN_4_(mvec4_yyyy);	GEN_SWIZZLE_FUN_4_(mvec4_yyyz);	GEN_SWIZZLE_FUN_4_(mvec4_yyyw);
GEN_SWIZZLE_FUN_4_(mvec4_yyzx);	GEN_SWIZZLE_FUN_4_(mvec4_yyzy);	GEN_SWIZZLE_FUN_4_(mvec4_yyzz);	GEN_SWIZZLE_FUN_4_(mvec4_yyzw);
GEN_SWIZZLE_FUN_4_(mvec4_yywx);	GEN_SWIZZLE_FUN_4_(mvec4_yywy);	GEN_SWIZZLE_FUN_4_(mvec4_yywz);	GEN_SWIZZLE_FUN_4_(mvec4_yyww);
GEN_SWIZZLE_FUN_4_(mvec4_yzxx);	GEN_SWIZZLE_FUN_4_(mvec4_yzxy);	GEN_SWIZZLE_FUN_4_(mvec4_yzxz);	GEN_SWIZZLE_FUN_4C(mvec4_yzxw);
GEN_SWIZZLE_FUN_4_(mvec4_yzyx);	GEN_SWIZZLE_FUN_4_(mvec4_yzyy);	GEN_SWIZZLE_FUN_4_(mvec4_yzyz);	GEN_SWIZZLE_FUN_4_(mvec4_yzyw);
GEN_SWIZZLE_FUN_4_(mvec4_yzzx);	GEN_SWIZZLE_FUN_4_(mvec4_yzzy);	GEN_SWIZZLE_FUN_4_(mvec4_yzzz);	GEN_SWIZZLE_FUN_4_(mvec4_yzzw);
GEN_SWIZZLE_FUN_4C(mvec4_yzwx);	GEN_SWIZZLE_FUN_4_(mvec4_yzwy);	GEN_SWIZZLE_FUN_4_(mvec4_yzwz);	GEN_SWIZZLE_FUN_4_(mvec4_yzww);
GEN_SWIZZLE_FUN_4_(mvec4_ywxx);	GEN_SWIZZLE_FUN_4_(mvec4_ywxy);	GEN_SWIZZLE_FUN_4C(mvec4_ywxz);	GEN_SWIZZLE_FUN_4_(mvec4_ywxw);
GEN_SWIZZLE_FUN_4_(mvec4_ywyx);	GEN_SWIZZLE_FUN_4_(mvec4_ywyy);	GEN_SWIZZLE_FUN_4_(mvec4_ywyz);	GEN_SWIZZLE_FUN_4_(mvec4_ywyw);
GEN_SWIZZLE_FUN_4C(mvec4_ywzx);	GEN_SWIZZLE_FUN_4_(mvec4_ywzy);	GEN_SWIZZLE_FUN_4_(mvec4_ywzz);	GEN_SWIZZLE_FUN_4_(mvec4_ywzw);
GEN_SWIZZLE_FUN_4_(mvec4_ywwx);	GEN_SWIZZLE_FUN_4_(mvec4_ywwy);	GEN_SWIZZLE_FUN_4_(mvec4_ywwz);	GEN_SWIZZLE_FUN_4_(mvec4_ywww);

GEN_SWIZZLE_FUN_4_(mvec4_zxxx);	GEN_SWIZZLE_FUN_4_(mvec4_zxxy);	GEN_SWIZZLE_FUN_4_(mvec4_zxxz);	GEN_SWIZZLE_FUN_4_(mvec4_zxxw);
GEN_SWIZZLE_FUN_4_(mvec4_zxyx);	GEN_SWIZZLE_FUN_4_(mvec4_zxyy);	GEN_SWIZZLE_FUN_4_(mvec4_zxyz);	GEN_SWIZZLE_FUN_4C(mvec4_zxyw);
GEN_SWIZZLE_FUN_4_(mvec4_zxzx);	GEN_SWIZZLE_FUN_4_(mvec4_zxzy);	GEN_SWIZZLE_FUN_4_(mvec4_zxzz);	GEN_SWIZZLE_FUN_4_(mvec4_zxzw);
GEN_SWIZZLE_FUN_4_(mvec4_zxwx);	GEN_SWIZZLE_FUN_4C(mvec4_zxwy);	GEN_SWIZZLE_FUN_4_(mvec4_zxwz);	GEN_SWIZZLE_FUN_4_(mvec4_zxww);
GEN_SWIZZLE_FUN_4_(mvec4_zyxx);	GEN_SWIZZLE_FUN_4_(mvec4_zyxy);	GEN_SWIZZLE_FUN_4_(mvec4_zyxz);	GEN_SWIZZLE_FUN_4C(mvec4_zyxw);
GEN_SWIZZLE_FUN_4_(mvec4_zyyx);	GEN_SWIZZLE_FUN_4_(mvec4_zyyy);	GEN_SWIZZLE_FUN_4_(mvec4_zyyz);	GEN_SWIZZLE_FUN_4_(mvec4_zyyw);
GEN_SWIZZLE_FUN_4_(mvec4_zyzx);	GEN_SWIZZLE_FUN_4_(mvec4_zyzy);	GEN_SWIZZLE_FUN_4_(mvec4_zyzz);	GEN_SWIZZLE_FUN_4_(mvec4_zyzw);
GEN_SWIZZLE_FUN_4C(mvec4_zywx);	GEN_SWIZZLE_FUN_4_(mvec4_zywy);	GEN_SWIZZLE_FUN_4_(mvec4_zywz);	GEN_SWIZZLE_FUN_4_(mvec4_zyww);
GEN_SWIZZLE_FUN_4_(mvec4_zzxx);	GEN_SWIZZLE_FUN_4_(mvec4_zzxy);	GEN_SWIZZLE_FUN_4_(mvec4_zzxz);	GEN_SWIZZLE_FUN_4_(mvec4_zzxw);
GEN_SWIZZLE_FUN_4_(mvec4_zzyx);	GEN_SWIZZLE_FUN_4_(mvec4_zzyy);	GEN_SWIZZLE_FUN_4_(mvec4_zzyz);	GEN_SWIZZLE_FUN_4_(mvec4_zzyw);
GEN_SWIZZLE_FUN_4_(mvec4_zzzx);	GEN_SWIZZLE_FUN_4_(mvec4_zzzy);	GEN_SWIZZLE_FUN_4_(mvec4_zzzz);	GEN_SWIZZLE_FUN_4_(mvec4_zzzw);
GEN_SWIZZLE_FUN_4_(mvec4_zzwx);	GEN_SWIZZLE_FUN_4_(mvec4_zzwy);	GEN_SWIZZLE_FUN_4_(mvec4_zzwz);	GEN_SWIZZLE_FUN_4_(mvec4_zzww);
GEN_SWIZZLE_FUN_4_(mvec4_zwxx);	GEN_SWIZZLE_FUN_4C(mvec4_zwxy);	GEN_SWIZZLE_FUN_4_(mvec4_zwxz);	GEN_SWIZZLE_FUN_4_(mvec4_zwxw);
GEN_SWIZZLE_FUN_4C(mvec4_zwyx);	GEN_SWIZZLE_FUN_4_(mvec4_zwyy);	GEN_SWIZZLE_FUN_4_(mvec4_zwyz);	GEN_SWIZZLE_FUN_4_(mvec4_zwyw);
GEN_SWIZZLE_FUN_4_(mvec4_zwzx);	GEN_SWIZZLE_FUN_4_(mvec4_zwzy);	GEN_SWIZZLE_FUN_4_(mvec4_zwzz);	GEN_SWIZZLE_FUN_4_(mvec4_zwzw);
GEN_SWIZZLE_FUN_4_(mvec4_zwwx);	GEN_SWIZZLE_FUN_4_(mvec4_zwwy);	GEN_SWIZZLE_FUN_4_(mvec4_zwwz);	GEN_SWIZZLE_FUN_4_(mvec4_zwww);

GEN_SWIZZLE_FUN_4_(mvec4_wxxx);	GEN_SWIZZLE_FUN_4_(mvec4_wxxy);	GEN_SWIZZLE_FUN_4_(mvec4_wxxz);	GEN_SWIZZLE_FUN_4_(mvec4_wxxw);
GEN_SWIZZLE_FUN_4_(mvec4_wxyx);	GEN_SWIZZLE_FUN_4_(mvec4_wxyy);	GEN_SWIZZLE_FUN_4C(mvec4_wxyz);	GEN_SWIZZLE_FUN_4_(mvec4_wxyw);
GEN_SWIZZLE_FUN_4_(mvec4_wxzx);	GEN_SWIZZLE_FUN_4C(mvec4_wxzy);	GEN_SWIZZLE_FUN_4_(mvec4_wxzz);	GEN_SWIZZLE_FUN_4_(mvec4_wxzw);
GEN_SWIZZLE_FUN_4_(mvec4_wxwx);	GEN_SWIZZLE_FUN_4_(mvec4_wxwy);	GEN_SWIZZLE_FUN_4_(mvec4_wxwz);	GEN_SWIZZLE_FUN_4_(mvec4_wxww);
GEN_SWIZZLE_FUN_4_(mvec4_wyxx);	GEN_SWIZZLE_FUN_4_(mvec4_wyxy);	GEN_SWIZZLE_FUN_4C(mvec4_wyxz);	GEN_SWIZZLE_FUN_4_(mvec4_wyxw);
GEN_SWIZZLE_FUN_4_(mvec4_wyyx);	GEN_SWIZZLE_FUN_4_(mvec4_wyyy);	GEN_SWIZZLE_FUN_4_(mvec4_wyyz);	GEN_SWIZZLE_FUN_4_(mvec4_wyyw);
GEN_SWIZZLE_FUN_4C(mvec4_wyzx);	GEN_SWIZZLE_FUN_4_(mvec4_wyzy);	GEN_SWIZZLE_FUN_4_(mvec4_wyzz);	GEN_SWIZZLE_FUN_4_(mvec4_wyzw);
GEN_SWIZZLE_FUN_4_(mvec4_wywx);	GEN_SWIZZLE_FUN_4_(mvec4_wywy);	GEN_SWIZZLE_FUN_4_(mvec4_wywz);	GEN_SWIZZLE_FUN_4_(mvec4_wyww);
GEN_SWIZZLE_FUN_4_(mvec4_wzxx);	GEN_SWIZZLE_FUN_4C(mvec4_wzxy);	GEN_SWIZZLE_FUN_4_(mvec4_wzxz);	GEN_SWIZZLE_FUN_4_(mvec4_wzxw);
GEN_SWIZZLE_FUN_4C(mvec4_wzyx);	GEN_SWIZZLE_FUN_4_(mvec4_wzyy);	GEN_SWIZZLE_FUN_4_(mvec4_wzyz);	GEN_SWIZZLE_FUN_4_(mvec4_wzyw);
GEN_SWIZZLE_FUN_4_(mvec4_wzzx);	GEN_SWIZZLE_FUN_4_(mvec4_wzzy);	GEN_SWIZZLE_FUN_4_(mvec4_wzzz);	GEN_SWIZZLE_FUN_4_(mvec4_wzzw);
GEN_SWIZZLE_FUN_4_(mvec4_wzwx);	GEN_SWIZZLE_FUN_4_(mvec4_wzwy);	GEN_SWIZZLE_FUN_4_(mvec4_wzwz);	GEN_SWIZZLE_FUN_4_(mvec4_wzww);
GEN_SWIZZLE_FUN_4_(mvec4_wwxx);	GEN_SWIZZLE_FUN_4_(mvec4_wwxy);	GEN_SWIZZLE_FUN_4_(mvec4_wwxz);	GEN_SWIZZLE_FUN_4_(mvec4_wwxw);
GEN_SWIZZLE_FUN_4_(mvec4_wwyx);	GEN_SWIZZLE_FUN_4_(mvec4_wwyy);	GEN_SWIZZLE_FUN_4_(mvec4_wwyz);	GEN_SWIZZLE_FUN_4_(mvec4_wwyw);
GEN_SWIZZLE_FUN_4_(mvec4_wwzx);	GEN_SWIZZLE_FUN_4_(mvec4_wwzy);	GEN_SWIZZLE_FUN_4_(mvec4_wwzz);	GEN_SWIZZLE_FUN_4_(mvec4_wwzw);
GEN_SWIZZLE_FUN_4_(mvec4_wwwx);	GEN_SWIZZLE_FUN_4_(mvec4_wwwy);	GEN_SWIZZLE_FUN_4_(mvec4_wwwz);	GEN_SWIZZLE_FUN_4_(mvec4_wwww);


template<typename T> vec_element<T>* value_ptr(T& a) {
	if constexpr ( !is_vector_v<T> )	return &a;
	else								return a.v;
}

template<typename T> const vec_element<T>* value_ptr(const T& a) {
	if constexpr ( !is_vector_v<T> )	return &a;
	else								return a.v;
}

#define GEN_OPERATOR( OP ) \
template<typename T1, typename T2, \
typename=std::enable_if_t<(!is_vector_v<T1>||!is_vector_v<T2>||is_same_length_v<T1,T2>)&&(is_vector_v<T1>||is_vector_v<T2>)>> \
auto operator OP ( const T1& a, const T2& b ) { \
	if constexpr ( is_vector_v<T1> ) { \
		if constexpr ( is_vector_v<T2> ) { \
			using scalar = common_element_type_t<T1,T2>; \
			if constexpr ( vec_length<T1> == 4)		return vec_type_t<scalar,4>(a[0] OP b[0],a[1] OP b[1],a[2] OP b[2],a[3] OP b[3]); \
			else if constexpr ( vec_length<T1> ==3)	return vec_type_t<scalar,3>(a[0] OP b[0],a[1] OP b[1],a[2] OP b[2]); \
			else									return vec_type_t<scalar,2>(a[0] OP b[0],a[1] OP b[1]); \
		} \
		else { \
			using scalar = vec_element<T1>; \
			if constexpr ( vec_length<T1> == 4)		return vec_type_t<scalar,4>(a[0] OP b,a[1] OP b,a[2] OP b,a[3] OP b); \
			else if constexpr ( vec_length<T1> ==3)	return vec_type_t<scalar,3>(a[0] OP b,a[1] OP b,a[2] OP b); \
			else									return vec_type_t<scalar,2>(a[0] OP b,a[1] OP b); \
		} \
	} \
	else { \
		using scalar = vec_element<T2>; \
		if constexpr ( vec_length<T2> == 4)		return vec_type_t<scalar,4>(a OP b[0],a OP b[1],a OP b[2],a OP b[3]); \
		else if constexpr ( vec_length<T2> ==3)	return vec_type_t<scalar,3>(a OP b[0],a OP b[1],a OP b[2]); \
		else									return vec_type_t<scalar,2>(a OP b[0],a OP b[1]); \
	} \
}

GEN_OPERATOR( + );
GEN_OPERATOR( - );
GEN_OPERATOR( * );
GEN_OPERATOR( / );

template<typename T, typename=std::enable_if_t<is_vector_v<T>>>
auto operator - ( const T& a ) {
	if constexpr ( vec_length<T> == 4)		return comp_vec_type_t<T>(-a[0],-a[1],-a[2],-a[3]);
	else if constexpr ( vec_length<T> == 3)	return comp_vec_type_t<T>(-a[0],-a[1],-a[2]);
	else									return comp_vec_type_t<T>(-a[0],-a[1]);
}
template<typename T, typename=std::enable_if_t<is_vector_v<T>>>
auto operator + ( const T& a ) {
	if constexpr ( vec_length<T> == 4)		return comp_vec_type_t<T>(a[0],a[1],a[2],a[3]);
	else if constexpr ( vec_length<T> == 3) return comp_vec_type_t<T>(a[0],a[1],a[2]);
	else									return comp_vec_type_t<T>(a[0],a[1]);
}
template<typename T1,typename T2, typename=std::enable_if_t<is_vector_v<T1> && is_same_length_v<T1, T2>>>
auto operator == ( const T1& a, const T2& b ) { \
	if constexpr ( vec_length<T1> == 4)		return a[0]==b[0]&&a[1]==b[1]&&a[2]==b[2]&&a[3]==b[3];
	else if constexpr ( vec_length<T1> ==3)	return a[0]==b[0]&&a[1]==b[1]&&a[2]==b[2];
	else									return a[0]==b[0]&&a[1]==b[1];
}
template<typename T1,typename T2, typename=std::enable_if_t<is_vector_v<T1> && is_same_length_v<T1, T2>>>
auto operator != ( const T1& a, const T2& b ) { \
	if constexpr ( vec_length<T1> ==4)		return a[0]!=b[0]||a[1]!=b[1]||a[2]!=b[2]||a[3]!=b[3];
	else if constexpr ( vec_length<T1> ==3)	return a[0]!=b[0]||a[1]!=b[1]||a[2]!=b[2];
	else									return a[0]!=b[0]||a[1]!=b[1];
}



typedef mvec2_t<float> vec2;
typedef mvec3_t<float> vec3;
typedef mvec4_t<float> vec4;

typedef mvec2_t<half> hvec2;
typedef mvec3_t<half> hvec3;
typedef mvec4_t<half> hvec4;

typedef mvec2_t<double> dvec2;
typedef mvec3_t<double> dvec3;
typedef mvec4_t<double> dvec4;

typedef mvec2_t<bool> bvec2;
typedef mvec3_t<bool> bvec3;
typedef mvec4_t<bool> bvec4;

typedef mvec2_t<char> i8vec2;
typedef mvec3_t<char> i8vec3;
typedef mvec4_t<char> i8vec4;

typedef mvec2_t<short> i16vec2;
typedef mvec3_t<short> i16vec3;
typedef mvec4_t<short> i16vec4;

typedef mvec2_t<int> ivec2;
typedef mvec3_t<int> ivec3;
typedef mvec4_t<int> ivec4;

typedef mvec2_t<uchar> u8vec2;
typedef mvec3_t<uchar> u8vec3;
typedef mvec4_t<uchar> u8vec4;

typedef mvec2_t<ushort> u16vec2;
typedef mvec3_t<ushort> u16vec3;
typedef mvec4_t<ushort> u16vec4;

typedef mvec2_t<uint> uvec2;
typedef mvec3_t<uint> uvec3;
typedef mvec4_t<uint> uvec4;

}

#endif /* jm_vec_h */
