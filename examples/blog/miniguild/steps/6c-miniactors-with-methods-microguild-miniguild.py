#!/usr/bin/python

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

    actor_methods = []

    def __init__(self, *argv, **argd):
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
        self.wake_callback = None
        self.sleeping = True if self.reactive else False

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
        for name in self.actor_methods:
            if name in self.behaviour.__class__.__dict__:
                setattr(self, name, mkActorMethod(self, name))
            else:
                print("name", name, "to add to", self, "NOT in", self.behaviour.__class__.__dict__)

    def link(self, methodname, target):             # Needs to be an actor method later on
        setattr(self.behaviour, methodname, target)

    def start(self, wake_callback):
        self.greenthread = self.main()
        self.wake_callback = wake_callback
        return self.greenthread

    def handle_inbox(self):
        msg = self.inbox.popleft()
        func, argv, argd = msg
        if hasattr(self.behaviour, func):
            f = getattr(self.behaviour, func)
            f(*argv, **argd)

    def main(self):
        while True:
            while self.inbox:
                self.handle_inbox()
            try:
                (self.behaviour.tick)()
            except StopIteration:
                break
            yield 1


class Scheduler:
    def __init__(self):
        self.runqueue = deque()
        self.newqueue = deque()

    def start(self, actor):
        actor.start(self.wake)
        self.newqueue.append(actor)

    def wake(self, actor):
        self.newqueue.append(actor)

    def run(self):
        self.runqueue = self.newqueue
        self.newqueue = deque()

        while len(self.runqueue) > 0:
            i = 0
            while i < len(self.runqueue):
                actor = self.runqueue[i]
                try:
                    next(actor.greenthread)
                    if not actor.reactive:  # Not a source, no main loop
                        self.newqueue.append(actor)
                    else:
                        actor.sleeping = True
                except StopIteration:
                    pass
                i += 1
            self.runqueue = self.newqueue
            self.newqueue = deque()

if __name__ == "__main__":


    class PrintActor(Actor):
        reactive = True
        class Behaviour:
            def print(self, *argv, **argd):
                print(*argv,**argd)

        actor_methods = ["print"]


    class LimitedFibonacciPrinter(Actor):
        class Behaviour:
            def __init__(self, basecase=1):
                self.basecase = basecase
            def main(self):
                a = b = self.basecase
                for _ in range(5):
                    yield 1
                    self.output("FIB:", a)
                    a, b = b, a+b
            def output(self, *message):
                pass

        actor_output_method = ["output"]


    class LimitedTrianglesPrinter(Actor):
        class Behaviour:
            def __init__(self, basecase=1):
                self.basecase = basecase
            def main(self):
                a = self.basecase
                n = a + 1
                for _ in range(5):
                    yield 1
                    self.output("TRIANGLE:", a)
                    a = a + n
                    n = n + 1
            def output(self, *message):
                pass

        actor_output_method = ["output"]


    def isprime(n):
        for i in range(2,n):
            if n % i == 0:
                return False
        return True


    class LimitedPrimesPrinter(Actor):
        class Behaviour:
            def __init__(self, printer, basecase=1):
                self.basecase = basecase
            def main(self):
                a =  self.basecase
                for _ in range(5):
                    while not isprime(a):
                        a += 1
                    yield 1
                    self.output("PRIME:", a)
                    a += 1
            def output(self, *message):
                pass

        actor_output_method = ["output"]

    pa = PrintActor()

    lfp = LimitedFibonacciPrinter(1)
    ltp = LimitedTrianglesPrinter(1)
    lpp = LimitedPrimesPrinter(99)

    lfp.link("output", pa.print)
    ltp.link("output", pa.print)
    lpp.link("output", pa.print)
    
    s = Scheduler()
    s.start(pa)
    s.start(lfp)
    s.start(ltp)
    s.start(lpp)
    s.run()

