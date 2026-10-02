//
//  _Timeline.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/7/24.
//

#ifndef _Timeline_h
#define _Timeline_h

#include <JGL2/_JGL.hpp>
#include <functional>

namespace JGL2 {

template<typename T> struct range_t {
	T start;
	T end;
	inline long length() const { return end - start; }
	inline long span() const { return end - 1 - start; }
};

typedef std::function<void(long f)>			FrameCallback_t;
typedef std::function<void(long s,long e)>	RangeCallback_t;
typedef std::function<void()>				AnimEventCallback_t ;


struct _Timeline {
	inline _Timeline() {}
	virtual inline	bool			handleTimeline(event_t e);
	virtual inline	void			drawTimeline(NVGcontext* vg, const rct_t&r, align_t a);

	virtual inline	bool			timeProgress();
	virtual inline	bool			frameForward()				{ stopPlayback(); return moveCurrentFrame( 1 ); }
	virtual inline	bool			frameBackward()				{ stopPlayback(); return moveCurrentFrame(-1 ); }
	virtual inline	bool			skipForward(float dt)		{ return moveCurrentFrame( dt*_fps ); }
	virtual inline	bool			skipBackward(float dt)		{ return moveCurrentFrame(-dt*_fps ); }

	virtual inline	void			startPlayback( bool autoRewind=true );
	virtual inline	void			stopPlayback();
	virtual inline	void			togglePlayback( bool autoRewind=true );

	virtual	inline	void			range(long s,long e);
	virtual	inline	void			range(long e)						{ range(0,e); }
	virtual	inline	void			numFrames(long e)					{ range(0,e); }
	template<typename T>
	inline	void					range(const range_t<T>& r)			{ range( static_cast<long>(r.start), static_cast<long>(r.end)); }
	virtual inline	void			fps(float f)						{ _fps=f; }
	virtual inline	float			fps() const							{ return _fps; }
			
	virtual inline	range_t<long>	range() const						{ return _range; }
	virtual inline	long			currentFrame() const				{ return _curFrame; }
	virtual inline	void			currentFrame(long f)				{ setCurrentFrame( f ); }
			
	virtual inline	bool			playing() const						{ return _playing; }
	virtual inline	bool			atTheEnd() const					{ return _atTheEnd; }
	virtual inline	bool			atTheStart() const					{ return _atTheStart; }
			
	virtual inline	void			startCB	(AnimEventCallback_t cb)	{ _startPlaybackCB = cb; }
	virtual inline	void			stopCB	(AnimEventCallback_t cb)	{ _stopPlaybackCB = cb; }
	virtual inline	void			rewindCB(AnimEventCallback_t cb)	{ _rewindCB = cb; }
	virtual inline	void			endCB	(AnimEventCallback_t cb)	{ _endFrameReachCB = cb; }
	virtual inline	void			frameCB	(FrameCallback_t cb)		{ _frameCB = cb; }
	virtual inline	void			rangeCB	(RangeCallback_t cb)		{ _rangeCB = cb; }

	virtual inline	void			resetStartPlaybackCB()				{ _startPlaybackCB = defTimelineCB; }
	virtual inline	void			resetStopPlaybackCB()				{ _stopPlaybackCB = defTimelineCB; }
	virtual inline	void			resetRewindCB()						{ _rewindCB = defTimelineCB; }
	virtual inline	void			resetEndFrameReachCB()				{ _endFrameReachCB = defTimelineCB; }
	virtual inline	void			resetFrameCB()						{ _frameCB = defFrameCB; }
	virtual inline	void			resetRangeCB()						{ _rangeCB = defRangeCB; }


	virtual inline	bool			animationAvailable() const			{ return _range.span()>0; }
	
	
	virtual inline	void			timeFrameColor( const color_t& v )	{ _timeFrameColor=v; }
	virtual inline	void			timeBarColor( const color_t& v )	{ _timeBarColor=v; }
	virtual inline	void			timeBarHgColor( const color_t& v )	{ _timeBarHgColor=v; }
	virtual inline	void			buttonColor( const color_t& v )		{ _buttonColor=v; }
	virtual inline	void			handleColor( const color_t& v )		{ _handleColor=v; }
	virtual inline	void			handleHgColor( const color_t& v )	{ _handleHgColor=v; }
	virtual inline	void			timelineHeight( float v ) 			{ _timelineHeight=v; }
	virtual inline	void			handleWidth( float v )				{ _handleWidth=v; }
	virtual inline	void			handleHgWidth( float v ) 			{ _handleHgWidth=v; }
	virtual inline	void			handleHeight( float v )				{ _handleHeight=v; }
	virtual inline	void			timeBarHeight( float v )			{ _timeBarHeight=v; }
	virtual inline	void			timeBarHgHeight( float v )			{ _timeBarHgHeight=v; }
	virtual inline	void			buttonWidth( float v )				{ _buttonWidth=v; }
	virtual inline	void			timeBarMargin( float v )			{ _timeBarMargin=v; }
	virtual inline	void			uiMaxAlpha( float v )				{ _uiMaxAlpha=v; }
	virtual inline	void			uiDisappearDelay( float v )			{ _uiDisappearDelay=v; }
	virtual inline	void			uiAppearAlphaDelta( float v )		{ _uiAppearAlphaDelta=v; }
	virtual inline	void			uiDisappearAlphaDelta( float v )	{ _uiDisappearAlphaDelta=v; }
	virtual inline	void			uiOnlyOnUI( bool v )				{ _uiOnlyOnUI=v; }
	
	
	virtual inline	const color_t&	timeFrameColor() const				{ return _timeFrameColor; }
	virtual inline	const color_t&	timeBarColor() const				{ return _timeBarColor; }
	virtual inline	const color_t&	timeBarHgColor() const				{ return _timeBarHgColor; }
	virtual inline	const color_t&	buttonColor() const					{ return _buttonColor; }
	virtual inline	const color_t&	handleColor() const					{ return _handleColor; }
	virtual inline	const color_t&	handleHgColor() const				{ return _handleHgColor; }
	virtual inline	float			timelineHeight() const				{ return _timelineHeight; }
	virtual inline	float			handleWidth() const					{ return _handleWidth; }
	virtual inline	float			handleHgWidth() const				{ return _handleHgWidth; }
	virtual inline	float			handleHeight() const				{ return _handleHeight; }
	virtual inline	float			timeBarHeight() const				{ return _timeBarHeight; }
	virtual inline	float			timeBarHgHeight() const				{ return _timeBarHgHeight; }
	virtual inline	float			buttonWidth() const					{ return _buttonWidth; }
	virtual inline	float			timeBarMargin() const				{ return _timeBarMargin;  }
	virtual inline	float			uiMaxAlpha() const					{ return _uiMaxAlpha; }
	virtual inline	float			uiDisappearDelay() const			{ return _uiDisappearDelay; }
	virtual inline	float			uiAppearAlphaDelta() const			{ return _uiAppearAlphaDelta; }
	virtual inline	float			uiDisappearAlphaDelta() const		{ return _uiDisappearAlphaDelta; }
	virtual inline	bool			uiOnlyOnUI() const					{ return _uiOnlyOnUI; }
	
	virtual inline	color_t&		timeFrameColor()		{ return _timeFrameColor; }
	virtual inline	color_t&		timeBarColor()			{ return _timeBarColor; }
	virtual inline	color_t&		timeBarHgColor()		{ return _timeBarHgColor; }
	virtual inline	color_t&		buttonColor()			{ return _buttonColor; }
	virtual inline	color_t&		handleColor()			{ return _handleColor; }
	virtual inline	color_t&		handleHgColor()			{ return _handleHgColor; }
	virtual inline	float&			timelineHeight()		{ return _timelineHeight; }
	virtual inline	float&			handleWidth()			{ return _handleWidth; }
	virtual inline	float&			handleHgWidth()			{ return _handleHgWidth; }
	virtual inline	float&			handleHeight()			{ return _handleHeight; }
	virtual inline	float&			timeBarHeight()			{ return _timeBarHeight; }
	virtual inline	float&			timeBarHgHeight()		{ return _timeBarHgHeight; }
	virtual inline	float&			buttonWidth()			{ return _buttonWidth; }
	virtual inline	float&			timeBarMargin()			{ return _timeBarMargin;  }
	virtual inline	float&			uiMaxAlpha()			{ return _uiMaxAlpha; }
	virtual inline	float&			uiDisappearDelay()		{ return _uiDisappearDelay; }
	virtual inline	float&			uiAppearAlphaDelta()	{ return _uiAppearAlphaDelta; }
	virtual inline	float&			uiDisappearAlphaDelta()	{ return _uiDisappearAlphaDelta; }
	virtual inline	bool&			uiOnlyOnUI()			{ return _uiOnlyOnUI; }
	
protected:
	const AnimEventCallback_t	defTimelineCB = [](){};
	const FrameCallback_t		defFrameCB = [](long){};
	const RangeCallback_t		defRangeCB = [](long,long){};
	
	AnimEventCallback_t			_startPlaybackCB	= defTimelineCB;
	AnimEventCallback_t			_stopPlaybackCB		= defTimelineCB;
	AnimEventCallback_t			_rewindCB			= defTimelineCB;
	AnimEventCallback_t			_endFrameReachCB	= defTimelineCB;
	FrameCallback_t				_frameCB			= defFrameCB;
	RangeCallback_t				_rangeCB			= defRangeCB;
	
	
	range_t<long>		_range					= {0,0};
	float				_fps					= 30;
	long				_curFrame				= 0;
	std::vector<long>	_keyFrames;
	long				_sessionStartFrame		= 0;
	float				_sessionPlaybackTime	= 0;
	bool				_playing				= false;
	bool				_atTheEnd				= false;
	bool				_atTheStart				= false;
	bool				_initialized			= false;

	// Style Parameters
	
	color_t				_timeFrameColor			= {.11,.11,.11};
	color_t				_timeBarColor			= {.25,.25,.25};
	color_t				_timeBarHgColor			= {.3,.3,.3};
	color_t				_buttonColor			= {.6,.6,.6};
	color_t				_handleColor			= {.82,.82,.82};
	color_t				_handleHgColor			= {1,1,1};

	float				_timelineHeight			= 40;
	float				_handleWidth			= 3;
	float				_handleHgWidth			= 5;
	float				_handleHeight			= 20;
	float				_timeBarHeight			= 4;
	float				_timeBarHgHeight		= 6;
	float				_buttonWidth			= 38;
	float				_timeBarMargin			= 12;
	float				_uiMaxAlpha				= 0.8f;
	float				_uiDisappearDelay		= 2.5f;
	float				_uiAppearAlphaDelta		= 0.1f;
	float				_uiDisappearAlphaDelta	= 0.05f;
	bool				_uiOnlyOnUI				= false;

	// UI parameter
	rct_t				_prevButtonRect;
	rct_t				_nextButtonRect;
	rct_t				_playButtonRect;
	rct_t				_timeFrameRect;
	rct_t				_timeBarRect;
	rct_t				_timeHandleRect;
	pos_t				_timeHandlePos;

	bool				_cursorOnHandle			= false;
	float				_cursorHandleOffset		= 0;
	float				_uiAlpha				= 0;
	bool				_uiAppearing			= false;
	float				_uiAppearTime;
	bool				_cursorOnUI				= false;
	bool				_cursorOnBar			= false;

	virtual void		frameChanged();
	virtual bool		setCurrentFrame( long frame, bool resetPlayback=false );
	virtual bool		moveCurrentFrame( float delta ) { return setCurrentFrame( _curFrame + long( round(delta)) ); }

	virtual long		cursorToFrame( float x );
	virtual void		showUI();
};

inline void _Timeline::range(long s,long e) {
	_range.start = s; _range.end = e;
	_curFrame = s;
	_rangeCB(s,e);
	_rewindCB();
	frameChanged();
}

inline void	_Timeline::startPlayback( bool autoRewind ) {
	if( !animationAvailable() ) return;
	if( _playing ) return;
	if( _atTheEnd ) {
		if( autoRewind ) {
			_rewindCB();
			setCurrentFrame(0);
		}
		else return;
	}
	_sessionPlaybackTime = float(glfwGetTime());
	_sessionStartFrame = _curFrame;
	_playing = true;
	_startPlaybackCB();
}

inline void _Timeline::stopPlayback() {
	if( !_playing ) return;
	_playing = false;
	_stopPlaybackCB();
}

inline void _Timeline::togglePlayback( bool autoRewind ) {
	if( playing() )	stopPlayback();
	else			startPlayback( autoRewind );
}

inline bool _Timeline::timeProgress() {
	if( !_initialized ) {
		frameChanged();
		_initialized = true;
		return true;
	}
	if( !playing() ) return false;
	float dt = float(glfwGetTime()) - _sessionPlaybackTime;
	setCurrentFrame(_sessionStartFrame + long( round( dt*_fps )));
	Widget* w = dynamic_cast<Widget*>(this);
	if( w ) w->animate();
	if( _atTheEnd && _playing ) {
		stopPlayback();
		return false;
	}
	return true;
}

inline void _Timeline::frameChanged() {
	_atTheStart = false;
	_atTheEnd = false;
	if( _curFrame >= _range.end-1 ) {
		_atTheEnd = true;
		_endFrameReachCB();
	}
	if( _curFrame <= _range.start ) _atTheStart = true;

	_frameCB( _curFrame );
	Widget* w = dynamic_cast<Widget*>(this);
	if( w ) w->redraw();
}

inline bool _Timeline::setCurrentFrame( long frame, bool resetPlayback ) {
	long oldFrame = _curFrame;
	_curFrame = std::max( _range.start, std::min( frame, _range.end-1 ) );
	
	if( resetPlayback && _playing ) {
		_sessionPlaybackTime = float(glfwGetTime());
		_sessionStartFrame = _curFrame;
	}

	if( oldFrame != _curFrame ) {
		frameChanged();
		return true;
	}
	return false;
}





inline bool _Timeline::handleTimeline(event_t e) {
	if( e == event_t::KEYDOWN ) {
		switch( eventKey() ) {
			case ' ':
				togglePlayback();
				return true;
			case ',':
				frameBackward();
				return true;
			case '.':
				frameForward();
				return true;
			case '0':
			case GLFW_KEY_HOME:
				_rewindCB();
				setCurrentFrame(0, true);
				return true;
			case GLFW_KEY_END:
				setCurrentFrame( _range.end-1, true );
				return true;
		}
	}
	else if( e == event_t::REPEAT ) {
		switch( eventKey() ) {
			case ',':
				frameBackward();
				return true;
			case '.':
				frameForward();
				return true;
		}
	}
	else if( e == event_t::PUSH ) {
		if( !_uiOnlyOnUI ) showUI();
		if( !animationAvailable() ) return false;
		pos_t pt = _JGL::eventPt();
		if( _playButtonRect.in(pt) ) {
			togglePlayback();
			return true;
		}
		if( _prevButtonRect.in(pt)) {
			frameBackward();
			return true;
		}
		if( _nextButtonRect.in(pt)) {
			frameForward();
			return true;
		}
		if( _cursorOnBar ) {
			setCurrentFrame( cursorToFrame( pt.x ), true );
			_cursorOnHandle = true;
			_cursorHandleOffset = 0;
			return true;
		}
		if( _cursorOnHandle ) {
			_cursorHandleOffset = pt.x - _timeHandlePos.x;
			return true;
		}
	}
	else if( e == event_t::DRAG ) {
		if( !_uiOnlyOnUI ) showUI();
		pos_t pt = _JGL::eventPt();
		if( _cursorOnHandle ) {
			setCurrentFrame( cursorToFrame( pt.x - _cursorHandleOffset), true );
			return true;
		}
	}
	else if( e == event_t::MOVE ) {
		if( !_uiOnlyOnUI || _cursorOnUI ) showUI();
		pos_t pt = _JGL::eventPt();
		_cursorOnUI = _timeFrameRect.in(pt);
		_cursorOnBar= _timeBarRect.in(pt);
		_cursorOnHandle = _timeHandleRect.in(pt);
	}
	return false;
}





inline long _Timeline::cursorToFrame( float x ) {
	float ratio = (x-_timeBarRect.x)/_timeBarRect.w;
	return long( round( ratio*_range.span() ) );
}

inline void _Timeline::showUI() {
	if( !_uiAppearing ) {
		Widget* w = dynamic_cast<Widget*>(this);
		if( w ) w->animate();
	}
	_uiAppearing = true;
	_uiAppearTime = float(glfwGetTime());
}

inline void draw_timeline_prev_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);
inline void draw_timeline_next_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);
inline void draw_timeline_play_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);
inline void draw_timeline_pause_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c);



inline void _Timeline::drawTimeline(NVGcontext* vg, const rct_t&r, align_t a){
	if( _uiAlpha>0 ||_uiAppearing ) {
		Widget* w = dynamic_cast<Widget*>(this);
		if( w ) w->animate();
	}
	if( !_uiAppearing ) {
		float cur = float(glfwGetTime());
		if( _cursorOnUI ) _uiAppearTime = cur;
		if( cur > _uiAppearTime+_uiDisappearDelay ) {
			_uiAlpha = std::max( _uiAlpha-_uiDisappearAlphaDelta,0.f );
		}
	}
	else {
		_uiAlpha = std::min( _uiAlpha+_uiAppearAlphaDelta,_uiMaxAlpha );
		if( _uiAlpha > _uiMaxAlpha-0.001f )
			_uiAppearing = false;
	}
	float top = r.bl().y - _timelineHeight;
	NVGcolor buttonColor = toNVGcolor(_buttonColor,animationAvailable()?_uiAlpha:0.2f*_uiAlpha);

	float xx1 = r.x + _timeBarMargin;
	float xx2 = xx1 + _buttonWidth;
	float xx3 = xx2 + _buttonWidth;
	float xx4 = xx3 + _buttonWidth + _timeBarMargin;
	float xx5 = r.x + r.w - _timeBarMargin;
	
	float handleWidth = (_cursorOnBar||_cursorOnHandle)?_handleHgWidth:_handleWidth;
	float barHeight = (_cursorOnBar||_cursorOnHandle)?_timeBarHgHeight:_timeBarHeight;
	
	_prevButtonRect = rct_t(xx1,top,_buttonWidth,_timelineHeight);
	_playButtonRect = rct_t(xx2,top,_buttonWidth,_timelineHeight);
	_nextButtonRect = rct_t(xx3,top,_buttonWidth,_timelineHeight);
	_timeFrameRect  = rct_t(xx4,top,xx5-xx4,_timelineHeight);
	_timeBarRect    = rct_t(_timeFrameRect.x,top+_timelineHeight/2-barHeight/2, _timeFrameRect.w, barHeight);
	if( animationAvailable() ) {
		_timeHandlePos.x = _timeBarRect.x + _timeFrameRect.w/(_range.span())*_curFrame;
		_timeHandlePos.y = _timeBarRect.y+_timeBarRect.h/2;
		_timeHandleRect = rct_t( _timeHandlePos+pos_t(-handleWidth/2,-_timelineHeight*0.25f), handleWidth, _timelineHeight*0.5f );
	}
	else {
		_timeHandlePos = {0,0};
		_timeHandleRect = rct_t(_timeHandlePos,0,0);
	}

	nvgBeginPath(vg);
	nvgRect(vg, r.x, top, r.w, _timelineHeight);
	nvgFillColor(vg, toNVGcolor(_timeFrameColor, _uiAlpha));
	nvgFill(vg);

	draw_timeline_prev_button(vg, _prevButtonRect, buttonColor);
	if( !playing() )
		draw_timeline_play_button(vg,_playButtonRect, buttonColor);
	else
		draw_timeline_pause_button(vg,_playButtonRect, buttonColor);
	draw_timeline_next_button(vg,_nextButtonRect, buttonColor);

	nvgBeginPath(vg);
	nvgRoundedRect(vg, _timeBarRect.x, _timeBarRect.y, _timeBarRect.w, _timeBarRect.h, _timeBarRect.h/2);
	nvgFillColor(vg, toNVGcolor(_cursorOnBar?_timeBarHgColor:_timeBarColor, _uiAlpha));
	nvgFill(vg);
	
	if( animationAvailable() ) {
		nvgBeginPath(vg);
		nvgRoundedRect(vg, _timeHandleRect.x, _timeHandleRect.y, _timeHandleRect.w, _timeHandleRect.h, _handleWidth/2);
		nvgFillColor(vg, toNVGcolor(_cursorOnBar?_handleHgColor:_handleColor,_uiAlpha));
		nvgFill(vg);
	}
}





inline void draw_timeline_triangle_button( NVGcontext* vg, const rct_t&r, const NVGcolor& c, const pos_t& p1, const pos_t& p2, const pos_t& p3 ) {
	nvgBeginPath(vg);
	nvgMoveTo(vg,r.x+r.w*p1.x,r.y+r.h*p1.y);
	nvgLineTo(vg,r.x+r.w*p2.x,r.y+r.h*p2.y);
	nvgLineTo(vg,r.x+r.w*p3.x,r.y+r.h*p3.y);
	nvgClosePath(vg);
	nvgFillColor(vg,c);
	nvgFill(vg);
}


inline void draw_timeline_prev_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_timeline_triangle_button(vg,r,c,{0.5f,0.3f},{0.2f,0.5f},{0.5f,0.7f});
	draw_timeline_triangle_button(vg,r,c,{0.8f,0.3f},{0.5f,0.5f},{0.8f,0.7f});
}
inline void draw_timeline_next_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_timeline_triangle_button(vg,r,c,{0.2f,0.3f},{0.5f,0.5f},{0.2f,0.7f});
	draw_timeline_triangle_button(vg,r,c,{0.5f,0.3f},{0.8f,0.5f},{0.5f,0.7f});
}

inline void draw_timeline_play_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	draw_timeline_triangle_button(vg,r,c,{0.3f,0.25f},{0.8f,0.5f},{0.3f,0.75f});
}

inline void draw_timeline_pause_button(NVGcontext* vg, const rct_t&r, const NVGcolor& c) {
	float x1 = r.x+r.w*0.3f,	x2 = r.x+r.w*0.45f;
	float x3 = r.x+r.w*0.55f,	x4 = r.x+r.w*0.7f;
	float y1 = r.y+r.h*0.25f,	y2 = r.y+r.h*0.75f;
	nvgBeginPath(vg);
	nvgRoundedRect(vg, x1, y1, x2-x1, y2-y1, (x2-x1)/2);
	nvgRoundedRect(vg, x3, y1, x4-x3, y2-y1, (x4-x3)/2);
	nvgFillColor(vg,c);
	nvgFill(vg);
}

} // namespace JGL2

#endif /* _Timeline_h */
