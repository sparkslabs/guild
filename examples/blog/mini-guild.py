#!/usr/bin/python
"""mini-guild

A simplified version of guild without the full set of capabilities.
Has actor_methods and late bound methods.

"""
def mkActorMethod(self, func_name):
    def actor_method(*args, **argd):
        self.inputqueue.append((func_name, args, argd))
        self.sleeping = False
        self.scheduler.wake(self)
    return actor_method

class Actor:
    Behaviour = None # Override with your behaviour, doesn't have to be a special class
    Behaviours = []
    default_actor_methods = ["input"]
    actor_methods = []

    def __init__(self, *args, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            if self.Behaviours != []:
                self.Behaviour = self.Behaviours[0]
            else:
                raise Exception("You do not call Actor directly. Inherit and override Behaviour")
        self.args = args
        self.argd = argd
        self.greenthread = None
        self.inputqueue = []
        self.active = False
        self.sleeping = False
        self.passive = False
        self.become(self.Behaviour)

    def initialiseBehaviour(self, *args, **argd):
        self._behaviour = (self.Behaviour)(*args, **argd)
        for name in self.default_actor_methods + self.actor_methods:
            if name in self.Behaviour.__dict__:
                setattr(self, name, mkActorMethod(self, name))
        self._behaviour.become = self.become
        if not hasattr(self._behaviour, "tick"):
            self.passive = True
            self.sleeping = True

        self._behaviour._wrapper = self

    def become(self, behaviour_class):
        self.Behaviour = behaviour_class
        self.initialiseBehaviour(*self.args, **self.argd)

    def start(self, scheduler):
        self.greenthread = self.main()
        self.active = True
        self.scheduler = scheduler
        return self

    def tick(self):
        try:
            live = next(self.greenthread)
            return live
        except StopIteration:
            return False

    def handle_inqueue(self):
        call = self.inputqueue.pop(0)
        func_name, argv, argd = call[0], call[1], call[2]
        #print(func_name, args)
        func = getattr(self._behaviour, func_name)
        func(*argv, **argd)

    def main(self):
        while self.active:
            yield 1
            while (self.inputqueue  and self.active):
                self.handle_inqueue()
            if not self.passive:
                if self.active and not self.sleeping:
                    self._behaviour.tick()

    def link(self, methodname, target):
        setattr(self._behaviour, methodname, target)

    def isactive(self):
        return self.active

    def issleeping(self):
        return self.sleeping

    def stop(self):
        if hasattr(self._behaviour, "stop"):
            self.inputqueue.append(("stop", ))
        self.active = False
        self.sleeping = False


class Scheduler:
    def __init__(self, maxrun=None):
        self.actors = []
        self.maxrun = maxrun

    def schedule(self, *actors):
        for actor in actors:
            actor.start(self)
            if not actor.sleeping:
                self.actors.append(actor)

    def wake(self, actor):
        self.actors.append(actor)

    def run(self):
        ticks = 0
        while len(self.actors) > 0:
            nactors = []
            if self.maxrun:
                ticks +=1
            for actor in self.actors:
                actor.tick()
                if actor.active:
                    if not actor.sleeping:
                        nactors.append(actor)
            if self.maxrun and (ticks >= self.maxrun):
                [x.stop() for x in self.actors]

            self.actors = nactors


class API:
    """"Not technically needed in this version (remnants of "`Activity` actor"""
    def input(self, data):
        pass
    def output(self, data):
        raise Exception("base class `output` called directly - you should link over this")


class Producer(Actor):
    class Behaviour:
        def __init__(self, message):
            super(Producer.Behaviour, self).__init__()
            self.message = message
            self.greenthread = self.main()  # This could be pushed into API
            self.tick = self.greenthread.__next__

        def main(self):
            while True:
                yield 1
                self.output(self.message)


class Consumer(Actor):
    class Behaviour:
        def __init__(self):
            super(Consumer.Behaviour, self).__init__()
            self.count = 0
        def input(self, data):
            self.count += 1
            print("Consumed:", data, self.count)
            self.sleeping = True

        def munch(self, data):
            self.count += 1
            print("Munched:", data, self.count)
            self.sleeping = True

    actor_methods = ["munch"]


class Door(Actor):
    class OpenBehaviour:
        def open(self):
            print("OPEN:open.  The Door is already open!")
        def close(self):
            print("OPEN:close. The door is now closed!")
            self.become(Door.ClosedBehaviour)

    class ClosedBehaviour:
        def open(self):
            print("CLOSE:open.  The door is now open!")
            self.become(Door.OpenBehaviour)
        def close(self):
            print("CLOSE:close. The Door is already closed!")

    actor_methods = ["open","close"]
    Behaviours = ClosedBehaviour, OpenBehaviour

import time
class RingPinger(Actor):
    class Behaviour:
        def __init__(self, next_actor=None):
            self.next_actor = next_actor
            self.start = time.time()

        def ping(self, message):
            if message[0] == self._wrapper:
                now = time.time()
                #print("LOOPTIME", now-self.start)
                self.start = now

                if message[1] == 1:
                    self._wrapper.stop()
                message[1] -= 1
                self.next_actor.ping(message)
            else:
                self._wrapper.sleeping = True
                if message[1] == 1:
                    self._wrapper.stop()
                self.next_actor.ping(message)

        def set_next(self, next_actor):
            self.next_actor = next_actor

    actor_methods = ["ping","set_next"]

if __name__ == "__main__":

    import sys

    N = int(sys.argv[1])
    M = int(sys.argv[2])
    print("n, m", repr(N), repr(M))

    first = RingPinger()
    last = first
    pingers = [first]
    for _ in range(N):
        last = RingPinger(last)
        pingers.append(last)

    import time
    s = Scheduler()

    s.schedule(*pingers)

    first.set_next(last)
    last.ping( [first, M] )

    start = time.time()
    print("START", start, time.asctime())
    s.run()
    end = time.time()
    print("END  ", end, time.asctime())
    print("DURATION:", end-start)

if 0:
    s = Scheduler()
    d = Door()

    d.open()
    d.open()
    d.close()
    d.close()
    d.open()
    d.open()

    p = Producer("Hello")
    c = Consumer()
    p.link("output", c.munch)
    s.schedule(p, c, d )

