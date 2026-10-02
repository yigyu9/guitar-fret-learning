//
//  _Theme.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__Theme_h
#define JGL2__Theme_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_MathTypes.hpp>
#include <JGL2/_Draw.hpp>

namespace JGL2 {

template<typename T,typename=std::enable_if_t<std::is_enum_v<T>>> T operator | (T a, T b) {
	return T(int(a)|int(b));
}

template<typename T,typename=std::enable_if_t<std::is_enum_v<T>>> T operator & (T a, T b) {
	return T(int(a)&int(b));
}

template<typename T,typename=std::enable_if_t<std::is_enum_v<T>>> T operator ~ (T a) {
	return T(~int(a));
}
/*
template<typename T,typename=std::enable_if_t<std::is_enum_v<T>>> bool operator ! (T a) {
	return int(a)==0;
}
*/
template<typename T,typename=std::enable_if_t<std::is_enum_v<T>>> bool contains(T a, T b) {
	return ((int)a & (int)b)!=0;
}


enum class align_t : int {
	NONE			= 0,
	TOP				= (1<<0),
	BOTTOM			= (1<<1),
	LEFT			= (1<<2),
	RIGHT			= (1<<3),
	SIDE			= LEFT|RIGHT,
	TOP_BOTTOM		= TOP|BOTTOM,
	ALL				= SIDE|TOP_BOTTOM,
};

enum class shade_state_t {
	NORMAL				=0,
	WINDOW_UNFOCUSED	=(1<<0),
	INACTIVE			=(1<<1),
	TARGETTED			=(1<<2),
	PRESSED				=(1<<3),
	ENGAGED				=(1<<4),
};

enum class box_type_t {
	BOX_IND		= 0,
	BOX_LEFT	= 1,
	BOX_RIGHT	= 2,
	BOX_TOP		= 3,
	BOX_BOTTOM	= 4,
	BOX_MIDDLE	= 5,
};

enum class autoscale_t {
	NONE		= 0,
	W			= 1<<0,
	H			= 1<<1,
	ALL			= W|H,
};

enum class slide_type_t {
	NONE		= 0,
	TICKED		= 1,
	VALUED		= 2,
	ALL			= 3,
};

inline pos_t alignRect(const rct_t& range, const sz2_t& obj, align_t align) {
	pos_t ret = range.tl();
	if( contains( align, align_t::TOP ) && contains(align,align_t::BOTTOM) )
		ret.y = range.y+(range.h-obj.h)/2;
	else if( contains(align,align_t::TOP) )
		ret.y = range.y;
	else if( contains(align,align_t::BOTTOM) )
		ret.y = range.y+(range.h-obj.h);
	else
		ret.y = range.y+(range.h-obj.h)/2;
	
	if( contains( align,align_t::LEFT ) && contains(align,align_t::RIGHT) )
		ret.x = range.x+(range.w-obj.w)/2;
	else if( contains(align,align_t::LEFT) )
		ret.x = range.x;
	else if( contains(align,align_t::RIGHT) )
		ret.x = range.x+(range.w-obj.w);
	else
		ret.x = range.x+(range.w-obj.w)/2;
	return ret;
}



typedef const char* fontname;

struct Theme {

	static Theme*& instance() {
		static Theme* instance = nullptr;
		return instance;
	}
	static	void setTheme(Theme* t);
	static	const Theme& getCurrentTheme();
	virtual ~Theme(){}
	
	virtual NVGcolor  	_color_background						()const=0;
	virtual float		_pt_label								()const=0;
	virtual NVGcolor  	_color_label							()const=0;
	virtual fontname	_font_label								()const=0;
	virtual NVGcolor 	_color_panel							()const=0;
	virtual NVGcolor	_color_panel_separator					()const=0;
	virtual NVGcolor	_color_list_box							()const=0;
	virtual NVGcolor	_color_list_box_unfocussed				()const=0;
	virtual NVGcolor	_color_button_bound						()const=0;
	virtual NVGcolor	_color_button_bound_engaged				()const=0;
	virtual NVGcolor	_color_button_shade_pushed				()const=0;
	virtual NVGcolor	_color_button_shade_engaged				()const=0;
	virtual NVGcolor	_color_button_fill						()const=0;
	virtual NVGcolor	_color_button_fill_pressed				()const=0;
	virtual float		_width_button_bound						()const=0;
	virtual fontname	_font_menuitem							()const=0;
	virtual float		_size_scroller_offset					()const=0;
	virtual float		_size_scroller_offset2					()const=0;
	virtual float		_size_scroller_thickness				()const=0;
	virtual float		_size_scroller_thickness2				()const=0;
	virtual NVGcolor	_color_scroll_indicator					()const=0;
	virtual float		_size_scroll_indicator_arrow_height 	()const=0;
	virtual float		_size_scroll_indicator_arrow_width		()const=0;
	virtual NVGcolor	_size_scroller_background				()const=0;
	virtual float		_size_split_min							()const=0;
	virtual float		_size_property_label_offset				()const=0;
	virtual NVGcolor	_color_toolbar_fill_unfocused			()const=0;
	virtual NVGcolor	_color_toolbar_fill_line1				()const=0;
	virtual NVGcolor	_color_toolbar_fill_line2				()const=0;
	virtual NVGcolor	_color_toolbar_fill_grad1				()const=0;
	virtual NVGcolor	_color_toolbar_fill_grad2				()const=0;
	virtual NVGcolor	_color_toolbar_fill_line3				()const=0;
	virtual NVGcolor	_color_toolbar_fill_line4				()const=0;
	virtual NVGcolor	_color_statusbar_fill_top				()const=0;
	virtual float		_width_panel_separator					()const=0;
	virtual NVGcolor 	_color_menupan_background				()const=0;
	virtual NVGcolor	_color_menupan_separator				()const=0;
	virtual NVGcolor	_color_menupan_bound					()const=0;
	virtual NVGcolor  	_color_menupan_fill_under_item			()const=0;
	virtual NVGcolor	_color_menu_text						()const=0;
	virtual NVGcolor	_color_menu_text_under_item				()const=0;
	virtual float		_pt_menu_text							()const=0;
	virtual float		_size_menupan_separator_height			()const=0;
	virtual float		_size_menupan_menuitem_height			()const=0;
	virtual float		_size_menupan_shadow_width				()const=0;
	virtual float		_size_menupan_shadow_offset_y			()const=0;
	virtual float		_radius_menupan							()const=0;
	virtual float		_radius_popupbox						()const=0;
	virtual float		_radius_button							()const=0;
	virtual float 		_size_button_height						()const=0;
	virtual float		_size_button_width						()const=0;
	virtual float		_size_toolbar_height					()const=0;
	virtual float		_size_statusbar_height					()const=0;
	virtual float		_size_options_box_horz_padding			()const=0;
	virtual float		_size_menupan_check_left_offset			()const=0;
	virtual float		_size_splitter_spacing					()const=0;
	virtual float		_size_menupan_padding_horz				()const=0;
	virtual float		_size_menupan_padding_vert				()const=0;
	virtual sz2_t		_dim_check_action_size					()const=0;
	virtual sz2_t		_dim_options_action_min_size			()const=0;
	virtual	sz2_t		_size_optionbox_arrow					()const=0;
	virtual	pos_t		_vec_optionbox_arrow_offset				()const=0;
	virtual NVGcolor	_color_targetted_glow					()const=0;
	virtual float		_size_button_group_check				()const=0;
	virtual NVGcolor	_color_tooltip_box						()const=0;
	virtual NVGcolor	_color_tooltip_bound					()const=0;
	virtual float		_width_tooltip_bound					()const=0;
	virtual fontname	_font_tooltip_text						()const=0;
	virtual float		_pt_tooltip_text						()const=0;
	virtual NVGcolor	_color_tooltip_text						()const=0;
	virtual float		_radius_tooltip_box						()const=0;
	virtual float		_size_tooltip_padding					()const=0;
	virtual float		_size_slider_ticks_minor				()const=0;
	virtual float		_size_slider_ticks_major				()const=0;
	virtual float		_size_slider_ticks_fine					()const=0;
	virtual float		_size_slider_padding					()const=0;
	virtual float		_size_slider_bar_height					()const=0;
	virtual float		_size_slider_tick_minWidth				()const=0;
	virtual pos_t		_vec_tooltip_offset						()const=0;
	virtual NVGcolor	_color_f_button_bound					(shade_state_t s)const=0;
	virtual NVGcolor	_color_f_button_fill_over				(shade_state_t s)const=0;
	virtual float		_alpha_f_label							(shade_state_t s)const=0;
	virtual NVGcolor	_color_f_label							(shade_state_t s)const=0;
	virtual float		_alpha_f_button_fill					(shade_state_t s)const=0;
	virtual NVGcolor	_color_f_button_fill					(shade_state_t s)const=0;
	virtual float		_radius_f_slider_cursor					(slide_type_t type)const=0;
	virtual float		_pos_slider_number						(slide_type_t type,const rct_t& r)const=0;
	virtual float		_pos_f_slider_y							(slide_type_t type,const rct_t& r)const=0;
	virtual float		_size_options_button_width				(const sz2_t& r)const=0;
	virtual float		_size_options_arrow_hwidth				(const sz2_t& r)const=0;
	virtual float		_size_options_arrow_y_offset			(const sz2_t& r)const=0;
	virtual float		_size_options_arrow_height				(const sz2_t& r)const=0;

	virtual rct_t		_rect_menuitem_expandable_arrow_box		(const rct_t& r)const=0;
	virtual	rct_t		_rect_optionbox_arrow					(const rct_t& r)const=0;
	virtual float		_pos_slider_tick						(const rct_t& r)const=0;
	virtual sz2_t		_measure_text_label						(NVGcontext* vg, const str_t& s, float pt)const=0;
	virtual sz2_t		_measure_menuitem						(NVGcontext* vg, const str_t& s, bool sep)const=0;
	virtual sz2_t		_measure_tooltip_text					(NVGcontext* vg, const str_t& s)const=0;
	virtual sz2_t		_measure_textinputbase_text				(NVGcontext* vg, const str_t& s)const=0;
	virtual bool		_test_scrollbar_horz					(const rct_t& r, const pos_t& p)const=0;
	virtual bool		_test_scrollbar_vert					(const rct_t& r, const pos_t& p)const=0;
	virtual void		_draw_popupbox_box						(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_menupan_box						(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_menupan_separator					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_menupan_box_over					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_toolbar_box_base					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box						(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box_left					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box_right					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box_top					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box_bottom					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_button_box_middle					(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_group								(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_scroll_indicator_top				(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_scroll_indicator_bottom			(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_scroll_indicator_left				(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_scroll_indicator_right			(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_scroll_indicator_left				(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_scroll_indicator_right			(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_scroll_indicator_top				(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_scroll_indicator_bottom			(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_imagelabel						(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_path_menupan_box						(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_menupan_under_item_fill			(NVGcontext* vg, const rct_t& r)const=0;
	virtual void		_draw_toolbar_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_statusbar_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_options_control					(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_optionbox_arrow					(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_options_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_check_box							(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_check_checked						(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_textinputbase_box					(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_draw_button_group_check				(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual	void		_draw_radio_button_group_box			(NVGcontext* vg, const rct_t& r, shade_state_t s)const=0;
	virtual void		_path_separator_vert					(NVGcontext* vg, const rct_t& r, float y)const=0;
	virtual void		_path_separator_horz					(NVGcontext* vg, const rct_t& r, float x)const=0;
	virtual void		_draw_splitter_separator_horz			(NVGcontext* vg, const rct_t& r, float x) const=0;
	virtual void		_draw_splitter_separator_vert			(NVGcontext* vg, const rct_t& r, float y) const=0;
	virtual void		_path_button_box						(NVGcontext* vg, const rct_t& r, box_type_t boxType)const=0;
	virtual void		_draw_menupan_checked_item_check		(NVGcontext* vg, const rct_t& r, bool under)const=0;
	virtual void		_draw_menuitem_expandable_arrow			(NVGcontext* vg, const rct_t& r, bool state, bool disabled)const=0;
	virtual void		_draw_button_box_over					(NVGcontext* vg, const rct_t& r, shade_state_t state, box_type_t boxType)const=0;
	virtual void		_draw_button_box						(NVGcontext* vg, const rct_t& r, shade_state_t state, box_type_t boxType)const=0;
	virtual void		_draw_imagelabel						(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state)const=0;
	virtual void		_draw_button_box_image					(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state, box_type_t boxType)  const=0;
	virtual void		_draw_text_label						(NVGcontext* vg, const rct_t& r, const NVGcolor& color, const str_t& str, float pt, align_t align, shade_state_t state )const=0;
	virtual void		_path_scrollbar_horz					(NVGcontext* vg, const rct_t& r, float scale, float total, float delta)const=0;
	virtual void		_path_scrollbar_vert					(NVGcontext* vg, const rct_t& r, float scale, float total, float delta)const=0;
	virtual void		_draw_scrollbar_horz					(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount)const=0;
	virtual void		_draw_scrollbar_vert					(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount)const=0;
	virtual void		_draw_menuitem							(NVGcontext* vg, const rct_t& r, const str_t& str, align_t align, bool state, bool disabled, bool separator)const=0;
	virtual void		_draw_options_text						(NVGcontext* vg, const rct_t& r, const str_t& str, shade_state_t state)const=0;

	virtual void		_draw_tooltip							(NVGcontext* vg,const rct_t& p,float dx,const str_t& str,float alpha)const=0;
	virtual void		_draw_textinputbase_selection			(NVGcontext* vg,const rct_t& r,const rct_t& sr,float x0,float x1, shade_state_t state)const=0;
	virtual void		_draw_textinputbase_cursor				(NVGcontext* vg,const rct_t& r,const rct_t& sr,float x,shade_state_t state)const=0;
	virtual void		_draw_textinputbase_text				(NVGcontext* vg,const rct_t& r,const rct_t& sr,const str_t& str,align_t align,shade_state_t state)const=0;

	virtual void		_draw_slider_cursor						(NVGcontext* vg,slide_type_t type,const rct_t& r,float x,shade_state_t s)const=0;
	virtual void		_draw_slider_ticks_minor				(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const=0;
	virtual void		_draw_slider_ticks_major				(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const=0;
	virtual void		_draw_slider_ticks_fine					(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const=0;
	virtual void		_draw_slider_numbers					(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step, float valueOffset,float valueStep,double base)const=0;
	virtual void		_draw_slider_bar						(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s) const=0;
};

inline	int _alignment_to_NVGAlign( align_t a ) {
	int halign = NVG_ALIGN_CENTER;
	int valign = NVG_ALIGN_MIDDLE;
	
	if( contains(a,align_t::LEFT) && contains(a,align_t::RIGHT) )	halign = NVG_ALIGN_CENTER;
	else if( contains(a,align_t::LEFT) )							halign = NVG_ALIGN_LEFT;
	else if( contains(a,align_t::RIGHT) )							halign = NVG_ALIGN_RIGHT;
	
	if( contains(a,align_t::TOP)  && contains(a,align_t::BOTTOM))	valign = NVG_ALIGN_MIDDLE;
	else if( contains(a,align_t::TOP)    )							valign = NVG_ALIGN_TOP;
	else if( contains(a,align_t::BOTTOM) )							valign = NVG_ALIGN_BOTTOM;
	return halign|valign;
}

} // namespace JGL2

#include "_ThemeDef.hpp"

namespace JGL2 {

inline void Theme::setTheme(Theme* t){
	if( instance() ) delete instance();
	instance() = t;
};
inline const Theme& Theme::getCurrentTheme() {
	if( !instance()) setTheme(new ThemeDef());
	return *instance();
}


inline float _size_property_label_offset() {
	return Theme::getCurrentTheme()._size_property_label_offset();
}
inline NVGcolor _color_label() {
	return Theme::getCurrentTheme()._color_label();
}
inline NVGcolor _color_targetted_glow() {
	return Theme::getCurrentTheme()._color_targetted_glow();
}
inline float _size_button_group_check() {
	return Theme::getCurrentTheme()._size_button_group_check();
}
inline NVGcolor _color_menu_text_under_item() {
	return Theme::getCurrentTheme()._color_menupan_fill_under_item();
}
inline NVGcolor _color_f_label(shade_state_t s) {
	return Theme::getCurrentTheme()._color_f_label(s);
}
inline NVGcolor _color_f_button_fill(shade_state_t s) {
	return Theme::getCurrentTheme()._color_f_button_fill(s);
}
inline NVGcolor _color_f_button_bound(shade_state_t s) {
	return Theme::getCurrentTheme()._color_f_button_bound(s);
}
inline NVGcolor _color_button_shade_pushed() {
	return Theme::getCurrentTheme()._color_button_shade_pushed();
}

inline fontname _font_menuitem() {
	return Theme::getCurrentTheme()._font_menuitem();
}
inline float _pt_label() {
	return Theme::getCurrentTheme()._pt_label();
}
inline void _draw_statusbar_box(NVGcontext* vg, const rct_t& r, shade_state_t s ) {
	Theme::getCurrentTheme()._draw_statusbar_box(vg, r, s);
}
inline void _draw_menuitem(NVGcontext* vg, const rct_t& r, const str_t& l, align_t align, bool state, bool disabled, bool isSeparator ) {
	Theme::getCurrentTheme()._draw_menuitem(vg, r, l, align, state, disabled, isSeparator);
}
inline void _draw_menuitem_expandable_arrow(NVGcontext* vg, const rct_t& r, bool state, bool disabled ) {
	Theme::getCurrentTheme()._draw_menuitem_expandable_arrow(vg, r, state, disabled );
}

inline sz2_t _measure_menuitem(NVGcontext* vg, const str_t& l, bool isSeparator ) {
	return Theme::getCurrentTheme()._measure_menuitem(vg, l, isSeparator);
}
inline void _draw_menupan_box(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_menupan_box(vg, r);
}
inline void _draw_menupan_box_over(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_menupan_box_over(vg, r);
}

inline void _draw_menupan_under_item_fill(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_menupan_under_item_fill(vg, r);
}
inline void _draw_menupan_checked_item_check(NVGcontext* vg, const rct_t& r, bool under) {
	Theme::getCurrentTheme()._draw_menupan_checked_item_check(vg, r, under);
}
inline void _draw_menupan_separator(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_menupan_separator(vg, r);
}
inline void _draw_imagelabel(NVGcontext* vg, const rct_t& r, const NVGpaint& p, shade_state_t s) {
	Theme::getCurrentTheme()._draw_imagelabel(vg, r, p, s);
}
inline sz2_t _measure_text_label(NVGcontext* vg, const str_t& l, float pt ) {
	return Theme::getCurrentTheme()._measure_text_label(vg, l, pt);
}
inline void _draw_text_label(NVGcontext* vg, const rct_t& r, const NVGcolor& c, const str_t& l, float pt, align_t a, shade_state_t state) {
	Theme::getCurrentTheme()._draw_text_label(vg, r, c, l, pt, a, state);
}



inline float _size_options_button_width(const sz2_t& r) {
	return Theme::getCurrentTheme()._size_options_button_width(r);
}
inline float _size_options_arrow_y_offset(const sz2_t& r) {
	return Theme::getCurrentTheme()._size_options_arrow_y_offset(r);
}
inline float _size_options_arrow_height(const sz2_t& r) {
	return Theme::getCurrentTheme()._size_options_arrow_height(r);
}
inline float _size_options_arrow_hwidth(const sz2_t& r) {
	return Theme::getCurrentTheme()._size_options_arrow_hwidth(r);
}

inline void _draw_optionbox_arrow(NVGcontext* vg, const rct_t& r, shade_state_t state ) {
	Theme::getCurrentTheme()._draw_optionbox_arrow(vg,r,state);
}


inline rct_t _rect_menuitem_expandable_arrow_box(const rct_t& r) {
	return Theme::getCurrentTheme()._rect_menuitem_expandable_arrow_box(r);
}


inline float _size_menupan_menuitem_height() {
	return Theme::getCurrentTheme()._size_menupan_menuitem_height();
}
inline float _pt_menu_text() {
	return Theme::getCurrentTheme()._pt_menu_text();
}
inline float _size_options_box_horz_padding() {
	return Theme::getCurrentTheme()._size_options_box_horz_padding();
}
inline NVGcolor _color_panel() {
	return Theme::getCurrentTheme()._color_panel();
}
inline NVGcolor _color_background() {
	return Theme::getCurrentTheme()._color_background();
}
inline float _size_button_height() {
	return Theme::getCurrentTheme()._size_button_height();
}
inline float _size_button_width() {
	return Theme::getCurrentTheme()._size_button_width();
}
inline float _size_toolbar_height() {
	return Theme::getCurrentTheme()._size_toolbar_height();
}
inline float _size_statusbar_height() {
	return Theme::getCurrentTheme()._size_statusbar_height();
}
inline float _size_split_min() {
	return Theme::getCurrentTheme()._size_split_min();
}
inline float _size_scroller_offset() {
	return Theme::getCurrentTheme()._size_scroller_offset();
}
inline float _size_splitter_spacing() {
	return Theme::getCurrentTheme()._size_splitter_spacing();
}
inline float _size_menupan_padding_horz() {
	return Theme::getCurrentTheme()._size_menupan_padding_horz();
}
inline float _size_menupan_padding_vert() {
	return Theme::getCurrentTheme()._size_menupan_padding_vert();
}
inline bool _test_scrollbar_horz(const rct_t& r, const pos_t& pt) {
	return Theme::getCurrentTheme()._test_scrollbar_horz(r,pt);
}
inline bool _test_scrollbar_vert(const rct_t& r, const pos_t& pt) {
	return Theme::getCurrentTheme()._test_scrollbar_vert(r,pt);
}


inline sz2_t _dim_options_action_min_size() {
	return Theme::getCurrentTheme()._dim_options_action_min_size();
}
inline sz2_t _dim_check_action_size() {
	return Theme::getCurrentTheme()._dim_check_action_size();
}






inline void _draw_popupbox_box(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_popupbox_box(vg, r);
}
inline void _draw_splitter_separator_horz(NVGcontext* vg, const rct_t& r, float x) {
	Theme::getCurrentTheme()._draw_splitter_separator_horz(vg, r, x);
}
inline void _draw_splitter_separator_vert(NVGcontext* vg, const rct_t& r, float y) {
	Theme::getCurrentTheme()._draw_splitter_separator_vert(vg, r, y);
}
inline void _draw_scroll_indicator_left(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_scroll_indicator_left(vg, r);
}
inline void _draw_scroll_indicator_right(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_scroll_indicator_right(vg, r);
}
inline void _draw_scroll_indicator_top(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_scroll_indicator_top(vg, r);
}
inline void _draw_scroll_indicator_bottom(NVGcontext* vg, const rct_t& r) {
	Theme::getCurrentTheme()._draw_scroll_indicator_bottom(vg, r);
}
inline void _draw_scrollbar_horz(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float am) {
	Theme::getCurrentTheme()._draw_scrollbar_horz(vg, r, alpha, sz, total, am);
}
inline void _draw_scrollbar_vert(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float am) {
	Theme::getCurrentTheme()._draw_scrollbar_vert(vg, r, alpha, sz, total, am);
}



inline void _draw_toolbar_box(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_toolbar_box(vg, r, s);
}
inline void _draw_button_box(NVGcontext* vg, const rct_t& r, shade_state_t s, box_type_t t) {
	Theme::getCurrentTheme()._draw_button_box(vg, r, s, t);
}
inline void _draw_button_box_over(NVGcontext* vg, const rct_t& r, shade_state_t s, box_type_t t) {
	Theme::getCurrentTheme()._draw_button_box_over(vg, r, s, t);
}
inline void _draw_button_box_image(NVGcontext* vg, const rct_t& r, const NVGpaint& p, shade_state_t s, box_type_t t) {
	Theme::getCurrentTheme()._draw_button_box_image(vg, r, p, s, t);
}
inline void _draw_button_group_check( NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_button_group_check(vg,r,s);
}

inline void _draw_radio_button_group_box(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_radio_button_group_box(vg, r, s);
}




inline float _size_tooltip_padding() {
	return Theme::getCurrentTheme()._size_tooltip_padding();
}

inline void _draw_options_box(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_options_box(vg, r, s);
}
inline void _draw_options_text(NVGcontext* vg, const rct_t& r, const str_t& l, shade_state_t s) {
	Theme::getCurrentTheme()._draw_options_text(vg, r, l, s);
}
inline void _draw_options_control(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_options_control(vg, r, s);
}
inline void _draw_check_box(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_check_box(vg, r, s);
}
inline void _draw_check_checked(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_check_checked(vg, r, s);
}
inline void _draw_tooltip(NVGcontext* vg, const rct_t& r, float dx, const str_t& str, float alpha ) {
	Theme::getCurrentTheme()._draw_tooltip(vg, r, dx, str, alpha);
}
inline sz2_t	_measure_tooltip_text(NVGcontext* vg,  const str_t& s) {
	return Theme::getCurrentTheme()._measure_tooltip_text(vg, s);
}

inline pos_t	_vec_tooltip_offset() {
	return Theme::getCurrentTheme()._vec_tooltip_offset();
}


inline void _draw_textinputbase_box(NVGcontext* vg, const rct_t& r, shade_state_t s) {
	Theme::getCurrentTheme()._draw_textinputbase_box(vg,r,s);
}
inline void _draw_textinputbase_selection(NVGcontext* vg, const rct_t& r, const rct_t& sr, float x0, float x1, shade_state_t s) {
	Theme::getCurrentTheme()._draw_textinputbase_selection(vg,r,sr,x0,x1,s);
}
inline void _draw_textinputbase_cursor(NVGcontext* vg, const rct_t& r, const rct_t& sr, float x, shade_state_t s) {
	Theme::getCurrentTheme()._draw_textinputbase_cursor(vg,r,sr,x,s);
}
inline void _draw_textinputbase_text(NVGcontext* vg, const rct_t& r, const rct_t& sr, const str_t& str, align_t align, shade_state_t s) {
	Theme::getCurrentTheme()._draw_textinputbase_text(vg,r,sr,str,align,s);
}
inline sz2_t _measure_textinputbase_text(NVGcontext* vg, const str_t& str) {
	return Theme::getCurrentTheme()._measure_textinputbase_text(vg,str);
}




inline float _pos_slider_tick (const rct_t& r) {
	return Theme::getCurrentTheme()._pos_slider_tick(r);
}
inline float _size_slider_padding () {
	return Theme::getCurrentTheme()._size_slider_padding();
}
inline float	_radius_f_slider_cursor(slide_type_t type) {
	return Theme::getCurrentTheme()._radius_f_slider_cursor(type);
}
inline float	_pos_f_slider_y(slide_type_t type,const rct_t&r) {
	return Theme::getCurrentTheme()._pos_f_slider_y(type,r);
}
inline float	_pos_slider_number(slide_type_t type,const rct_t&r) {
	return Theme::getCurrentTheme()._pos_slider_number(type,r);
}



inline void		_draw_slider_cursor(NVGcontext* vg,slide_type_t type,const rct_t& r,float x,shade_state_t s) {
	return Theme::getCurrentTheme()._draw_slider_cursor(vg,type,r,x,s);
}
inline void		_draw_slider_ticks_major(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step) {
	return Theme::getCurrentTheme()._draw_slider_ticks_major(vg,type,r,s,offset,step);
}
inline void		_draw_slider_ticks_minor(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step) {
	return Theme::getCurrentTheme()._draw_slider_ticks_minor(vg,type,r,s,offset,step);
}
inline void		_draw_slider_ticks_fine(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step) {
	return Theme::getCurrentTheme()._draw_slider_ticks_fine(vg,type,r,s,offset,step);
}
inline void		_draw_slider_numbers(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step, float valueOffset,float valueStep,double base) {
	return Theme::getCurrentTheme()._draw_slider_numbers(vg,type,r,s,offset,step,valueOffset,valueStep,base);
}
inline void _draw_slider_bar(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s)  {
	return Theme::getCurrentTheme()._draw_slider_bar(vg,type,r,s);
}


inline NVGcolor _color_tooltip_box() {
	return Theme::getCurrentTheme()._color_tooltip_box();
}
inline NVGcolor _color_tooltip_bound() {
	return Theme::getCurrentTheme()._color_tooltip_bound();
}
inline NVGcolor _color_tooltip_text() {
	return Theme::getCurrentTheme()._color_tooltip_text();
}
inline float _radius_tooltip_box() {
	return Theme::getCurrentTheme()._radius_tooltip_box();
}
inline float _width_tooltip_bound() {
	return Theme::getCurrentTheme()._width_tooltip_bound();
}
inline float _pt_tooltip_text() {
	return Theme::getCurrentTheme()._pt_tooltip_text();
}
inline const char* _font_tooltip_text() {
	return Theme::getCurrentTheme()._font_tooltip_text();
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _Theme_h */
