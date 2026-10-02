//
//  Tabular.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Tabular_hpp
#define JGL2_Tabular_hpp

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <mutex>

#include <JGL2/Aligner.hpp>

namespace JGL2 {

struct Tabular : public Aligner {
	Tabular(float x=0, float y=0, float w=10, float h=10, const str_t& t="Tabular" );
	Tabular(const pos_t& pos, const sz2_t& sz, const str_t& t="Tabular" );
	Tabular(const sz2_t& sz, const str_t& t="Tabular" );

	virtual void		rearrange(NVGcontext*,autoscale_t scaling) override;
	virtual sz2_t		minSize() const override;
	virtual int			columns() const;
	virtual void		columns(int n);
	virtual int			rows() const;
	virtual int			visibleChildren() const;
	virtual float		spacing() const override { return _spacing<0?_size_splitter_spacing():_spacing; }
protected:
	virtual void		alignChildren(NVGcontext* vg, const rct_t& r) override;
	virtual void		rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling) override;
	virtual void		drawContents(NVGcontext* vg, const rct_t& r, align_t align) override;

	float				_spacing = 0;
	int					_columns = 0;
};

} // namespace JGL2

namespace JGL2 {

inline Tabular::Tabular(float x, float y, float w, float h, const str_t& t )
: Aligner( x, y, w, h, t ) {
	alignment( align_t::ALL );
}

inline Tabular::Tabular(const pos_t& pos, const sz2_t& sz, const str_t& t )
: Aligner( pos, sz, t ) {
	alignment( align_t::ALL );
}

inline Tabular::Tabular(const sz2_t& sz, const str_t& t )
: Aligner( pos_t(0,0), sz, t ) {
	alignment( align_t::ALL );
}

inline int Tabular::visibleChildren() const {
	int count = 0;
	for( const auto& c: _children )
		if( c && !c->hidden() ) count++;
	return count;
}

inline int Tabular::columns() const {
	if( _columns>0 ) return _columns;
	return int(ceilf(sqrtf(float(visibleChildren()))));
}
inline void Tabular::columns(int n) {
	_columns = n;
	changed();
}

inline int Tabular::rows() const {
	return int(ceil(visibleChildren()/float(columns())));
}


inline void Tabular::alignChildren(NVGcontext* vg, const rct_t& r) {
	int cs = columns();
	int rs = rows();
	float ww = (r.w-(cs-1)*spacing())/cs;
	float hh = (r.h-(rs-1)*spacing())/rs;

	std::vector<float> widths(cs,ww);
	std::vector<float> heights(rs,hh);

	int count = 0;
	for( const auto c : _children ) {
		int xx = count%cs;
		int yy = count/cs;
		if( c && !c->hidden() ) {
			widths [xx] = std::max( widths[xx],  c->minSize().w );
			heights[yy] = std::max( heights[yy], c->minSize().h );
			count++;
		}
	}
	std::vector<float> xxs(cs,0);
	std::vector<float> yys(rs,0);
	for( int i=0; i<widths .size()-1; i++ ) xxs[i+1] = xxs[i]+widths[i]+spacing();
	for( int i=0; i<heights.size()-1; i++ ) yys[i+1] = yys[i]+heights[i]+spacing();
	count = 0;
	for( const auto c : _children ) {
		int xx = count%cs;
		int yy = count/cs;
		if( c && !c->hidden() ) {
			c->x(xxs[xx]);
			c->y(yys[yy]);
			c->w(widths[xx]);
			c->h(heights[yy]);
			c->reform(vg,autoscale_t::ALL);
			count++;
		}
	}
	w(xxs[cs-1]+spacing()+widths[cs-1]);
	h(yys[rs-1]+spacing()+heights[rs-1]);
}

inline void Tabular::rearrangeChildren(NVGcontext* vg, const rct_t& r, autoscale_t scaling){
	alignChildren(vg, r);
	updateContentsRect(vg);
}


inline void Tabular::rearrange(NVGcontext* vg,autoscale_t scaling) {
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

		if( contains(sc,autoscale_t::W))
			_setSize.w = std::max(_contentsRect.w,_setSize.w);
		if( contains(sc,autoscale_t::H))
			_setSize.h = std::max(_contentsRect.h,_setSize.h);
		_bound.wh() = max(_setSize, minSize() );
	}
	_changed = false;
}

inline sz2_t Tabular::minSize() const {
	int cs = columns();
	int rs = rows();

	std::vector<float> widths(cs,0);
	std::vector<float> heights(rs,0);

	int count = 0;
	for( const auto c : _children ) {
		int xx = count%cs;
		int yy = count/cs;
		if( c && !c->hidden() ) {
			widths [xx] = std::max( widths[xx],  c->minSize().w );
			heights[yy] = std::max( heights[yy], c->minSize().h );
			count++;
		}
	}
	float ww = 0;
	float hh = 0;
	for( int i=0; i<widths .size(); i++ ) ww = ww+widths[i]+spacing();
	for( int i=0; i<heights.size(); i++ ) hh = hh+heights[i]+spacing();

	return sz2_t(ww-spacing(),hh-spacing());
}

inline void Tabular::drawContents(NVGcontext* vg, const rct_t& r, align_t align) {
	Aligner::drawContents(vg, r, align);

	std::unique_lock<std::mutex> lock(_childMutex);
	int cs = columns();
	int rs = rows();
	for( int i=1; i<cs; i++ ) {
		if( !child(i)->hidden() )
			_draw_splitter_separator_horz(vg, r, child(i)->x() );
	}
	for( int i=1; i<rs; i++ )
		if( !child(i)->hidden() )
			_draw_splitter_separator_vert(vg, r, child(i*cs)->y() );
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Aligner_hpp */
