#!/usr/bin/python

import pygame
import time
import guild
from guild.actor import *


class Display(Actor):

    def gen_process(self):
      displaysize = 800,600
      self.display = pygame.display.set_mode(displaysize)

      while True:
        pygame.display.flip()
        yield 1

    def onStop(self):
        # close the display?
        pass

    @actor_method
    def blit(self, surface, position):
        self.display.blit(surface, position)

    @actor_function
    def get_surface(self, size):
      surface = pygame.Surface( self.size )
      self.tracking.append(surface)
      return surface


from random import randint
import random

class Ticker(Actor):
    def __init__(self, size, location):
        super(Ticker,self).__init__()
        self.size = size
        self.location = location

    def process_start(self):
        self.display = guild.lookup("display")
        self.surface = self.display.get_surface( self.size )

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
        self.display.blit(self.surface, self.location)

if __name__ == "__main__":
    display = Display()
    guild.init()
    guild.register("display", display)
    ticker = Ticker((300,200),(50,100))
    ticker2 = Ticker((300,200),(400,100))
    ticker3 = Ticker((300,200),(50,350))
    ticker4 = Ticker((300,200),(400,350))
    display.start()
    ticker.start()
    ticker2.start()
    ticker3.start()
    ticker4.start()
    time.sleep(60)

    ticker.stop()
    ticker2.stop()
    ticker3.stop()
    ticker4.stop()
    display.stop()
    ticker.join()
    ticker2.join()
    display.join()
