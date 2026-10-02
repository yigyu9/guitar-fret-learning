//
//  matn.hpp
//  TextileMeasure
//
//  Created by Hyun Joon Shin on 2/28/25.
//

#ifndef matn_hpp
#define matn_hpp

#include "vecn.hpp"

namespace jm {

template<typename T> struct matrix_t;
template<typename T> struct matrix_op_t {
	size_t m, n;
	inline matrix_op_t( size_t mm, size_t nn): m(mm), n(nn){}
	inline virtual T operator()(size_t i,size_t j) const = 0;
	inline const matrix_op_t<T>& operator - ()    const;
	inline const matrix_op_t<T>& operator + (T s) const;
	inline const matrix_op_t<T>& operator - (T s) const;
	inline const matrix_op_t<T>& operator * (T s) const;
	inline const matrix_op_t<T>& operator / (T s) const;
	
	inline const matrix_op_t<T>& operator + (const matrix_t<T>& m) const;
	inline const matrix_op_t<T>& operator - (const matrix_t<T>& m) const;
	inline const matrix_op_t<T>& operator * (const matrix_t<T>& m) const;
	inline const matrix_op_t<T>& operator / (const matrix_t<T>& m) const;
	inline const matrix_op_t<T>& operator % (const matrix_t<T>& m) const;

	inline const matrix_op_t<T>& operator + (const matrix_op_t<T>& m) const;
	inline const matrix_op_t<T>& operator - (const matrix_op_t<T>& m) const;
	inline const matrix_op_t<T>& operator * (const matrix_op_t<T>& m) const;
	inline const matrix_op_t<T>& operator / (const matrix_op_t<T>& m) const;
	inline const matrix_op_t<T>& operator % (const matrix_op_t<T>& m) const;
	
	inline const vector_op_t<T>& operator * (const vector_op_t<T>& v) const;
	inline const vector_op_t<T>& operator * (const vector_t<T>& v) const;

	inline friend const matrix_op_t<T>& operator + (T s,const matrix_op_t<T>& m);
	inline friend const matrix_op_t<T>& operator - (T s,const matrix_op_t<T>& m);
	inline friend const matrix_op_t<T>& operator * (T s,const matrix_op_t<T>& m);
	inline friend const matrix_op_t<T>& operator / (T s,const matrix_op_t<T>& m);
	
	inline friend const matrix_op_t<T>& transpose(const matrix_op_t<T>& m);
};

template<typename T> struct matrix_op_matrix_t : matrix_op_t<T> {
	const matrix_t<T>& mat;
	inline matrix_op_matrix_t( const matrix_t<T>& mm):matrix_op_t<T>(mm.m,mm.n),mat(mm){}
	inline virtual ~matrix_op_matrix_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override;
};
template<typename T> struct matrix_op_neg_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	inline matrix_op_neg_t( const matrix_op_t<T>& mm):matrix_op_t<T>(mm.m,mm.n),mat(mm){}
	inline virtual ~matrix_op_neg_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ -mat(i,j); };
};
template<typename T> struct matrix_op_transpose_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	inline matrix_op_transpose_t(const matrix_op_t<T>& mm):matrix_op_t<T>(mm.n,mm.m),mat(mm){}
	inline virtual ~matrix_op_transpose_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return -mat(j,i); };
};
template<typename T> struct matrix_op_m_s_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat; T s;
	inline matrix_op_m_s_t(const matrix_op_t<T>& mm,T ss):matrix_op_t<T>(mat.m,mat.n),mat(mm){}
	inline virtual ~matrix_op_m_s_t(){ delete &mat; }
};
template<typename T> struct matrix_op_s_m_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat; T s;
	inline matrix_op_s_m_t(T ss,const matrix_op_t<T>& mm):matrix_op_t<T>(mat.m,mat.n),mat(mm){}
	inline virtual ~matrix_op_s_m_t(){ delete &mat; }
};
template<typename T> struct matrix_op_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	inline matrix_op_m_m_t(const matrix_op_t<T>& m1,const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m1.n),mat1(m1),mat2(m2){ assert(m1.m==m2.m && m1.n==m2.n); }
	inline virtual ~matrix_op_m_m_t(){ delete &mat1; delete &mat2; }
};

template<typename T> struct matrix_op_add_m_s_t : matrix_op_m_s_t<T> {
	inline matrix_op_add_m_s_t(const matrix_op_t<T>& mm,T ss):matrix_op_m_s_t<T>(mm,ss){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)+matrix_op_m_s_t<T>::s; };
};
template<typename T> struct matrix_op_sub_m_s_t : matrix_op_m_s_t<T> {
	inline matrix_op_sub_m_s_t(const matrix_op_t<T>& mm,T ss):matrix_op_m_s_t<T>(mm,ss){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)-matrix_op_m_s_t<T>::s; };
};
template<typename T> struct matrix_op_mul_m_s_t : matrix_op_m_s_t<T> {
	inline matrix_op_mul_m_s_t(const matrix_op_t<T>& mm,T ss):matrix_op_m_s_t<T>(mm,ss){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)*matrix_op_m_s_t<T>::s; };
};
template<typename T> struct matrix_op_div_m_s_t : matrix_op_m_s_t<T> {
	inline matrix_op_div_m_s_t(const matrix_op_t<T>& mm,T ss):matrix_op_m_s_t<T>(mm,ss){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)/matrix_op_m_s_t<T>::s; };
};

template<typename T> struct matrix_op_sub_s_m_t : matrix_op_s_m_t<T> {
	inline matrix_op_sub_s_m_t(T ss,const matrix_op_t<T>& mm):matrix_op_m_s_t<T>(ss,mm){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_s_m_t<T>::s-matrix_op_s_m_t<T>::mat(i,j); };
};
template<typename T> struct matrix_op_div_s_m_t : matrix_op_s_m_t<T> {
	inline matrix_op_div_s_m_t(T ss,const matrix_op_t<T>& mm):matrix_op_m_s_t<T>(ss,mm){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_s_m_t<T>::s/matrix_op_s_m_t<T>::mat(i,j); };
};


template<typename T> struct matrix_op_add_m_m_t : matrix_op_m_m_t<T> {
	inline matrix_op_add_m_m_t(const matrix_op_t<T>& m1,const matrix_op_t<T>& m2):matrix_op_m_m_t<T>(m1,m2){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)+matrix_op_m_s_t<T>::mat2(i,j); };
};
template<typename T> struct matrix_op_sub_m_m_t : matrix_op_m_m_t<T> {
	inline matrix_op_sub_m_m_t(const matrix_op_t<T>& m1,const matrix_op_t<T>& m2):matrix_op_m_m_t<T>(m1,m2){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)-matrix_op_m_s_t<T>::mat2(i,j); };
};
template<typename T> struct matrix_op_elmmul_m_m_t : matrix_op_m_m_t<T> {
	inline matrix_op_elmmul_m_m_t(const matrix_op_t<T>& m1,const matrix_op_t<T>& m2):matrix_op_m_m_t<T>(m1,m2){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)*matrix_op_m_s_t<T>::mat2(i,j); };
};
template<typename T> struct matrix_op_elmdiv_m_m_t : matrix_op_m_m_t<T> {
	inline matrix_op_elmdiv_m_m_t(const matrix_op_t<T>& m1,const matrix_op_t<T>& m2):matrix_op_m_m_t<T>(m1,m2){}
	inline virtual T operator()(size_t i,size_t j) const override{ return matrix_op_m_s_t<T>::mat(i,j)/matrix_op_m_s_t<T>::mat2(i,j); };
};

template<typename T> struct matrix_op_mul_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	size_t p;
	inline matrix_op_mul_m_m_t(const matrix_op_t<T>& m1, const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m2.n),mat1(m1),mat2(m2),p(m1.n){ assert( m1.n == m2.m ); }
	inline virtual ~matrix_op_mul_m_m_t(){ delete &mat1; delete &mat2; }
	inline virtual T operator()(size_t i,size_t j) const override{
		T ret = T(0);
		for( size_t k=0; k<p; k++) ret+=mat1(i,k)*mat2(k,j);
		return ret;
	};
};


template<typename T> struct vector_op_mul_m_v_t : vector_op_t<T> {
	const matrix_op_t<T>& mat;
	const vector_op_t<T>& v;
	inline vector_op_mul_m_v_t(const matrix_op_t<T>& mm, const vector_op_t<T>& vv):vector_op_t<T>(mm.m),mat(mm),v(vv){ assert( mm.n == vv.n );}
	inline virtual ~vector_op_mul_m_v_t(){ delete &mat; delete &v; }
	inline T operator()(size_t i) const override {
		T ret = T(0);
		for( size_t k=0; k<mat.n; k++) ret+=mat(i,k)*v(k);
		return ret;
	};
};


// ROW MAJOR MATRIX!!!
template<typename T> struct matrix_t {
	//! The size of the matrix # rows: m, #cols: n
	size_t m=0, n=0;
	//! the array of data. The matrix is stored in a 1-D array in row-major shape.
	T* data = nullptr;
	//! If the matrix is wrapping a memory.
	//! When it is false, the matrix wrapping a memory allocated by the other part.
	bool alloced = true;
	
	inline matrix_t<T> wrap(size_t m, size_t n, T* d) {
		matrix_t ret;
		ret.m = m;
		ret.n = n;
		ret.data = d;
		ret.alloced = false;
		return ret;
	}

	inline matrix_t(): m(0), n(0), alloced(true), data(nullptr) {}
	inline matrix_t(const matrix_t& v): matrix_t(v.m,v.n,v.data) {}
	inline matrix_t(matrix_t&& v): m(v.m),n(v.n),data(v.data),alloced(v.alloced) { v.data = nullptr; v.alloced = false; }
	inline matrix_t(const matrix_op_t<T>& o): matrix_t(o.m,o.n) {
		for( size_t i=0; i<m; i++ ) for( size_t j=0; j<n; j++ ) (*this)(i,j) = o(i,j);
		delete &o;
	}

	inline matrix_t(size_t m_, size_t n_) { resize(m_,n_); }
	//! Initialize a diagonal matrix with the given diagonal value v
	inline matrix_t(size_t m_, size_t n_, T v) {
		resize(m_,n_);
		for(size_t i=0; i<m*n; i++) data[i] = 0;
		size_t p = std::min(m,n);
		for(size_t i=0; i<p; i++ ) data[i*n+i] = v;
	}

	//! Initialize a square diagonal matrix with the given diagonal value v
	inline matrix_t(const vector_t<T>& v) {
		resize(v.n,v.n);
		for(size_t i=0; i<m*n; i++) data[i] = 0;
		for(size_t i=0; i<n; i++ ) data[i*n+i] = v[i];
	}
	//! Initialize a square diagonal matrix with the given diagonal value v
	inline matrix_t(const vector_op_t<T>& v) {
		resize(v.n,v.n);
		for(size_t i=0; i<m*n; i++) data[i] = 0;
		for(size_t i=0; i<n; i++ ) data[i*n+i] = v(i);
	}
	//! The default direction is row major. When \ref transpose is enabled, \ref d regarded to be column major.
	inline matrix_t(size_t m_, size_t n_, const T* d, bool transpose=false): matrix_t(m_,n_) {
		if( !transpose )
			for(size_t i=0; i<m*n; i++) data[i] = d[i];
		else
			for(size_t i=0; i<m; i++) for(size_t j=0; j<n; j++) data[i*n+j] = d[j*m+i];
	}
	inline matrix_t(size_t m_, size_t n_, T* d): m(m_),n(n_), data(d), alloced(false) {}

	//! param v the vector of rows vector.
	inline matrix_t(const std::vector<std::vector<T>>& mat){
		if( mat.size()<1 ) return;
		resize( mat.size(), mat[0].size() );
		for( int i=0; i<m; i++ ) {
			assert( mat[i].size() == n );
			for( int j=0; j<n; j++ ) (*this)(i,j) = mat[i][j];
		}
	}


	
	inline void free() {
		if( alloced && data ) delete [] data;
		data = nullptr;
		alloced = false;
		m = 0;
		n = 0;
	}
	inline void resize(size_t m_, size_t n_) {
		if( n==n_ && m==m_ ) return;
		if( alloced && data ) delete [] data;
		m = m_;
		n = n_;
		data = new T[m*n];
		alloced = true;
	}

	inline matrix_t& operator = (const matrix_t& v) {
		if( !alloced ) assert( m==v.m && n==v.n );
		resize(v.m,v.n);
		for( size_t i=0; i<m*n; i++ ) data[i] = v.data[i];
		return *this;
	}
	inline matrix_t& operator = (matrix_t&& v){
		free();
		m = v.m;
		n = v.n;
		data = v.data;
		alloced = v.alloced;
		v.data = nullptr;
		v.alloced = false;
		return *this;
	}
	inline matrix_t& operator = (const matrix_op_t<T>& l) {
		if( !alloced ) assert( m==l.m && n==l.n  );
		for(size_t i=0; i<m; i++ ) for(size_t j=0; j<n; j++ ) (*this)(i,j) = l(i,j);
	}


	inline matrix_t& operator = (const std::vector<std::vector<T>>& mat) {
		if( !alloced ) assert( m==mat.size() && n==mat[0].size() );
		resize( mat.size(), mat[0].size() );
		for( int i=0; i<m; i++ ) {
			assert( mat[i].size() == n );
			for( int j=0; j<n; j++ ) (*this)(i,j) = mat[i][j];
		}
	}
	inline matrix_t& operator = (const std::tuple<size_t,size_t,const T*> v) {
		if( !alloced ) assert( n == std::get<0>(v) && m == std::get<1>(v) );
		resize(std::get<0>(v), std::get<1>(v));
		T* d = std::get<2>(v);
		for( size_t i=0; i<m*n; i++ ) data[i] = d[i];
		return *this;
	}
	inline matrix_t& operator = (const std::initializer_list<T>& l) {
		assert( m*n < l.size()  );
		int i=0; for( auto v: l ) data[i++] = v;
	}

	
	inline virtual ~matrix_t() {
		free();
	}
	inline vector_t<T> operator [] (size_t k) {
		return vector_t<T>::wrap(n,&(data[k*n]));
	}
	inline const vector_t<T> operator [] (size_t k) const {
		return vector_t<T>::wrap(n,&(data[k*n]));
	}
	inline T& operator () (size_t i, size_t j) {
		return data[i*n+j];
	}
	inline const T& operator () (size_t i, size_t j) const {
		return data[i*n+j];
	}
	
	inline matrix_t<T>& operator += (T s) { for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i)+=s; return *this; }
	inline matrix_t<T>& operator -= (T s) { for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i)-=s; return *this; }
	inline matrix_t<T>& operator *= (T s) { for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i)*=s; return *this; }
	inline matrix_t<T>& operator /= (T s) { for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i)/=s; return *this; }

	inline matrix_t<T>& operator += (const matrix_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)+=mat(i,j); return *this; }
	inline matrix_t<T>& operator -= (const matrix_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)-=mat(i,j); return *this; }
	inline matrix_t<T>& operator *= (const matrix_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)*=mat(i,j); return *this; }
	inline matrix_t<T>& operator /= (const matrix_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)/=mat(i,j); return *this; }

	inline matrix_t<T>& operator += (const matrix_op_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)+=mat(i,j); delete &mat; return *this; }
	inline matrix_t<T>& operator -= (const matrix_op_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)-=mat(i,j); delete &mat; return *this; }
	inline matrix_t<T>& operator *= (const matrix_op_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)*=mat(i,j); delete &mat; return *this; }
	inline matrix_t<T>& operator /= (const matrix_op_t<T>& mat) { assert(n==mat.n&&m==mat.m); for(auto i=0; i<m; i++) for(auto j=0; j<n; j++) (*this)(i,j)/=mat(i,j); delete &mat; return *this; }

	
	inline const matrix_op_t<T>& operator - ()    const { return *new matrix_op_neg_t    <T>(*new matrix_op_matrix_t<T>(*this)); }
	inline const matrix_op_t<T>& operator + (T s) const { return *new matrix_op_add_m_s_t<T>(*new matrix_op_matrix_t<T>(*this),s); }
	inline const matrix_op_t<T>& operator - (T s) const { return *new matrix_op_sub_m_s_t<T>(*new matrix_op_matrix_t<T>(*this),s); }
	inline const matrix_op_t<T>& operator * (T s) const { return *new matrix_op_mul_m_s_t<T>(*new matrix_op_matrix_t<T>(*this),s); }
	inline const matrix_op_t<T>& operator / (T s) const { return *new matrix_op_div_m_s_t<T>(*new matrix_op_matrix_t<T>(*this),s); }

	inline const matrix_op_t<T>& operator + (const matrix_t<T>& m) const { return *new matrix_op_add_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),*new matrix_op_matrix_t<T>(m)); }
	inline const matrix_op_t<T>& operator - (const matrix_t<T>& m) const { return *new matrix_op_sub_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),*new matrix_op_matrix_t<T>(m)); }
	inline const matrix_op_t<T>& operator * (const matrix_t<T>& m) const { return *new matrix_op_mul_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),*new matrix_op_matrix_t<T>(m)); }
	inline const matrix_op_t<T>& operator / (const matrix_t<T>& m) const { return *new matrix_op_elmdiv_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),*new matrix_op_matrix_t<T>(m)); }
	inline const matrix_op_t<T>& operator % (const matrix_t<T>& m) const { return *new matrix_op_elmmul_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),*new matrix_op_matrix_t<T>(m)); }

	inline const matrix_op_t<T>& operator + (const matrix_op_t<T>& m) const { return *new matrix_op_add_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),m); }
	inline const matrix_op_t<T>& operator - (const matrix_op_t<T>& m) const { return *new matrix_op_sub_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),m); }
	inline const matrix_op_t<T>& operator * (const matrix_op_t<T>& m) const { return *new matrix_op_mul_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),m); }
	inline const matrix_op_t<T>& operator / (const matrix_op_t<T>& m) const { return *new matrix_op_elmdiv_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),m); }
	inline const matrix_op_t<T>& operator % (const matrix_op_t<T>& m) const { return *new matrix_op_elmmul_m_m_t<T>(*new matrix_op_matrix_t<T>(*this),m); }

	inline const vector_op_t<T>& operator * (const vector_t<T>& v) const { return *new vector_op_mul_m_v_t<T>(*this,*new vector_op_t<T>(v)); }
	inline const vector_op_t<T>& operator * (const vector_op_t<T>& v) const { return *new vector_op_mul_m_v_t<T>(*this,v); }

	inline friend const matrix_op_t<T>& operator + (T s,const matrix_t<T>& m) { return *new matrix_op_add_m_s_t<T>(*new matrix_op_matrix_t<T>(m),s); }
	inline friend const matrix_op_t<T>& operator - (T s,const matrix_t<T>& m) { return *new matrix_op_sub_s_m_t<T>(s,*new matrix_op_matrix_t<T>(m)); }
	inline friend const matrix_op_t<T>& operator * (T s,const matrix_t<T>& m) { return *new matrix_op_mul_m_s_t<T>(*new matrix_op_matrix_t<T>(m),s); }
	inline friend const matrix_op_t<T>& operator / (T s,const matrix_t<T>& m) { return *new matrix_op_div_s_m_t<T>(s,*new matrix_op_matrix_t<T>(m)); }

	inline friend const matrix_op_t<T>& transpose(const matrix_t<T>& m) { return *new matrix_op_transpose_t<T>(*new matrix_op_t<T>(m)); }

	
#ifdef jm_mat_h
	template<typename T2, size_t M, size_t N> matrix_t& operator = (const jm::mmat_t<T2,M,N>& a) {
		if( !alloced ) assert( m == M && n == N );
		resize(M,N);
		for(size_t r=0; r<M; r++ ) for(size_t c=0; c<N; c++) (*this)[r][c]=a[c][r];
		return *this;
	}

/*	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 2, 2>& a) {
		if( !alloced ) assert( m == 2 && n == 2 );
		resize(2,2);
		data[0] = a[0][0];	data[2] = a[0][1];
		data[1] = a[1][0];	data[3] = a[1][1];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 2, 3>& a) {
		if( !alloced ) assert( m == 2 && n == 3 );
		resize(2,3);
		data[0] = a[0][0];	data[3] = a[0][1];
		data[1] = a[1][0];	data[4] = a[1][1];
		data[2] = a[2][0];	data[5] = a[2][1];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 2, 4>& a) {
		if( !alloced ) assert( m == 2 && n == 4 );
		resize(2,4);
		data[0] = a[0][0];	data[4] = a[0][1];
		data[1] = a[1][0];	data[5] = a[1][1];
		data[2] = a[2][0];	data[6] = a[2][1];
		data[3] = a[3][0];	data[7] = a[3][1];
	}

	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 3, 2>& a) {
		if( !alloced ) assert( m == 3 && n == 2 );
		resize(3,2);
		data[0] = a[0][0];	data[2] = a[0][1];	data[4] = a[0][2];
		data[1] = a[1][0];	data[3] = a[1][1];	data[5] = a[1][2];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 3, 3>& a) {
		if( !alloced ) assert( m == 3 && n == 3 );
		resize(3,3);
		data[0] = a[0][0];	data[3] = a[0][1];	data[6] = a[0][2];
		data[1] = a[1][0];	data[4] = a[1][1];	data[7] = a[1][2];
		data[2] = a[2][0];	data[5] = a[2][1];	data[8] = a[2][2];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 3, 4>& a) {
		if( !alloced ) assert( m == 3 && n == 4 );
		resize(3,4);
		data[0] = a[0][0];	data[4] = a[0][1];	data[ 8] = a[0][2];
		data[1] = a[1][0];	data[5] = a[1][1];	data[ 9] = a[1][2];
		data[2] = a[2][0];	data[6] = a[2][1];	data[10] = a[2][2];
		data[3] = a[3][0];	data[7] = a[3][1];	data[11] = a[3][2];
	}

	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 4, 2>& a) {
		if( !alloced ) assert( m == 4 && n == 2 );
		resize(4,2);
		data[0] = a[0][0];	data[2] = a[0][1];	data[4] = a[0][2];	data[4] = a[0][3];
		data[1] = a[1][0];	data[3] = a[1][1];	data[5] = a[1][2];	data[5] = a[1][3];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 4, 3>& a) {
		if( !alloced ) assert( m == 4 && n == 3 );
		resize(4,3);
		data[0] = a[0][0];	data[3] = a[0][1];	data[6] = a[0][2];	data[ 9] = a[0][3];
		data[1] = a[1][0];	data[4] = a[1][1];	data[7] = a[1][2];	data[10] = a[1][3];
		data[2] = a[2][0];	data[5] = a[2][1];	data[8] = a[2][2];	data[11] = a[2][3];
	}
	template<typename T2> matrix_t& operator = (const jm::mmat_t<T2, 4, 4>& a) {
		if( !alloced ) assert( m == 4 && n == 4 );
		resize(4,4);
		data[0] = a[0][0];	data[4] = a[0][1];	data[ 8] = a[0][2];	data[12] = a[0][3];
		data[1] = a[1][0];	data[5] = a[1][1];	data[ 9] = a[1][2];	data[13] = a[1][3];
		data[2] = a[2][0];	data[6] = a[2][1];	data[10] = a[2][2];	data[14] = a[2][3];
		data[3] = a[3][0];	data[7] = a[3][1];	data[11] = a[3][2];	data[15] = a[3][3];
	}
*/
	inline operator jm::mmat_t<T,2,2>() const {
		assert( m==2 && n==2 );
		return jm::mmat_t<T,2,2>(data[0],data[2],
								 data[1],data[3]);
	}
	inline operator jm::mmat_t<T,2,3>() const {
		assert( m==2 && n==3 );
		return jm::mmat_t<T,2,3>(data[0],data[3],
								 data[1],data[4],
								 data[2],data[5]);
	}
	inline operator jm::mmat_t<T,2,4>() const {
		assert( m==2 && n==4 );
		return jm::mmat_t<T,2,4>(data[0],data[4],
								 data[1],data[5],
								 data[2],data[6],
								 data[3],data[7]);
	}
	inline operator jm::mmat_t<T,3,2>() const {
		assert( m==3 && n==2 );
		return jm::mmat_t<T,3,2>(data[0],data[2],data[4],
								 data[1],data[3],data[5]);
	}
	inline operator jm::mmat_t<T,3,3>() const {
		assert( m==3 && n==3 );
		return jm::mmat_t<T,3,3>(data[0],data[3],data[6],
								 data[1],data[4],data[7],
								 data[2],data[5],data[8]);
	}
	inline operator jm::mmat_t<T,3,4>() const {
		assert( m==3 && n==4 );
		return jm::mmat_t<T,3,4>(data[0],data[4],data[ 8],
								 data[1],data[5],data[ 9],
								 data[2],data[6],data[10],
								 data[3],data[7],data[11]);
	}
	inline operator jm::mmat_t<T,4,2>() const {
		assert( m==4 && n==2 );
		return jm::mmat_t<T,4,2>(data[0],data[2],data[4],data[6],
								 data[1],data[3],data[5],data[7]);
	}
	inline operator jm::mmat_t<T,4,3>() const {
		assert( m==4 && n==3 );
		return jm::mmat_t<T,4,3>(data[0],data[3],data[6],data[ 9],
								 data[1],data[4],data[7],data[10],
								 data[2],data[5],data[8],data[11]);
	}
	inline operator jm::mmat_t<T,4,4>() const {
		assert( m==4 && n==4 );
		return jm::mmat_t<T,4,4>(data[0],data[4],data[ 8],data[12],
								 data[1],data[5],data[ 9],data[13],
								 data[2],data[6],data[10],data[14],
								 data[3],data[7],data[11],data[15]);
	}
#endif
#ifdef GLM_VERSION_MAJOR
/*	template<typename T2, int M, int N> matrix_t& operator = (const glm::mat<M,N,T2,glm::defaultp>& a) {
		if( !alloced ) assert( m == M && n == N );
		resize(M,N);
		for(size_t r=0; r<M; r++ ) for(size_t c=0; c<N; c++) (*this)[r][c]=T(a[c][r]);
		return *this;
	}
 */
	template<typename T2> matrix_t& operator = (const glm::mat<2, 2, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 2 && n == 2 );
		resize(2,2);
		data[0] = a[0][0];	data[2] = a[0][1];
		data[1] = a[1][0];	data[3] = a[1][1];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<2, 3, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 2 && n == 3 );
		resize(2,3);
		data[0] = a[0][0];	data[3] = a[0][1];
		data[1] = a[1][0];	data[4] = a[1][1];
		data[2] = a[2][0];	data[5] = a[2][1];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<2, 4, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 2 && n == 4 );
		resize(2,4);
		data[0] = a[0][0];	data[4] = a[0][1];
		data[1] = a[1][0];	data[5] = a[1][1];
		data[2] = a[2][0];	data[6] = a[2][1];
		data[3] = a[3][0];	data[7] = a[3][1];
		return *this;
	}

	template<typename T2> matrix_t& operator = (const glm::mat<3, 2, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 3 && n == 2 );
		resize(3,2);
		data[0] = a[0][0];	data[2] = a[0][1];	data[4] = a[0][2];
		data[1] = a[1][0];	data[3] = a[1][1];	data[5] = a[1][2];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<3, 3, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 3 && n == 3 );
		resize(3,3);
		data[0] = a[0][0];	data[3] = a[0][1];	data[6] = a[0][2];
		data[1] = a[1][0];	data[4] = a[1][1];	data[7] = a[1][2];
		data[2] = a[2][0];	data[5] = a[2][1];	data[8] = a[2][2];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<3, 4, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 3 && n == 4 );
		resize(3,4);
		data[0] = a[0][0];	data[4] = a[0][1];	data[ 8] = a[0][2];
		data[1] = a[1][0];	data[5] = a[1][1];	data[ 9] = a[1][2];
		data[2] = a[2][0];	data[6] = a[2][1];	data[10] = a[2][2];
		data[3] = a[3][0];	data[7] = a[3][1];	data[11] = a[3][2];
		return *this;
	}

	template<typename T2> matrix_t& operator = (const glm::mat<4, 2, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 4 && n == 2 );
		resize(4,2);
		data[0] = a[0][0];	data[2] = a[0][1];	data[4] = a[0][2];	data[4] = a[0][3];
		data[1] = a[1][0];	data[3] = a[1][1];	data[5] = a[1][2];	data[5] = a[1][3];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<4, 3, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 4 && n == 3 );
		resize(4,3);
		data[0] = a[0][0];	data[3] = a[0][1];	data[6] = a[0][2];	data[ 9] = a[0][3];
		data[1] = a[1][0];	data[4] = a[1][1];	data[7] = a[1][2];	data[10] = a[1][3];
		data[2] = a[2][0];	data[5] = a[2][1];	data[8] = a[2][2];	data[11] = a[2][3];
		return *this;
	}
	template<typename T2> matrix_t& operator = (const glm::mat<4, 4, T2, glm::defaultp>& a) {
		if( !alloced ) assert( m == 4 && n == 4 );
		resize(4,4);
		data[0] = a[0][0];	data[4] = a[0][1];	data[ 8] = a[0][2];	data[12] = a[0][3];
		data[1] = a[1][0];	data[5] = a[1][1];	data[ 9] = a[1][2];	data[13] = a[1][3];
		data[2] = a[2][0];	data[6] = a[2][1];	data[10] = a[2][2];	data[14] = a[2][3];
		data[3] = a[3][0];	data[7] = a[3][1];	data[11] = a[3][2];	data[15] = a[3][3];
		return *this;
	}

	inline operator glm::mat<2, 2, T, glm::defaultp>() const {
		assert( m==2 && n==2 );
		return glm::mat<2, 2, T, glm::defaultp>(data[0],data[2],
												data[1],data[3]);
	}
	inline operator glm::mat<2, 3, T, glm::defaultp>() const {
		assert( m==2 && n==3 );
		return glm::mat<2, 3, T, glm::defaultp>(data[0],data[3],
												data[1],data[4],
												data[2],data[5]);
	}
	inline operator glm::mat<2, 4, T, glm::defaultp>() const {
		assert( m==2 && n==4 );
		return glm::mat<2, 4, T, glm::defaultp>(data[0],data[4],
												data[1],data[5],
												data[2],data[6],
												data[3],data[7]);
	}
	inline operator glm::mat<3, 2, T, glm::defaultp>() const {
		assert( m==3 && n==2 );
		return glm::mat<3, 2, T, glm::defaultp>(data[0],data[2],data[4],
												data[1],data[3],data[5]);
	}
	inline operator glm::mat<3, 3, T, glm::defaultp>() const {
		assert( m==3 && n==3 );
		return glm::mat<3, 3, T, glm::defaultp>(data[0],data[3],data[6],
												data[1],data[4],data[7],
												data[2],data[5],data[8]);
	}
	inline operator glm::mat<3, 4, T, glm::defaultp>() const {
		assert( m==3 && n==4 );
		return glm::mat<3, 4, T, glm::defaultp>(data[0],data[4],data[ 8],
												data[1],data[5],data[ 9],
												data[2],data[6],data[10],
												data[3],data[7],data[11]);
	}
	inline operator glm::mat<4, 2, T, glm::defaultp>() const {
		assert( m==4 && n==2 );
		return glm::mat<4, 2, T, glm::defaultp>(data[0],data[2],data[4],data[6],
												data[1],data[3],data[5],data[7]);
	}
	inline operator glm::mat<4, 3, T, glm::defaultp>() const {
		assert( m==4 && n==3 );
		return glm::mat<4, 3, T, glm::defaultp>(data[0],data[3],data[6],data[ 9],
												data[1],data[4],data[7],data[10],
												data[2],data[5],data[8],data[11]);
	}
	inline operator glm::mat<4, 4, T, glm::defaultp>() const {
		assert( m==4 && n==4 );
		return glm::mat<4, 4, T, glm::defaultp>(data[0],data[4],data[ 8],data[12],
												data[1],data[5],data[ 9],data[13],
												data[2],data[6],data[10],data[14],
												data[3],data[7],data[11],data[15]);
	}
#endif
};

template<typename T> inline T matrix_op_matrix_t<T>::operator()(size_t i,size_t j) const { return mat(i,j); }

template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator - ()    const{ return *new matrix_op_neg_t(*this);}
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator + (T s) const{ return *new matrix_op_add_m_s_t(*this,s);}
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator - (T s) const{ return *new matrix_op_sub_m_s_t(*this,s);}
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator * (T s) const{ return *new matrix_op_mul_m_s_t(*this,s);}
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator / (T s) const{ return *new matrix_op_div_m_s_t(*this,s);}

template<typename T> inline const matrix_op_t<T>& operator + (T s,const matrix_op_t<T>& m){ return *new matrix_op_add_m_s_t<T>(m,s);}
template<typename T> inline const matrix_op_t<T>& operator - (T s,const matrix_op_t<T>& m){ return *new matrix_op_sub_s_m_t<T>(s,m);}
template<typename T> inline const matrix_op_t<T>& operator * (T s,const matrix_op_t<T>& m){ return *new matrix_op_mul_m_s_t<T>(m,s);}
template<typename T> inline const matrix_op_t<T>& operator / (T s,const matrix_op_t<T>& m){ return *new matrix_op_div_s_m_t<T>(s,m);}

template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator + (const matrix_t<T>& m) const { return *new matrix_op_add_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator - (const matrix_t<T>& m) const { return *new matrix_op_sub_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator * (const matrix_t<T>& m) const { return *new matrix_op_mul_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator / (const matrix_t<T>& m) const { return *new matrix_op_elmdiv_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator % (const matrix_t<T>& m) const { return *new matrix_op_elmmul_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }

template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator + (const matrix_op_t<T>& m) const { return *new matrix_op_add_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator - (const matrix_op_t<T>& m) const { return *new matrix_op_sub_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator * (const matrix_op_t<T>& m) const { return *new matrix_op_mul_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator / (const matrix_op_t<T>& m) const { return *new matrix_op_elmdiv_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }
template<typename T> inline const matrix_op_t<T>& matrix_op_t<T>::operator % (const matrix_op_t<T>& m) const { return *new matrix_op_elmmul_m_m_t<T>(*this,*new matrix_op_matrix_t<T>(m)); }

template<typename T> inline const matrix_op_t<T>& transpose(const matrix_op_t<T> m) { return *new matrix_op_transpose_t<T>(m); }

template<typename T> inline const vector_op_t<T>& matrix_op_t<T>::operator * (const vector_t<T>& v) const { return *new vector_op_mul_m_v_t<T>(*this,*new vector_op_t<T>(v)); }
template<typename T> inline const vector_op_t<T>& matrix_op_t<T>::operator * (const vector_op_t<T>& v) const { return *new vector_op_mul_m_v_t<T>(*this,v); }

using matn = matrix_t<float>;
using dmatn = matrix_t<double>;

} // namespace

#endif /* matn_hpp */

/*
template<typename T> struct matrix_op_add_m_s_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_add_m_s_t(const matrix_op_t<T>& mm, T v):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_add_m_s_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat(i,j)+s; }
};
template<typename T> struct matrix_op_sub_m_s_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_sub_m_s_t(const matrix_op_t<T>& mm, T v):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_sub_m_s_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat(i,j)-s; }
};
template<typename T> struct matrix_op_mul_m_s_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_mul_m_s_t(const matrix_op_t<T>& mm, T v):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_mul_m_s_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat(i,j)*s; }
};
template<typename T> struct matrix_op_div_m_s_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_div_m_s_t(const matrix_op_t<T>& mm, T v):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_div_m_s_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat(i,j)/s; }
};

template<typename T> struct matrix_op_sub_s_m_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_sub_s_m_t(T v,const matrix_op_t<T>& mm):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_sub_s_m_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return s-mat(i,j); }
};
template<typename T> struct matrix_op_div_s_m_t : matrix_op_t<T> {
	const matrix_op_t<T>& mat;
	T s;
	inline matrix_op_div_s_m_t(T v, const matrix_op_t<T>& mm):matrix_op_t<T>(mm.m,mm.n),mat(mm), s(v){}
	inline virtual ~matrix_op_div_s_m_t(){ delete &mat; }
	inline virtual T operator()(size_t i,size_t j) const override{ return s/mat(i,j); }
};


template<typename T> struct matrix_op_add_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	inline matrix_op_add_m_m_t(const matrix_op_t<T>& m1, const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m1.n),mat1(m1),mat2(m2){ assert( m1.m == m2.m && m1.n == m2.n ); }
	inline virtual ~matrix_op_add_m_m_t(){ delete &mat1; delete &mat2; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat1(i,j)+mat2(i,j); };
};
template<typename T> struct matrix_op_sub_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	inline matrix_op_sub_m_m_t(const matrix_op_t<T>& m1, const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m1.n),mat1(m1),mat2(m2){ assert( m1.m == m2.m && m1.n == m2.n ); }
	inline virtual ~matrix_op_sub_m_m_t(){ delete &mat1; delete &mat2; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat1(i,j)-mat2(i,j); };
};
template<typename T> struct matrix_op_elmmul_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	inline matrix_op_elmmul_m_m_t(const matrix_op_t<T>& m1, const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m1.n),mat1(m1),mat2(m2){ assert( m1.m == m2.m && m1.n == m2.n ); }
	inline virtual ~matrix_op_elmmul_m_m_t(){ delete &mat1; delete &mat2; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat1(i,j)*mat2(i,j); };
};
template<typename T> struct matrix_op_elmdiv_m_m_t : matrix_op_t<T> {
	const matrix_op_t<T> &mat1, &mat2;
	inline matrix_op_elmdiv_m_m_t(const matrix_op_t<T>& m1, const matrix_op_t<T>& m2):matrix_op_t<T>(m1.m,m1.n),mat1(m1),mat2(m2){ assert( m1.m == m2.m && m1.n == m2.n ); }
	inline virtual ~matrix_op_elmdiv_m_m_t(){ delete &mat1; delete &mat2; }
	inline virtual T operator()(size_t i,size_t j) const override{ return mat1(i,j)/mat2(i,j); };
};
 */
