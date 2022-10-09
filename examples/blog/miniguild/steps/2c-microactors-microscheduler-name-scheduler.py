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
        while True:
            for g in self.runqueue:
                r = next(g)


class Fib(MicroActor):
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = b = self.basecase
        while True:
            yield 1
            print("FIB:", a)
            a, b = b, a+b


class Triangle(MicroActor):
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = self.basecase
        n = a + 1
        while True:
            yield 1
            print("TRIANGLE:", a)
            a = a + n
            n = n + 1


s = MicroScheduler()

print("\nCreate 10 fibs and 10 triangles")

for i in range(10):
    f = Fib(i)
    t = Triangle(i)
    s.add(f)
    s.add(t)

print("Run them all interleaved")
s.run()

