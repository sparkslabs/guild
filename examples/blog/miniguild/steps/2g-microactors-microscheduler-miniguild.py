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


class LimitedFibonacciPrinter(MicroActor):
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = b = self.basecase
        for _ in range(5):
            yield 1
            print("FIB:", a)
            a, b = b, a+b


class LimitedTrianglesPrinter(MicroActor):
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = self.basecase
        n = a + 1
        for _ in range(5):
            yield 1
            print("TRIANGLE:", a)
            a = a + n
            n = n + 1


def isprime(n):
    for i in range(2,n):
        if n % i == 0:
            return False
    return True


class LimitedPrimesPrinter(MicroActor):
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a =  self.basecase
        for _ in range(5):
            while not isprime(a):
                a += 1
            yield 1
            print("PRIME:", a)
            a += 1


if __name__ == "__main__":
    m = MicroActor()
    g = m.main()
    print("Sample run of MicroActor by itself")
    print(next(g))
    try:
        print(next(g))
    except StopIteration:
        print("StopIteration raised as expected when the MicroActor terminates")


    print("\nSample run of 3 Microactors concurrently")
    lfp = LimitedFibonacciPrinter(1)
    ltp = LimitedTrianglesPrinter(1)
    lpp = LimitedPrimesPrinter(99)

    s = MicroScheduler()
    s.add(lfp)
    s.add(ltp)
    s.add(lpp)
    s.run()

