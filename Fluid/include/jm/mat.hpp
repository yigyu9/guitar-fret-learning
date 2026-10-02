//
//  jm_mat.hpp
//  SystemCalib
//
//  Created by Hyun Joon Shin on 2023/08/25.
//

#ifndef jm_mat_h
#define jm_mat_h

#include "vec_func.hpp"

namespace jm {

#define MatType mmat_t
template<typename T,size_t COL, size_t ROW> struct MatType {
	using VecType = vec_type_t<T,ROW>;
	VecType v[COL];
	
	MatType() { for( int i=0; i<COL; i++ ) v[i]=VecType(0); }
	
	template<typename T1, typename=std::enable_if_t<is_number_v<T1>>>		// Single vector constructor is not allowed
	MatType(const T1& a);

	template<typename T1,typename T2,typename=std::enable_if_t<COL==2&&vec_length<T1> ==ROW&&vec_length<T2> ==ROW>>
	MatType(const T1& a0, const T2& a1) {
		v[0]=VecType(a0); v[1]=VecType(a1);
	}
	template<typename T1,typename T2,typename T3,typename=std::enable_if_t<COL==3&&vec_length<T1> ==ROW&&vec_length<T2> ==ROW&&vec_length<T3> ==ROW>>
	MatType(const T1& a0, const T2& a1, const T3& a2) {
		v[0]=VecType(a0); v[1]=VecType(a1); v[2]=VecType(a2);
	}
	template<typename T1,typename T2,typename T3,typename T4,typename=std::enable_if_t<COL==4&&vec_length<T1> ==ROW&&vec_length<T2> ==ROW&&vec_length<T3> ==ROW&&vec_length<T4> ==ROW>>
	MatType(const T1& a0, const T2& a1, const T3& a2, const T4& a3) {
		v[0]=VecType(a0); v[1]=VecType(a1); v[2]=VecType(a2); v[3]=VecType(a3);
	}
	template<typename T00, typename T01, typename T10, typename T11,
	typename=std::enable_if_t<COL==2&&ROW==2&&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T10>&&is_number_v<T11>>>
	MatType(T00 a00, T10 a10, T01 a01, T11 a11) {	// 2x2
		v[0][0]=T(a00); v[1][0]=T(a01);
		v[0][1]=T(a10); v[1][1]=T(a11);
	}
	template<typename T00, typename T01, typename T02, typename T10, typename T11, typename T12,
	typename=std::enable_if_t<((COL==3&&ROW==2)||(COL==2&&ROW==3))&&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T02>&&is_number_v<T10>&&is_number_v<T11>&&is_number_v<T12>>>
	MatType(T00 a00, T10 a10, T01 a01, T11 a11, T02 a02, T12 a12 ) {
		if constexpr ( COL==3 ) {									 // 3x2
			v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02);
			v[0][1]=T(a10); v[1][1]=T(a11); v[2][1]=T(a12);
		}
		else {														 // 2x3
			v[0][0]=T(a00); v[1][0]=T(a01);
			v[0][1]=T(a02); v[1][1]=T(a10);
			v[0][2]=T(a11); v[1][2]=T(a12);
		}
	}
	template<typename T00, typename T01, typename T02, typename T03, typename T10, typename T11, typename T12, typename T13,
	typename=std::enable_if_t<((COL==4&&ROW==2)||(COL==2&&ROW==4))&&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T02>&&is_number_v<T03>&&is_number_v<T10>&&is_number_v<T11>&&is_number_v<T12>&&is_number_v<T13>>>
	MatType(T00 a00, T10 a10, T01 a01, T11 a11, T02 a02, T12 a12, T03 a03, T13 a13 ) { // 4x2
		if constexpr ( COL==4 ) {
			v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02); v[3][0]=T(a03);
			v[0][1]=T(a10); v[1][1]=T(a11); v[2][1]=T(a12); v[3][1]=T(a13);
		}
		else {															// 2x4
			v[0][0]=T(a00); v[1][0]=T(a01);
			v[0][1]=T(a02); v[1][1]=T(a03);
			v[0][2]=T(a10); v[1][2]=T(a11);
			v[0][3]=T(a12); v[1][3]=T(a13);
		}
	}
	template<typename T00, typename T01, typename T02, typename T10, typename T11, typename T12, typename T20, typename T21, typename T22,
	typename=std::enable_if_t<COL==3&&ROW==3&&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T02>&&is_number_v<T10>&&is_number_v<T11>&&is_number_v<T12>&&is_number_v<T20>&&is_number_v<T21>&&is_number_v<T22>>>
	MatType(T00 a00, T10 a10, T20 a20, T01 a01, T11 a11, T21 a21, T02 a02, T12 a12, T22 a22 ) {	 // 3x3
		v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02);
		v[0][1]=T(a10); v[1][1]=T(a11); v[2][1]=T(a12);
		v[0][2]=T(a20); v[1][2]=T(a21); v[2][2]=T(a22);
	}
	template<typename T00, typename T01, typename T02, typename T03, typename T10, typename T11, typename T12, typename T13, typename T20, typename T21, typename T22, typename T23,
	typename=std::enable_if_t<((COL==4&&ROW==3)||(COL==3&&ROW==4))
	&&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T02>&&is_number_v<T03>
	&&is_number_v<T10>&&is_number_v<T11>&&is_number_v<T12>&&is_number_v<T13>
	&&is_number_v<T20>&&is_number_v<T21>&&is_number_v<T22>&&is_number_v<T23> >>
	MatType(T00 a00, T10 a10, T20 a20, T01 a01, T11 a11, T21 a21, T02 a02, T12 a12, T22 a22, T03 a03, T13 a13, T23 a23 ) {
		if constexpr ( COL==4 ) {												 // 4x3
			v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02); v[3][0]=T(a03);
			v[0][1]=T(a10); v[1][1]=T(a11); v[2][1]=T(a12); v[3][1]=T(a13);
			v[0][2]=T(a20); v[1][2]=T(a21); v[2][2]=T(a22); v[3][2]=T(a23);
		}
		else {																	// 3x4
			v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02);
			v[0][1]=T(a03); v[1][1]=T(a10); v[2][1]=T(a11);
			v[0][2]=T(a12); v[1][2]=T(a13); v[2][2]=T(a20);
			v[0][3]=T(a21); v[1][3]=T(a22); v[2][3]=T(a23);
		}
	}
	template<typename T00, typename T01, typename T02, typename T03, typename T10, typename T11, typename T12, typename T13, typename T20, typename T21, typename T22, typename T23, typename T30, typename T31, typename T32, typename T33,
	typename=std::enable_if_t<COL==4&&ROW==4
	&is_number_v<T00>&&is_number_v<T01>&&is_number_v<T02>&&is_number_v<T03>
	&is_number_v<T10>&&is_number_v<T11>&&is_number_v<T12>&&is_number_v<T13>
	&is_number_v<T20>&&is_number_v<T21>&&is_number_v<T22>&&is_number_v<T23>
	&is_number_v<T30>&&is_number_v<T31>&&is_number_v<T32>&&is_number_v<T33> >>
	MatType(T00 a00, T10 a10, T20 a20, T30 a30, T01 a01, T11 a11, T21 a21, T31 a31, T02 a02, T12 a12, T22 a22, T32 a32, T03 a03, T13 a13, T23 a23, T33 a33 ) { // 4x4
		v[0][0]=T(a00); v[1][0]=T(a01); v[2][0]=T(a02); v[3][0]=T(a03);
		v[0][1]=T(a10); v[1][1]=T(a11); v[2][1]=T(a12); v[3][1]=T(a13);
		v[0][2]=T(a20); v[1][2]=T(a21); v[2][2]=T(a22); v[3][2]=T(a23);
		v[0][3]=T(a30); v[1][3]=T(a31); v[2][3]=T(a32); v[3][3]=T(a33);
	}

	VecType& operator[] ( size_t i ) { return v[i]; }
	const VecType& operator[] ( size_t i ) const { return v[i]; }
	template<typename T2> MatType& operator += ( const MatType<T2,COL,ROW>& a ) { for(int i=0; i<COL; i++ ) v[i]+=a[i]; return *this; }
	template<typename T2> MatType& operator -= ( const MatType<T2,COL,ROW>& a ) { for(int i=0; i<COL; i++ ) v[i]-=a[i]; return *this; }
//	template<typename T2> MatType& operator *= ( const MatType<T2,COL,ROW>& a ) { for(int i=0; i<COL; i++ ) v[i]*=a[i]; return *this; }
//	template<typename T2> MatType& operator /= ( const MatType<T2,COL,ROW>& a ) { for(int i=0; i<COL; i++ ) v[i]/=a[i]; return *this; }
	
	template<typename T2,typename=std::enable_if_t<!is_vector_v<T2>>>
	MatType& operator += ( const T2& a ) {
		for(int i=0; i<COL; i++ ) v[i]+=a; return *this;
	}
	template<typename T2,typename=std::enable_if_t<!is_vector_v<T2>>>
	MatType& operator -= ( const T2& a ) {
		for(int i=0; i<COL; i++ ) v[i]-=a; return *this;
	}
	template<typename T2,typename=std::enable_if_t<!is_vector_v<T2>>>
	MatType& operator *= ( const T2& a ) {
		for(int i=0; i<COL; i++ ) v[i]*=a; return *this;
	}
	template<typename T2,typename=std::enable_if_t<!is_vector_v<T2>>>
	MatType& operator /= ( const T2& a ) {
		for(int i=0; i<COL; i++ ) v[i]/=a; return *this;
	}

};
#undef MatType

template<size_t C,size_t R> struct _elmt_< mmat_t <float  ,C,R>> : _type_<float> {};
template<size_t C,size_t R> struct _elmt_< mmat_t <double ,C,R>> : _type_<double>{};
template<size_t C,size_t R> struct _elmt_< mmat_t <bool   ,C,R>> : _type_<bool>  {};
template<size_t C,size_t R> struct _elmt_< mmat_t <char   ,C,R>> : _type_<char>  {};
template<size_t C,size_t R> struct _elmt_< mmat_t <uchar  ,C,R>> : _type_<uchar> {};
template<size_t C,size_t R> struct _elmt_< mmat_t <short  ,C,R>> : _type_<float> {};
template<size_t C,size_t R> struct _elmt_< mmat_t <ushort ,C,R>> : _type_<ushort>{};
template<size_t C,size_t R> struct _elmt_< mmat_t <int    ,C,R>> : _type_<int>   {};
template<size_t C,size_t R> struct _elmt_< mmat_t <uint   ,C,R>> : _type_<uint>  {};

template<typename A> 	struct _cols_: _cnt_<1>{};
template<typename A> 	struct _rows_: _cnt_<1>{};

template<typename T,size_t R> struct _rows_< _mvec_<T,R>> : _cnt_<R> {};
template<typename T,size_t C,size_t R> struct _cols_< mmat_t<T,C,R>> : _cnt_<C> {};
template<typename T,size_t C,size_t R> struct _rows_< mmat_t<T,C,R>> : _cnt_<R> {};
/*template<size_t C,size_t R> struct _cols_< mmat_t<float  ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<double ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<bool   ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<char   ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<uchar  ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<short  ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<ushort ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<int    ,C,R>> : _cnt_<C> {};
template<size_t C,size_t R> struct _cols_< mmat_t<uint   ,C,R>> : _cnt_<C> {};
*/

/*template<size_t C,size_t R> struct _rows_< mmat_t<float  ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<double ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<bool   ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<char   ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<uchar  ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<short  ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<ushort ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<int    ,C,R>> : _cnt_<R> {};
template<size_t C,size_t R> struct _rows_< mmat_t<uint   ,C,R>> : _cnt_<R> {};
*/



template<typename T, size_t C, size_t R> auto operator +(const mmat_t<T,C,R>& a, const mmat_t<T,C,R>& b ) { auto ret = a; ret+=b; return ret; }
template<typename T, size_t C, size_t R> auto operator -(const mmat_t<T,C,R>& a, const mmat_t<T,C,R>& b ) { auto ret = a; ret-=b; return ret; }
template<typename T, size_t C, size_t R> auto operator *(const mmat_t<T,C,R>& a, const mmat_t<T,R,C>& b ) {
	mmat_t<T,R,R> ret;
	for( int c=0; c<R; c++) for( int r=0; r<R; r++ ) {
		ret[c][r]=0;
		for( int d=0; d<C; d++) ret[c][r]+=a[d][r]*b[c][d];
	}
	return ret;
}
template<typename T, size_t C, size_t R> auto operator *(const mmat_t<T,C,R>& a, const vec_type_t<T,C>& b ) {
	vec_type_t<T,R> ret;
	for( int r=0; r<R; r++) {
		ret[r]=0;
		for( int d=0; d<C; d++) ret[r]+=a[d][r]*b[d];
	}
	return ret;
}
template<typename T, size_t C, size_t R> auto operator *(const vec_type_t<T,R>& b,const mmat_t<T,C,R>& a) {
	vec_type_t<T,C> ret;
	for( int c=0; c<C; c++) {
		ret[c]=0;
		for( int d=0; d<R; d++) ret[c]+=a[c][d]*b[d];
	}
	return ret;
}
template<typename T, size_t C, size_t R> auto operator *(const mmat_t<T,C,R>& a, T b ) { auto ret = a; ret*=b; return ret; }
template<typename T, size_t C, size_t R> auto operator /(const mmat_t<T,C,R>& a, T b ) { auto ret = a; ret/=b; return ret; }
template<typename T, size_t C, size_t R> auto operator *(T b, const mmat_t<T,C,R>& a ) { auto ret = a; ret*=b; return ret; }

template<typename T, size_t C, size_t R> auto transpose(const mmat_t<T,C,R>& a) {
	mmat_t<T,R,C> ret;
	for( int r=0; r<R; r++) for( int c=0; c<C; c++) {
		ret[r][c]=a[c][r];
	}
	return ret;
}

template<typename T, size_t C, size_t R> auto matrixCompMult(const mmat_t<T,C,R>& a, const mmat_t<T,C,R>& b ) {
	mmat_t<T,C,R> ret;
	for( int c=0; c<C; c++) {
		ret[c]=a[c]*b[c];
	}
	return ret;
}

template<typename T, size_t C, size_t R> auto outerProduct(const vec_type_t<T,R>& a, const vec_type_t<T,C>& b) {
	mmat_t<T,C,R> ret;
	for( int c=0; c<C; c++) for( int r=0; r<R; r++) ret[c][r] = a[r]*b[c];
	return ret;
}

template<typename T, size_t C> scalar_t determinant( const mmat_t<T,C,C>& a ) {
	if constexpr ( C==2 ) {
		return a[0][0]*a[1][1]
			-  a[0][1]*a[1][0];
	}
	else if constexpr (C==3) {
		return a[0][0]*( a[1][1]*a[2][2]-a[1][2]*a[2][1] )
			-  a[1][0]*( a[0][1]*a[2][2]-a[0][2]*a[2][1] )
			+  a[2][0]*( a[0][1]*a[1][2]-a[1][1]*a[0][2]);
	}
	else {
		return a[0][3]*a[1][2]*a[2][1]*a[3][0] - a[0][2]*a[1][3]*a[2][1]*a[3][0] - a[0][3]*a[1][1]*a[2][2]*a[3][0] + a[0][1]*a[1][3]*a[2][2]*a[3][0]
			+  a[0][2]*a[1][1]*a[2][3]*a[3][0] - a[0][1]*a[1][2]*a[2][3]*a[3][0] - a[0][3]*a[1][2]*a[2][0]*a[3][1] + a[0][2]*a[1][3]*a[2][0]*a[3][1]
			+  a[0][3]*a[1][0]*a[2][2]*a[3][1] - a[0][0]*a[1][3]*a[2][2]*a[3][1] - a[0][2]*a[1][0]*a[2][3]*a[3][1] + a[0][0]*a[1][2]*a[2][3]*a[3][1]
			+  a[0][3]*a[1][1]*a[2][0]*a[3][2] - a[0][1]*a[1][3]*a[2][0]*a[3][2] - a[0][3]*a[1][0]*a[2][1]*a[3][2] + a[0][0]*a[1][3]*a[2][1]*a[3][2]
			+  a[0][1]*a[1][0]*a[2][3]*a[3][2] - a[0][0]*a[1][1]*a[2][3]*a[3][2] - a[0][2]*a[1][1]*a[2][0]*a[3][3] + a[0][1]*a[1][2]*a[2][0]*a[3][3]
			+  a[0][2]*a[1][0]*a[2][1]*a[3][3] - a[0][0]*a[1][2]*a[2][1]*a[3][3] - a[0][1]*a[1][0]*a[2][2]*a[3][3] + a[0][0]*a[1][1]*a[2][2]*a[3][3];
	}
}
// inverse
template<typename T, size_t C> auto inverse( const mmat_t<T,C,C>& a ) {
	if constexpr ( C==2 ) {
		mmat_t<T,C,C> r;
		r[0][0] = a[1][1];
		r[0][1] =-a[0][1];
		r[1][0] =-a[1][0];
		r[1][1] = a[0][0];
		r/=determinant(a);
		return r;
	}
	else if constexpr (C==3) {
		mmat_t<T,3,3> r;
		r[0][0] = a[1][1]*a[2][2]-a[1][2]*a[2][1];
		r[0][1] =-a[0][1]*a[2][2]+a[0][2]*a[2][1];
		r[0][2] = a[0][1]*a[1][2]-a[0][2]*a[1][1];
		r[1][0] =-a[1][0]*a[2][2]+a[1][2]*a[2][0];
		r[1][1] = a[0][0]*a[2][2]-a[0][2]*a[2][0];
		r[1][2] =-a[0][0]*a[1][2]+a[0][2]*a[1][0];
		r[2][0] = a[1][0]*a[2][1]-a[1][1]*a[2][0];
		r[2][1] =-a[0][0]*a[2][1]+a[0][1]*a[2][0];
		r[2][2] = a[0][0]*a[1][1]-a[0][1]*a[1][0];
		r/=determinant(a);
		return r;
	}
	else {
		mmat_t<T,4,4> r;
		r[0][0] = a[1][2]*a[2][3]*a[3][1] - a[1][3]*a[2][2]*a[3][1] + a[1][3]*a[2][1]*a[3][2] - a[1][1]*a[2][3]*a[3][2] - a[1][2]*a[2][1]*a[3][3] + a[1][1]*a[2][2]*a[3][3];
		r[0][1] = a[0][3]*a[2][2]*a[3][1] - a[0][2]*a[2][3]*a[3][1] - a[0][3]*a[2][1]*a[3][2] + a[0][1]*a[2][3]*a[3][2] + a[0][2]*a[2][1]*a[3][3] - a[0][1]*a[2][2]*a[3][3];
		r[0][2] = a[0][2]*a[1][3]*a[3][1] - a[0][3]*a[1][2]*a[3][1] + a[0][3]*a[1][1]*a[3][2] - a[0][1]*a[1][3]*a[3][2] - a[0][2]*a[1][1]*a[3][3] + a[0][1]*a[1][2]*a[3][3];
		r[0][3] = a[0][3]*a[1][2]*a[2][1] - a[0][2]*a[1][3]*a[2][1] - a[0][3]*a[1][1]*a[2][2] + a[0][1]*a[1][3]*a[2][2] + a[0][2]*a[1][1]*a[2][3] - a[0][1]*a[1][2]*a[2][3];
		r[1][0] = a[1][3]*a[2][2]*a[3][0] - a[1][2]*a[2][3]*a[3][0] - a[1][3]*a[2][0]*a[3][2] + a[1][0]*a[2][3]*a[3][2] + a[1][2]*a[2][0]*a[3][3] - a[1][0]*a[2][2]*a[3][3];
		r[1][1] = a[0][2]*a[2][3]*a[3][0] - a[0][3]*a[2][2]*a[3][0] + a[0][3]*a[2][0]*a[3][2] - a[0][0]*a[2][3]*a[3][2] - a[0][2]*a[2][0]*a[3][3] + a[0][0]*a[2][2]*a[3][3];
		r[1][2] = a[0][3]*a[1][2]*a[3][0] - a[0][2]*a[1][3]*a[3][0] - a[0][3]*a[1][0]*a[3][2] + a[0][0]*a[1][3]*a[3][2] + a[0][2]*a[1][0]*a[3][3] - a[0][0]*a[1][2]*a[3][3];
		r[1][3] = a[0][2]*a[1][3]*a[2][0] - a[0][3]*a[1][2]*a[2][0] + a[0][3]*a[1][0]*a[2][2] - a[0][0]*a[1][3]*a[2][2] - a[0][2]*a[1][0]*a[2][3] + a[0][0]*a[1][2]*a[2][3];
		r[2][0] = a[1][1]*a[2][3]*a[3][0] - a[1][3]*a[2][1]*a[3][0] + a[1][3]*a[2][0]*a[3][1] - a[1][0]*a[2][3]*a[3][1] - a[1][1]*a[2][0]*a[3][3] + a[1][0]*a[2][1]*a[3][3];
		r[2][1] = a[0][3]*a[2][1]*a[3][0] - a[0][1]*a[2][3]*a[3][0] - a[0][3]*a[2][0]*a[3][1] + a[0][0]*a[2][3]*a[3][1] + a[0][1]*a[2][0]*a[3][3] - a[0][0]*a[2][1]*a[3][3];
		r[2][2] = a[0][1]*a[1][3]*a[3][0] - a[0][3]*a[1][1]*a[3][0] + a[0][3]*a[1][0]*a[3][1] - a[0][0]*a[1][3]*a[3][1] - a[0][1]*a[1][0]*a[3][3] + a[0][0]*a[1][1]*a[3][3];
		r[2][3] = a[0][3]*a[1][1]*a[2][0] - a[0][1]*a[1][3]*a[2][0] - a[0][3]*a[1][0]*a[2][1] + a[0][0]*a[1][3]*a[2][1] + a[0][1]*a[1][0]*a[2][3] - a[0][0]*a[1][1]*a[2][3];
		r[3][0] = a[1][2]*a[2][1]*a[3][0] - a[1][1]*a[2][2]*a[3][0] - a[1][2]*a[2][0]*a[3][1] + a[1][0]*a[2][2]*a[3][1] + a[1][1]*a[2][0]*a[3][2] - a[1][0]*a[2][1]*a[3][2];
		r[3][1] = a[0][1]*a[2][2]*a[3][0] - a[0][2]*a[2][1]*a[3][0] + a[0][2]*a[2][0]*a[3][1] - a[0][0]*a[2][2]*a[3][1] - a[0][1]*a[2][0]*a[3][2] + a[0][0]*a[2][1]*a[3][2];
		r[3][2] = a[0][2]*a[1][1]*a[3][0] - a[0][1]*a[1][2]*a[3][0] - a[0][2]*a[1][0]*a[3][1] + a[0][0]*a[1][2]*a[3][1] + a[0][1]*a[1][0]*a[3][2] - a[0][0]*a[1][1]*a[3][2];
		r[3][3] = a[0][1]*a[1][2]*a[2][0] - a[0][2]*a[1][1]*a[2][0] + a[0][2]*a[1][0]*a[2][1] - a[0][0]*a[1][2]*a[2][1] - a[0][1]*a[1][0]*a[2][2] + a[0][0]*a[1][1]*a[2][2];
		r/=determinant(a);
		return r;
	}
}
/*
template<> inline mmat_t<float ,2,2>::mmat_t(float  a) { for( int i=0; i<2; i++ ) { v[i]= vec2(0); v[i][i]=a; } }
template<> inline mmat_t<float ,3,3>::mmat_t(float  a) { for( int i=0; i<3; i++ ) { v[i]= vec3(0); v[i][i]=a; } }
template<> inline mmat_t<float ,4,4>::mmat_t(float  a) { for( int i=0; i<4; i++ ) { v[i]= vec4(0); v[i][i]=a; } }
template<> inline mmat_t<double,2,2>::mmat_t(double a) { for( int i=0; i<2; i++ ) { v[i]=dvec2(0); v[i][i]=a; } }
template<> inline mmat_t<double,3,3>::mmat_t(double a) { for( int i=0; i<3; i++ ) { v[i]=dvec3(0); v[i][i]=a; } }
template<> inline mmat_t<double,4,4>::mmat_t(double a) { for( int i=0; i<4; i++ ) { v[i]=dvec4(0); v[i][i]=a; } }
*/
template<typename T,size_t C, size_t R> template<typename T1,typename> mmat_t<T,C,R>::mmat_t(const T1& a) {
	using VecType = vec_type_t<T,R>;
	if constexpr ( _rows_<T1>::n ==1 && _cols_<T1>::n ==1 ) {				// is scalar
		if constexpr (C == R) {										// square matrix
			for( int i=0; i<C; i++ ) { v[i]= VecType(0); v[i][i]=a; }
		}
		else {														// non-square matrix
			for( int i=0; i<C; i++ ) v[i]=VecType(a);
		}
	}
	else {															// matrix
		for( int i=0; i<C; i++ ) for( int j=0; j<R; j++ ) {
			if( j < _rows_<T1>::n && i < _cols_<T1>::n ) v[i][j] = a[i][j];
			else if( i==j ) v[i][j] = 1;
			else v[i][j] = 0;
		}
	}
}


typedef mmat_t<float,2,2> mat2;
typedef mmat_t<float,3,3> mat3;
typedef mmat_t<float,4,4> mat4;
typedef mmat_t<float,2,2> mat2x2;
typedef mmat_t<float,2,3> mat2x3;
typedef mmat_t<float,2,4> mat2x4;
typedef mmat_t<float,3,2> mat3x2;
typedef mmat_t<float,3,3> mat3x3;
typedef mmat_t<float,3,4> mat3x4;
typedef mmat_t<float,4,2> mat4x2;
typedef mmat_t<float,4,3> mat4x3;
typedef mmat_t<float,4,4> mat4x4;

typedef mmat_t<double,2,2> dmat2;
typedef mmat_t<double,3,3> dmat3;
typedef mmat_t<double,4,4> dmat4;
typedef mmat_t<double,2,2> dmat2x2;
typedef mmat_t<double,2,3> dmat2x3;
typedef mmat_t<double,2,4> dmat2x4;
typedef mmat_t<double,3,2> dmat3x2;
typedef mmat_t<double,3,3> dmat3x3;
typedef mmat_t<double,3,4> dmat3x4;
typedef mmat_t<double,4,2> dmat4x2;
typedef mmat_t<double,4,3> dmat4x3;
typedef mmat_t<double,4,4> dmat4x4;

template<> inline float* value_ptr<mat2>  (mat2& a)   { return (float*)a.v; }
template<> inline float* value_ptr<mat3>  (mat3& a)   { return (float*)a.v; }
template<> inline float* value_ptr<mat4>  (mat4& a)   { return (float*)a.v; }
template<> inline float* value_ptr<mat2x3>(mat2x3& a) { return (float*)a.v; }
template<> inline float* value_ptr<mat2x4>(mat2x4& a) { return (float*)a.v; }
template<> inline float* value_ptr<mat3x2>(mat3x2& a) { return (float*)a.v; }
template<> inline float* value_ptr<mat3x4>(mat3x4& a) { return (float*)a.v; }
template<> inline float* value_ptr<mat4x2>(mat4x2& a) { return (float*)a.v; }
template<> inline float* value_ptr<mat4x3>(mat4x3& a) { return (float*)a.v; }

template<> inline double* value_ptr<dmat2>  (dmat2& a)   { return (double*)a.v; }
template<> inline double* value_ptr<dmat3>  (dmat3& a)   { return (double*)a.v; }
template<> inline double* value_ptr<dmat4>  (dmat4& a)   { return (double*)a.v; }
template<> inline double* value_ptr<dmat2x3>(dmat2x3& a) { return (double*)a.v; }
template<> inline double* value_ptr<dmat2x4>(dmat2x4& a) { return (double*)a.v; }
template<> inline double* value_ptr<dmat3x2>(dmat3x2& a) { return (double*)a.v; }
template<> inline double* value_ptr<dmat3x4>(dmat3x4& a) { return (double*)a.v; }
template<> inline double* value_ptr<dmat4x2>(dmat4x2& a) { return (double*)a.v; }
template<> inline double* value_ptr<dmat4x3>(dmat4x3& a) { return (double*)a.v; }

template<> const inline float* value_ptr (const mat2& a)   { return (float*)a.v; }
template<> const inline float* value_ptr (const mat3& a)   { return (float*)a.v; }
template<> const inline float* value_ptr (const mat4& a)   { return (float*)a.v; }
template<> const inline float* value_ptr (const mat2x3& a) { return (float*)a.v; }
template<> const inline float* value_ptr (const mat2x4& a) { return (float*)a.v; }
template<> const inline float* value_ptr (const mat3x2& a) { return (float*)a.v; }
template<> const inline float* value_ptr (const mat3x4& a) { return (float*)a.v; }
template<> const inline float* value_ptr (const mat4x2& a) { return (float*)a.v; }
template<> const inline float* value_ptr (const mat4x3& a) { return (float*)a.v; }

template<> const inline double* value_ptr(const dmat2& a)   { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat3& a)   { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat4& a)   { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat2x3& a) { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat2x4& a) { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat3x2& a) { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat3x4& a) { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat4x2& a) { return (double*)a.v; }
template<> const inline double* value_ptr(const dmat4x3& a) { return (double*)a.v; }


} // namespace jm
#endif /* jm_mat_h */
