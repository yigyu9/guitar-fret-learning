//
//  Toolbar.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Toolbar_h
#define JGL2_Toolbar_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Aligner.hpp>

namespace JGL2 {

const float DIM_TOOLBAR_ITEM_HEIGHT = 24;
const float DIM_TOOLBAR_VERT_MARGIN = 4;
const float DIM_TOOLBAR_HORZ_MARGIN = 8;
const float DIM_TOOLBAR_ITEM_GAP = 4;
const float DIM_TOOLBAR_HEIGHT = DIM_TOOLBAR_ITEM_HEIGHT+DIM_TOOLBAR_VERT_MARGIN*2;
const float DIM_MENUBAR_HEIGHT = 20;
const float DIM_TOOLBAR_ITEM_MIN_WIDTH = 48;

struct Toolbar : public Aligner {

	Toolbar(float xx,float yy,float ww,float hh,const str_t& label="Toolbar" );
	Toolbar(float xx,float yy,float ww,const str_t& label="Toolbar" );
	Toolbar(const pos_t& pos,const sz2_t& sz,const str_t& label="Toolbar" );
	Toolbar(const pos_t& pos,float ww,const str_t& label="Toolbar" );

protected:

	virtual void drawBox(NVGcontext* vg,const rct_t& r) override;
};

inline Toolbar::Toolbar(float xx,float yy,float ww,float hh,const str_t& label )
: Aligner( xx, yy, ww, hh, label ){
	padding( 7, 6 );
	spacing( 6 );
	alignment( align_t::LEFT );
}

inline Toolbar::Toolbar(float xx,float yy,float ww,const str_t& label )
: Aligner( xx, yy, ww, _size_toolbar_height(), label ){
	padding( 7, 6 );
	spacing( 6 );
	alignment( align_t::LEFT );
}

inline Toolbar::Toolbar(const pos_t& pos,const sz2_t& sz,const str_t& label )
: Aligner( pos, sz, label ){
	padding( 7, 6 );
	spacing( 6 );
	alignment( align_t::LEFT );
}

inline Toolbar::Toolbar(const pos_t& pos,float ww,const str_t& label )
: Aligner( pos,sz2_t(ww, _size_toolbar_height()), label ){
	padding( 7, 6 );
	spacing( 6 );
	alignment( align_t::LEFT );
}

inline void Toolbar::drawBox(NVGcontext* vg,const rct_t& r) {
	_draw_toolbar_box(vg, r, shadeState() );
	Aligner::drawBox(vg,r);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Toolbar_h */
