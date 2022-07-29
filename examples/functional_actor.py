#!/usr/bin/python


import time
from guild.actor import *


class Woofie(Actor):
    @actor_method
    def bark(self):
        print("woof")

    @actor_function
    def name(self):
        return "woofie"

woofie = Woofie()

woofie.start()

time.sleep(0.01)     # Give woofie a chance
name = woofie.name()
print("NAME", name)
woofie.bark()
woofie.stop()
woofie.join()
