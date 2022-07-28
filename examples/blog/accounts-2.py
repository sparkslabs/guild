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
        print( "DEPOSIT", "\t", amount, "\t", self.balance )
        self.balance = self.balance + amount
        return self.balance

    @actor_function
    def withdraw(self, amount):
        if self.balance < amount:
            raise InsufficientFunds("Insufficient Funds in your account",
                                    requested=amount,
                                    balance=self.balance)
        self.balance = self.balance - amount
        print( "WITHDRAW", "\t", amount, "\t", self.balance )
        return amount


class MoneyDrain(Actor):
    def __init__(self, sharedaccount):
        super(MoneyDrain, self).__init__()
        self.sharedaccount = sharedaccount
        self.grabbed = 0

    @process_method
    def process(self):
        try:
            to_grab = random.choice([10, 20, 40, 80, 160])
            grabbed = self.sharedaccount.withdraw(to_grab)
        except InsufficientFunds as e:
            print( "Awww, Tapped out", e.balance, "<", e.requested )
            self.stop()
            return
        self.grabbed = self.grabbed + grabbed


class MoneySource(Actor):
    def __init__(self, sharedaccount):
        super(MoneySource, self).__init__()
        self.sharedaccount = sharedaccount

    @process_method
    def process(self):
        self.sharedaccount.deposit(random.randint(1, 100))


account = Account(1000).go()

fred = MoneyDrain(account).go()
barney = MoneyDrain(account).go()
betty = MoneyDrain(account).go()

wilma = MoneySource(account).go()  # Wilma carries all of them.

wait_for(fred, barney, betty)
wilma.stop()
wilma.join()

account.stop()
account.join()

print( "GAME OVER" )

print( "Fred grabbed", fred.grabbed )
print( "Wilma grabbed", barney.grabbed)
print( "Betty grabbed", betty.grabbed)
print( "Total grabbed", fred.grabbed + barney.grabbed + betty.grabbed)
print( "Since they stopped grabbing...")
print( "Money left", account.balance)
