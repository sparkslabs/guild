#!/usr/bin/python

from collections import deque

class MicroActor:
    Behaviour = None
    Behaviours = None
    reactive = False
    
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
        self.gen = None
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

    def start(self, wake_callback):
        self.gen = self.main()
        self.wake_callback = wake_callback
        return self.gen

    def handle_inqueue(self):
        msg = self.inbox.popleft()
        func, argv, argd = msg
        if hasattr(self.behaviour, func):
            f = getattr(self.behaviour, func)
            f(*argv, **argd)

    def main(self):
        while True:
            while self.inbox:
                self.handle_inqueue()
            try:
                (self.behaviour.tick)()
            except StopIteration:
                break
            yield 1


class MicroScheduler:
    def __init__(self):
        self.runqueue = deque()
        self.newqueue = deque()

    def start(self, microactor):
        microactor.start(self.wake)
        self.newqueue.append(microactor)

    def wake(self, microactor):
        self.newqueue.append(microactor)

    def run(self):
        self.runqueue = self.newqueue
        self.newqueue = deque()

        while len(self.runqueue) > 0:
            i = 0
            while i < len(self.runqueue):
                microactor = self.runqueue[i]
                try:
                    next(microactor.gen)
                    if not microactor.reactive:  # Not a source, no main loop
                        self.newqueue.append(microactor)
                    else:
                        microactor.sleeping = True
                except StopIteration:
                    pass
                i += 1
            self.runqueue = self.newqueue
            self.newqueue = deque()



class PrintActor(MicroActor):
    reactive = True
    class NormalBehaviour:  # Normal Behaviour
        def print(self, *argv, **argd):
            print(*argv,**argd)
    
    class PausedBehaviour: # Behaviour when printing is paused
        def print(self, *argv, **argd):
            pass # Just throw away output

    Behaviours = [ NormalBehaviour, PausedBehaviour ]

    def print(self, *argv, **argd):   # EXTERNAL API
        self.inbox.append(("print", argv, argd))
        self.wake()



class LimitedFibonacciPrinter(MicroActor):
    class Behaviour:
        def __init__(self, printer, basecase=1):
            self.basecase = basecase
            self.printer = printer
        def main(self):
            a = b = self.basecase
            for _ in range(5):
                yield 1
                self.printer.print("FIB:", a)
                a, b = b, a+b


class LimitedTrianglesPrinter(MicroActor):
    class Behaviour:
        def __init__(self, printer, basecase=1):
            self.basecase = basecase
            self.printer = printer
        def main(self):
            a = self.basecase
            n = a + 1
            for _ in range(5):
                yield 1
                self.printer.print("TRIANGLE:", a)
                a = a + n
                n = n + 1


def isprime(n):
    for i in range(2,n):
        if n % i == 0:
            return False
    return True


class LimitedPrimesPrinter(MicroActor):
    class Behaviour:
        def __init__(self, printer, basecase=1):
            self.basecase = basecase
            self.printer = printer
        def main(self):
            a =  self.basecase
            for _ in range(5):
                while not isprime(a):
                    a += 1
                yield 1
                self.printer.print("PRIME:", a)
                a += 1

if __name__ == "__main__":
    pa = PrintActor()
    lfp = LimitedFibonacciPrinter(pa, 1)
    ltp = LimitedTrianglesPrinter(pa, 1)
    lpp = LimitedPrimesPrinter(pa, 99)
    
    s = MicroScheduler()
    s.start(pa)
    s.start(lfp)
    s.start(ltp)
    s.start(lpp)
    s.run()

