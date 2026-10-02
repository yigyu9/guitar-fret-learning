//
//  TextInputBase.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_TextInputBase_h
#define JGL2_TextInputBase_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <string>

#include <JGL2/Property.hpp>

namespace JGL2 {

struct _TextInputBase: public Property, public _Targettable {
	enum class operation_type {
		SET,
		ADD,
		DEL,
		REPLACE,
		PASTE,
		CUT,
		OTHER,
	};
	virtual bool			textDamaged() { return _textDamaged; }
	virtual void			textDamage();
	
	virtual void			textAlignment(align_t a);
	virtual align_t 		textAlignment() const { return _textAlignment; }
		
	virtual void			select(idx_t start,idx_t end);
	virtual void			deleteSelection();
	virtual void			append( const str_t& s);
	virtual void			replace( const str_t& s);
		
	virtual bool			handle(event_t event) override;
		
	virtual void			enterPressed();
	virtual void			enterPressedCallback( Callback_t c, void* ud=nullptr);
		
	virtual str_t			str() const { return _str; }
	virtual void			str(const str_t& s);
	virtual void			stringEntered(){}
		
protected:
	
	_TextInputBase(float x,float y,float w,float h, const str_t& label );

	virtual bool			valid(const str_t& s) const =0;
	
	virtual float			boxHorzPadding() const { return _boxHorzPadding<0?_size_options_box_horz_padding():_boxHorzPadding; }
	virtual sz2_t			minActionSize(NVGcontext*vg) const override;
	virtual void			drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) override;
	
	virtual void			updateLocations(NVGcontext*vg);
	virtual void			stringChanged();
	
	virtual float			cursorLoc(idx_t c);
	virtual float			cursorPos(idx_t c);
	virtual idx_t			ptToCursor( const pos_t& pt );
	virtual void			updateScroll(const rct_t& r);
	
	str_t					_str					="";
	idx_t					_cursor					=0;
	idx_t					_selectionL				=0;
	idx_t					_selectionR				=0;
	flst_t					_locations				={0,0};
	align_t					_textAlignment			=align_t::LEFT;
	float					_boxHorzPadding			=-1.f;
	float					_scrolled				=0;
	pos_t					_textOffset				=pos_t(0,0);
	sz2_t					_textSz					=sz2_t(0,0);
	bool					_textDamaged			=true;
	idx_t					_clickedCursor			=0;
		
	Callback_t				_enterPressedCallback	=nullptr;
	void*					_enterPressedUserdata	=nullptr;
	
	
	// For undo...
	virtual bool			undo();
	virtual bool			redo();
	virtual void			storeUndo(operation_type operation);
	virtual void			setUndoCursor();
	virtual void			clearLastOp();
	virtual void			clearUndo();

	slst_t					_undoStack				= {""};
	ilst_t					_undoCursorStack		= {0};
	idx_t					_undoValidPointer		= 0;
	idx_t					_undoPointer			= 0;
	operation_type			_lastOp					= operation_type::OTHER;
	idx_t					_maxHistory				= 20;
};

inline _TextInputBase::_TextInputBase(float x,float y,float w,float h, const str_t& label )
:Property(x, y, w, h, label){ }

inline bool is_break_letter( char c ) { return c=='.' || c==' ' || c==':' || c==';'; }

inline idx_t skipBreakLeft(const str_t& str, idx_t l) {
	for( idx_t i=l-1; i>=0; i-- ) if( !is_break_letter(str[i]) ) return i+1;
	return 0;
}

inline idx_t beforeBreakLeft(const str_t& str, idx_t l) {
	for( idx_t i=l-1; i>=0; i-- ) if(  is_break_letter(str[i]) ) return i+1;
	return 0;
}

inline idx_t skipBreakRight(const str_t& str, idx_t r) {
	for( idx_t i=r; i<str.length(); i++ ) if( !is_break_letter(str[i]) ) return i;
	return idx_t(str.length());
}

inline idx_t beforeBreakRight(const str_t& str, idx_t r) {
	for( idx_t i=r; i<str.length(); i++ ) if(  is_break_letter(str[i]) ) return i;
	return idx_t(str.length());
}

inline bool wordSelection() {
#ifdef __APPLE__
	return _JGL::eventMods(mod_t::ALT);
#else
	return  _JGL::eventMods(mod_t::CONTROL);
#endif
}

inline bool _TextInputBase::handle(event_t event) {
	switch( event ) {
		case event_t::CHAR:
			replace(to_utf8str(_JGL::eventCodePoint()));
			return true;
		case event_t::TARGETTED:
			_selectionL = 0;
			_selectionR = idx_t(_str.length());
			_cursor = _selectionR;
			_scrolled = 0;
			clearLastOp();
			damage();
			return true;
		case event_t::UNTARGETTED:
			_scrolled = 0;
			enterPressed();
			damage();
			return true;
		case event_t::PUSH: {
			idx_t c = ptToCursor( _JGL::eventPt() );
			_clickedCursor = c;
			if( _cursor!=_clickedCursor || _cursor!=_selectionL || _cursor!=_selectionR ) {
				_cursor = _selectionL = _selectionR = c;
				clearLastOp();
				damage();
			}
		} return true;
		case event_t::DRAG: {
			idx_t c = ptToCursor( _JGL::eventPt() );
			if( _clickedCursor== c )
				_cursor = _selectionR = _selectionL = c;
			else if( _clickedCursor< c )
				_cursor = _selectionR = c;
			else
				_cursor = _selectionL = c;
			clearLastOp();
			damage();
		} 	return true;
		case event_t::PASTE: {
			str_t str = _JGL::eventPasteString();
			if( str.length()>0 ) {
				clearLastOp();
				replace(str);
			}
		} return true;
		case event_t::COPY:
			if( _selectionL<_selectionR )
				_JGL::eventCopyString( _str.substr(_selectionL, _selectionR-_selectionL) );
			return true;
		case event_t::CUT:
			if( _selectionL<_selectionR ) {
				_JGL::eventCopyString( _str.substr(_selectionL, _selectionR-_selectionL) );
				clearLastOp();
				deleteSelection();
			}
			return true;
		case event_t::UNDO:
			undo();
			break;
		case event_t::REDO:
			redo();
			return true;
		case event_t::REPEAT:
		case event_t::KEYDOWN: {
			switch( _JGL::eventKey() ) {
				case GLFW_KEY_BACKSPACE:
					if( _cursor!=_selectionR || _cursor!=_selectionL )
						deleteSelection();
					else if( _cursor>0 ) {
						_selectionL=_cursor-1;
						_selectionR=_cursor;
						deleteSelection();
					}
					return true;
				case GLFW_KEY_DELETE:
					if( _cursor!=_selectionR || _cursor!=_selectionL )
						deleteSelection();
					else if( _cursor<_str.length() ) {
						_selectionL=_cursor;
						_selectionR=_cursor+1;
						deleteSelection();
					}
					return true;
				case GLFW_KEY_LEFT:
					if( _JGL::eventMods(mod_t::SHIFT) ) {
						if( _cursor == _selectionL ) {
							if( _selectionL>0 ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_selectionL = 0;
								}
								else if( wordSelection() ) {
									_selectionL = skipBreakLeft(_str,_selectionL);
									_selectionL = beforeBreakLeft(_str,_selectionL);
								}
								else _selectionL--;
								_cursor=_selectionL;
								clearLastOp();
								damage();
							}
						} else {
							if( _selectionR>0 ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_selectionR = _selectionL;
								}
								else if( wordSelection() ) {
									_selectionR = beforeBreakLeft(_str,_selectionR);
									_selectionR = skipBreakLeft(_str,_selectionR);
									_selectionR = std::max( _selectionR, _selectionL );
								}
								else _selectionR--;
								_cursor=_selectionR;
								clearLastOp();
								damage();
							}
						}
					}
					else {
						if( _cursor!=_selectionR || _cursor!=_selectionL )
							_cursor = _selectionL;
						else {
							if( _cursor>0 ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_cursor = 0;
								}
								else if( wordSelection() ) {
									_cursor = skipBreakLeft(_str,_cursor);
									_cursor = beforeBreakLeft(_str,_cursor);
								}
								else
									_cursor--;
							}
						}
						_selectionL = _selectionR = _cursor;
						clearLastOp();
						damage();
					}
					return true;
				case GLFW_KEY_RIGHT:
					if( _JGL::eventMods(mod_t::SHIFT) ) {
						if( _cursor == _selectionR ) {
							if( _selectionR<idx_t(_str.length()) ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_selectionR = idx_t(_str.length());
								}
								else if( wordSelection() ) {
									_selectionR = skipBreakRight(_str,_selectionR);
									_selectionR = beforeBreakRight(_str,_selectionR);
								}
								else _selectionR++;
								_cursor=_selectionR;
								clearLastOp();
								damage();
							}
						} else {
							if( _selectionL<idx_t(_str.length()) ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_selectionL = _selectionR;
								}
								else if( wordSelection() ) {
									_selectionL = beforeBreakRight(_str,_selectionL);
									_selectionL = skipBreakRight(_str,_selectionL);
									_selectionL = std::min( _selectionR, _selectionL );
								}
								else _selectionL++;
								_cursor=_selectionL;
								clearLastOp();
								damage();
							}
						}
					}
					else {
						if( _cursor!=_selectionR || _cursor!=_selectionL )
							_cursor = _selectionR;
						else {
							if( _cursor<idx_t(_str.length()) ) {
								if( _JGL::eventMods(mod_t::SUPER) ) {
									_cursor = idx_t(_str.length());
								}
								else if( wordSelection() ) {
									_cursor = beforeBreakRight(_str,_cursor);
									_cursor = skipBreakRight(_str,_cursor);
								}
								else
									_cursor++;
							}
						}
						_selectionL = _selectionR = _cursor;
						clearLastOp();
						damage();
					}
					return true;
				case GLFW_KEY_HOME:
					if( _JGL::eventMods(mod_t::SHIFT) ) {
						if( _selectionL>0 ) {
							_selectionL = 0;
							_cursor=_selectionL;
							clearLastOp();
							damage();
						}
					}
					else {
						_cursor = 0;
						_selectionL = _selectionR = _cursor;
						clearLastOp();
						damage();
					}
					return true;
				case GLFW_KEY_END:
					if( _JGL::eventMods(mod_t::SHIFT) ) {
						if( _selectionR<idx_t(_str.length()) ) {
							_selectionL = idx_t(_str.length());
							_cursor=_selectionR;
							clearLastOp();
							damage();
						}
					}
					else {
						_cursor = idx_t(_str.length());
						_selectionL = _selectionR = _cursor;
						clearLastOp();
						damage();
					}
					return true;
				case GLFW_KEY_ENTER:
					clearLastOp();
					enterPressed();
					return true;
			}
		} break;
		default:
			break;
	}
	return Property::handle(event);
}

inline void _TextInputBase::append(const str_t &s) {
	str_t temp;
	if( _cursor==0 )
		temp = s+_str;
	else if( _cursor == _str.length() )
		temp = _str+s;
	else
		temp = _str.substr(0,_cursor)+s+_str.substr(_cursor,str_t::npos);
	if( valid( temp ) ) {
		_str = temp;
//		stringEntered();
		storeUndo(operation_type::ADD);
		_cursor+=idx_t(s.length());
		_selectionL = _selectionR = _cursor;
		setUndoCursor();
		textDamage();
	}
}

inline void _TextInputBase::deleteSelection() {
	if( _cursor!=_selectionR || _cursor!=_selectionL ) {
		str_t temp = "";
		if( _selectionL>0 )
			temp+= _str.substr(0,_selectionL);
		if( _selectionR<_str.length() )
			temp+= _str.substr(_selectionR,str_t::npos);
		if( valid( temp ) ) {
			_str = temp;
//			stringEntered();
			storeUndo(operation_type::DEL);
			_cursor = _selectionL;
			_selectionR = _cursor;
			setUndoCursor();
			textDamage();
		}
	}
}

inline void _TextInputBase::replace( const str_t& s) {
	if( _cursor!=_selectionR || _cursor!=_selectionL ) {
		str_t temp = "";
		if( _selectionL>0 )
			temp+= _str.substr(0,_selectionL);
		temp+=s;
		if( _selectionR<_str.length() )
			temp+= _str.substr(_selectionR,str_t::npos);
		if( valid( temp ) ) {
			_str = temp;
//			stringEntered();
			storeUndo(operation_type::REPLACE);
			_cursor = _selectionL;
			_cursor+= idx_t(s.length());
			_selectionL = _selectionR = _cursor;
			setUndoCursor();
			textDamage();
		}
	}
	else
		append(s);
}

inline void _TextInputBase::str(const str_t& i) {
	if( valid( i ) ) {
		clearUndo();
		_str = i;
		stringEntered();
		select(0,idx_t(_str.length()) );
		storeUndo(operation_type::SET);
		_cursor = idx_t(_str.length());
		setUndoCursor();
		textDamage();
	}
}

inline void _TextInputBase::textDamage() {
	_textDamaged = true; // Update locations as soon as the next rendering time
	stringChanged();
	damage();			// which will be automatically called right after.
}

inline void _TextInputBase::select(idx_t start,idx_t end) {
	_selectionL = std::min(idx_t(0),start);
	_selectionR = std::max(idx_t(_str.length()-1),end<0?idx_t(_str.length()-1):end);
	damage();
}

inline void _TextInputBase::updateLocations(NVGcontext* vg) {
	static std::vector<NVGglyphPosition> pos;
	if( vg ) {
		pos.resize(_str.length()+1);
		size_t cnt = nvgTextGlyphPositions(vg, 0, 0, _str.c_str(), 0, pos.data(), int(pos.size()) );
		_locations.resize(_str.length()+1 );
		for( size_t i=0; i<cnt; i++ )
			_locations[i] = pos[i].maxx;
	}
}

inline void _TextInputBase::textAlignment(align_t a) {
	if( a!=_textAlignment ) {
		_textAlignment=a;
		damage();
	}
}

inline sz2_t _TextInputBase::minActionSize(NVGcontext*vg) const {
	return sz2_t(50,25);
}

inline void _TextInputBase::drawAction(NVGcontext* vg, const rct_t& r, align_t alignment) {
	rct_t contentBox = rct_t(r.x+boxHorzPadding(),r.y,r.w-boxHorzPadding()*2,r.h);

	if( textDamaged() ) {
		_textSz = _measure_textinputbase_text(vg, _str);
		updateLocations(vg);
		_textOffset = alignRect(contentBox, _textSz, _textAlignment);
		_textDamaged = false;
	}
	updateScroll( contentBox );

	rct_t textBox = rct_t( _textOffset+pos_t(_scrolled,0), _textSz );
	shade_state_t s = shadeState();

	_draw_textinputbase_box(vg, r, s);

	rct_t scissorRect = rct_t(r.x, r.y, r.w, r.h);

	if( _selectionR!=_cursor || _selectionL!=_cursor )
		_draw_textinputbase_selection(vg,r,scissorRect, cursorPos(_selectionL), cursorPos(_selectionR), s);
	else
		_draw_textinputbase_cursor(vg,r,scissorRect,cursorPos(_cursor),s);
	_draw_textinputbase_text(vg,textBox,scissorRect,_str,_textAlignment,s);
}

inline float _TextInputBase::cursorLoc(idx_t c) {
	return c==0?0:_locations[std::min(c,int(_str.length()))-1];
}

inline float _TextInputBase::cursorPos(idx_t c) {
	return _textOffset.x+_scrolled+cursorLoc(c);
}

inline idx_t _TextInputBase::ptToCursor(const pos_t& pt) {
	float x = pt.x-_textOffset.x-_scrolled;
	if( _str.length()<1 || x<_locations[0]/2)
		return 0;

	for( size_t i=0; i<_str.length()-1; i++)
		if( x<(_locations[i+1]+_locations[i])/2 )
			return idx_t(i+1);

	return idx_t(_str.length());
}

const float _def_after_cursor_visible = 10;
const float _def_cursor_size = 0;

inline void _TextInputBase::updateScroll(const rct_t& r) {
	if( !targetted() ) {
		_scrolled = 0;
		return;
	}
	float cx = cursorLoc(_cursor);

	if( r.w>_textSz.w ) _scrolled = 0;
	else if( cx+_textOffset.x+_scrolled > r.br().x-_def_after_cursor_visible ) {
		// The cursor is at the right boundary
		_scrolled = (r.br().x-_def_after_cursor_visible-cx-_textOffset.x);
		// Make sure that translated text is off right
		// _textSz.w+_textOffset.x+_scrolled>=r.br().x-cursorSize
		_scrolled = std::max(r.br().x-_def_cursor_size-(_textSz.w+_textOffset.x), _scrolled );
	}
	else if( cx+_textOffset.x+_scrolled < r.tl().x+_def_after_cursor_visible ) {
		_scrolled = r.tl().x+_def_after_cursor_visible-cx-_textOffset.x;
		// _textOffset.x+_scrolled<=r.tl().x+cursorSize
		_scrolled = std::min(r.tl().x+_def_cursor_size-_textOffset.x, _scrolled);
	}
}

inline void _TextInputBase::stringChanged() {
	doCallback();
}

inline void _TextInputBase::enterPressed() {
	stringEntered();
	if( _enterPressedCallback )
		_enterPressedCallback( this, _enterPressedUserdata );
}

inline void _TextInputBase::enterPressedCallback( Callback_t c, void* ud) {
	_enterPressedCallback = c;
	_enterPressedUserdata = ud;
}

inline bool _TextInputBase::undo() {
	if( _undoPointer>0 ) {
		--_undoPointer;
		_str = _undoStack[_undoPointer];
//		stringEntered();
		_cursor = _selectionL = _selectionR = _undoCursorStack[_undoPointer];
		clearLastOp();
		textDamage();
		return true;
	}
	return false;
}

inline bool _TextInputBase::redo() {
	if( _undoPointer<_undoStack.size()-1 && _undoPointer<_undoValidPointer ) {
		_undoPointer++;
		_str = _undoStack[_undoPointer];
//		stringEntered();
		_cursor = _selectionL = _selectionR = _undoCursorStack[_undoPointer];
		clearLastOp();
		textDamage();
		return true;
	}
	return false;
}

inline void _TextInputBase::clearUndo() {
	_undoPointer = -1;
	_undoValidPointer = -1;
	_undoStack.clear();
	_undoCursorStack.clear();
	clearLastOp();
}

inline void _TextInputBase::clearLastOp() {
	_lastOp = operation_type::OTHER;
}

inline void _TextInputBase::setUndoCursor() {
	if( _undoPointer>=0 && _undoPointer<_undoCursorStack.size() )
		_undoCursorStack[_undoPointer]=_cursor;
}

inline void _TextInputBase::storeUndo(operation_type operation) {
	if( _lastOp != operation || operation==operation_type::SET ) {
		if( _undoPointer>=0 )
			_undoCursorStack[_undoPointer]=_cursor;
		_undoPointer++;
	}
	if( _undoPointer<_undoStack.size() ) {
		_undoStack[_undoPointer]= _str ;
		_undoCursorStack[_undoPointer]=_cursor;
	}
	else {
		if( _undoStack.size()>=_maxHistory ) {
			_undoStack.erase(_undoStack.begin());
			_undoCursorStack.erase(_undoCursorStack.begin());
		}
		_undoStack.push_back( _str );
		_undoCursorStack.push_back(_cursor);
		_undoPointer = idx_t(_undoStack.size())-1;
	}
	_undoValidPointer = _undoPointer;
	_lastOp = operation;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* TextInputBase_h */
