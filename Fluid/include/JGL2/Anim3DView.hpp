//
//  Anim3DView.hpp
//  nanoVGTest
//
//  Created by Hyun Joon Shin on 2/8/24.
//

#ifndef JGL_Anim3DView_hpp
#define JGL_Anim3DView_hpp

#include "View3D.hpp"
#include <JGL2/_Timeline.hpp>

namespace JGL2 {

template<typename T=JR::PBRRenderer, typename=enable_if_renderer<T>>
struct Anim3DView : public Render3DView<T>, public _Timeline {
	Anim3DView(float x, float y, float w, float h, const std::string& name="")
	: Render3DView<T>(x,y,w,h,name){}

	bool handle(event_t e) override {
		bool ret = handleTimeline(e);
		if( ret ) return true;
		return Render3DView<T>::handle(e);
	}
	virtual void drawGL() override {
		timeProgress();
		Render3DView<T>::drawGL();
	}
	virtual void drawContents(NVGcontext* vg, const rct_t&r, align_t a ) override {
		drawTimeline(vg,r,a);
	}
};

}

#endif /* JGL_Anim3DView_hpp */
