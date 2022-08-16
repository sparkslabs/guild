#!/usr/bin/python
"""mini-guild

A simplified version of guild without the full set of capabilities.
Has actor_methods and late bound methods.

"""
class Activity:
    def __init__(self):
        super(Activity, self).__init__()
        self.greenthread = None
        self.active = False
        self.sleeping = False
    # --------------------------
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
    # --------------------------
    def input(self, data):
        pass
    def output(self, data):
        raise Exception("base class `output` called directly - you should link over this")
    # --------------------------
    def main(self):
        while self.active:
            self.sleeping = True
            yield 1
    def stop(self):
        self.active = False
    def link(self, methodname, target):
        setattr(self, methodname, target)


class Actor(Activity):
    Behaviour = None # Should be a subclass of Activity
    def __init__(self, *args, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            raise Exception("You do not call Actor directly. Inherit and override Behaviour")
        self.inputqueue = []
        self._behaviour = (self.Behaviour)(*args, **argd)

    def handle_inqueue(self):
        call = self.inputqueue.pop(0)
        func_name, args = call[0], call[1:]
        #print(func_name, args)
        func = getattr(self._behaviour, func_name)
        func(*args)

    def main(self):
        self._behaviour.start()
        while self._behaviour.active:
            yield 1
            while (self.inputqueue  and self._behaviour.active):
                self.handle_inqueue()
            if self._behaviour.active and not self._behaviour.sleeping:
                self._behaviour.tick()

    def link(self, methodname, target):
        setattr(self._behaviour, methodname, target)

    def isactive(self):
        return self._behaviour.active
    def issleeping(self):
        return self._behaviour.sleeping

    def input(self, data):
        self.inputqueue.append(("input", data))
        self._behaviour.sleeping = False

    def link(self, *args):
        self.inputqueue.append(("link", *args))
        self._behaviour.sleeping = False

    def stop(self):
        self.inputqueue.append(("stop", ))
        self._behaviour.sleeping = False


class Producer(Actor):
    class Behaviour(Activity):
        def __init__(self, message):
            super(Producer.Behaviour, self).__init__()
            self.message = message
        def main(self):
            while True:
                yield 1
                self.output(self.message)


class Consumer(Actor):
    class Behaviour(Activity):
        def __init__(self):
            super(Consumer.Behaviour, self).__init__()
            self.count = 0
        def input(self, data):
            self.count += 1
            print(data, self.count)
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
