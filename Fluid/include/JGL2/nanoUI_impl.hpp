//
//  nanoUI_impl.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/19/24.
//

#ifndef nanoUI_impl_h
#define nanoUI_impl_h

#ifdef JGL2_Widget_h
inline NANO_UI_BUTTON nanoWidget::toNanoUIButtonJGL2(const JGL2::button_t& b) {
	switch( b ) {
		case JGL2::button_t::LBUTTON:	return BUTTON_LEFT;
		case JGL2::button_t::RBUTTON:	return BUTTON_RIGHT;
		case JGL2::button_t::MBUTTON:	return BUTTON_MIDDLE;
		default:						return BUTTON_NONE;
	}
}
inline NANO_UI_MOD nanoWidget::toNanoUIModsJGL2() {
	NANO_UI_MOD ret = MOD_NONE;
	if( JGL2::eventMods(JGL2::mod_t::CONTROL)) ret=(NANO_UI_MOD)((int)ret|(int)MOD_CTRL);
	if( JGL2::eventMods(JGL2::mod_t::SHIFT  )) ret=(NANO_UI_MOD)((int)ret|(int)MOD_SHIFT_);
	if( JGL2::eventMods(JGL2::mod_t::SUPER  )) ret=(NANO_UI_MOD)((int)ret|(int)MOD_SUPER);
	if( JGL2::eventMods(JGL2::mod_t::ALT    )) ret=(NANO_UI_MOD)((int)ret|(int)MOD_ALT_);
	if( JGL2::eventMods(JGL2::mod_t::LBUTTON)) ret=(NANO_UI_MOD)((int)ret|(int)MOD_LBTN);
	if( JGL2::eventMods(JGL2::mod_t::RBUTTON)) ret=(NANO_UI_MOD)((int)ret|(int)MOD_RBTN);
	return ret;
}
inline bool nanoWidget::nanoUIHandle(const  JGL2::event_t& e, nanoWidget& group ) {
	NANO_UI_BUTTON btn = toNanoUIButtonJGL2(JGL2::_JGL::eventButton());
	global().ui_mods = toNanoUIModsJGL2();
	if( e == JGL2::event_t::PUSH )
		return group.press( JGL2::_JGL::eventX(), JGL2::_JGL::eventY(), btn, global().ui_mods );
	else if( e == JGL2::event_t::RELEASE )
		return group.release( JGL2::_JGL::eventX(), JGL2::_JGL::eventY(), btn, global().ui_mods );
	else if( e == JGL2::event_t::MOVE )
		return group.move( JGL2::_JGL::eventX(), JGL2::_JGL::eventY(), global().ui_mods);
	else if( e == JGL2::event_t::DRAG )
		return group.move( JGL2::_JGL::eventX(), JGL2::_JGL::eventY(), global().ui_mods);
	return false;
}

#elif defined _glfw3_h_

inline bool nanoWidget::nanoUIButton( GLFWwindow* win, int button, int action, int mods, nanoWidget& group ) {
	double mx, my;
	NANO_UI_BUTTON btn;
	NANO_UI_MOD tempMods = MOD_NONE;
	if( button == GLFW_MOUSE_BUTTON_1 ) {
		tempMods = MOD_LBTN;
		btn = BUTTON_LEFT;
	}
	else if( button == GLFW_MOUSE_BUTTON_2 ) {
		tempMods = MOD_RBTN;
		btn = BUTTON_RIGHT;
	}
	else if( button == GLFW_MOUSE_BUTTON_3 ) {
		btn =BUTTON_MIDDLE;
	}
	glfwGetCursorPos( win, &mx, &my );
	if( action == GLFW_PRESS ) {
		_ui_mods = (NANO_UI_MOD)(mods|((_ui_mods&MOD_BTN_MASK)|tempMods));
		return group.press( (float)mx, (float)my, btn, _ui_mods );
	}
	else if( action == GLFW_RELEASE ) {
		_ui_mods = (NANO_UI_MOD)(mods|((_ui_mods&MOD_BTN_MASK)&(~tempMods)));
		return group.release( (float)mx, (float)my, btn, (NANO_UI_MOD)mods );
	}
	return 0;
}
inline bool nanoWidget::nanoUIMove( GLFWwindow* win, double mx, double my, nanoWidget& group ) {
	return group.move( (float)mx, (float)my, _ui_mods);
}
inline void nanoWidget::nanoUIRender( NVGcontext* vg, int width, int height, nanoWidget& group ) {
	nvgBeginFrame(vg, width, height, 1);
	group.render(vg);
	nvgEndFrame(vg);
}
static NVGcontext* nanoUIInit(const std::string& path ) {
#ifdef __GL21__
	NVGcontext* vg = nvgCreateGL2(NVG_ANTIALIAS | NVG_STENCIL_STROKES | NVG_DEBUG);
#else
	NVGcontext* vg = nvgCreateGL3(NVG_ANTIALIAS | NVG_STENCIL_STROKES | NVG_DEBUG);
#endif
	nvgRegisterDefaultFonts( vg, path );
	return vg;
}
#endif

#endif /* nanoUI_impl_h */
