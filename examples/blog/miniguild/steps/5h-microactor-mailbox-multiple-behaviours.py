#!/usr/bin/python

from collections import deque

class MicroActor:
    Behaviour = None
    Behaviours = None
    
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

    def become(self, BehaviourClass):
        self.behaviour = BehaviourClass(*self.argv, **self.argd)
        self.behaviour.tick = lambda : None
        if hasattr(self.behaviour, "main"):
            self.behaviour.greenthread = self.behaviour.main()
            self.behaviour.tick = self.behaviour.greenthread.__next__

    def main(self):
        while True:
            while self.inbox:
                msg = self.inbox.popleft()
                func, argv, argd = msg
                if hasattr(self.behaviour, func):
                    f = getattr(self.behaviour, func)
                    f(*argv, **argd)
            try:
                (self.behaviour.tick)()
            except StopIteration:
                break
            yield 1


class MicroScheduler:
    def __init__(self):
        self.runqueue = deque()

    def add(self, microactor):
        g = microactor.main()
        self.runqueue.append(g)

    def run(self):
        while len(self.runqueue) > 0:
            new_runqueue = deque()
            i = 0
            while i < len(self.runqueue):
                g = self.runqueue[i]
                try:
                    next(g)
                    new_runqueue.append(g)
                except StopIteration:
                    pass
                i += 1
            self.runqueue = new_runqueue


class PrintActor(MicroActor):
    class NormalBehaviour:  # Normal Behaviour
        def print(self, *argv, **argd):
            print(*argv,**argd)
    
    class PausedBehaviour: # Behaviour when printing is paused
        def print(self, *argv, **argd):
            pass # Just throw away output

    Behaviours = [ NormalBehaviour, PausedBehaviour ]

    def print(self, *argv, **argd):   # EXTERNAL API
        self.inbox.append(("print", argv, argd))



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
    s.add(pa)
    s.add(lfp)
    s.add(ltp)
    s.add(lpp)
    s.run()

