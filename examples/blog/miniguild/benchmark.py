#!/usr/bin/python
"""
Mini Guild Benchmark

"""

import miniguild

from miniguild import Scheduler, Actor

class RingPinger(Actor):
    class Behaviour:
        def __init__(self, next_actor=None):
            self.next_actor = next_actor
            self.start = time.time()

        def ping(self, message):
            if message[0] == self._wrapper:
                now = time.time()
                self.start = now

                if message[1] == 1:
                    self._wrapper.stop()
                message[1] -= 1
                self.next_actor.ping(message)
            else:
                self._wrapper.sleeping = True
                if message[1] == 1:
                    self._wrapper.stop()
                self.next_actor.ping(message)

        def set_next(self, next_actor):
            self.next_actor = next_actor

        def startping(self, first, last, M, N):
            first.set_next(last)
            last.ping( [first, M] )

    actor_methods = ["ping","set_next","startping"]


if __name__ == "__main__":
    import sys
    import time
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("     ", sys.argv[0], "<num actors> <num times round ring>")
        sys.exit(0)

    N = int(sys.argv[1])
    M = int(sys.argv[2])
    print("n, m", repr(N), repr(M))

    first = RingPinger()
    last = first
    pingers = [first]
    for _ in range(N):
        last = RingPinger(last)
        pingers.append(last)

    def init():
        first.startping(first, last, M, N)

    s = Scheduler(initialise = init)
    s.schedule(*pingers)


    start = time.time()
    print("START", start, time.asctime())


    s.run()

    end = time.time()
    print("END  ", end, time.asctime())
    print("DURATION:", end-start)
    print("Rate:", int((N*M)/(end-start)+0.5), "messages/sec")
