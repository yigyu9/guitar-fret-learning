//
//  ImageViewer.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_ImageViewer_h
#define JGL2_ImageViewer_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>

#include <JGL2/_ImageViewerBase.hpp>
#include <JGL2/_Draw.hpp>
#include <JGL2/_Scrollable.hpp>
#include <JGL2/TexImage.hpp>
#include <jm/half.hpp>

namespace JGL2 {

struct ImageViewer: public ImageViewerBase {
	enum class ColorMode {
		AS_IS = 0,
		S_RGB,
		LINEAR_S_RGB,
		ADOBE_BAYER,
	};
	
	ImageViewer(float xx, float yy, float ww, float hh, const str_t& title="" );
	ImageViewer(const pos_t& pos, const sz2_t& sz, const str_t& title="" );

	virtual isz_t			imageSize() const override		{ return texImage().imgSize(); };
	virtual bool 			imageAvailable() const override { return texImage().imageAvailable(); }

	virtual void clear();
	virtual	void			setImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual	void			setImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual	void			setImage( const jm::half* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual	void			setImage( const float* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual void			setImage( const color_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void			setImage( const colora_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void			setImage( const colorh_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void			setImage( const colorah_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );

	virtual TexImage&		texImage()						{ return _texImage; }
	virtual const TexImage& texImage() const				{ return _texImage; }

	virtual void 			imageGamma( const color_t& g )	{ _texImage.gamma(g); }
	virtual color_t 		imageGamma()					{ return _texImage.gamma(); }

	virtual void 			imageRGB2PCS( const colorMat_t& m )	{ _texImage.RGB2PCS(m); }
	virtual colorMat_t 		imageRGB2PCS()					{ return _texImage.RGB2PCS(); }

	virtual void 			isImageBayer( bool b )			{ _texImage.isBayer(b); }
	virtual bool 			isImageBayer()					{ return _texImage.isBayer(); }
	
	virtual void 			imageColorOverride(ColorMode v) { _imageColorOverride = v; }
	virtual	ColorMode		imageColorOverride() const		{ return _imageColorOverride; }
	virtual	ColorMode&		imageColorOverride()			{ return _imageColorOverride; }

	virtual void			limitDynamicRange(bool v)		{ _limitedDynamicRange = v; }
	virtual	bool			limitDynamicRange() const		{ return _limitedDynamicRange; }
	virtual	bool&			limitDynamicRange()				{ return _limitedDynamicRange; }

	virtual	color_t			displayGamma() const			{ return _displayGamma; }
	virtual void			displayGamma(color_t v)			{ _displayGamma = v; }
	virtual	color_t&		displayGamma()					{ return _displayGamma; }

	virtual void 			imageGain(float v) 				{ _imageGain = v; }
	virtual	float			imageGain() const				{ return _imageGain; }
	virtual	float&			imageGain() 					{ return _imageGain; }

	virtual void			PCSToDisplay(colorMat_t v)		{ _PCSToDisplay = v; }
	virtual	colorMat_t		PCSToDisplay() const			{ return _PCSToDisplay; }
	virtual	colorMat_t&		PCSToDisplay()					{ return _PCSToDisplay; }

	virtual void			setImageChanged()				{ texImage().changed(true); redraw(); }

	virtual colorMat_t		getColorMat() const;
	virtual color_t			getColorGamma() const;

	virtual void			zoomOneToOne(const pos_t &mousePt=pos_t(-1,-1));
	virtual void			disableAlpha(bool v)			{ _disableAlpha = v; }
	virtual bool			disableAlpha() const			{ return _disableAlpha; }
protected:
	virtual void			drawImage( JR::Program& prog, const transf2_t& mat=transf2_t(1) ) override;
	virtual void			drawImage( const transf2_t& mat=transf2_t(1) ) override;
	virtual void			drawImage( const pos_t& offset, float scale ) override;
	virtual void			imageSizeChanged( const isz_t& oldSz );
	TexImage				_texImage;
	ColorMode				_imageColorOverride		= ColorMode::AS_IS;
	float					_imageGain				= 1.f;
	bool 					_limitedDynamicRange	= false;
	bool					_disableAlpha			= false;
	color_t					_displayGamma			= color_t(2.4f);
	colorMat_t				_PCSToDisplay			= colorMat_t(1);
};

} // namespace JGL2


namespace JGL2 {

inline ImageViewer::ImageViewer(float xx, float yy, float ww, float hh, const str_t& title)
:ImageViewerBase(xx,yy,ww,hh,title) {
	minSize(sz2_t(200,200));
	_PCSToDisplay = SCMS::fromXYZ_D65(SCMS::PROF_sRGB);
	quickUI().add(new nanoCheckR(0,0,150,"Disable Alpha",_disableAlpha));
	quickUI().add(new nanoCheckR(0,0,150,"Limited Gammut",_limitedDynamicRange));
	quickUI().add(new nanoSliderF(0,0,150,"Gain",0,5,_imageGain));
	quickUI().add(new nanoOptions<ColorMode>(0,0,160,"Override",{"As-Is","sRGB","Linear","Adobe Bayer"},_imageColorOverride) );
	quickUI().shrink(false);
}

inline ImageViewer::ImageViewer(const pos_t& pos, const sz2_t& sz, const str_t& title)
:ImageViewerBase(pos,sz,title) {
	minSize(sz2_t(200,200));
	_PCSToDisplay = SCMS::fromXYZ_D65(SCMS::PROF_sRGB);
}

inline void ImageViewer::clear() {
	texImage().clear();
}

inline colorMat_t ImageViewer::getColorMat() const {
	switch( _imageColorOverride ) {
	default:
	case ColorMode::AS_IS:
		return texImage()._rgb_to_pcs;
		break;
	case ColorMode::S_RGB:
		return SCMS::toXYZ_D65(SCMS::PROF_sRGB);
		break;
	case ColorMode::LINEAR_S_RGB:
		return SCMS::toXYZ_D65(SCMS::PROF_sRGB);
		break;
	case ColorMode::ADOBE_BAYER:
//		return SCMS::typicalBayerMat;
		return inverse(transpose(SCMS::imx183BayerMat));
		break;
	}
}

inline color_t ImageViewer::getColorGamma() const {
	switch( _imageColorOverride ) {
	default:
	case ColorMode::AS_IS:
		return texImage()._gamma;
		break;
	case ColorMode::S_RGB:
		return SCMS::PROF_sRGB.gamma;
		break;
	case ColorMode::LINEAR_S_RGB:
		return color_t(1);
		break;
	case ColorMode::ADOBE_BAYER:
		return color_t(1);
		break;
	}
}

inline void ImageViewer::setImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, channels, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, channels, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const jm::half* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, channels, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const float* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, channels, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const color_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const colora_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const colorh_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::setImage( const colorah_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	isz_t oldSize = texImage().imgSize();
	texImage().setImage(d, ww, hh, isBGR, toCopy);
	imageSizeChanged( oldSize );
}

inline void ImageViewer::imageSizeChanged( const isz_t& oldSz ) {
	if( resizableToImage() ) {
		float targetWidth = std::min( _maxWidth, std::max( _minWidth, float(texImage().imgSize().w) ));
		float targetHeight= std::min( _maxHeight,std::max( _minHeight,float(texImage().imgSize().h) ));
		size( sz2_t( targetWidth, targetHeight ) );
	}
	if( oldSz.w!=texImage().imgSize().w || oldSz.h!=texImage().imgSize().h ) {
		fitToScreen();
//		( !_syncHost && _syncViews.size()<1 ) && (
	}
	_scroller.scrollRange( size(), rct_t(pos_t(0,0),texImage().imgSize()*_viewScale), alignment());
	damage();
}

inline void ImageViewer::drawImage(JR::Program& prog, const transf2_t& mat ) {
	if( _disableAlpha )
		glDisable(GL_BLEND);
	else
		glEnable(GL_BLEND);
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
	prog.use();
	prog.setUniform("factor", _imageGain);
	Window* win = window();
	prog.setUniform("outputGamma", win->windowGamma());
	prog.setUniform("PCSToDisplay", win->windowColorMat()*_PCSToDisplay);
	prog.setUniform("limitedDynamicRange", _limitedDynamicRange?1:0);
	texImage().draw(prog, viewProjection(), to3DTransform(mat), getColorMat(), getColorGamma());
	if( _disableAlpha )
		glEnable(GL_BLEND);
}

inline void ImageViewer::drawImage( const transf2_t& mat) {
	drawImage( JR::blitProgram(), mat );
}

inline void ImageViewer::drawImage(const pos_t& v, float s ) {
	drawImage(transf2_t(1,0,0,0,1,0,v.x,v.y,1) * transf2_t(s,0,0,0,s,0,0,0,1));
}

inline void ImageViewer::zoomOneToOne(const pos_t& mousePt) {
	if( !imageAvailable() ) return;
	pos_t pivot = mousePt;
	if( mousePt.x<0 || mousePt.y<0 || mousePt.x>w() || mousePt.y>h() ) pivot = pos_t(w()/2,h()/2);
	JGL2::pos_t imagePt = screenToImage( pivot );
	imagePt.x = std::min( imageSize().w-1.f, std::max( 0.f, imagePt.x ) );
	imagePt.y = std::min( imageSize().h-1.f, std::max( 0.f, imagePt.y ) );

//	float oldViewScale = _viewScale;
	JGL2::pos_t oldOffset = _scroller.scrollOffset();
	_desiredScale = 1;
	if( abs( _desiredScale-1.f )<0.05 ) _viewScale = 1.f;
	else if( abs( _desiredScale/_fitScale-1.f )<0.025 ) _viewScale = _fitScale;
	else _viewScale = _desiredScale;
	
	JGL2::pos_t pivot2 = imageToScreen( imagePt, oldOffset );
	if( imageAvailable() ) {
		_scroller.scrollRange(size(),JGL2::rct_t(JGL2::pos_t(0),imageSize()*_viewScale),alignment());
		_scroller.scrollOffset(oldOffset-pivot+pivot2);
	}
	_fitted = false;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* ImageViewer_h */
