#!/usr/bin/python

import random
from guild.actor import *

import time

SHOWRACE = True

def microsleep():
    if SHOWRACE:
        i = random.random()*0.000001
        time.sleep(i)

class InsufficientFunds(ActorException):
    pass


class Account(Actor):
    def __init__(self, balance=10):
        super(Account, self).__init__()
        self.balance = balance

    # Removing the Actor Function decorator to show what breaks/goes wrong
    def deposit(self, amount):
        # This is a function to allow the deposit to be confirmed
        microsleep()
        balance = self.balance
        microsleep()
        balance = balance + amount
        microsleep()
        self.balance = balance
        microsleep()
        return self.balance

    # Removing the Actor Function decorator to show what breaks/goes wrong
    def withdraw(self, amount):
        microsleep()
        if self.balance < amount:
            raise InsufficientFunds("Insufficient Funds in your account",
                                    requested=amount,
                                    balance=self.balance)
        microsleep()
        balance = self.balance
        microsleep()
        balance = balance - amount
        microsleep()
        self.balance = balance
        microsleep()
#        self.balance = self.balance - amount
#        print("WITHDRAW", "\t", amount, "\t", self.balance)
        return amount


def transfer(amount, payer, payee):
    funds = payer.withdraw(amount)
    payee.deposit(funds)


class MischiefMaker(Actor):
    def __init__(self, myaccount, friendsaccount):
        super(MischiefMaker, self).__init__()
        self.myaccount = myaccount
        self.friendsaccount = friendsaccount
        self.grabbed = 0

    @process_method
    def process(self):
        try:
            grab = random.randint(1, 10) * 10
            transfer(grab, self.friendsaccount, self.myaccount)


#        def transfer(amount, self.friendsaccount, self.myaccount):
#            funds = self.friendsaccount.withdraw(grab)
#            self.myaccount.deposit(funds)


        except InsufficientFunds as e:
            print("----------------------------------------------------------------")
            print("Awww, Tapped out", e.balance, "<", e.requested, "::", (self.__class__.__name__, id(self)))
            self.stop()
            print("----------------------------------------------------------------")
            return
        self.grabbed = self.grabbed + grab


account1 = Account(1000).go()
account2 = Account(1000).go()

fred = MischiefMaker(account1, account2).go()
barney = MischiefMaker(account2, account1).go()


wait_for(fred, barney)

account1.stop()
account2.stop()
account1.join()
account2.join()

print("GAME OVER")

print("Fred grabbed", fred.grabbed)
print("Barney grabbed", barney.grabbed)
print("Total grabbed", fred.grabbed + barney.grabbed)
print("Since they stopped grabbing...")
print("Money left", account1.balance, account2.balance)
print("Ending money", account1.balance + account2.balance)
