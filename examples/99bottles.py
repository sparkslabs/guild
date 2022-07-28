#!/usr/bin/python
"""
This is what the 99 bottles idea looks like here.

"tail -f /var/log/system.log |grep pants"

This defines:
   * "tail -f" as Follow
   * "grep" as Grep

However, as noted on the wiki page here:
  - https://wiki.python.org/moin/Concurrency/99Bottles

This version here does the more complex version of following multiple
files simultaneously, and piping into 1 grep actor.

The simplest way of running this example is as follows:

    rm -f x.log y.log z.log
    touch x.log y.log z.log
    ./99bottles.py &
    for i in `seq 1 10`; do echo "x:`date`:$i" >> x.log; echo "y:`date`:$i" >> y.log; echo "z:`date`:$i" >> z.log; sleep 1; done



"""

import re
import sys
import time

from guild.actor import *


class Follow(Actor):
    def __init__(self, fname):
        self.fname = fname
        self.f = None
        super(Follow, self).__init__()

    def main(self):
        self.f = f = open(self.fname)
        f.seek(0, 2)  # go to the end
        while True:
            yield 1
            l = f.readline()
            if not l:  # no data
                time.sleep(.1)
            else:
                self.output(l)

    def onStop(self):
        if self.f:
            self.f.close()

    @late_bind
    def output(self, line):
        pass


class Grep(Actor):
    def __init__(self, pattern):
        self.regex = re.compile(pattern)
        super(Grep, self).__init__()

    @actor_method
    def input(self, line):
        if self.regex.search(line):
            self.output(line)

    @late_bind
    def output(self, line):
        pass


class Printer(Actor):
    @actor_method
    def input(self, line):
        sys.stdout.write(line)
        sys.stdout.flush()


if __name__ == "__main__":
    f1 = Follow("x.log").go()
    f2 = Follow("y.log").go()
    f3 = Follow("z.log").go()
    g = Grep(":").go()
    p = Printer().go()

    pipeline(f1, g, p)
    pipeline(f2, g)
    pipeline(f3, g)

    wait_KeyboardInterrupt()
    stop(f1, f2, f3, g, p)
    wait_for(f1, f2, f3, g, p)
