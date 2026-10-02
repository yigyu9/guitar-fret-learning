//
//  _Valued.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__Valued_h
#define JGL2__Valued_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/Widget.hpp>

namespace JGL2 {

template<typename T>
struct _Valued {
	virtual void		value(const T&) = 0;
	virtual T			value() const = 0;
	virtual void		autoValue(T& v) { autoValue(&v); }
	virtual void		autoValue(T* v);
protected:
	T*					_autoValuePtr = nullptr;
	void				updateAutoVal();
};

template<typename T>
void	_Valued<T>::autoValue(T* v) {
	if( v ) value(*v);
	_autoValuePtr = v;
	if( _autoValuePtr )
		*_autoValuePtr = value();

}

template<typename T>
void _Valued<T>::updateAutoVal() {
	if( _autoValuePtr ) *_autoValuePtr = value();
/*	Widget* w = dynamic_cast<Widget*>(this);
	if( _autoValuePtr && w )
		cout<<w->label()<<" auto value is changed to :"<<(*_autoValuePtr)<<endl;*/
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _Valued_h */
