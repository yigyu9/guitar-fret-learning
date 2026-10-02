//
//  vecn.hpp
//  TextileMeasure
//
//  Created by Hyun Joon Shin on 2/28/25.
//

#ifndef vecn_hpp
#define vecn_hpp

#include <cassert>
#include <stdexcept>
#include <vector>

namespace jm {

template<typename T> struct vector_t;
template<typename T> struct vector_op_t {
	size_t n;
	inline vector_op_t( size_t nn): n(nn) {}
	virtual inline T operator()(size_t i) const = 0;
	virtual inline T operator[](size_t i) const { return (*this)(i); }
	inline const vector_op_t<T>& operator - ()    const;
	inline const vector_op_t<T>& operator + (T s) const;
	inline const vector_op_t<T>& operator - (T s) const;
	inline const vector_op_t<T>& operator * (T s) const;
	inline const vector_op_t<T>& operator / (T s) const;
	
	friend inline const vector_op_t<T>& operator + (T s,const vector_op_t<T>& m);
	friend inline const vector_op_t<T>& operator - (T s,const vector_op_t<T>& m);
	friend inline const vector_op_t<T>& operator * (T s,const vector_op_t<T>& m);
	friend inline const vector_op_t<T>& operator / (T s,const vector_op_t<T>& m);

	inline const vector_op_t<T>& operator + (const vector_t<T>& m) const;
	inline const vector_op_t<T>& operator - (const vector_t<T>& m) const;
	inline const vector_op_t<T>& operator * (const vector_t<T>& m) const;
	inline const vector_op_t<T>& operator / (const vector_t<T>& m) const;
	inline T operator % (const vector_t<T>& m) const;

	inline const vector_op_t<T>& operator + (const vector_op_t<T>& m) const;
	inline const vector_op_t<T>& operator - (const vector_op_t<T>& m) const;
	inline const vector_op_t<T>& operator * (const vector_op_t<T>& m) const;
	inline const vector_op_t<T>& operator / (const vector_op_t<T>& m) const;
	inline T operator % (const vector_op_t<T>& m) const;
	inline virtual ~vector_op_t() {}
};

template<typename T> struct vector_op_vector_t : vector_op_t<T> {
	const vector_t<T>& v;
	inline vector_op_vector_t(const vector_t<T>& vv):vector_op_t<T>(vv.n),v(vv){}
	inline virtual ~vector_op_vector_t() {}
	inline virtual T operator()(size_t i) const override;
};
template<typename T> struct vector_op_neg_t : vector_op_t<T> {
	const vector_op_t<T>& v;
	inline vector_op_neg_t(const vector_op_t<T>& vv):vector_op_t<T>(vv.n),v(vv){}
	inline virtual ~vector_op_neg_t() { delete &v; }
	inline virtual T operator()(size_t i) const override{ return -v(i); };
};


template<typename T> struct vector_op_v_s_t : vector_op_t<T> {
	const vector_op_t<T>& v; T s;
	inline vector_op_v_s_t(const vector_op_t<T>& vv, T ss)
		:vector_op_t<T>(vv.n),v(vv), s(ss){}
	inline virtual ~vector_op_v_s_t() { delete &v; }
};
template<typename T> struct vector_op_add_v_s_t: vector_op_v_s_t<T> {
	inline vector_op_add_v_s_t(const vector_op_t<T>& vv, T ss): vector_op_v_s_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_v_s_t<T>::v(i)+vector_op_v_s_t<T>::s; }
};
template<typename T> struct vector_op_sub_v_s_t: vector_op_v_s_t<T> {
	inline vector_op_sub_v_s_t(const vector_op_t<T>& vv, T ss): vector_op_v_s_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_v_s_t<T>::v(i)-vector_op_v_s_t<T>::s; }
};
template<typename T> struct vector_op_mul_v_s_t: vector_op_v_s_t<T> {
	inline vector_op_mul_v_s_t(const vector_op_t<T>& vv, T ss): vector_op_v_s_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_v_s_t<T>::v(i)*vector_op_v_s_t<T>::s; }
};
template<typename T> struct vector_op_div_v_s_t: vector_op_v_s_t<T> {
	inline vector_op_div_v_s_t(const vector_op_t<T>& vv, T ss): vector_op_v_s_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_v_s_t<T>::v(i)/vector_op_v_s_t<T>::s; }
};


template<typename T> struct vector_op_s_v_t {
	const vector_op_t<T>& v; T s;
	inline vector_op_s_v_t(T ss,const vector_op_t<T>& vv)
		:vector_op_t<T>(vv.n),v(vv), s(ss){}
	inline virtual ~vector_op_s_v_t() { delete &v; }
};
template<typename T> struct vector_op_sub_s_v_t: vector_op_s_v_t<T> {
	inline vector_op_sub_s_v_t(T ss,const vector_op_t<T>& vv): vector_op_s_v_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_s_v_t<T>::s-vector_op_s_v_t<T>::v(i); }
};
template<typename T> struct vector_op_div_s_v_t: vector_op_s_v_t<T> {
	inline vector_op_div_s_v_t(T ss,const vector_op_t<T>& vv): vector_op_s_v_t<T>(vv,ss){}
	inline virtual T operator()(size_t i)const override{ return vector_op_s_v_t<T>::s/vector_op_s_v_t<T>::v(i); }
};


template<typename T> struct vector_op_v_v_t : vector_op_t<T> {
	const vector_op_t<T> &v1, &v2;
	inline vector_op_v_v_t(const vector_op_t<T>& vv1, const vector_op_t<T>& vv2)
		:vector_op_t<T>(vv1.n),v1(vv1),v2(vv2){ assert( vv1.n == vv2.n ); }
	inline virtual ~vector_op_v_v_t() { delete &v1; delete &v2; }
};
template<typename T> struct vector_op_add_v_v_t : vector_op_v_v_t<T> {
	inline vector_op_add_v_v_t(const vector_op_t<T>& vv1, const vector_op_t<T>& vv2): vector_op_v_v_t<T>(vv1,vv2){}
	inline virtual T operator()(size_t i) const override{ return vector_op_v_v_t<T>::v1(i)+vector_op_v_v_t<T>::v2(i); }
};
template<typename T> struct vector_op_sub_v_v_t : vector_op_v_v_t<T> {
	inline vector_op_sub_v_v_t(const vector_op_t<T>& vv1, const vector_op_t<T>& vv2): vector_op_v_v_t<T>(vv1,vv2){}
	inline virtual T operator()(size_t i) const override{ return vector_op_v_v_t<T>::v1(i)-vector_op_v_v_t<T>::v2(i); }
};
template<typename T> struct vector_op_mul_v_v_t : vector_op_v_v_t<T> {
	inline vector_op_mul_v_v_t(const vector_op_t<T>& vv1, const vector_op_t<T>& vv2): vector_op_v_v_t<T>(vv1,vv2){}
	inline virtual T operator()(size_t i) const override{ return vector_op_v_v_t<T>::v1(i)*vector_op_v_v_t<T>::v2(i); }
};
template<typename T> struct vector_op_div_v_v_t : vector_op_v_v_t<T> {
	inline vector_op_div_v_v_t(const vector_op_t<T>& vv1, const vector_op_t<T>& vv2): vector_op_v_v_t<T>(vv1,vv2){}
	inline virtual T operator()(size_t i) const override{ return vector_op_v_v_t<T>::v1(i)/vector_op_v_v_t<T>::v2(i); }
};


template<typename T> struct vector_t {
	//! The length of the vector
	size_t n=0;
	//! brief The data array
	T* data = nullptr;
	
	//! Indicating the memory (\ref data) is allocated by itself.
	//!  It is false either when the meomry is moved to other vector via move operator
	//!  or it is wrapping the memory allocated by other part such as matrix row.
	bool alloced = true;

	//! Creating a vector wrapping an array provided by other part, such as matrix row.
	//! Caution: Be careful not to delete (free) memory while the returned vector alive.
	//! param n size of the vector
	//! param v pointer of the array to wrap
	static inline vector_t<T> wrap(size_t n, T* v) {
		vector_t<T> ret;
		ret.n = n;
		ret.data = v;
		ret.alloced = false;
		return ret;
	}

	//************** Constructors
	//! Default constructor.
	//! Constructing an empty vector.
	inline vector_t(): n(0), alloced(true), data(nullptr) {}
	//! Copy constructor
	//! param v the vector to copy
	inline vector_t(const vector_t& v): vector_t(v.n,v.data) {}
	//! (Internal) Move constructor
	//! param v the vector to move
	inline vector_t(vector_t&& v): n(v.n),data(v.data),alloced(v.alloced) { v.data = nullptr; v.alloced = false; }
	//! (Internal) Copy constructor from a \ref vector_op_t
	//! param v the vector to copy
	inline vector_t(const vector_op_t<T>& v): vector_t(v.n) {
		for( size_t i=0; i<n; i++ ) data[i] = v(i);
		delete &v;
	}

	
	
	//! Vector constructor with the size
	//! Constructing a vector of the given size. The data is not initialized.
	//! param n size of the vector
	inline vector_t(size_t n_) { resize(n_); }
	//! Vector constructor with the size
	//! Constructing a vector of the given size. All element is initialized with the given value.
	//! Ex. vector_t<float> v(3,0); yields a zero-vector of size 3.
	//! param n size of the vector.
	//! param v initial value.
	inline vector_t(size_t n_, T v):vector_t(n_) { for( size_t i=0; i<n; i++ ) data[i]=v; }

	//! Creating a vector and copy the data
	//! param n size of the vector
	//! param v pointer of the array to copy
	inline vector_t(size_t n_, const T* v): vector_t(n_) { for( size_t i=0; i<n; i++) data[i] = v[i]; }
	//! Creating a vector wrapping the array.
	//! param n size of the vector
	//! param v pointer of the array to wrap.
	inline vector_t(size_t n_, T* v): n(n_), data(v), alloced(false) {}

	//! Creating a vector and copy the data.  Ex. vector_t<float> v({1,2,3,4});
	//! param v std::vector containing the data.
	inline vector_t(const std::vector<T>& v): vector_t(v.size(),v.data()) {}
	//! Creating a vector and copy the data. Ex. vector_t<float> v = {1,2,3,4};
	//! param v std::initializer_list to copy.
	inline vector_t(const std::initializer_list<T>& l) {
		resize(l.size());
		int i=0; for( auto v: l ) data[i++] = v;
	}
	
	//************** Memory management functions
	//! Deallocating the memory and setting the size to zero.
	inline void free(){
		if( alloced && data ) delete [] data;
		data = nullptr;
		alloced = false;
		n = 0;
	}
	//! Resizing the vector.
	//! When the current size is the same as the target size, the vector is untouched.
	inline void resize(size_t n_) {
		if( n==n_ ) return;
		if( alloced && data ) delete [] data;
		n = n_;
		data = new T[n];
		alloced = true;
	}

	//************** Copy & move operators
	//! (Internal) Copy operator
	//! Note that when the lengthes mismatch, it automatically resizes the left-hand side vector.
	//! However, when the vector is wrapping, the size must matches.
	inline vector_t& operator = (const vector_t& v) {
		if( !alloced ) assert( n == v.n );
		resize(v.n);
		for( size_t i=0; i<n; i++ ) data[i] = v.data[i];
		return *this;
	}
	//! (Internal) Move operator
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = (vector_t&& v){
		free();
		n = v.n;
		data = v.data;
		alloced = v.alloced;
		v.data = nullptr;
		v.alloced = false;
		return *this;
	}
	//! (Internal) Copy operator
	//! Note that when the lengthes mismatch, it automatically resizes the left-hand side vector.
	//! However, when the vector is wrapping, the size must matches.
	inline vector_t& operator = (const vector_op_t<T>& v) {
		if( !alloced ) assert( n == v.n );
		resize(v.n);
		for( size_t i=0; i<n; i++ ) data[i] = v(i);
		delete &v;
		return *this;
	}

	inline vector_t& operator = (const std::vector<T>& v) {
		if( !alloced ) assert( n == v.size() );
		resize(v.size());
		for( size_t i=0; i<n; i++ ) data[i] = v.data[i];
		return *this;
	}
	inline vector_t& operator = (const std::tuple<size_t,const T*> v) {
		if( !alloced ) assert( n == std::get<0>(v) );
		resize(std::get<0>(v));
		T* d = std::get<1>(v);
		for( size_t i=0; i<n; i++ ) data[i] = d[i];
		return *this;
	}
	inline vector_t& operator = (const std::tuple<int,const T*> v) {
		*this = std::make_tuple(size_t(std::get<0>(v)),std::get<1>(v));
		return *this;
	}
	inline vector_t& operator = (const std::initializer_list<T>& l) {
		if( !alloced ) assert( n == l.size() );
		resize(l.size());
		int i=0; for( auto v: l ) data[i++] = v;
	}

	
	//! Destructor
	inline virtual ~vector_t() {
		free();
	}
	//************** Element access function
	//! Element access
	inline T& operator () ( size_t k ) {
		return data[k];
	}
	//! Element access
	inline const T& operator () ( size_t k ) const {
		return data[k];
	}
	//! Element access
	inline T& operator [] ( size_t k ) {
		return data[k];
	}
	//! Element access
	inline const T& operator [] ( size_t k ) const {
		return data[k];
	}
	
	//************** Combination assignment operators
	//! Addition combination assignment operator. The scalar value is to be added to each element.
	inline vector_t<T>& operator += (T s) { for(auto i=0; i<n; i++) (*this)(i)+=s; return *this; }
	//! Subtraction combination assignment operator. The scalar value is to be subtracted from each element.
	inline vector_t<T>& operator -= (T s) { for(auto i=0; i<n; i++) (*this)(i)-=s; return *this; }
	//! Scalar-multiplication combination assignment operator.
	inline vector_t<T>& operator *= (T s) { for(auto i=0; i<n; i++) (*this)(i)*=s; return *this; }
	//! Division combination assignment operator.
	inline vector_t<T>& operator /= (T s) { for(auto i=0; i<n; i++) (*this)(i)/=s; return *this; }

	//! Addition combination assignment operator
	inline vector_t<T>& operator += (const vector_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)+=v(i); return *this; }
	//! Subtraction combination assignment operator
	inline vector_t<T>& operator -= (const vector_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)-=v(i); return *this; }
	//! Element-wise multiplication combination assignment operator
	inline vector_t<T>& operator *= (const vector_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)*=v(i); return *this; }
	//! Element-wise division combination assignment operator
	inline vector_t<T>& operator /= (const vector_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)/=v(i); return *this; }

	//! Addition combination assignment operator
	inline vector_t<T>& operator += (const vector_op_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)+=v(i); delete &v; return *this; }
	//! Subtraction combination assignment operator
	inline vector_t<T>& operator -= (const vector_op_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)-=v(i); delete &v; return *this; }
	//! Element-wise multiplication combination assignment operator
	inline vector_t<T>& operator *= (const vector_op_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)*=v(i); delete &v; return *this; }
	//! Element-wise division combinationassignment  operator
	inline vector_t<T>& operator /= (const vector_op_t<T>& v) { assert(n==v.n); for(auto i=0; i<n; i++) (*this)(i)/=v(i); delete &v; return *this; }

	//************** Arithmatic operators
	//! Negation operator.
	inline const vector_op_t<T>& operator - ()    const { return *(new vector_op_neg_t    <T>(*new vector_op_vector_t<T>(*this))); }
	//! Addition operator. The scalar value is to be added to each element.
	inline const vector_op_t<T>& operator + (T s) const { return *(new vector_op_add_v_s_t<T>(*new vector_op_vector_t<T>(*this),s)); }
	//! Addition operator. The scalar value is to be subtracted from each element.
	inline const vector_op_t<T>& operator - (T s) const { return *(new vector_op_sub_v_s_t<T>(*new vector_op_vector_t<T>(*this),s)); }
	//! Vector-scalar multiplication operator.
	inline const vector_op_t<T>& operator * (T s) const { return *(new vector_op_mul_v_s_t<T>(*new vector_op_vector_t<T>(*this),s)); }
	//! Vector-scalar division operator.
	inline const vector_op_t<T>& operator / (T s) const { return *(new vector_op_div_v_s_t<T>(*new vector_op_vector_t<T>(*this),s)); }
	//! Addition operator. The scalar value is to be added to each element.
	inline friend vector_op_t<T>& operator + (T s,const vector_t<T>& v) { return *(new vector_op_add_v_s_t<T>(*new vector_op_vector_t<T>(v),s)); }
	//! Subtraction operator. Each element is subtracted to the scalar value.
	inline friend vector_op_t<T>& operator - (T s,const vector_t<T>& v) { return *(new vector_op_sub_s_v_t<T>(s,*new vector_op_vector_t<T>(v))); }
	//! Vector-scalar multiplication operator.
	inline friend vector_op_t<T>& operator * (T s,const vector_t<T>& v) { return *(new vector_op_mul_v_s_t<T>(*new vector_op_vector_t<T>(v),s)); }
	//! Vector-scalar division operator. The scalar value is divided by each element.
	inline friend vector_op_t<T>& operator / (T s,const vector_t<T>& v) { return *(new vector_op_div_s_v_t<T>(s,*new vector_op_vector_t<T>(v))); }

	//! Addition operator.
	inline const vector_op_t<T>& operator + (const vector_t<T>& v) const { return *(new vector_op_add_v_v_t<T>(*new vector_op_vector_t<T>(*this),*new vector_op_vector_t<T>(v))); }
	//! Subtraction operator.
	inline const vector_op_t<T>& operator - (const vector_t<T>& v) const { return *(new vector_op_sub_v_v_t<T>(*new vector_op_vector_t<T>(*this),*new vector_op_vector_t<T>(v))); }
	//! Element-wise multiplication operator.
	inline const vector_op_t<T>& operator * (const vector_t<T>& v) const { return *(new vector_op_mul_v_v_t<T>(*new vector_op_vector_t<T>(*this),*new vector_op_vector_t<T>(v))); }
	//! Element-wise division operator.
	inline const vector_op_t<T>& operator / (const vector_t<T>& v) const { return *(new vector_op_div_v_v_t<T>(*new vector_op_vector_t<T>(*this),*new vector_op_vector_t<T>(v))); }

	//! Addition operator.
	inline const vector_op_t<T>& operator + (const vector_op_t<T>& v) const { return *(new vector_op_add_v_v_t<T>(*new vector_op_vector_t<T>(*this),v)); }
	//! Subtraction operator.
	inline const vector_op_t<T>& operator - (const vector_op_t<T>& v) const { return *(new vector_op_sub_v_v_t<T>(*new vector_op_vector_t<T>(*this),v)); }
	//! Element-wise multiplication operator.
	inline const vector_op_t<T>& operator * (const vector_op_t<T>& v) const { return *(new vector_op_mul_v_v_t<T>(*new vector_op_vector_t<T>(*this),v)); }
	//! Element-wise division operator.
	inline const vector_op_t<T>& operator / (const vector_op_t<T>& v) const { return *(new vector_op_div_v_v_t<T>(*new vector_op_vector_t<T>(*this),v)); }

	//! Dot product.
	inline T operator % (const vector_t<T>& v) const {
		T ret = T(0);
		for( size_t i=0; i<n; i++) ret+=(*this)(i)*v(i);
		return ret;
	}
	//! Dot product.
	inline T operator % (const vector_op_t<T>& v) const  {
		T ret = T(0);
		for( size_t i=0; i<n; i++) ret+=(*this)(i)*v(i);
		delete &v;
		return ret;
	}

	//*************** Basic vector functions
	//! Dot product.
	inline friend T dot(const vector_op_t<T>& v1,const vector_op_t<T>& v2) { T ret = v1%v2; delete &v1; delete &v2; return ret; }
	//! Dot product.
	inline friend T dot(const vector_t<T>& v1,const vector_op_t<T>& v2) { T ret = v1%v2; delete &v2; return ret; }
	//! Dot product.
	inline friend T dot(const vector_op_t<T>& v1,const vector_t<T>& v2) { T ret = v1%v2; delete &v1; return ret; }
	//! Dot product.
	inline friend T dot(const vector_t<T>& v1,const vector_t<T>& v2) { T ret = v1%v2; return ret; }
	
	//! The length of the vector.
	inline friend T length(const vector_op_t<T>& v) {
		T sqSum = T(0);
		for( size_t i=0; i<v.n; i++ ) sqSum+=v(i)*v(i);
		delete &v;
		return sqrt(sqSum);
	}
	//! The length of the vector.
	inline friend T length(const vector_t<T>& v) {
		T sqSum = T(0);
		for( size_t i=0; i<v.n; i++ ) sqSum+=v(i)*v(i);
		return sqrt(sqSum);
	}
	//! The square of the length of the vector.
	inline friend T sqlength(const vector_op_t<T>& v) {
		T sqSum = T(0);
		for( size_t i=0; i<v.n; i++ ) sqSum+=v(i)*v(i);
		delete &v;
		return sqSum;
	}
	//! The square of the length of the vector.
	inline friend T sqlength(const vector_t<T>& v) {
		T sqSum = T(0);
		for( size_t i=0; i<v.n; i++ ) sqSum+=v(i)*v(i);
		return sqSum;
	}

	
	//************* JM mvec_t interop
#ifdef jm_vec_h
	//! (Internal) Copy operator from jm::mvec2_t
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const jm::mvec2_t<T>& v ) {
		if( !alloced ) assert( n==2 );
		resize(2);
		data[0] = v[0];
		data[1] = v[1];
		return *this;
	}
	//! (Internal) Copy operator from jm::mvec3_t
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const jm::mvec3_t<T>& v ) {
		if( !alloced ) assert( n==3 );
		resize(3);
		data[0] = v[0];
		data[1] = v[1];
		data[2] = v[2];
		return *this;
	}
	//! (Internal) Copy operator from jm::mvec4_t
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const jm::mvec4_t<T>& v ) {
		if( !alloced ) assert( n==4 );
		resize(4);
		data[0] = v[0];
		data[1] = v[1];
		data[2] = v[2];
		data[3] = v[3];
		return *this;
	}
	//! Casting operator to jm::mvec2_t.
	inline operator jm::mvec2_t<T>() const {
		assert( n==2 );
		return jm::mvec2_t<T>(data[0],data[1]);
	}
	//! Casting operator to jm::mvec3_t.
	inline operator jm::mvec3_t<T>() const {
		assert( n==3 );
		return jm::mvec3_t<T>(data[0],data[1],data[2]);
	}
	//! Casting operator to jm::mvec4_t.
	inline operator jm::mvec4_t<T>() const {
		assert( n==4 );
		return jm::mvec4_t<T>(data[0],data[1],data[2],data[3]);
	}
#endif
	
	//************* GLM interop
#ifdef GLM_VERSION_MAJOR
	//! (Internal) Copy operator from glm::vec2
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const glm::vec<2, T, glm::defaultp>& v ) {
		if( !alloced ) assert( n==2 );
		resize(2);
		data[0] = v[0];
		data[1] = v[1];
		return *this;
	}
	//! (Internal) Copy operator from glm::vec3
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const glm::vec<3, T, glm::defaultp>& v ) {
		if( !alloced ) assert( n==3 );
		resize(3);
		data[0] = v[0];
		data[1] = v[1];
		data[2] = v[2];
		return *this;
	}
	//! (Internal) Copy operator from glm::vec4
	//! Note that when the sizes of left and right-hand side mismatch, the left-hand side vector is resized with wrapping connection broken.
	inline vector_t& operator = ( const glm::vec<4, T, glm::defaultp>& v ) {
		if( !alloced ) assert( n==4 );
		resize(4);
		data[0] = v[0];
		data[1] = v[1];
		data[2] = v[2];
		data[3] = v[3];
		return *this;
	}
	//! Casting operator to glm::vec2.
	inline operator glm::vec<2, T, glm::defaultp>() const {
		assert( n==2 );
		return glm::vec<2, T, glm::defaultp>(data[0],data[1]);
	}
	//! Casting operator to glm::vec3.
	inline operator glm::vec<3, T, glm::defaultp>() const {
		assert( n==3 );
		return glm::vec<3, T, glm::defaultp>(data[0],data[1],data[2]);
	}
	//! Casting operator to glm::vec4.
	inline operator glm::vec<4, T, glm::defaultp>() const {
		assert( n==4 );
		return glm::vec<4, T, glm::defaultp>(data[0],data[1],data[2],data[3]);
	}
#endif
};

template<typename T> inline T vector_op_vector_t<T>::operator()(size_t i) const { return v(i);}


template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator - ()    const{ return *new vector_op_neg_t(*this);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator + (T s) const{ return *new vector_op_add_v_s_t(*this,s);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator - (T s) const{ return *new vector_op_sub_v_s_t(*this,s);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator * (T s) const{ return *new vector_op_mul_v_s_t(*this,s);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator / (T s) const{ return *new vector_op_div_v_s_t(*this,s);}

template<typename T> inline const vector_op_t<T>& operator + (T s,const vector_op_t<T>& v){ return *new vector_op_add_v_s_t(v,s);}
template<typename T> inline const vector_op_t<T>& operator - (T s,const vector_op_t<T>& v){ return *new vector_op_sub_s_v_t(s,v);}
template<typename T> inline const vector_op_t<T>& operator * (T s,const vector_op_t<T>& v){ return *new vector_op_mul_v_s_t(v,s);}
template<typename T> inline const vector_op_t<T>& operator / (T s,const vector_op_t<T>& v){ return *new vector_op_div_s_v_t(s,v);}

template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator + (const vector_t<T>& v) const{ return *new vector_op_add_v_v_t(*this,vector_op_vector_t(v));}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator - (const vector_t<T>& v) const{ return *new vector_op_sub_v_v_t(*this,vector_op_vector_t(v));}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator * (const vector_t<T>& v) const{ return *new vector_op_mul_v_v_t(*this,vector_op_vector_t(v));}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator / (const vector_t<T>& v) const{ return *new vector_op_div_v_v_t(*this,vector_op_vector_t(v));}
template<typename T> inline T vector_op_t<T> ::operator % (const vector_t<T>& v) const {
	assert(n==v.n);
	T ret = T(0);
	for( size_t i=0; i<n; i++ ) ret+=(*this)(i)*v(i);
	return ret;
}

template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator + (const vector_op_t<T>& v) const{ return *new vector_op_add_v_v_t(*this,v);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator - (const vector_op_t<T>& v) const{ return *new vector_op_sub_v_v_t(*this,v);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator * (const vector_op_t<T>& v) const{ return *new vector_op_mul_v_v_t(*this,v);}
template<typename T> inline const vector_op_t<T>& vector_op_t<T>::operator / (const vector_op_t<T>& v) const{ return *new vector_op_div_v_v_t(*this,v);}
template<typename T> inline T vector_op_t<T>::operator % (const vector_op_t<T>& v) const {
	assert(n==v.n);
	T ret = T(0);
	for( size_t i=0; i<n; i++ ) ret+=(*this)(i)*v(i);
	return ret;
}

using vecn = vector_t<float>;
using dvecn = vector_t<double>;

} // namespace

#endif /* vecn_hpp */
