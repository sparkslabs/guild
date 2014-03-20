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

    def gen_process(self):
        self.f = f = file(self.fname)
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
    g = Grep("pants").go()
    p = Printer().go()

    pipeline(f1, g, p)
    pipeline(f2, g)
    pipe(f3, "output", g, "input")

    wait_KeyboardInterrupt()
    stop(f1, f2, f3, g)
    wait_for(f1, f2, f3, g)
