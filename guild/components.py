#!/usr/bin/python

from actor import Actor, actor_method, process_method, late_bind, UnboundActorMethod
import time
import sys

class Splitter(Actor):
    def __init__(self):
        super(Splitter,self).__init__()
        self.subscribers = []

    @actor_method
    def subscribe(self, callback):
        #print "SUBSCRIBE", callback
        #print "         LIST", self.subscribers
        self.subscribers.append(callback)

    @actor_method
    def unsubscribe(self, callback):
        #print "UNSUBSCRIBE", callback
        #print "           LIST", self.subscribers
        self.subscribers = [ x for x in self.subscribers if x != callback ]

    @actor_method
    def publish(self, data):
        for subscriber in self.subscribers:
            subscriber(data)

    input = publish


class Printer(Actor):
  @actor_method
  def input(self, line):
      if isinstance(line,str):
          sys.stdout.write(line)
      else:
          sys.stdout.write(" ".join([ str(x) for x in line]) )
      sys.stdout.write("\n")
      sys.stdout.flush()

if __name__ == "__main__":
    class producer(Actor):
        @process_method
        def process(self):
            #self.count +=1
            try:
                self.Print( "meow" )
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
            print "Look what we go ma!", what, self

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