#!/usr/bin/python

class Fib:
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = b = self.basecase
        while True:
            yield ("FIB:", a)
            a, b = b, a+b


class Triangle:
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = self.basecase
        n = a + 1
        while True:
            yield ("TRIANGLE:", a)
            a = a + n
            n = n + 1


print("\nCreate 10 fibs")
fibs = [Fib(i) for i in range(10) ]

print("\nCreate 10 triangles")
triangles = [Triangle(i) for i in range(10) ]

runnables = fibs + triangles

print("\nStart the runnables")
gens = [f.main() for f in runnables ]

print("\nGive them 5 iterations")
for i in range(5):
    print( [next(x) for x in gens ] )

