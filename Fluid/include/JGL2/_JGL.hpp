//
//  _JGL.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__JGL_h
#define JGL2__JGL_h

#include <thread>
#include <mutex>
#include <set>

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#ifdef __APPLE__
#define GL_SILENCE_DEPRECATION
#include <opengl/gl3.h>
#endif

#ifdef _MSC_VER
#define WIN32_LEAN_AND_MEAN
#include <Windows.h>
#undef min
#undef max
#define GLEW_STATIC
#include <gl/glew.h>
#pragma comment (lib,"glew32s")
#pragma comment (lib,"opengl32.lib")
#pragma comment (lib,"glfw3.lib")
#endif

#include <JGL2/_MathTypes.hpp>
#include <nanovg/nanovg.h>

#include <GLFW/glfw3.h>
#include <queue>
#include <functional>

namespace JGL2 {

struct Widget;
struct Window;
struct Group;
struct _Popup;
struct _PopupHandler;
enum class mod_t;

enum class event_t {
	NONE			= 0,
	MOVE			= 10,	//!< The mouse pointer moved without any button pressed.
	DRAG			= 11,	//!< The mouse pointer moved with one or more buttons pressed.
	PUSH			= 12,	//!< A mouse button is pressed.
	RELEASE			= 13,	//!< A mouse button is released.
	CANCEL			= 15,
	KEYDOWN			= 20,
	KEYUP			= 21,
	CHAR			= 22,
	REPEAT			= 23,
	ENTER			= 30,
	LEAVE			= 31,
	SCROLL			= 40,
	ZOOM			= 41,
	TARGETTED		= 50,
	UNTARGETTED		= 51,
	PASTE			= 60,
	COPY			= 61,
	CUT				= 62,
	UNDO			= 64,
	REDO			= 65,
	DND				= 90,
	POPUP_DISMISSED	= 100,
	DISMISS_POPUP	= 101,
	WINDOW_FOCUSED	= 110,
	WINDOW_UNFOCUSED= 111,
};

enum class button_t {
	NONE				= 0,
	LBUTTON 			= (1<<0),
	RBUTTON 			= (1<<1),
	MBUTTON 			= (1<<2),
	XBUTTON 			= (1<<3),
	YBUTTON 			= (1<<4),
};
inline button_t	operator | (const button_t& a,const button_t& b) { return button_t(int(a)|int(b)); }
inline button_t	operator & (const button_t& a,const button_t& b) { return button_t(int(a)&int(b)); }
inline button_t	operator ~ (const button_t& a) { return button_t(~int(a)); }
inline bool		operator ! (const button_t& a) { return int(a)==0; }


enum class cursor_t {
	ARROW			= GLFW_ARROW_CURSOR,
	IBEAM			= GLFW_IBEAM_CURSOR,
	CROSSHAIR		= GLFW_CROSSHAIR_CURSOR,
	HAND			= GLFW_HAND_CURSOR,
	HRESIZE			= GLFW_HRESIZE_CURSOR,
	VRESIZE			= GLFW_VRESIZE_CURSOR,
};
	
enum class mod_t {
	NONE				= 0,
	LSHIFT				= (1<<0),
	RSHIFT				= (1<<1),
	SHIFT				= (LSHIFT|RSHIFT),
	LCONTROL			= (1<<2),
	RCONTROL			= (1<<3),
	CONTROL				= (LCONTROL|RCONTROL),
	LALT				= (1<<4),
	RALT				= (1<<5),
	ALT					= (LALT|RALT),
	LSUPER				= (1<<6),
	RSUPER				= (1<<7),
	SUPER				= (LSUPER|RSUPER),
	LBUTTON				= (1<<8),
	RBUTTON				= (1<<9),
	MBUTTON				= (1<<10),
	XBUTTON				= (1<<11),
	YBUTTON				= (1<<12),
};
inline mod_t	operator | (const mod_t& a,const mod_t& b) { return mod_t(int(a)|int(b)); }
inline mod_t	operator & (const mod_t& a,const mod_t& b) { return mod_t(int(a)&int(b)); }
inline mod_t	operator ~ (const mod_t& a) { return mod_t(~int(a)); }
inline bool		operator ! (const mod_t& a) { return int(a)==0; }

enum class pop_reason_t{
	NONE				=0,
	OTHER_START			=(1<<5),
	ESC_PRESSED			=(1<<3),
	WINDOW_UNFOCUSED	=(1<<4),

	CLICK_OUTSIDE		=(1<<0),
//	RELEASE_INSIDE		=(1<<1),
	POPUP_ACTION		=(1<<2),

	OTHER_DISMISS		=(1<<6),
	CHILD_START			=(1<<7),
	CHILD_ACTION		=(1<<8),
	CHILD_CANCEL		=(1<<9),

	TYPE_CASCADE_MENU	=CLICK_OUTSIDE
						|POPUP_ACTION
						|OTHER_START
						|CHILD_ACTION
						|WINDOW_UNFOCUSED,
	TYPE_DIALOG			=POPUP_ACTION|ESC_PRESSED,
	ALL					=(1<<10)-1,
};

enum class label_pos_t {
	NONE			= 0,
	LEFT			= 1,
	RIGHT			= 2,
	BOTTOM			= 3,
	TOP				= 4,
};

typedef unsigned int key_t;
typedef int idx_t;

struct _JGL {
protected:
	static _JGL& instance() {
		static _JGL instance;
		return instance;
	}
	static _JGL& get() {
		static std::once_flag flag;
		std::call_once(flag, [] { instance(); });
		return instance();
	}

	struct _EventQueueItem {
		Widget* target = nullptr;
		event_t	event  = event_t::NONE;
		pop_reason_t reason = pop_reason_t::NONE;
		_Popup*	popup  = nullptr;
		_PopupHandler* win = nullptr;
		_EventQueueItem(): target(nullptr), event( event_t::NONE ) {};
		_EventQueueItem( Widget* t, event_t e): target(t), event(e) {};
	};
	
	struct _RunOnUIThreadItem {
		std::function<void(void*ud)> func;
		void* ud = nullptr;
		_RunOnUIThreadItem(std::function<void(void*ud)> fun, void* userData=nullptr) : func(fun), ud(userData){}
		void run() { func(ud); }
	};

	using run_item_queue_t	= std::queue<_RunOnUIThreadItem>;
	using event_queue_t		= std::queue<_EventQueueItem>;


	// Window management variables + focussed window
	window_list_t		_windows;
	size_t 				_focusedWindow = 0;
	
	bool				_pressForFocus = false;
	button_t 			_pressedButtons = button_t::NONE;
	mod_t  				_modState = mod_t::NONE;
	run_item_queue_t	_runOnUIThreadQueue;

	
	// Adding group
	group_list_t		_currentAddingGroup;

	// Event context related function
	Widget*				_currentEventContext = nullptr;
	Widget* 			_currentUnderWidget = nullptr;
	Widget* 			_currentTargetWidget = nullptr;

	Window*				_currentDrawWindow = nullptr;
	Window* 			_currentEventWindow = nullptr;

	pos_t				_mousePt = pos_t(0,0);
	pos_t				_scrollDelta = pos_t(0,0);
	float				_zoomFactor = 0;
	button_t			_eventButton = button_t::NONE;
	key_t				_eventKey = 0;
	char32_t			_eventCodePoint = 0;
	str_t				_eventPasteString = "";
	slst_t				_eventDropedStrings;
	event_queue_t		_eventQueue;

	pos_t				_mouseLButtonPressedPt = pos_t(0,0);
	pos_t				_mouseRButtonPressedPt = pos_t(0,0);
	pos_t				_mouseMButtonPressedPt = pos_t(0,0);
	pos_t				_mouseXButtonPressedPt = pos_t(0,0);
	pos_t				_mouseYButtonPressedPt = pos_t(0,0);

	Widget* 			_mouseLButtonPressedWidget = nullptr;
	Widget* 			_mouseRButtonPressedWidget = nullptr;
	Widget* 			_mouseMButtonPressedWidget = nullptr;
	Widget* 			_mouseXButtonPressedWidget = nullptr;
	Widget* 			_mouseYButtonPressedWidget = nullptr;

	std::function<void(const std::filesystem::path&)> _openDocumentCB=[](const std::filesystem::path&){};
	
	
	
	
	
	
	void					__pushAddingGroup(Group*);
	void					__clearAddingGroup();
	void					__popAddingGroup();
	void					__popAddingGroupUntil( Group* );
	Group*					__getCurrentAddingGroup();
	void					__addToCurrentGroup( Widget* );

	const Widget*			__eventContext();
	void					__clearEventContext();
	
	bool					__dispatchEvent( Widget* w, event_t event );
	bool					__sendEvent( Widget* w, event_t event );

	float					__eventX();
	float					__eventY();
	pos_t					__eventPt();
	float					__eventScrollX();
	float					__eventScrollY();
	pos_t					__eventScroll();
	float					__eventZoom();
	slst_t const& 			__eventDND();
	float					__eventWindowX();
	float					__eventWindowY();
	pos_t					__eventWindowPt();
	bool					__eventMods( mod_t mod );
	key_t					__eventKey();
	button_t				__eventButton();
	char32_t				__eventCodePoint();
	const Window*			__eventWindow();
	NVGcontext*				__eventWindowContext();
	const str_t&			__eventPasteString();
	void					__eventCopyString( const str_t& );
	bool					__startPopup( Widget* w, Widget* parent, const pos_t& p, pop_reason_t r=pop_reason_t::ALL );
	void					__dismissPopup( _PopupHandler* win, _Popup* p, pop_reason_t reason );
	void					__dismissPopups( _PopupHandler* win, pop_reason_t reason );
	void					__dismissPopup( Widget* w, pop_reason_t reason );
	void					__run();
	void					__setCurrentDrawWindow( Window* win );
	const Window*			__currentDrawWindow();
	NVGcontext*				__getCurrentNVGContext();
	bool					__getCurrentDrawWindowFocused();
	float					__getCurrentDrawWindowPxRatio();
	float					__getCurrentDrawWindowUIRatio();
	void					__drawAsChild( NVGcontext* vg, Widget* w );
	void					__setCursor( cursor_t cursor );
	void					__runOnUIThread( std::function<void(void*ud)> func, void* ud=nullptr );
	void					__propagateLeaveEnter( Widget* w, const pos_t& oldPt, const pos_t& newPt );
	void					__registerWindow( Window* win );
	void					__registerWindowCallbacks( Window* win );
	GLFWwindow* 			__getShaderableContext();
	Window*					__eventWindow_();
	idx_t					__searchWindow( GLFWwindow* window );
	void					__mousePositionCallback( GLFWwindow* window, double x, double y);
	void					__mouseButtonCallback( GLFWwindow* window, int button, int action, int mods );
	void					__keyCallback( GLFWwindow* window, int key, int scan, int action, int mods );
	void					__charCallback( GLFWwindow* window, unsigned int codepoint);
	void					__resizeCallback( GLFWwindow* window, int w, int h );
	void					__fbResizeCallback( GLFWwindow* window, int w, int h );
	void					__windowFocusCallback( GLFWwindow* window, int );
	void					__scrollCallback( GLFWwindow* window,  double, double );
	void					__zoomCallback( GLFWwindow* window,  double );
	void					__dragAndDropCallback( GLFWwindow* win, int n, const char*[] );
	void					__contentsScaleCallback( GLFWwindow* win, float, float );
	void					__eventContext( Widget* g );
	void					__handleDismissPopupEvent(const _EventQueueItem& item );
	void					__setOpenDoumentCB(std::function<void(const std::filesystem::path& path)>);

public:
	
	//* Adding group management
	static void				pushAddingGroup(Group* g) { get().__pushAddingGroup(g); }
	static void				clearAddingGroup() { get().__clearAddingGroup(); }
	static void				popAddingGroup() { get().__popAddingGroup(); }
	static void				popAddingGroupUntil( Group* g) { get().__popAddingGroupUntil(g); }
	static Group*			getCurrentAddingGroup() { return get().__getCurrentAddingGroup(); }
	static void				addToCurrentGroup( Widget* w) { get().__addToCurrentGroup(w); }

	//* Event context (for which Widget the event is being dispatched.)
	static const Widget*	eventContext() { return get().__eventContext(); }
	static void				clearEventContext() { get().__clearEventContext(); }
	
	//* Event dispatch function
	static bool				dispatchEvent( Widget* w, event_t event ) { return get().__dispatchEvent(w, event); }
	static bool				sendEvent( Widget* w, event_t event ) { return get().__sendEvent(w,event); }

	//* Event data retrival functions
	static float			eventX() { return get().__eventX(); }
	static float			eventY() { return get().__eventY(); }
	static pos_t			eventPt() { return get().__eventPt(); }
	static float			eventScrollX() { return get().__eventScrollX(); }
	static float			eventScrollY() { return get().__eventScrollY(); }
	static pos_t			eventScroll() { return get().__eventScroll(); }
	static float			eventZoom() { return get().__eventZoom(); }
	static slst_t const&	eventDND() { return get().__eventDND(); }
	static float			eventWindowX() { return get().__eventWindowX(); }
	static float			eventWindowY() { return get().__eventWindowY(); }
	static pos_t			eventWindowPt() { return get().__eventWindowPt(); }
	static bool				eventMods( mod_t mod ) { return get().__eventMods(mod); }
	static key_t			eventKey() { return get().__eventKey(); }
	static button_t			eventButton() { return get().__eventButton(); }
	static char32_t			eventCodePoint() { return get().__eventCodePoint(); }
	static const Window*	eventWindow() { return get().__eventWindow(); }
	static NVGcontext*		eventWindowContext() { return get().__eventWindowContext(); }
	static const str_t&		eventPasteString() { return get().__eventPasteString(); }
	static void				eventCopyString( const str_t& s) { return get().__eventCopyString(s); }


	//* Popup management
	static bool				startPopup( Widget* w, Widget* parent, const pos_t& p, pop_reason_t r=pop_reason_t::ALL ) { return get().__startPopup(w,parent,p,r); }
	static void				dismissPopup( _PopupHandler* win, _Popup* p, pop_reason_t reason ) { get().__dismissPopup(win,p,reason); }
	static void				dismissPopups( _PopupHandler* win, pop_reason_t reason ) { get().__dismissPopups(win,reason); }
		// Widget leven request..
	static void				dismissPopup(Widget* w, pop_reason_t reason) { get().__dismissPopup(w,reason); }

	//* Run
	static void				run() { get().__run(); }
	
	
	//* Window drawing management
	static void				setCurrentDrawWindow( Window* win ) { get().__setCurrentDrawWindow(win); }
	static const Window*	currentDrawWindow() { return get().__currentDrawWindow(); }
	static NVGcontext*		getCurrentNVGContext() { return get().__getCurrentNVGContext(); }
	static bool				getCurrentDrawWindowFocused() { return get().__getCurrentDrawWindowFocused(); }
	static float			getCurrentDrawWindowPxRatio() { return get().__getCurrentDrawWindowPxRatio(); }
	static float			getCurrentDrawWindowUIRatio() { return get().__getCurrentDrawWindowUIRatio(); }

	//* A function to be called for drawing a child (or member) widget
	static void				drawAsChild( NVGcontext* vg, Widget* w ) { get().__drawAsChild(vg,w); }
	
	//* Window level control functions
	static void				setCursor( cursor_t cursor ) { get().__setCursor(cursor); }
	
	static void				runOnUIThread(std::function<void(void*ud)> func, void* ud=nullptr) { get().__runOnUIThread(func,ud); }
	static void				setOpenDoumentCB(std::function<void(const std::filesystem::path& path)> fn) { get().__setOpenDoumentCB(fn); }
protected:
	

	//* Very special function to dispatch "ENTER/LEAVE" events
	static void				propagateLeaveEnter( Widget* w, const pos_t& oldPt, const pos_t& newPt ) { get().__propagateLeaveEnter(w,oldPt,newPt); }

	
	//* Window management functions
	static void				registerWindow( Window* win ) { get().__registerWindow(win); }
	static void				registerWindowCallbacks( Window* win ) { get().__registerWindowCallbacks(win); }
	static GLFWwindow* 		getShaderableContext() { return get().__getShaderableContext(); }

	
	static Window*			eventWindow_() { return get().__eventWindow_(); }
	static idx_t			searchWindow( GLFWwindow* window ) { return get().__searchWindow(window); }
	static void				mousePositionCallback( GLFWwindow* window, double x, double y) { get().__mousePositionCallback(window,x,y); }
	static void				mouseButtonCallback( GLFWwindow* window, int button, int action, int mods ) { get().__mouseButtonCallback(window,button,action,mods); }
	static void				keyCallback( GLFWwindow* window, int key, int scan, int action, int mods ) { get().__keyCallback(window,key,scan,action,mods); }
	static void				charCallback( GLFWwindow* window, unsigned int codepoint) { get().__charCallback(window,codepoint); }
	static void				resizeCallback( GLFWwindow* window, int w, int h ) { get().__resizeCallback(window,w,h); }
	static void				fbResizeCallback( GLFWwindow* window, int w, int h ) { get().__fbResizeCallback(window,w,h); }
	static void				windowFocusCallback( GLFWwindow* window, int b) { get().__windowFocusCallback(window,b); }
	static void				scrollCallback( GLFWwindow* window,  double x, double y) { get().__scrollCallback(window,x,y); }
	static void				zoomCallback( GLFWwindow* window,  double z) { get().__zoomCallback(window,z); }
	static void				dragAndDropCallback( GLFWwindow* win, int n, const char* s[] ) { get().__dragAndDropCallback(win,n,s); }
	static void				contentsScaleCallback( GLFWwindow* win, float x, float y) { get().__contentsScaleCallback(win,x,y); }
		
	static void				eventContext( Widget* g ) { get().__eventContext(g); }
			
	static void				handleDismissPopupEvent(const _EventQueueItem& item ) { get().__handleDismissPopupEvent(item); }

	static void				sOpenDocumentCB(const char*);
	
	friend Window;
};

} // namespace JGL2


#include <JGL2/Widget.hpp>
#include <JGL2/Window.hpp>

namespace JGL2 {

inline void _JGL::__pushAddingGroup(Group* g) {
	_currentAddingGroup.push_back(g);
}

inline void _JGL::__clearAddingGroup() {
	_currentAddingGroup.clear();
}

inline void _JGL::__popAddingGroup() {
	_currentAddingGroup.pop_back();
}

inline void _JGL::__popAddingGroupUntil( Group* g ) {
	idx_t groupIdx = -1;
	for( idx_t i=idx_t(_currentAddingGroup.size())-1; i>=0; i-- ) {
		if( g == _currentAddingGroup[i] ) {
			groupIdx = i;
			break;
		}
	}
	if( groupIdx>=0 ) {
		while( groupIdx < _currentAddingGroup.size() )
			_currentAddingGroup.pop_back();
	}
}

inline Group* _JGL::__getCurrentAddingGroup() {
	if( _currentAddingGroup.size()>0 ) return _currentAddingGroup.back();
	return nullptr;
}

inline void _JGL::__addToCurrentGroup( Widget* w ) {
	Group* group = __getCurrentAddingGroup();
	if( group ) group->add( w );
}



///**********************************
///
///  Event Handling
///
///**********************************

// Event context to translate the event relative to the reciever widget


inline void _JGL::__eventContext( Widget* g ) {
	_currentEventContext = g;
}

inline void _JGL::__clearEventContext() {
	_currentEventContext = nullptr;
}

inline const Widget* _JGL::__eventContext() {
	return _currentEventContext;
}

inline NVGcontext* _JGL::__eventWindowContext() {
	return eventWindow_()->nvgContext();
}

inline float _JGL::__eventX() {
	const Widget* context = _currentEventContext;
	return _mousePt.x-(context?context->abs_x():0);
}

inline float _JGL::__eventY() {
	const Widget* context = _currentEventContext;
	return _mousePt.y-(context?context->abs_y():0);
}

inline pos_t _JGL::__eventPt() {
	const Widget* context = _currentEventContext;
	return _mousePt-(context?context->abs_pos():pos_t(0));
}

inline float _JGL::__eventWindowX() {
	return _mousePt.x;
}

inline float _JGL::__eventWindowY() {
	return _mousePt.y;
}

inline pos_t _JGL::__eventWindowPt() {
	return _mousePt;
}

inline float _JGL::__eventScrollX() {
	return -_scrollDelta.x;
}

inline float _JGL::__eventScrollY() {
	return -_scrollDelta.y;
}

inline pos_t _JGL::__eventScroll() {
	return -_scrollDelta;
}

inline bool _JGL::__eventMods( mod_t mod ) {
	return contains(_modState, mod);
}

inline key_t _JGL::__eventKey() {
	return _eventKey;
}

inline char32_t _JGL::__eventCodePoint() {
	return _eventCodePoint;
}

inline float _JGL::__eventZoom() {
	return _zoomFactor;
}

inline button_t _JGL::__eventButton() {
	return _eventButton;
}

inline const str_t& _JGL::__eventPasteString() {
	return _eventPasteString;
}

inline slst_t const& _JGL::__eventDND() {
	return _eventDropedStrings;
}

inline void _JGL::__eventCopyString(const str_t& str) {
	_eventPasteString = str;
	glfwSetClipboardString(eventWindow()->nativeWindow(), str.c_str());
}

inline void _JGL::__setOpenDoumentCB(std::function<void (const std::filesystem::path &)> fn) {
	_openDocumentCB = fn;
}

inline void	_JGL::sOpenDocumentCB(const char* s) {
	get()._openDocumentCB(std::filesystem::u8path(s) );
}


// Event distribution and handling

inline const Window* _JGL::__eventWindow() {
	return _currentEventWindow;
}

inline Window* _JGL::__eventWindow_() {
	return _currentEventWindow;
}

inline void _JGL::__setCursor( cursor_t cursor ) {
	if( _currentEventWindow ) {
		GLFWcursor* cursorHandle = nullptr;
		if( cursor!=cursor_t::ARROW )
			cursorHandle = glfwCreateStandardCursor((int)cursor);
		if( _currentEventWindow->_currentCursor )
			glfwDestroyCursor( _currentEventWindow->_currentCursor );
		_currentEventWindow->_currentCursor = cursorHandle;
		
		glfwSetCursor( _currentEventWindow->glfwWindow(), cursorHandle );
	}
}

inline bool _JGL::__sendEvent( Widget* w, event_t event ) {
	_eventQueue.emplace( w, event );
	return true;
}

inline bool _JGL::__dispatchEvent( Widget* w, event_t event ) {
	Window* win = dynamic_cast<Window*>(w);
	if( win && win->hasPopup() ) {
		bool ret = win->popupHandle( event );
		if( event == event_t::KEYDOWN && eventKey() == GLFW_KEY_ESCAPE )
			__dismissPopups(win, pop_reason_t::ESC_PRESSED);
		
		if( ret ) return true;
	}
	if( w && w->active() && !w->hidden() ) {
		_JGL::eventContext( w );
		
		Group* group = dynamic_cast<Group*>(w);
		_Scrollable* scroller = dynamic_cast<_Scrollable*>(w);
		
		if( event == event_t::SCROLL && group ) {
			if( group->propagateEvent( event ) )
				return true;
		}
		if( w->quickUIHandle( event ) ) {
			w->animate();
			return true;
		}
		if( w->handle( event ) )
			return true;
		if( scroller && scroller->scrollHandle(event)) {
			w->damage();
			return true;
		}
		
		if( event != event_t::SCROLL && group ) {
			if( group->propagateEvent( event ) )
				return true;
		}
	}
	return false;
}

inline void _JGL::__propagateLeaveEnter( Widget* w, const pos_t& oldPt, const pos_t& newPt ) {
	if( w->under(oldPt) && !w->under( newPt ) )
		__dispatchEvent( w, event_t::LEAVE );
	else if( !w->under(oldPt) && w->under( newPt ) )
		__dispatchEvent( w, event_t::ENTER );
	Group* g = dynamic_cast<Group*>(w);
	if( g ) {
		g->forAllChild([&](auto c){
			__propagateLeaveEnter( c, oldPt, newPt );
		});
	}
}


inline idx_t _JGL::__searchWindow( GLFWwindow* window ) {
	for( idx_t i=0; i<_windows.size(); i++ ) {
		if( _windows[i] && _windows[i]->glfwWindow() == window ) return i;
	}
	return -1;
}

inline void _JGL::__mousePositionCallback( GLFWwindow* window, double x, double y) {
	idx_t win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];

		_pressForFocus = false;
		pos_t oldPt = _mousePt;
		_mousePt = pos_t( float(x), float(y) )/_currentEventWindow->uiRatio();

		_currentUnderWidget = _windows[win]->underMouse();
		
		std::set<Widget*> oldUnderWidgets;
		if( eventMods(mod_t::LBUTTON ) )
			oldUnderWidgets.insert( _mouseLButtonPressedWidget );
		if( eventMods(mod_t::RBUTTON ) )
			oldUnderWidgets.insert( _mouseRButtonPressedWidget );
		if( eventMods(mod_t::MBUTTON ) )
			oldUnderWidgets.insert( _mouseRButtonPressedWidget );
		if( eventMods(mod_t::XBUTTON ) )
			oldUnderWidgets.insert( _mouseRButtonPressedWidget );
		if( eventMods(mod_t::YBUTTON ) )
			oldUnderWidgets.insert( _mouseRButtonPressedWidget );
		if( !(_modState&(mod_t::LBUTTON|mod_t::RBUTTON|mod_t::MBUTTON|mod_t::XBUTTON|mod_t::YBUTTON ) ))
			__dispatchEvent( _windows[win], event_t::MOVE );
		else {
			__dispatchEvent( _windows[win], event_t::DRAG );
			for( auto w: oldUnderWidgets )
				__dispatchEvent( w, event_t::DRAG );
		}
		__propagateLeaveEnter( _windows[win], oldPt, _mousePt );
	}
}
		
inline void _JGL::__mouseButtonCallback( GLFWwindow* window, int button, int action, int mods ) {
	idx_t win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		if( _pressForFocus ) {
			if( action == GLFW_RELEASE ) _pressForFocus = false;
			return;
		}

		Widget* oldWidget = nullptr;
		switch( button ) {
			case GLFW_MOUSE_BUTTON_1	:
				_eventButton = button_t::LBUTTON;
				if( action == GLFW_PRESS ) {
					_mouseLButtonPressedPt=eventPt();
					_mouseLButtonPressedWidget=_windows[win]->underWidget( eventWindowPt() );
					_modState= _modState | mod_t::LBUTTON;
				}
				else {
					_modState = _modState&~mod_t::LBUTTON;
					oldWidget=_mouseLButtonPressedWidget;
				}
				break;
			case GLFW_MOUSE_BUTTON_2	:
				_eventButton = button_t::RBUTTON;
				if( action == GLFW_PRESS ) {
					_mouseRButtonPressedPt=eventPt();
					_mouseRButtonPressedWidget=_windows[win]->underWidget( eventWindowPt() );
					_modState = _modState|mod_t::RBUTTON;
				}
				else {
					_modState =_modState&~mod_t::RBUTTON;
					oldWidget=_mouseRButtonPressedWidget;
				} break;
			case GLFW_MOUSE_BUTTON_3	:
				_eventButton = button_t::MBUTTON;
				if( action == GLFW_PRESS ) {
					_mouseMButtonPressedPt=eventPt();
					_mouseMButtonPressedWidget=_windows[win]->underWidget( eventWindowPt() );
					_modState =_modState|mod_t::MBUTTON;
				}
				else {
					_modState =_modState&~mod_t::MBUTTON;
					oldWidget=_mouseMButtonPressedWidget;
				} break;
			case GLFW_MOUSE_BUTTON_4	:
				_eventButton = button_t::XBUTTON;
				if( action == GLFW_PRESS ) {
					_mouseXButtonPressedPt=eventPt();
					_mouseXButtonPressedWidget=_windows[win]->underWidget( eventWindowPt() );
					_modState = _modState|mod_t::XBUTTON;
				}
				else {
					_modState = _modState&~mod_t::XBUTTON;
					oldWidget=_mouseXButtonPressedWidget;
				} break;
			case GLFW_MOUSE_BUTTON_5	:
				_eventButton = button_t::YBUTTON;
				if( action == GLFW_PRESS ) {
					_mouseYButtonPressedPt=eventPt();
					_mouseYButtonPressedWidget=_windows[win]->underWidget( eventWindowPt() );
					_modState = _modState|mod_t::YBUTTON;
				}
				else {
					_modState = _modState&~mod_t::YBUTTON;
					oldWidget=_mouseYButtonPressedWidget;
				} break;
		}
		if( action == GLFW_PRESS ) {
			_pressedButtons = _pressedButtons | _eventButton;
			__dispatchEvent( _windows[win], event_t::PUSH );

			if( _eventButton==button_t::LBUTTON
			   && _currentUnderWidget!=_windows[win]->targetWidget() ) {
				_windows[win]->clearTargetWidget();

				Widget* c = _currentUnderWidget;
				while( c ) {
					_Targettable* t = dynamic_cast<_Targettable*>(c);
					if( t && t->targettable() && c->active() )
						break;
					c = c->parent();
				}
				if( c )
					_windows[win]->targetWidget(c);
			}
		}
		else {
			if( _currentUnderWidget!=oldWidget && _mouseLButtonPressedWidget )
				__dispatchEvent( _mouseLButtonPressedWidget, event_t::CANCEL );
			__dispatchEvent( _windows[win], event_t::RELEASE );
		}
	}
}

inline void _JGL::__resizeCallback( GLFWwindow* window, int w, int h ) {
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();
		_windows[win]->size( sz2_t(float(w),float(h))/_windows[win]->uiRatio() );
		_windows[win]->reform(_windows[win]->nvgContext(),autoscale_t::NONE);
		_windows[win]->render();
	}
}

inline void _JGL::__fbResizeCallback( GLFWwindow* window, int w, int h ) {
}


inline void _JGL::__windowFocusCallback( GLFWwindow* window, int focus ) {
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		if( focus ) {
			__dispatchEvent(_windows[win], event_t::WINDOW_FOCUSED);
			_focusedWindow = win;
		}
		else {
			__dispatchEvent(_windows[win], event_t::WINDOW_UNFOCUSED);
			__dismissPopups(_windows[win], pop_reason_t::WINDOW_UNFOCUSED);
		}
		if( _windows[win]) {
			_pressForFocus = true;
			_windows[win]->isFocused( focus );
			_windows[win]->damage();
			if( focus ) {
				double mouseX, mouseY;
				glfwGetCursorPos( _windows[win]->glfwWindow(), &mouseX, &mouseY );
				_mousePt = pos_t( float(mouseX), float(mouseY) );
			}
		}
	}
}

inline void _JGL::__scrollCallback( GLFWwindow* window,  double dx, double dy ) {
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		_scrollDelta = pos_t( float(dx), float(dy) );
		if( _windows[win] ) {
			__dispatchEvent( _windows[win], event_t::SCROLL );
		}
	}
}

inline void _JGL::__zoomCallback( GLFWwindow* window,  double factor ) {
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		_zoomFactor = float(factor);
		if( _windows[win] ) {
			__dispatchEvent( _windows[win], event_t::ZOOM );
		}
	}
}

inline void _JGL::__charCallback( GLFWwindow* window, unsigned int codePoint) {
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();
		
		_eventCodePoint = codePoint;
		bool dispatched = false;
		if( _windows[win]->targetWidget() )
			dispatched = __dispatchEvent( _windows[win]->targetWidget(), event_t::CHAR );
//		if( !dispatched )
//			__dispatchEvent( _windows[win], event_t_CHAR );
	}
}

inline void _JGL::__keyCallback( GLFWwindow* window, int key, int scan, int action, int mods ) {
	if( action == GLFW_PRESS ) {
		switch( key ) {
			case GLFW_KEY_LEFT_SHIFT	: _modState=_modState|mod_t::LSHIFT		; break;
			case GLFW_KEY_RIGHT_SHIFT	: _modState=_modState|mod_t::RSHIFT		; break;
			case GLFW_KEY_LEFT_ALT		: _modState=_modState|mod_t::LALT		; break;
			case GLFW_KEY_RIGHT_ALT		: _modState=_modState|mod_t::RALT		; break;
			case GLFW_KEY_LEFT_CONTROL	: _modState=_modState|mod_t::LCONTROL	; break;
			case GLFW_KEY_RIGHT_CONTROL	: _modState=_modState|mod_t::RCONTROL	; break;
			case GLFW_KEY_LEFT_SUPER	: _modState=_modState|mod_t::LSUPER		; break;
			case GLFW_KEY_RIGHT_SUPER	: _modState=_modState|mod_t::RSUPER		; break;
		}
	}
	else if( action == GLFW_RELEASE ) {
		switch( key ) {
			case GLFW_KEY_LEFT_SHIFT	: _modState =_modState&(~mod_t::LSHIFT	); break;
			case GLFW_KEY_RIGHT_SHIFT	: _modState =_modState&(~mod_t::RSHIFT	); break;
			case GLFW_KEY_LEFT_ALT		: _modState =_modState&(~mod_t::LALT	); break;
			case GLFW_KEY_RIGHT_ALT		: _modState =_modState&(~mod_t::RALT	); break;
			case GLFW_KEY_LEFT_CONTROL	: _modState =_modState&(~mod_t::LCONTROL); break;
			case GLFW_KEY_RIGHT_CONTROL	: _modState =_modState&(~mod_t::RCONTROL); break;
			case GLFW_KEY_LEFT_SUPER	: _modState =_modState&(~mod_t::LSUPER	); break;
			case GLFW_KEY_RIGHT_SUPER	: _modState =_modState&(~mod_t::RSUPER	); break;
		}
	}
	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		_eventKey = key;
		if( _windows[win] ) {
			if( action == GLFW_PRESS ) {
#ifdef __APPLE__
				if( mods == GLFW_MOD_SUPER ){
#else
				if( mods == GLFW_MOD_CONTROL ){
#endif
					if( key==GLFW_KEY_V ) {
						_eventPasteString = glfwGetClipboardString(_windows[win]->nativeWindow() );
						__dispatchEvent( _windows[win]->targetWidget(), event_t::PASTE );
					}
					else if( key == GLFW_KEY_C )
						__dispatchEvent( _windows[win]->targetWidget(), event_t::COPY );
					else if( key == GLFW_KEY_X )
						__dispatchEvent( _windows[win]->targetWidget(), event_t::CUT );
					else if( key == GLFW_KEY_Z )
						__dispatchEvent( _windows[win]->targetWidget(), event_t::UNDO );
				}
#ifdef __APPLE__
				else if( mods == (GLFW_MOD_SUPER|GLFW_MOD_SHIFT) ){
#else
				else if( mods == (GLFW_MOD_CONTROL|GLFW_MOD_SHIFT) ) {
#endif
					if( key == GLFW_KEY_Z )
						__dispatchEvent( _windows[win]->targetWidget(), event_t::REDO );
				}
			}
			bool dispatched = false;
			event_t ev = event_t::NONE;
			if( action == GLFW_PRESS )			ev = event_t::KEYDOWN;
			else if( action == GLFW_REPEAT )	ev = event_t::REPEAT;
			else 								ev = event_t::KEYUP;
			if( _windows[win]->targetWidget() )
				dispatched = __dispatchEvent( _windows[win]->targetWidget(), ev );
			if( !dispatched /*&& eventKey()==GLFW_KEY_TAB*/ )
				__dispatchEvent( _windows[win], ev );
		}
	}
}

inline void _JGL::__dragAndDropCallback( GLFWwindow* window, int n, const char* str[] ) {
	_eventDropedStrings.clear();
	for( int i=0; i<n; i++ )
		_eventDropedStrings.push_back( str[i] );

	int win = __searchWindow( window );
	if( win>=0 ) {
		_currentEventWindow = _windows[win];
		_windows[win]->dismissTooltip();

		bool dispatched = false;
		if( _currentUnderWidget ) {
			if( _currentUnderWidget->dndCallback() ) {
				dispatched = _currentUnderWidget->doDNDCallback();
			}
			else
				dispatched = __dispatchEvent( _currentUnderWidget, event_t::DND );
		}
		if( !dispatched ) {
			if( _windows[win]->dndCallback() ) {
				_windows[win]->doDNDCallback();
			}
		}
	}
}


inline void _JGL::__contentsScaleCallback(GLFWwindow* window, float sx, float sy ) {
#ifdef _MSC_VER
	int win = __searchWindow( window );
	_windows[win]->uiRatio(std::min(sx,sy), true);
#endif
}


///**********************************
///
///  Window Management
///
///**********************************


inline void _JGL::__registerWindow( Window* win ) {
	_windows.push_back( win );
}

inline void _JGL::__registerWindowCallbacks( Window *win ) {
	GLFWwindow* glfwWindow = win->glfwWindow();
	glfwSetCursorPosCallback		( glfwWindow, _JGL::mousePositionCallback );
	glfwSetWindowSizeCallback		( glfwWindow, _JGL::resizeCallback );
	glfwSetFramebufferSizeCallback	( glfwWindow, _JGL::fbResizeCallback );
	glfwSetKeyCallback				( glfwWindow, _JGL::keyCallback );
	glfwSetCharCallback				( glfwWindow, _JGL::charCallback );
	glfwSetWindowFocusCallback		( glfwWindow, _JGL::windowFocusCallback );
	glfwSetMouseButtonCallback		( glfwWindow, _JGL::mouseButtonCallback );
	glfwSetScrollCallback			( glfwWindow, _JGL::scrollCallback );
#ifdef __glfw3_joony_custom__
	glfwSetZoomCallback				( glfwWindow, _JGL::zoomCallback );
#endif
	glfwSetDropCallback				( glfwWindow, _JGL::dragAndDropCallback );
	glfwSetWindowContentScaleCallback(glfwWindow, _JGL::contentsScaleCallback );
/*
	if(!win->hidden()) {
		if(_windows[_focusedWindow]) {
			dispatchEvent(_windows[_focusedWindow],event_t_WINDOW_UNFOCUSED);
			dismissPopups(_windows[_focusedWindow],REASON_WINDOW_UNFOCUSED);
			_windows[_focusedWindow]->dismissTooltip();
		}

		_focusedWindow = _windows.size()-1;
		dispatchEvent(_windows[_focusedWindow],event_t_WINDOW_FOCUSED);
		_windows[_focusedWindow]->damage();
	}
*/
}

inline GLFWwindow* _JGL::__getShaderableContext() {
	for( auto w: _windows )
		if( w && w->glfwWindow() )
			return w->glfwWindow();
	return nullptr;
}

inline void _JGL::__runOnUIThread(std::function<void(void*ud)> func, void* ud) {
	_runOnUIThreadQueue.push(_RunOnUIThreadItem(func,ud));
}

inline void _JGL::__run() {
	while( true ) {
		while( !_eventQueue.empty() ) {
			_EventQueueItem item = _eventQueue.front();
			_eventQueue.pop();
			if( item.event == event_t::DISMISS_POPUP )
				__handleDismissPopupEvent( item );
			else if( item.target && item.event!=event_t::NONE )
				__dispatchEvent( item.target, item.event );
		}
		while( !_runOnUIThreadQueue.empty() ) {
			_RunOnUIThreadItem item = _runOnUIThreadQueue.front();
			_runOnUIThreadQueue.pop();
			item.run();
		}
		bool openWindowExisted = false;
		bool animating = false;
		for(auto w: _windows) {
			if( w && !w->hidden() && !w->destroyed() ) {
				if( w->shoudClosed() ) {
					w->destory();
				}
				else {
					openWindowExisted = true;
					if( w->changed() ) {
						w->reform(w->nvgContext(),autoscale_t::NONE);
					}
					if( w->popupChanged() ) {
						// TODO: popup reform function need the consideration of window size
						// TODO: and corresponding autoscaling flags setting
						w->popupReform(w->nvgContext(),autoscale_t::ALL);
					}
					if( w->damaged() /*|| w->popupDamaged()*/ ) {
						w->render();
					}
				}
				glFinish();
				if( w->animated() ) {
					w->damage();
					w->clearAnimated();
					animating = true;
				}
			}
		}
		if( !openWindowExisted ) break;
		if( animating )
			glfwPollEvents();
		else
			glfwWaitEventsTimeout(0.1);
		if( _focusedWindow>=0 && _windows[_focusedWindow] ) {
			Window* win = _windows[_focusedWindow];
			win->updateUnderWidget( eventWindowPt(), float(glfwGetTime()) );
		}
	}
	glfwTerminate();
}



//**********************************
//
//   Popup management
//
//

inline void _JGL::__dismissPopups(_PopupHandler* win, pop_reason_t reason ) {
	__sendEvent( nullptr, event_t::DISMISS_POPUP );
	_eventQueue.back().reason = reason;
	_eventQueue.back().win = win;
}

inline void _JGL::__dismissPopup(Widget* w, pop_reason_t reason) {
	__sendEvent( w, event_t::DISMISS_POPUP );
	_eventQueue.back().reason = reason;
}

inline void _JGL::__dismissPopup( _PopupHandler* win, _Popup* p, pop_reason_t reason ) {
	__sendEvent( nullptr, event_t::DISMISS_POPUP );
	_eventQueue.back().win = win;
	_eventQueue.back().reason = reason;
}
		
inline void _JGL::__handleDismissPopupEvent(const _EventQueueItem& item ) {
	if( item.win ) {
		if( item.popup ) {
			item.win->dismissPopup(item.popup, item.reason);
			Window* window = dynamic_cast<Window*>(item.win);
			if( window ) window->dismissTooltip();
		}
		else {
			item.win->dismissPopups( item.reason );
			Window* window = dynamic_cast<Window*>(item.win);
			if( window ) window->dismissTooltip();
		}
	}
	else if( item.target ) {
		for( auto win: _windows ) {
			win->dismissPopup(item.target, item.reason);
			win->dismissTooltip();
		}
	}
}

inline bool _JGL::__startPopup( Widget* w, Widget* parent, const pos_t& p, pop_reason_t r ) {
	if( _currentEventWindow ) {
		for( auto& popup: _currentEventWindow->_popups )
			dismissPopup(_currentEventWindow, &popup, pop_reason_t::OTHER_START);
		Widget* par = parent?parent:_currentEventWindow;
		w->_parent = par;
		w->position( p );
		_currentEventWindow->addPopup(_Popup(w,par,r));
		_currentEventWindow->damage();
		return true;
	}
	return false;
}

inline void _JGL::__drawAsChild( NVGcontext* vg, Widget* w ) {
	nvgSave( vg );
	if( w->parent() ) {
		_Scrollable* scroller = dynamic_cast<_Scrollable*>(w->parent());
		if( scroller )
			nvgTranslate(vg, -scroller->scrollOffset().x, -scroller->scrollOffset().y );
	}
	nvgTranslate( vg, w->x(), w->y() );
//	nvgIntersectScissor( vg, 0, 0, w->w(), w->h() );
	if( w->quickUIDraw(vg) ) w->animate();
	w->draw(vg);
	nvgRestore( vg );
}


// Current Window ..
inline const Window* _JGL::__currentDrawWindow() {
	return _currentDrawWindow;
}

inline void _JGL::__setCurrentDrawWindow( Window* win ) {
	_currentDrawWindow = win;
}
		
inline bool _JGL::__getCurrentDrawWindowFocused() {
	return _currentDrawWindow?_currentDrawWindow->isFocused():false;
}
		
inline float _JGL::__getCurrentDrawWindowPxRatio() {
	return _currentDrawWindow?_currentDrawWindow->pxRatio():1.f;
}
		
inline float _JGL::__getCurrentDrawWindowUIRatio() {
	return _currentDrawWindow?_currentDrawWindow->uiRatio():1.f;
}
				
inline NVGcontext* _JGL::__getCurrentNVGContext() {
	return _currentDrawWindow?_currentDrawWindow->nvgContext():(_windows.size()>0?_windows[0]->nvgContext():nullptr);
}

//* Event data retrival functions
inline float			eventX() { return _JGL::eventX(); }
inline float			eventY() { return _JGL::eventY(); }
inline pos_t			eventPt() { return _JGL::eventPt(); }
inline float			eventScrollX() { return _JGL::eventScrollX(); }
inline float			eventScrollY() { return _JGL::eventScrollY(); }
inline pos_t			eventScroll() { return _JGL::eventScroll(); }
inline float			eventZoom() { return _JGL::eventZoom(); }
inline slst_t const&	eventDND() { return _JGL::eventDND(); }
inline float			eventWindowX() { return _JGL::eventWindowX(); }
inline float			eventWindowY() { return _JGL::eventWindowY(); }
inline pos_t			eventWindowPt() { return _JGL::eventWindowPt(); }
inline bool				eventMods( mod_t mod ) { return _JGL::eventMods(mod); }
inline key_t			eventKey() { return _JGL::eventKey(); }
inline button_t			eventButton() { return _JGL::eventButton(); }
inline char32_t			eventCodePoint() { return _JGL::eventCodePoint(); }
inline const Window*	eventWindow() { return _JGL::eventWindow(); }
inline NVGcontext*		eventWindowContext() { return _JGL::eventWindowContext(); }
inline const str_t&		eventPasteString() { return _JGL::eventPasteString(); }
inline void				eventCopyString( const str_t& s) { return _JGL::eventCopyString(s); }


//* Popup management
//inline bool				startPopup( Widget* w, Widget* parent, const pos_t& p, pop_reason_t r=pop_reason_t::ALL ) { return get().__startPopup(w,parent,p,r); }
//inline void				dismissPopup( _PopupHandler* win, _Popup* p, pop_reason_t reason ) { get().__dismissPopup(win,p,reason); }
//inline void				dismissPopups( _PopupHandler* win, pop_reason_t reason ) { get().__dismissPopups(win,reason); }
	// Widget leven request..
//inline void				dismissPopup(Widget* w, pop_reason_t reason) { get().__dismissPopup(w,reason); }

//* Run
inline void				run() { _JGL::run(); }


//* Window drawing management
//inline const Window*	currentDrawWindow() { return get().__currentDrawWindow(); }
//inline NVGcontext*		getCurrentNVGContext() { return get().__getCurrentNVGContext(); }
//inline bool				getCurrentDrawWindowFocused() { return get().__getCurrentDrawWindowFocused(); }
inline float			getCurrentDrawWindowPxRatio() { return _JGL::getCurrentDrawWindowPxRatio(); }
//inline float			getCurrentDrawWindowUIRatio() { return get().__getCurrentDrawWindowUIRatio(); }

//* Window level control functions
inline void				setCursor( cursor_t cursor ) { _JGL::setCursor(cursor); }

inline void				runOnUIThread(std::function<void(void*ud)> func, void* ud=nullptr) { _JGL::runOnUIThread(func,ud); }
		
} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _JGL_h */
