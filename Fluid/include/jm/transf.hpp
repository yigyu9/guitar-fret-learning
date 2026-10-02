//
//  transf.hpp
//  SystemCalib
//
//  Created by Hyun Joon Shin on 2023/08/25.
//

#ifndef transf_h
#define transf_h

#include "mat.hpp"

namespace jm {

template<typename T, typename=std::enable_if_t< is_length_v<T, 3> && is_floatd_v<T>> >
auto translate( const T& v ) {
	using elmType = vec_element<T>;
	mmat_t<elmType,4,4> ret(1);
	ret[3]=mvec4_t<elmType>(v,1);
	return ret;
}

template<typename T0, typename T,typename=std::enable_if_t< is_length_v<T, 3> && is_floatd_v<T>>>
auto translate( const mmat_t<T0,4,4>& m, const T& v ) {
	mmat_t<T0,4,4> ret = m;
	ret[3] = m[0] * v[0] + m[1] * v[1] + m[2] * v[2] + m[3];
	return ret;
}

template<typename T0, typename T,typename=std::enable_if_t< !is_vector_v<T0> && is_length_v<T, 3> && is_floatd_v<T>>>
auto rotate( T0 angle, const T& v ) {
	using scalar = vec_element<T>;
	mmat_t<scalar,4,4> r(0);
	const scalar a = scalar(angle);
	const scalar c = scalar(cos(a));
	const scalar s = scalar(sin(a));

	vec3 axis(normalize(v));
	vec3 temp((1.f - c) * axis);
	
	r[0][0] = c + temp[0] * axis[0];
	r[0][1] = temp[0] * axis[1] + s * axis[2];
	r[0][2] = temp[0] * axis[2] - s * axis[1];
	
	r[1][0] = temp[1] * axis[0] - s * axis[2];
	r[1][1] = c + temp[1] * axis[1];
	r[1][2] = temp[1] * axis[2] + s * axis[0];
	
	r[2][0] = temp[2] * axis[0] + s * axis[1];
	r[2][1] = temp[2] * axis[1] - s * axis[0];
	r[2][2] = c + temp[2] * axis[2];
	r[3][3] = 1;
	
	return r;
}

template<typename T,typename=std::enable_if_t< is_length_v<T, 3> && is_floatd_v<T>>>
auto rotate( const T& v) {
	return rotate( length(v), normalize(v) );
}

template<typename T0, typename T,typename=std::enable_if_t< !is_vector_v<T0> && is_length_v<T, 3> && is_floatd_v<T>>>
auto rotate( const mmat_t<T0,4,4>& m, float angle, const T& v ) {
	using scalar = vec_element<T>;
	mmat_t<T0,4,4> ret(1), r;
	const scalar a = angle;
	const scalar c = scalar(::cos(double(a)));
	const scalar s = scalar(::sin(double(a)));
	
	mvec3_t<scalar> axis(normalize(v));
	mvec3_t<scalar> temp((scalar(1) - c) * axis);
	
	r[0][0] = c + temp[0] * axis[0];
	r[0][1] = temp[0] * axis[1] + s * axis[2];
	r[0][2] = temp[0] * axis[2] - s * axis[1];
	
	r[1][0] = temp[1] * axis[0] - s * axis[2];
	r[1][1] = c + temp[1] * axis[1];
	r[1][2] = temp[1] * axis[2] + s * axis[0];
	
	r[2][0] = temp[2] * axis[0] + s * axis[1];
	r[2][1] = temp[2] * axis[1] - s * axis[0];
	r[2][2] = c + temp[2] * axis[2];
	
	ret[0] = m[0] * r[0][0] + m[1] * r[0][1] + m[2] * r[0][2];
	ret[1] = m[0] * r[1][0] + m[1] * r[1][1] + m[2] * r[1][2];
	ret[2] = m[0] * r[2][0] + m[1] * r[2][1] + m[2] * r[2][2];
	ret[3] = m[3];
	return ret;
}

template<typename T0, typename T,typename=std::enable_if_t< !is_vector_v<T0> && is_length_v<T, 3> && is_floatd_v<T>>>
auto rotate( const mmat_t<T0,4,4>& m, const T& v) {
	return rotate( m, length(v), normalize(v) );
}

template<typename T,typename=std::enable_if_t< is_length_v<T, 3> && is_floatd_v<T>>>
auto scale( const T& v ) {
	return mmat_t<vec_element<T>,4,4>(v[0],0,0,0, 0,v[1],0,0, 0,0,v[2],0, 0,0,0,1);
}

template<typename T0, typename T,typename=std::enable_if_t< !is_vector_v<T0> && is_length_v<T, 3> && is_floatd_v<T>>>
auto scale( const mmat_t<T0,4,4>& m, const T& v ) {
	mmat_t<T0,4,4> ret;
	ret[0] = m[0] * v[0];
	ret[1] = m[1] * v[1];
	ret[2] = m[2] * v[2];
	ret[3] = m[3];
	return ret;
}

template<typename T0, typename T1, typename T2, typename T3, typename T4, typename T5>
auto frustum(T0 left, T1 right, T2 bottom, T3 top, T4 zNear, T5 zFar) {
	using scalar = float;
	const scalar l=scalar(left);
	const scalar r=scalar(right);
	const scalar b=scalar(bottom);
	const scalar t=scalar(top);
	const scalar n=scalar(zNear);
	const scalar f=scalar(zFar);
	
	return mat4(scalar(2)*n/(r-l), 0, 0, 0,
				0, scalar(2)*n/(t-b), 0, 0,
				(r+l)/(r-l),(t+b)/(t-b), -(f+n)/(f-n), -1,
				0, 0, -scalar(2)*f*n/(f-n), 0);
}

template<typename T0, typename T1, typename T2, typename T3, typename T4, typename T5>
auto ortho(T0 left, T1 right, T2 bottom, T3 top, T4 zNear, T5 zFar) {
	using scalar = float;
	const scalar l=scalar(left);
	const scalar r=scalar(right);
	const scalar b=scalar(bottom);
	const scalar t=scalar(top);
	const scalar n=scalar(zNear);
	const scalar f=scalar(zFar);

	return mat4(scalar(2)/(l-r), 0, 0, 0,
				0, scalar(2)/(t-b), 0, 0,
				0, 0,-scalar(2)/(f-n), 0,
				-(r+l)/(l-r), -(t+b)/(t-b), -(f+n)/(f-n), 1 );
}

template<typename T0, typename T1, typename T2, typename=std::enable_if_t<is_length_v<T0,3> && is_length_v<T1,3> && is_length_v<T2,3>>>
auto lookAt(T0 const& eye, T1 const& center, T2 const& up) {
	using scalar = std::common_type_t<vec_element<T2>,vec_element<T1>,vec_element<T0>,float>;
	mvec3_t<scalar> f = normalize( center - eye );
	mvec3_t<scalar> U = normalize( up );
	mvec3_t<scalar> s = normalize( cross( f, U ) );
	mvec3_t<scalar> u = cross( s, f );
	return mmat_t<scalar,4,4>(s[0],u[0],-f[0],0,
							  s[1],u[1],-f[1],0,
							  s[2],u[2],-f[2],0,
							  0,0,0,1) * translate(-eye);
}

template<typename T0, typename T1, typename T2, typename T3, typename T4, typename T5, typename T6, typename T7, typename T8>
auto lookAt(T0 eyeX, T1 eyeY, T2 eyeZ, T3 centerX, T4 centerY, T5 centerZ, T6 upX, T7 upY, T8 upZ ) {
	return lookAt( vec3(eyeX,eyeY,eyeZ), vec3(centerX,centerY,centerZ), vec3(upX,upY,upZ) );
}

template<typename T0, typename T1, typename T2, typename T3>
auto ortho2D(T0 left, T1 right, T2 bottom, T3 top) {
	return ortho(left,right,bottom,top,-1,1);
}

template<typename T0, typename T1, typename T2, typename T3>
auto perspective(T0 fovy, T1 aspect, T2 zNear, T3 zFar) {
	using scalar = float;
	const scalar F = 1/::tan(scalar(fovy)/2);
	const scalar a = scalar(aspect);
	const scalar n = scalar(zNear);
	const scalar f = scalar(zFar);
	return mmat_t<scalar,4,4>(F/a,0,0,0,
							  0,F,0,0,
							  0,0,(f+n)/(n-f),-1,
							  0,0,2*f*n/(n-f),0);
}



/*
glm::mat4 pickMatrix(glm::vec2 const& center, glm::vec2 const& delta, glm::ivec4 const& viewport);
glm::dmat4 pickMatrix(glm::dvec2 const& center, glm::dvec2 const& delta, glm::ivec4 const& viewport);

glm::vec3 project(glm::vec3 const& obj, glm::mat4 const& model, glm::mat4 const& proj, glm::ivec4 const& viewport);
glm::dvec3 project(glm::dvec3 const& obj, glm::dmat4 const& model, glm::dmat4 const& proj, glm::ivec4 const& viewport);

glm::vec3 unProject(glm::vec3 const& win, glm::mat4 const& model, glm::mat4 const& proj, glm::ivec4 const& viewport);
glm::dvec3 unProject(glm::dvec3 const& win, glm::dmat4 const& model, glm::dmat4 const& proj, glm::ivec4 const& viewport);
 
 */


} // namespace jm

#endif

