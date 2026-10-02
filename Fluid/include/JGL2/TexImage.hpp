//
//  TexImage.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_TexImage_h
#define JGL2_TexImage_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/JR_DrawGL.hpp>
#include <JGL2/SCMS.hpp>
#include <jm/half.hpp>

namespace JGL2 {

//! \Brief The OpenGL texture image.
//! The texture Image that can be drawn by OpenGL.
struct TexImage {
	// The size and the number of channels of the current texture
	unsigned int		_texWidth  = 0; //!< The width of the OpenGL allocated texture. \sa texSize()
	unsigned int		_texHeight = 0; //!< The height of the OpenGL allocated texture. \sa texSize()
	unsigned int		_texChannels=0; //!< The number of channnels of the OpenGL allocated texture.
	GLuint				_texID = 0;           //!< The OpenGL texture ID. \sa texId()
		
	// The size of the image requested to setup
	unsigned int		_imageWidth = 0; 		//!< The width of the image sent by the user. \sa imgSize()
	unsigned int		_imageHeight = 0;		//!< The height of the image sent by the user. \sa imgSize()
	unsigned int		_imageChannels = 0;	//!< The number of channels of the image sent by the user.
	unsigned int		_bitDepth = 8;
	unsigned char*		_data = nullptr;				//!< The copy of the pixel data, which is GL_BYTE (unsigned). Note this will be immediately deleted when the image is sent to OpenGL.
	bool				_BGR = true;					//!< The flag indicating If it is BGR image. For OpenCV compatibility. \sa isBGR()
	bool				_isBayer = false;
	bool				_changed = false;				//!< The flag indicating if the user-sent image is changed to the OpenGL texture image. \sa changed()
	bool				_imageLocked = false;			//!< The flag indicating the user-sent image is being modified. (Required for multi-threading model)
	bool				_ownBuffer = false;
	colorMat_t			_rgb_to_pcs = colorMat_t(1);
	color_t				_gamma = color_t(2.4f);

	enum class colorReaingMode_t {
		AS_FILE,
		SRGB,
		XYZ,
	};
	virtual	colora_t 	getColor( const ipos_t& pi, colorReaingMode_t mode ) const;


	virtual bool		imageAvailable() const { return _imageWidth>0&&_imageHeight>0&&_imageChannels>0&&!_imageLocked; }
	virtual GLuint		texId() const { return _texID; }
	virtual void		makeGLImage();
	virtual void		clear();
	template<typename T,typename=std::enable_if_t< std::is_same_v<T,unsigned char>
												|| std::is_same_v<T,unsigned short>
												|| std::is_same_v<T,jm::half>
												|| std::is_same_v<T,float> >>
	void				setImage( const T* d, int ww, int hh, int channels, bool isBGR=true, bool toCopy=true  );
	template<typename T,typename=std::enable_if_t< std::is_same_v<T,color_t>
												|| std::is_same_v<T,colorah_t>
												|| std::is_same_v<T,colorh_t>
												|| std::is_same_v<T,colora_t> >>
	void				setImage( const T* d, int ww, int hh, bool isBGR=true, bool toCopy=true  );

	virtual void		RGB2PCS( const colorMat_t& m )	{ _rgb_to_pcs = m; }
	virtual colorMat_t	RGB2PCS() const					{ return _rgb_to_pcs; }

	virtual void		gamma( const color_t& g )		{ _gamma = g; }
	virtual color_t		gamma()	const					{ return _gamma; }

	virtual void		isBayer( bool b )				{ _isBayer = b; }
	virtual bool		isBayer() const					{ return _isBayer; }

	virtual transf3_t	getImageMat()					{ return scale(JR::vec3(float(_imageWidth),float(_imageHeight),1.f)); }

	virtual void		changed(bool b)					{ _changed=b; }
	virtual bool		changed() const					{ return _changed; }
	virtual bool		imageLocked() const				{ return _imageLocked; }
	virtual isz_t		texSize() const					{ return isz_t(_texWidth,_texHeight); }
	virtual isz_t		imgSize() const					{ return isz_t(_imageWidth,_imageHeight); }
	unsigned char*		createThumbnail( int& iw, int& ih, int THUMB_W=256, int THUMB_H=256 );
	virtual void		setShaderParams( JR::Program& prog, const transf3_t& m, const colorMat_t& cm = colorMat_t(-1), const color_t& gma = color_t(-1) );

	virtual void		draw( JR::Program& prog, const transf3_t& viewProjection, const transf3_t& mat=transf3_t(1), const colorMat_t& cm=colorMat_t(-1), const color_t& gma = color_t(-1) );
	virtual void		draw( JR::Program& prog, const transf3_t& viewProjection, const transf2_t& mat, const colorMat_t& cm=colorMat_t(-1), const color_t& gma = color_t(-1) );
	virtual void		draw( JR::Program& prog, const transf3_t& viewProjection, const pos_t& offset, float s, const colorMat_t& cm=colorMat_t(-1), const color_t& gma = color_t(-1) );
	virtual void		draw( JR::Program& prog, const transf3_t& mat, const colorMat_t& cm=colorMat_t(-1), const color_t& gma = color_t(-1) );
	virtual				~TexImage();
	TexImage( TexImage&& a );
	TexImage();
};

} // namespace JGL

#ifdef THUMB_OPENCV
#ifdef _MSC_VER
#ifdef _DEBUG
#pragma comment (lib,"opencv_world453d")
#else
#pragma comment (lib,"opencv_world453")
#endif
#endif
#endif

#include <JGL2/_JGL.hpp>
#include <JGL2/Window.hpp>
#include <JGL2/_Draw.hpp>

#include <stb_image_resize.h>

#define GL_TEXTURE_MAX_ANISOTROPY_EXT          0x84FE
#define GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT      0x84FF


namespace JGL2 {

inline TexImage::~TexImage() {
	clear();
}

inline TexImage::TexImage() {
	_texWidth  = 0;
	_texHeight = 0;
	_texChannels = 0;
	_texID = 0;
	_bitDepth = 8;
	
	_imageWidth = 0;
	_imageHeight = 0;
	_imageChannels = 0;
	_data = nullptr;
	_BGR = true;
	_changed = false;
	_rgb_to_pcs		= SCMS::toXYZ_D65( SCMS::PROF_sRGB );
}


inline TexImage::TexImage( TexImage&& a )
: _texWidth(a._texWidth),
_texHeight(a._texHeight),
_texChannels(a._texChannels),
_texID(a._texID),
_imageWidth(a._imageWidth),
_imageHeight(a._imageHeight),
_imageChannels(a._imageChannels),
_data(a._data),
_BGR(a._BGR),
_changed(a._changed),
_rgb_to_pcs(a._rgb_to_pcs),
_gamma(a._gamma),
_bitDepth(a._bitDepth) {
	a._texID = 0;
	a._data = nullptr;
}


inline void TexImage::makeGLImage() {
	glPixelStorei( GL_UNPACK_ALIGNMENT, 1 );
	GLint oldTex;
	glGetIntegerv( GL_TEXTURE_BINDING_2D, &oldTex );

	if( _imageWidth != _texWidth || _imageHeight != _texHeight || _imageChannels != _texChannels ) {
		_texWidth = _imageWidth;
		_texHeight= _imageHeight;
		_texChannels = _imageChannels;
		if( _texID ) glDeleteTextures( 1, &_texID ); _texID = 0;
		

#ifdef _MSC_VER
		glewInit();
#endif
		if( _texWidth>0 && _texHeight>0 ) {
			glGenTextures( 1, &_texID );
			glBindTexture( GL_TEXTURE_2D, _texID );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT );
			glTexParameteri( GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT );
			float aniso = 0.0f;
			glGetFloatv(GL_MAX_TEXTURE_MAX_ANISOTROPY_EXT, &aniso);
			glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, aniso);
			glTexImage2D( GL_TEXTURE_2D, 0, GL_RGBA32F, _texWidth, _texHeight, 0, GL_RGBA, GL_FLOAT, 0 );
		}
	}
	if( _texWidth>0 && _texHeight>0 && _data ) {
		glBindTexture( GL_TEXTURE_2D, _texID );
		GLint dataType = GL_RGB;
		if( _texChannels == 3 ) {
			if( _BGR )	dataType = GL_BGR;
			else		dataType = GL_RGB;
		}
		else if( _texChannels == 1 ){ // texChannels == 4
			if( _BGR )	dataType = GL_RED;
			else		dataType = GL_RED;
		}
		else { // texChannels == 4
			if( _BGR )	dataType = GL_BGRA;
			else		dataType = GL_RGBA;
		}
		switch( _bitDepth ) {
			case 32:
				glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, _texWidth, _texHeight, dataType, GL_FLOAT, _data );
				break;
			case 16:
				glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, _texWidth, _texHeight, dataType, GL_HALF_FLOAT, _data );
				break;
			case 15:
				glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, _texWidth, _texHeight, dataType, GL_UNSIGNED_SHORT, _data );
				break;
			case 8:
			default:
				glTexSubImage2D( GL_TEXTURE_2D, 0, 0, 0, _texWidth, _texHeight, dataType, GL_UNSIGNED_BYTE, _data );
		}
		glGenerateMipmap( GL_TEXTURE_2D );
	}
	glBindTexture( GL_TEXTURE_2D, oldTex );
	_changed = false;
}

inline void TexImage::clear() {
	if( _data && _ownBuffer ) {
		delete _data;
		_ownBuffer = false;
	}
	_data = nullptr;
	
	if( _texID ) {
		glDeleteTextures( 1, &_texID );
	}
	_texID = 0;
	_changed = true;
	_imageWidth    = 0;
	_imageHeight   = 0;
	_imageChannels = 0;
	_texWidth    = 0;
	_texHeight   = 0;
	_texChannels = 0;
}

template<typename T,typename> void TexImage::setImage( const T* d, int ww, int hh, int channels, bool isBGR, bool toCopy  ) {
	_imageLocked = true;
	if( _data && _ownBuffer ) {
		delete [] _data;
		_ownBuffer = false;
	}
	_data = nullptr;
	_imageWidth = 0;
	_imageHeight = 0;
	_imageChannels = 0;
	assert( channels==1 || channels==3 || channels==4 );
	if( !d ) {
		_changed = true;
		_imageLocked = false;
		return;
	}
	if( ww>0 && hh>0 ) {
		if( toCopy ) {
			_data = (unsigned char*) new T[ww*hh*channels];
			memcpy( _data, d, sizeof(T)*ww*hh*channels );
		}
		else {
			_data = (unsigned char*)d;
			_ownBuffer = false;
		}
		_ownBuffer		= toCopy;
		if constexpr( std::is_same_v<T,unsigned short> ) {
			_bitDepth = 15;
		}
		else {
			_bitDepth		= sizeof(T)*8;
		}
		_imageWidth		= ww;
		_imageHeight	= hh;
		_imageChannels	= channels;
		_BGR			= isBGR;
		if( std::is_same<T,unsigned char>::value )
			_gamma = color_t(2.4f);
		else if( std::is_same<T,unsigned short>::value ) {
			if( _imageChannels==1 )
				_gamma = color_t(2.4f);
			else
				_gamma = color_t(1);
		}
		else
			_gamma = color_t(1);
	}
	if( channels!=1 ) _isBayer = false;
	_changed = true;
	_imageLocked = false;
}

template<typename T,typename> void TexImage::setImage( const T* d, int ww, int hh, bool isBGR, bool toCopy  ) {
	if constexpr( std::is_same<T,colora_t>::value )
		setImage( (float*)d, ww, hh, 4, isBGR, toCopy );
	else if constexpr( std::is_same<T,colorah_t>::value )
		setImage( (jm::half*)d, ww, hh, 4, isBGR, toCopy );
	else if constexpr( std::is_same<T,colorh_t>::value )
		setImage( (jm::half*)d, ww, hh, 3, isBGR, toCopy );
	else
		setImage( (float*)d, ww, hh, 3, isBGR, toCopy );
}

inline void TexImage::setShaderParams( JR::Program& prog, const transf3_t& mat, const colorMat_t& cm, const color_t& gamma  ) {
	glActiveTexture( GL_TEXTURE0 );
	glBindTexture( GL_TEXTURE_2D, texId() );
	prog.setUniform( "tex", 0 );
	prog.setUniform( "flip", 1 );
	prog.setUniform( "inputGamma", gamma[0]>0?gamma: _gamma );
	prog.setUniform( "isBayer", _isBayer?1:0 );
	prog.setUniform( "rgbToPCS", cm[0][0]>0?cm:_rgb_to_pcs );
	prog.setUniform( "singleChannel", _texChannels==1?1:0 );
	prog.setUniform( "modelMat", mat*getImageMat() );
}

inline void TexImage::draw( JR::Program& prog, const transf3_t& viewProjection, const transf3_t& modelMat, const colorMat_t& cm, const color_t& gma ) {
	if( imageAvailable() && changed() )
		makeGLImage();
	
	if( imageAvailable() && texId()>0 ) {
		glActiveTexture( GL_TEXTURE0 );
		glBindTexture( GL_TEXTURE_2D, texId() );
		transf3_t mat = viewProjection*modelMat;
		prog.use();
		setShaderParams( prog, mat, cm, gma );
		JR::drawScreenQuad();
		glUseProgram(0);
		glBindTexture( GL_TEXTURE_2D, 0 );
	}
}

inline void TexImage::draw( JR::Program& prog, const transf3_t& mat, const colorMat_t& cm, const color_t& gma ) {
	draw( prog, mat, transf3_t(1), cm, gma );
}

inline void TexImage::draw( JR::Program& prog, const transf3_t& viewProjection, const transf2_t& mat, const colorMat_t& cm, const color_t& gma ) {
	draw( prog, viewProjection, to3DTransform(mat), cm, gma );
}

inline void TexImage::draw( JR::Program& prog, const transf3_t& viewProjection, const pos_t& v, float s, const colorMat_t& cm, const color_t& gma ) {
	draw( prog, viewProjection, JR::translate(JR::vec3(v.x,v.y,0)) * JR::scale(JR::vec3(s,s,1)), cm, gma);
}

template<class T>
std::tuple<T,T,T,T> getPixelColor(const T* data, const isz_t& sz, unsigned c, const ipos_t& p, T defAlpha) {
	const T* pt = data+(p.y*sz.w+p.x)*c;
	switch(c) {
		case 1:
			return std::make_tuple(*pt,*pt,*pt,defAlpha);
		default:
		case 3:
			return std::make_tuple(*pt,*(pt+1),*(pt+2),defAlpha);
		case 4:
			return std::make_tuple(*pt,*(pt+1),*(pt+2),*(pt+3));
	}
}

inline colora_t TexImage::getColor( const ipos_t& pi, colorReaingMode_t mode ) const {
	colora_t rgba;
	if( !irct_t(pos_t(0,0),imgSize()).in(pi) )
		return colora_t(0,0,0,0);
	switch( _bitDepth ) {
		default:
		case 8: {
			auto [r,g,b,a] = getPixelColor( (unsigned char*)_data, imgSize(), _imageChannels, pi, (unsigned char)(255));
			rgba = colora_t(r,g,b,a)/255.f;
		} break;
		case 16: {
			auto [r,g,b,a] = getPixelColor( (jm::half*)_data, imgSize(), _imageChannels, pi, jm::half(1));
			rgba = colora_t(r,g,b,a);
		} break;
		case 15: {
			auto [r,g,b,a] = getPixelColor( (unsigned short*)_data, imgSize(), _imageChannels, pi, (unsigned short)(65535));
			rgba = colora_t(r,g,b,a)/65535.f;
		} break;
		case 32: {
			auto [r,g,b,a] = getPixelColor( (float*)_data, imgSize(), _imageChannels, pi, 1.f);
			rgba = colora_t(r,g,b,a);
		} break;
	}
	switch( mode ) {
		case colorReaingMode_t::SRGB: {
			color_t XYZ = _rgb_to_pcs*SCMS::invTonemap(color_t(rgba),_gamma);
			color_t srgb = SCMS::tonemap(SCMS::fromXYZ_D65(SCMS::PROF_sRGB)*XYZ,SCMS::PROF_sRGB.gamma);
			return colora_t(srgb,rgba.a);
		}
		case colorReaingMode_t::XYZ: {
			color_t XYZ = _rgb_to_pcs*SCMS::invTonemap(color_t(rgba),_gamma);
			return colora_t(XYZ,rgba.a);
		}
		default:
		case colorReaingMode_t::AS_FILE:
			return rgba;
	}
}

inline unsigned char* TexImage::createThumbnail( int& iw, int& ih, int THUMB_W, int THUMB_H ) {
	float scaleX = THUMB_W / float( imgSize().w );
	float scaleY = THUMB_H / float( imgSize().h );
	float scale = std::min( scaleX, scaleY );
	iw = int( roundf( imgSize().w * scale ) );
	ih = int( roundf( imgSize().h * scale ) );
	unsigned char* thumb_data4 = new unsigned char[iw*ih*4];
	
#ifdef THUMB_OPENCV
	if( _float ) {
		if( _imageChannels==3 ) {
			cv::Mat src( imgSize().h, imgSize().w, CV_32FC3, _data);
			cv::Mat temp;
			cv::resize( src, temp, cv::Size(iw,ih) );
			temp.convertTo( temp, CV_8U, 255 );
			cv::Mat dst( ih, iw, CV_8UC4, thumb_data4);
			if( _BGR )
				cv::cvtColor( temp, dst, cv::COLOR_RGB2BGRA );
			else
				cv::cvtColor( temp, dst, cv::COLOR_BGR2BGRA );
		}
		else { // _imageChannels == 4
			cv::Mat src( imgSize().h, imgSize().w, CV_8UC4, _data);
			cv::Mat temp;
			cv::resize( src, temp, cv::Size(iw,ih) );
			temp.convertTo( temp, CV_8U, 255 );
			cv::Mat dst( ih, iw, CV_8UC4, thumb_data4);
			if( _BGR )
				cv::cvtColor( temp, dst, cv::COLOR_RGBA2BGRA );
			else
				temp.copyTo( dst );
		}
	}
	else {
		if( _imageChannels==3 ) {
			cv::Mat src( imgSize().h, imgSize().w, CV_8UC3, _data);
			cv::Mat temp;
			cv::resize( src, temp, cv::Size(iw,ih) );
			cv::Mat dst( ih, iw, CV_8UC4, thumb_data4);
			if( _BGR )
				cv::cvtColor( temp, dst, cv::COLOR_RGB2BGRA );
			else
				cv::cvtColor( temp, dst, cv::COLOR_BGR2BGRA );
		}
		else { // _imageChannels == 4
			cv::Mat src( imgSize().h, imgSize().w, CV_8UC4, _data);
			cv::Mat temp;
			cv::resize( src, temp, cv::Size(iw,ih) );
			cv::Mat dst( ih, iw, CV_8UC4, thumb_data4);
			if( _BGR )
				cv::cvtColor( temp, dst, cv::COLOR_RGB2BGRA );
			else
				temp.copyTo( dst );
		}
	}
#else
	unsigned char* thumb_data = new unsigned char[iw*ih*_imageChannels];
	stbir_resize_uint8( (unsigned char*)_data, imgSize().w, imgSize().h, 0,
					thumb_data, iw, ih, 0, _imageChannels);//, 0, STBIR_EDGE_CLAMP );
	if( _imageChannels==3 ) {
		if( _BGR ) {
			for( int i=0; i<iw*ih; i++ ) {
				thumb_data4[i*4  ] = thumb_data[i*3+2];
				thumb_data4[i*4+1] = thumb_data[i*3+1];
				thumb_data4[i*4+2] = thumb_data[i*3  ];
				thumb_data4[i*4+3] = 255;
			}
		}
		else {
			for( int i=0; i<iw*ih; i++ ) {
				thumb_data4[i*4  ] = thumb_data[i*3  ];
				thumb_data4[i*4+1] = thumb_data[i*3+1];
				thumb_data4[i*4+2] = thumb_data[i*3+2];
				thumb_data4[i*4+3] = 255;
			}
		}
	}
	else { // _imageChannels == 4
		if( _BGR ) {
			for( int i=0; i<iw*ih; i++ ) {
				thumb_data4[i*4  ] = thumb_data[i*4+2];
				thumb_data4[i*4+1] = thumb_data[i*4+1];
				thumb_data4[i*4+2] = thumb_data[i*4  ];
				thumb_data4[i*4+3] = thumb_data[i*4+3];
			}
		}
		else {
			for( int i=0; i<iw*ih; i++ ) {
				thumb_data4[i*4  ] = thumb_data[i*4  ];
				thumb_data4[i*4+1] = thumb_data[i*4+1];
				thumb_data4[i*4+2] = thumb_data[i*4+2];
				thumb_data4[i*4+3] = thumb_data[i*4+3];
			}
		}
	}
	delete [] thumb_data;
#endif
	return thumb_data4;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* TexImage_h */
