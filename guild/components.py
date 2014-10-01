#!/usr/bin/python

from __future__ import print_function

import time
import sys
import guild
from guild.actor import *

guild.init()


class Splitter(Actor):
    """A Splitter takes data published to it and passes it to subscribers

    Additionally, a splitter can be used in a bridging mode, such
    that two splitters can be joined to each other allowing anyone
    to publish two either splitter and be recieved by all subscribers
    of either splitter, with no data looping"""

    def __init__(self):
        super(Splitter, self).__init__()
        self.subscribers = []
        self.bridge_subscribers = []

    @actor_method
    def subscribe(self, callback):
        self.subscribers.append(callback)

    @actor_method
    def subscribe_bridge(self, callback):
        self.bridge_subscribers.append(callback)

    @actor_method
    def unsubscribe(self, callback):
        self.subscribers = [x for x in self.subscribers if x != callback]

    @actor_method
    def unsubscribe_bridge(self, callback):
        self.bridge_subscribers = [x for x in self.bridge_subscribers \
                                                      if x != callback]

    @actor_method
    def publish(self, data):   # Data coming in not from a bridge
        for subscriber in self.subscribers:
            subscriber(data)

        for subscriber in self.bridge_subscribers:
            subscriber(data)

    @actor_method
    def publish_bridge(self, data):
        # Data coming in from other bridges - only forward internally
        for subscriber in self.subscribers:
            subscriber(data)

    input = publish


def Backplane(name):
    plane = Splitter()
    guild.register(name, plane)
    return plane


def PublishTo(name):
    splitter = guild.lookup(name)
    return splitter


class SubscribeTo(Actor):
    def __init__(self, name):
        super(SubscribeTo, self).__init__()
        self.name = name

    def process_start(self):
        tries = 0
        while True:
            splitter = guild.lookup(self.name)
            if splitter is None:
                tries += 1
                time.sleep(0.01)
                if tries > 100:
                    raise Exception("BUST")
            else:
                break
        splitter.subscribe(self.input)

    @actor_method
    def input(self, value):
        self.output(value)

    @late_bind_safe
    def output(self, value):
        pass


class Printer(Actor):
    @actor_method
    def input(self, line):
        if isinstance(line, str):
            sys.stdout.write(line)
        else:
            sys.stdout.write(" ".join([str(x) for x in line]))
        sys.stdout.write("\n")
        sys.stdout.flush()

    @late_bind_safe
    def output(self, line):
        print("unbound, odd,", line)


if __name__ == "__main__":
    class producer(Actor):
        @process_method
        def process(self):
            #self.count +=1
            try:
                self.Print("meow")
            except UnboundActorMethod:
                pass
            #if self.count >= 20:
                #self.stop()
                #return False

        @late_bind
        def Print(self, message):
            pass

    class consumer(Actor):
        @actor_method
        def consume(self, what):
            print("Look what we go ma!", what, self)

    p = producer()
    c = consumer()
    c2 = consumer()
    c3 = consumer()
    s = Splitter()
    s.start()

    p.bind("Print", s, "publish")
    s.subscribe(c.consume)
    s.subscribe(c2.consume)
    s.subscribe(c3.consume)

    p.start()
    c.start()
    c2.start()
    c3.start()

    time.sleep(0.1)
    p.stop()
    c.stop()
    p.join()
    c.join()
