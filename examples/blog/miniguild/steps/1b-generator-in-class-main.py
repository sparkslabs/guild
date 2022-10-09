#!/usr/bin/python

class Fib:
    def __init__(self, basecase=1):
        self.basecase = basecase
    def main(self):
        a = b = self.basecase
        while True:
            yield a
            a, b = b, a+b


print("Simple fib")
f = Fib()
g = f.main()
print(next(g))
print(next(g))
print(next(g))
print(next(g))

print("\nCreate 10 fibs")
fibs = [Fib(i) for i in range(10) ]
print(fibs)

print("\nStart the fibs")
fib_gens = [f.main() for f in fibs ]

print("\nGive them 5 iterations")
for i in range(5):
    print( [next(x) for x in fib_gens ] )

