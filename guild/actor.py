#!/usr/bin/python
#
#-------------------------------------------------------------------------
#

# Careful with naming to deliberately allow this:
# from actor import *

from collections import deque as _deque
from functools import wraps as _wraps
import logging
import queue
import sys
from threading import Thread as _Thread
import time
import sys
import inspect
from guild.promise import Promise, PromiseAPI

from guild.exceptions import *

__all__ = ["Actor", "ActorMixin", "ActorMetaclass",
           "actor_method", "actor_function", "process_method",
           "late_bind", "UnboundActorMethod", "ActorException",
           "ActorNotStartedException",
           "late_bind_safe", "pipe", "wait_for", "join", "stop", "pipeline",
           "wait_KeyboardInterrupt", "start"]


strace = False  #NOTE: Overview documented
trace_actor_calls = False


def Print(*args):   #NOTE: Overview documented
    sys.stderr.write(" ".join([str(x) for x in args]))
    sys.stderr.write("\n")
    sys.stderr.flush()

def mkactorfunction_wtimeout(func, __fcall_timeout):
    promise = Promise()

    @_wraps(func)
    def t(self, *args, **argd):
        op = (func, self, args, argd)
        if strace:                                          # EXPERIMENTAL
            Print("strace:ACTORFUNCTION args", op)          # EXPERIMENTAL
        if promise.queue:
            self.F_inbound.append((op, promise))
            self._actor_notify()
        else:
            raise JobCancelled(self, op)

        try:
            result_fail, result = promise.queue.get(True, __fcall_timeout) # 5 seconds means pretty non-responsive.
        except AttributeError:
            # Queue was deleted during the above block
            raise JobCancelled(self, op)
        except queue.Empty:
            # The function call timed out. This could be a problem
            # with the actor or it might not have been started. Check
            # which and raise appropriately
            if not self.is_alive():
                raise ActorNotStartedException
            raise
        if result_fail:
            exc_info = result_fail
            tp, value, tb = result_fail
            raise value.with_traceback(tb)


        if strace:                                          # EXPERIMENTAL
            Print("strace:ACTORFUNCTION result", result)    # EXPERIMENTAL
        return result
    return t

def mkactorfunction_promise(func, __fcall_timeout):
    @_wraps(func)
    def t(self, *args, **argd):
        promise = Promise()
        promise.promiser = self
        op = (func, self, args, argd)
        if strace:                                          # EXPERIMENTAL
            Print("strace:ACTORFUNCTION args", op)          # EXPERIMENTAL
        if promise.queue:
            self.F_inbound.append((op, promise))
            self._actor_notify()
        else:  # Job cancelled already!
            raise JobCancelled(self, op)


        return promise

    return t

def mkactormethod(func):
    @_wraps(func)
    def t(self, *args, **argd):
        if strace:                                            # EXPERIMENTAL
            Print("strace:CALL ACTORMETHOD", func, args, argd)# EXPERIMENTAL
        self.inbound.append((func, self, args, argd))
        self._actor_notify()
    return t


def mkprocessmethod(func):
    @_wraps(func)
    def s(self, *args, **argd):
        if strace:                                          # EXPERIMENTAL
            Print("strace:PROCESSMETHOD", func, args, argd) # EXPERIMENTAL
        try:
            x = func(self)
        except Exception as e:
            self.killflag = True
            raise
        if x == False:
            self.killflag = True # Exitting - make sure thread stops
            return
        if self.killflag:
            return
        self.core.append((s, self, (), {}))
    return s

def latebind(func):
    @_wraps(func)
    def s(self, *args, **argd):
        if strace:                                     # EXPERIMENTAL
            Print("strace:LATEBIND", func, args, argd) # EXPERIMENTAL
        raise UnboundActorMethod("Call to Unbound Latebind", func)
    return s

def mklatebindsafe(func):
    @_wraps(func)
    def t(self, *args, **argd):
        if strace:                                              # EXPERIMENTAL
            Print("strace:LATEBINDSAFE", func, self, args, argd)# EXPERIMENTAL
        self.inbound.append((func, self, args, argd))
        self._actor_notify()
    return t


class ActorMetaclass(type):   #NOTE: Overview documented
    def __new__(cls, clsname, bases, dct):
        new_dct = {}
        promise_dct = {}
        inboxes = {}
        outboxes = {}
        for name, val in dct.items():
            new_dct[name] = val
            if val.__class__ == tuple and len(val) == 3:
                tag, fn, arg = str(val[0]), val[1], val[2]
                if tag.startswith("ACTORFUNCTION"):
                    new_dct[name] = mkactorfunction_wtimeout(fn, arg)
                    promise_dct[name] = mkactorfunction_promise(fn, arg)

            if val.__class__ == tuple and len(val) == 2:
                tag, fn = str(val[0]), val[1]
                if tag.startswith("ACTORMETHOD"):
                    inboxes[fn.__name__] = fn.__doc__
                    new_dct[name] = mkactormethod(fn)

                elif tag.startswith("PROCESSMETHOD"):
                    new_dct[name] = mkprocessmethod(fn)

                elif tag == "LATEBIND":
                    outboxes[fn.__name__] = fn.__doc__
                    new_dct[name] = latebind(fn)

                elif tag == "LATEBINDSAFE":
                    outboxes[fn.__name__] = fn.__doc__
                    new_dct[name] = mklatebindsafe(fn)

        new_dct["_promise_dct"] = promise_dct
        new_dct["Inboxes"] = inboxes
        new_dct["Outboxes"] = outboxes
        return type.__new__(cls, clsname, bases, new_dct)


def actor_method_max_queue(length):  #FIXME: Not actually active...   #NOTE: Overview documented
    def decorator(method):
        return ("ACTORMETHOD", length, method)
    return decorator


def actor_method_lossy_queue(length):
    def decorator(method):
        return ("ACTORMETHOD", length, method)
    return decorator

def actor_method(method):
    return ("ACTORMETHOD", method)

def actor_function(timeout=None):
    # Just used as "@actor_function -- ie the common case"
    if callable(timeout):
        return actor_function(None)(timeout)

    def dec(fn):
        return ("ACTORFUNCTION", fn, timeout)

    return dec

def process_method(method):
    return ("PROCESSMETHOD", method)


def late_bind(method):
    return ("LATEBIND", method)


def late_bind_safe(method):
    return ("LATEBINDSAFE", method)


class ActorMixin(metaclass=ActorMetaclass):
    """Actor mixin base class.

    Provides partial implementation of a guild actor. Use with a
    scheduler of some kind to create a complete actor base class.

    """

    def __init__(self, *argv, **argd):
        self.promise = PromiseAPI(self)
        self.inbound = _deque()
        self.F_inbound = _deque()
        self.core = _deque()
        self._actor_logger = logging.getLogger(
            '%s.%s' % (self.__module__, self.__class__.__name__))
        super(ActorMixin, self).__init__(*argv, **argd)

    def interpret(self, command):
        callback, zelf, argv, argd = command
        if zelf:
            if trace_actor_calls:
                Print("ActorCall:", zelf.__class__.__name__ +"."+ callback.__name__, argv, argd)
            try:
                result = callback(zelf, *argv, **argd)
                return result
            except TypeError:
                import sys
                sys.stderr.write("FAILURE -- ")
                sys.stderr.write("command (callback, zelf, argv, argd): ")
                sys.stderr.write(", ".join([repr(x) for x in command]))
                sys.stderr.write("\n")
                sys.stderr.flush()
                raise
        else:
            result = callback(*argv, **argd)
            return result

    def process_start(self):
        pass

    def onStop(self):
        pass

    @process_method
    def process(self):
        return False

    @actor_method
    def bind(self, source, dest, destmeth):
        setattr(self, source, getattr(dest, destmeth))

    def go(self):
        self.start()
        return self

    @late_bind_safe
    def output(self, *argv, **argd):
        pass

    @actor_method
    def input(self, *argv, **argd):
        pass

    def _actor_notify(self):
        """Alert scheduler to queued method invocation.

        If your scheduler is event driven then over-ride this method
        to trigger the scheduler (in a thread safe manner) to run
        _actor_do_queued.

        """
        pass

    def _actor_do_queued(self):
        """Do queued method invocation.

        The scheduler needs to call this method whenever there are
        queued method invocations, or poll it at frequent intervals.

        It returns False if there was nothing to do.

        """
        if not (self.F_inbound or self.inbound or self.core):
            return False

        if self.inbound:
            command = self.inbound.popleft()
            try:
                self.interpret(command)
            except Exception as e:
                self._actor_logger.exception(e)
                self.stop()

        if self.F_inbound:
            command, promise = self.F_inbound.popleft()
            if promise.queue: # May have been cancelled between call and now
                result = None
                result_fail = 0
                try:
                    result = self.interpret(command)
                except Exception:
                    result_fail = sys.exc_info()
            else:
                raise JobCancelled(self, command)

            if promise.queue:
                promise.queue.put_nowait((result_fail, result))
            else:
                raise JobCancelled(self, command)

        if self.core:
            command = self.core.popleft()
            try:
                self.interpret(command)
            except Exception as e:
                self._actor_logger.exception(e)

        return True


class Actor(ActorMixin, _Thread):
    daemon = True

    def __init__(self):
        self.killflag = False
        super(Actor, self).__init__()

    def run(self):
        self.process_start()
        self.process()
        try:
            gen = self.main
        except AttributeError:
            try:
                gen = self.gen_process
            except AttributeError:
                gen = None

        if gen:
            # NB next line looks at the code object, and checks a flag
            if inspect.isgeneratorfunction(gen):
                g = gen()
                self.killflag = False  # Or else an empty process_method can cause shutdown
            else:
                function_name = gen.__self__.__class__.__name__ +"."+gen.__name__
                source_ref = "(%s, line: %d)" % (gen.__func__.__code__.co_filename, gen.__func__.__code__.co_firstlineno)
                warning = "Function %s %s must be a generator" % (function_name, source_ref)
                raise ValueError(warning)
        else:
            g = None

        while not self.killflag:
            # Next loop also checks for the killflag, since it is likely that the killflag gets set within this loop
            while (self.F_inbound or self.inbound or self.core) and (not self.killflag):
                self._actor_do_queued()

            if not self._actor_do_queued():
                if g is None:
                    time.sleep(0.01)
            if g:
                try:
                    next(g)
                except StopIteration:
                    # Generator Exitted
                    self.stop()
                    g = None
        self.onStop()
        if g:
            try:
                g.throw(StopIteration)
            except StopIteration as e:
                pass
            except RuntimeError as e:
                if ( len(e.args)==1) and ( "StopIteration" in e.args[0] ):
                    # Expected error
                    pass
                else:
                    print("Unexpected error", repr(e), dir(e))
                    raise

    def stop(self):
        self.killflag = True


def pipe(source, source_box, sink, sinkbox):
    source.bind(source_box, sink, sinkbox)


def pipeline(*actors):
    x = list(actors)
    while len(x) > 1:
        pipe(x[0], "output", x[1], "input")
        del x[0]


def wait_for(*actors):
    for p in actors:
        p.join()

def join(*actors):
    for p in actors:
        p.join()


def stop(*actors):
    for p in actors:
        p.stop()


def start(*actors):
    for p in actors:
        p.start()


def wait_KeyboardInterrupt():
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
