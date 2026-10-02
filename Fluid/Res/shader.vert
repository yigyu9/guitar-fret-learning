
#version 410 core
layout(location=0) in vec3 in_Position;
layout(location=2) in vec2 in_TexCoord;
uniform mat4 viewMat = mat4(1);
uniform mat4 projMat = mat4(1);
uniform mat4 modelMat = mat4(1);
out vec2 texCoord;
void main(void) {
	gl_Position= vec4(in_Position,1);
	texCoord = in_TexCoord;
}


