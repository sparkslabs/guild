#!/usr/bin/python

import time

from guild.actor import *
from guild.components import Backplane, PublishTo, SubscribeTo, Printer


class Producer(Actor):
    @process_method
    def process(self):
        self.output("hello")

    @late_bind_safe
    def output(self, value):
        pass


Backplane("HELLO").start()
p = Producer()
pr = Printer()

time.sleep(1)

pub = PublishTo("HELLO")
sub = SubscribeTo("HELLO")

print("pub", pub, repr(pub), pub.input)

pipeline(p, pub)
pipeline(sub, pr)

start(p, pr, sub)

time.sleep(1.0)

stop(p, pr, sub)
wait_for(p, pr, sub)
