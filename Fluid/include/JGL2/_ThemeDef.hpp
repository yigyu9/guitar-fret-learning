//
//  _ThemeDef.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2__ThemeDef_h
#define JGL2__ThemeDef_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#include <JGL2/_Theme.hpp>
#include <JGL2/_Draw.hpp>

namespace JGL2 {

struct ThemeDef : public Theme {

	virtual NVGcolor  	_color_background						()const override;
	virtual float		_pt_label								()const override;
	virtual NVGcolor  	_color_label							()const override;
	virtual fontname	_font_label								()const override;
	virtual NVGcolor 	_color_panel							()const override;
	virtual NVGcolor	_color_panel_separator					()const override;
	virtual NVGcolor	_color_list_box							()const override;
	virtual NVGcolor	_color_list_box_unfocussed				()const override;
	virtual NVGcolor	_color_button_bound						()const override;
	virtual NVGcolor	_color_button_bound_engaged				()const override;
	virtual NVGcolor	_color_button_shade_pushed				()const override;
	virtual NVGcolor	_color_button_shade_engaged				()const override;
	virtual NVGcolor	_color_button_fill						()const override;
	virtual NVGcolor	_color_button_fill_pressed				()const override;
	virtual float		_width_button_bound						()const override;
	virtual fontname	_font_menuitem							()const override;
	virtual float		_size_scroller_offset					()const override;
	virtual float		_size_scroller_offset2					()const override;
	virtual float		_size_scroller_thickness				()const override;
	virtual float		_size_scroller_thickness2				()const override;
	virtual NVGcolor	_color_scroll_indicator					()const override;
	virtual float		_size_scroll_indicator_arrow_height 	()const override;
	virtual float		_size_scroll_indicator_arrow_width		()const override;
	virtual NVGcolor	_size_scroller_background				()const override;
	virtual float		_size_split_min							()const override;
	virtual float		_size_property_label_offset				()const override;
	virtual NVGcolor	_color_toolbar_fill_unfocused			()const override;
	virtual NVGcolor	_color_toolbar_fill_line1				()const override;
	virtual NVGcolor	_color_toolbar_fill_line2				()const override;
	virtual NVGcolor	_color_toolbar_fill_grad1				()const override;
	virtual NVGcolor	_color_toolbar_fill_grad2				()const override;
	virtual NVGcolor	_color_toolbar_fill_line3				()const override;
	virtual NVGcolor	_color_toolbar_fill_line4				()const override;
	virtual NVGcolor	_color_statusbar_fill_top				()const override;
	virtual float		_width_panel_separator					()const override;
	virtual NVGcolor 	_color_menupan_background				()const override;
	virtual NVGcolor	_color_menupan_separator				()const override;
	virtual NVGcolor	_color_menupan_bound					()const override;
	virtual NVGcolor  	_color_menupan_fill_under_item			()const override;
	virtual NVGcolor	_color_menu_text						()const override;
	virtual NVGcolor	_color_menu_text_under_item				()const override;
	virtual float		_pt_menu_text							()const override;
	virtual float		_size_menupan_separator_height			()const override;
	virtual float		_size_menupan_menuitem_height			()const override;
	virtual float		_size_menupan_shadow_width				()const override;
	virtual float		_size_menupan_shadow_offset_y			()const override;
	virtual float		_radius_menupan							()const override;
	virtual float		_radius_popupbox						()const override;
	virtual float		_radius_button							()const override;
	virtual float 		_size_button_height						()const override;
	virtual float		_size_button_width						()const override;
	virtual float		_size_toolbar_height					()const override;
	virtual float		_size_statusbar_height					()const override;
	virtual float		_size_options_box_horz_padding			()const override;
	virtual float		_size_menupan_check_left_offset			()const override;
	virtual float		_size_splitter_spacing					()const override;
	virtual float		_size_menupan_padding_horz				()const override;
	virtual float		_size_menupan_padding_vert				()const override;
	virtual sz2_t		_dim_check_action_size					()const override;
	virtual sz2_t		_dim_options_action_min_size			()const override;
	virtual	sz2_t		_size_optionbox_arrow					()const override;
	virtual	pos_t		_vec_optionbox_arrow_offset				()const override;
	virtual NVGcolor	_color_targetted_glow					()const override;
	virtual float		_size_button_group_check				()const override;
	virtual NVGcolor	_color_tooltip_box						()const override;
	virtual NVGcolor	_color_tooltip_bound					()const override;
	virtual float		_width_tooltip_bound					()const override;
	virtual fontname	_font_tooltip_text						()const override;
	virtual float		_pt_tooltip_text						()const override;
	virtual NVGcolor	_color_tooltip_text						()const override;
	virtual float		_radius_tooltip_box						()const override;
	virtual float		_size_tooltip_padding					()const override;
	virtual float		_size_slider_ticks_minor				()const override;
	virtual float		_size_slider_ticks_major				()const override;
	virtual float		_size_slider_ticks_fine					()const override;
	virtual float		_size_slider_padding					()const override;
	virtual float		_size_slider_bar_height					()const override;
	virtual float		_size_slider_tick_minWidth				()const override;
	virtual pos_t		_vec_tooltip_offset						()const override;
	virtual NVGcolor	_color_f_button_bound					(shade_state_t s)const override;
	virtual NVGcolor	_color_f_button_fill_over				(shade_state_t s)const override;
	virtual float		_alpha_f_label							(shade_state_t s)const override;
	virtual NVGcolor	_color_f_label							(shade_state_t s)const override;
	virtual float		_alpha_f_button_fill					(shade_state_t s)const override;
	virtual NVGcolor	_color_f_button_fill					(shade_state_t s)const override;
	virtual float		_radius_f_slider_cursor					(slide_type_t type)const override;
	virtual float		_pos_slider_number						(slide_type_t type,const rct_t& r)const override;
	virtual float		_pos_f_slider_y							(slide_type_t type,const rct_t& r)const override;
	virtual float		_size_options_button_width				(const sz2_t& r)const override;
	virtual float		_size_options_arrow_hwidth				(const sz2_t& r)const override;
	virtual float		_size_options_arrow_y_offset			(const sz2_t& r)const override;
	virtual float		_size_options_arrow_height				(const sz2_t& r)const override;
	virtual rct_t		_rect_menuitem_expandable_arrow_box		(const rct_t& r)const override;
	virtual	rct_t		_rect_optionbox_arrow					(const rct_t& r)const override;
	virtual float		_pos_slider_tick						(const rct_t& r)const override;
	virtual sz2_t		_measure_text_label						(NVGcontext* vg, const str_t& s, float pt)const override;
	virtual sz2_t		_measure_menuitem						(NVGcontext* vg, const str_t& s, bool sep)const override;
	virtual sz2_t		_measure_tooltip_text					(NVGcontext* vg, const str_t& s)const override;
	virtual sz2_t		_measure_textinputbase_text				(NVGcontext* vg, const str_t& s)const override;
	virtual bool		_test_scrollbar_horz					(const rct_t& r, const pos_t& p)const override;
	virtual bool		_test_scrollbar_vert					(const rct_t& r, const pos_t& p)const override;
	virtual void		_draw_popupbox_box						(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_menupan_box						(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_menupan_separator					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_menupan_box_over					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_toolbar_box_base					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box						(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box_left					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box_right					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box_top					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box_bottom					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_button_box_middle					(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_group								(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_scroll_indicator_top				(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_scroll_indicator_bottom			(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_scroll_indicator_left				(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_scroll_indicator_right			(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_scroll_indicator_left				(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_scroll_indicator_right			(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_scroll_indicator_top				(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_scroll_indicator_bottom			(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_imagelabel						(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_path_menupan_box						(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_menupan_under_item_fill			(NVGcontext* vg, const rct_t& r)const override;
	virtual void		_draw_toolbar_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_statusbar_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_options_control					(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_optionbox_arrow					(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_options_box						(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_check_box							(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_check_checked						(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_textinputbase_box					(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_draw_button_group_check				(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual	void		_draw_radio_button_group_box			(NVGcontext* vg, const rct_t& r, shade_state_t s)const override;
	virtual void		_path_separator_vert					(NVGcontext* vg, const rct_t& r, float y)const override;
	virtual void		_path_separator_horz					(NVGcontext* vg, const rct_t& r, float x)const override;
	virtual void		_draw_splitter_separator_horz			(NVGcontext* vg, const rct_t& r, float x) const override;
	virtual void		_draw_splitter_separator_vert			(NVGcontext* vg, const rct_t& r, float y) const override;
	virtual void		_path_button_box						(NVGcontext* vg, const rct_t& r, box_type_t boxType)const override;
	virtual void		_draw_menupan_checked_item_check		(NVGcontext* vg, const rct_t& r, bool under)const override;
	virtual void		_draw_menuitem_expandable_arrow			(NVGcontext* vg, const rct_t& r, bool state, bool disabled)const override;
	virtual void		_draw_button_box_over					(NVGcontext* vg, const rct_t& r, shade_state_t state, box_type_t boxType)const override;
	virtual void		_draw_button_box						(NVGcontext* vg, const rct_t& r, shade_state_t state, box_type_t boxType)const override;
	virtual void		_draw_imagelabel						(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state)const override;
	virtual void		_draw_button_box_image					(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state, box_type_t boxType)  const override;
	virtual void		_draw_text_label						(NVGcontext* vg, const rct_t& r, const NVGcolor& color, const str_t& str, float pt, align_t align, shade_state_t state )const override;
	virtual void		_path_scrollbar_horz					(NVGcontext* vg, const rct_t& r, float scale, float total, float delta)const override;
	virtual void		_path_scrollbar_vert					(NVGcontext* vg, const rct_t& r, float scale, float total, float delta)const override;
	virtual void		_draw_scrollbar_horz					(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount)const override;
	virtual void		_draw_scrollbar_vert					(NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount)const override;
	virtual void		_draw_menuitem							(NVGcontext* vg, const rct_t& r, const str_t& str, align_t align, bool state, bool disabled, bool separator)const override;
	virtual void		_draw_options_text						(NVGcontext* vg, const rct_t& r, const str_t& str, shade_state_t state)const override;
	virtual void		_draw_tooltip							(NVGcontext* vg,const rct_t& p,float dx,const str_t& str,float alpha)const override;
	virtual void		_draw_textinputbase_selection			(NVGcontext* vg,const rct_t& r,const rct_t& sr,float x0,float x1, shade_state_t state)const override;
	virtual void		_draw_textinputbase_cursor				(NVGcontext* vg,const rct_t& r,const rct_t& sr,float x,shade_state_t state)const override;
	virtual void		_draw_textinputbase_text				(NVGcontext* vg,const rct_t& r,const rct_t& sr,const str_t& str,align_t align,shade_state_t state)const override;
	virtual void		_draw_slider_cursor						(NVGcontext* vg,slide_type_t type,const rct_t& r,float x,shade_state_t s)const override;
	virtual void		_draw_slider_ticks_minor				(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const override;
	virtual void		_draw_slider_ticks_major				(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const override;
	virtual void		_draw_slider_ticks_fine					(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const override;
	virtual void		_draw_slider_numbers					(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step, float valueOffset,float valueStep,double base)const override;
	virtual void		_draw_slider_bar						(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s) const override;
};



inline	NVGcolor	ThemeDef::_color_background						()const{ return {0.965f, 0.965f, 0.965f, 1.};}
inline	float		ThemeDef::_pt_label								()const{ return 13.f;}
inline	NVGcolor 	ThemeDef::_color_label							()const{ return {0,0,0,1};}
inline	fontname	ThemeDef::_font_label							()const{ return "system";}
inline	NVGcolor	ThemeDef::_color_panel							()const{ return { .926f,.926f,.926f,1};}
inline	NVGcolor	ThemeDef::_color_panel_separator				()const{ return {0.655f, 0.655f, 0.655f, 1};}
inline	NVGcolor	ThemeDef::_color_list_box						()const{ return {.843f,.867f,.88f,1};}
inline	NVGcolor	ThemeDef::_color_list_box_unfocussed			()const{ return {.914f,.942f,.96f,1};}
inline	NVGcolor	ThemeDef::_color_button_bound					()const{ return {.706f, .706f, .706f, 1};}
inline	NVGcolor	ThemeDef::_color_button_bound_engaged			()const{ return {.205f,.493f,1,.2f};}
inline	NVGcolor	ThemeDef::_color_button_shade_pushed			()const{ return {0,0,0,0.098f};}
//inline	NVGcolor	ThemeDef::_color_button_shade_engaged		()const{ return {.205f,.493f,1,.2f};}
inline	NVGcolor	ThemeDef::_color_button_shade_engaged			()const{ return {.205f,.493f,1,0.f};}
inline	NVGcolor	ThemeDef::_color_button_fill					()const{ return {.987f,.987f,.987f,1};}
inline	NVGcolor	ThemeDef::_color_button_fill_pressed			()const{ return {.89f,.89f,.89f,1};}
inline	float		ThemeDef::_width_button_bound					()const{ return 1.2f;}
inline	fontname	ThemeDef::_font_menuitem						()const{ return "system";}


inline	float		ThemeDef::_size_scroller_offset					()const{ return 2.f; }
inline	float		ThemeDef::_size_scroller_offset2				()const{ return 1.f; }
inline	float		ThemeDef::_size_scroller_thickness				()const{ return 3.f; }
inline	float		ThemeDef::_size_scroller_thickness2				()const{ return 7.f; }
inline	NVGcolor	ThemeDef::_color_scroll_indicator				()const{ return {0,0,0,.4f}; }
inline	float		ThemeDef::_size_scroll_indicator_arrow_height	()const{ return 3.f; }
inline	float		ThemeDef::_size_scroll_indicator_arrow_width	()const{ return 3.f; }
inline	NVGcolor	ThemeDef::_size_scroller_background				()const{ return {.987f,.987f,.987f,.4f}; }
inline	float		ThemeDef::_size_split_min						()const{ return 80.f; }
inline	float		ThemeDef::_size_property_label_offset			()const{ return 4.f; }
inline	float		ThemeDef::_size_splitter_spacing				()const{ return 1.f; }

inline	NVGcolor	ThemeDef::_color_toolbar_fill_unfocused			()const { return {0.965f, 0.965f, 0.965f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_line1				()const { return {0.957f, 0.957f, 0.957f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_line2				()const { return {0.922f, 0.922f, 0.922f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_grad1				()const { return {0.898f, 0.898f, 0.898f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_grad2				()const { return {0.804f, 0.804f, 0.804f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_line3				()const { return {0.745f, 0.745f, 0.745f, 1};}
inline	NVGcolor	ThemeDef::_color_toolbar_fill_line4				()const { return {0.655f, 0.655f, 0.655f, 1};}
inline	NVGcolor	ThemeDef::_color_statusbar_fill_top				()const { return {0.696f, 0.696f, 0.696f, 1};}

inline	float		ThemeDef::_width_panel_separator				()const { return 1.2f;}
inline	NVGcolor	ThemeDef::_color_menupan_background				()const { return {.987f,.987f,.987f,1};}
inline	NVGcolor	ThemeDef::_color_menupan_separator				()const { return {.839f,.859f,.876f,1};}
inline	NVGcolor	ThemeDef::_color_menupan_bound					()const { return {.839f,.859f,.876f,1};}
inline	NVGcolor	ThemeDef::_color_menupan_fill_under_item		()const { return {.302f,.600f,.992f,1.f};}
inline	NVGcolor	ThemeDef::_color_menu_text						()const { return {0,0,0,1};}
inline	NVGcolor	ThemeDef::_color_menu_text_under_item			()const { return {1,1,1,1};}
inline	float		ThemeDef::_pt_menu_text							()const { return 15.f;}
inline	float		ThemeDef::_size_menupan_separator_height		()const { return 12.f;}
inline	float		ThemeDef::_size_menupan_menuitem_height			()const { return 19.f;}
inline	float		ThemeDef::_size_menupan_shadow_width			()const { return 24.f;}
inline	float		ThemeDef::_size_menupan_shadow_offset_y			()const { return 8.f;}
inline	float		ThemeDef::_radius_menupan						()const { return 6.f;}
inline	float		ThemeDef::_radius_popupbox						()const { return 6.f;}
inline	float		ThemeDef::_radius_button						()const { return 5.f;}
inline	float		ThemeDef::_size_button_height					()const { return 24.f;}
inline	float		ThemeDef::_size_button_width					()const { return 38.f;}
inline	float		ThemeDef::_size_toolbar_height					()const { return 38.f;}
inline	float		ThemeDef::_size_statusbar_height				()const { return 25.f;}

inline	float		ThemeDef::_size_menupan_check_left_offset		()const { return 6.f;}
inline	float		ThemeDef::_size_options_box_horz_padding		()const { return 9.f;}

inline	sz2_t		ThemeDef::_dim_options_action_min_size			()const { return sz2_t(30.f,16.f); }
inline	sz2_t		ThemeDef::_dim_check_action_size				()const { return sz2_t(16.f,16.f); }


inline	float		ThemeDef::_size_menupan_padding_horz			()const { return 18.f; }
inline	float		ThemeDef::_size_menupan_padding_vert			()const { return 5.f; }

inline	NVGcolor	ThemeDef::_color_tooltip_box					()const { return {.8f,.82f,.85f,1}; }
inline	NVGcolor	ThemeDef::_color_tooltip_bound					()const { return {0,0,0,1}; }
inline	float		ThemeDef::_width_tooltip_bound					()const { return .4f; }
inline	fontname	ThemeDef::_font_tooltip_text					()const { return "system"; }
inline	float		ThemeDef::_pt_tooltip_text						()const { return 13.f; }
inline	NVGcolor	ThemeDef::_color_tooltip_text					()const { return {0,0,0,1}; }
inline	float		ThemeDef::_radius_tooltip_box					()const { return 1.5f; }
inline	float		ThemeDef::_size_tooltip_padding					()const { return 4.f; }
inline	pos_t		ThemeDef::_vec_tooltip_offset					()const { return pos_t(-20.f,15.f); }

inline	NVGcolor	ThemeDef::_color_targetted_glow					()const { return {.514f,.671f,.957f,1.f}; }
inline  float 		ThemeDef::_size_button_group_check				()const { return 14.f; }

inline	float		ThemeDef::_size_options_button_width			(const sz2_t& r)const {
	return std::min(24.f,r.h)*0.75f;// 18;
}
inline	float		ThemeDef::_size_options_arrow_hwidth			(const sz2_t& r)const {
	return std::min(24.f,r.h)*0.2f; //5;
}
inline	float		ThemeDef::_size_options_arrow_y_offset			(const sz2_t& r)const {
	return std::min(24.f,r.h)*0.2f; //5;
}
inline	float		ThemeDef::_size_options_arrow_height			(const sz2_t& r)const {
	return std::min(24.f,r.h)*0.2f; //5;
}
inline	sz2_t		ThemeDef::_size_optionbox_arrow					()const {
	return sz2_t(6,5);
}
inline	pos_t		ThemeDef::_vec_optionbox_arrow_offset			()const {
	return pos_t(-6,-8);
}
inline	rct_t		ThemeDef::_rect_optionbox_arrow					(const rct_t& r)const {
	return rct_t(r.br()+_vec_optionbox_arrow_offset(),_size_optionbox_arrow() );
}
inline	rct_t		ThemeDef::_rect_menuitem_expandable_arrow_box	(const rct_t& r)const {
	const pos_t arrow_offset = {-8,-2};
	const float arrow_width = 4;
	const float arrow_height = 6;
	rct_t b( r.x+r.w+arrow_offset.x, r.y+r.h/2-arrow_height/3.f+arrow_offset.y, arrow_width, arrow_height );
	return b;
}

inline	NVGcolor ThemeDef::_color_f_button_bound( shade_state_t s ) const {
	NVGcolor ret = _color_button_bound();
	if( contains(s, shade_state_t::ENGAGED ) )
		ret = _color_button_bound_engaged();
	if( contains(s, shade_state_t::WINDOW_UNFOCUSED ) )
		ret.a*=0.7f;
	return ret;
}

inline	NVGcolor ThemeDef::_color_f_button_fill_over( shade_state_t s ) const {
	NVGcolor ret = {0,0,0,0};
	if( contains(s, shade_state_t::ENGAGED ) )
		ret = _color_button_shade_engaged();
	if( contains(s, shade_state_t::PRESSED ) )
		ret = _color_button_shade_pushed();
	if( contains(s, shade_state_t::WINDOW_UNFOCUSED ) )
		ret.a*=0.7f;
	return ret;
}

inline	float ThemeDef::_alpha_f_label( shade_state_t s ) const {
	float alpha = 1.;
	if( contains(s, shade_state_t::WINDOW_UNFOCUSED ) ) {
		if( contains(s, shade_state_t::INACTIVE ) )
			alpha = 0.1f;
		else
			alpha = 0.3f;
	}
	else if( contains(s, shade_state_t::INACTIVE ) )
		alpha = 0.2f;
	return alpha;
}

inline	float ThemeDef::_alpha_f_button_fill( shade_state_t s ) const {
	float alpha = 1.;
	if( contains(s, shade_state_t::WINDOW_UNFOCUSED ) )
		alpha = 0.0f;
	return alpha;
}

inline	NVGcolor ThemeDef::_color_f_button_fill( shade_state_t s ) const {
	if( contains(s, shade_state_t::WINDOW_UNFOCUSED ) )
		return _color_background();
	return _color_button_fill();
}

inline	NVGcolor ThemeDef::_color_f_label(shade_state_t s) const {
	return nvgColorA( _color_label(), _alpha_f_label(s) );
}

inline	void ThemeDef::_draw_text_label(NVGcontext* vg, const rct_t& r, const NVGcolor& color, const str_t& str, float pt, align_t align, shade_state_t state ) const {
	nvgFontSize( vg, pt );
	nvgFontFace( vg, _font_label() );
	nvgFillColor( vg, nvgColorA( color, _alpha_f_label(state) ) );
	nvgTextAligned( vg, r, str, _alignment_to_NVGAlign( align ));
}

inline	sz2_t ThemeDef::_measure_text_label(NVGcontext* vg, const str_t& str, float pt ) const {
	return nvgMeasureText(vg, str, pt, _font_label());
}

inline	void ThemeDef::_path_button_box( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgRoundedRect( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_path_button_box_left( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgPathLeftRoundBox( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_path_button_box_right( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgPathRightRoundBox( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_path_button_box_top( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgPathTopRoundBox( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_path_button_box_bottom( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgPathBottomRoundBox( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_path_button_box_middle( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgRect( vg, r.x, r.y, r.w, r.h );
}

inline	void ThemeDef::_path_imagelabel( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgRoundedRect( vg, r.x, r.y, r.w, r.h, _radius_button() );
}
inline	void ThemeDef::_draw_imagelabel(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state) const {
	NVGpaint p = paint;
	float alpha = _alpha_f_label(state);
	p.innerColor.a *= alpha;
	p.outerColor.a *= alpha;
	nvgFillPaint(vg, p);
	_path_imagelabel(vg, r);
	nvgFill( vg );
}



inline	void ThemeDef::_path_group( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgRect( vg, r.x, r.y, r.w, r.h );
}

inline	void ThemeDef::_path_scroll_indicator_top( NVGcontext* vg, const rct_t& r ) const {
	float ww = r.w*.5f;
	nvgBeginPath(vg);
	nvgMoveTo(vg,ww,_size_scroller_offset());
	nvgLineTo(vg,ww-_size_scroll_indicator_arrow_height(),_size_scroller_offset()+_size_scroll_indicator_arrow_width());
	nvgLineTo(vg,ww+_size_scroll_indicator_arrow_height(),_size_scroller_offset()+_size_scroll_indicator_arrow_width());
	nvgClosePath(vg);
}

inline	void ThemeDef::_path_scroll_indicator_bottom( NVGcontext* vg, const rct_t& r ) const {
	float ww = r.w*.5f;
	nvgBeginPath(vg);
	nvgMoveTo(vg,ww,r.h-_size_scroller_offset());
	nvgLineTo(vg,ww-_size_scroll_indicator_arrow_height(),r.h-_size_scroller_offset()-_size_scroll_indicator_arrow_width());
	nvgLineTo(vg,ww+_size_scroll_indicator_arrow_height(),r.h-_size_scroller_offset()-_size_scroll_indicator_arrow_width());
	nvgClosePath(vg);
}

inline	void ThemeDef::_path_scroll_indicator_left( NVGcontext* vg, const rct_t& r ) const {
	float hh = r.h*.5f;
	nvgBeginPath(vg);
	nvgMoveTo(vg,_size_scroller_offset(),hh);
	nvgLineTo(vg,_size_scroller_offset()+_size_scroll_indicator_arrow_width(),hh-_size_scroll_indicator_arrow_height());
	nvgLineTo(vg,_size_scroller_offset()+_size_scroll_indicator_arrow_width(),hh+_size_scroll_indicator_arrow_height());
	nvgClosePath(vg);
}

inline	void ThemeDef::_path_scroll_indicator_right( NVGcontext* vg, const rct_t& r ) const {
	float hh = r.h*.5f;
	nvgBeginPath(vg);
	nvgMoveTo(vg,r.w-_size_scroller_offset(),hh);
	nvgLineTo(vg,r.w-_size_scroller_offset()-_size_scroll_indicator_arrow_width(),hh-_size_scroll_indicator_arrow_height());
	nvgLineTo(vg,r.w-_size_scroller_offset()-_size_scroll_indicator_arrow_width(),hh+_size_scroll_indicator_arrow_height());
	nvgClosePath(vg);
}

inline	void ThemeDef::_draw_scroll_indicator_left(NVGcontext* vg, const rct_t& r) const {
	nvgFillColor(vg,_color_scroll_indicator());
	_path_scroll_indicator_left(vg, r);
	nvgFill(vg);
}

inline	void ThemeDef::_draw_scroll_indicator_right(NVGcontext* vg, const rct_t& r) const {
	nvgFillColor(vg,_color_scroll_indicator());
	_path_scroll_indicator_right(vg, r);
	nvgFill(vg);
}

inline	void ThemeDef::_draw_scroll_indicator_top(NVGcontext* vg, const rct_t& r) const {
	nvgFillColor(vg,_color_scroll_indicator());
	_path_scroll_indicator_top(vg, r);
	nvgFill(vg);
}

inline	void ThemeDef::_draw_scroll_indicator_bottom(NVGcontext* vg, const rct_t& r) const {
	nvgFillColor(vg,_color_scroll_indicator());
	_path_scroll_indicator_bottom(vg, r);
	nvgFill(vg);
}






inline	void ThemeDef::_path_scrollbar_horz( NVGcontext* vg, const rct_t& r, float scale, float total, float delta ) const {
	float sz =mix(_size_scroller_thickness(),_size_scroller_thickness2(), scale );
	float off=mix(_size_scroller_offset(),_size_scroller_offset2(), scale );
	float scrollerRange = r.w-off*2;
	float scrollerW = scrollerRange*(r.w/total);
	float scrollerX = scrollerRange*(delta/total) + off;
	nvgBeginPath(vg);
	nvgRoundedRect(vg, scrollerX, r.h-sz-off, scrollerW, sz, sz/2.f);
}

inline	void ThemeDef::_path_scrollbar_vert( NVGcontext* vg, const rct_t& r, float scale, float total, float delta ) const {
	float sz  =mix(_size_scroller_thickness(),_size_scroller_thickness2(), scale );
	float off =mix(_size_scroller_offset(),_size_scroller_offset2(), scale );
	float scrollerRange = r.h-off*2;
	float scrollerH = scrollerRange*(r.h/total);
	float scrollerY = scrollerRange*(delta/float(total)) + off;
	nvgBeginPath(vg);
	nvgRoundedRect(vg, r.w-sz-off, scrollerY, sz, scrollerH, sz/2.f);
}

inline	void ThemeDef::_draw_scrollbar_horz( NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount) const {
	nvgFillColor(vg,nvgColorA(_size_scroller_background(),sz));
	nvgBeginPath(vg);
	nvgRect(vg, r.x,
			r.h+r.y-_size_scroller_offset2()*2-_size_scroller_thickness2(),
			r.w, _size_scroller_offset2()*2+_size_scroller_thickness2());
	nvgFill(vg);

	nvgFillColor(vg,nvgColorA(_color_scroll_indicator(),alpha));
	_path_scrollbar_horz(vg,r,sz, total, amount );
	nvgFill(vg);
}

inline	void ThemeDef::_draw_scrollbar_vert( NVGcontext* vg, const rct_t& r, float alpha, float sz, float total, float amount) const {
	nvgFillColor(vg,nvgColorA(_size_scroller_background(),sz));
	nvgBeginPath(vg);
	nvgRect(vg, r.w+r.x-_size_scroller_offset2()*2-_size_scroller_thickness2(), r.y,
			_size_scroller_offset2()+_size_scroller_thickness2(),r.h);
	nvgFill(vg);

	nvgFillColor(vg,nvgColorA(_color_scroll_indicator(),alpha));
	_path_scrollbar_vert(vg, r, sz, total, amount );
	nvgFill(vg);
}

inline	bool ThemeDef::_test_scrollbar_horz( const rct_t& r, const pos_t& pt) const {
	return pt.y>=r.h-_size_scroller_thickness()-_size_scroller_offset()-4
	   && pt.y<r.h-_size_scroller_offset()+4;
}

inline	bool ThemeDef::_test_scrollbar_vert( const rct_t& r, const pos_t& pt) const {
	return pt.x>=r.w-_size_scroller_thickness()-_size_scroller_offset()-4
		&& pt.x<r.w-_size_scroller_offset()+4;
}




inline sz2_t ThemeDef::_measure_menuitem(NVGcontext* vg, const str_t& str, bool separator ) const {
	if( !separator ) {
		float w = 0;
		if( vg )
			w = nvgMeasureText(vg, str, _pt_menu_text(), _font_menuitem()).w;
		return sz2_t(w,_size_menupan_menuitem_height() );
	}
	return sz2_t( 0, _size_menupan_separator_height() );
}

inline	void ThemeDef::_draw_menuitem(NVGcontext* vg, const rct_t& r, const str_t& str, align_t align, bool state, bool disabled, bool separator ) const {
	if( !separator ) {
		NVGcolor color = _color_menu_text();
		if( disabled )		color.a = 0.4f;
		else if( state )	color = _color_menu_text_under_item();
		nvgFontFace( vg, _font_menuitem() );
		nvgFontSize( vg, _pt_menu_text() );
		nvgFillColor( vg, color );
		nvgTextAligned(vg, r, str, _alignment_to_NVGAlign(align));
	}
}

inline void	ThemeDef::_draw_menuitem_expandable_arrow(NVGcontext* vg, const rct_t& r, bool state, bool disabled ) const {
	NVGcolor color = _color_menu_text();
	if( disabled )		color.a = 0.4f;
	else if( state )	color = _color_menu_text_under_item();
	rct_t b = _rect_menuitem_expandable_arrow_box(r);
	nvgBeginPath( vg );
	nvgMoveTo( vg, b.x+b.w, b.y+b.h/2.f );
	nvgLineTo( vg, b.x, b.y );
	nvgLineTo( vg, b.x, b.y+b.h );
	nvgFillColor( vg, color );
	nvgFill(vg);
}





inline	void ThemeDef::_path_separator_vert( NVGcontext* vg, const rct_t& r, float y ) const {
	nvgPathLineR(vg,pos_t(r.x,r.y+y),pos_t(r.w,0));
}

inline	void ThemeDef::_path_separator_horz( NVGcontext* vg, const rct_t& r, float x ) const {
	nvgPathLineR(vg,pos_t(r.x+x,r.y),pos_t(0,r.h));
}
	

inline	void ThemeDef::_path_menupan_box( NVGcontext* vg, const rct_t& r ) const {
	nvgBeginPath(vg);
	nvgRoundedRect( vg, r.x, r.y, r.w, r.h, _radius_menupan());
}

inline	void ThemeDef::_draw_menupan_under_item_fill(NVGcontext* vg, const rct_t& r) const {
	nvgBeginPath(vg);
	nvgFillColor(vg,_color_menupan_fill_under_item());
	nvgRect(vg,r.x,r.y,r.w,r.h);
	nvgFill(vg);
}

inline	void ThemeDef::_draw_menupan_checked_item_check(NVGcontext* vg, const rct_t& r,bool under) const {
	rct_t rr(r.x,r.y+r.h/2-8,16,16);
	nvgPathCheck(vg, rr);
	nvgStrokeColor(vg,under?_color_menu_text_under_item():_color_menu_text());
	nvgStrokeWidth(vg,1.5f);
	nvgStroke(vg);
}


inline	void ThemeDef::_path_button_box(NVGcontext* vg, const rct_t& r, box_type_t boxType) const {
	switch( boxType ) {
		case box_type_t::BOX_LEFT:
			_path_button_box_left(vg, r);
			break;
		case box_type_t::BOX_RIGHT:
			_path_button_box_right(vg, r);
			break;
		case box_type_t::BOX_MIDDLE:
			_path_button_box_middle(vg, r);
			break;
		case box_type_t::BOX_TOP:
			_path_button_box_top(vg, r);
			break;
		case box_type_t::BOX_BOTTOM:
			_path_button_box_bottom(vg, r);
			break;
		case box_type_t::BOX_IND:
		default:
			_path_button_box( vg, r );
			break;
	}
}

inline	void ThemeDef::_draw_button_box_over(NVGcontext* vg, const rct_t& r, shade_state_t state, box_type_t boxType) const {
	_path_button_box(vg, r, boxType);
	
	NVGcolor c = _color_f_button_fill_over(state);
	if( c.a>0 ) {
		nvgFillColor(vg, c);
		nvgFill(vg);
	}
}

inline	void ThemeDef::_draw_button_box_image(NVGcontext* vg, const rct_t& r, const NVGpaint& paint, shade_state_t state, box_type_t boxType) const {
	NVGpaint p=paint;
	float alpha = _alpha_f_label(state);
	p.innerColor.a *= alpha;
	p.outerColor.a *= alpha;
	nvgFillPaint(vg, p);
	_path_button_box(vg, r, boxType);
	nvgFill( vg );
}

inline	void ThemeDef::_draw_button_box(NVGcontext* vg, const rct_t& r, shade_state_t s, box_type_t boxType) const {
	if( contains(s,shade_state_t::TARGETTED) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) )
		nvgGlowBox(vg, r, 4, 5, _color_targetted_glow() );

	NVGcolor c = _color_f_button_fill(s);
	_path_button_box(vg, r, boxType);
	if( c.a>0 ) {
		nvgFillColor( vg, c );
		nvgFill(vg);
	}
	nvgStrokeColor(vg, _color_f_button_bound(s));
	nvgStrokeWidth(vg, _width_button_bound());
	nvgStroke(vg);
}

inline void ThemeDef::_draw_radio_button_group_box(NVGcontext* vg, const rct_t& r, shade_state_t s) const {
	if( contains(s,shade_state_t::TARGETTED) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) )
		nvgGlowBox(vg, r, 4, 5, _color_targetted_glow() );
}

inline void	ThemeDef::_draw_button_group_check( NVGcontext* vg, const rct_t& r, shade_state_t s) const {
	float h = std::min(_size_button_group_check(), std::min( r.w-4,r.h-4));
	float R = h/2;
	float x = r.x+r.w-R-2;
	float y = r.y+R+2;
	nvgBeginPath(vg);
	nvgCircle(vg, x, y, R);
	if( contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		NVGpaint p=nvgRadialGradient(vg, x, y, R, R+2,
									 nvgColorA(_color_menupan_fill_under_item(),0.4f),
									 nvgColorA(_color_menupan_fill_under_item(),0) );
		nvgFillPaint(vg, p);
	}
	else{
		NVGpaint p=nvgRadialGradient(vg, x, y, R, R+2,
									 _color_menupan_fill_under_item(),
									 nvgColorA(_color_menupan_fill_under_item(),0) );
		nvgFillPaint(vg, p);
	}
	nvgFill(vg);
	rct_t rr = rct_t( x-R, y-R,h,h);
	nvgPathCheck(vg,rr);
	nvgStrokeWidth(vg,1.5f);
	if( contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		nvgStrokeColor(vg,nvgRGBAf(1,1,1,.4f));
	}
	else {
		nvgStrokeColor(vg,nvgRGBAf(1,1,1,1));
	}
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_splitter_separator_horz(NVGcontext* vg, const rct_t& r, float x ) const {
	nvgStrokeColor(vg, _color_panel_separator() );
	nvgStrokeWidth(vg, _width_panel_separator() );
	_path_separator_horz(vg, r, x );
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_splitter_separator_vert(NVGcontext* vg, const rct_t& r, float y ) const {
	nvgStrokeColor(vg, _color_panel_separator() );
	nvgStrokeWidth(vg, _width_panel_separator() );
	_path_separator_vert(vg, r, y );
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_popupbox_box(NVGcontext* vg, const rct_t& r) const {
	// SHADOW************
	nvgShadowRect(vg, rct_t(r.x,r.y-2,r.w,r.h), _size_menupan_shadow_width(),
				  pos_t(0,_size_menupan_shadow_offset_y()), _radius_popupbox()*1.5f);
	// SHADOW************
	nvgBeginPath(vg);
	nvgPathBottomRoundBox(vg, r.x, r.y-2, r.w, r.h, _radius_popupbox());
	nvgFillColor(vg,_color_panel());
	nvgFill(vg);
	
	nvgStrokeColor(vg,_color_panel_separator());
	nvgStroke(vg);

}

inline	void ThemeDef::_draw_menupan_box(NVGcontext* vg, const rct_t& r) const {
	nvgShadowRect(vg, r, _size_menupan_shadow_width(),
				  pos_t(0,_size_menupan_shadow_offset_y()), _radius_menupan()*1.5f);
	nvgFillColor(vg, _color_menupan_background() );
	_path_menupan_box(vg, r);
	nvgFill(vg);
}

inline	void ThemeDef::_draw_menupan_separator(NVGcontext* vg, const rct_t& r) const {
	nvgPathLineR(vg,pos_t(r.x,r.y+r.h*.5f), pos_t(r.w,0));
	nvgStrokeColor(vg, _color_menupan_separator());
	nvgStrokeWidth(vg,1.5f);
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_menupan_box_over(NVGcontext* vg, const rct_t& r) const {
	nvgBeginPath(vg);
	nvgRoundedRect(vg, r.x,r.y,r.w,r.h, _radius_menupan() );
	nvgStrokeColor(vg,nvgRGBAf(.70f,.70f,.70f,1));
	nvgStrokeWidth(vg,_width_button_bound());
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_toolbar_box_base(NVGcontext* vg, const rct_t& r) const {
	float x=r.x, y=r.y, w=r.w, h=r.h;
	NVGpaint paint = nvgLinearGradient( vg,x,y,x,y+h, _color_toolbar_fill_grad1(), _color_toolbar_fill_grad2());
	nvgFillPaint(vg,paint);
	nvgBeginPath(vg);
	nvgRect(vg,x,y,w,h);
	nvgFill(vg);

	nvgStrokeWidth(vg,1);

	nvgPathLineR(vg,pos_t(x,y),pos_t(w,0));
	nvgStrokeColor(vg, _color_toolbar_fill_line1());
	nvgStroke(vg);
	
	nvgPathLineR(vg,pos_t(x,y+1),pos_t(w,0));
	nvgStrokeColor(vg, _color_toolbar_fill_line2());
	nvgStroke(vg);

	nvgPathLineR(vg,pos_t(x,h+y-1),pos_t(w,0));
	nvgStrokeColor(vg, _color_toolbar_fill_line3());
	nvgStroke(vg);

	nvgPathLineR(vg,pos_t(x,h+y),pos_t(w,0));
	nvgStrokeColor(vg, _color_toolbar_fill_line4());
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_toolbar_box(NVGcontext* vg, const rct_t& r, shade_state_t s) const {
	if( !contains(s, shade_state_t::WINDOW_UNFOCUSED ) ) {
		_draw_toolbar_box_base(vg,r);
	}
	else {
		nvgFillColor( vg, _color_toolbar_fill_unfocused() );
		nvgBeginPath(vg);
		nvgRect( vg, r.x, r.y, r.w, r.h);
		nvgFill(vg);
		
		nvgPathLineR(vg,r.bl(),pos_t(r.w,0));
		nvgStrokeWidth(vg,1);
		nvgStrokeColor(vg, _color_panel_separator());
		nvgStroke(vg);
	}
}

inline	void ThemeDef::_draw_statusbar_box(NVGcontext* vg, const rct_t& r, shade_state_t s) const {
	if( ( s & shade_state_t::WINDOW_UNFOCUSED )==shade_state_t::NORMAL ) {
		_draw_toolbar_box_base(vg,r);
		nvgPathLineR(vg,r.tl(),pos_t(r.w,0));
		nvgStrokeWidth(vg,1);
		nvgStrokeColor(vg, _color_statusbar_fill_top() );
		nvgStroke(vg);
	}
	else {
		nvgFillColor( vg, _color_toolbar_fill_unfocused() );
		nvgBeginPath(vg);
		nvgRect( vg, r.x, r.y, r.w, r.h);
		nvgFill(vg);
		nvgPathLineR(vg,r.tl(),pos_t(r.w,0));
		nvgStrokeWidth(vg,1);
		nvgStrokeColor(vg, _color_panel_separator());
		nvgStroke(vg);
	}
}


inline	void ThemeDef::_draw_options_control(NVGcontext* vg, const rct_t& r, shade_state_t state ) const {
	sz2_t sz = r.wh();
	float tx =r.w+r.x+_size_options_arrow_hwidth(sz)-_size_options_button_width(sz);
	float ty =r.y+_size_options_arrow_y_offset(sz);
	nvgStrokeColor(vg,nvgColorA(_color_menu_text(),_alpha_f_label(state) ));
	nvgStrokeWidth(vg,1.5f);
	nvgBeginPath(vg);
	nvgMoveTo(vg,tx-_size_options_arrow_hwidth(sz),ty+_size_options_arrow_height(sz));
	nvgLineTo(vg,tx,ty);
	nvgLineTo(vg,tx+_size_options_arrow_hwidth(sz),ty+_size_options_arrow_height(sz));
	ty =r.y+r.h-_size_options_arrow_y_offset(sz);
	nvgMoveTo(vg,tx-_size_options_arrow_hwidth(sz),ty-_size_options_arrow_height(sz));
	nvgLineTo(vg,tx,ty);
	nvgLineTo(vg,tx+_size_options_arrow_hwidth(sz),ty-_size_options_arrow_height(sz));
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_options_box(NVGcontext* vg, const rct_t& r, shade_state_t s ) const {
	if( contains(s,shade_state_t::TARGETTED ) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) )
		nvgGlowBox(vg, r, 4, 5, _color_targetted_glow() );
	_draw_button_box(vg, r, s, box_type_t::BOX_IND);
}

inline	void ThemeDef::_draw_options_text(NVGcontext* vg, const rct_t& r, const str_t& str, shade_state_t state ) const {
	nvgFontFace( vg, _font_menuitem() );
	nvgFontSize( vg, _pt_menu_text() );
	nvgFillColor( vg, nvgColorA( _color_menu_text(), _alpha_f_label(state) ) );
	nvgTextAligned(vg, r, str, NVG_ALIGN_LEFT|NVG_ALIGN_MIDDLE );
}

inline	void ThemeDef::_draw_optionbox_arrow(NVGcontext* vg, const rct_t& r, shade_state_t state ) const {
	rct_t b = _rect_optionbox_arrow(r);
	nvgBeginPath(vg);
	nvgMoveTo(vg, b.x, b.y);
	nvgLineTo(vg, b.x+b.w, b.y);
	nvgLineTo(vg, b.x+b.w/2.f, b.y+b.h);
	nvgClosePath(vg);
	nvgFillColor(vg, _color_f_label(state) );
	nvgFill(vg);

}


inline	void ThemeDef::_draw_check_box(NVGcontext* vg, const rct_t& r, shade_state_t s ) const {
	if( contains(s,shade_state_t::TARGETTED ) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) )
		nvgGlowBox(vg, r, 4, 5, _color_targetted_glow() );
	_draw_button_box(vg, r, s, box_type_t::BOX_IND);
}

inline	void ThemeDef::_draw_check_checked(NVGcontext* vg, const rct_t& r, shade_state_t state ) const {
	nvgPathCheck(vg,r);
	nvgStrokeWidth(vg,1.5);
	nvgStrokeColor(vg,nvgColorA(_color_label(),_alpha_f_label(state) ));
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_tooltip(NVGcontext* vg, const rct_t& rr, float dx, const str_t& str, float alpha ) const {
	nvgShadowRect(vg, rr, _size_menupan_shadow_width(), pos_t(0,2), _radius_tooltip_box()*1.5f);
	nvgPathBalloon(vg,rr,pos_t(dx,-10),_radius_tooltip_box(),sz2_t(6,5));
	nvgFillColor(vg, nvgColorA(_color_tooltip_box(),alpha));
	nvgFill(vg);
	nvgStrokeWidth(vg, _width_tooltip_bound());
	nvgStrokeColor(vg, nvgColorA(_color_tooltip_bound(),alpha));
	nvgStroke(vg);
	nvgFillColor(vg, nvgColorA(_color_tooltip_text(),alpha));
	nvgFontFace( vg, _font_tooltip_text() );
	nvgFontSize( vg, _pt_tooltip_text() );
	nvgTextAligned(vg, rr, str, NVG_ALIGN_MIDDLE|NVG_ALIGN_CENTER);
}

inline	sz2_t ThemeDef::_measure_tooltip_text(NVGcontext* vg, const str_t& s) const {
	return nvgMeasureText(vg, s, _pt_tooltip_text(), _font_tooltip_text());
}


inline	void ThemeDef::_draw_textinputbase_box(NVGcontext* vg, const rct_t& r, shade_state_t s) const {
	if( contains(s,shade_state_t::TARGETTED ) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		nvgGlowBox(vg, r, 4, 2, _color_targetted_glow() );
	}
	nvgBeginPath(vg);
	nvgRect(vg,r.x,r.y,r.w,r.h);
	nvgFillColor(vg,_color_f_button_fill(s));
	nvgFill(vg);
	nvgStrokeWidth(vg,1);
	nvgStrokeColor(vg,_color_f_button_bound(s));
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_textinputbase_selection(NVGcontext* vg, const rct_t& r, const rct_t& sr, float x0, float x1, shade_state_t s) const {
	if( contains(s,shade_state_t::TARGETTED )&& !contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		nvgSave(vg);
		nvgScissor(vg, sr.x, sr.y, sr.w, sr.h );
		nvgFillColor(vg,_color_targetted_glow() );
		nvgBeginPath(vg);
		nvgRect(vg, x0, r.y+4, x1-x0, r.h-8 );
		nvgFill(vg);
		nvgRestore(vg);
	}
}
inline	void ThemeDef::_draw_textinputbase_cursor(NVGcontext* vg, const rct_t& r, const rct_t& sr, float x, shade_state_t s) const {
	if( contains(s,shade_state_t::TARGETTED ) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		nvgSave(vg);
		nvgScissor(vg, sr.x, sr.y, sr.w, sr.h );
		nvgStrokeColor(vg,_color_label());
		nvgStrokeWidth(vg,2);
		nvgPathLineR(vg,pos_t(x,r.y+4),pos_t(0,r.h-8));
		nvgStroke(vg);
		nvgRestore(vg);
	}
}
inline	void ThemeDef::_draw_textinputbase_text(NVGcontext* vg, const rct_t& r, const rct_t& sr, const str_t& str, align_t align, shade_state_t state) const {
	nvgSave(vg);
	nvgScissor(vg, sr.x, sr.y, sr.w, sr.h );
	nvgFontFace(vg, "system");
	nvgFontSize(vg, _pt_menu_text());
	nvgFillColor(vg,nvgColorA(_color_label(),_alpha_f_label(state)));
	nvgTextAligned(vg, r, str, _alignment_to_NVGAlign(align));
	nvgRestore(vg);
}

inline	float ThemeDef::_size_slider_padding() const { return 8;}
inline	float ThemeDef::_size_slider_bar_height() const { return 1.5f; }
inline	float ThemeDef::_size_slider_tick_minWidth() const { return 6; }
inline	float ThemeDef::_size_slider_ticks_fine() const { return 2; }
inline	float ThemeDef::_size_slider_ticks_minor() const { return 3.5f; }
inline	float ThemeDef::_size_slider_ticks_major() const { return 5; }

inline	sz2_t ThemeDef::_measure_textinputbase_text(NVGcontext* vg, const str_t& str) const {
	return nvgMeasureText(vg, str, _pt_menu_text(), "system");
}

inline	float ThemeDef::_radius_f_slider_cursor(slide_type_t type)const {
	if( type==slide_type_t::ALL )			return 5;
	else if( type==slide_type_t::TICKED )	return 6;
	else									return 7;
}

inline	float ThemeDef::_pos_f_slider_y(slide_type_t type,const rct_t&r)const {
	float centerY = r.y+r.h/2;
	if( type==slide_type_t::ALL )			return centerY;
	else if( type==slide_type_t::TICKED )	return centerY-4.5f;
	else if( type==slide_type_t::VALUED )	return centerY-4.5f;
	else									return centerY;
}

inline	float ThemeDef::_pos_slider_tick(const rct_t& r) const {
	return r.y+r.h/2+6;
}

inline	float ThemeDef::_pos_slider_number(slide_type_t type, const rct_t& r) const {
	return r.y+r.h/2 + (contains(type,slide_type_t::TICKED)?-5:6);
}

inline	void ThemeDef::_draw_slider_bar(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s) const {
	float centerY = _pos_f_slider_y(type,r);
	nvgBeginPath(vg);
	nvgRoundedRect(vg, r.x-_size_slider_bar_height()+_size_slider_padding(),
				   centerY-_size_slider_bar_height(),
				   r.w+_size_slider_bar_height()*2-_size_slider_padding()*2,
				   _size_slider_bar_height()*2, _size_slider_bar_height() );
	nvgFillColor(vg, _color_f_button_bound(s));
	nvgFill(vg);
}

inline	void ThemeDef::_draw_slider_cursor(NVGcontext* vg,slide_type_t type,const rct_t& r,float x,shade_state_t s) const {
	float y = _pos_f_slider_y(type,r);
	NVGcolor c = _color_targetted_glow();
	NVGpaint glowPaint = nvgRadialGradient(vg, x, y,
										   _radius_f_slider_cursor(type)+1,
										   _radius_f_slider_cursor(type)+4,
										   c, nvgRGBAf(c.r,c.g,c.b,0));
	if( contains(s,shade_state_t::TARGETTED ) && !contains(s,shade_state_t::WINDOW_UNFOCUSED) ) {
		nvgBeginPath(vg);
		nvgCircle(vg,x,y,_radius_f_slider_cursor(type)+6);
		nvgFillPaint(vg, glowPaint);
		nvgFill(vg);
	}
	nvgBeginPath(vg);
	if( type==slide_type_t::ALL )
		nvgPathHexagon(vg, rct_t(x-5,y-6,10,12), 3);
	else if( type==slide_type_t::TICKED || type==slide_type_t::VALUED )
		nvgPathBalloon(vg, rct_t(x-6,y-6.5f,12,11), pos_t(6,22), 3, sz2_t(5,5));
	else
		nvgCircle(vg, x, y, _radius_f_slider_cursor(type));

	nvgFillColor(vg,_color_f_button_fill(s));
	nvgFill(vg);
	nvgStrokeWidth(vg,1);
	nvgStrokeColor(vg,_color_f_button_bound(s));
	nvgStroke(vg);
	if( contains(s,shade_state_t::PRESSED )) {
		nvgFillColor(vg,_color_button_shade_pushed());
		nvgFill(vg);
	}
}

inline	void ThemeDef::_draw_slider_ticks_fine(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const {
	float y = _pos_slider_tick(r) ;
	nvgStrokeWidth(vg,0.5);
	nvgBeginPath(vg);
	if( step>0 )
	for( float x=offset; x<=r.w-_size_slider_padding()*2; x+=step )
		nvgLineR(vg, pos_t(x+r.x+_size_slider_padding(), y), pos_t(0,_size_slider_ticks_fine()));
	nvgStrokeColor(vg, _color_f_label(s));
	nvgStroke(vg);
}

inline	void ThemeDef::_draw_slider_ticks_minor(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const {
	float y = _pos_slider_tick(r) ;
	nvgStrokeWidth(vg,0.5);
	nvgBeginPath(vg);
	if( step>0 )
	for( float x=offset; x<=r.w-_size_slider_padding()*2; x+=step )
		nvgLineR(vg, pos_t(x+r.x+_size_slider_padding(), y), pos_t(0,_size_slider_ticks_minor()));
	nvgStrokeColor(vg, _color_f_label(s));
	nvgStroke(vg);
}
inline	void ThemeDef::_draw_slider_ticks_major(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step)const {
	float y = _pos_slider_tick(r) ;
	nvgStrokeWidth(vg,1);
	nvgBeginPath(vg);
	if( step>0 )
	for( float x=offset; x<=r.w-_size_slider_padding()*2+2; x+=step )
		nvgLineR(vg, pos_t(x+r.x+_size_slider_padding(), y), pos_t(0,_size_slider_ticks_major()));
	nvgStrokeColor(vg, _color_f_label(s));
	nvgStroke(vg);
}
inline	void ThemeDef::_draw_slider_numbers(NVGcontext* vg,slide_type_t type,const rct_t& r,shade_state_t s,float offset,float step, float valueOffset,float valueStep, double base)const {
	nvgFontSize(vg, 7);
	nvgTextAlign(vg, (contains(type,slide_type_t::TICKED)?NVG_ALIGN_BOTTOM:NVG_ALIGN_TOP)|NVG_ALIGN_CENTER);
	nvgFillColor(vg, _color_f_label(s));
	float y = _pos_slider_number(type,r);
	float val = valueOffset;
	for( float x=offset; x<=r.w-_size_slider_padding()*2+2; x+=step ) {
		str_t str = std::to_string( round(val/base)*base );
		nvgText(vg, x+r.x+_size_slider_padding(), y, str.c_str(), 0);
		val+=valueStep;
	}
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _ThemeDef_h */
