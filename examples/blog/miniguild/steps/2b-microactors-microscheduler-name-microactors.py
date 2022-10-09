#!/usr/bin/python

class MicroActor:
    def main(self):
        yield 1


class GeneratorClassRunner:
    def __init__(self):
        self.runnables = []

    def addRunnable(self, runnable):
        started_runnable = runnable.main()
        self.runnables.append( (runnable, started_runnable))

    def run(self):
        while True:
            for source, gen in self.runnables:
                r = next(gen)


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


runner = GeneratorClassRunner()

print("\nCreate 10 fibs and 10 triangles")

for i in range(10):
    f = Fib(i)
    t = Triangle(i)
    runner.addRunnable(f)
    runner.addRunnable(t)

print("Run them all interleaved")
runner.run()

