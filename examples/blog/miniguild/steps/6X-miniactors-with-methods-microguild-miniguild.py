#!/usr/bin/python

# File: 4

from collections import deque

def mkActorMethod(self, func_name):
    def actor_method(*argv, **argd):
        self.inbox.append((func_name, argv, argd))
        self.wake()
    return actor_method

class Actor:
    Behaviour = None
    Behaviours = None
    reactive = False

    default_actor_methods = ["input"]
    actor_methods = []

    def __init__(self, *argv, **argd):
        super(Actor, self).__init__()
        self.argv = argv
        self.argd = argd
        self.inbox = deque()
        if self.Behaviour:
            self.become(self.Behaviour)
        elif self.Behaviours:
            self.become(self.Behaviours[0])
        else:
            raise Exception("No behaviour defined")
        self.greenthread = None
        self.wake_callback = lambda x : None
        self.sleeping = True if self.reactive else False
        self.active = False      # Set to true when the actor is awake, and used to allow graceful shutdown

    def wake(self):
        if self.sleeping:
            self.sleeping = False
            if self.wake_callback:
               (self.wake_callback)(self)

    def become(self, BehaviourClass):
        self.behaviour = BehaviourClass(*self.argv, **self.argd)
        self.behaviour.tick = lambda : None
        if hasattr(self.behaviour, "main"):
            self.behaviour.greenthread = self.behaviour.main()
            self.behaviour.tick = self.behaviour.greenthread.__next__
        else:
            self.reactive = True
            self.sleeping = True

        for name in self.default_actor_methods:
            if name in self.behaviour.__class__.__dict__:
                setattr(self, name, mkActorMethod(self, name))

        for name in self.actor_methods:
            if name in self.behaviour.__class__.__dict__:
                setattr(self, name, mkActorMethod(self, name))
            else:
                print("name", name, "to add to", self, "NOT in", self.behaviour.__class__.__dict__)

        self.behaviour.become = self.become
        self.behaviour._wrapper = self


    def start(self, wake_callback=None):
        if wake_callback:
            self.wake_callback = wake_callback
        self.greenthread = self.main()
        self.active = True
        self.tick = self.greenthread.__next__
        return self

    def handle_inbox(self):
        msg = self.inbox.popleft()
        func, argv, argd = msg
        if hasattr(self.behaviour, func):
            f = getattr(self.behaviour, func)
            f(*argv, **argd)

    def handle_stop(self):
        while self.inbox:
            msg = self.inbox.popleft()
            func, argv, argd = msg
            if func == "stop":
                if hasattr(self.behaviour, func):
                    f = getattr(self.behaviour, func)
                    f(*argv, **argd)

    def main(self):
        while self.active:
            while self.inbox and self.active:
                self.handle_inbox()
            if not self.reactive:
                if self.active and not self.sleeping:
                    try:
                        self.behaviour.tick()
                    except StopIteration: # Shutdown request
                        self.active = False # Shutdown
            yield 1
        self.handle_stop()

    def link(self, methodname, target):             # Needs to be an actor method later on
        setattr(self.behaviour, methodname, target)

    def stop(self):
        if hasattr(self.behaviour, "stop"):
            self.inbox.append(("stop", [], {}))
        self.active = False
        self.sleeping = False

    def run(self):
        self.start()
        for i in self.main():
            pass


class Scheduler(Actor):
    class Behaviour:
        def __init__(self, maxrun=None, initialise=lambda : None):
            self.runqueue = deque()
            self.newqueue = deque()
            self.maxrun = maxrun
            self.initialise = initialise

        def schedule(self, *actors):
            for actor in actors:
                actor.start(self.wake_callback)
                if not actor.sleeping:
                    self.runqueue.append(actor)
            if self.initialise:
                (self.initialise)()
                self.initialise = None # run once

        def wake_callback(self, actor):
            self.runqueue.append(actor)

        def main(self):
            ticks = 0
            newqueue = deque()
            while len(self.runqueue) > 0:
                yield 1
                if self.maxrun:
                    ticks +=1

                i = 0
                while i < len(self.runqueue):
                    actor = self.runqueue[i]
                    i += 1
                    try:
                        actor.tick() # TICK!
                    except StopIteration:
                        continue # Skip rest of loop body
                    if actor.active:
                        if not actor.sleeping:
                            newqueue.append(actor)
                if self.maxrun and (ticks >= self.maxrun):
                    [x.stop() for x in self.runqueue]

                self.runqueue = newqueue
                newqueue = deque()

    actor_methods = ["schedule"]




if __name__ == "__main__":
    print("See examples in this directory")
    print("Note: This is a mini-guild, not guild and has missing features")
