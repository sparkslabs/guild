#!/usr/bin/python
"""mini-guild Example

Simple producer/consumer example

"""

from miniguild import SchedulerActor, Actor, run_scheduler

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


if __name__ == "__main__":
    s = SchedulerActor()
    p = Producer("Hello")
    c = Consumer()
    p.link("output", c.munch)
    s.schedule(p, c)

    run_scheduler(s)

