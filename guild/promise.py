#!/usr/bin/python
import sys
import queue
import time

from guild.exceptions import *

# 5 seconds means pretty non-responsive.
DEFAULT_TIMEOUT = 5

class Promise:
    def __init__(self, timeout=DEFAULT_TIMEOUT):
        self.promiser=None
        self.queue = queue.Queue()
        self.timeout = timeout

    def ready(self):
        if self.queue:
            return not self.queue.empty()
        else:
            return False # Could raise an exception instead?

    def unwrap(self):
        "Blocks on this particular queue"
        try:
            result_fail, result = self.queue.get(True, self.timeout)
        except queue.Empty:
            # The function call timed out. This could be a problem
            # with the actor or it might not have been started. Check
            # which and raise appropriately
            if not self.promiser.is_alive():
                raise ActorNotStartedException
            raise
        if result_fail:
            exc_info = result_fail
            tp, value, tb = result_fail
            raise value.with_traceback(tb)
        return result

    def cancel(self):
        self.queue = None # Throw away the queue - which cancels the request


def wait_all(*promises):
    while not all([x.ready() for x in promises]):
        time.sleep(0.001)

def wait_any(*promises):
    while not any([x.ready() for x in promises]):
        time.sleep(0.001)

def cancel(*promises):
    for promise in promises:
        promise.cancel()


class PromiseAPI:
    def __init__(self, promiser=None):
        self.promiser = promiser
    def __getattribute__(self, attr):
        try:
            r = super(PromiseAPI, self).__getattribute__(attr)
            return r
        except AttributeError:
            pass
        def r(*args, **argv):
            func_dct = self.promiser.__getattribute__("_promise_dct")
            func = func_dct[attr]

            return func(self.promiser, *args, **argv)
        return r
    def set_promiser(self, promiser):
        self.promiser = promiser
        promiser.promiser = promiser


if __name__ == "__main__":

    class Promiser:
        def __init__(self):
            self.promise = PromiseAPI(self)

    p = PromiseAPI("fish")
    p.promiser
    p.promised
    p.promised(1,2,name="hello")


    pygamedisplay = Promiser()
    pygamedisplay.promise.get_surface((400,300), (100,100))




