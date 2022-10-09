#!/usr/bin/python

class MicroActor:
    def main(self):
        yield 1


class MicroScheduler:
    def __init__(self):
        self.runqueue = []

    def add(self, microactor):
        g = microactor.main()
        self.runqueue.append(g)

    def run(self):
        while len(self.runqueue) > 0:
            new_runqueue = []
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
    class Behaviour:  # BEHAVIOUR API
        def print(self, *argv, **argd):
            print(*argv,**argd)

    def __init__(self):
        self.inbox = []
        self.behaviour = self.Behaviour()

    def print(self, *argv, **argd):   # EXTERNAL API
        self.inbox.append(("print", argv, argd))

    def main(self):
        while True:
            while self.inbox:
                msg = self.inbox.pop(0)
                func, argv, argd = msg
                if func == "print":
                    self.behaviour.print(*argv, **argd)
            yield 1


class LimitedFibonacciPrinter(MicroActor):
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

