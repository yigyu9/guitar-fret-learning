//
//  ImageViewer.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_ImageViewerBase_h
#define JGL2_ImageViewerBase_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>

#include <JGL2/Widget.hpp>
#include <JGL2/JR_DrawGL.hpp>
#include <JGL2/_Scrollable.hpp>

namespace JGL2 {

struct ImageViewerBase: public Widget, public _Targettable {

	ImageViewerBase(float xx, float yy, float ww, float hh, const str_t& title="" );
	ImageViewerBase(const pos_t& pos, const sz2_t& sz, const str_t& title="" );

	virtual isz_t 			imageSize() const = 0;
	virtual bool			imageAvailable() const =0;

	virtual void			fitToScreen();
	template<typename T>
			t_vec2(T)		screenToImage( const t_vec2(T)& pt ) const;
	template<typename T>
			t_vec2(T)		imageToScreen( const t_vec2(T)& pt ) const;
	virtual rct_t			getScreenRect( const rct_t& rect ) const;
	virtual irct_t 			getScreenRect( const irct_t& rect ) const;
	virtual void			resizableToImage( bool resizable ) { _resizableToImage = resizable; }
	virtual bool			resizableToImage() const { return _resizableToImage; }
	virtual transf3_t		viewProjection() const;
	virtual bool 			zoomAction( const pos_t& mousePt, float zoomDelta );
	virtual bool			fitted() const { return _fitted; }
	virtual bool			oneToOne() const { return abs(_viewScale-1.)<0.0000001?true:false;}

	// Following function is only for specual purpose. Here, the scroll value is ignored and replaced with the given offset value
	template<typename T>
			t_vec2(T)		screenToImage( const t_vec2(T)& pt, const pos_t& offset ) const;
	template<typename T>
			t_vec2(T)		imageToScreen( const t_vec2(T)& pt, const pos_t& offset ) const;
	virtual rct_t			getScreenRect( const rct_t& rect, const pos_t& offset ) const;
	virtual irct_t 			getScreenRect( const irct_t& rect, const pos_t& offset ) const;

	virtual void			addSyncView(ImageViewerBase* v);
	virtual void			removeSyncView(ImageViewerBase* v);
	virtual void			backgroundColor(const color_t& c){ _backgroundColor=c; redraw(); }
	virtual color_t			backgroundColor() const { return _backgroundColor; }

protected:

	virtual void			drawImage( JR::Program& prog, const transf2_t& mat=transf2_t(1) ) = 0;
	virtual void			drawImage( const transf2_t& mat=transf2_t(1) ) = 0;
	virtual void			drawImage( const pos_t& v, float s ) = 0;
		
	virtual void			rearrange( NVGcontext* vg,autoscale_t scaling ) override;
	virtual void			drawBoxOver(NVGcontext* vg,const rct_t&r) override;
	virtual void			drawContents(NVGcontext* vg,const rct_t&r,align_t a) override;
		
	virtual void			drawGL() override;
	virtual bool			handle( event_t e ) override;

	virtual void			updateFitScale();
	virtual void			notifySyncHost(float scale, pos_t pos);
	virtual void			setViewing(float scale, pos_t pos);
	virtual void			updateSlaves(float scale, pos_t pos);
	virtual void			viewingUpdated();
	
	virtual void			setSyncHost(ImageViewerBase* host);

	float 					_minWidth 			= 100.f;
	float 					_maxWidth 			= 1920.f;
	float 					_minHeight			= 100.f;
	float 					_maxHeight			= 1300.f;

	bool					_resizableToImage	= false;
	
	_Scrollable				_scroller;
	pos_t					_lastPt;
	
	color_t					_backgroundColor	= toColor(_color_background());
	float					_viewScale			= 1.f;	// image -> window: imageSize* scale = windowSpan
	float					_desiredScale		= 1.f;
	float					_fitScale			= 1.f;

	bool					_fitted				= false;
	bool					_keepFitted			= false;
	ImageViewerBase*		_syncHost			= nullptr;
	std::vector<ImageViewerBase*>	_syncViews;
	
};


template<typename T> inline t_vec2(T) ImageViewerBase::screenToImage( const t_vec2(T)& pt, const pos_t& offset ) const {
	t_vec2(T) pti;
	pti.x = T((pt.x+offset.x)/_viewScale);
	pti.y = T((pt.y+offset.y)/_viewScale);
	return pti;
}
template<typename T> inline t_vec2(T) ImageViewerBase::screenToImage( const t_vec2(T)& pt ) const {
	t_vec2(T) pti;
	pti.x = T((pt.x+_scroller.scrollOffset().x)/_viewScale);
	pti.y = T((pt.y+_scroller.scrollOffset().y)/_viewScale);
	return pti;
}

template<typename T> inline t_vec2(T) ImageViewerBase::imageToScreen( const t_vec2(T)& pt, const pos_t& offset ) const {
	t_vec2(T) pti;
	pti.x = T((pt.x)*_viewScale-offset.x);
	pti.y = T((pt.y)*_viewScale-offset.y);
	return pti;
}

template<typename T> inline t_vec2(T) ImageViewerBase::imageToScreen( const t_vec2(T)& pt ) const {
	t_vec2(T) pti;
	pti.x = T((pt.x)*_viewScale-_scroller.scrollOffset().x);
	pti.y = T((pt.y)*_viewScale-_scroller.scrollOffset().y);
	return pti;
}

} // namespace JGL2


namespace JGL2 {

inline ImageViewerBase::ImageViewerBase(float xx, float yy, float ww, float hh, const str_t& title)
:Widget(xx,yy,ww,hh,title), _Targettable(false) {
	minSize(sz2_t(200,200));
}

inline ImageViewerBase::ImageViewerBase(const pos_t& pos, const sz2_t& sz, const str_t& title)
:Widget(pos,sz,title), _Targettable(false) {
	minSize(sz2_t(200,200));
}

inline void ImageViewerBase::rearrange(NVGcontext* vg,autoscale_t scaling) {
	if( !changed() ) return;
	Widget::rearrange(vg,scaling);
	updateFitScale();
	if( _fitted ) fitToScreen();
	if( imageAvailable() ) {
		rct_t cont = rct_t(pos_t(0),imageSize()*_viewScale);
		_scroller.scrollRange(size(),cont,align_t::NONE);
		viewingUpdated();
	}
}

inline transf3_t ImageViewerBase::viewProjection() const {
	return JR::getOrthoTransform(w(),h())
	*JR::translate(JR::vec3(-_scroller.scrollOffset(),0))
	*JR::scale(JR::vec3(_viewScale,_viewScale,1));
}

inline void ImageViewerBase::drawBoxOver(NVGcontext* vg, const rct_t&r) {
	if( _scroller.scrollDrawIndicators(vg) )
		animate();
	Widget::drawBoxOver(vg, r);
}

inline void ImageViewerBase::drawGL() {
	color_t cc = windowColor(this, _backgroundColor);
	glClearColor(cc.r, cc.g, cc.b, 1);
	glClear(GL_COLOR_BUFFER_BIT);
	if( imageAvailable() )
		drawImage();
	_drawGLCB(bound());
}

inline void	ImageViewerBase::drawContents(NVGcontext* vg,const rct_t&r,align_t a) {
	_drawCB(vg,r,a);
}


inline bool ImageViewerBase::handle( event_t e ) {
	if( _scroller.scrollHandle(e) ) {
		viewingUpdated();
		damage();
		return true;
	}
	if( e == event_t::ZOOM ) {
		if( zoomAction(_JGL::eventPt(), _JGL::eventZoom()*60.f ) ) {
			viewingUpdated();
			damage();
		}
		return true;
	}
	if( e == event_t::SCROLL ) {
		if( _JGL::eventMods( mod_t::CONTROL) ){
			if( zoomAction(_JGL::eventPt(), -_JGL::eventScrollY()*5.f ) ) {
				viewingUpdated();
				damage();
				return true;
			}
		}
	}
	if( e== event_t::DRAG && _JGL::eventMods(mod_t::LBUTTON) && _JGL::eventMods(mod_t::CONTROL)) {
		pos_t pt = _JGL::eventPt();
		_scroller.scrollOffset(_lastPt-pt+_scroller.scrollOffset());
		viewingUpdated();
		_lastPt = pt;
		damage();
		return true;
	}
	if( e== event_t::PUSH && _JGL::eventButton()==button_t::LBUTTON && _JGL::eventMods(mod_t::CONTROL)) {
		_lastPt = _JGL::eventPt();
		return true;
	}
	return Widget::handle(e);
}

inline void ImageViewerBase::updateFitScale() {
	if( imageAvailable() ) {
		isz_t imgSz = imageSize();
		if(imgSz.w<1 || imgSz.h<1) return;
		float xScale = w()/(float)imgSz.w;
		float yScale = h()/(float)imgSz.h;
		_fitScale = std::min(xScale,yScale);
	}
}

inline void ImageViewerBase::fitToScreen() {
	if( !imageAvailable() ) return;
	updateFitScale();
	_fitted = true;
	_desiredScale = _viewScale = _fitScale;
	_scroller.scrollRange(size(),rct_t(pos_t(0),imageSize()*_viewScale),alignment());
	viewingUpdated();
}

inline rct_t ImageViewerBase::getScreenRect( const rct_t& re, const pos_t& offset ) const {
	float l = re.tl().x*_viewScale-offset.x;
	float r = re.tr().x*_viewScale-offset.x;
	float t = re.tl().y*_viewScale-offset.y;
	float b = re.bl().y*_viewScale-offset.y;
	return rct_t( l, t, r-l, b-t );
}

inline irct_t ImageViewerBase::getScreenRect( const irct_t& re, const pos_t& offset ) const {
	int l = int(round(re.tl().x*_viewScale-offset.x));
	int r = int(round(re.tr().x*_viewScale-offset.x));
	int t = int(round(re.tl().y*_viewScale-offset.y));
	int b = int(round(re.bl().y*_viewScale-offset.y));
	return irct_t( l, t, r-l, b-t );
}

inline rct_t ImageViewerBase::getScreenRect( const rct_t& re ) const {
	float l = re.tl().x*_viewScale-_scroller.scrollOffset().x;
	float r = re.tr().x*_viewScale-_scroller.scrollOffset().x;
	float t = re.tl().y*_viewScale-_scroller.scrollOffset().y;
	float b = re.bl().y*_viewScale-_scroller.scrollOffset().y;
	return rct_t( l, t, r-l, b-t );
}

inline irct_t ImageViewerBase::getScreenRect( const irct_t& re ) const {
	int l = int(round(re.tl().x*_viewScale-_scroller.scrollOffset().x));
	int r = int(round(re.tr().x*_viewScale-_scroller.scrollOffset().x));
	int t = int(round(re.tl().y*_viewScale-_scroller.scrollOffset().y));
	int b = int(round(re.bl().y*_viewScale-_scroller.scrollOffset().y));
	return irct_t( l, t, r-l, b-t );
}

inline bool ImageViewerBase::zoomAction(const pos_t& mousePt, float zoomDelta ) {
	pos_t pivot = mousePt;
	pos_t imagePt = screenToImage( pivot );

	float oldViewScale = _viewScale;
	pos_t oldOffset = _scroller.scrollOffset();
	_desiredScale *= powf(1.01f,zoomDelta);
	if( abs( _desiredScale-1.f )<0.05 ) _viewScale = 1.f;
	else if( abs( _desiredScale/_fitScale-1.f )<0.025 ) _viewScale = _fitScale;
	else _viewScale = _desiredScale;
	
	pos_t pivot2 = imageToScreen( imagePt, oldOffset );
	if( imageAvailable() ) {
		_scroller.scrollRange(size(),rct_t(pos_t(0),imageSize()*_viewScale),alignment());
		_scroller.scrollOffset(oldOffset-pivot+pivot2);
	}

	if( abs(_viewScale/_fitScale-1.f)<0.000001 ) _fitted = true;
	else _fitted = false;
	
	if( _viewScale!= oldViewScale )
		return true;
	return false;
}

inline void ImageViewerBase::setSyncHost(ImageViewerBase* v) {
	if( _syncHost ) _syncHost->removeSyncView( this );
	_syncHost = v;
	auto slaves = _syncViews;
	for( auto s: slaves ) s->setSyncHost(v);
}

inline void ImageViewerBase::addSyncView(ImageViewerBase* v) {
	if( !v ) return;
	v->setSyncHost(this);
	assert( v->_syncViews.size()==0 ); // To prevent cycle, a slave cannot be a host, at the same time.
	_syncViews.push_back(v);
}

inline void ImageViewerBase::removeSyncView(ImageViewerBase* v) {
	if( v && v->_syncHost==this ) v->_syncHost=nullptr;
	auto pos = std::find( _syncViews.begin(), _syncViews.end(), v );
	if( pos!= _syncViews.end() )
		_syncViews.erase( pos );
}

inline void	ImageViewerBase::viewingUpdated() {
	if( _syncHost ) _syncHost->notifySyncHost(_viewScale, _scroller.scrollOffset() );
	else notifySyncHost( _viewScale, _scroller.scrollOffset() ); // notify itself
}

inline void ImageViewerBase::notifySyncHost(float scale, pos_t pos) {
	// TODO: do I need to check host-slave relation, here?
	if( _syncHost ) notifySyncHost(scale,pos);
	else			setViewing( scale, pos );
}

inline void ImageViewerBase::updateSlaves( float scale, pos_t pos) {
	for( auto c: _syncViews ) {
		c->setViewing( scale, pos );
	}
}

inline void ImageViewerBase::setViewing(float scale, pos_t pos) {
	if( scale != _viewScale || pos.x!=_scroller.scrollOffset().x || pos.y!=_scroller.scrollOffset().y ) {
		_fitted=false;
		_viewScale = scale;
		_desiredScale = scale;
		if( imageAvailable() ) {
			rct_t cont = rct_t(pos_t(0),imageSize()*_viewScale);
			_scroller.scrollRange(size(),cont,align_t::NONE);
		}
		_scroller.scrollOffset( pos );
		damage();
	}
	updateSlaves( scale, pos );
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* ImageViewer_h */
