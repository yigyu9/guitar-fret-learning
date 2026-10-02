//
//  Splitter.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_Splitter_h
#define JGL2_Splitter_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Aligner.hpp>

namespace JGL2 {

struct Splitter: public Aligner {
	Splitter(float x,float y,float w,float h, const str_t& label="Splitter" );
	Splitter(const pos_t& pos, const sz2_t& sz, const str_t& label="Splitter" );
	virtual float spacing() const override { return _spacing<0?_size_splitter_spacing():_spacing; }
	virtual Widget* underWidget(const pos_t& pt) override;

protected:
	virtual bool handle( event_t event ) override;
	virtual void drawContents(NVGcontext* vg,const rct_t& r, align_t a) override;

	int			_onSplitter = 0;
	pos_t		_lastPointer;
};

inline Splitter::Splitter(float x,float y,float w,float h, const str_t& label )
: Aligner(x,y,w,h,label){
	Aligner::spacing(-1);
}

inline Splitter::Splitter(const pos_t& pos, const sz2_t& sz, const str_t& label )
: Aligner(pos,sz,label){
	Aligner::spacing(-1);
}

inline void Splitter::drawContents(NVGcontext* vg, const rct_t& r, align_t align) {
	Aligner::drawContents(vg, r, align);

	std::unique_lock<std::mutex> lock(_childMutex);
	if( type() == direction_t::HORIZONTAL )
		for( int i=1; i<children(); i++ ) {
			if( !child(i)->hidden() )
				_draw_splitter_separator_horz(vg, r, child(i)->x() );
		}
	else
		for( int i=1; i<children(); i++ )
			if( !child(i)->hidden() )
				_draw_splitter_separator_vert(vg, r, child(i)->y() );
}

inline Widget* Splitter::underWidget(const pos_t& pt) {
	if( under(pt) && _onSplitter>0 ) return this;
	return Aligner::underWidget( pt );
}

inline bool Splitter::handle( event_t event ) {
	switch( event ) {
		case event_t::ENTER:
			_onSplitter = 0;
			break;
		case event_t::MOVE: {
			int oldSplitter = _onSplitter;
			_onSplitter = 0;
			std::unique_lock<std::mutex> lock(_childMutex);
			{
				for( int i=1; i<children(); i++ ) {
					if( !child(i)->hidden() ) {
						float delta = 0;
						if( type() == direction_t::HORIZONTAL )
							delta = ( child(i)->x()-1 ) - _JGL::eventX();
						else
							delta = ( child(i)->y()-1 ) - _JGL::eventY();
						if( abs( delta )<4 ) {
							_onSplitter = i;
							break;
						}
					}
				}
			}
			if( _onSplitter>0 ) {
				_lastPointer =  _JGL::eventPt();
				if(  oldSplitter<1 )
					_JGL::setCursor( type() == direction_t::HORIZONTAL?cursor_t::HRESIZE:cursor_t::VRESIZE );
			}
			else if( _onSplitter<1 && oldSplitter>0 )
				_JGL::setCursor( cursor_t::ARROW );
		}
		break;
		case event_t::DRAG:
			if( _onSplitter>0 ) {
				pos_t pos0 = child(_onSplitter-1)->position();
				pos_t pos1 = child(_onSplitter  )->position();
				sz2_t sz0  = child(_onSplitter-1)->size();
				sz2_t sz1  = child(_onSplitter  )->size();

				if( type() == direction_t::HORIZONTAL ) {
					float delta = _JGL::eventPt().x-_lastPointer.x;
					_lastPointer = _JGL::eventPt();
					if( sz0.w+delta<std::max(_size_split_min(),child(_onSplitter-1)->minSize().w) )
						delta=std::max(_size_split_min(),child(_onSplitter-1)->minSize().w)-sz0.w;
					if( sz1.w-delta<std::max(_size_split_min(),child(_onSplitter  )->minSize().w) )
						delta=sz1.w-std::max(_size_split_min(),child(_onSplitter  )->minSize().w);
					if( !_JGL::eventMods(mod_t::SHIFT) ) {
						float dd = 0;
						if( abs( (sz0.w+delta)-(sz1.w-delta) )<10 )
							dd = (sz0.w+delta-sz1.w+delta)/2;
						else if( abs( sz0.w+delta - w()/children() )<10 )
							dd = sz0.w +delta - w()/children();
						else if( abs( sz1.w-delta - w()/children() )<10 )
							dd =  w()/children() - sz1.w + delta;
						delta -= dd;
						_lastPointer.x -= dd;
					}
					sz0.w += delta;
					sz1.w -= delta;
					pos1.x+= delta;
				}
				else {
					float delta = _JGL::eventPt().y-_lastPointer.y;
					_lastPointer = _JGL::eventPt();
					if( sz0.h+delta<std::max(_size_split_min(),child(_onSplitter-1)->minSize().h) )
						delta=std::max(_size_split_min(),child(_onSplitter-1)->minSize().h)-sz0.h;
					if( sz1.h-delta<std::max(_size_split_min(),child(_onSplitter  )->minSize().h) )
						delta=sz1.h-std::max(_size_split_min(),child(_onSplitter  )->minSize().h);
					if( !_JGL::eventMods(mod_t::SHIFT) ) {
						float dd = 0;
						if( abs( (sz0.h+delta)-(sz1.h-delta) )<10 )
							dd = (sz0.h+delta-sz1.h+delta)/2;
						else if( abs( sz0.h+delta - h()/children() )<10 )
							dd = sz0.h +delta - h()/children();
						else if( abs( sz1.h-delta - h()/children() )<10 )
							dd =  h()/children() - sz1.h + delta;
						delta -= dd;
						_lastPointer.y -= dd;
					}
					sz0.h += delta;
					sz1.h -= delta;
					pos1.y+= delta;
				}
				child(_onSplitter-1)->resize( pos0, sz0 );
				child(_onSplitter  )->resize( pos1, sz1 );
				change();
				damage();
			}
			break;
		case event_t::LEAVE:
			if( _onSplitter>0 )
				_JGL::setCursor( cursor_t::ARROW );
			break;
		default:
			break;
	}
	
	if( _onSplitter>0 ) return true;
	
	return false;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* Splitter_h */
