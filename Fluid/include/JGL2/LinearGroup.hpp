//
//  LinearGroup.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_LinearGroup_h
#define JGL2_LinearGroup_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Group.hpp>

namespace JGL2 {

struct LinearGroup: public Group {
	enum class direction_t {
		HORIZONTAL = 0,
		VERTICAL   = 1,
	};
	direction_t			type() const { return _type; }
	void				type( direction_t t ) { _type = t; }

	virtual void 		add( Widget* w ) override;
	virtual void		resizable( Widget* w );
	virtual void		resizable( Widget& w ) { resizable(&w); }
	virtual Widget*		resizable() const { return _resizable; }

protected:

	LinearGroup(float x, float y, float w, float h, const str_t& label="" );
	LinearGroup(const pos_t& pos, const sz2_t& sz, const str_t& label="" );
	virtual void		sortChildren();
	bool				_sorted		= false;
	direction_t			_type		= direction_t::HORIZONTAL;
	Widget*				_resizable	= nullptr;

};

} // namespace JGL2

#include <algorithm>

namespace JGL2 {

inline LinearGroup::LinearGroup(float x, float y, float w, float h, const str_t& label )
: Group( x, y, w, h, label ) {}

inline LinearGroup::LinearGroup(const pos_t& pos, const sz2_t& sz, const str_t& label )
: Group( pos, sz, label ) {}

inline void LinearGroup::sortChildren() {
	if( type() == direction_t::HORIZONTAL )
		std::sort( _children.begin(), _children.end(), [&]( const auto& a, const auto& b) {
			return a->x()<b->x();
		});
	else
		std::sort( _children.begin(), _children.end(), [&]( const auto& a, const auto& b) {
			return a->y()<b->y();
		});
	change();
}

inline void LinearGroup::add( Widget* w ) {
	Group::add(w);
//	sortChildren();
	change();
}

inline void LinearGroup::resizable( Widget* w ) {
	_resizable = w;
	if( _resizable ) {
		_resizable->changed();
	}
	changed();
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* LinearGroup_h */
