#!/usr/bin/python

def fib(basecase=1):
    a = b = basecase
    while True:
        yield a
        a, b = b, a+b

print("Simple fib")
fib_gen = fib()
print(next(fib_gen))
print(next(fib_gen))
print(next(fib_gen))
print(next(fib_gen))

print("\nCreate 10 fib_gens")
fib_gens = [fib(i) for i in range(10) ]
print(fib_gens)

print("\nGive them 5 iterations")
for i in range(5):
    print( [next(x) for x in fib_gens ] )

