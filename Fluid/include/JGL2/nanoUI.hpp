//
//  nanoUI.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/19/24.
//

#ifndef nanoUI_h
#define nanoUI_h

#include <string>
#include <vector>

#include <nanovg/nanovg.h>
//#include <nanovg/nanovg_gl.h>
#include "math.h"

enum NANO_UI_MOD {
	MOD_NONE  = 0,
	MOD_SHIFT_ = 1,
	MOD_CTRL  = 2,
	MOD_ALT_   = 4,
	MOD_SUPER = 8,
	MOD_LBTN  = 16,
	MOD_RBTN  = 32,
	MOD_BTN_MASK = 0xF0,
};

enum NANO_UI_BUTTON {
	BUTTON_NONE = 0,
	BUTTON_LEFT = 1,
	BUTTON_RIGHT= 2,
	BUTTON_MIDDLE=3,
};

#ifdef JGL2_Widget_h
namespace JGL2 {
	enum class event_t;
	enum class button_t;
}
#endif

const float NANO_WIDGET_HEIGHT_PT_RATIO = 1.5f;
const float NANO_CHECK_SIZE_PT_RATIO = 1.3f;
const float NANO_SLIDER_KNOB_RADIUS_RATIO = 0.3f;
const float NANO_SLIDER_LABEL_OFFSET_PT_RATIO = 0.5f;
const float NANO_GROUP_DEF_PADDING_PT_RATIO = 0.5f;
const float NANO_GROUP_HANDLE_Y_OFFSET = 20.f;

const NVGcolor NANO_UI_SHADOW_COLOR = nvgRGBA(0,0,0,128);
const NVGcolor NANO_UI_SHADOW_OUT_COLOR = nvgRGBA(0,0,0,0);

const NVGcolor NANO_UI_DOWNBOX_INNER_COLOR = nvgRGBA(0,0,0,96);
const NVGcolor NANO_UI_DOWNBOX_OUTER_COLOR = nvgRGBA(0,0,0,128);

const NVGcolor NANO_SLIDER_KNOB_BACKGROUND_COLOR = nvgRGBA(40,43,48,128);
const NVGcolor NANO_SLIDER_KNOB_TOP_COLOR = nvgRGBA(255,255,255,116);
const NVGcolor NANO_SLIDER_KNOB_BOTTOM_COLOR = nvgRGBA(64,64,64,116);
const NVGcolor NANO_SLIDER_KNOB_BOUND_COLOR = nvgRGBA(0,0,0,92);


const float NANO_GROUP_CORNER_RADIUS = 7.0f;
const float NANO_GROUP_SHADOW_WIDTH = 10.f;

const float NANO_GROUP_SHRINK_STEP = 0.1f;

struct nanoRect {
	float _x, _y, _w, _h;
	nanoRect( float x, float y, float w, float h ): _x(x),_y(y),_w(w),_h(h){}
	nanoRect( float w, float h ): _x(0),_y(0),_w(w),_h(h){}
	nanoRect(): _x(0),_y(0),_w(0),_h(0){}
	nanoRect resizeLeft ( float w ) const { return nanoRect( _x, _y, w, _h ); }
	nanoRect resizeRight( float w ) const { return nanoRect( _x+_w-w, _y, w, _h ); }
	nanoRect offsetLeft ( float d ) const { return nanoRect( _x, _y, _w-d, _h ); }
	nanoRect offsetRight( float d ) const { return nanoRect( _x+d, _y, _w-d, _h ); }
	nanoRect offsetDown ( float d ) const { return nanoRect( _x, _y, _w, _h-d ); }
	nanoRect offsetUp	( float d ) const { return nanoRect( _x, _y+d, _w, _h-d ); }
	nanoRect resizeUp   ( float h ) const { return nanoRect( _x, _y, _w, h ); }
	nanoRect resizeDown ( float h ) const { return nanoRect( _x, _y+_h-h, _w, h ); }
	nanoRect resizeHorz ( float w ) const { return nanoRect( _x+(_w-w)/2, _y, w, _h ); }
	nanoRect resizeVert ( float h ) const { return nanoRect( _x, _y+(_h-h)/2, _w, h ); }
	nanoRect expand		( float d ) const { return nanoRect( _x-d, _y-d, _w+d+d, _h+d+d ); }
	bool inside( float x, float y ) const { return x>=_x && y>=_y && x<_x+_w && y<_y+_h; }
};

extern void nvgRegisterDefaultFonts( NVGcontext* vg, const std::string& path="" );
extern void nvgShadowedText( NVGcontext* vg, float x, float y,
							const char* str,
							const NVGcolor& textColor,
							const NVGcolor& shadowColor=NANO_UI_SHADOW_COLOR );

extern char* cpToUTF8(int cp, char* str);
extern void drawKnob(NVGcontext* vg, float kx, float ky, float kr);
extern void drawDownBox(NVGcontext* vg, const nanoRect& r);
extern void drawCheck(NVGcontext* vg, const nanoRect& r,const NVGcolor& c);
extern nanoRect measureText( NVGcontext* vg, float pt, const char* fnt, const std::string& txt);
extern void drawText(NVGcontext* vg, const nanoRect& r, float pt, const char* fnt, int align, const std::string& txt, const NVGcolor& color );
extern void drawGroupBack(NVGcontext* vg,const nanoRect& r, const NVGcolor& color,
						  const NVGcolor& btnColor, bool arrowDir, const nanoRect& hr);
extern void drawOptionBack(NVGcontext* vg,const nanoRect& r, const NVGcolor& color);
extern void drawTicks(NVGcontext* vg,const nanoRect& r, float baseY, float height, float w, const NVGcolor& c, const std::vector<float>& poss);



struct nanoGroup;
struct nanoExpandable;

struct nanoWidget {
	using rgba = NVGcolor;
	using str = std::string;
	using VG = NVGcontext;
	struct nanoWidgetGlobal {
		float			labelPt				= 14;
		std::string		lableFont			= "system";
		NVGcolor		labelColor			= nvgRGBA(255,255,255,192);
		NVGcolor		labelColorDisable	= nvgRGBA(255,255,255,60);
		NVGcolor		groupColor			= nvgRGBA(62,64,68,192);
		NANO_UI_MOD 	ui_mods				= (NANO_UI_MOD)0;
		float			sliderWidth			= 100.f;
		float			sliderHeight		= 2.f;
	};
	static nanoWidgetGlobal& global() {
		static nanoWidgetGlobal g;
		return g;
	}
	nanoRect		_rect;
	float			_margin =0;
	float			_padding=0;
	bool			_enabled = true;
	bool			_wAutosize = false;
	bool			_hAutosize = false;
	std::string		_title;
	int				_titleAlign = NVG_ALIGN_LEFT|NVG_ALIGN_MIDDLE;

	nanoWidget( float x, float y, float w, float h, const std::string& title )
	:_rect(x,y,w,h), _title(title), _enabled(true),
	_wAutosize(_rect._w<=0), _hAutosize(_rect._h<=0){}
	virtual float	margin()	const 	{ return _margin; }
	virtual float	padding()	const 	{ return _padding; }
	virtual bool	enabled()	const 	{ return _enabled; }
	virtual str		title() 	const 	{ return _title; }
	virtual float&	margin() 			{ return _margin; }
	virtual float&	padding()			{ return _padding; }
	virtual bool&	enabled()			{ return _enabled; }
	virtual str&	title()				{ return _title; }

	virtual void 	margin(float v)		{ _margin = v; }
	virtual void 	padding(float v)	{ _padding = v; }
	virtual void 	enabled(bool v)		{ _enabled = v; }
	virtual void 	title(const str& v)	{ _title = v; }

	static void 	labelPt(float c) 			{ global().labelPt = c; }
	static void 	labelColor(rgba c) 			{ global().labelColor = c; }
	static void 	labelColorDisable(rgba c) 	{ global().labelColorDisable = c; }
	static void 	groupColor(rgba c) 			{ global().groupColor = c; }
	static void 	sliderWidth(float s) 		{ global().sliderWidth = s; }
	static void 	sliderHeight(float s) 		{ global().sliderHeight = s; }
	static void 	lableFont(const str& c)		{ global().lableFont = c; }

	
	virtual bool 	render(VG* vg) { updateSize(vg); drawLabel(vg,contentRect()); return false; }
	virtual void	updateSize(VG* vg) {
		if( _wAutosize || _rect._w<=0 )	_rect._w = labelSize(vg)._w+padding()*2+margin()*2;
		if( _hAutosize || _rect._h<=0 )	_rect._h = labelSize(vg)._h+padding()*2+margin()*2;
	}
	virtual bool 	press	(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) { return false; }
	virtual bool 	release	(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) { _pressedOn = false; return false; }
	virtual bool 	move	(float x, float y, NANO_UI_MOD mods )  { return false; }

	virtual nanoRect contentRect()	const { return _rect.expand(-padding()-margin()); }
	virtual nanoRect backRect()		const { return _rect.expand(-margin()); }


	virtual NVGcolor	labelColor()	const { return _enabled?global().labelColor:global().labelColorDisable; }
	virtual float		labelPt()		const { return global().labelPt; }
	virtual const char*	labelFont()		const { return global().lableFont.c_str(); }
	virtual nanoRect 	labelSize(VG* vg) const { return measureText(vg,labelPt(),labelFont(),_title ); }
	virtual void 		drawLabel(VG* vg, const nanoRect& r ) const {
		drawText(vg, r, labelPt(), labelFont(), _titleAlign, _title, labelColor() );
	}
	
#ifdef JGL2_Widget_h
	// JGL bining
	
	static NANO_UI_BUTTON toNanoUIButtonJGL2(const JGL2::button_t& b);
	static NANO_UI_MOD toNanoUIModsJGL2();
	static bool nanoUIHandle(const JGL2::event_t& e, nanoWidget& group );
	static bool nanoUIRender( NVGcontext* vg, float width, float height, nanoWidget& group ) { return group.render(vg); }
	
#elif defined _glfw3_h_

	// GLFW direct binding fuctions
	static bool nanoUIButton( GLFWwindow* win, int button, int action, int mods, nanoWidget& group );
	static bool nanoUIMove( GLFWwindow* win, double mx, double my, nanoWidget& group );
	static void nanoUIRender( NVGcontext* vg, int width, int height, nanoWidget& group );
	static NVGcontext* nanoUIInit(const std::string& path );
#endif

protected:
	bool	_pressedOn = false;
	friend	nanoGroup;
};




struct nanoExpandable: nanoWidget {
	nanoExpandable( float x, float y, float w, float h, const std::string& title )
	: nanoWidget(x,y,w,h,title){}
	virtual inline nanoRect expandedRect() const=0;
	virtual inline bool expanded() const { return _expanded; }
	virtual inline void shrink() { _expanded = false; }
	virtual inline void expand() { _expanded = true; }
protected:
	bool _expanded = false;
};







struct nanoGroup: nanoWidget {
	const float handleWidth=15;
	const float handleHeight=34;

	std::vector<nanoWidget*> _widgets;

	bool _wScaleChild = true;
	bool _hPackChild = true;
	enum EXPANSION_STATE {
		NANO_GROUP_EXPANDED = 0,
		NANO_GROUP_SHRINKING = 1,
		NANO_GROUP_SHRINKED = 2,
		NANO_GROUP_EXPANDING = 3,
	};
	nanoGroup(float x=0, float y=0, float w=0, float h=0, const std::string& title="")
	:nanoWidget(x,y,w,h,title){ _margin=0; _padding=labelPt()*NANO_GROUP_DEF_PADDING_PT_RATIO; }

	virtual ~nanoGroup() {
		for(nanoWidget*& w: _widgets ) {
			if( w ) delete w;
			w = nullptr;
		}
		_widgets.clear();
	}
	virtual void add(nanoWidget* widget) {
		_widgets.push_back(widget);
	}
	virtual nanoWidget& child(size_t i) {
		assert( i<_widgets.size() );
		return *_widgets[i];
	}
	virtual const nanoWidget& child(size_t i) const {
		assert( i<_widgets.size() );
		return *_widgets[i];
	}
	virtual size_t children() const { return _widgets.size(); }
	virtual bool render(NVGcontext* vg) override {
		if( _widgets.size()<1 ) return false;
		bool ret = processAnimation();
		updateSize(vg);
		nanoRect backR = backRect();
		nanoRect contR = contentRect();
		float visibleRectOffset = backR._w*(1-_expandedRatio);
		float visibleRectWidth  = backR._w*(_expandedRatio);
		drawGroupBack(vg,backR.resizeLeft(visibleRectWidth),global().groupColor,global().labelColor,
					  _expState==NANO_GROUP_SHRINKED||_expState==NANO_GROUP_SHRINKING,
					  handleRect());
		nvgSave(vg);
		nvgIntersectScissor(vg,backR._x+visibleRectOffset,backR._y,visibleRectWidth,backR._h);
		nvgTranslate(vg, contR._x, contR._y);
		if( contR._w>0 && contR._h>0 ) nvgIntersectScissor(vg, 0, 0, contR._w, contR._h);
		nvgTranslate(vg,-visibleRectOffset,0);
		for( auto& widget: _widgets ) if( widget ) {
			nanoExpandable* e = dynamic_cast<nanoExpandable*>(widget);
			if( !e || !e->expanded() ) ret |= widget->render(vg);
		}
		for( auto& widget: _widgets ) if( widget ) {
			nanoExpandable* e = dynamic_cast<nanoExpandable*>(widget);
			if( e && e->expanded() ) ret |= widget->render(vg);
		}
		nvgRestore(vg);
		return ret;
	}
	virtual void updateSize(NVGcontext* vg) override {
		if( _widgets.size()<1 ) return;
		for( auto& widget: _widgets ) if( widget )
			widget->updateSize(vg);
		
		if( _wAutosize || _rect._w<=0) for( auto& widget: _widgets ) if( widget )
			_rect._w = std::max( _rect._w, widget->_rect._w+widget->_rect._x+(margin()+padding())*2 );
		if( _wScaleChild ) for( auto& widget: _widgets ) if( widget ) {
			widget->_rect._w = _rect._w-(padding()+margin())*2;
			widget->_wAutosize = false;
		}
		if( _hPackChild ) {
			float y = 0;
			for( auto& widget: _widgets ) if( widget ) {
				widget->_rect._y = y;
				y+=widget->_rect._h;
			}
		}
		if( _hAutosize || _rect._h<=0 ) for( auto& widget: _widgets ) if( widget )
			_rect._h = std::max( _rect._h, widget->_rect._h+widget->_rect._y+(margin()+padding())*2 );
	}
	virtual void shrink( bool animating = true ) {
		if( _expState == NANO_GROUP_EXPANDED ){
			shrinkExpandables( nullptr );
			if( animating )
				_expState = NANO_GROUP_SHRINKING;
			else {
				_expState = NANO_GROUP_SHRINKED;
				_expandedRatio = 0;
			}
		}
	}
	virtual void expand( bool animating = true ) {
		if( _expState == NANO_GROUP_SHRINKED ){
			if( animating )
				_expState = NANO_GROUP_EXPANDING;
			else {
				_expState = NANO_GROUP_EXPANDED;
				_expandedRatio = 1;
			}
		}
	}
	virtual bool press(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		if( _widgets.size()<1 ) {
			_pressedOn = false;
			return _pressedOn;
		}
		nanoWidget* pressedWidget = nullptr;
		if( handleRect().inside(x,y) ) {
			if( _expState == NANO_GROUP_EXPANDED )
				shrink(true);
			else if( _expState == NANO_GROUP_SHRINKED )
				expand(true);
			_pressedOn = true;
			return _pressedOn;
		}
		if( _expState!= NANO_GROUP_EXPANDED ) return false;
		_pressedOn =  _rect.inside(x, y);
		for( auto& widget: _widgets ) if( widget ) {
			nanoExpandable* e = dynamic_cast<nanoExpandable*>(widget);
			if( e && e->expanded() ) _pressedOn |= e->expandedRect().inside(x,y);
		}
		if( _pressedOn && _enabled ) {
			nanoRect contR = contentRect();
			for( auto& widget: _widgets ) if( widget ) {
				if( widget->press(x-contR._x,y-contR._y,button,mods) ) {
					pressedWidget=widget;
					break;
				}
			}
		}
		shrinkExpandables( pressedWidget );
		return _pressedOn;
	}
	virtual bool release(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		if( _widgets.size()<1 ) return _pressedOn;
		nanoRect contR = contentRect();
		for( auto& widget: _widgets ) if( widget && widget->_pressedOn )
			if( widget->release(x-contR._x,y-contR._y,button,mods) ) return true;
		_pressedOn = false;
		return false;
	}
	virtual bool move(float x, float y, NANO_UI_MOD mods ) override {
		if( _widgets.size()<1 ) return _pressedOn;
		nanoRect contR = contentRect();
		for( auto& widget: _widgets ) if( widget )
			if( widget->move(x-contR._x,y-contR._y,mods) ) return true;
		return _pressedOn;
	}
	virtual bool processAnimation() {
	   bool ret = false;
	   if( _expState == NANO_GROUP_EXPANDING ) {
		   _expandedRatio+=NANO_GROUP_SHRINK_STEP;
		   if( _expandedRatio>0.99 ) {
			   _expandedRatio=1;
			   _expState = NANO_GROUP_EXPANDED;
		   }
		   ret = true;
	   }
	   else if( _expState == NANO_GROUP_SHRINKING ) {
		   _expandedRatio-=NANO_GROUP_SHRINK_STEP;
		   if( _expandedRatio<0.01 ) {
			   _expandedRatio=0;
			   _expState = NANO_GROUP_SHRINKED;
		   }
		   ret = true;
	   }
	   return ret;
	}
	virtual void shrinkExpandables(nanoWidget* w) {
		for( auto& c: _widgets ) {
			if( w == c ) continue;
			nanoExpandable* e = dynamic_cast<nanoExpandable*>(c);
			if( e ) e->shrink();
		}
	}
	virtual nanoRect handleRect() const {
	   float hndH = std::min( backRect()._h-6, handleHeight );
	   nanoRect r = backRect();
	   float visibleRectWidth  = r._w*(_expandedRatio);
	   float handleY = std::min( NANO_GROUP_HANDLE_Y_OFFSET, (r._h-hndH)/2 );
	   return nanoRect( r._x + visibleRectWidth, r._y+handleY, handleWidth, hndH );
	}

protected:
	float			_expandedRatio	= 1;
	bool 			_arrowDirection	= false;
	EXPANSION_STATE _expState		= NANO_GROUP_EXPANDED;
};










struct nanoCheck: nanoWidget {
	bool* _checked = nullptr;
	nanoCheck( float x, float y, float w, const std::string& title, bool& checked )
	:nanoWidget(x, y, w, 0, title ), _checked(&checked){}

	virtual nanoRect checkRect() {
		return contentRect().resizeVert(labelPt()).resizeLeft(labelPt());
	}
	virtual bool render(NVGcontext* vg) override {
		updateSize(vg);
		drawLabel(vg, contentRect().offsetRight( labelPt()*NANO_CHECK_SIZE_PT_RATIO ) );
		bool checked = false;
		if( _checked && *_checked ) checked = true;
		nanoRect checkR = checkRect();
		drawDownBox(vg, checkR);
		if( checked ) drawCheck(vg,checkR,labelColor());
		return false;
	}
	virtual void updateSize(NVGcontext* vg) override {
		if( _wAutosize || _rect._w<=0 )
			_rect._w = labelSize(vg)._w+padding()*2+margin()*2+labelPt()*NANO_CHECK_SIZE_PT_RATIO;
		if( _hAutosize || _rect._h<=0 )
			_rect._h = labelPt()*NANO_WIDGET_HEIGHT_PT_RATIO;
	}
	virtual bool press(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		_pressedOn = contentRect().inside(x, y);
		if( _pressedOn && _enabled ) {
			if( _checked ) *_checked = !*_checked;
		}
		return _pressedOn;
	}
};

struct nanoCheckR: nanoCheck {
	nanoCheckR( float x, float y, float w, const std::string& title, bool& checked )
	:nanoCheck(x, y, w, title, checked ) {}
	virtual nanoRect checkRect() override {
		return contentRect().resizeRight( labelPt() ).resizeVert( labelPt() );
	}
	virtual bool render(NVGcontext* vg) override {
		updateSize(vg);
		drawLabel(vg, contentRect().offsetLeft( labelPt()*NANO_CHECK_SIZE_PT_RATIO ));
		bool checked = false;
		if( _checked && *_checked ) checked = true;
		nanoRect checkR = checkRect();
		drawDownBox(vg, checkR);
		if( checked ) drawCheck(vg,checkR,labelColor());
		return false;
	}
};







struct nanoSliderBase: nanoWidget {
	int _dragging = 0;
	bool _stopped = false;
	virtual float getPos() const = 0;
	virtual float setPos( float p, bool stopToInitial=false ) = 0;
	nanoSliderBase( float x, float y, float w, const std::string& title )
	:nanoWidget(x, y, w, 0, title ) {}
	
	virtual float knobRadius() const {
		return contentRect()._h*NANO_SLIDER_KNOB_RADIUS_RATIO;
	}
	virtual nanoRect sliderRect() const {
		nanoRect cr = contentRect();
		float kr = knobRadius();
		return nanoRect( cr._x+cr._w-global().sliderWidth+kr, cr._y+cr._h/2-global().sliderHeight,global().sliderWidth-kr*2, global().sliderHeight*2 );
	}
	virtual float toX(float p) const { auto sr = sliderRect(); return sr._x+p*sr._w; }
	virtual float knobX() const { return toX( getPos() ); }
	virtual float knobY() const {
		nanoRect cr = contentRect();
		return cr._y+cr._h/2;
	}
	virtual void renderKnob(NVGcontext* vg) const {
		drawKnob(vg,knobX(),knobY(),knobRadius());
	}
	virtual void renderSliderBase(NVGcontext* vg, const nanoRect& r) const {
		drawDownBox(vg, r.resizeHorz(r._w+global().sliderHeight*2 ) );
	}
	virtual void renderTicksUnder(NVGcontext* vg, const nanoRect& r) const{}
	virtual void renderTicksOver(NVGcontext* vg, const nanoRect& r) const{}
	virtual void renderSlider(NVGcontext* vg, const nanoRect& r) const {
		renderTicksUnder(vg,r);
		renderSliderBase(vg, r);
		renderTicksOver(vg,r);
	}
	virtual bool render(NVGcontext* vg) override  {
		updateSize(vg);
		drawLabel(vg, contentRect().offsetLeft(global().sliderWidth+labelPt()*NANO_SLIDER_LABEL_OFFSET_PT_RATIO) );
		renderSlider(vg, sliderRect());
		renderKnob(vg);
		return false;
	}
	virtual void updateSize(NVGcontext* vg) override {
		if( _wAutosize || _rect._w<=0 )	_rect._w = labelSize(vg)._w+padding()*2+margin()*2+global().sliderWidth+labelPt()*0.5f;
		if( _hAutosize || _rect._h<=0 )	_rect._h = labelPt()*NANO_WIDGET_HEIGHT_PT_RATIO;
	}
	virtual bool press(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
	   _pressedOn = _rect.inside(x,y);
	   if( _pressedOn && _enabled ) {
		   float kx = knobX(), ky = knobY(), kr = knobRadius();
		   nanoRect sliderR = sliderRect();
		   if( (x-kx)*(x-kx)+(y-ky)*(y-ky)< kr*kr ) {
			   _dragging = true;
			   return true;
		   }
		   else if( sliderR.resizeVert(global().sliderHeight*4).inside( x, y ) ) {
			   setPos( (x-sliderR._x)/(sliderR._w) );
			   return true;
		   }
		   _stopped = false;
	   }
	   return false;
	}
	virtual bool move(float x, float y, NANO_UI_MOD mods ) override {
		nanoRect sliderR = sliderRect();
		if( _dragging ) setPos( (x-sliderR._x)/(sliderR._w), mods&MOD_SHIFT_ );
		return _dragging;
	}
	virtual bool release(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		_pressedOn = false;
		_dragging = false;
		_stopped = false;
		return false;
	}

};










template<typename T> struct nanoSlider: nanoSliderBase {
	T* _value = nullptr;
	T _stopValue;
	float _stepStop = 0.f;
	T _minVal = 0, _maxVal = 1;
	nanoSlider<T>( float x, float y, float w, const std::string& title,
				T minVal, T maxVal, T& value )
	:nanoSliderBase(x, y, w, title ),
	_value(&value), _minVal(float(minVal)), _maxVal(float(maxVal)), _stopValue(value) {}
	virtual float getPos() const override {
		if( _value ) return float(*_value-_minVal)/float(_maxVal-_minVal);
		else return 0.f;
	}
	virtual float getPos(T x) const {
		return float(x-_minVal)/float(_maxVal-_minVal);
	}
	virtual void renderTicksOver(NVGcontext* vg, const nanoRect& r) const override {
		nanoSliderBase::renderTicksOver(vg, r);
	}
	virtual void renderTicksUnder(NVGcontext* vg, const nanoRect& r) const override {
		drawTicks(vg, r, knobY()-(knobRadius()), (knobRadius()*2), 1, labelColor(), {getPos(_stopValue)});
	}
	virtual float setPos( float p, bool stopToInitial=false ) override {
		if( _stopped ) return getPos();
		if( p<0 ) p=0;
		if( p>1 ) p=1;
		T v = p*(_maxVal-_minVal)+_minVal;
		if( _value && stopToInitial && ( (v<_stopValue && *_value>_stopValue ) || (v>_stopValue && *_value<_stopValue ) )) {
			_stopped = true;
			v = _stopValue;
		}
		if( _value ) *_value = v;
		return getPos();
	}
};
typedef nanoSlider<float> nanoSliderF;
typedef nanoSlider<int> nanoSliderI;

template<> inline float nanoSlider<int>::setPos( float p, bool stopToInitial ) {
	if( _stopped ) return getPos();
	p = std::min(1.f,std::max(0.f,p));
	int v = (int)round( p*(_maxVal-_minVal)+_minVal );
	if( _value && stopToInitial && ( (v<=_stopValue && *_value>_stopValue ) || (v>=_stopValue && *_value<_stopValue ) )) {
		_stopped = true;
		v = _stopValue;
	}
	if( _value ) *_value = v;
	return getPos();
}

template<> inline void nanoSlider<int>::renderTicksUnder(NVGcontext* vg, const nanoRect& r) const {
/*	if( (_maxVal-_minVal)*2<r._w ) {
		std::vector<float> xx;
		for( int i=_minVal+1; i<_maxVal; i++ ) if(i!=_stopValue) xx.push_back(getPos(i));
		drawTicks(vg, r, knobY()-(r._h/4), r._h/2, 1, labelColor(), xx);
	}*/
	drawTicks(vg, r, knobY()-(knobRadius()), (knobRadius()*2), 1, labelColor(), {getPos(_stopValue)});
}
template<> inline void nanoSlider<int>::renderTicksOver(NVGcontext* vg, const nanoRect& r) const {
	if( (_maxVal-_minVal)*2<r._w ) {
		std::vector<float> xx;
		for( int i=_minVal+1; i<_maxVal; i++ ) if(i!=_stopValue) xx.push_back(getPos(i));
		drawTicks(vg, r, knobY()-(r._h/8), r._h/4, .7f, labelColor(), xx);
	}
	//drawTicks(vg, r, knobY()-(knobRadius()), (knobRadius()*2), 1, labelColor(), {getPos(_stopValue)});
}

template<> inline float nanoSlider<float>::setPos( float p, bool stopToInitial ) {
	if( _stopped ) return getPos();
	p = std::min(1.f,std::max(0.f,p));
	float v;
	if( _stepStop>0.0 )	{
		v= ((int)round( p*(_maxVal-_minVal)/_stepStop ))*_stepStop+_minVal;
	}
	else{
		v= p*(_maxVal-_minVal)+_minVal;
		if( _value && stopToInitial && ( (v<_stopValue && *_value>_stopValue ) || (v>_stopValue && *_value<_stopValue ) )) {
			_stopped = true;
			v = _stopValue;
		}
	}
	if( _value ) *_value = v;
	return getPos();
}










template <typename E>
constexpr typename std::underlying_type<E>::type to_underlying(E e) noexcept {
	return static_cast<typename std::underlying_type<E>::type>(e);
}
template<typename E>
struct nanoOptions : nanoExpandable {
	nanoOptions( float x, float y, float w, const std::string& title,
				const std::vector<std::string>& opts, E& value )
	:_options(opts), _value(&value), nanoExpandable(x,y,w,0,title){}
	
	virtual void updateSize(NVGcontext* vg) override {
		if( _wAutosize || _rect._w<=0 )	_rect._w = labelSize(vg)._w+padding()*2+margin()*2+global().sliderWidth;
		if( _hAutosize || _rect._h<=0 )	_rect._h = labelPt()*NANO_WIDGET_HEIGHT_PT_RATIO;
	}
	virtual nanoRect optionRect() const { return contentRect().resizeRight(global().sliderWidth); }
	virtual nanoRect expandedRect() const override { return optionRect().resizeUp(_options.size()*contentRect()._h); }
	virtual nanoRect itemRect(int i) const { return expandedRect().offsetUp(i*contentRect()._h).resizeUp(contentRect()._h); }
	virtual void drawOptionLabel(NVGcontext* vg, const nanoRect& r, const std::string& txt, bool emph=false ) const {
		drawText(vg, r.resizeHorz(r._w-labelPt()*0.5f-(emph?5:0)), labelPt()*.8f, labelFont(), NVG_ALIGN_LEFT|NVG_ALIGN_MIDDLE, txt, labelColor());
	}
	virtual int onItem(float x, float y) const {
		for(size_t i=0; i< _options.size(); i++) if( itemRect((int)i).inside(x, y) ) return int(i);
		return -1;
	}
	virtual bool render(NVGcontext* vg) override {
		updateSize(vg);
		drawLabel(vg, contentRect().offsetLeft(global().sliderWidth+labelPt()*NANO_SLIDER_LABEL_OFFSET_PT_RATIO) );
		if( !expanded() ) {
			nanoRect optR = optionRect();
			drawDownBox(vg, optR);
			drawOptionLabel(vg,optR,_options[to_underlying(*_value)]);
		}
		else {
			nanoRect expR = expandedRect();
			nanoRect shdR = expR.expand(NANO_GROUP_SHADOW_WIDTH);
			nvgSave(vg);
			nvgScissor(vg, shdR._x, shdR._y, shdR._w, shdR._h);
			drawOptionBack(vg,expR,global().groupColor);
			for(size_t i=0; i< _options.size(); i++) drawOptionLabel(vg, itemRect((int)i), _options[i], i==_onItem);
			nvgRestore(vg);
		}
		return false;
	}
	virtual bool press(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		if( expanded() ) {
			_pressedOn = expandedRect().inside(x,y);
			if( _pressedOn ) {
				int item = onItem(x,y);
				if( item>0 || item<_options.size() ) {
					*_value = E(item);
					shrink();
				}
			}
			else _pressedOn= false;
			return _pressedOn;
		}
		else {
			_pressedOn = optionRect().inside(x,y);
			if( _pressedOn ) {
				expand();
				_onItem = to_underlying(*_value);
			}
			return _pressedOn;
		}
		return false;
	}
	virtual bool release(float x, float y, NANO_UI_BUTTON button, NANO_UI_MOD mods) override {
		_pressedOn = false;
		if( _shrinkOnRelease ) shrink();
		_shrinkOnRelease = false;
		return false;
	}
	virtual bool move		(float x, float y, NANO_UI_MOD mods ) override {
		if( _pressedOn && expanded() ) {
			int i = onItem(x,y);
			if( i>=0 && i<_options.size() && _onItem!=i ) {
				*_value = E(_onItem = i);
				_shrinkOnRelease = true;
			}
		}
		return _pressedOn && expanded();
	}
	int _onItem = -1;
	bool _shrinkOnRelease=false;
	E*	_value = nullptr;
	std::vector<std::string> _options;
};










//!@ Utility function to register default fonts for NVGcontext
inline void nvgRegisterDefaultFonts( NVGcontext* vg, const std::string& path ) {
	std::string ppp = path+((path.length()>0)?"/":"");
	int fontNormal = nvgCreateFont(vg, "system", (ppp+"Roboto-Regular.ttf").c_str());
	int fontBold =   nvgCreateFont(vg, "system-bold", (ppp+"Roboto-Bold.ttf").c_str());
	int fontEmoji =  nvgCreateFont(vg, "emoji", (ppp+"NotoEmoji-Regular.ttf").c_str());
					 nvgCreateFont(vg, "icons", (ppp+"entypo.ttf").c_str());
	
	nvgAddFallbackFontId(vg, fontNormal, fontEmoji);
	nvgAddFallbackFontId(vg, fontBold, fontEmoji);
}
inline void nvgShadowedText( NVGcontext* vg, float x, float y, const char* str,
							const NVGcolor& textColor, const NVGcolor& shadowColor ) {
	const std::vector<float> dx = { 0, 0, 0,-1, 1 };
	const std::vector<float> dy = { 0,-1, 1, 0, 0 };
	nvgFontBlur(vg, 1);
	nvgFillColor(vg, shadowColor);
	for( int i=0; i<(int)dx.size(); i++ )
		nvgText(vg, x+dx[i],y+dy[i],str,NULL);
	nvgFontBlur(vg, 0);
	nvgFillColor(vg, textColor);
	nvgText(vg, x  ,y  ,str,NULL);
}
inline nanoRect measureText( NVGcontext* vg, float pt, const char* fnt, const std::string& txt) {
	nanoRect ret;
	nvgFontSize(vg, pt);
	nvgFontFace(vg, fnt);
	nvgTextAlign(vg, NVG_ALIGN_TOP|NVG_ALIGN_LEFT);
	nvgTextBounds(vg, 0, 0, txt.c_str(), NULL, (float*)&ret);
	return ret;
}
inline void drawKnob(NVGcontext* vg,float kx, float ky, float kr) {
	// Knob Shadow
	NVGpaint bg = nvgRadialGradient(vg, kx, ky+1, kr-3,kr+3, NANO_UI_SHADOW_COLOR, NANO_UI_SHADOW_OUT_COLOR);
	nvgBeginPath(vg);
	nvgRect(vg, kx-kr-5, ky-kr-5,kr*2+5+5,kr*2+5+5+3);
	nvgCircle(vg, kx,ky, kr);
	nvgPathWinding(vg, NVG_HOLE);
	nvgFillPaint(vg, bg);
	nvgFill(vg);

	// Knob
	NVGpaint knob = nvgLinearGradient(vg, kx,ky-kr,kx,ky+kr,
									  NANO_SLIDER_KNOB_TOP_COLOR, NANO_SLIDER_KNOB_BOTTOM_COLOR );
	nvgBeginPath(vg);
	nvgCircle(vg, kx, ky, kr-1);
	nvgFillColor(vg, NANO_SLIDER_KNOB_BACKGROUND_COLOR);
	nvgFill(vg);
	nvgFillPaint(vg, knob);
	nvgFill(vg);
	
	nvgBeginPath(vg);
	nvgCircle(vg, kx, ky, kr-0.5f);
	nvgStrokeColor(vg, NANO_SLIDER_KNOB_BOUND_COLOR);
	nvgStroke(vg);
}

inline void drawCheck(NVGcontext* vg, const nanoRect& r, const NVGcolor& labelColor) {
	float x1 = r._x+r._w*0.2f, x2 = r._x+r._w*0.5f, x3 = r._x+r._w*0.8f;
	float y1 = r._y+r._h*0.35f, y2 = r._y+r._h*0.7f, y3 = r._y+r._h*0.2f;
	nvgBeginPath(vg);
	nvgMoveTo(vg,x1,y1);
	nvgLineTo(vg,x2,y2);
	nvgLineTo(vg,x3,y3);
	nvgStrokeWidth(vg,r._w*0.15f);
	nvgStrokeColor(vg,labelColor);
	nvgStroke(vg);
}


					  
inline void drawDownBox(NVGcontext* vg, const nanoRect& r ) {
	NVGpaint bg = nvgBoxGradient(vg, r._x+1,r._y+1,r._w-2,r._h-2, 3,5,
								 NANO_UI_DOWNBOX_INNER_COLOR, NANO_UI_DOWNBOX_OUTER_COLOR);
	nvgBeginPath(vg);
	nvgRoundedRect(vg, r._x,r._y, r._w,r._h, std::min(4.f,r._h/2) );
	nvgFillPaint(vg, bg);
	nvgFill(vg);
}
inline void drawText(NVGcontext* vg, const nanoRect& r, float pt, const char* fnt, int align, const std::string& txt, const NVGcolor& color ) {
	nvgSave(vg);
	nvgIntersectScissor(vg, r._x, r._y, r._w, r._h);
	nvgFontSize(vg, pt);
	nvgFontFace(vg, fnt);
	nvgTextAlign(vg,align);
	nvgShadowedText(vg, r._x,r._y+r._h/2,txt.c_str(), color);
	nvgRestore(vg);
}
inline void drawHandledPanRight(NVGcontext* vg,const nanoRect& r, const nanoRect& hr, float cr0=7) {
	float cr1 = (r._x)>0?cr0:0;
	float cr2 = std::min( cr0, (hr._y-r._y)/2);
	float cr3 = std::min( cr0, (r._h-(hr._y+hr._h)));
	float cr4 = hr._w/3.f;
	float x1 = 0, x2 = r._w+hr._w, x3 = r._w;
	float y1 = 0, y2 = hr._y, y3 = hr._y+hr._h, y4 = r._h;
	const float kp = 1-NVG_KAPPA90;

	nvgMoveTo(vg,x1,y4-cr1);
	if( cr1>0 )	nvgBezierTo(vg, x1,y4-cr1*kp, x1+cr1*kp, y4, x1+cr1, y4);
	nvgLineTo(vg,x3-cr0,y4);	// bottom
	if( cr3>0 )	nvgBezierTo(vg, x3-cr3*kp,y4, x3, y4-cr3*kp, x3, y4-cr3);

	nvgLineTo(vg,x3,y3);
	nvgLineTo(vg,x2-cr4,y3);	// to bottom right pan
	if( cr4>0 )	nvgBezierTo(vg, x2-cr4*kp,y3, x2, y3-cr4*kp, x2, y3-cr4);
	nvgLineTo(vg,x2,y2+cr0);	// to top right pan
	if( cr4>0 )	nvgBezierTo(vg, x2,y2+cr4*kp, x2-cr4*kp, y2, x2-cr4, y2);
	nvgLineTo(vg,x3,y2);	// to top left pan

	nvgLineTo(vg,x3,y1+cr2);	// to top
	if( cr2>0 )	nvgBezierTo(vg, x3,y1+cr2*kp, x3-cr2*kp, y1, x3-cr2, y1);
	nvgLineTo(vg,x1+cr1,y1);
	if( cr1>1 )	nvgBezierTo(vg, x1+cr1*kp,y1, x1, y1+cr1*kp, x1, y1+cr1);
	
	nvgClosePath(vg);
}


inline void drawGroupBack(NVGcontext* vg,const nanoRect& r, const NVGcolor& color, const NVGcolor& btnColor,
						  bool arrowDir, const nanoRect& hr ) {
	if( r._h<1 ) return;
	NVGpaint shadowPaint;
	nvgSave(vg);
	nvgTranslate(vg, r._x, r._y);

	nvgBeginPath(vg);
	drawHandledPanRight( vg, r, hr, NANO_GROUP_CORNER_RADIUS);
	nvgFillColor(vg, color);
	nvgFill(vg);

	shadowPaint = nvgBoxGradient(vg,0, 0, r._w, r._h,
								 NANO_GROUP_CORNER_RADIUS, NANO_GROUP_SHADOW_WIDTH,
								 NANO_UI_SHADOW_COLOR, NANO_UI_SHADOW_OUT_COLOR);
	nvgBeginPath(vg);
	nvgRect(vg, -NANO_GROUP_SHADOW_WIDTH, -NANO_GROUP_SHADOW_WIDTH,
			hr._x+hr._w+NANO_GROUP_SHADOW_WIDTH*2, r._h+NANO_GROUP_SHADOW_WIDTH*2);
	drawHandledPanRight( vg, r, hr, NANO_GROUP_CORNER_RADIUS);

	nvgPathWinding(vg, NVG_HOLE);
	nvgFillPaint(vg, shadowPaint);
	nvgFill(vg);

	shadowPaint = nvgBoxGradient(vg, hr._x, hr._y, hr._w, hr._h,
								 NANO_GROUP_CORNER_RADIUS, NANO_GROUP_SHADOW_WIDTH,
								 NANO_UI_SHADOW_COLOR, NANO_UI_SHADOW_OUT_COLOR);
	nvgBeginPath(vg);
	nvgRect(vg, -NANO_GROUP_SHADOW_WIDTH, -NANO_GROUP_SHADOW_WIDTH,
			r._w+hr._w+NANO_GROUP_SHADOW_WIDTH*2,r._h+NANO_GROUP_SHADOW_WIDTH*2);
	drawHandledPanRight( vg, r, hr, NANO_GROUP_CORNER_RADIUS);

	nvgPathWinding(vg, NVG_HOLE);
	nvgFillPaint(vg, shadowPaint);
	nvgFill(vg);

	float cpx = hr._x+hr._w/2;
	float cpy = hr._y+hr._h/2;
	float btnSz = hr._w/2.f;
	nvgBeginPath(vg);
	if( arrowDir ) {
		nvgMoveTo(vg,cpx-btnSz*0.4f,cpy-btnSz*0.6f);
		nvgLineTo(vg,cpx-btnSz*0.4f,cpy+btnSz*0.6f);
		nvgLineTo(vg,cpx+btnSz*0.6f,cpy);
	}
	else {
		nvgMoveTo(vg,cpx+btnSz*0.4f,cpy-btnSz*0.6f);
		nvgLineTo(vg,cpx-btnSz*0.6f,cpy);
		nvgLineTo(vg,cpx+btnSz*0.4f,cpy+btnSz*0.6f);
	}
	nvgClosePath(vg);
	nvgFillColor(vg, btnColor);
	nvgFill(vg);
	
	nvgRestore(vg);
}

inline void drawOptionBack(NVGcontext* vg,const nanoRect& r, const NVGcolor& color) {
	if( r._h<1 ) return;
	NVGpaint shadowPaint;
	nvgSave(vg);
	nvgTranslate(vg, r._x, r._y);
	
	nvgBeginPath(vg);
	nvgRoundedRect(vg, 0, 0, r._w, r._h, NANO_GROUP_CORNER_RADIUS);
	nvgFillColor(vg, color);
	nvgFill(vg);
	
	shadowPaint = nvgBoxGradient(vg,0, 0, r._w, r._h,
								 NANO_GROUP_CORNER_RADIUS, NANO_GROUP_SHADOW_WIDTH,
								 NANO_UI_SHADOW_COLOR, NANO_UI_SHADOW_OUT_COLOR);
	nvgBeginPath(vg);
	nvgRect(vg, -NANO_GROUP_SHADOW_WIDTH, -NANO_GROUP_SHADOW_WIDTH,
			r._w+NANO_GROUP_SHADOW_WIDTH*2, r._h+NANO_GROUP_SHADOW_WIDTH*2);
	nvgRoundedRect(vg, 0, 0, r._w, r._h, NANO_GROUP_CORNER_RADIUS);
	nvgPathWinding(vg, NVG_HOLE);
	nvgFillPaint(vg, shadowPaint);
	nvgFill(vg);
	nvgRestore(vg);
}

inline void drawTicks(NVGcontext* vg,const nanoRect& r, float baseY, float height, float w, const NVGcolor& c, const std::vector<float>& poss) {
	float y0 = baseY;
	float y1 = y0+height;
	nvgBeginPath(vg);
	for( auto p: poss ) {
		float xx = p*(r._w)+r._x;
		nvgMoveTo(vg,xx,y0);
		nvgLineTo(vg,xx,y1 );
	}
	nvgStrokeColor(vg, c);
	nvgStrokeWidth(vg, w);
	nvgStroke(vg);
}


#endif /* nanoUI_h */
