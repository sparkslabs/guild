#!/usr/bin/python
"""mini-guild

A simplified version of guild without the full set of capabilities.
Has actor_methods and late bound methods.

"""

class Actor:
    Behaviour = None # Should be a subclass of Activity
    def __init__(self, *args, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            raise Exception("You do not call Actor directly. Inherit and override Behaviour")
        self.greenthread = None
        self.inputqueue = []
        self._behaviour = (self.Behaviour)(*args, **argd)
        self.active = False
        self.sleeping = False

    def start(self):
        self.greenthread = self.main()
        self.active = True
        return self

    def tick(self):
        try:
            live = next(self.greenthread)
            return live
        except StopIteration:
            return False

    def handle_inqueue(self):
        call = self.inputqueue.pop(0)
        func_name, args = call[0], call[1:]
        #print(func_name, args)
        func = getattr(self._behaviour, func_name)
        func(*args)

    def main(self):
        if not hasattr(self._behaviour, "tick"):
            self._behaviour.tick = lambda *args: None
        while self.active:
            yield 1
            while (self.inputqueue  and self.active):
                self.handle_inqueue()
            if self.active and not self.sleeping:
                self._behaviour.tick()

    def link(self, methodname, target):
        setattr(self._behaviour, methodname, target)

    def isactive(self):
        return self.active

    def issleeping(self):
        return self.sleeping

    def input(self, data):
        self.inputqueue.append(("input", data))

    def stop(self):
        if hasattr(self._behaviour, "stop"):
            self.inputqueue.append(("stop", ))
        self.active = False
        self.sleeping = False


class API:
    """"Not technically needed in this version (remnants of "`Activity` actor"""
    def input(self, data):
        pass
    def output(self, data):
        raise Exception("base class `output` called directly - you should link over this")


class Producer(Actor):
    class Behaviour:
        def __init__(self, message):
            super(Producer.Behaviour, self).__init__()
            self.message = message
            self.greenthread = self.main()  # This could be pushed into API
            self.tick = self.greenthread.__next__

        def main(self):
            while True:
                yield 1
                self.output(self.message)


class Consumer(Actor):
    class Behaviour:
        def __init__(self):
            super(Consumer.Behaviour, self).__init__()
            self.count = 0
        def input(self, data):
            self.count += 1
            print("Consumed:", data, self.count)
            self.sleeping = True


if __name__ == "__main__":

    p = Producer("Hello").start()
    c = Consumer().start()

    p.link("output", c.input)

    x = 0

    # Manual scheduler

    p.tick()
    c.tick()
    while p.isactive() and c.isactive():
        p.tick()
        c.tick()
        x +=1
        if x > 10:
            p.stop()
            c.stop()
