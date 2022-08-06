#!/usr/bin/python

from guild.actor import *
from guild.promise import wait_all

class Barkie(Actor):
    def __init__(self, name):
        super(Barkie, self).__init__()
        self._name = name
    @actor_method
    def bark(self):
        print("bark")
    @actor_function(timeout=1)
    def name(self):
        return self._name + " "+str(self)
    @actor_function
    def nom(self):
        return "barkie"


                            
names = ["one", "two", "three"]
barkies = [Barkie(x) for x in names]
[ x.start() for x in barkies ]

names_after = [ x.name() for x in barkies ]
print("AF", names_after)

promises = [ x.promise.name() for x in barkies ]
wait_all(*promises)
values = [ p.unwrap() for p in promises ]
print("P", values)
