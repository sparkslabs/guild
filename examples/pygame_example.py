#!/usr/bin/python

"""when green flag clicked
when [space] key pressed
when this sprite clicked
when backdrop switches to [backgroundx]
when [loudness] > 10    | loudness/videomotion/timer
when I recieve [message1]
broadcast [message]
broadcast [message] and wait"""

import pygame
import time
import sys
import random

from guild.actor import *
from guild.stm import Store, ConcurrentUpdate, BusyRetry, retry

pygame.init()
display = pygame.display.set_mode([800,600])


def register(key, value):
    try:
        repo = services.checkout()
        while repo.notcheckedin:
            with repo.changeset(key) as c:
                c[key].set(value)
    except _MAXFAIL as mf:
        print("TRANSACTION COMPLETELY FAILED")


class Sprite(Actor):

    def __init__(self):
        super(Sprite, self).__init__()
        self.sprite_state = Store()
        self.update_pos(400,300)
        self.pos = self.get_pos()
        print( self.pos )

    def get_pos(self, force=False):
        if (time.time() < self.sprite_state.last_update) or force:
            self.pos = self.sprite_state.export(["x", "y"])
        return self.pos

    # Threadsafe update of shareable state
    @retry
    def update_pos(self, x, y):
        repo = self.sprite_state.checkout()
        with repo.changeset("x","y") as c: # This can fail
            c["x"].set(x)
            c["y"].set(y)

        self.pos = self.get_pos(force=True)


    def render(self, surface, absolute=True): # Assume screen co-ordinates
        pass

class Landscape(Sprite):
    def render(self, surface, absolute=True): # Assume screen co-ordinates
        pos = self.get_pos()

        pygame.draw.rect(surface, (200,200,250), (0,0,800,600),0)
        pygame.draw.rect(surface, (100,200,100), (0,300,800,300),0)

class Flappy(Sprite):
    def __init__(self, x, y):
        super(Flappy, self).__init__()
        self.update_pos(x,y)

    def render(self, surface, absolute=True):
        now = int(time.time()*12)
        pos = self.get_pos()
        x = pos["x"]
        y = pos["y"]

        pygame.draw.circle(display, (250,250,100), (int(x), int(y)), 30)
        pygame.draw.circle(display, (250,250,250), (int(x)+10, int(y)-10), 5)
        pygame.draw.circle(display, (0,0,0), (int(x)+10, int(y)-10), 2)

        pygame.draw.polygon(display, (150,100,50), [(int(x)+x_, int(y)+y_) for (x_,y_) in [ (30,-5),(30,+5),(40,0) ] ] )

        if now % 2:
            pygame.draw.polygon(display, (150,150,100), [(int(x)+x_, int(y)+y_) for (x_,y_) in [ (0,0),(-20,0),(-30,-30) ] ] )
        else:
            pygame.draw.polygon(display, (150,150,100), [(int(x)+x_, int(y)+y_) for (x_,y_) in [ (0,0),(-20,0),(-30,30) ] ] )

l = Landscape()
fs = []
for i in range(250):
    x = random.randint(10,70)*10
    y = random.randint(10,50)*10
    f = Flappy(x,y)
    fs.append(f)

while True:
    ts = time.time()
    l.render(display)

    if pygame.event.peek():
        event = pygame.event.wait()
        if event.type==pygame.QUIT: sys.exit()
        if event.type==pygame.KEYDOWN:
            if event.key == pygame.K_q:
                break

    for f in fs:
        f.render(display)
    pygame.display.flip()  # Make any updates to the display visible
    te = ts + 0.04
    now = time.time()
    delay = te-now
    if delay>0:
        time.sleep(delay)

