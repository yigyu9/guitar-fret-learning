//
//  _MathTypes.hpp
//  JGL2
//
//  Created by Hyun Joon Shin on 2023/08/29.
//

#ifndef JGL2_MathTypes_h
#define JGL2_MathTypes_h

#ifdef __APPLE__
#pragma clang visibility push(default)
#pragma clang diagnostic ignored "-Wdocumentation"
#endif

#ifdef JGL2_USE_GLM
#include <glm/glm.hpp>
#include <JGL2/glm_rect.hpp>
#define SCMS_USE_GLM = 1
#define JR_USE_GLM = 1
#else
#include <jm/jm.hpp>
#endif

#include <vector>
#include <string>

namespace JGL2 {
#ifdef JGL2_USE_GLM

using pos_t		= glm::vec2;
using ipos_t	= glm::ivec2;
using sz2_t		= glm::dim2;
using isz_t		= glm::idim2;
using dt2_t		= glm::vec2;
using rct_t		= glm::rect;
using irct_t	= glm::irect;
using colora_t	= glm::vec4;
using scl2_t	= glm::vec2;
using transf3_t	= glm::mat4;
using transf2_t	= glm::mat3;

using glm::mix;
using glm::fract;
using glm::sign;

#define t_vec2(T) glm::vec<2,T>

#else

using pos_t		= jm::vec2;
using ipos_t	= jm::ivec2;
using sz2_t		= jm::dim2;
using isz_t		= jm::idim2;
using dt2_t		= jm::vec2;
using rct_t		= jm::rect;
using irct_t	= jm::irect;
using colora_t	= jm::vec4;
using colorah_t	= jm::hvec4;
using scl2_t	= jm::vec2;
using transf3_t	= jm::mat4;
using transf2_t	= jm::mat3;

using jm::mix;
using jm::fract;
using jm::sign;

#define t_vec2(T) jm::mvec2_t<T>

#endif

using str_t		= std::string;
using ilst_t	= std::vector<int>;
using flst_t	= std::vector<float>;
using slst_t	= std::vector<str_t>;
using llst_t	= std::vector<size_t>;
using plst_t	= std::vector<pos_t>;

struct Window;
struct Group;
struct Widget;
struct _Popup;
struct _MenuItem;

using widget_list_t		= std::vector<Widget*>;
using window_list_t		= std::vector<Window*>;
using group_list_t		= std::vector<Group*>;
using popup_list_t		= std::vector<_Popup>;
using menuitem_list_t	= std::vector<_MenuItem>;

using menu_data_t		= int;
using idx_t				= int;

inline transf3_t to3DTransform(const transf2_t& m) {
	return transf3_t(m[0][0],m[0][1],0,m[0][2],
					 m[1][0],m[1][1],0,m[1][2],
					 0,0,1,0,
					 m[2][0],m[2][1],0,m[2][2]);
}

} // namespace JGL2

#ifdef __APPLE__
#pragma clang visibility pop
#endif

#endif /* _MathType_h */
