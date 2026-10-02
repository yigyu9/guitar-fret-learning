//
//  NumberInput.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_NumberInput_h
#define JGL2_NumberInput_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_TextInputBase.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

template<typename T>
struct NumberInput: public _TextInputBase, public _Valued<T> {
	
	NumberInput(float x, float y, float w, float h, const str_t& label)
	: _TextInputBase(x,y,w,h,label) { value(0); }

	virtual T		value() const override { return stringToNumber( _TextInputBase::str() ); }
	virtual void	value(const T& v) override;
protected:
	virtual void	stringEntered() override;
	virtual void	enterPressed() override;
	virtual void	stringChanged() override;

	virtual bool	valid( const str_t& s) const override;
	
	virtual str_t	numberToString(const T& v) const;
	virtual T		stringToNumber(const str_t& s) const;
};

template<typename T> inline
void NumberInput<T>::stringEntered() {
	_Valued<T>::updateAutoVal();
}

template<typename T> inline
void NumberInput<T>::value(const T& v) {
	str( numberToString( v ) );
	_Valued<T>::updateAutoVal();
}

template<typename T> inline
void NumberInput<T>::stringChanged() {
	if( valid(_str) ) {
		_Valued<T>::updateAutoVal();
	}
	_TextInputBase::stringChanged();
}

template<typename T> inline
void NumberInput<T>::enterPressed() {
	_str = numberToString(stringToNumber(_TextInputBase::str()));
	_TextInputBase::enterPressed();
}

template<> inline
bool	NumberInput<int>::valid( const str_t& s) const {
	size_t end;
	str_t temp = s;
	if( s.length()<1 )
		temp = "0";
	try {
		void(stoi(temp, &end));
	}
	catch( std::exception ) {
		return false;
	}
	return end==temp.length();
}

template<> inline
bool	NumberInput<float>::valid( const str_t& s) const {
	size_t end;
	str_t temp = s;
	if( s.length()<1 )
		temp = "0";
	try {
		void(stof(temp, &end));
	}
	catch( std::exception ) {
		return false;
	}
	return end==temp.length();
}



template<> inline
str_t	NumberInput<int>::numberToString(const int& v) const {
	return to_str(v);
}

template<> inline
str_t	NumberInput<float>::numberToString(const float& v) const {
	return to_str(v);
}


template<> inline
int NumberInput<int>::stringToNumber(const str_t& s) const {
	str_t temp = s;
	int v = 0;
	if( s.length()<1 )
		temp = "0";
	try {
		v = stoi(temp);
	}
	catch( std::exception ) {
		return false;
	}
	return v;
}


template<> inline
float NumberInput<float>::stringToNumber(const str_t& s) const {
	str_t temp = s;
	float v = 0;
	if( s.length()<1 )
		temp = "0";
	try {
		v = stof(temp);
	}
	catch( std::exception ) {
		return false;
	}
	return v;
}

using NumberInputF = NumberInput<float>;
using NumberInputI = NumberInput<int>;

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* NumberInput_h */
