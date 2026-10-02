//
//  Plotter.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Plotter_h
#define JGL2_Plotter_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>
#include <JGL2/Widget.hpp>
#include <memory>

namespace JGL2 {

struct series_t;
struct scatter_t;

using series_list_t = std::vector<series_t>;
using scatter_list_t = std::vector<scatter_t>;

inline color_t HSV(const color_t& hsv) {
	color_t rgb(0);
	rgb.r = std::clamp( 5*abs(hsv.r-3.f/5.f)-1.f,0.f,1.f);
	rgb.g = std::clamp(-5*abs(hsv.r-2.f/5.f)+2,0.f,1.f);
	rgb.b = std::clamp(-5*abs(hsv.r-4.f/5.f)+2,0.f,1.f);
	rgb = mix(color_t(1,1,1),rgb,hsv.g);
	return rgb*hsv.b;
}

inline NVGcolor nvgRGBA(const colora_t& c) { return nvgRGBAf(c.r,c.g,c.b,c.a); }

struct Plotter;

struct series_t : public flst_t {
	enum class style_t {
		NONE = 0,
		DOTTED = 1,
		LINED = 2,
	};
	series_t(){}
	series_t( const colora_t& c, float w = 3, style_t s=style_t::DOTTED ):color(c),width(w),style(s){}
	series_t( flst_t&& v ): flst_t( std::move(v)) {}
	series_t( const flst_t& v ): flst_t(v) {}
	series_t( const flst_t& v, const colora_t& c, float w = 3, style_t s=style_t::DOTTED ): flst_t(v), color(c), width(w), style(s) {}
	series_t( const flst_t& v, float w, const colora_t& c=colora_t(0), style_t s=style_t::DOTTED ): flst_t(v), color(c), width(w), style(s) {}
	series_t( const flst_t& v, style_t s, float w=3, const colora_t& c=colora_t(0) ): flst_t(v), color(c), width(w), style(s) {}
	series_t( const series_t& other ): flst_t(other), width(other.width), color(other.color), style(other.style){}
	series_t( series_t&& other ): flst_t(std::move(other)), width(other.width), color(other.color), style(other.style){}

	virtual	series_t&	operator=( const flst_t& other )		{ flst_t::operator=(other); return *this; }
	virtual	series_t&	operator=( flst_t&& other )			{ flst_t::operator=(other); return *this; }
	virtual	series_t&	operator=( std::initializer_list<float> ilist){ flst_t::operator=(ilist); return *this; }
	virtual	series_t&	operator=( const series_t& other )			{ flst_t::operator=(other); width=other.width; color=other.color; style=other.style; return *this; }
	virtual	series_t&	operator=( series_t&& other )					{ flst_t::operator=(other); width=other.width; color=other.color; style=other.style; return *this; }
	virtual	float		min() const { return *std::min_element(cbegin(), cend()); }
	virtual	float		max() const { return *std::max_element(cbegin(), cend()); }
	virtual	void		setData( const flst_t& v ) { flst_t::operator = (v); }

	virtual	void		draw(const Plotter& plt, NVGcontext* vg, const rct_t& r, const llst_t& sortedXIndices ) const;

	colora_t			color = colora_t(0,0,0,0);
	float				width = 2;
	style_t				style = style_t::DOTTED;
	bool				drawEnabled = true;
};



struct scatter_t : public plst_t {
	void updateSortedXList() {
		_sortedXIndices.resize( size() );
		for( size_t i=0; i<size(); i++ ) _sortedXIndices[i] = i;
		std::sort( _sortedXIndices.begin(), _sortedXIndices.end(), [&](auto a, auto b) { return at(a).x<at(b).x; });
	}
	void setData(const flst_t& x, const flst_t& y ) {
		assert( x.size() == y.size() );
		resize(x.size());
		for( size_t i=0; i<x.size(); i++ ) at(i)=pos_t(x[i],y[i]);
		updateSortedXList();
	}
	scatter_t( const colora_t& c, float w = 3, series_t::style_t s=series_t::style_t::DOTTED ):color(c),width(w),style(s){}
	scatter_t( const plst_t& v): plst_t(v) { updateSortedXList(); }
	scatter_t( const flst_t& x, const flst_t& y ) { setData(x,y); }
	scatter_t( const flst_t& x, const series_t& y )
	: width(y.width), color(y.color), style(y.style) { setData(x,y); }
	scatter_t( const flst_t& x, const flst_t& y, const colora_t& c, float w = 3, series_t::style_t s=series_t::style_t::DOTTED )
	: color(c), width(w), style(s) { setData(x,y); }
	scatter_t( const flst_t& x, const flst_t& y, float w, const colora_t& c=colora_t(0), series_t::style_t s=series_t::style_t::DOTTED )
	: color(c), width(w), style(s) { setData(x,y); }
	scatter_t( const flst_t& x, const flst_t& y, series_t::style_t s, float w=3, const colora_t& c=colora_t(0) )
	: color(c), width(w), style(s) { setData(x,y); }

	scatter_t( const scatter_t& other )
	: plst_t(other), width(other.width), color(other.color), style(other.style), _sortedXIndices(other._sortedXIndices) {}
	scatter_t( scatter_t&& other )
	: plst_t(std::move(other)), width(other.width), color(other.color), style(other.style), _sortedXIndices(std::move(other._sortedXIndices)) {}

	scatter_t& operator=( const std::pair<std::initializer_list<float>,std::initializer_list<float>>& ilist ) {
		setData( ilist.first, ilist.second);
		return *this;
	}
	scatter_t& operator=( const scatter_t& other ) {
		width=other.width; color=other.color; style=other.style;
		plst_t::operator=(other);
		_sortedXIndices=other._sortedXIndices;
		return *this;
	}
	scatter_t& operator=( scatter_t&& other ) {
		width=other.width; color=other.color; style=other.style;
		plst_t::operator=(std::move(other));
		_sortedXIndices=std::move(other._sortedXIndices);
		return *this;
	}
	
	float min() const { return (*std::min_element(cbegin(), cend(),[](auto a,auto b){ return a.y<b.y; })).y; }
	float max() const { return (*std::max_element(cbegin(), cend(),[](auto a,auto b){ return a.y<b.y; })).y; }
	float minX() const { return (*std::min_element(cbegin(), cend(),[](auto a,auto b){ return a.x<b.x; })).x; }
	float maxX() const { return (*std::max_element(cbegin(), cend(),[](auto a,auto b){ return a.x<b.x; })).x; }
	void draw(const Plotter& plt, NVGcontext* vg, const rct_t& r ) const;

	llst_t _sortedXIndices;
	colora_t color = colora_t(0,0,0,0);
	float width = 2;
	series_t::style_t style = series_t::style_t::DOTTED;
	bool	drawEnabled = true;
};

inline series_t::style_t operator|(series_t::style_t a, series_t::style_t b) {
	return static_cast<series_t::style_t>(static_cast<int>(a) | static_cast<int>(b));
}

struct GridInfo {
	float start  =0.f;
	float step	 =1.f;
	float scale  =1.f;
	float offset =0.f;
	size_t count = 1;
	//char formatString[100];
	int labelDigit = 1;

	inline static float bestDataStep( float ss, float minImageStep=50 ) {
		float min_data_step = minImageStep/ss;
/*		float step2 = pow(2, ceil( log2(min_data_step) ) );
		float step5 = pow(5, ceil( log10(min_data_step)/log10(5) ) );
		float step10= pow(10, ceil( log10(min_data_step) ) );
		return std::min( {step2, step5, step10} );
 */

		float step10= powf(10.f, ceilf( log10f(min_data_step) ) );
		if( step10/5.f>min_data_step ) return step10/5.f;
		if( step10/2.f>min_data_step ) return step10/2.f;
		return step10;
	}
	GridInfo() {}
	GridInfo( float w, float x, float margin, float x0, float range, float sc, float off, float minImageStep=50) {
		float ww =w*(1-margin*2);
		float xx =x+w*margin;
		scale = ww/range*sc;
		offset = off*ww + xx - x0*scale;
		step = bestDataStep( scale, minImageStep );
		float x_0 = -offset/scale;
		start = sign(x_0)*ceil(abs(x_0)/step)*step;
		count = int(ceil(w/scale/step))+1;
		
		labelDigit = std::max(0,(int)ceil(-log10(step)));
	}
	float toImage(float x) const { return scale*x+offset; }
	float getX(size_t i) const { return start+i*step; }
	std::tuple<float,str_t> getLabel(size_t i) const {
		float x = getX(i);
		float xx = toImage(x);
		return std::make_tuple(xx,toStr(x,labelDigit));
	}
};

struct Plotter : public Widget, public _Targettable {
	Plotter( float x, float y, float w, float h, const str_t& name="Plot");
	Plotter( const pos_t& pos, const sz2_t& sz, const str_t& name="Plot");
	virtual void				addSeries( const series_t& y );
	virtual void				addSeries( const flst_t& y, const colora_t& c=colora_t(0), float w=3, series_t::style_t s=series_t::style_t::DOTTED );
	virtual void				addSeries( const flst_t& y, series_t::style_t s, const colora_t& c=colora_t(0), float w=3 );
	virtual void				updateSeries( size_t i, const series_t& y );
	virtual void				updateSeries( size_t i, const flst_t& y );
	
	virtual void				addScatter( const flst_t& x, const series_t& y );
	virtual void				addScatter( const flst_t& x, const flst_t& y, const colora_t& c=colora_t(0), float w=3, series_t::style_t s=series_t::style_t::DOTTED );
	virtual void				addScatter( const flst_t& x, const flst_t& y, series_t::style_t s, const colora_t& c=colora_t(0), float w=3 );

	
	virtual series_t&			series(size_t i) { if( i>=_series.size() ) throw std::out_of_range("Out of range"); return _series[i]; }
	virtual const series_t&		series(size_t i) const { if( i>=_series.size() ) throw std::out_of_range("Out of range"); return _series[i]; }

	virtual scatter_t&			scatter(size_t i) { if( i>=_scatters.size() ) throw std::out_of_range("Out of range"); return _scatters[i]; }
	virtual const scatter_t&	scatter(size_t i) const { if( i>=_scatters.size() ) throw std::out_of_range("Out of range"); return _scatters[i]; }
	virtual void				clearSerises();
	virtual void				clear();
	virtual void				allocateSerieses(size_t n);
	virtual void				allocateScatters(size_t n);

	
	virtual void				setX( const flst_t& x );
	virtual flst_t&				xAxis() { return _xAxis; }
	virtual const flst_t&		xAxis() const { return _xAxis; }
	virtual rct_t				range() const { return _range; }
	virtual void				range(const rct_t& r) { _range = r; _autoRange=false; }
	virtual void				enableAutoRange() { _autoRange=true; updateRange(); }

	virtual const colora_t		gridColor() const { return _gridColor; }
	virtual const colora_t		axesColor() const { return _axesColor; }
	virtual const colora_t		textColor() const { return _textColor; }
	virtual void				gridColor( const colora_t& color ) { _gridColor = color; redraw(); }
	virtual void				axesColor( const colora_t& color ) { _axesColor = color; redraw(); }
	virtual void				textColor( const colora_t& color ) { _textColor = color; redraw(); }

	virtual float				gridWidth() const { return _gridWidth; }
	virtual float				axesWidth() const { return _axesWidth; }
	virtual void				gridWidth( float w ) { _gridWidth = w; redraw(); }
	virtual void				axesWidth( float w ) { _axesWidth = w; redraw(); }

	virtual float				textSize() { return _textSize; }
	virtual void				textSize( float sz ) { _textSize = sz; redraw(); }
	
	virtual const colora_t		guideColor() const { return _guideColor; }
	virtual const colora_t		guideLabelColor() const { return _guideLabelColor; }
	virtual const colora_t		guideLabelBkColor() const { return _guideLabelBkColor; }
	virtual float				guideLabelSize() const { return _guideLabelSize; }

	virtual void				guideColor(const colora_t& c) { _guideColor=c; }
	virtual void				guideLabelColor(const colora_t& c) { _guideLabelColor=c; }
	virtual void				guideLabelBkColor(const colora_t& c) { _guideLabelBkColor=c; }
	virtual void				guideLabelSize(float v) { _guideLabelSize=v; }

	
	virtual void				updateRange();
	virtual void				updateGrid();
	virtual void				updateGuide();
	virtual void				fit();
	virtual void				scroll(const pos_t& d);
	virtual void				zoom(float x);
	virtual void				zoom(float x, const pos_t& pt);
	virtual void				zoomY(float x, const pos_t& pt);
	virtual void				moveGuide(const pos_t& pt);

	
	virtual bool				handle( event_t e ) override;
	virtual void				drawContents( NVGcontext* vg, const rct_t& r, align_t align ) override;
	virtual colora_t			autoColor( const colora_t& c);
	virtual float				toImageX(float x) const;
	virtual float				toImageY(float y) const;
	virtual pos_t				toImage(const pos_t& p) const;
	virtual float				screenX(size_t i) const;

	virtual void 				drawGuideLabel(NVGcontext* vg, bool vert, const pos_t pt, const rct_t& screen, const str_t& str, float labelSz, float padding, float margin, float arrowLength, float arrowWidth );
	
	virtual void				drawGrids(NVGcontext* vg, const rct_t& r);
	virtual void				drawPlot(NVGcontext* vg, const rct_t& r);
	virtual void				drawGuide(NVGcontext* vg, const rct_t& r);

	series_list_t	 			_series;
	scatter_list_t 				_scatters;
	flst_t						_xAxis;
	llst_t						_sortedXIndices;

	bool						_autoRange = true;
	rct_t						_range = rct_t(0,0,1,1);

	pos_t						_scale = pos_t(1);
	pos_t						_margin = pos_t(0.05f);
	pos_t						_offset = pos_t(0,0);
	GridInfo					_gridX;
	GridInfo					_gridY;


	colora_t					_gridColor = colora_t(.25,.25,.25,.5);
	float						_gridWidth = 1.f;
	colora_t					_axesColor = colora_t(0,0,0,1);
	float						_axesWidth = 2.f;
	colora_t					_textColor = colora_t(0,0,0,1);
	float						_textSize = 9;
	colora_t					_guideColor = colora_t(1,0,0,.5);
	colora_t					_guideLabelColor = colora_t(1,0,0,1);
	colora_t					_guideLabelBkColor = colora_t(_color_background().r,_color_background().g,_color_background().b,_color_background().a);
	float						_guideLabelSize = 10;

	bool						_logScaleX = false;
	bool						_logScaleY = false;
	bool						_fitted = true;
	
	pos_t						_lastPt = pos_t(0);
	bool						_mouseOnScreen = false;
	float						_guide = NAN;
	flst_t						_guideY;
};

} // namespace JGL2

#include <JGL2/_Draw.hpp>

namespace JGL2 {

inline void series_t::draw(const Plotter& plt, NVGcontext* vg, const rct_t& r, const llst_t& sortedXIndices ) const {
	if( size()<1 ) return;
	if( !drawEnabled ) return;
	nvgFillColor( vg, nvgRGBA(color));
	nvgStrokeColor( vg, nvgRGBA(color));
	nvgStrokeWidth( vg, width );
	
	if( sortedXIndices.size()>0 ) {
		if( int(style) & int(style_t::DOTTED) ) {
			for( auto i: sortedXIndices ) {
				if( i>=size() ) continue;
				nvgBeginPath(vg);
				nvgCircle(vg, plt.screenX(i), plt.toImageY(at(i)), width );
				nvgFill(vg);
			}
		}
		if( int(style) & int(style_t::LINED) ) {
			if( sortedXIndices.size()>0 ) {
				nvgBeginPath(vg);
				size_t j=0;
				while( sortedXIndices[j]>=size() ) j++;
				auto i=sortedXIndices[j];
				nvgMoveTo(vg, plt.screenX(i), plt.toImageY(at(i)));
				for( j++; j<sortedXIndices.size(); j++ ) {
					auto i=sortedXIndices[j];
					if( i>=size() ) continue;
					nvgLineTo(vg, plt.screenX(i), plt.toImageY(at(i)) );
				}
				nvgStroke(vg);
			}
		}
	}
	else {
		if( int(style) & int(style_t::DOTTED) ) {
			for( size_t i=0; i<size(); i++ ) {
				nvgBeginPath(vg);
				nvgCircle(vg, plt.toImageX(float(i)), plt.toImageY(at(i)), width );
				nvgFill(vg);
			}
		}
		if( int(style) & int(style_t::LINED) ) {
			nvgBeginPath(vg);
			nvgMoveTo(vg,plt.toImageX(0),plt.toImageY(at(0)));
			for( size_t i=1; i<size(); i++ )
				nvgLineTo(vg, plt.toImageX(float(i)), plt.toImageY(at(i)));
			nvgStroke(vg);
		}
	}
}

inline void scatter_t::draw(const Plotter& plt, NVGcontext* vg, const rct_t& r ) const {
	if( size()<1 ) return;
	if( !drawEnabled ) return;
	nvgFillColor( vg, nvgRGBA(color) );
	nvgStrokeColor( vg, nvgRGBA(color) );
	nvgStrokeWidth( vg, width );
	if( int(style) & int(series_t::style_t::DOTTED) ) {
		for( auto i: _sortedXIndices ) {
			nvgBeginPath(vg);
			auto pt = plt.toImage(at(i));
			nvgCircle(vg, pt.x, pt.y, width );
			nvgFill(vg);
		}
	}
	if( int(style) & int(series_t::style_t::LINED) ) {
		nvgBeginPath(vg);
		size_t j=0;
		auto i=_sortedXIndices[j];
		auto pt = plt.toImage(at(i));
		nvgMoveTo(vg, pt.x, pt.y);
		for( j++; j<_sortedXIndices.size(); j++ ) {
			auto i=_sortedXIndices[j];
			auto pt = plt.toImage(at(i));
			nvgLineTo(vg, pt.x, pt.y );
		}
		nvgStroke(vg);
	}
}

inline str_t guideLabelText(float value, float valuePerPixel) {
	int gridXDigits = (int)(-ceil(log10(valuePerPixel))+1);
	return toStr(value,gridXDigits);
}

inline void nvgDrawPinned(NVGcontext* vg, const rct_t& box, const pos_t pt, float arrowWidth, float boxr) {
	float l=box.x, r=box.tr().x, t=box.y, b=box.bl().y;
	float alx = std::min(std::max(pt.x-arrowWidth,l),r-arrowWidth*2), arx = alx+arrowWidth*2;
	float aty = std::min(std::max(pt.y-arrowWidth,t),b-arrowWidth*2), aby = aty+arrowWidth*2;

	if( pt.y<t ) {
		nvgMoveTo(vg,pt.x,pt.y);
		if( alx>l ) 		nvgLineTo(vg,alx,t);
		if( alx>l+boxr )	nvgLineTo(vg,l+boxr,t);
		if( alx>l )			nvgQuadTo(vg,l,t,l,t+boxr);
		if( alx<=l )		nvgLineTo(vg,l,t+boxr);
		nvgLineTo(vg,l,b-boxr);
		nvgQuadTo(vg,l,b,l+boxr,b);
		nvgLineTo(vg,r-boxr,b);
		nvgQuadTo(vg,r,b,r,b-boxr);
		nvgLineTo(vg,r,t+boxr);
		if( arx<r )			nvgQuadTo(vg,r,t,std::max(r-boxr,arx),t);
		if( arx<r-boxr )	nvgLineTo(vg,arx,t);
		nvgClosePath(vg);
	}
	else if( pt.y>=t && pt.y<=b) {
		if( pt.x<l ) {
			nvgMoveTo(vg,pt.x,pt.y);
			nvgLineTo(vg,l,aby);
			if( aby<b-boxr )	nvgLineTo(vg,l,b-boxr);
			if( aby<b )			nvgQuadTo(vg,l,b,l+boxr,b);
			nvgLineTo(vg,r-boxr,b);
			nvgQuadTo(vg,r,b,r,b-boxr);
			nvgLineTo(vg,r,t+boxr);
			nvgQuadTo(vg,r,t,r-boxr,t);
			nvgLineTo(vg,l+boxr,t);
			if( aty>t )			nvgQuadTo(vg,l,t,l,std::min(t+boxr,aty));
			if( aty>t+boxr )	nvgLineTo(vg,l,aty);
			nvgClosePath(vg);
		}
		else if( pt.x<=r ) {
			nvgRoundedRect(vg, l, t, r-l, b-t, boxr);
		}
		else {
			nvgMoveTo(vg,pt.x,pt.y);
			nvgLineTo(vg,r,aty);
			if( aty>t+boxr )	nvgLineTo(vg,r,t+boxr);
			if( aty>t )			nvgQuadTo(vg,r,t,r-boxr,t);
			nvgLineTo(vg,l+boxr,t);
			nvgQuadTo(vg,l,t,l,t+boxr);
			nvgLineTo(vg,l,b-boxr);
			nvgQuadTo(vg,l,b,l+boxr,b);
			nvgLineTo(vg,r-boxr,b);
			if( aby<b )			nvgQuadTo(vg,r,b,r,std::max(b-boxr,aby));
			if( aby<b-boxr )	nvgLineTo(vg,r,aby);
			nvgClosePath(vg);
		}
	}
	else {
		nvgMoveTo(vg,pt.x,pt.y);
		nvgLineTo(vg,arx,t);
		if( arx<r-boxr )	nvgLineTo(vg,r-boxr,b);
		if( arx<r )			nvgQuadTo(vg,r,b,r,b-boxr);
		nvgLineTo(vg,r,t+boxr);
		nvgQuadTo(vg,r,t,r-boxr,t);
		nvgLineTo(vg,l-boxr,t);
		nvgQuadTo(vg,l,t,l,t+boxr);
		nvgLineTo(vg,l,b-boxr);
		if( alx>l )			nvgQuadTo(vg,l,b,std::min(l+boxr,alx),b);
		if( alx>l+boxr )	nvgLineTo(vg,alx,b);
		nvgClosePath(vg);
	}
}

inline Plotter::Plotter( float x, float y, float w, float h, const str_t& name)
: Widget( x, y, w, h, name), _Targettable(false) { alignment(align_t::TOP|align_t::SIDE); }

inline Plotter::Plotter( const pos_t& pos, const sz2_t& sz, const str_t& name)
: Widget( pos, sz, name), _Targettable(false) { alignment(align_t::TOP|align_t::SIDE); }

inline void Plotter::clear() {
	_xAxis.clear();
	_sortedXIndices.clear();
	_series.clear();
	_scatters.clear();
}

inline void Plotter::clearSerises() {
	_series.clear();
}

inline void Plotter::setX( const std::vector<float>& x ) {
	_xAxis = x;
	_sortedXIndices.resize( _xAxis.size() );
	for( size_t i=0; i<_xAxis.size(); i++ ) _sortedXIndices[i] = i;
	sort( _sortedXIndices.begin(), _sortedXIndices.end(), [&](auto a, auto b) {
		return _xAxis[a]<_xAxis[b];
	});
	updateRange();
}


inline colora_t Plotter::autoColor( const colora_t& c) {
	if( c.a>0.001 ) return c;
	else return colora_t(HSV({fract((_series.size()+_scatters.size()+1)*0.62f),1.f,.5}),1.f);
}

inline void Plotter::addSeries( const series_t& y ) {
	_series.push_back(y);
	updateRange();
}

inline void Plotter::addSeries( const flst_t& y, const colora_t& c, float w, series_t::style_t s ) {
	_series.push_back({y,autoColor(c),w,s});
	updateRange();
}
inline void Plotter::addSeries( const flst_t& y, series_t::style_t s, const colora_t& c, float w ) {
	_series.push_back({y,autoColor(c),w,s});
	updateRange();
}

inline void Plotter::updateSeries( size_t i, const series_t& y ) {
	if( i>=_series.size() ) throw std::out_of_range("Out of range");
	_series[i] = y;
	updateRange();
}

inline void Plotter::updateSeries( size_t i, const flst_t& y ) {
	if( i>=_series.size() ) throw std::out_of_range("Out of range");
	_series[i] = y;
	updateRange();
}

inline void Plotter::addScatter( const flst_t& x, const series_t& y ) {
	_scatters.emplace_back(x,y,autoColor(colora_t(0)));
	updateRange();
}

inline void Plotter::addScatter( const flst_t& x, const flst_t& y, const colora_t& c, float w, series_t::style_t s ) {
	_scatters.emplace_back(x,y,autoColor(c),w,s);
	updateRange();
}

inline void Plotter::addScatter( const flst_t& x, const flst_t& y, series_t::style_t s, const colora_t& c, float w ) {
	_scatters.emplace_back(x,y,autoColor(c),w,s);
	updateRange();
}

inline void Plotter::allocateScatters(size_t n) {
	for( size_t i=0; i<n; i++ )
		_scatters.emplace_back(autoColor(colora_t(0)));
}

inline void Plotter::allocateSerieses(size_t n) {
	for( size_t i=0; i<n; i++ )
		_series.emplace_back(autoColor(colora_t(0)));
}

inline void Plotter::updateRange() {
	if( !_autoRange ) return;
	float x_min = 100000000, y_min = 100000000;
	float x_max = -100000000, y_max = -100000000;
	size_t count_max = 0;
	for( const auto& s: _series ) {
		if( s.size()>0 ) {
			y_min = std::min( y_min, s.min() );
			y_max = std::max( y_max, s.max() );
			count_max = std::max( count_max, s.size()-1 );
		}
	}
	for( const auto& s: _scatters ) {
		if( s.size()>0 ) {
			y_min = std::min( y_min, s.min() );
			y_max = std::max( y_max, s.max() );
		}
	}
	if( _xAxis.size()>0 ) {
		x_min = *std::min_element( _xAxis.begin(), _xAxis.end() );
		x_max = *std::max_element( _xAxis.begin(), _xAxis.end() );
	}
	for( const auto& s: _scatters ) {
		if( s.size()>0 ) {
			x_min = std::min( x_min, s.minX() );
			x_max = std::max( x_max, s.maxX() );
		}
	}
	if( y_min>y_max )	{ _range.h = 0; _range.y = 0; }
	else				{ _range.h = y_max - y_min; _range.y = y_min; }

	if( x_min>x_max )	{ _range.w = float(count_max); _range.x = 0; }
	else				{ _range.w = x_max - x_min; _range.x = x_min; }
	redraw();
	if( _fitted ) fit();
}

inline void Plotter::fit() {
	_offset=pos_t(0);
	_scale =pos_t(1);
	redraw();
}

inline void Plotter::updateGrid() {
}

inline void Plotter::scroll( const pos_t& d ) {
	_offset.x+=d.x/w();
	_offset.y-=d.y/h();
	redraw();
}

inline void Plotter::zoom( float x) {
	zoom(x, {w()/2,h()/2} );
}

inline void Plotter::zoom( float x, const pos_t& p) {
	pos_t pivot = { p.x, h()-p.y };
	float scale = powf(1.2f,x);
	_scale*=scale;
	_offset = scale*_offset + (1-scale) * pivot / pos_t(w(),h());
	redraw();
}

inline void Plotter::zoomY( float x, const pos_t& p) {
	pos_t pivot = { p.x, h()-p.y };
	float scale = powf(1.2f,x);
	_scale.y*=scale;
	_offset.y = scale*_offset.y + (1-scale) * pivot.y / h();
	redraw();
}

inline void Plotter::updateGuide() {
	_guideY.resize(_series.size(), NAN );
	size_t l=0, r=0;
	float t=0;
	if( _sortedXIndices.size()>0 ) {
		for( size_t i=0; i<_sortedXIndices.size()-1; i++ ) {
			r = _sortedXIndices[i+1];
			if( _xAxis[r]>_guide ) {
				l = _sortedXIndices[i];
				t = (_guide-_xAxis[l])/(_xAxis[r]-_xAxis[l]);
				break;
			}
		}
	}
	else {
		l = size_t(floor(_guide));
		r = l+1;
		t = _guide - l;
	}
	for( size_t j=0; j<_series.size(); j++ ) {
		if( series(j).size()>l && series(j).size()>r )
			_guideY[j] = mix( _series[j][l], _series[j][r], t );
	}
	redraw();
}

inline void Plotter::moveGuide( const pos_t& pt) {
	_guide = (pt.x-_gridX.offset)/_gridX.scale;
	_guide = std::clamp(_guide,_range.x,_range.tr().x);
	updateGuide();
}

inline bool Plotter::handle( event_t e ) {
	switch( e ) {
		case event_t::SCROLL:
			if( _JGL::eventMods(mod_t::CONTROL) )
				if( _JGL::eventMods(mod_t::SHIFT) )
					zoomY( -_JGL::eventScrollY()*.3f, _lastPt );
				else
					zoom( -_JGL::eventScrollY()*.3f, _lastPt );
			else
				scroll( {-_JGL::eventScrollX()*3.f, -_JGL::eventScrollY()*3.f} );
			return true;
		case event_t::DRAG: {
				pos_t pt = _JGL::eventPt();
				if( _JGL::eventMods(mod_t::CONTROL) )
					scroll( pt-_lastPt );
				else
					moveGuide(pt);
				_lastPt = pt;
			}
			return true;
		case event_t::LEAVE:
			_mouseOnScreen = false;
			break;;
		case event_t::ENTER:
			_mouseOnScreen = true;
			break;
		case event_t::MOVE:
			_lastPt = _JGL::eventPt();
			_mouseOnScreen = true;
			return true;
		case event_t::PUSH :
			_lastPt = _JGL::eventPt();
			moveGuide(_lastPt);
			return true;
		case event_t::ZOOM:
			if( _JGL::eventMods(mod_t::SHIFT) )
				zoomY( _JGL::eventZoom()*2.f, _lastPt );
			else
				zoom( _JGL::eventZoom()*2.f, _lastPt );
			return true;
		case event_t::KEYDOWN:
			if( _JGL::eventKey()==GLFW_KEY_ENTER ) {
				fit();
				return true;
			}
			break;
		default:
			break;
	}
	return Widget::handle(e);
}

inline float Plotter::toImageX(float x) const { return _gridX.toImage(x); }
inline float Plotter::toImageY(float y) const { return h()-_gridY.toImage(y); }
inline float Plotter::screenX(size_t i) const { return toImageX(_xAxis[i]); }
inline pos_t Plotter::toImage(const pos_t& p) const { return pos_t(_gridX.toImage(p.x), h()-_gridY.toImage(p.y)); }

inline void Plotter::drawGuideLabel(NVGcontext* vg, bool vert, const pos_t pt, const rct_t& screen, const str_t& str, float labelSz, float padding, float margin, float arrowLength, float arrowWidth ) {
	float boxr = 3;
	sz2_t tSz = nvgMeasureText(vg, str, labelSz);
	rct_t box( 0, 0, tSz.w+padding*2, tSz.h+padding*2 );
	box.x = std::min(screen.w-margin-box.w, std::max(margin,pt.x+(vert?(-box.w/2.f):(arrowLength+margin))) );
	box.y = vert?(screen.h-box.h-margin):(pt.y-box.h/2);
	pos_t ppt = pt;
	nvgBeginPath(vg);
	if( vert ) ppt.y = box.y-arrowLength;
	nvgDrawPinned(vg, box, ppt, arrowWidth, boxr);

	nvgFillColor(vg,nvgRGBA(guideLabelBkColor()));
	nvgFill(vg);
	nvgStrokeWidth(vg,1);
	nvgStrokeColor(vg,nvgRGBA(guideColor()));
	nvgStroke(vg);

	nvgFillColor(vg,nvgRGBA(guideLabelColor()));
	nvgTextAligned(vg, box, str, NVG_ALIGN_MIDDLE|NVG_ALIGN_CENTER);
}

inline void Plotter::drawGrids(NVGcontext* vg, const rct_t& r) {
	nvgStrokeColor(vg, nvgRGBA(_gridColor));
	nvgStrokeWidth(vg, _gridWidth);
	nvgBeginPath(vg);
	for( size_t i=0; i<_gridX.count; i++ )
		nvgLineR(vg,pos_t(toImageX(_gridX.getX(i)),r.y),pos_t(0,r.h));
	for( size_t i=0; i<_gridY.count; i++ )
		nvgLineR(vg,pos_t(r.x,toImageY(_gridY.getX(i))),pos_t(r.w,0));
	nvgStroke(vg);

	
	nvgBeginPath(vg);
	nvgStrokeColor(vg, nvgRGBA(_axesColor));
	nvgStrokeWidth(vg, _axesWidth);
	
	float x0 = toImageX(0), y0 = toImageY(0);
	if( y0>0 && y0<r.h)
		nvgLineR(vg, pos_t(r.x,y0), pos_t(r.w,0));
	if( x0>0 && x0<r.w)
		nvgLineR(vg, pos_t(x0,r.y), pos_t(0,r.h));
	nvgStroke(vg);

	nvgFontSize( vg, textSize() );
	float tw=0;
	for( size_t i=0; i<_gridY.count; i++ ) {
		auto [yy,label] = _gridY.getLabel(i);
		tw = std::max(tw,nvgMeasureText(vg, label).w);
	}

	float labelY = std::max(2.f,std::min(r.h-textSize()-2,y0+2));
	float labelX = std::max(2.f,std::min(r.w-tw-2,x0-tw-2));
	int labelXAlign=NVG_ALIGN_RIGHT|NVG_ALIGN_MIDDLE, labelYAlign = NVG_ALIGN_CENTER|NVG_ALIGN_TOP;
	
	nvgFillColor( vg, nvgRGBA(_textColor) );
	for( size_t i=0; i<_gridX.count; i++ ) {
		auto [xx,label] = _gridX.getLabel(i);
		nvgTextAligned(vg, rct_t(xx-25,labelY,50,_textSize), label, labelYAlign);
	}
	for( size_t i=0; i<_gridY.count; i++ ) {
		auto [yy,label] = _gridY.getLabel(i);
		nvgTextAligned(vg, rct_t(labelX,r.h-yy-_textSize/2,tw,_textSize), label, labelXAlign);
	}
}

inline void Plotter::drawPlot(NVGcontext* vg, const rct_t& r) {
	for( const auto& s: _scatters ) s.draw( *this, vg, r );
	for( const auto& s: _series ) s.draw( *this, vg, r, _sortedXIndices );
}
	
inline void Plotter::drawGuide(NVGcontext* vg, const rct_t& r) {
	if( isnan(_guide) ) return;
	float gx = toImageX(_guide);
	nvgStrokeColor( vg, nvgRGBA(guideColor()));
	nvgStrokeWidth( vg, 1 );
	if( gx>=0 && gx<=r.w ) {
		nvgBeginPath(vg);
		nvgLineR(vg,pos_t(gx,r.y),pos_t(0,r.h));
		nvgStroke(vg);
	}
	for( auto yy: _guideY ) {
		if( isnan(yy) ) continue;
		nvgBeginPath(vg);
		nvgLineR(vg,pos_t(r.x,toImageY(yy)),pos_t(r.w,0));
		nvgStroke(vg);
	}
	nvgFontSize(vg, guideLabelSize());
	drawGuideLabel(vg, true, {gx,0}, r, guideLabelText(_guide, 1/_gridX.scale), guideLabelSize(), 2, 2, 4, 2);
	for( auto yy: _guideY ) {
		if( isnan(yy) ) continue;
		float gy = toImageY(yy);
		drawGuideLabel(vg, false, {gx,gy}, r, guideLabelText(yy, 1/_gridY.scale), guideLabelSize(), 2, 2, 4, 2);
	}
}

inline void Plotter::drawContents( NVGcontext* vg, const rct_t& r, align_t align ) {
	nvgSave(vg);
	_gridX = GridInfo(r.w, r.x, _margin.x, _range.x, _range.w, _scale.x, _offset.x);
	_gridY = GridInfo(r.h, r.y, _margin.y, _range.y, _range.h, _scale.y, _offset.y);
	drawGrids(vg,r);
	drawPlot(vg,r);
	drawGuide(vg,r);
	nvgRestore(vg);
	Widget::drawContents(vg,r,align);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Slider_h */
