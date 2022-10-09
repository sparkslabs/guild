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
            for g in self.runqueue:  # What if .add is called ?
                try:
                    next(g)
                    new_runqueue.append(g)
                except StopIteration:
                    pass
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


s = MicroScheduler()

print("\nCreate 10 fibs and 10 triangles")

for i in range(10):
    f = LimitedFibonacciPrinter(i)
    t = LimitedTrianglesPrinter(i)
    s.add(f)
    s.add(t)

print("Run them all interleaved")
s.run()

