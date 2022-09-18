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

import sys
import time
import threading

# NOTE: Python's deque is threadsafe, and quicker than a list..
from collections import deque

# This is likely the wrong approach to dealing with a threading scheduler. Feels/seems wrong.

SCHEDULER_IN_THREAD = True
#SCHEDULER_IN_THREAD = False

def mkActorMethod(self, func_name):
    def actor_method(*args, **argd):
        self.inputqueue.append((func_name, args, argd))
        self.sleeping = False
        (self.wake_callback)(self)
    return actor_method

class Actor:
    Behaviour = None # Override with your behaviour
                     # doesn't have to be a special class
    Behaviours = []
    default_actor_methods = ["input"]
    actor_methods = []

    def __init__(self, *args, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            if self.Behaviours == []:
                raise Exception("You do not call Actor directly."
                                 "Inherit and override Behaviour")

            self.Behaviour = self.Behaviours[0] # Default behaviour

        self.args = args
        self.argd = argd
        self.greenthread = None
        self.inputqueue = deque()
        self.active = False
        self.sleeping = False
        self.reactive = False
        self.become(self.Behaviour)
        self.wake_callback = lambda x: None

    def initialiseBehaviour(self, *args, **argd):
        self._behaviour = (self.Behaviour)(*args, **argd)
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
        self.initialiseBehaviour(*self.args, **self.argd)

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

    def handle_inqueue(self):
        call = self.inputqueue.popleft()
        func_name, argv, argd = call[0], call[1], call[2]
        func = getattr(self._behaviour, func_name)
        func(*argv, **argd)

    def main(self):
        while self.active:
            yield 1
            while (self.inputqueue  and self.active):
                self.handle_inqueue()
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
            self.inputqueue.append(("stop", ))
        self.active = False
        self.sleeping = False

    def run(self):
        self.start()
        for i in self.main():
            pass


class ThreadActor(threading.Thread, Actor): # Experiment
    def __init__(self, *args, **argd):
        # Can't use super() --> args to __init__ differ in base classes
        Actor.__init__(self, *args, **argd)
        threading.Thread.__init__(self)

    def actor_start(self, *args):
        Actor.start(self, *args)

    def run(self):
        self.actor_start()
        for i in self.main():
            pass


if SCHEDULER_IN_THREAD:
    scheduler_class = ThreadActor
else:
    scheduler_class = Actor


class SchedulerActor(scheduler_class):
    class Behaviour:
        def __init__(self, maxrun=None, initialise=lambda : None):
            self.actors = deque()
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

        def main(self):                           # NOTE: Name
            ticks = 0
            while len(self.actors) > 0:
                yield 1                           # NOTE: added 'yield'
                nactors = deque()
                if self.maxrun:
                    ticks +=1

                i = 0
                # We do this, not "for" because of waking actors
                # The alternative is less clear
                while i < len(self.actors):
                    actor = self.actors[i]
                    try:
                        actor.tick() # TICK!
                    except StopIteration:
                        continue # Skip rest of loop body
                    if actor.active:
                        if not actor.sleeping:
                            nactors.append(actor)
                    i += 1
                if self.maxrun and (ticks >= self.maxrun):
                    [x.stop() for x in self.actors]

                self.actors = nactors

    actor_methods = ["wake","schedule"]


def run_scheduler(s):
    if SCHEDULER_IN_THREAD:
        s.start()
        s.join()
    else:
        s.run()


if __name__ == "__main__":
    print("See examples in this directory")
    print("Note: This is a mini-guild, not guild and has missing features")
