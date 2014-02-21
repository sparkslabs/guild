#!/usr/bin/python

#
# Careful with naming to deliberately allow this:
# from actor import *
#

from threading import Thread as _Thread
import Queue as _Queue
import sys

__all__ = ["Actor", "actor_method", "actor_function", "process_method", "late_bind", "UnboundActorMethod", "late_bind_safe", "pipe", "wait_for", "stop", "pipeline", "wait_KeyboardInterrupt", "start" ]

import time
class UnboundActorMethod(Exception):
    pass

#ACTORFUNCTION

class ActorMetaclass(type):
    def __new__(cls, clsname, bases, dct):
        new_dct = {}
        for name,val in dct.items():
            if hasattr(val,"__call__"):
                new_dct[name] = val
            elif val.__class__ == tuple and len(val) == 2 and str(val[0]).startswith("ACTORMETHOD"):
                  def mkcallback(func):
                      def t(self, *args, **argd):
                          self.inbound.put_nowait( (func, self, args, argd) )
                      return t

                  new_dct[name] = mkcallback(val[1])
            elif val.__class__ == tuple and len(val) == 2 and str(val[0]).startswith("ACTORFUNCTION"):
                  def mkcallback(func):
                      resultQueue = _Queue.Queue()
                      def t(self, *args, **argd):
                          print "OK, in here"
                          self.F_inbound.put_nowait( ( (func, self, args, argd), resultQueue) )
                          print "I put it!!!"
                          result = resultQueue.get(True, None)
                          print "I got result", result
                          return result
                      return t

                  new_dct[name] = mkcallback(val[1])
            elif val.__class__ == tuple and len(val) == 2 and str(val[0]).startswith("PROCESSMETHOD"):
                      def mkcallback(func):
                          def s(self, *args, **argd):
                              x = func(self)
                              #print "HM", x
                              if x == False:
                                return
                              self.core.put_nowait( (s, self, (),{} ) )
                          return s

                      new_dct[name] = mkcallback(val[1])
            elif val.__class__ == tuple and len(val) == 2 and str(val[0]) == ("LATEBIND"):
                          # print "latebind", name, clsname
                          def mkcallback(func):
                              def s(self, *args, **argd):
                                  print "WARNING to unbound late bound actor method"
                                  raise UnboundActorMethod("Call to Unbound Latebind")
                                  self.inbound.put_nowait( (func, self, args, argd) )
                              return s
                          new_dct[name] = mkcallback(val[1])
            elif val.__class__ == tuple and len(val) == 2 and str(val[0]) == ("LATEBINDSAFE"):
                              # print "latebindsafe", name, clsname
                              def mkcallback(func):
                                  def t(self, *args, **argd):
                                      self.inbound.put_nowait( (func, self, args, argd) )
                                  return t

                              new_dct[name] = mkcallback(val[1])
            else:
                              new_dct[name] = val


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
        super(Actor,self).__init__()
        self._uThread = None

    def run(self):
        self._uThread = self.main()

        while True:
            try:
                self._uThread.next()
            except StopIteration:
                break
            if self.killflag:
                self.onStop()
                try:
                    self._uThread.throw(StopIteration)
                except StopIteration:
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
              print "self", self
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
            # print "Huh", self, "G", g
        except:
            # print "HM", self
            g = None
        while True:
            if g != None:
                g.next()
            yield 1
            if self.F_inbound.qsize() > 0 or  self.inbound.qsize() > 0 or  self.core.qsize() > 0:

               if self.inbound.qsize() > 0:
                    command = self.inbound.get_nowait()
                    self.interpret(command)

               if self.F_inbound.qsize() > 0:
                    print "OK, got function"
                    command, result_queue = self.F_inbound.get_nowait()
                    result = self.interpret(command)
                    result_queue.put_nowait(result)

               if self.core.qsize() > 0:
                    #print self.core.qsize()
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
        # print "binding source to dest", source, "Dest", dest, destmeth
        setattr(self, source, getattr(dest, destmeth))

    def go(self):
        self.start()
        return self

    @late_bind
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
