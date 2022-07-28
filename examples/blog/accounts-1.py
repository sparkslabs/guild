#!/usr/bin/python

import random

from guild.actor import *


class InsufficientFunds(ActorException):
    pass


class Account(Actor):
    def __init__(self, balance=10):
        super(Account, self).__init__()
        self.balance = balance

    @actor_function
    def deposit(self, amount):
        # This is a function to allow the deposit to be confirmed
        print( "DEPOSIT", "\t", amount, "\t", self.balance)
        self.balance = self.balance + amount
        return self.balance

    @actor_function
    def withdraw(self, amount):
        if self.balance < amount:
            raise InsufficientFunds("Insufficient Funds in your account",
                                    requested=amount,
                                    balance=self.balance)
        self.balance = self.balance - amount
        print( "WITHDRAW", "\t", amount, "\t", self.balance)
        return amount


account = Account(1000).go()

fred, barney, wilma = 0, 0, 0
try:
    while True:
        account.deposit(100)
        fred += account.withdraw(random.choice([10, 20, 40, 80, 160]))
        barney += account.withdraw(random.choice([10, 20, 40, 80, 160]))
        wilma += account.withdraw(random.choice([10, 20, 40, 80, 160]))
except InsufficientFunds as e:
    print( e.args )
    print( "Balance", e.balance )
    print( "Requested", e.requested )
    print( account.balance )


print( "GAME OVER" )

print( "Fred grabbed", fred )
print( "Wilma grabbed", wilma )
print( "Barney grabbed", barney )

account.stop()
account.join()
