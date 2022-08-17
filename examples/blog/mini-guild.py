#!/usr/bin/python
"""mini-guild

A simplified version of guild without the full set of capabilities.
Has actor_methods and late bound methods.

"""
def mkActorMethod(self, func_name):
    def actor_method(*args, **argd):
        self.inputqueue.append((func_name, args, argd))
    return actor_method

class Actor:
    Behaviour = None # Override with your behaviour, doesn't have to be a special class
    Behaviours = []
    default_actor_methods = ["input"]
    actor_methods = []

    def __init__(self, *args, **argd):
        super(Actor, self).__init__()
        if self.Behaviour is None:
            if self.Behaviours != []:
                self.Behaviour = self.Behaviours[0]
            else:
                raise Exception("You do not call Actor directly. Inherit and override Behaviour")
        self.args = args
        self.argd = argd
        self.greenthread = None
        self.inputqueue = []
        self.become(self.Behaviour)
        self.active = False
        self.sleeping = False

    def initialiseBehaviour(self, *args, **argd):
        self._behaviour = (self.Behaviour)(*args, **argd)
        for name in self.default_actor_methods + self.actor_methods:
            if name in self.Behaviour.__dict__:
                setattr(self, name, mkActorMethod(self, name))
        self._behaviour.become = self.become
        if not hasattr(self._behaviour, "tick"):
            self._behaviour.tick = lambda *args: None

    def become(self, behaviour_class):
        self.Behaviour = behaviour_class
        self.initialiseBehaviour(*self.args, **self.argd)

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
        func_name, argv, argd = call[0], call[1], call[2]
        #print(func_name, args)
        func = getattr(self._behaviour, func_name)
        func(*argv, **argd)

    def main(self):
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

        def munch(self, data):
            self.count += 1
            print("Munched:", data, self.count)
            self.sleeping = True

    actor_methods = ["munch"]


class Door(Actor):
    class OpenBehaviour:
        def open(self):
            print("OPEN:open.  The Door is already open!")
        def close(self):
            print("OPEN:close. The door is now closed!")
            self.become(Door.ClosedBehaviour)

    class ClosedBehaviour:
        def open(self):
            print("CLOSE:open.  The door is now open!")
            self.become(Door.OpenBehaviour)
        def close(self):
            print("CLOSE:close. The Door is already closed!")

    actor_methods = ["open","close"]
    Behaviours = ClosedBehaviour, OpenBehaviour


if __name__ == "__main__":

    p = Producer("Hello").start()
    c = Consumer().start()
    d = Door().start()

    d.open()
    d.open()
    d.close()
    d.close()
    d.open()
    d.open()
    d.tick()
    d.tick()
    d.tick()
    d.tick()
    d.tick()
    d.tick()

    p.link("output", c.munch)

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
