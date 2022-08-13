#!/usr/bin/python

from random import randint
import random

import pygame
import time
import guild
from guild.actor import *

import os
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"

class Display(Actor):

    def __init__(self):
        super(Display, self).__init__()
        self.tracking = []

    def main(self):
      self.displaysize = 800,600
      self.display = pygame.display.set_mode(self.displaysize)

      while True:
        pygame.display.flip()
        for surface, location in self.tracking:
            self.display.blit(surface, location)
        yield 1

    def onStop(self):
        # close the display?
        pass

    def track(self, surface, location):
        self.tracking.append((surface, location))

    @actor_function
    def get_surface(self, size, location):
        surface = pygame.Surface( size )
        self.track(surface, location)
        return surface


class Flicker(Actor):
    def __init__(self, size, location):
        super(Flicker,self).__init__()
        self.size = size
        self.location = location

    def process_start(self):
        self.display = guild.lookup("display")
        self.surface = self.display.get_surface( self.size,self.location )

        self.r, self.dr = 128, random.choice([-3,-2,-1,1,2,3])
        self.g, self.dg = 128, random.choice([-3,-2,-1,1,2,3])
        self.b, self.db = 128, random.choice([-3,-2,-1,1,2,3])

    @process_method
    def process(self):
        time.sleep(0.01)
        self.r +=  self.dr
        self.g +=  self.dg
        self.b +=  self.db
        if self.r>255:
            self.r, self.dr = 255, -self.dr
        if self.g>255:
            self.g, self.dg = 255, -self.dg
        if self.b>255:
            self.b, self.db = 255, -self.db

        if self.r<0:
            self.r, self.dr = 0, -self.dr
        if self.g<0:
            self.g, self.dg = 0, -self.dg
        if self.b<0:
            self.b, self.db = 0, -self.db

        if random.random() < 0.1:
            self.dr = random.choice([-3,-2,-1,1,2,3])
        if random.random() < 0.1:
            self.dg = random.choice([-3,-2,-1,1,2,3])
        if random.random() < 0.1:
            self.db = random.choice([-3,-2,-1,1,2,3])

        pygame.draw.rect(self.surface,
                         (self.r, self.g, self.b),
                          ( 0,0 , 
                           self.size[0], self.size[1]))

if __name__ == "__main__":
    display = Display()
    guild.init()
    guild.register("display", display)
    rects = [
                ((300,200),(50,100)),
                ((300,200),(400,100)),
                ((300,200),(50,350)),
                ((300,200),(400,350))
            ]

    flickers = []
    for pos, size in rects:
        flickers.append( Flicker(pos, size) )

    start(display,*flickers)

    time.sleep(10)

    stop(display, *flickers)
    join(display,*flickers)
