//
//  MultiImageViewer.h
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_MultiImageViewer_h
#define JGL2_MultiImageViewer_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/ImageViewer.hpp>

namespace JGL2 {

const float _def_image_selection_button_width = 36.f;
const float _def_image_selection_button_height = 24.f;
const float _def_image_selection_button_spacing = 6.f;
const float _def_image_selection_button_padding = 1.2f;

struct MultiImageViewer: public ImageViewer {
	
public:
	MultiImageViewer(float xx, float yy, float ww, float hh, const std::string& title="" );
	
	virtual isz_t	imageSize() const override;
	virtual void	clear() override;
	virtual void	addImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const jm::half* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const float* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const color_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const colora_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const colorh_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual void	addImage( const colorah_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true );
	virtual	void	setImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true ) override;
	virtual	void	setImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true ) override;
	virtual	void	setImage( const jm::half* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true ) override;
	virtual	void	setImage( const float* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true ) override;
	virtual void	setImage( const color_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true ) override;
	virtual void	setImage( const colora_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true ) override;
	virtual void	setImage( const colorh_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true ) override;
	virtual void	setImage( const colorah_t* d, int ww, int hh, bool isBGR=true, bool toCopy=true ) override;

	virtual TexImage& texImage() override;
	virtual void	visible( int x );
	virtual int		visible() const { return _visibleTexImage; }
	virtual bool	imageAvailable() const override;
	virtual void	rearrange(NVGcontext* vg, autoscale_t scaling) override;
protected:
	virtual void	drawContents(NVGcontext* vg,const rct_t&r, align_t a) override;
	virtual bool	handle(event_t event) override;
	static	void	selectionCB( Widget* w, void* ud ) { ((MultiImageViewer*)ud)->selectionChanged(); }
	virtual void	selectionChanged();
	virtual void	drawGL() override;

	template<typename T>
			void	addImageInternal( const T* d, int ww, int hh, int channels, bool isBGR, bool toCopy);
	
	std::vector<TexImage>	_texImages;
	std::vector<TexImage>	_texImagesToDelete;
	int						_visibleTexImage = 0;
	RadioButtonGroup		_buttonGroup;
	std::mutex				_listMutex;
};

}

namespace JGL2 {

#include <JGL2/Button.hpp>
#include <JGL2/_JGL.hpp>

inline MultiImageViewer::MultiImageViewer( float xx, float yy, float ww, float hh, const std::string& title )
:ImageViewer(xx,yy,ww,hh,title),
_buttonGroup(0.f, 0.f, ww, _def_image_selection_button_height+_def_image_selection_button_spacing*2.f, "ImageSelectionButton") {
	_visibleTexImage = 0;
	_buttonGroup.end();
//	_buttonGroup.autoscale(true);
	_buttonGroup.alignment(align_t::LEFT|align_t::TOP);
	_buttonGroup.parent(this);
	_buttonGroup.padding( _def_image_selection_button_spacing );
	_buttonGroup.callback( selectionCB, this );
}

inline isz_t MultiImageViewer::imageSize() const {
	if( _texImages.size()>0 ) return _texImages.front().imgSize();
	return isz_t(0,0);
}

inline void MultiImageViewer::clear() {
	for( auto& t: _texImages ) {
		_texImagesToDelete.push_back( std::move(t) );
		t.clear();
	}
	_texImages.clear();
	ImageViewer::damage();
	_buttonGroup.clear();
	_buttonGroup.changed();
}

inline void MultiImageViewer::drawGL()  {
	std::unique_lock<std::mutex> lock(_listMutex);
	ImageViewer::drawGL();
	for( auto& t: _texImagesToDelete )
		t.clear();
	_texImagesToDelete.clear();
	lock.unlock();
}

inline void MultiImageViewer::selectionChanged() {
	visible( _buttonGroup.value() );
	doCallback();
}

inline TexImage& MultiImageViewer::texImage() {
	return _texImages[_visibleTexImage];
}
	
inline void MultiImageViewer::visible( int x ) {
	if( x>=0 && x<_texImages.size() ) {
		_visibleTexImage = x;
		ImageViewer::change();
	}
}

inline bool MultiImageViewer::imageAvailable() const {
	return ( _texImages.size()>_visibleTexImage && _visibleTexImage>=0 );
}

inline void MultiImageViewer::setImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImage( d, ww, hh, channels, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImage( d, ww, hh, channels, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const jm::half* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImage( d, ww, hh, channels, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const float* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImage( d, ww, hh, channels, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const color_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImage( (float*)d, ww, hh, 3, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const colora_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImage( (float*)d, ww, hh, 4, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const colorh_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImage( (jm::half*)d, ww, hh, 3, isBGR, toCopy );
}
inline void MultiImageViewer::setImage( const colorah_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImage( (jm::half*)d, ww, hh, 4, isBGR, toCopy );
}

inline void MultiImageViewer::addImage( const unsigned char* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImageInternal(d, ww, hh, channels, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const unsigned short* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImageInternal(d, ww, hh, channels, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const jm::half* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImageInternal(d, ww, hh, channels, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const float* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	addImageInternal(d, ww, hh, channels, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const color_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImageInternal((float*)d, ww, hh, 3, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const colora_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImageInternal((float*)d, ww, hh, 4, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const colorh_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImageInternal((jm::half*)d, ww, hh, 3, isBGR, toCopy);
}
inline void MultiImageViewer::addImage( const colorah_t* d, int ww, int hh, bool isBGR, bool toCopy ) {
	addImageInternal((jm::half*)d, ww, hh, 4, isBGR, toCopy);
}

template<typename T>
void MultiImageViewer::addImageInternal( const T* d, int ww, int hh, int channels, bool isBGR, bool toCopy ) {
	// If current tex image is empty, load the image to it.
	if( ww<1 || hh<1 ) return;

	std::unique_lock<std::mutex> lock(_listMutex);
	auto target_itr = _texImages.begin();
	while( target_itr!=_texImages.end() && target_itr->imgSize().w>1 )
		target_itr++;
	if( target_itr >= _texImages.end() ) {
		_texImages.push_back(TexImage());
		target_itr = _texImages.begin()+(_texImages.size()-1);
	}
	auto& target = *target_itr;

	target.setImage(d, ww, hh, channels, isBGR);

	if( target_itr == _texImages.begin() ) {
		if( resizableToImage() ) {
			float targetWidth = std::min( _maxWidth, std::max( _minWidth, float(texImage().imgSize().w)));
			float targetHeight= std::min( _maxHeight,std::max( _minHeight,float(texImage().imgSize().h)));
			ImageViewer::size( sz2_t( targetWidth, targetHeight ) );
		}
		fitToScreen();
		_scroller.scrollRange( size(), rct_t(0,0,texImage().imgSize()*_viewScale), alignment());
//		_offset = -_scroller.scrollOffset();
		ImageViewer::damage();
	}
	int iw, ih;
	unsigned char* thumb_data = target.createThumbnail( iw, ih );
	
	// Here update button Group too.
	Button* b = new Button( int(_texImages.size()-1)*_def_image_selection_button_width, 0,
								 _def_image_selection_button_width, _def_image_selection_button_height, std::to_string(_texImages.size() ) );
	_buttonGroup.add( b );
	b->image( thumb_data, iw, ih );
	delete [] thumb_data;
	b->padding(_def_image_selection_button_padding);
	_buttonGroup.end();
	_buttonGroup.damage();
	_buttonGroup.change();
	change();
}

inline bool MultiImageViewer::handle( event_t e ) {
	if( !_buttonGroup.hidden() && _buttonGroup.under() && _buttonGroup.active()
	   && _JGL::dispatchEvent( &_buttonGroup, e ) ) return true;

	return ImageViewer::handle(e);
}

inline void MultiImageViewer::drawContents(NVGcontext* vg,const rct_t&r, align_t a) {
	_JGL::drawAsChild( vg, &_buttonGroup );
	ImageViewer::drawContents(vg,r,a);
}

inline void MultiImageViewer::rearrange(NVGcontext* vg,autoscale_t scaling) {
	if( changed() ) {
		ImageViewer::rearrange(vg,scaling);
		_buttonGroup.w(w());
	}
	if( _buttonGroup.changed() )
		_buttonGroup.reform(vg,autoscale_t::ALL);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* MultiImageViewer_h */
