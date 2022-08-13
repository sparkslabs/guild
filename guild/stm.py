#!/usr/bin/python
#
# Copyright 2010 British Broadcasting Corporation and Kamaelia Contributors(1)
#
# (1) Kamaelia Contributors are listed in the AUTHORS file and at
#     http://www.kamaelia.org/AUTHORS - please extend this file,
#     not this notice.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# -------------------------------------------------------------------------

from __future__ import print_function

from functools import wraps as _wraps
from contextlib import contextmanager

import copy
import threading

from guild.actor import Actor, ActorException
import time

class MaxRetriesExceeded(ActorException):
    pass


class RetryTimeoutExceeded(ActorException):
    pass


"""
===
STM
===

Support for basic in-process software transactional memory.



What IS it?
-----------

Software Transactional Memory (STM) is a technique for allowing multiple
threads to share data in such a way that they know when something has gone
wrong. It's been used in databases (just called transactions there really) for
some time and is also very similar to version control. Indeed, you can think of
STM as being like variable level version control.



Why is it useful?
-----------------

Why do you need it? Well, in normal code, Global variables are generally
shunned because it can make your code a pain to work with and a pain to be
certain if it works properly. Even with linear code, you can have 2 bits of
code manipulating a structure in surprising ways - but the results are
repeatable. Not-properly-managed-shared-data is to threaded systems as
not-properly-managed-globals are to normal code. (This code is one way of
helping manage shared data)

Well, with code where you have multiple threads active, having shared data is
like an even nastier version of globals. Why? Well, when you have 2 (or more)
running in parallel, the results of breakage can become hard to repeat as two
pieces of code "race" to update values.

With STM you make it explicit what the values are you want to update, and only
once you're happy with the updates do you publish them back to the shared
storage. The neat thing is, if someone else changed things since you last
looked, you get told (your commit fails), and you have to redo the work. This
may sound like extra work (you have to be prepared to redo the work), but it's
nicer than your code breaking :-)

The way you get that message is the .commit raises a ConcurrentUpdate
exception.

Also, it's designed to work happily in code that requires non-blocking usage -
which means you may also get a BusyRetry exception under load. If you do, you
should as the exception suggests retry the action that you just tried. (With or
without restarting the transaction)

Apologies if that sounds too noddy :)



Using It
--------

Accessing/Updating a single shared value in the store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can have many single vars in a store of course... If they're related though
or updated as a group, see the next section::

    from Axon.STM import Store

    S = Store()
    greeting = S.usevar("hello")
    print(repr(greeting.value))
    greeting.set("Hello World")
    greeting.commit()



Accessing/Updating a collection of shared values in the store
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Likewise you can use as many collections of values from the store as you like::

    from Axon.STM import Store

    S = Store()
    D = S.using("account_one", "account_two", "myaccount")
    D["account_one"].set(50)
    D["account_two"].set(100)
    D.commit()
    S.dump()

    D = S.using("account_one", "account_two", "myaccount")
    D["myaccount"].set(D["account_one"].value+D["account_two"].value)
    D["account_one"].set(0)
    D["account_two"].set(0)
    D.commit()
    S.dump()



What can (possibly) go wrong?
-----------------------------

You can have 2 people trying to update the same values at once. An example of
this would be - suppose you have the following commands being executed by 2
threads with this mix of commands::

    S = Store()
    D = S.using("account_one", "account_two", "myaccount")
    D["myaccount"].set(0)
    D["account_one"].set(50)
    D["account_two"].set(100)
    D.commit() # 1
    S.dump()

    D = S.using("account_one", "account_two", "myaccount")
    D["myaccount"].set(D["account_one"].value+D["account_two"].value)
    E = S.using("account_one", "myaccount")
    E["myaccount"].set(E["myaccount"].value-100)
    E["account_one"].set(100)
    E.commit() # 2
    D["account_one"].set(0)
    D["account_two"].set(0)
    D.commit() # 3 - should fail
    S.dump()

You do actually want this to fail because you have concurrent updates. This
will fail on the third commit, and fail by throwing a ConcurrentUpdate
exception. If you get this, you should redo the transaction.

The other is where there's lots of updates happening at once. Rather than the
code waiting until it acquires a lock, it is possible for either the .using,
.usevar or .commit methods to fail with a BusyRetry exception. This means
exactly what it says on the tin - the system was busy & you need to retry. In
this case you do not have to redo the transaction. This is hard to replicate
except under load. The reason we do this however is because most Kamaelia
components are implemented as generators, which makes blocking operation ( as a
.acquire() rather than .acquire(0) would be) an expensive operation.
"""

import time


class ConcurrentUpdate(Exception):
    pass


class BusyRetry(Exception):
    pass


class FAIL(Exception):
    pass


class MAXFAIL(Exception):
    pass


class Value(object):
    """
    Value(version, value, store, key) -> new Value object

    A simple versioned key-value pair which belongs to a thread-safe store

    Arguments:

    - version -- the initial version of the value
    - value -- the object's initial value
    - store -- a Store object to hold the value and it's history
    - key -- a key to refer to the value

    Note: You do not instantiate these - the Store does that
    """
    def __init__(self, version, value, store, key):
        """
        x.__init__(...) initializes x; see x.__class__.__doc__ for signature
        """

        self.version = version
        self.value = value
        self.store = store
        self.key = key

    def __repr__(self):
        return "Value" + repr((self.version, self.value))

    def set(self, value):
        """ Set the value without storing """
        self.value = value

    def commit(self):
        """ Commit a new version of the value to the store """
        newvalue = self.store.set(self.key, self)
        return newvalue

    def copy_value(self, value):
        return copy.deepcopy(value)

    def clone(self):
        """ Returns a clone of the value """
        if isinstance(self.value, Actor):
            return (self.__class__)(self.version, self.value, self.store, self.key)
        # otherwise...
        return (self.__class__)(self.version,
                     self.copy_value(self.value),
                     self.store,
                     self.key)


class Collection(dict):
    """
    Collection() -> new Collection dict

    A dictionary which belongs to a thread-safe store

    Again, you do not instantiate these yourself
    """
    def make_snapshot(self):
        self.isSnapshot = True
    def set_store(self, store):
        """ Set the store to associate the collection with """
        self.store = store

    def commit(self):
        """ Commit new versions of the collection's items to the store """
        self.store.set_values(self)

    def __getattribute__(self, key):
        keys = super(Collection, self).keys()
        if key in keys:
            value = self[key].value
            return value
        return super(Collection, self).__getattribute__(key)

    def __setattr__(self, key, value):
        keys = super(Collection, self).keys()
        if key in keys:
            self[key].set(value)
        else:
            super(Collection, self).__setattr__(key, value)

    def pull_updates(self):
        if self.isSnapshot:
            new_snapshot = self.store.snapshot()
            curr_keys = self.keys()
            new_keys = new_snapshot.keys()

            updates = set()
            for key in new_keys:
                if key not in curr_keys:
                    self[key] = self.store.usevar(key)
                    updates.add(self[key])

                if new_snapshot[key].version > self[key].version:
                    self[key] = new_snapshot[key]
                    updates.add(self[key])

            return updates
        else:
            return []
        return []

class Store(object):
    """
    Store() -> new Store object

    A thread-safe versioning store for key-value pairs

    You instantiate this as per the documentation for this module
    """
    def __init__(self, valuetype=Value):
        self.store = {}                # Threadsafe
        self.lock = threading.Lock()

        self.last_update = time.time() # Readonly
        self.valuetype = valuetype

    # ////---------------------- Direct access -----------------------\\\\
    # Let's make this lock free, and force the assumption that to do
    # this the store must be locked.
    #
    # Let's make this clear by marking these private
    #
    # Reads Store Value - need to protect during clone
    def __get(self, key):
        """
        Retreive a value.  Returns a clone of the Value.  Not thread-safe.
        """
        return self.store[key].clone()

    # Writes Store Value - need to prevent multiple concurrent write
    def __make(self, key):
        """ Create a new key-value pair.  Not thread-safe """
        self.store[key] = (self.valuetype)(0, None, self, key)

    # Writes Store Value  - need to prevent multiple concurrent write
    def __do_update(self, key, value):
        """
        Update a key-value pair and increment the version.  Not thread-safe
        """
        newvalue = value.clone()
        newvalue.version = newvalue.version + 1
        self.store[key] = newvalue
        return newvalue

    # Reads Store Value - possibly thread safe, depending on VM implementation
    def __can_update(self, key, value):
        """
        Returns true if a value can be safely updated.  Potentially not
        thread-safe
        """
        return not (self.store[key].version > value.version)
    # \\\\---------------------- Direct access -----------------------////

    # ////----------------- Single Value Mediation ------------------\\\\
    # Both of these are read-write
    # Reads and Writes Values (since value may not exist)
    def usevar(self, key, islocked=False):
        """
        Tries to get an item from the store.  Returns the requested
        Value object.  If the store is already in use a BusyRetry
        error is raised.
        """
        locked = islocked
        if not locked:
            locked = self.lock.acquire(blocking=False)
        result = None
        if locked:
            try:
                try:
                    result = self.__get(key)
                except KeyError:
                    self.__make(key)
                    result = self.__get(key)
            finally:
                if not islocked:
                    self.lock.release()    # only release if we acquire
        else:
            raise BusyRetry
        return result

    # Reads and Writes Values (has to check store contents)
    def set(self, key, value):
        """
        Tries to update a value in the store.  If the store is already
        in use a BusyRetry error is raised.  If the value has been
        updated by another thread a ConcurrentUpdate error is raised
        """
        locked = self.lock.acquire(0)
        HasBeenSet = False
        if locked:
            try:
                if self.__can_update(key, value):
                    newvalue = self.__do_update(key, value)
                    HasBeenSet = True
            finally:
                self.lock.release()
        else:
            raise BusyRetry
        if not HasBeenSet:
            raise ConcurrentUpdate

        self.last_update = time.time()
        return newvalue

    # \\\\----------------- Single Value Mediation ------------------////

    # ////----------------- Multi-Value Mediation ------------------\\\\
    # Both of these are read-write
    # Reads and Writes Values (since values may not exist)
    def using(self, *keys):
        """
        Tries to get a selection of items from the store. Returns a
        Collection dictionary containing the requested values.  If the
        store is already in use a BusyRetry error is raised.
        """
        locked = self.lock.acquire(0)
        if locked:
            try:

                D = Collection()
                for key in keys:
                    D[key] = self.usevar(key, islocked=True)
                D.set_store(self)

            finally:
                self.lock.release()
        else:
            raise BusyRetry

        return D

    # Reads and Writes Values (has to check store contents)
    def set_values(self, D):
        """
        Tries to update a selection of values in the store.  If the store is
        already in use a BusyRetry error is raised.  If one of the values has
        been updated by another thread a ConcurrentUpdate error is raised.
        """
        CanUpdateAll = True  # Hope for the best :-)

        locked = self.lock.acquire(0)
        if locked:
            try:
                for key in D:
                    # Let experience teach us otherwise :-)
                    CanUpdateAll = CanUpdateAll and self.__can_update(key, D[key])  # Reading Store

                if CanUpdateAll:
                    for key in D:
                        self.__do_update(key, D[key])  # Writing Store
            finally:
                self.lock.release()
        else:
            raise BusyRetry

        if not CanUpdateAll:
            raise ConcurrentUpdate

    # \\\\----------------- Multi-Value Mediation ------------------////

    def names(self):
        keys = self.store.keys()
        return keys

    def snapshot(self):
        D = self.using(*self.names())
        D.make_snapshot()
        return D

    def export(self, names = None):
        result = {}
        if names == None:
            names = self.names()
        locked = self.lock.acquire(0)
        for name in names:
            value_clone = self.store[name].clone()
            value = value_clone.value
            result[name] = value
        self.lock.release()

        return result

    def dump(self):
        # Who cares really? This is a debug :-)
        print("DEBUG: Store dump ------------------------------")
        for k in self.store:
            print("     ", k, ":", self.store[k])
        print ()

#    def usevar(self, key, islocked=False):
    def checkout(self, key=None, islocked=False):
        if key is not None:
            return self.usevar(key, islocked)
        return STMCheckout(self)


class Bunch(object):
    def __init__(self, keys):
        i = 0
        for key in keys:
            self.__dict__[key] = i
            i += 1


class STMCheckout(object):
    def __init__(self, store, max_tries=10):
        self.notcheckedin = True
        self.num_tries = 0
        self.max_tries = max_tries
        self.store = store

    @contextmanager
    def changeset(self, *args, **argd):
        autocheckin = argd.get("autocheckin", True)
        # print("WOMBAT", args, self.store)
        D = self.store.using(*args)
        self.num_tries += 1
        try:
            yield D
            if autocheckin:
                D.commit()
            self.notcheckedin = False
        except ConcurrentUpdate as f:
            if self.max_tries:
                if self.max_tries == self.num_tries:
                    raise MAXFAIL(f)

def retry(max_tries=None, timeout=None):
    if callable(max_tries):
        return retry(None)(max_tries)

    def mk_transaction(function):
        @_wraps(function)
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


if __name__ == "__main__":
    if 0:
        S = Store()
        D = S.using("account_one", "account_two", "myaccount")
        D["myaccount"].set(0)
        D["account_one"].set(50)
        D["account_two"].set(100)
        D.commit()  # 1
        S.dump()

        D = S.using("account_one", "account_two", "myaccount")
        D["myaccount"].set(D["account_one"].value + D["account_two"].value)
        E = S.using("account_one", "myaccount")
        E["myaccount"].set(E["myaccount"].value - 100)
        E["account_one"].set(100)
        E.commit()  # 2
        D["account_one"].set(0)
        D["account_two"].set(0)
        D.commit()  # 3 - should fail
        S.dump()

    if 0:
        S = Store()
        D = S.using("account_one", "account_two", "myaccount")
        D["account_one"].set(50)
        D["account_two"].set(100)
        D.commit()
        S.dump()

        D = S.using("account_one", "account_two", "myaccount")
        D["myaccount"].set(D["account_one"].value + D["account_two"].value)
        D["account_one"].set(0)
        D["account_two"].set(0)
        D.commit()
        S.dump()

    if 0:
        S = Store()
        D = S.usevar("accounts")
        D.set({"account_one": 50, "account_two": 100, "myaccount": 0})
        D.commit()  # First
        S.dump()
        X = D.value
        X["myaccount"] = X["account_one"] + X["account_two"]
        X["account_one"] = 0

        E = S.usevar("accounts")
        Y = E.value
        Y["myaccount"] = Y["myaccount"] - 100
        Y["account_one"] = 100
        E.set(Y)
        E.commit()  # Second
        S.dump()

        X["account_two"] = 0
        D.set(X)
        D.commit()  # Third - This Should fail
        S.dump()
        print ("Committed", D.value["myaccount"])

    if 1:
        S = Store()
        greeting = S.usevar("hello")
        print (repr(greeting.value))
        greeting.set("Hello World")
        greeting.commit()
        # ------------------------------------------------------
        print (greeting)
        S.dump()
        # ------------------------------------------------------
        par = S.usevar("hello")
        par.set("Woo")
        par.commit()
        # ------------------------------------------------------
        print (greeting)
        S.dump()
        # ------------------------------------------------------
        greeting.set("Woo")
        greeting.commit()  # Should fail
        print (repr(greeting), repr(greeting.value))
        S.dump()
