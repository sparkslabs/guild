#!/usr/bin/python
#
# See: http://www.sparkslabs.com/michael/blog/2014/03/07/guild---pipelinable-actors-with-late-binding/
#

import os
import pygame
import pygame.camera
import time

from guild.actor import *
pygame.camera.init()


class Camera(Actor):
    def main(self):
        camera = pygame.camera.Camera(pygame.camera.list_cameras()[0])
        camera.start()
        while True:
            yield 1
            frame = camera.get_image()
            self.output(frame)
            time.sleep(1.0 / 50)


class Display(Actor):
    def __init__(self, size):
        super(Display, self).__init__()
        self.size = size

    def process_start(self):
        self.display = pygame.display.set_mode(self.size)

    @actor_method
    def show(self, frame):
        self.display.blit(frame, (0, 0))
        pygame.display.flip()

    input = show


class FrameStore(Actor):
    def __init__(self, directory='Images', base='snap'):
        super(FrameStore, self).__init__()
        self.directory = directory
        self.base = base
        self.count = 0

    def process_start(self):
        try:
            os.makedirs(self.directory)
        except OSError as e:
            if e.errno != 17:
                raise

    @actor_method
    def input(self, frame):
        self.count += 1
        now = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        filename = "%s/%s-%s-%05d.jpg" % (self.directory,
                                          self.base, now,
                                          self.count)
        pygame.image.save(frame, filename)
        self.output(frame)


camera = Camera().go()
display = Display((800, 600)).go()
framestore = FrameStore().go()
pipeline(camera, framestore, display)

while 1:
    time.sleep(30)

stop(camera, framestore, display)
wait_for(camera, framestore, display)
