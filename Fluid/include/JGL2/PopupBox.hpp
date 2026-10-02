//
//  PopupBox.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_PopupBox_h
#define JGL2_PopupBox_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Group.hpp>

namespace JGL2 {

struct PopupBox : Group {
	PopupBox(float w,float h, const str_t& label="");
	PopupBox(const sz2_t& sz, const str_t& label="");

	static pos_t		popupPos(Widget* popup, Widget* parent);
	// TODO: Resizable popupbox
protected:
	virtual void		drawBox(NVGcontext* vg, const rct_t& r ) override;
	virtual void		drawBoxOver(NVGcontext* vg, const rct_t& r ) override;
};


} // namespace JGL2

namespace JGL2 {

inline PopupBox::PopupBox(float w,float h, const str_t& label)
: Group( 0,0,w,h,label) {
}

inline PopupBox::PopupBox(const sz2_t& sz, const str_t& label)
: Group( pos_t(0,0),sz,label) {
}

inline pos_t PopupBox::popupPos(Widget* popup, Widget* parent) {
	const Window* win = _JGL::eventWindow();
	if( !win ) return pos_t(0);
	const Widget* par = parent?parent:win;
	pos_t dx = par->abs_pos();
	const _Scrollable* scroller = dynamic_cast<const _Scrollable*>(par);
	if( scroller ) dx+=scroller->scrollOffset();
	return pos_t(dx.x+(win->w())/2-popup->w()/2, dx.y );
}

inline void PopupBox::drawBox(NVGcontext* vg, const rct_t& r ) {
	_draw_popupbox_box(vg,r);
	Group::drawBox(vg,r);
}

inline void PopupBox::drawBoxOver(NVGcontext* vg, const rct_t& r ) {
	Group::drawBoxOver(vg,r);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* PopupBox_h */
