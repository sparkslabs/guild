#!/usr/bin/python

from guild.actor import *
import random

class InsufficientFunds(ActorException):
    pass

class Account(Actor):
    def __init__(self, balance=10):
        super(Account, self).__init__()
        self.balance = balance

    @actor_function
    def deposit(self, amount):
        # I've made this a function to allow the value to be confirmed deposited
        print "DEPOSIT", "\t", amount, "\t", self.balance
        self.balance = self.balance + amount
        return self.balance 

    @actor_function
    def withdraw(self, amount):
        if self.balance < amount:
            raise InsufficientFunds("Insufficient Funds in your account", requested=amount, balance=self.balance)
        self.balance = self.balance - amount
        print "WITHDRAW", "\t", amount, "\t", self.balance
        return amount

class MoneyDrain(Actor):
    def __init__(self, sharedaccount):
        super(MoneyDrain, self).__init__()
        self.sharedaccount = sharedaccount
        self.grabbed = 0

    @process_method
    def process(self):
        try:
            grabbed = self.sharedaccount.withdraw(random.choice([10,20,40,80,160]))
        except InsufficientFunds as e:
            print "Awww, Tapped out", e.balance, "<", e.requested
            self.stop()
            return
        self.grabbed = self.grabbed + grabbed

class MoneySource(Actor):
    def __init__(self, sharedaccount):
        super(MoneySource, self).__init__()
        self.sharedaccount = sharedaccount

    @process_method
    def process(self):
        self.sharedaccount.deposit(random.randint(1,100))

account = Account(1000).go()

if False:
    print "Frank\tWilma\tBetty"
    frank, wilma, betty = 0,0,0
    try:
        while True:
            account.deposit(100)
            frank += account.withdraw(random.choice([10,20,40,80,160]))
            betty += account.withdraw(random.choice([10,20,40,80,160]))
            wilma += account.withdraw(random.choice([10,20,40,80,160]))
            print frank, "\t", wilma, "\t", betty
    except InsufficientFunds as e:
        print e.message
        print "Balance", e.balance
        print "Requested", e.requested
        print account.balance


    print "GAME OVER"

    print "Frank grabbed", frank
    print "Wilma grabbed", wilma
    print "Betty grabbed", betty

    account.stop()
    account.join()

else:

    frank = MoneyDrain(account).go()
    wilma = MoneyDrain(account).go()
    betty = MoneyDrain(account).go()
    barny = MoneySource(account).go()

    wait_for(frank, wilma, betty)
    barny.stop()
    barny.join()

    account.stop()
    account.join()
    
    print "GAME OVER"

    print "Frank grabbed", frank.grabbed
    print "Wilma grabbed", wilma.grabbed
    print "Betty grabbed", betty.grabbed
    print "Total grabbed", frank.grabbed + wilma.grabbed + betty.grabbed
    print "Since they stopped grabbing..."
    print "Money left", account.balance



