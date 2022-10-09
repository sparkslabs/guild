#!/usr/bin/python

# File: 4e

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
        return self.greenthread

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
            try:
                (self.behaviour.tick)()
            except StopIteration:
                break
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
        def __init__(self):
            self.runqueue = deque()
            self.newqueue = deque()

        def schedule(self, *actors):
            for actor in actors:
                actor.start(self.wake_callback)
                self.newqueue.append(actor)

        def wake_callback(self, actor):
            self.newqueue.append(actor)

        def main(self):
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
                yield 1

    actor_methods = ["schedule"]

if __name__ == "__main__":


    class PrintActor(Actor):
        reactive = True
        class Behaviour:
            def input(self, *argv, **argd):
                print(*argv,**argd)


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
                print("LFP", message)

        actor_output_method = ["output"]

    class LimitedTrianglesPrinter(Actor):
        class Behaviour:
            def __init__(self, basecase=1):
                self.basecase = basecase
            def main(self):
                a = self.basecase
                n = a + 1
                for _ in range(8):
                    yield 1
                    self.output("TRIANGLE:", a)
                    a = a + n
                    n = n + 1
            def output(self, *message):
                pass
            def stop(self):
                print("STOPPING TRIANGLES")

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
                self.signal()
            def signal(self):
                "Logically for passing on the shutdown message"
                pass
            def output(self, *message):
                pass

        actor_output_methods = ["output", "signal"]

    printer = PrintActor()

    fibonnacis = LimitedFibonacciPrinter(1)
    triangles = LimitedTrianglesPrinter(1)
    primes = LimitedPrimesPrinter(99)

    fibonnacis.link("output", printer.input)
    triangles.link("output", printer.input)
    primes.link("output", printer.input)
    primes.link("signal", triangles.stop)

    s = Scheduler()
    s.schedule(printer, fibonnacis, triangles, primes)
    s.run()

    standalone_fibs = LimitedFibonacciPrinter(1)
    standalone_fibs.run()
