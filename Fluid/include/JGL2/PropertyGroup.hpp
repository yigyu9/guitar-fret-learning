//
//  PropertyGroup.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_PropertyGroup_h
#define JGL2_PropertyGroup_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Aligner.hpp>
#include <JGL2/Property.hpp>

namespace JGL2 {

struct PropertyGroup : Aligner {
	PropertyGroup(float x, float y, float w, float h, const str_t& l="") :Aligner(x,y,w,h,l) { type(direction_t::VERTICAL); }
	PropertyGroup(const pos_t& pos, const sz2_t& sz, const str_t& l="") :Aligner(pos,sz,l) { type(direction_t::VERTICAL); }
	
	virtual void		rearrange(NVGcontext* vg,autoscale_t scaling) override;

	virtual void		labelAlignment( align_t a );
	virtual void		actionAlignment( align_t a );
	virtual void		labelOffset(float off);
	virtual void		labelPos(label_pos_t pos);
	
protected:
	align_t				_labelAlignment = align_t::RIGHT;
	align_t				_actionAlignment = align_t::LEFT;
	label_pos_t			_labelPos = label_pos_t::LEFT;
	float				_labelOffset = _size_property_label_offset();
};

inline void PropertyGroup::labelAlignment( align_t a ){
	if( _labelAlignment!=a ) {
		_labelAlignment = a;
		changed();
	}
}

inline void PropertyGroup::actionAlignment( align_t a ){
	if( _actionAlignment!=a ) {
		_actionAlignment = a;
		changed();
	}
}

inline void PropertyGroup::labelOffset(float off){
	if( _labelOffset!=off ) {
		_labelOffset = off;
		changed();
	}
}

inline void PropertyGroup::labelPos(label_pos_t pos){
	if( _labelPos!=pos ) {
		_labelPos = pos;
		changed();
	}
}

inline void PropertyGroup::rearrange(NVGcontext* vg,autoscale_t scaling) {
	float maxLabelWidth = 0;
	for( auto c: _children ) {
		Property* p = dynamic_cast<Property*>(c);
		if( p ) {
			p->labelPos( _labelPos );
			p->alignment( _labelAlignment );
			p->labelOffset( _labelOffset );
			p->actionAlignment( _actionAlignment );
			float labelWidth = p->measureTextLabel(vg).w;
			maxLabelWidth = std::max( labelWidth, maxLabelWidth );
		}
	}
	for( auto c: _children ) {
		Property* p = dynamic_cast<Property*>(c);
		if( p ) {
			sz2_t sz = p->measureTextLabel(vg);
			p->labelSize( sz2_t( maxLabelWidth, sz.h));
		}
	}
	Aligner::rearrange(vg,scaling);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* PropertyGroup_h */
