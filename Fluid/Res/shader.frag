#version 410 core

in vec2 texCoord;

uniform sampler2D tex;

out vec4 out_Color;

void main(void) {
//	out_Color = vec4(vec3(pow(texture(tex,texCoord).r,1/2.2)),1);
	out_Color = vec4(vec3(texture(tex,texCoord).r),1);
//	out_Color = vec4(texCoord,0,1);
}
