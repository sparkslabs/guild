#!/usr/bin/python

#
# Careful with naming to deliberately allow this:
# from actor import *
#

from collections import deque as _deque
from functools import wraps as _wraps
import logging
import six
from six.moves import queue as _Queue
import sys
from threading import Thread as _Thread
import time
import sys
import inspect

__all__ = ["Actor", "ActorMixin", "ActorMetaclass",
           "actor_method", "actor_function", "process_method",
           "late_bind", "UnboundActorMethod", "ActorException",
           "ActorNotStartedException",
           "late_bind_safe", "pipe", "wait_for", "stop", "pipeline",
           "wait_KeyboardInterrupt", "start"]


strace = False  #NOTE: Overview documented
trace_actor_calls = False

class UnboundActorMethod(Exception): #NOTE: Overview documented
    pass

class ActorNotStartedException(Exception): #NOTE: Overview documented
    pass


class ActorException(Exception):   #NOTE: Overview documented
    def __init__(self, *argv, **argd):
        super(ActorException, self).__init__(*argv)
        self.__dict__.update(argd)

def Print(*args):   #NOTE: Overview documented
    sys.stderr.write(" ".join([str(x) for x in args]))
    sys.stderr.write("\n")
    sys.stderr.flush()


class ActorMetaclass(type):   #NOTE: Overview documented
    def __new__(cls, clsname, bases, dct):
        new_dct = {}
        inboxes = {}
        outboxes = {}
        for name, val in dct.items():
            new_dct[name] = val
            if val.__class__ == tuple and len(val) == 3:
                tag, fn, arg = str(val[0]), val[1], val[2]
                if tag.startswith("ACTORFUNCTION"):
                    def mkcallback(func, __fcall_timeout=arg):
                        resultQueue = _Queue.Queue()
                        @_wraps(func)
                        def t(self, *args, **argd):
                            op = (func, self, args, argd)
                            if strace:                                          # EXPERIMENTAL
                                Print("strace:ACTORFUNCTION args", op)          # EXPERIMENTAL
                            self.F_inbound.append((op, resultQueue))
                            self._actor_notify()
                            #e, result = resultQueue.get(True, None)
                            try:
                                e, result = resultQueue.get(True, __fcall_timeout) # 5 seconds means pretty non-responsive.
                            except _Queue.Empty:
                                # The function call timed out. This could be a problem
                                # with the actor or it might not have been started. Check
                                # which and raise appropriately
                                if not self.is_alive():
                                    raise ActorNotStartedException
                                raise
                            if e:
                                six.reraise(*e)
                            if strace:                                          # EXPERIMENTAL
                                Print("strace:ACTORFUNCTION result", result)    # EXPERIMENTAL
                            return result
                        return t

                    new_dct[name] = mkcallback(fn,arg)

            if val.__class__ == tuple and len(val) == 2:
                tag, fn = str(val[0]), val[1]
                if tag.startswith("ACTORMETHOD"):
                    inboxes[fn.__name__] = fn.__doc__
                    def mkcallback(func):
                        @_wraps(func)
                        def t(self, *args, **argd):
                            if strace:                                            # EXPERIMENTAL
                                Print("strace:CALL ACTORMETHOD", func, args, argd)# EXPERIMENTAL
                            self.inbound.append((func, self, args, argd))
                            self._actor_notify()
                        return t
                    new_dct[name] = mkcallback(fn)

                elif tag.startswith("ACTORFUNCTION"):
                    def mkcallback(func):
                        resultQueue = _Queue.Queue()

                        @_wraps(func)
                        def t(self, __fcall_timeout=5, *args, **argd):
                            op = (func, self, args, argd)
                            if strace:                                          # EXPERIMENTAL
                                Print("strace:ACTORFUNCTION args", op)          # EXPERIMENTAL
                            self.F_inbound.append((op, resultQueue))
                            self._actor_notify()
                            #e, result = resultQueue.get(True, None)
                            try:
                                e, result = resultQueue.get(True, __fcall_timeout) # 5 seconds means pretty non-responsive.
                            except _Queue.Empty:
                                # The function call timed out. This could be a problem
                                # with the actor or it might not have been started. Check
                                # which and raise appropriately
                                if not self.is_alive():
                                    raise ActorNotStartedException
                                raise
                            if e:
                                six.reraise(*e)
                            if strace:                                          # EXPERIMENTAL
                                Print("strace:ACTORFUNCTION result", result)    # EXPERIMENTAL
                            return result
                        return t

                    new_dct[name] = mkcallback(fn)

                elif tag.startswith("PROCESSMETHOD"):
                    def mkcallback(func):
                        @_wraps(func)
                        def s(self, *args, **argd):
                            if strace:                                          # EXPERIMENTAL
                                Print("strace:PROCESSMETHOD", func, args, argd) # EXPERIMENTAL
                            x = func(self)
                            if x == False:
                                return
                            self.core.append((s, self, (), {}))
                        return s

                    new_dct[name] = mkcallback(fn)

                elif tag == "LATEBIND":
                    outboxes[fn.__name__] = fn.__doc__
                    def mkcallback(func):
                        @_wraps(func)
                        def s(self, *args, **argd):
                            if strace:                                     # EXPERIMENTAL
                                Print("strace:LATEBIND", func, args, argd) # EXPERIMENTAL
                            raise UnboundActorMethod("Call to Unbound Latebind", func)
                        return s
                    new_dct[name] = mkcallback(fn)

                elif tag == "LATEBINDSAFE":
                    outboxes[fn.__name__] = fn.__doc__
                    def mkcallback(func):
                        @_wraps(func)
                        def t(self, *args, **argd):
                            if strace:                                              # EXPERIMENTAL
                                Print("strace:LATEBINDSAFE", func, self, args, argd)# EXPERIMENTAL
                            self.inbound.append((func, self, args, argd))
                            self._actor_notify()
                        return t

                    new_dct[name] = mkcallback(fn)

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

#def actor_function(fn):
    #return ("ACTORFUNCTION", fn)

def process_method(method):
    return ("PROCESSMETHOD", method)


def late_bind(method):
    return ("LATEBIND", method)


def late_bind_safe(method):
    return ("LATEBINDSAFE", method)


@six.add_metaclass(ActorMetaclass)
class ActorMixin(object):
    """Actor mixin base class.

    Provides partial implementation of a guild actor. Use with a
    scheduler of some kind to create a complete actor base class.

    """

    def __init__(self, *argv, **argd):
        self.inbound = _deque()
        self.F_inbound = _deque()
        self.core = _deque()
        self._actor_logger = logging.getLogger(
            '%s.%s' % (self.__module__, self.__class__.__name__))
        super(ActorMixin, self).__init__(*argv, **argd)

    def interpret(self, command):
        # print command
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
                # print "self", self
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
            command, result_queue = self.F_inbound.popleft()
            result = None
            result_fail = 0
            try:
                result = self.interpret(command)
            except Exception:
                result_fail = sys.exc_info()

            result_queue.put_nowait((result_fail, result))

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
            else:
                function_name = gen.__self__.__class__.__name__ +"."+gen.__name__
                source_ref = "(%s, line: %d)" % (gen.__func__.__code__.co_filename, gen.__func__.__code__.co_firstlineno)
                warning = "Function %s %s must be a generator" % (function_name, source_ref)
                raise ValueError(warning)
        else:
            g = None

        while not self.killflag:

            while (self.F_inbound or self.inbound or self.core):
                self._actor_do_queued()

            if not self._actor_do_queued():
                if g is None:
                    time.sleep(0.01)
            if g:
                try:
                    next(g)
                except StopIteration:
                    # Print("Generator Exited")
                    self.stop()
                    g = None
        self.onStop()
        if g:
            try:
                g.throw(StopIteration)
            except StopIteration:
                pass

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
