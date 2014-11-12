#!/usr/bin/python

from __future__ import print_function

from guild.actor import Actor, actor_method, process_method, late_bind


class Dog(Actor):

    @actor_method    # Input - triggered by data coming in
    def woof(self):
        print("Woof", self)

    @process_method  # Process - triggered each time it's run
    def process(self):
        #print(" ", end="")
        pass

    @late_bind       # Output
    def produce(self):
        pass


class Shitzu(Dog):
    def __init__(self):
        self.count = 0
        super(Dog, self).__init__()

    @process_method
    def process(self):
        self.count += 1
        print("I don't go meow", self.count)
        if self.count >= 20:
            self.stop()
            return False


if __name__ == "__main__":
    import time

    dog = Dog()
    shitzu = Shitzu()

    dog.start()
    shitzu.start()
    dog.woof()
    shitzu.woof()
    time.sleep(0.1)

    shitzu.join()
    time.sleep(0.1)
    dog.stop()
    dog.join()
