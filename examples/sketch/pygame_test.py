#!/usr/bin/python
"""
This is a sketch example, to represent how a single display could be shared by
many actors.

This example demonstrates

* One approach to using Actors in Pygame
* Using STM for sharing data in a way perhaps quicker than actor methods
* Using guild services

This example has 5 actors:

* A display actor that can provide traced surfaces to clients
* 4 "flicker" actors

The Display Actor:

* Creates an STM for the surfaces to be tracked
    * This uses custom a Value type: SurfaceValue
* Creates a window
* Creates a snapshot of the STM store
* In it's mainloop
    * Pulls all updates from the STM store into its local snapshot
    * The updates are the rendered to the surface
    * We also print out the number of updates
    * We then wait a stupidly small time before doing this again - this is to ensure a small number of updates per loop

* Provides an actor function get_tracked_surfaceL
    * This takes a size and position
    * It creates an SDL surface
    * An STM SurfaceValue is created to track this
    * This value is pushed into the STM store
    * The tracked value/surface is returned to the client

Each flicker actor:

* Looks for a display service
* Asks the display for a tracked surface
* Then in it's main loop:
    * Updates the surface
    * Pushes updates to the tracked_surface store.
    * Uses the updated surface

"""

import os
from random import randint
import random
import time

import pygame

from guild.actor import *
from guild.stm import Store, ConcurrentUpdate, BusyRetry, Value

# This next line is useful to get SDL to play nicely with Plasma under Linux
# It's not necessary generally, but makes pygame play nicer on my system
os.environ["SDL_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR"] = "0"

class SurfaceValue(Value):
    def copy_value(self, value):
        if value is None:
            return value
        surface, location = value
        newvalue = (pygame.Surface.copy(surface), location)
        return newvalue

    def push(self):
        try:
            newvalue = self.commit()
            self.version = newvalue.version
            self.value = newvalue.value
        except ConcurrentUpdate as e:
            print(repr(e))
        except BusyRetry as e:
            pass


class Display(Actor):

    def __init__(self):
        super(Display, self).__init__()
        self.nextid = 1
        self.surface_store = Store(valuetype=SurfaceValue)

    def main(self):
        self.displaysize = 800,600
        self.display = pygame.display.set_mode(self.displaysize)
        snapshot = self.surface_store.snapshot()

        while True:
            pygame.display.flip()

            updates = snapshot.pull_updates()
            if len(updates) >0:
                  print("LENGTH UPDATES", len(updates))
                  for item in updates:
                      surface, location = item.value
                      self.display.blit(surface, location)
            time.sleep(0.001) # Stupidly small wait time to ensure we see a length < 4 for this example
            yield 1

    def onStop(self):
        # close the display?
        pass

    def track(self, surface, location):
        nextid = self.nextid
        self.nextid += 1
        tracked_surface = self.surface_store.usevar(nextid)  # Initialise tracking of surface
        tracked_surface.value = (surface, location)          # Create the surface
        tracked_surface.push()                               # Push this update
        return tracked_surface

    @actor_function
    def get_tracked_surface(self, size, location):
        surface = pygame.Surface( size )
        tracked_surface = self.track(surface, location)
        return tracked_surface


class Flicker(Actor):
    def __init__(self, size, location):
        super(Flicker,self).__init__()
        self.size = size
        self.location = location

    def process_start(self):
        self.display = guild.lookup("display")
        self.tracked_surface = self.display.get_tracked_surface(self.size, self.location )
        self.surface = self.tracked_surface.value[0]

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

        self.tracked_surface.push()
        self.surface = self.tracked_surface.value[0]

if __name__ == "__main__":
    import guild

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

    time.sleep(2)

    stop(display, *flickers)
    join(display,*flickers)
