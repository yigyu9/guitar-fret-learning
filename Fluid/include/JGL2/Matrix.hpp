//
//  Aligner.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Aligner_hpp
#define JGL2_Aligner_hpp

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <mutex>

#include <JGL2/LinearGroup.hpp>

namespace JGL2 {

struct ViewMatrix : public Group {
	ViewMatrix(float x=0, float y=0, float w=10, float h=10, const str_t& t="Aligner" );
	ViewMatrix(const pos_t& pos, const sz2_t& sz, const str_t& t="Aligner" );
	ViewMatrix(const sz2_t& sz, const str_t& t="Aligner" );

	virtual void		cols(size_t c);
	virtual size_t		cols() const { return _cols; }
	virtual size_t		rows() const { return size_t(ceilf(children()/float(_cols))); }
	virtual float		hSpacing() const { return _hspacing; }
	virtual void		hSpacing( float _hspacing );
	virtual float		vSpacing() const { return _vspacing; }
	virtual void		vSpacing( float _vspacing );
	virtual void		rearrange(NVGcontext*,autoscale_t scaling) override;
	virtual sz2_t		minSize() const override;

protected:
	virtual void		fitAllChildren(NVGcontext* vg, const rct_t& r);
	virtual void		alignChildren(NVGcontext* vg, const rct_t& r);
	virtual bool		checkResizable();
	virtual void		rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling) override;

	float				_vspacing = 0;
	float				_hspacing = 0;
	size_t				_cols = 1;
};

} // namespace JGL2

namespace JGL2 {

inline ViewMatrix::ViewMatrix(float x, float y, float w, float h, const str_t& t )
: LinearGroup( x, y, w, h, t ) {
	alignment( ALIGN_ALL );
}

inline ViewMatrix::ViewMatrix(const pos_t& pos, const sz2_t& sz, const str_t& t )
: LinearGroup( pos, sz, t ) {
	alignment( ALIGN_ALL );
}

inline ViewMatrix::ViewMatrix(const sz2_t& sz, const str_t& t )
: LinearGroup( pos_t(0,0), sz, t ) {
	alignment( ALIGN_ALL );
}

inline void ViewMatrix::cols(size_t c) {
	_cols = c;
	
}

inline bool ViewMatrix::checkResizable() {
	bool resizableFound = false;
	// Check condition for filling
	if(  (type()==HORIZONTAL && (alignment()&ALIGN_LEFT) && (alignment()&ALIGN_RIGHT ) )
	   ||(type()==VERTICAL   && (alignment()&ALIGN_TOP ) && (alignment()&ALIGN_BOTTOM) )) {
		for( auto c: _children ) if( c && !c->hidden() ) {
			if( c == resizable() ) {
				resizableFound = true;
				break;
			}
		}
	}
	return resizableFound;
}

inline void ViewMatrix::fitAllChildren(NVGcontext* vg, const rct_t& r) {
	if( type() == HORIZONTAL && (alignment()&ALIGN_TOP) && (alignment()&ALIGN_BOTTOM) ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->h( std::max(c->minSize().h, r.h ) );
			c->reform(vg,AUTOSCALE_W);
		}
	}
	else if( type() == VERTICAL && (alignment()&ALIGN_LEFT) && (alignment()&ALIGN_RIGHT) ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->w( std::max( c->minSize().w, r.w ) );
			c->reform(vg,AUTOSCALE_H);
		}
	}
}

inline void ViewMatrix::alignChildren(NVGcontext* vg, const rct_t& r) {
	if( type() == HORIZONTAL ) {
		float xx = r.x;
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->x(xx);
			c->y( alignRect( r, c->size(), alignment() ).y );
			if( !c->hidden() )
				xx+=c->w()+spacing();
		}
	}
	else {
		float yy = r.y;
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->y( yy );
			c->x( alignRect( r, c->size(), alignment() ).x );
			if( !c->hidden() )
				yy+=c->h()+spacing();
		}
	}
}

inline void ViewMatrix::rearrangeChildren(NVGcontext* vg, const rct_t& r, int scaling){
	int sc = autoscale()&scaling;
	alignChildren(vg, r);
	fitAllChildren(vg, r);
	alignChildren(vg, r);
	updateContentsRect(vg);

	if( type() == HORIZONTAL && (sc&AUTOSCALE_H) )
		h(_contentsRect.h);
	if( type() == VERTICAL && (sc&AUTOSCALE_W) )
		w(_contentsRect.w);

	bool resizableFound = checkResizable();

	fitAllChildren(vg, r);
	alignChildren(vg, r);
	updateContentsRect(vg);
	
	if( resizableFound ) {
		if( type() == HORIZONTAL ) {
			float resizableSz = _setSize.w - contentsRect().w + resizable()->w();
			resizableSz = std::max( resizableSz, resizable()->minSize().w );
			resizable()->w( resizableSz );
			resizable()->reform(vg,AUTOSCALE_ALL);
		}
		else {
			float resizableSz = _setSize.h - contentsRect().h + resizable()->h();
			resizableSz = std::max( resizableSz, resizable()->minSize().h );
			resizable()->h( resizableSz );
			resizable()->reform(vg,AUTOSCALE_ALL);
		}
	}
	alignChildren(vg, r);
}

inline void ViewMatrix::rearrange(NVGcontext* vg,int scaling) {
	{
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			if( c->changed() ) c->reform(vg,AUTOSCALE_ALL);
		}
	}
	int sc = autoscale()&scaling;

	if( changed() ) {
		rearrangeChildren(vg, paddedRect(),scaling);
		updateContentsRect(vg);

		if( type() == HORIZONTAL && (sc&AUTOSCALE_W))
			_setSize.w = std::max(_contentsRect.w,_setSize.w);
		if( type() == VERTICAL && (sc&AUTOSCALE_H))
			_setSize.h = std::max(_contentsRect.h,_setSize.h);

		_bound.wh() = max(_setSize, minSize() );
	}
	_changed = false;
//	_Scrollable::scrollRange( size(), contentsRect(), alignment() );
}

inline void ViewMatrix::hSpacing( float s ) {
	_hspacing = s;
	change();
}

inline void ViewMatrix::vSpacing( float s ) {
	_vspacing = s;
	change();
}

inline sz2_t Aligner::minSize() const {
	float ww = 0, hh = 0;
	if( _type == VERTICAL ) hh = spacing();
	else					ww = spacing();
	for(const auto c: _children ){
		auto sz = c->minSize();
		if( _type == VERTICAL ) {
			ww = std::max( ww, sz.w );
			hh+= sz.h + spacing();
		}
		else {
			ww+= sz.w + spacing();
			hh = std::max( hh, sz.h );
		}
	};
	return sz2_t(ww,hh);
}

inline void ViewMatrix::resizable( Widget* w ) {
	_resizable = w;
	if( _resizable ) {
		_resizable->changed();
	}
	changed();
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Aligner_hpp */
