#!/usr/bin/python
#
# See: http://www.sparkslabs.com/michael/blog/2014/03/07/guild---pipelinable-actors-with-late-binding/
#

import re
import sys
import time
from guild.actor import *


class Follow(Actor):
    def __init__(self, filename):
        super(Follow, self).__init__()
        self.filename = filename
        self.f = None

    def main(self):
        self.f = f = open(self.filename)
        f.seek(0, 2)   # seek to end
        while True:
            yield 1
            line = f.readline()
            if not line:  # no data, so wait
                time.sleep(0.1)
            else:
                self.output(line)

    def onStop(self):
        if self.f:
            self.f.close()


class Grep(Actor):
    def __init__(self, pattern):
        super(Grep, self).__init__()
        self.regex = re.compile(pattern)

    @actor_method
    def input(self, line):
        if self.regex.search(line):
            self.output(line)


class Printer(Actor):
    @actor_method
    def input(self, line):
        sys.stdout.write(line)
        sys.stdout.flush()


follow1 = Follow("x.log").go()
follow2 = Follow("y.log").go()
grep = Grep("pants").go()
printer = Printer().go()

pipeline(follow1, grep, printer)
pipeline(follow2, grep)
wait_KeyboardInterrupt()
stop(follow1, follow2, grep, printer)
wait_for(follow1, follow2, grep, printer)
