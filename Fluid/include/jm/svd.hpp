//
//  svd.hpp
//  TextileMeasure
//
//  Created by Hyun Joon Shin on 2/25/25.
//

#ifndef svd_hpp
#define svd_hpp

#include <cassert>
#include <stdexcept>
#include "matn.hpp"

namespace jm {

template<typename T> struct svd_t {
	const float eps = 1E-20;
	
	// the input matrix A of size m_ x n_
	// the decomposed matrix A = u x w x vT
	// Notice that v in the matrix is v not vT
	// The size of u = m x n
	// the size of w = n
	// the size of v = n x n
	svd_t(){}
	svd_t(size_t m_, size_t n_, const T* A_) {
		init( matrix_t<T>(m_, n_, A_) );
	}
	svd_t(const matrix_t<T>& A) {
		init(A);
	}
	void init(size_t m_, size_t n_, const T* A_) {
		init( matrix_t<T>(m_, n_, A_) );
	}
	void init(const matrix_t<T>& A) {
		size_t m = A.m;
		size_t n = A.n;

		u = A;
		w.resize(n);
		v.resize(n,n);
		vector_t<T> rv1(n);

		int q = int(std::min(m,n));
		int i, j, jj, k, l=1, nm;
		bool flag = true;
		float anorm = 0.f, g = 0.f, scale = 0.f, s=0.f;
		float c, f, h, x, y, z;
		
		for (i = 0; i < n; i++) {
			l = i + 1;
			rv1[i] = scale * g;
			g = 0.f;
			s = 0.f;
			scale = 0.f;
			if (i < m) {
				for (k = i; k < m; k++) scale += fabsf(u[k][i]);
				if (scale!=0.f) {
					for (k = i; k < m; k++) {
						u[k][i] /= scale;
						s += u[k][i] * u[k][i];
					}
					f = u[i][i];
					g = -SIGN(sqrt(s),f);
					h = f * g - s;
					u[i][i] = f - g;
					for (j = l; j < n; j++) {
						for (s = 0.f, k = i; k < m; k++) s += u[k][i] * u[k][j];
						f = s / h;
						for (k = i; k < m; k++) u[k][j] += f * u[k][i];
					}
					for (k = i; k < m; k++) u[k][i] *= scale;
				}
			}
			w[i] = scale * g;
			g = 0.f;
			s = 0.f;
			scale = 0.f;
			if (i < m && i != n - 1) {
				for (k = l; k < n; k++) scale += fabsf(u[i][k]);
				if (scale!=0.f) {
					for (k = l; k < n; k++) {
						u[i][k] /= scale;
						s += u[i][k] * u[i][k];
					}
					f = u[i][l];
					g = -SIGN(sqrt(s),f);
					h = f * g - s;
					u[i][l] = f - g;
					for (k = l; k < n; k++) rv1[k] = u[i][k] / h;
					for (j = l; j < m; j++) {
						for (s = 0.f, k = l; k < n; k++) s += u[j][k] * u[i][k];
						for (k = l; k < n; k++) u[j][k] += s * rv1[k];
					}
					for (k = l; k < n; k++) u[i][k] *= scale;
				}
			}
			anorm = std::max(anorm, (fabsf(w[i]) + fabsf(rv1[i])));
		}
		
		for (i = int(n) - 1; i >= 0; i--) {
			if (i < n - 1) {
				if (g!=0.f) {
					for (j = l; j < n; j++) v[j][i] = (u[i][j] / u[i][l]) / g;
					for (j = l; j < n; j++) {
						for (s = 0.f, k = l; k < n; k++) s += u[i][k] * v[k][j];
						for (k = l; k < n; k++) v[k][j] += s * v[k][i];
					}
				}
				for (j = l; j < n; j++) v[i][j] = v[j][i] = 0.f;
			}
			v[i][i] = 1.f;
			g = rv1[i];
			l = i;
		}
		
		for (i = q - 1; i >= 0; i--) {
			l = i + 1;
			g = w[i];
			for (j = l; j < n; j++) u[i][j] = 0.f;
			if (g!=0.f) {
				g = 1.f / g;
				for (j = l; j < n; j++) {
					for (s = 0.f, k = l; k < m; k++) s += u[k][i] * u[k][j];
					f = (s / u[i][i]) * g;
					for (k = i; k < m; k++)	u[k][j] += f * u[k][i];
				}
				for (j = i; j < m; j++) u[j][i] *= g;
			} else
				for (j = i; j < m; j++) u[j][i] = 0.f;
			++u[i][i];
		}
		nm = int(n)-2;
		for (k = int(n) - 1; k >= 0; k--) {
			for (int its = 0; its < 30; its++) {
				flag = true;
				for (l = k; l >= 0; l--) {
					nm = l - 1;
					if ((fabsf(rv1[l]) + anorm) == anorm) {
						flag = false;
						break;
					}
					if ((fabsf(w[nm]) + anorm) == anorm) break;
				}
				if (flag) {
					c = 0.f;
					s = 1.f;
					for (i = l; i <= k; i++) {
						f = s * rv1[i];
						rv1[i] = c * rv1[i];
						if ((fabsf(f) + anorm) == anorm) break;
						g = w[i];
						h = pythag(f, g);
						w[i] = h;
						h = 1.f / h;
						c = g * h;
						s = -f * h;
						for (j = 0; j < m; j++) {
							y = u[j][nm];
							z = u[j][i];
							u[j][nm] = y * c + z * s;
							u[j][i] = z * c - y * s;
						}
					}
				}
				z = w[k];
				if (l == k) {
					if (z < 0.f) {
						w[k] = -z;
						for (j = 0; j < n; j++) v[j][k] = -v[j][k];
					}
					break;
				}
				if (its == 29) throw std::runtime_error("no convergence in 30 svdcmp iterations");
				x = w[l];
				nm = k - 1;
				y = w[nm];
				g = rv1[nm];
				h = rv1[k];
				f = ((y - z) * (y + z) + (g - h) * (g + h)) / (2.f * h * y);
				g = pythag(f, 1.f);
				f = ((x - z) * (x + z) + h * ((y / (f + SIGN(g,f)))- h)) / x;
				c = s = 1.f;
				for (j = l; j <= nm; j++) {
					i = j + 1;
					g = rv1[i];
					y = w[i];
					h = s * g;
					g = c * g;
					z = pythag(f, h);
					rv1[j] = z;
					c = f / z;
					s = h / z;
					f = x * c + g * s;
					g = g * c - x * s;
					h = y * s;
					y *= c;
					for (jj = 0; jj < n; jj++) {
						x = v[jj][j];
						z = v[jj][i];
						v[jj][j] = x * c + z * s;
						v[jj][i] = z * c - x * s;
					}
					z = pythag(f, h);
					w[j] = z;
					if (z!=0.f) {
						z = 1.f / z;
						c = f * z;
						s = h * z;
					}
					f = c * g + s * y;
					x = c * y - s * g;
					for (jj = 0; jj < m; jj++) {
						y = u[jj][j];
						z = u[jj][i];
						u[jj][j] = y * c + z * s;
						u[jj][i] = z * c - y * s;
					}
				}
				rv1[l] = 0.f;
				rv1[k] = f;
				w[k] = x;
			}
		}
	}
	
	virtual ~svd_t() {
	}

	// the length of b is m
	// the length of x is n
	void solve(const vector_t<T>& b, vector_t<T>& x, float thresh=-1.f) {
		assert((void("SVD is not initialized."),u.m>0&&u.n>0));
		assert((void("The length of the vector and the matrix size mismatch."),b.n==u.m) );
		x.resize(u.n);
		size_t m = u.m, n = u.n;
		int i,j,jj;
		float s;
		vector_t<T> tmp(n);
		float tsh = (thresh >= 0. ? thresh : 0.5*sqrt(m+n+1.)*w[0]*eps);
		for (j=0;j<n;j++) {
			s=0.0;
			if (w[j] > tsh) {
				for (i=0;i<m;i++) s += u[i][j]*b[i];
				s /= w[j];
			}
			tmp[j]=s;
		}
		for (j=0;j<n;j++) {
			s=0.0;
			for (jj=0;jj<n;jj++) s += v[j][jj]*tmp[jj];
			x[j]=s;
		}
	}
	// the size of matrix b is m x p
	// the size of matrix x is n x p
	void solve(const matrix_t<T>& b, matrix_t<T>& x, float thresh=-1.f) {
		assert((void("The matrix size mismatch."),b.m==u.m) );
		size_t m = u.m, p = b.n, n = u.n;
		x.resize(n,p);
		vector_t<T> xx(n), bc(m);
		for (size_t j=0;j<p;j++) {
			for (size_t i=0;i<m;i++) bc[i] = b[i][j];
			solve(bc,xx,thresh);
			for (size_t i=0;i<n;i++) x[i][j] = xx[i];
		}
	}
	
	// the length of b is m == m_
	// the length of x is n
	vector_t<T> solve(const vector_t<T>& b, float thresh=-1.f) {
		vector_t<T> x;
		solve(b,x,thresh);
		return x;
	}
	// the size of b is m x p
	// the size of x is n x p
	matrix_t<T> solve(const matrix_t<T>& b, float thresh=-1.f) {
		matrix_t<T> x;
		solve(b,x,thresh);
		return x;
	}

	// calculates sqrt( a^2 + b^2 ) with decent precision
	static inline float pythag(float a, float b) {
		float absa = fabsf(a), absb = fabsf(b);
		if (absa > absb)	return (absa * sqrtf(1.0 + SQR(absb/absa)));
		else				return (absb == 0.0 ? 0.0 : absb * sqrtf(1.0 + SQR(absa / absb)));
	}
	static inline float SIGN(float a,float b) {return ((b) > 0.f ? fabsf(a) : - fabsf(a)); }
	static inline float SQR(float a) { return a==0.f ? 0.f : a * a; }

	vector_t<T> w;
	matrix_t<T> u;
	matrix_t<T> v;
};

using svd = svd_t<float>;


template<typename T> vector_t<T> solve(const matrix_t<T>& A, const vector_t<T>& b, float thresh=-1.f ) {
	svd_t<T> solver( A );
	return solver.solve(b,thresh);
}

template<typename T> matrix_t<T> solve(const matrix_t<T>& A, const matrix_t<T>& b, float thresh=-1.f ) {
	svd_t<T> solver( A );
	return solver.solve(b,thresh);
}

// A : m x n
// b : m
template<typename T> vector_t<T> solve(size_t m, size_t n, T* A, const T* b, float thresh=-1.f ) {
	svd_t<T> solver( m,n,A );
	return solver.solve(b,thresh);
}

// A : m x n
// b : m x p
template<typename T> matrix_t<T> solve(size_t m, size_t n, T* A, size_t p, T* b, float thresh=-1.f ) {
	svd_t<T> solver( A );
	return solver.solve(b,thresh);
}

// A : m x n
// b : m
// x : n
template<typename T> void solve(size_t m, size_t n, T* A, const T* b, T* x, float thresh=-1.f ) {
	svd_t<T> solver( m,n,A );
	auto xx = solver.solve(b,thresh);
	T* ret = xx.data;
	xx.allocated = false;
	xx.data = nullptr;
	return ret;
}

// A : m x n
// b : m x p
// x : n x p
template<typename T> void solve(size_t m, size_t n, T* A, size_t p, T* b, T* x, float thresh=-1.f ) {
	svd_t<T> solver( A );
	auto xx = solver.solve(b,thresh);
	T* ret = xx.data;
	xx.allocated = false;
	xx.data = nullptr;
	return ret;
}

} // namespace

#endif /* svd_h */
