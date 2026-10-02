//
//  Property.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Property_h
#define JGL2_Property_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Widget.hpp>

namespace JGL2 {

struct PropertyGroup;

struct Property : Widget {

	virtual label_pos_t	labelPos() const { return _labelPos; }
	virtual float		labelOffset() const { return _labelOffset<-100.?_size_property_label_offset():_labelOffset; }
	virtual sz2_t		actionSize() const { return _actionSz; }
	virtual bool		labelSizeConstrained() const { return _labelSizeConstrained; }
	virtual align_t		actionAlignment() const { return _actionAlignment; }

	virtual void		labelPos(label_pos_t pos);
	virtual void		labelOffset(float off);
	virtual void		actionAlignment(align_t a);
	
	virtual bool		active() const override;
		
protected:
	
	virtual void		labelSize(const sz2_t& sz);

	Property(float x, float y, float w, float h, const str_t& label="");
	Property(const pos_t& pos, const sz2_t& sz, const str_t& label="");
	label_pos_t			_labelPos			= label_pos_t::LEFT;
	float				_labelOffset		= -101.f;
	sz2_t				_actionSz;
	sz2_t				_constLabelSz;
	align_t				_actionAlignment	= align_t::LEFT;
	
	rct_t				_actionBox;
	rct_t				_labelBox;
	bool				_labelSizeConstrained = false;

	virtual void		unconstrainLabelSize();

	virtual void		drawContents(NVGcontext* vg, const rct_t& r, align_t alignment) override;

	virtual void 		updateContentsRect(NVGcontext* vg) override;
	virtual void		rearrange(NVGcontext* vg,autoscale_t scaling) override;

	virtual sz2_t		minActionSize(NVGcontext* vg) const = 0;
	virtual void		drawAction(NVGcontext* vg, const rct_t& r, align_t alignment)=0;

private:
	virtual void		updateLabelAction(NVGcontext*vg);
	virtual void		autoActionSize(NVGcontext*vg);
	friend PropertyGroup;
};


inline Property::Property(float x, float y, float w, float h, const str_t& label)
:Widget(x,y,w,h,label) {}

inline Property::Property(const pos_t& pos, const sz2_t& sz, const str_t& label)
:Widget(pos,sz,label) {}

inline void Property::labelPos(label_pos_t pos) {
	if( _labelPos!= pos ) {
		_labelPos = pos;
		if( parent() ) parent()->change();
		change();
		damage();
	}
}

inline void Property::labelOffset(float offset) {
	if( _labelOffset!= offset ) {
		_labelOffset = offset;
		if( parent() ) parent()->change();
		change();
		damage();
	}
}

inline void Property::labelSize(const sz2_t& sz) {
	_constLabelSz = sz;
	_labelSizeConstrained = true;
	change();
	if( parent() ) parent()->change();
}

inline void Property::actionAlignment(align_t a) {
	_actionAlignment = a;
	change();
	if( parent() ) parent()->change();
}

inline void Property::unconstrainLabelSize() {
	_labelSizeConstrained = false;
	change();
	if( parent() ) parent()->change();
}

inline void Property::drawContents(NVGcontext* vg, const rct_t& r, align_t alignment){
	if( labelPos()!=label_pos_t::NONE )
		drawTextLabel(vg,_labelBox,alignment);
	drawAction(vg,_actionBox,actionAlignment());
//	Widget::drawContents(vg,r,alignment);
}

inline void Property::updateContentsRect(NVGcontext* vg) {
	sz2_t fitSize(0,0);
//	rect box = paddedRect();
	sz2_t labelSz = _labelSizeConstrained?_constLabelSz:measureTextLabel(vg);
	sz2_t minActionSz = minActionSize(vg);
	switch( labelPos() ) {
		case label_pos_t::NONE:
//			if( actionScalableW() )
//				fitSize.w = glm::max( box.w, minActionSz.w );
//				fitSize.w = minActionSz.w;
//			else
				fitSize.w = minActionSz.w;
//			if( actionScalableH() )
//				fitSize.h = glm::max( box.h, minActionSz.h );
//				fitSize.h = minActionSz.h;
//			else
				fitSize.h = minActionSz.h;
			break;
		case label_pos_t::LEFT:
		case label_pos_t::RIGHT:
//			if( actionScalableW() )
//				fitSize.w = labelSz.w+labelOffset()+glm::max( box.w-labelSz.w-labelOffset(), minActionSz.w );
//				fitSize.w = labelSz.w+labelOffset()+minActionSz.w;
//			else
				fitSize.w = labelSz.w+labelOffset()+minActionSz.w;
//			if( actionScalableH() )
//				fitSize.h = glm::max( box.h, glm::max( labelSz.h, minActionSz.h ) );
//				fitSize.h = glm::max( labelSz.h, minActionSz.h );
//			else
				fitSize.h = std::max( labelSz.h, minActionSz.h );
			break;
		case label_pos_t::TOP:
		case label_pos_t::BOTTOM:
//			if( actionScalableW() )
//				fitSize.w = glm::max( box.w, glm::max( labelSz.w, minActionSz.w ) );
//				fitSize.w = glm::max( labelSz.w, minActionSz.w );
//			else
				fitSize.w = std::max( labelSz.w, minActionSz.w );
//			if( actionScalableH() )
//				fitSize.h = labelSz.h+labelOffset()+glm::max( box.h-labelSz.h-labelOffset(), minActionSz.h );
//				fitSize.h = labelSz.h+labelOffset()+minActionSz.h;
//			else
				fitSize.h = labelSz.h+labelOffset()+minActionSz.h;
			break;
	}
	_contentsRect.tl()=pos_t(0,0);
	_contentsRect.wh()=fitSize+sz2_t(horzPadding(),vertPadding());
}

inline void Property::rearrange(NVGcontext* vg,autoscale_t scaling) {
	if( changed() ) {
		autoscale_t sc = autoscale() & scaling;
		autoActionSize(vg);
		updateContentsRect(vg);
		if( (sc & autoscale_t::W)!=autoscale_t::NONE )
			_setSize.w = contentsRect().w;
		if( (sc & autoscale_t::H)!=autoscale_t::NONE )
			_setSize.h = contentsRect().h;
		_bound.wh() = max(_setSize,minSize());
		autoActionSize(vg);
		updateLabelAction(vg);
	}
	_changed = false;
}

inline void Property::autoActionSize(NVGcontext*vg) {
//	if( actionSizeConstrained() ) return;
	rct_t box = paddedRect();
	sz2_t labelSz = _labelSizeConstrained?_constLabelSz:measureTextLabel(vg);
	sz2_t minActionSz = minActionSize(vg);

	switch( labelPos() ) {
		case label_pos_t::NONE:
			_actionSz.h = std::max( box.h, minActionSz.h );
			_actionSz.w = std::max( box.w, minActionSz.w );
			break;
		case label_pos_t::TOP:
			_actionSz.h = std::max( box.h-labelSz.h-labelOffset(), minActionSz.h );
			_actionSz.w = std::max( box.w, minActionSz.w );
			break;
		case label_pos_t::BOTTOM:
			_actionSz.h = std::max( box.h-labelSz.h-labelOffset(), minActionSz.h );
			_actionSz.w = std::max( box.w, minActionSz.w );
			break;
		case label_pos_t::LEFT:
			_actionSz.w = std::max( box.w-labelSz.w-labelOffset(), minActionSz.w );
			_actionSz.h = std::max( box.h, minActionSz.h );
			break;
		case label_pos_t::RIGHT:
			_actionSz.w = std::max( box.w-labelSz.w-labelOffset(), minActionSz.w );
			_actionSz.h = std::max( box.h, minActionSz.h );
			break;
	}
}


inline void Property::updateLabelAction(NVGcontext*vg) {
	rct_t box = paddedRect();
	switch( labelPos() ) {
		case label_pos_t::NONE:
			_actionBox = box;
			break;
		case label_pos_t::TOP:
			_actionBox = rct_t( box.x, box.y+box.h-actionSize().h, box.w, actionSize().h );
			_labelBox  = rct_t( box.tl(), box.w, box.h-actionSize().h-labelOffset() );
			break;
		case label_pos_t::BOTTOM:
			_actionBox = rct_t( box.tl(), box.w, actionSize().h );
			_labelBox  = rct_t( box.x, box.y+actionSize().h+labelOffset(),
							  box.w, box.h-actionSize().h-labelOffset() );
			break;
		case label_pos_t::LEFT:
			_actionBox = rct_t( box.x+box.w-actionSize().w, box.y, actionSize().w, box.h );
			_labelBox  = rct_t( box.tl(), box.w-actionSize().w-labelOffset(), box.h );
			break;
		case label_pos_t::RIGHT:
			_actionBox = rct_t( box.tl(), actionSize().w, box.h );
			_labelBox  = rct_t( box.x+actionSize().w+labelOffset(), box.y,
							  box.w-actionSize().w-labelOffset(), box.h );
			break;

	}
}

struct PropertyGroup;

inline bool Property::active() const {
	return parent()->active() && Widget::active();
}


} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Property_h */
