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

struct Aligner : public LinearGroup {
	Aligner(float x=0, float y=0, float w=10, float h=10, const str_t& t="Aligner" );
	Aligner(const pos_t& pos, const sz2_t& sz, const str_t& t="Aligner" );
	Aligner(const sz2_t& sz, const str_t& t="Aligner" );

	virtual float		spacing() const { return _spacing; }
	virtual void		spacing( float _spacing );
	virtual void		rearrange(NVGcontext*,autoscale_t scaling) override;
	virtual sz2_t		minSize() const override;

protected:
	virtual void		fitAllChildren(NVGcontext* vg, const rct_t& r);
	virtual void		alignChildren(NVGcontext* vg, const rct_t& r);
	virtual bool		checkResizable();
	virtual void		rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling) override;

	float				_spacing = 0;	
};


} // namespace JGL2

namespace JGL2 {

inline Aligner::Aligner(float x, float y, float w, float h, const str_t& t )
: LinearGroup( x, y, w, h, t ) {
	alignment( align_t::ALL );
}

inline Aligner::Aligner(const pos_t& pos, const sz2_t& sz, const str_t& t )
: LinearGroup( pos, sz, t ) {
	alignment( align_t::ALL );
}

inline Aligner::Aligner(const sz2_t& sz, const str_t& t )
: LinearGroup( pos_t(0,0), sz, t ) {
	alignment( align_t::ALL );
}

inline bool Aligner::checkResizable() {
	bool resizableFound = false;
	// Check condition for filling
	if(  (type()==direction_t::HORIZONTAL && contains(alignment(),align_t::LEFT) && contains(alignment(),align_t::RIGHT ) )
	   ||(type()==direction_t::VERTICAL   && contains(alignment(),align_t::TOP ) && contains(alignment(),align_t::BOTTOM) ) ) {
		for( auto c: _children ) if( c && !c->hidden() ) {
			if( c == resizable() ) {
				resizableFound = true;
				break;
			}
		}
	}
	return resizableFound;
}

inline void Aligner::fitAllChildren(NVGcontext* vg, const rct_t& r) {
	if( type() == direction_t::HORIZONTAL && contains(alignment(),align_t::TOP) && contains(alignment(),align_t::BOTTOM) ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->h( std::max(c->minSize().h, r.h ) );
			c->reform(vg,autoscale_t::W);
		}
	}
	else if( type() == direction_t::VERTICAL && contains(alignment(),align_t::LEFT) && contains(alignment(),align_t::RIGHT) ) {
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			c->w( std::max( c->minSize().w, r.w ) );
			c->reform(vg,autoscale_t::H);
		}
	}
}

inline void Aligner::alignChildren(NVGcontext* vg, const rct_t& r) {
	if( type() == direction_t::HORIZONTAL ) {
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

inline void Aligner::rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling){
	autoscale_t sc = autoscale()&scaling;
	alignChildren(vg, r);
	fitAllChildren(vg, r);
	alignChildren(vg, r);
	updateContentsRect(vg);

	if( type() == direction_t::HORIZONTAL && contains(sc,autoscale_t::H) )
		h(_contentsRect.h);
	if( type() == direction_t::VERTICAL && contains(sc,autoscale_t::W) )
		w(_contentsRect.w);

	bool resizableFound = checkResizable();

	fitAllChildren(vg, r);
	alignChildren(vg, r);
	updateContentsRect(vg);
	
	if( resizableFound ) {
		if( type() == direction_t::HORIZONTAL ) {
			float resizableSz = _setSize.w - contentsRect().w + resizable()->w();
			resizableSz = std::max( resizableSz, resizable()->minSize().w );
			resizable()->w( resizableSz );
			resizable()->reform(vg,autoscale_t::ALL);
		}
		else {
			float resizableSz = _setSize.h - contentsRect().h + resizable()->h();
			resizableSz = std::max( resizableSz, resizable()->minSize().h );
			resizable()->h( resizableSz );
			resizable()->reform(vg,autoscale_t::ALL);
		}
	}
	alignChildren(vg, r);
}


inline void Aligner::rearrange(NVGcontext* vg,autoscale_t scaling) {
	{
		std::unique_lock<std::mutex> lock(_childMutex);
		for( auto c: _children ) if( c ) {
			if( c->changed() ) c->reform(vg,autoscale_t::ALL);
		}
	}
	autoscale_t sc = autoscale()&scaling;

	if( changed() ) {
		rearrangeChildren(vg, paddedRect(),scaling);
		updateContentsRect(vg);

		if( type() == direction_t::HORIZONTAL && contains(sc,autoscale_t::W))
			_setSize.w = std::max(_contentsRect.w,_setSize.w);
		if( type() == direction_t::VERTICAL && contains(sc,autoscale_t::H))
			_setSize.h = std::max(_contentsRect.h,_setSize.h);

		_bound.wh() = max(_setSize, minSize() );
	}
	_changed = false;
//	_Scrollable::scrollRange( size(), contentsRect(), alignment() );
}

inline void Aligner::spacing( float s ) {
	_spacing = s;
	change();
}

inline sz2_t Aligner::minSize() const {
	float ww = 0, hh = 0;
	if( _type == direction_t::VERTICAL ) hh = spacing();
	else					ww = spacing();
	for(const auto c: _children ){
		auto sz = c->minSize();
		if( _type == direction_t::VERTICAL ) {
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

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Aligner_hpp */
