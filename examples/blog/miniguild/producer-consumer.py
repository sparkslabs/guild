#!/usr/bin/python
"""mini-guild Example

Simple producer/consumer example

"""

from miniguild import Scheduler, Actor

class Producer(Actor):
    class Behaviour:
        def __init__(self, message):
            self.message = message

        def main(self):
            while True:
                yield 1
                self.output(self.message)


class Consumer(Actor):
    class Behaviour:
        def __init__(self):
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


# Single class that has both behaviours essentially
class ProducerConsumer(Actor):
    class Behaviour:
        def __init__(self, message):
            self.message = message

        def main(self):
            while True:
                yield 1
                self.output(self.message)

        def munch(self, data):
            self.count += 1
            print("Munched:", data, self.count)
            self.sleeping = True

    actor_methods = ["munch"]

if __name__ == "__main__":
    s = Scheduler()
    p = Producer("Hello")
    c = Consumer()
    p.link("output", c.munch)
    s.schedule(p, c)

    s.run()

