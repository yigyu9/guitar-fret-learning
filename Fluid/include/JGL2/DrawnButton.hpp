//
//  DrawnButton.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_DrawnButton_hpp
#define JGL2_DrawnButton_hpp

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Button.hpp>

namespace JGL2 {

struct DrawnButton: Button {
	DrawnButton(float x,float y,float w,float h,const str_t& label="") : Button(x,y,w,h,label) { tooltip(label); }
	DrawnButton(const pos_t& pos, const sz2_t& sz,const str_t& label="") : Button(pos,sz,label) { tooltip(label); }
	NVGcolor strokeColor() const { return _color_f_label( shadeState() ); }
};

struct ZoomInBtn: DrawnButton {
	ZoomInBtn(float x,float y,float w,float h,const str_t& label="") : DrawnButton(x,y,w,h,label) {}
	ZoomInBtn(const pos_t& pos, const sz2_t& sz,const str_t& label="") : DrawnButton(pos,sz,label) {}
	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t align) override {
//		Button::drawContents(vg,r,align);
		float s = std::min(r.w, r.h);
		pos_t c = pos_t(r.w/2,r.h/2)+r.tl();
		pos_t cc = {c.x-s*0.05f,c.y-s*0.05f};
		float cr = s*0.2f;
		nvgStrokeWidth(vg, 1.3f);
		nvgStrokeColor(vg,strokeColor());
		nvgBeginPath(vg);
		nvgCircle(vg, cc.x, cc.y, cr);
		nvgMoveTo(vg, cc.x+cr*0.707f,cc.y+cr*0.707f );
		nvgLineTo(vg, cc.x+cr*1.707f,cc.y+cr*1.707f );
		nvgMoveTo(vg, cc.x-cr*0.5f,cc.y );
		nvgLineTo(vg, cc.x+cr*0.5f,cc.y );
		nvgMoveTo(vg, cc.x,cc.y-cr*0.5f );
		nvgLineTo(vg, cc.x,cc.y+cr*0.5f );
		nvgStroke(vg);
	}
};


struct ZoomOutBtn: DrawnButton {
	ZoomOutBtn(float x,float y,float w,float h,const str_t& label="") : DrawnButton(x,y,w,h,label) {}
	ZoomOutBtn(const pos_t& pos, const sz2_t& sz,const str_t& label="") : DrawnButton(pos,sz,label) {}
	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t align) override {
//		Button::drawContents(vg,r,align);
		float s = std::min(r.w, r.h);
		pos_t c = pos_t(r.w/2,r.h/2)+r.tl();
		pos_t cc = {c.x-s*0.05f,c.y-s*0.05f};
		float cr = s*0.2f;
		nvgStrokeWidth(vg, 1.3f);
		nvgStrokeColor(vg,strokeColor());
		nvgBeginPath(vg);
		nvgCircle(vg, cc.x, cc.y, cr);
		nvgMoveTo(vg, cc.x+cr*0.707f,cc.y+cr*0.707f );
		nvgLineTo(vg, cc.x+cr*1.707f,cc.y+cr*1.707f );
		nvgMoveTo(vg, cc.x-cr*0.5f,cc.y );
		nvgLineTo(vg, cc.x+cr*0.5f,cc.y );
		nvgStroke(vg);
	}
};

struct ZoomFitBtn: DrawnButton {
	ZoomFitBtn(float x,float y,float w,float h,const str_t& label="") : DrawnButton(x,y,w,h,label) {}
	ZoomFitBtn(const pos_t& pos, const sz2_t& sz,const str_t& label="") : DrawnButton(pos,sz,label) {}
	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t align) override {
//		Button::drawContents(vg,r,align);
		float s = std::min(r.w, r.h);
		pos_t c = pos_t(r.w/2,r.h/2)+r.tl();
		float rr = s*0.25f;
		nvgStrokeWidth(vg, 1.3f);
		nvgStrokeColor(vg,strokeColor());
		nvgBeginPath(vg);
		nvgRect(vg, c.x-rr, c.y-rr, rr*2, rr*2);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.18f,c.y);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.18f,c.y);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.08f,c.y-s*0.04f);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.08f,c.y-s*0.04f);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.08f,c.y+s*0.04f);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.08f,c.y+s*0.04f);

		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x,        c.y-rr+s*0.18f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x,        c.y+rr-s*0.18f);
		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x-s*0.04f,c.y-rr+s*0.08f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x-s*0.04f,c.y+rr-s*0.08f);
		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x+s*0.04f,c.y-rr+s*0.08f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x+s*0.04f,c.y+rr-s*0.08f);

		nvgStroke(vg);
	}
};


struct ZoomOneToOneBtn: DrawnButton {
	ZoomOneToOneBtn(float x,float y,float w,float h,const str_t& label="") : DrawnButton(x,y,w,h,label) {}
	ZoomOneToOneBtn(const pos_t& pos, const sz2_t& sz,const str_t& label="") : DrawnButton(pos,sz,label) {}
	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t align) override {
//		Button::drawContents(vg,r,align);
		float s = std::min(r.w, r.h);
		pos_t c = pos_t(r.w/2,r.h/2)+r.tl();
		float rr = s*0.25f;
		nvgStrokeWidth(vg, 1.3f);
		nvgStrokeColor(vg,strokeColor());
		nvgBeginPath(vg);
		nvgRect(vg, c.x-rr+s*0.18f, c.y-rr+s*0.18f, (rr-s*0.18f)*2, (rr-s*0.18f)*2);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.18f,c.y);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.18f,c.y);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.08f,c.y-s*0.04f);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.08f,c.y-s*0.04f);
		nvgMoveTo(vg,c.x-rr+1.0f,   c.y);
		nvgLineTo(vg,c.x-rr+s*0.08f,c.y+s*0.04f);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgLineTo(vg,c.x+rr-s*0.08f,c.y+s*0.04f);

		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x,        c.y-rr+s*0.18f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x,        c.y+rr-s*0.18f);
		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x-s*0.04f,c.y-rr+s*0.08f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x-s*0.04f,c.y+rr-s*0.08f);
		nvgMoveTo(vg,c.x,        c.y-rr+1.0f   );
		nvgLineTo(vg,c.x+s*0.04f,c.y-rr+s*0.08f);
		nvgMoveTo(vg,c.x,        c.y+rr-1.0f   );
		nvgLineTo(vg,c.x+s*0.04f,c.y+rr-s*0.08f);
		nvgStroke(vg);
	}
};


struct SaveBtn: DrawnButton {
	SaveBtn(float x,float y,float w,float h,const str_t& label="") : DrawnButton(x,y,w,h,label) {}
	SaveBtn(const pos_t& pos, const sz2_t& sz,const str_t& label="") : DrawnButton(pos,sz,label) {}
	virtual void drawContents(NVGcontext* vg, const rct_t& r, align_t align) override {
//		Button::drawContents(vg,r,align);
		float s = std::min(r.w, r.h);
		pos_t c = pos_t(r.w/2,r.h/2)+r.tl();
		float rr = s*0.25f;
		nvgStrokeWidth(vg, 1.3f);
		nvgStrokeColor(vg,strokeColor());
		nvgBeginPath(vg);
		nvgMoveTo(vg,c.x,        c.y-rr);
		nvgLineTo(vg,c.x,        c.y+rr);
		nvgMoveTo(vg,c.x-rr*.5f, c.y+rr*.5f);
		nvgLineTo(vg,c.x,        c.y+rr);
		nvgLineTo(vg,c.x+rr*.5f, c.y+rr*.5f);
		nvgMoveTo(vg,c.x-rr,     c.y+rr);
		nvgLineTo(vg,c.x+rr,     c.y+rr);
		nvgMoveTo(vg,c.x+rr-1.0f,   c.y);
		nvgStroke(vg);
	}
};

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Check_h */
