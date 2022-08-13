#!/usr/bin/python

from guild.actor import ActorException
from guild.stm import Store, ConcurrentUpdate, BusyRetry
import time

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


class MaxRetriesExceeded(ActorException):
    pass


class RetryTimeoutExceeded(ActorException):
    pass


def retry(max_tries=None, timeout=None):
    if callable(max_tries):
        return retry(None)(max_tries)

    def mk_transaction(function):
        def as_transaction(*argv, **argd):
            count = 0
            ts = time.time()
            succeeded = False
            while not succeeded:
                if max_tries is not None:
                    if count > max_tries:
                        raise MaxRetriesExceeded()
                    count += 1
                if timeout is not None:
                    now = time.time()
                    if now-ts > timeout:
                        raise RetryTimeoutExceeded(now-ts , timeout)
                try:
                    result = function(*argv, **argd)
                    succeeded = True
                except ConcurrentUpdate:
                    pass
                except BusyRetry:
                    pass
            return result
        return as_transaction

    return mk_transaction


class Account2(object):
    def __init__(self, balance=10):
        self.account_info = Store()

        curr_balance = self.get_balance_checkout()
        curr_balance.set(balance)
        curr_balance.commit()

    def get_balance_checkout(self):
        success = False
        while not success:
            try:
                curr_balance = self.account_info.checkout("balance")
                success = True
            except BusyRetry:
                pass
        return curr_balance

    @retry                    # Retries until transaction succeeds
    def deposit(self, amount):
        curr_balance = self.get_balance_checkout()
        new_balance = curr_balance.value + amount
        curr_balance.set(new_balance)
        curr_balance.commit()
        return new_balance

#    @retry(max_tries=100)        # Try up to 100 times - maybe should be a timeout?
    @retry(timeout=0.005)        # Timeout after 5 milliseconds (Are we really that worried?)
    def withdraw(self, amount):
        curr_balance = self.get_balance_checkout()
        print( "ATTEMPT WITHDRAW", amount, self, curr_balance )
        if curr_balance.value < amount:
            raise InsufficientFunds("Insufficient Funds in your account",
                                    requested=amount,
                                    balance=curr_balance.value)
        new_balance = curr_balance.value - amount
        curr_balance.set(new_balance)
        curr_balance.commit()
        print( "WITHDRAW SUCCESS", amount, self, curr_balance )
        return amount

    @property
    def balance(self):
        curr_balance = self.get_balance_checkout()
        return curr_balance.value


import random
from guild.actor import *


def transfer(amount, payer, payee):
    funds = payer.withdraw(amount)
    payee.deposit(funds)


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
            print( "TRANSFER", grab, self.friendsaccount, self.myaccount, self.name )
            transfer(grab, self.friendsaccount, self.myaccount)
            print( "TRANSFER SUCCESS", grab, self.friendsaccount, self.myaccount, self.name )
        except InsufficientFunds as e:
            print( "Awww, Tapped out", e.balance, "<", e.requested )
            self.stop()
            return
        except RetryTimeoutExceeded as e:
            print("Timed out withdrawing for whatever reason?", self, e)
            self.stop()
            return
        self.grabbed = self.grabbed + grab


account1 = Account2(1000)
account2 = Account2(1000)

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

