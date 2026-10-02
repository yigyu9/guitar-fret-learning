//
//  ButtonGroup.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_ButtonGroup_h
#define JGL2_ButtonGroup_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Aligner.hpp>

namespace JGL2 {

struct ButtonGroup: public Aligner {
	ButtonGroup(float x, float y, float w, float h, const str_t& label="ButtonGroup" );
	ButtonGroup(float x, float y, float w, const str_t& label="ButtonGroup" );
	ButtonGroup(const pos_t& pos, const sz2_t& sz, const str_t& label="ButtonGroup" );
	ButtonGroup(const pos_t& pos, float w, const str_t& label="ButtonGroup" );
	
	virtual void		rearrange(NVGcontext* vg,autoscale_t scaling) override;
	virtual void		asGroup() { _asGroup = true; change(); }
	virtual void		asIndividual() { _asGroup = false; change(); }

protected:
	virtual void		drawBoxOver(NVGcontext* vg,const rct_t& r) override;
	bool				_asGroup = true;

};

} // namespace JGL2


#include "Button.hpp"
#include <mutex>

namespace JGL2 {

inline ButtonGroup::ButtonGroup(float x, float y, float w, float h, const str_t& label )
:Aligner(x,y,w,h,label){
	alignment(align_t::ALL);
	autoscale(autoscale_t::ALL);
}

inline ButtonGroup::ButtonGroup(float x, float y, float w, const str_t& label )
:Aligner(x,y,w,_size_button_height(),label){
	alignment(align_t::ALL);
	autoscale(autoscale_t::ALL);
}

inline ButtonGroup::ButtonGroup(const pos_t& pos, const sz2_t& sz, const str_t& label )
:Aligner(pos,sz,label){
	alignment(align_t::ALL);
	autoscale(autoscale_t::ALL);
}

inline ButtonGroup::ButtonGroup(const pos_t& pos, float w, const str_t& label )
:Aligner(pos,sz2_t(w,_size_button_height()),label){
	alignment(align_t::ALL);
	autoscale(autoscale_t::ALL);
}

inline void findFirstLast( const widget_list_t& _children, Widget*& first, Widget* & last) {
	first = nullptr;
	last = nullptr;
	for( auto c : _children ) if(c && !c->hidden() ){
		if( !first ) first = c;
		last = c;
	}
}

inline void ButtonGroup::rearrange(NVGcontext* vg,autoscale_t scaling) {
	if( changed() ) {
		Aligner::rearrange(vg,scaling);
		if( _asGroup ) {
			Button* first = nullptr;
			Button* last = nullptr;
			
			std::unique_lock<std::mutex> lock(_childMutex);
			for( auto c : _children ) if(c && !c->hidden() ){
				Button* b = dynamic_cast<Button*>(c);
				if( b ) {
					if( !first ) {
						first = b;
						b->boxType(box_type_t::BOX_LEFT);
					}
					else
						b->boxType(box_type_t::BOX_MIDDLE);
					last = b;
				}
			}
			if( last ) {
				if( first != last )
					last->boxType(box_type_t::BOX_RIGHT);
				else
					last->boxType(box_type_t::BOX_IND);
			}
		}
		else {
			std::unique_lock<std::mutex> lock(_childMutex);
			for( auto c : _children ) if(c && !c->hidden() ){
				Button* b = dynamic_cast<Button*>(c);
				if( b ) {
					b->boxType(box_type_t::BOX_IND);
				}
			}
		}
	}
}

inline void ButtonGroup::drawBoxOver(NVGcontext* vg,const rct_t& r) {
	Widget* targetted = nullptr;
	for( size_t i=0; i<children(); i++ ) {
		_Targettable* t = dynamic_cast<_Targettable*>(child(idx_t(i)));
		if( t && t->targetted() ) { targetted = child(idx_t(i)); break; }
	}
	if( targetted ) ((_Targettable*)targetted)->clearTarget();
	
	
	Aligner::drawBoxOver(vg,r);
	if( !targetted ) return;

	_Targettable* t = dynamic_cast<_Targettable*>(targetted);
	t->setTarget();
	
	
	nvgSave( vg );
	_Scrollable* sc = dynamic_cast<_Scrollable*>(this);
	if( sc )
		nvgTranslate(vg, -sc->scrollOffset().x, -sc->scrollOffset().y );
	nvgSave( vg );
	nvgTranslate( vg, targetted->x(), targetted->y() );
	rct_t box = rct_t(0,0,targetted->w(), targetted->h());
	nvgIntersectScissor( vg, 0, 0, box.w, box.h );
	targetted->drawBox(vg,box);
	targetted->drawContents(vg,box,targetted->alignment());
	targetted->drawBoxOver(vg,box);
	nvgRestore(vg);
	nvgRestore(vg);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* ButtonGroup_h */
