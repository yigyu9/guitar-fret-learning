//
//  Label.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Label_h
#define JGL2_Label_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Widget.hpp>

namespace JGL2 {

struct Label : public Widget {
	Label( float x, float y, float w, float h, const str_t& name="");
	Label( const pos_t& pos, const sz2_t& sz, const str_t& name="");
//	Size minSize() const override;
};

inline Label::Label( float x, float y, float w, float h, const str_t& name )
:Widget(x,y,w,h,name) {
}
inline Label::Label(const pos_t& pos, const sz2_t& sz, const str_t& name )
:Widget(pos,sz,name) {
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Label_h */
