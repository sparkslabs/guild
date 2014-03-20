#!/usr/bin/python

import random
import sys


def is_prime(n):
    if n == 2 or n == 3:
        return True
    if n < 2 or n % 2 == 0:
        return False
    if n < 9:
        return True
    if n % 3 == 0:
        return False
    r = int(n ** 0.5)
    f = 5
    while f <= r:
        if n % f == 0:
            return False
        if n % (f + 2) == 0:
            return False
        f += 6
    return True


def big_prime():
    k = random.randint(2 ** 8, 2 ** 10)
    while not is_prime(k):
        k += 1
    return k


def small_prime():
    k = random.randint(2 ** 2, 2 ** 5)
    while not is_prime(k):
        k += 1
    return k


p = big_prime()    # Prime Number
q = big_prime()    # Prime Number
e = small_prime()  # Chosen, public prime

#p = 13 # Prime Number
#q = 11 # Prime Number
#e = 7 # Chosen, public prime

N = p * q

public_key = N, e

print "Public_key", N, e


def find_private_key(p, q, e):
    d = 0
    found = False
    while not found:
        x = (e * d % ((p - 1) * (q - 1)))
        if x == 1:
            found = True
        else:
            d = d + 1
        if d % 10000 == 0:
            print "Checking above", d, p, q, e
        if d > 8000000:
            raise Exception("Bollocks")
    return d

d = find_private_key(p, q, e)
private_key = d
print "Public_key", N, e
print "Private Key", d


def encrypt_value(value, N, e):   # Encrypt with public key
    cipher_text = (value ** e) % N
    return cipher_text


def decrypt_value(value, private_key, N):
    d = private_key
    plain_text = (value ** d) % N
    return plain_text


message = "Hello World"
message_list = [x for x in message]
print message_list
message_values = [ord(x) for x in message]
print message_values
encrypted_message = [encrypt_value(ord(x), N, e) for x in message]
print "CIPHER TEXT:", encrypted_message

decrypted_message_raw = []
for x in encrypted_message:
    pt = decrypt_value(x, d, N)
    decrypted_message_raw.append(pt)
    sys.stdout.write(str(pt) + " ")
    sys.stdout.flush()


print decrypted_message_raw

decrypted_message_letters = [chr(x) for x in decrypted_message_raw]
print decrypted_message_letters
print "".join(decrypted_message_letters)

print "p", p
print "q", q
print "e", e
print "d", d
print "N", N

"""
secret_num_1 = secret_prime_1 -1
secret_num_2 = secret_prime_2 -1

public_prime * private_prime  % (secret_num_1 * secret_num_2)

Then:
    Secret Information (can be thrown away after keys created!):
        secret_prime_1
        secret_prime_2

    Shared information:
        N = secret_prime_1*secret_prime_2
        public_prime

    Private Information:
        private_prime

    C = (D ** public_prime) % N
    D = (C ** private_prime) % N

    Security of this depends crucially on N being difficult to factor.
    That is the secrecy of
        secret_prime_1, secret_prime_2
"""
