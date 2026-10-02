
//
//  main.cpp
//  Fluid
//
//  Created by Hyun Joon Shin on 2021/05/31.
//

#define JGL2_IMPLEMENTATION
#include <iostream>
#include <JGL2/JGL.hpp>
#include "GLTools.hpp"
#include "TexView.hpp"
#include <algorithm>

using namespace jm;

TexView* view;
const int GRID_W = 256;
const int GRID_H = 256;

float* density = nullptr;
float* densityTemp = nullptr;
float* p = nullptr;
vec2* velocity = nullptr;
vec2* velocityTemp = nullptr;
ivec2 mousePt;
ivec2 lastPt;
bool pressed = false;

float H = 1;
float kappa = 10;


void init() {
	if( !density ) {
		density = new float[GRID_W*GRID_H];
		densityTemp = new float[GRID_W*GRID_H];
		velocity = new jm::vec2[GRID_W*GRID_H];
		velocityTemp = new jm::vec2[GRID_W*GRID_H];
		p = new float[GRID_W*GRID_H];
	}
	for( int i=0; i<GRID_H*GRID_W; i++ ) {
		density[i] = 0;
		velocity[i] = jm::vec2(0,0);
		p[i] = 1;
	}
}



void frame(float dt) {
	if( pressed )
		density[mousePt.x+mousePt.y*GRID_W]+=40;
//	diffuse( kappa, density, dt );
//	advection( density, densityTemp, velocity, dt );
//	diffuse( 100, velocity, dt );
//	advection( velocity, velocityTemp, velocity, dt );
//	convserveMass( velocity, velocityTemp, p );
}

void push( float x, float y ) {
	mousePt = jm::ivec2( x*GRID_W, y*GRID_H );
	pressed = true;
}

void release() {
	pressed =false;
}

void move( float x, float y ) {
	lastPt = mousePt;
	mousePt = jm::ivec2( x*GRID_W, y*GRID_H );
	if( JGL2::eventMods(JGL2::mod_t::SHIFT))
		velocity[lastPt.x+lastPt.y*GRID_W] = vec2(mousePt-lastPt)*1000.f;
}

void drag( float x, float y ) {
	mousePt = jm::ivec2( x*GRID_W, y*GRID_H );
}

void update(Tex& tex) {
	tex.create(GRID_W,GRID_H,GL_RED,GL_FLOAT, density );
}

int main(int argc, const char * argv[]) {
	
	init();
	
	JGL2::Window* window = new JGL2::Window(1024,1024,"Fluid");
	view = new TexView(0,0,1024,1024);
	view->initFunction = init;
	view->updateFunction = update;
	view->frameFunction = frame;
	view->dragFunction = drag;
	view->moveFunction = move;
	view->pushFunction = push;
	view->releaseFunction = release;
	window->end();
	window->show();
	
	JGL2::_JGL::run();
	return 0;
}

