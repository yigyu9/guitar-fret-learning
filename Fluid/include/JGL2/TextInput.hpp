//
//  TextInput.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_TextInput_h
#define JGL2_TextInput_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_TextInputBase.hpp>
#include <JGL2/_Valued.hpp>

namespace JGL2 {

struct TextInput: public _TextInputBase, public _Valued<str_t> {
	TextInput(float x, float y, float w, float h, const str_t& label);
	virtual	str_t	value() const override { return str(); }
	virtual void	value(const str_t& s) override;
protected:
	
	virtual void	stringEntered() override;
	virtual bool	valid(const str_t& s) const override;
};

inline TextInput::TextInput(float x, float y, float w, float h, const str_t& label)
: _TextInputBase(x, y, w, h, label) {}

inline void TextInput::stringEntered() {
	updateAutoVal();
}

inline void TextInput::value(const str_t& v) {
	str( v );
	updateAutoVal();
}

inline bool TextInput::valid(const str_t& s) const {
	return true;
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* TextInput_h */
