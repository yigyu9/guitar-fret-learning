//
//  Slider.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Slider_h
#define JGL2_Slider_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Property.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

const float _def_slider_padding = 8;
const float _def_slider_height = 1.5f;
const float _def_slider_tick_offset = 6;

template<typename T>
struct Slider: public Property, public _Targettable, public _Valued<T> {
	Slider(float x, float y, float w, float h, const str_t& label );

	virtual void		valueSetCallback(Callback_t c, void* ud=nullptr );
	virtual void		value(const T& i) override;

	virtual void		minValue(const T v);
	virtual void		maxValue(const T v);
	virtual void		range(const T& minVal, const T& maxVal);
	virtual void		autostep(bool b);
	virtual void		step(const T& s);

	virtual void		logScale(bool b);
	
	virtual void		ticked(bool b);
	virtual void		valued(bool b);

	virtual T			value() const override { return _value; }

	virtual T			minValue() const { return _minValue; }
	virtual T			maxValue() const { return _maxValue; }
	virtual bool		autostep() const { return _autostep; }
	virtual T			step() const { return _step; }

	virtual bool		logScale() const { return _logScale; }

	virtual bool		ticked() const { return _ticked; }
	virtual bool		valued() const { return _valued; }

	virtual void		rearrange(NVGcontext* vg, autoscale_t scale) override;

protected:
	virtual T			xToValue( float x ) const;
	virtual float		valueToX( const T& v ) const;
	virtual void		gridDamage();
	virtual bool		gridDamaged() const { return _gridDamaged; }

	virtual void		updateGridStep();
//
	virtual void		drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) override;
	virtual bool		handle(event_t event) override;


	virtual sz2_t		minActionSize(NVGcontext*vg) const override;
	virtual shade_state_t	shadeState() const override;

	str_t				toString(const int v) const { return to_str(v); }
	str_t				toString(const double v) const { return to_str( roundOff(v,5) ); }

	virtual double		roundOff( double x, size_t precision ) const;
	virtual void		doValueSetCallback();
	
	T					_value;
	T					_minValue;
	T					_maxValue;
	T					_step;
	T					_keyStep;
	bool				_logScale			= false;
	bool				_gridDamaged		= false;
	bool				_pressed			= false;
	Callback_t			_valueSetCallback	= nullptr;
	void*				_valueSetUserdata	= nullptr;
	bool				_autostep			= true;
			
	float				_gridFineStep		= 1;
	float				_gridFineOffset		= 0;
	float				_gridMinorStep		= 1;
	float				_gridMinorOffset	= 0;
	float				_gridMajorStep		= 1;
	float				_gridMajorOffset	= 0;
	float				_gridTextStep		= 1;
	float				_gridTextOffset		= 0;
	double				_gridValueStep		= 1;
	double				_gridValueOffset	= 0;
	double				_gridValueBase		= 1;
			
	bool				_valued				= true;
	bool				_ticked				= true;
	pos_t				_cursorPt;
	float				_cursorR			= 5;
	float				_clickedCursorFromMouse;
			
	bool				_valueTipEngaged	= false;
	float				_valueTipAlpha		= 0.f;
};

template<typename T> inline  void Slider<T>::drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) {
	if( gridDamaged() ) {
		updateGridStep();
		_gridDamaged = false;
	}
	// TODO
	shade_state_t s = shadeState();
	slide_type_t type = (_valued?slide_type_t::VALUED:slide_type_t::NONE)|(_ticked?slide_type_t::TICKED:slide_type_t::NONE);

	_draw_slider_bar(vg,type,r,s);
	if( _ticked ) {
		_draw_slider_ticks_fine (vg, type, r, s, _gridFineOffset, _gridFineStep);
		_draw_slider_ticks_minor(vg, type, r, s, _gridMinorOffset, _gridMinorStep);
		_draw_slider_ticks_major(vg, type, r, s, _gridMajorOffset, _gridMajorStep);
	}
	if( _valued ) {
		nvgFontSize(vg, 7);
		nvgTextAlign(vg, (contains(type,slide_type_t::TICKED)?NVG_ALIGN_BOTTOM:NVG_ALIGN_TOP)|NVG_ALIGN_CENTER);
		nvgFillColor(vg, _color_f_label(s));
		float y = _pos_slider_number(type,r);
		double val = _gridValueOffset;
		for( float x=_gridTextOffset; x<=r.w-_size_slider_padding()*2+2; x+=_gridTextStep ) {
			double v = logScale()?pow(10,val):val;
			str_t str = toString( (double)v );
			nvgText(vg, x+r.x+_size_slider_padding(), y, str.c_str(), 0);
			val+=_gridValueStep;
		}
	}
	_cursorPt = pos_t( valueToX( value() ), _pos_f_slider_y(type, r) );
	_cursorR = _radius_f_slider_cursor(type);
	_draw_slider_cursor(vg,type,r,_cursorPt.x,s);
	if( _valueTipEngaged ) {
		_valueTipAlpha+=0.2f;
		if( _valueTipAlpha<1 ) animate();
		else _valueTipAlpha = 1.f;
	}
	else {
		_valueTipAlpha -=0.1f;
		if( _valueTipAlpha>0 ) animate();
		else _valueTipAlpha = 0.f;
	}
	if( _valueTipAlpha>0 ) {
		nvgSave(vg);
		nvgResetScissor(vg);
		str_t str = toString( value() );
		sz2_t sz = nvgMeasureText(vg, str, _pt_tooltip_text(),_font_tooltip_text() );
		rct_t rr;
		if(  0 > _cursorPt.y-sz.h-10+abs_pos().y ) {
			float r = _cursorPt.x-8, l = r-sz.w-6,
			t = _cursorPt.y-sz.h/2-1, b = t+sz.h+2;
			rr = rct_t(l,t,r-l,b-t);
			nvgShadowRect(vg, rr, 10, pos_t(0,0), _radius_tooltip_box()*1.5f);
			float R = _radius_tooltip_box();
			float RR=R*0.4477152507f;
			nvgBeginPath(vg);
			nvgMoveTo(vg,r+5,_cursorPt.y);
			nvgLineTo(vg,r,t);
			nvgLineTo(vg,l+R,t);
			nvgBezierTo(vg,l+RR,t,l,t+RR,l,t+R);
			nvgLineTo(vg,l,b-R);
			nvgBezierTo(vg,l,b-RR,l+RR,b,l+R,b);
			nvgLineTo(vg,r-R,b);
			nvgClosePath(vg);
		}
		else {
			rr = rct_t(_cursorPt.x-sz.w/2-3, _cursorPt.y-sz.h-10, sz.w+6, sz.h+2);
			nvgShadowRect(vg, rr, 10, pos_t(0,0), _radius_tooltip_box()*1.5f);
			nvgPathBalloon(vg,rr,pos_t(_cursorPt.x-rr.x,rr.h+10),_radius_tooltip_box(),sz2_t(6,5));
			nvgTextAlign(vg, NVG_ALIGN_CENTER|NVG_ALIGN_MIDDLE);
		}
		nvgFillColor(vg, nvgColorA(_color_tooltip_box(),_valueTipAlpha));
		nvgFill(vg);
		nvgStrokeWidth(vg, _width_tooltip_bound() );
		nvgStrokeColor(vg, nvgColorA(_color_tooltip_bound(),_valueTipAlpha));
		nvgStroke(vg);
		nvgFillColor(vg, nvgColorA(_color_tooltip_text(),_valueTipAlpha));
		nvgTextAligned(vg,rr,str,NVG_ALIGN_CENTER|NVG_ALIGN_MIDDLE);
		nvgRestore(vg);
	}
}

template<typename T> inline bool Slider<T>::handle(event_t event) {
	switch( event ) {
		case event_t::MOVE: {
			pos_t pt = _JGL::eventPt();
			if( length(pt-_cursorPt)<_cursorR+0.1 ) {
				_valueTipEngaged = true;
				damage();
			}
			else {
				_valueTipEngaged = false;
				damage();
			}
		} break;
		case event_t::PUSH: {
			pos_t pt = _JGL::eventPt();
			if( length(pt-_cursorPt)<_cursorR+0.1 ) {
				_pressed =true;
				_clickedCursorFromMouse = _cursorPt.x-pt.x;
				damage();
				return true;
			}
			else {
				_pressed = false;
				value(xToValue(pt.x));
				_valueTipEngaged = true;
				doValueSetCallback();
				damage();
				return true;
			}
		}	break;
		case event_t::DRAG:
			if( _pressed ) {
				value( xToValue(_JGL::eventPt().x+_clickedCursorFromMouse ) );
				damage();
				return true;
			} break;
		case event_t::LEAVE:
			if( !_pressed ) {
				_valueTipEngaged = false;
				damage();
			}
			break;
		case event_t::CANCEL:
		case event_t::RELEASE:
			if( _pressed ) {
				_pressed = false;
				pos_t pt = _JGL::eventPt();
				if( length(pt-_cursorPt)>_cursorR+0.1 )
					_valueTipEngaged = false;
				doValueSetCallback();
				damage();
				return true;
			} break;
		case event_t::KEYUP:
			_valueTipEngaged = false;
			break;
		case event_t::KEYDOWN:
		case event_t::REPEAT:
			if( _JGL::eventKey() == GLFW_KEY_LEFT ) {
				_valueTipEngaged = true;
				_valueTipAlpha = 1.f;
				if( value()>minValue() ) {
					T v;
					if( logScale() ) {
						if(_keyStep>=_step )
							v = (T)pow(10,round( (log10(value())-_keyStep)/_keyStep )*_keyStep);
						else
							v = (T)pow(10, log10(value())-_step );
					}
					else {
						if(_keyStep>=_step )
							v = (T)(floor( (value()-_keyStep-minValue())/_keyStep+.5f )*_keyStep)+minValue();
						else
							v = value()-_step;
					}
					value(v);
					doValueSetCallback();
					damage();
				}
				return true;
			}
			else if( _JGL::eventKey() == GLFW_KEY_RIGHT ) {
				_valueTipEngaged = true;
				_valueTipAlpha = 1.f;
				if( value()<maxValue() ) {
					T v;
					if( logScale() ) {
						if(_keyStep>=_step )
							v = (T)pow(10,round( (log10(value())+_keyStep)/_keyStep )*_keyStep);
						else
							v = (T)pow(10, log10(value())+_step );
					}
					else {
						if(_keyStep>=_step )
							v = (T)(floor( (value()+_keyStep-minValue())/_keyStep+.5f )*_keyStep)+minValue();
						else
							v = value()+_step;
					}
					value(v);
					doValueSetCallback();
					damage();
				}
				return true;
			}
			break;
		default:
			break;
	}
	return Property::handle(event);
}

template<typename T> inline double Slider<T>::roundOff( double x, size_t precision ) const {
	double base = pow(10,std::min(round(log10(std::max(10e-2,(double)abs(minValue())))),
								  round(log10((double)maxValue())))-precision);
	if( logScale() )
		base = pow(10,round(log10(x))-precision);
	return round(x/base)*base;
}

template<typename T> inline void Slider<T>::doValueSetCallback() {
	if( _valueSetCallback )
		_valueSetCallback(this,_valueSetUserdata);
}

template<typename T> inline void Slider<T>::valueSetCallback(Callback_t c, void* ud ) {
	_valueSetCallback = c;
	_valueSetUserdata = ud;
}

template<typename T> inline void Slider<T>::ticked(bool b) {
	if( b!=_ticked ) {
		_ticked = b;
		damage();
	}
}

template<typename T> inline void Slider<T>::valued(bool b) {
	if( b!=_valued ) {
		_valued = b;
		damage();
	}
}

template<typename T> inline void Slider<T>::range(const T& minVal, const T& maxVal) {
	if( maxVal<minVal ) {
		minValue(maxVal);
		maxValue(minVal);
	}
	else {
		minValue(minVal);
		maxValue(maxVal);
	}
}

template<typename T> inline void Slider<T>::step(const T& s) {
	if( autostep() || _step!=s ) {
		_step = s;
		autostep( false );
		T v;
		if( logScale() )
			v = T(pow(10,round(log10(value())/(float)_step)*_step));
		else
			v = T(round(value()/(float)_step)*_step);
		if( value()!=v )
			value(v);
		damage();
	}
}

template<typename T> inline void Slider<T>::logScale(bool b) {
	assert( typeid(T)!=typeid(int) );
	if( _logScale!=b ) {
		_logScale = b;
		if( _logScale ) {
			maxValue(maxValue());
			minValue(minValue());
		}
		damage();
		gridDamage();
	}
}

template<typename T> inline void Slider<T>::gridDamage() {
	_gridDamaged = true;
}

template<typename T> inline void Slider<T>::autostep(bool b) {
	if( _autostep != b ) {
		_autostep = b;
		if( _autostep ) {
			updateGridStep();
			value(_value);
		}
	}
}

template<typename T> inline sz2_t Slider<T>::minActionSize(NVGcontext*vg) const {
	return sz2_t(30,25);
}

template<typename T> inline shade_state_t	 Slider<T>::shadeState() const {
	shade_state_t ret = Widget::shadeState();
	if( _pressed ) ret = ret | shade_state_t::PRESSED;
	return ret;
}

template<typename T> inline void Slider<T>::rearrange(NVGcontext* vg, autoscale_t scale) {
	Property::rearrange(vg,scale);
	gridDamage();
}

template<typename T> inline T Slider<T>::xToValue( float x ) const {
	float sliderWidth = _actionBox.w - _size_slider_padding()*2;
	float xx = (x-(_actionBox.x+_size_slider_padding()))/sliderWidth;
	if( !logScale() )
		return T(mix( minValue(), maxValue(), xx ));
	else
		return T(powf(10.f,mix( log10f(float(minValue())), log10f(float(maxValue())), xx ) ));
}

template<> inline int Slider<int>::xToValue( float x ) const {
	float sliderWidth = _actionBox.w - _size_slider_padding()*2;
	float xx = (x-(_actionBox.x+_size_slider_padding()))/sliderWidth;
	if( !logScale() )
		return int(mix( float(minValue()), float(maxValue()), xx )+.5f);
	else
		return int(powf(10.f,mix( log10f(float(minValue())), log10f(float(maxValue())), xx ) ));
}

template<typename T> float Slider<T>::valueToX( const T& v ) const {
	float sliderWidth = _actionBox.w - _size_slider_padding()*2;
	float xx;
	if( !logScale() )
		xx = (v-minValue())/float(maxValue()-minValue());
	else
		xx = float(log10(v)-log10(minValue()))/float(log10(maxValue())-log10(minValue()));
	return xx*sliderWidth + _actionBox.x+ _size_slider_padding();
}

const float _def_grid_width_step = 5;

template<> inline
Slider<float>::Slider(float x, float y, float w, float h, const str_t& label )
: Property(x,y,w,h,label) {
	_minValue = 0;
	_maxValue = 1;
	_value = 0;
	_step = 0.1f;
	_keyStep = 0.1f;
	gridDamage();
}

template<> inline
Slider<int>::Slider(float x, float y, float w, float h, const str_t& label )
: Property(x,y,w,h,label) {
	_minValue = 0;
	_maxValue = 10;
	_value = 0;
	_step = 1;
	_keyStep = 1;
	gridDamage();
}

template<> inline
void Slider<int>::value(const int& i) {
	int v = i;
	v = int(round((v-minValue())/(float)_step)*_step)+minValue();
	v = std::max(v,minValue());
	v = std::min(v,maxValue());
	if( _value!=v ) {
		_value=v;
		updateAutoVal();
		damage();
		doCallback();
	}
}

template<> inline
void Slider<float>::value(const float& i) {
	double v = (double)i;
	if( logScale() )
		v = pow(10,round(log10(v)/_step)*_step);
//		v = pow(10,round((log10(v)-log10(minValue()))/(float)_step)*_step+log10(minValue()));
	else
		v = round((v-minValue())/(float)_step)*_step+minValue();
	v = roundOff( v, 5 );
	v = std::max(v,(double)minValue());
	v = std::min(v,(double)maxValue());
	if( ( logScale() && pow(10,round(log10(v)/_step)*_step)!=pow(10,round(log10(_value)/_step)*_step) )
	   || (!logScale() && round((_value-minValue())/(float)_step)!=round((v-minValue())/(float)_step) )) {
		_value=float(v);
		updateAutoVal();
		damage();
		doCallback();
	}
}

template<> inline
void Slider<int>::updateGridStep() {
	float sliderWidth = (_actionBox.w - _def_slider_padding*2);
	int maxGridCount = int(sliderWidth/_def_grid_width_step)+1;
	int range = maxValue()-minValue();
	if( !logScale() ) {
		int step = 1;
		int minorStep = 5;
		int majorStep = 10;
		int textStep = 10;
		while( true ) {
			if( range/(float)step<maxGridCount ) {
				minorStep=step*5;
				majorStep=step*10;
				textStep =step*5;
				break;
			}
			if( range/((float)step*2)<maxGridCount ) {
				minorStep=-1;
				majorStep=step*10;
				textStep=step*10;
				step = step*2;
				break;
			}
			if( range/((float)step*5)<maxGridCount ) {
				step*=5;
				minorStep=step*2;
				majorStep=step*20;
				textStep = step*10;
				break;
			}
			step*=10;
		}
		_gridFineOffset = (ceil((minValue()/(float)step))*step-minValue())/float(range)*sliderWidth;
		_gridFineStep = step/float(range)*sliderWidth;
		_gridMinorOffset = (ceil((minValue()/(float)minorStep))*minorStep-minValue())/float(range)*sliderWidth;
		_gridMinorStep = minorStep/float(range)*sliderWidth;
		_gridMajorOffset = (ceil((minValue()/(float)majorStep))*majorStep-minValue())/float(range)*sliderWidth;
		_gridMajorStep = majorStep/float(range)*sliderWidth;
		_gridTextOffset = (ceil((minValue()/(float)textStep))*textStep-minValue())/float(range)*sliderWidth;
		_gridTextStep = textStep/float(range)*sliderWidth;
		_gridValueStep = textStep;
		_gridValueOffset = int(ceil((minValue()/(float)textStep))*textStep);
		_gridValueBase = pow(10,floor(log10(majorStep))-1);

		_keyStep = step>0?step:minorStep;
		if( autostep() ) {
			_step = step>0?step:minorStep;
			value(_value);
		}
	}
}

template<> inline
void Slider<float>::updateGridStep() {
	float sliderWidth = (_actionBox.w - _def_slider_padding*2);
	int maxGridCount = int(sliderWidth/_def_grid_width_step)+1;
	float range, mm;
	if( !logScale() ) {
		range = maxValue()-minValue();
		mm = minValue();
	}
	else {
		range = log10f(maxValue())-log10f(minValue());
		mm = log10f(minValue());
	}
	float step = powf(10,floor(log10f(range))-2);
	float minorStep = step*5;
	float majorStep = step*10;
	float textStep = step*10;

	while( true ) {
		if( range/(float)step<maxGridCount ) {
			minorStep=step*5;
			majorStep=step*10;
			textStep =step*5;
			break;
		}
		if( range/((float)step*2)<maxGridCount ) {
			minorStep=-1;
			majorStep=step*10;
			textStep=step*10;
			step = step*2;
			break;
		}
		if( range/((float)step*5)<maxGridCount ) {
			step*=5;
			minorStep=step*2;
			majorStep=step*20;
			textStep = step*10;
			break;
		}
		step*=10;
		minorStep*=10;
		majorStep*=10;
	}

	_gridFineOffset = (ceilf((mm/(float)step))*step-mm)/float(range)*sliderWidth;
	_gridFineStep = step/float(range)*sliderWidth;
	_gridMinorOffset = (ceilf((mm/(float)minorStep))*minorStep-mm)/float(range)*sliderWidth;
	_gridMinorStep = minorStep/float(range)*sliderWidth;
	_gridMajorOffset = (ceilf((mm/(float)majorStep))*majorStep-mm)/float(range)*sliderWidth;
	_gridMajorStep = majorStep/float(range)*sliderWidth;
	_gridTextOffset = (ceilf((mm/(float)textStep))*textStep-mm)/float(range)*sliderWidth;
	_gridTextStep = textStep/float(range)*sliderWidth;
	_gridValueStep = textStep;
	_gridValueOffset = ceilf((mm/(float)textStep))*textStep;
	_gridValueBase = powf(10,floor(log10(majorStep))-1);
	
	_keyStep = step>0?step:minorStep;
	if( autostep() ) {
		_step = step>0?step:minorStep;
		value(_value);
	}
}

template<> inline
void Slider<int>::minValue(const int v) {
	int m = v;
	if( logScale() && sign(m)<=0 ) {
		m = 1;
	}
	if( _minValue != m ) {
		_minValue = m;
		if( _value<_minValue ) value(_minValue);
		damage();
		gridDamage();
	}
}

template<> inline
void Slider<float>::minValue(const float v) {
	float m = v;
	if( logScale() && sign(m)<=0 ) {
		m = 1e-10f;
	}
	if( _minValue != m ) {
		_minValue = m;
		if( _value<_minValue ) value(_minValue);
		damage();
		gridDamage();
	}
}

template<> inline
void Slider<int>::maxValue(const int v) {
	int m = v;
	if( logScale() && sign(m)<=0 ) {
		m = 1000000000;
	}
	if( _maxValue != m ) {
		_maxValue = m;
		if( _value>_maxValue ) value(_maxValue);
		damage();
		gridDamage();
	}
}

template<> inline
void Slider<float>::maxValue(const float v) {
	float m = v;
	if( logScale() && sign(m)<=0 ) {
		m = 1e10f;
	}
	if( _maxValue != m ) {
		_maxValue = m;
		if( _value>_maxValue ) value(_maxValue);
		damage();
		gridDamage();
	}
}

using SliderF = Slider<float>;
using SliderI = Slider<int>;

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Slider_h */
