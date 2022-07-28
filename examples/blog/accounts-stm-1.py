#!/usr/bin/python

import random
import time

from guild.actor import *
from guild.stm import Store, ConcurrentUpdate, BusyRetry


class InsufficientFunds(ActorException):
    pass


class Account(object):
    """This is the 'traditional' approach of interacting with the STM module

    It's here as a bare example, but lends itself to other ideas/approaches.

    One of those other approaches is described in Account2
    """
    def __init__(self, balance=10):
        self.account_info = Store()

        curr_balance = self.account_info.checkout("balance")
        curr_balance.set(balance)
        curr_balance.commit()

    def deposit(self, amount):
        deposited = False
        while not deposited:
            try:
                curr_balance = self.account_info.checkout("balance")
                new_balance = curr_balance.value + amount
                curr_balance.set(new_balance)
                curr_balance.commit()
                deposited = True
            except ConcurrentUpdate:
                pass
            except BusyRetry:
                pass
        return new_balance

    def withdraw(self, amount):
        withdrawn = False
        while not withdrawn:
            try:
                curr_balance = self.account_info.checkout("balance")
                if curr_balance.value < amount:
                    raise InsufficientFunds(
                                    "Insufficient Funds in your account",
                                    requested=amount,
                                    balance=curr_balance.value)
                new_balance = curr_balance.value - amount
                curr_balance.set(new_balance)
                curr_balance.commit()
                withdrawn = True
            except ConcurrentUpdate:
                pass
            except BusyRetry:
                pass

        return amount

    @property
    def balance(self):
        curr_balance = self.account_info.checkout("balance")
        return curr_balance.value


# Transfer is the same function from the non-STM code
def transfer(amount, payer, payee):
    funds = payer.withdraw(amount)
    payee.deposit(funds)


# Transfer is the same class from the non-STM code
class MischiefMaker(Actor):
    def __init__(self, myaccount, friendsaccount, name):
        super(MischiefMaker, self).__init__()
        self.myaccount = myaccount
        self.friendsaccount = friendsaccount
        self.grabbed = 0
        self.name = name

    @process_method
    def process(self):
        try:
            grab = random.randint(1, 10) * 10
            transfer(grab, self.friendsaccount, self.myaccount)
        except InsufficientFunds as e:
            print( "Awww, Tapped out", e.balance, "<", e.requested)
            self.stop()
            return
        self.grabbed = self.grabbed + grab


# These two are now just plain objects rather than actors, so they
# don't need to be started - or stopped. Otherwise this code is
# un-modified
account1 = Account(1000)
account2 = Account(1000)

barney = MischiefMaker(account2, account1, "barney").go()
fred = MischiefMaker(account1, account2, "fred").go()

wait_for(fred, barney)


print( "GAME OVER")

print( "Fred grabbed", fred.grabbed)
print( "Barney grabbed", barney.grabbed)
print( "Total grabbed", fred.grabbed + barney.grabbed)
print( "Since they stopped grabbing...")
print( "Money left", account1.balance, account2.balance)
print( "Ending money", account1.balance + account2.balance)
