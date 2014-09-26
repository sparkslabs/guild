#!/usr/bin/python

#
# Careful with naming to deliberately allow this:
# from actor import *
#

from functools import wraps as _wraps
import Queue as _Queue
import sys
from threading import Thread as _Thread
import time

__all__ = ["Actor", "actor_method", "actor_function", "process_method",
           "late_bind", "UnboundActorMethod", "ActorException",
           "late_bind_safe", "pipe", "wait_for", "stop", "pipeline",
           "wait_KeyboardInterrupt", "start"]


class UnboundActorMethod(Exception):
    pass


class ActorException(Exception):
    def __init__(self, *argv, **argd):
        super(ActorException, self).__init__(*argv)
        self.__dict__.update(argd)


class ActorMetaclass(type):
    def __new__(cls, clsname, bases, dct):
        new_dct = {}
        new_dct['actor_methods'] = []
        new_dct['actor_functions'] = []
        new_dct['process_methods'] = []
        new_dct['late_binds'] = []
        new_dct['late_bind_safes'] = []
        for name, val in dct.items():
            new_dct[name] = val
            if val.__class__ == tuple and len(val) == 2:
                tag, fn = str(val[0]), val[1]
                if tag.startswith("ACTORMETHOD"):
                    def mkcallback(func):
                        @_wraps(func)
                        def t(self, *args, **argd):
                            self.inbound.put_nowait((func, self, args, argd))
                        return t

                    new_dct[name] = mkcallback(fn)
                    new_dct['actor_methods'].append(name)

                elif tag.startswith("ACTORFUNCTION"):
                    def mkcallback(func):
                        resultQueue = _Queue.Queue()

                        @_wraps(func)
                        def t(self, *args, **argd):
                            op = (func, self, args, argd)
                            self.F_inbound.put_nowait((op, resultQueue))
                            e, result = resultQueue.get(True, None)
                            if e != 0:
                                raise e.__class__, e, e.sys_exc_info
                            return result
                        return t

                    new_dct[name] = mkcallback(fn)
                    new_dct['actor_functions'].append(name)

                elif tag.startswith("PROCESSMETHOD"):
                    def mkcallback(func):
                        @_wraps(func)
                        def s(self, *args, **argd):
                            x = func(self)
                            if x == False:
                                return
                            self.core.put_nowait((s, self, (), {}))
                        return s

                    new_dct[name] = mkcallback(fn)
                    new_dct['process_methods'].append(name)

                elif tag == "LATEBIND":
                    def mkcallback(func):
                        @_wraps(func)
                        def s(self, *args, **argd):
                            raise UnboundActorMethod("Call to Unbound Latebind")
                        return s
                    new_dct[name] = mkcallback(fn)
                    new_dct['late_binds'].append(name)

                elif tag == "LATEBINDSAFE":
                    # print "latebindsafe", name, clsname
                    def mkcallback(func):
                        @_wraps(func)
                        def t(self, *args, **argd):
                            self.inbound.put_nowait((func, self, args, argd))
                        return t

                    new_dct[name] = mkcallback(fn)
                    new_dct['late_bind_safes'].append(name)

        return type.__new__(cls, clsname, bases, new_dct)


def actor_method_max_queue(length):
    def decorator(method):
        return ("ACTORMETHOD", length, method)
    return decorator


def actor_method_lossy_queue(length):
    def decorator(method):
        return ("ACTORMETHOD", length, method)
    return decorator


def actor_method(method):
    return ("ACTORMETHOD", method)


def actor_function(fn):
    return ("ACTORFUNCTION", fn)


def process_method(method):
    return ("PROCESSMETHOD", method)


def late_bind(method):
    return ("LATEBIND", method)


def late_bind_safe(method):
    return ("LATEBINDSAFE", method)


class Actor(_Thread):
    __metaclass__ = ActorMetaclass
    daemon = True

    def __init__(self):
        self.inbound = _Queue.Queue()
        self.F_inbound = _Queue.Queue()
        self.core = _Queue.Queue()
        self.killflag = False
        super(Actor, self).__init__()
        self._uThread = None
        self._g = None

    def run(self):
        self._uThread = self.main()

        while True:
            try:
                self._uThread.next()
            except StopIteration:
                break
            if self.killflag:
                self.onStop()
                dobreak = False
                try:
                    self._uThread.throw(StopIteration)
                except StopIteration:
                    dobreak = True
                try:
                    if self._g:
                        self._g.throw(StopIteration)
                except StopIteration:
                    dobreak = True
                if dobreak:
                    break

    def interpret(self, command):
        # print command
        callback, zelf, argv, argd = command
        if zelf:
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

    def main(self):
        self.process_start()
        self.process()
        try:
            g = self.gen_process()
        except:
            g = None
        self._g = g
        while True:
            if g != None:
                g.next()
            yield 1
            if (self.F_inbound.qsize() > 0 or
                self.inbound.qsize() > 0 or
                self.core.qsize() > 0):

                if self.inbound.qsize() > 0:
                    command = self.inbound.get_nowait()
                    try:
                        self.interpret(command)
                    except:
                        self.stop()

                if self.F_inbound.qsize() > 0:
                    command, result_queue = self.F_inbound.get_nowait()
                    result_fail = 0
                    try:
                        result = self.interpret(command)
                    except Exception as e:
                        result_fail = e
                        result_fail.sys_exc_info = sys.exc_info()[2]

                    result_queue.put_nowait((result_fail, result))

                if self.core.qsize() > 0:
                    command = self.core.get_nowait()
                    self.interpret(command)
            else:
                if g == None:
                    time.sleep(0.01)

    @process_method
    def process(self):
        return False

    def stop(self):
        self.killflag = True

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


def pipe(source, source_box, sink, sinkbox):
    source.bind(source_box, sink, sinkbox)


def pipeline(*processes):
    x = list(processes)
    while len(x) > 1:
        pipe(x[0], "output", x[1], "input")
        del x[0]


def wait_for(*processes):
    for p in processes:
        p.join()


def stop(*processes):
    for p in processes:
        p.stop()


def start(*processes):
    for p in processes:
        p.start()


def wait_KeyboardInterrupt():
    while True:
        try:
            time.sleep(0.1)
        except KeyboardInterrupt:
            break
