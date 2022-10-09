#!/usr/bin/python
"""mini-guild

A simplified version of guild without the full set of capabilities.
Has some extra (novel) features:

* Actors are generator based, and default to running in a global context
* Scheduler is an actor and can be run in a thread is desired
* Actors can be threaded.
* Virtually no difference between threaded and non-threaded actors

Has actor_methods and late bound methods.

"""
#---------------------------------------------------------------------------
import sys
import time
import threading

# NOTE: deque (pop/append) is threadsafe, and quicker than a list..
from collections import deque

def mkActorMethod(self, func_name):
    def actor_method(*argv, **argd):
        self.inbox.append((func_name, argv, argd))
        self.sleeping = False
        (self.wake_callback)(self)
    return actor_method

class Actor:
    blocking = False
    Behaviour = None # Override with your behaviour
                     # doesn't have to be a special class
    Behaviours = []
    default_actor_methods = ["input"]
    actor_methods = []

    def __init__(self, *argv, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            if self.Behaviours == []:
                raise Exception("You do not call Actor directly."
                                 "Inherit and override Behaviour")

            self.Behaviour = self.Behaviours[0] # Default behaviour

        self.argv = argv
        self.argd = argd
        self.greenthread = None
        self.inbox = deque()
        self.active = False
        self.sleeping = False
        self.reactive = False
        self.become(self.Behaviour)
        self.wake_callback = lambda x: None
        self._thread = None

    def initialiseBehaviour(self, *argv, **argd):
        self._behaviour = (self.Behaviour)(*argv, **argd)
        for name in self.default_actor_methods + self.actor_methods:
            if name in self.Behaviour.__dict__:
                setattr(self, name, mkActorMethod(self, name))
        self._behaviour.become = self.become
        if not hasattr(self._behaviour, "tick"):
            if hasattr(self._behaviour, "main"):
                self._behaviour.greenthread = self._behaviour.main()
                self._behaviour.tick = self._behaviour.greenthread.__next__
            else:
                self.reactive = True
                self.sleeping = True

        self._behaviour._wrapper = self

    def become(self, behaviour_class):
        self.Behaviour = behaviour_class
        self.initialiseBehaviour(*self.argv, **self.argd)

    def start(self, wake_callback=None):
        self.greenthread = self.main()
        self.active = True
        if wake_callback:
            self.wake_callback = wake_callback
        return self

    def tick(self):
        try:
            live = next(self.greenthread)
            return live
        except StopIteration:
            return False

    def handle_inbox(self):
        call = self.inbox.popleft()
        func_name, argv, argd = call[0], call[1], call[2]
        func = getattr(self._behaviour, func_name)
        func(*argv, **argd)

    def main(self):
        while self.active:
            yield 1
            while (self.inbox  and self.active):
                self.handle_inbox()
            if not self.reactive:
                if self.active and not self.sleeping:
                    try:
                        self._behaviour.tick()
                    except StopIteration: # Shutdown request
                        self.active = False # Shutdown

    def link(self, methodname, target):
        setattr(self._behaviour, methodname, target)

    def isactive(self):
        return self.active

    def issleeping(self):
        return self.sleeping

    def stop(self):
        if hasattr(self._behaviour, "stop"):
#            self._behaviour.stop()
            self.inbox.append(("stop", ))
        self.active = False
        self.sleeping = False

    def _run(self):
        self.start()
        for i in self.main():
            pass

    def run(self, run_in_thread=False):
        if self.blocking or run_in_thread:
            self.background()
            self.join()
        else:
            self._run()

    def background(self):
        "Run this actor in the background"
        self._thread = threading.Thread(target=self._run)
        self._thread.start()
        return self

    def join(self):
        "Wait for this actor's thread to finish"
        if self._thread is not None:
            self._thread.join()
        else:
            print("WARNING: join called on a non-threaded actor")


class ThreadActor(Actor):
    blocking = True


class Scheduler(Actor):
    blocking = True
    class Behaviour:
        def __init__(self, maxrun=None, initialise=lambda : None):

            self.actors = deque()
            self.nactors = deque()
            self.maxrun = maxrun
            self.initialise = initialise
            print("NUMBER OF THREADS", threading.active_count())

        def schedule(self, *actors):
            print("NUMBER OF THREADS", threading.active_count())
            for actor in actors:
                actor.start(self.wake)
                if not actor.sleeping:
                    self.actors.append(actor)
            if self.initialise:
                (self.initialise)()
                self.initialise = None # run once

        def wake(self, actor):
            self.actors.append(actor)

        def main(self):
            ticks = 0
            nactors = deque()
            while len(self.actors) > 0:
                yield 1
                if self.maxrun:
                    ticks +=1

                i = 0
                while i < len(self.actors):
                    actor = self.actors[i]
                    i += 1
                    try:
                        actor.tick() # TICK!
                    except StopIteration:
                        continue # Skip rest of loop body
                    if actor.active:
                        if not actor.sleeping:
                            nactors.append(actor)
                if self.maxrun and (ticks >= self.maxrun):
                    [x.stop() for x in self.actors]

                self.actors = nactors
                nactors = deque()

    actor_methods = ["wake","schedule"]




if __name__ == "__main__":
    print("See examples in this directory")
    print("Note: This is a mini-guild, not guild and has missing features")
