#!/usr/bin/python

from distutils.core import setup
import os

def is_package(path):
    return (
        os.path.isdir(path) and
        os.path.isfile(os.path.join(path, '__init__.py'))
        )

def find_packages(path, base="" ):
    """ Find all packages in path """
    packages = {}
    for item in os.listdir(path):
        dir = os.path.join(path, item)
        if is_package( dir ):
            if base:
                module_name = "%(base)s.%(item)s" % vars()
            else:
                module_name = item
            packages[module_name] = dir
            packages.update(find_packages(dir, module_name))
    return packages

packages = find_packages(".")
package_names = packages.keys()

setup(name = "guild",
      version = "1.3.7",
      description = "An Actor library supporting concurrency using pipelinable pythonic actors",
      author='Michael Sparks (sparkslabs)',
      author_email="sparks.m@gmail.com",
      url = "http://sparkslabs.com/michael/",
      license ="Apache Software License",
      packages = package_names,
      package_dir = packages,
      long_description = """
Python-Guild
============

Abstract
--------

Guild is a basic pipelineable Actor system, currently based around
threads and a developer friendly syntax. In particular it introduces 2
notions to an actor system - the idea of late binding, and of having
common names (or aliases) for the purposes of enabling pipelining.

It's inspired by Kamaelia, but with all the ugly parts removed.

The ability to have dynamic actor methods would be useful.

Michael.

Introduction/Overview
---------------------

At present the documentation is the code itself. That's not great
documentation, so this file consists of an overview of Guild.

Guild is a python library for creating thread based applications.

Threads are represented using actors - objects with threadsafe methods.
Calling a method puts a message on an inbound queue for execution within
the thread. Guild actors can also have stub actor methods, representing
output. These are stub methods which are expected to be rebound to actor
methods on other actors. These stub methods are called late bind
methods. This allows pipelines of Guild actors to be created in a
similar way to Unix pipelines.

Additionally, Guild actors can be active or reactive. A reactive actor
performs no actions until a message is received. An active guild actor
can be active in two main ways: it can either repeatedly perform an
action, or more complex behaviour can use a generator in a coroutine
style. The use of a generator allows Guild actors to be stopped in a
simpler fashion than traditional python threads. Finally, all Guild
actors provide a default 'output' late-bindable method, to cover the
common case of single input, single output.

Finally, Guild actors are just python objects and actors with additional
functionality - it's designed to fit in with your code, not the other
way round. This post covers some simple examples of usage of Guild, and
how it differs (slightly) from traditional actors.

Getting and Installing
----------------------

Installation is pretty simple:

::

    $ git clone https://github.com/sparkslabs/guild
    $ cd guild
    $ sudo python setup.py install

If you'd prefer to build, install and use a debian package:

::

    $ git clone https://github.com/sparkslabs/guild
    $ cd guild
    $ make deb
    $ sudo dpkg -i ../python-guild_1.0.0_all.deb

Example: viewing a webcam
-------------------------

This example shows the use of two actors - webcam capture, and image
display. The thing to note here is that we could easily add other actors
into the mix - for network serving, recording, analysis, etc. If we did,
the examples below can be reused as is.

First of all the code, then a brief discussion.

::

    import pygame, pygame.camera, time
    from guild.actor import *
    pygame.camera.init()

    class Camera(Actor):
        def main(self):
            camera = pygame.camera.Camera(pygame.camera.list_cameras()[0])
            camera.start()
            while True:
                yield 1
                frame = camera.get_image()
                self.output(frame)
                time.sleep(1.0/50)

    class Display(Actor):
        def __init__(self, size):
            super(Display, self).__init__()
            self.size = size

        def process_start(self):
            self.display = pygame.display.set_mode(self.size)

        @actor_method
        def show(self, frame):
            self.display.blit(frame, (0,0))
            pygame.display.flip()

        input = show

    camera = Camera().go()
    display = Display( (800,600) ).go()
    pipeline(camera, display)
    time.sleep(30)
    stop(camera, display)
    wait_for(camera, display)

In this example, Camera is an active actor. That is it sits there,
periodically grabbing frames from the webcam. To do this, it uses a
generator as a main loop. This allows the fairly basic behaviour of
grabbing frames for output to be clearly expressed. Note also this actor
does use the normal blocking sleep function.

The Display Actor initialises by capturing the passed parameters. Once
the actor has started, its process\_start method is called, enabling it
to create a display, it then sits and waits for messages. These arrive
when a caller calls the actor method 'show' or its alias 'input'. When
that happens the upshot is that the show method is called, but in a
threadsafe way - and it simply displays the image.

The setup/tear down code shows the following:

-  Creation of, and starting of, the Camera actor
-  Creation and start of the display
-  Linking the output of the Camera to the Display
-  The main thread then waits for 30 seconds - ie it allows the program
   to run for 30 seconds.
-  The camera and display actors are then stopped
-  And the main thread waits for the child threads to exit before
   exitting itself.

This could be simplified (and will be), but it shows that even though
the actors had no specific shut down code, they shut down cleanly this
way.

Example: following multiple log files looking for events
--------------------------------------------------------

This example follows two log files, and grep/output lines matching a
given pattern. In particular, it maps to this kind of command line:

::

    $ (tail -f x.log & tail -f y.log) | grep pants

This example shows that there are still some areas that would benefit
from additional syntactic sugar when it comes to wiring together
pipelines. In particular, this example should be writable together like
this:

::

    Pipeline( Parallel( Follow("x.log"), Follow("y.log"),
              Grep("pants"),
              Printer() ).run()

However, I haven't implemented the necessary chassis yet (they will be).

Once again, first the code, then a discussion.

::

    from guild.actor import *
    import re, sys, time

    class Follow(Actor):
        def __init__(self, filename):
            super(Follow, self).__init__()
            self.filename = filename
            self.f = None

        def main(self):
            self.f = f = file(self.filename)
            f.seek(0,2)   # seek to end
            while True:
                yield 1
                line = f.readline()
                if not line: # no data, so wait
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

As you can see, like the bash example, we have two actors that
tail/follow two different log files. These both feed into the same
'grep' actor that matches the given pattern, and these are finally
passed to a Printer actor for display. Each actor shows slightly
different aspects of Guild's model.

-  **Follow** is an active actor. It captures the filename to follow in
   the initialiser, and creates a placeholder for the associated file
   handle. The main loop them follows the file, calling its output
   method when it has a line. Finally, it will continue doing this until
   its .stop() method is called. When it is, the generator is killed
   (via a StopIteration exception being passed in), and the actor's
   onStop method is called allowing the actor to close the file.

-  **Grep** is a simple reactive actor with some setup. In particular,
   it takes the pattern provided, compiles a regex matcher using it.
   Then any actor call to its input method results in any matching lines
   to be passed through via its output method.

-  **Printer** is a simple reactive actor. Any actor call to its input
   method results in the data passed in being sent to stdout.

Work in progress
^^^^^^^^^^^^^^^^

**It is worth noting that Guild at present is not a mature library
yet,** **but is sufficiently useful for lots of tasks.** In particular,
one area Guild will improve on in - specifying coordination more
compactly. For example, the Camera example could become:

::

    Pipeline( Camera(),  Display( (800,600) ) ).run()

That's a work in progress however, adding with other chassis, and other
useful parts of kamaelia.

What are actors?
----------------

Actors are threads with a mailbox allowing them to receive and act upon
messages. In the above webcam example, it has 2 threads, one for
capturing images, and one for display. Images from the webcam end up in
the mailbox for the display, which displays images it receives. Often
actor libraries wrap up the action of sending a message to the mailbox
of an actor via a method on the thread object.

The examples above demonstrate this above via the decorated methods:

-  Display.show, Grep.input, Printer.input

All of these methods - when called by a client of the actor - take all
the arguments passed in, along with their function and place on the
actor's mailbox (a thread safe queue). The actor then has a main loop
that checks this mailbox and executes the method within the thread.

How does Guild differ from the actor model?
-------------------------------------------

In a traditional actor model, the code in the camera Actor might look
like this:

::

    import pygame, pygame.camera, time
    from guild.actor import *
    pygame.camera.init()

    class Camera(Actor):
        def __init__(self, display):
            super(Camera, self).__init__()
            self.display = display

        def main(self):
            camera = pygame.camera.Camera(pygame.camera.list_cameras()[0])
            camera.start()
            while True:
                yield 1
                frame = camera.get_image()
                self.display.show(frame)
                time.sleep(1.0/50)

-  **NB: This is perfectly valid in Guild.** If you don't want to use
   the idea of late bound methods or pipelining, then it can be used
   like any other actor library.

If you did this, the display code would not need any changes. The
start-up code that links things together though would now need to look
like this:

::

    display = Display( (800,600) ).go()
    camera = Camera(display).go()
    # No pipeline line anymore
    time.sleep(30)
    stop(camera, display)
    wait_for(camera, display)

On the surface of things, this looks like a simplification, and on one
level it is - we've removed one line from the program start-up code. Our
camera object however now has its destination embedded at object
initialisation and it's also become more complex, with zero increase in
flexibility. In fact I'd argue you've *lost* flexibility, but I'll leave
why for later.

For example, suppose we want to record the images to disk, we can do
this by adding a third actor that can sit in the middle of others:

::

    import time, os
    class FrameStore(Actor):
        def __init__(self, directory='Images', base='snap'):
            super(FrameStore, self).__init__()
            self.directory = directory
            self.base = base
            self.count = 0

        def process_start(self):
            os.makedir(self.directory)
            try:
                os.makedirs("Images")
             except OSError, e:
                if e.errno != 17: raise

        @actor_method
        def input(self, frame):
            self.count += 1
            now = time.strftime("%Y%m%d-%H%M%S",time.localtime())
            filename = "%s/%s-%s-%05d.jpg" % (self.directory, self.base, now, self.count)
            pygame.image.save(frame, filename)
            self.output(frame)

This could then be used in a Guild pipeline system this way:

::

    camera = Camera().go()
    framestore = FrameStore().go()
    display = Display( (800,600) ).go()
    pipeline(camera, framestore, display) 
    time.sleep(30)
    stop(camera, framestore, display) 
    wait_for(camera, framestore, display)

It's for this reason that Guild supports late bindable actor methods.

What's happening here is that the definition of Actor includes this:

::

    class Actor(object):
        #...
        @late_bind_safe
        def output(self, *argv, **argd):
            pass

That means every actor has available "output" as a late bound actor
method.

This pipeline called:

::

    pipeline(camera, display)

Essentially does this:

::

    camera.bind("output", display, "input")

This transforms to a threadsafe version of this:

::

    camera.output = display.input

As a result, it replaces the call camera.output with a call to
display.input for us - meaning that it is as efficient to do
camera.output as it is to do self.display.show in the example above -
but significantly more flexible.

There are lots of fringe benefits of this - which are best discussed in
later posts, but this does indicate best how Guild differs from the
usual actor model.


Why write and release this?
---------------------------

In late 2013/early 2013, I was working on a project with an aim of
investigating various ideas relating to of the Internet of Things.  (In
particular, which definition of that really mattered to us, why, and what
options it provided)

As part of that project, I wrote a small/just big enough library
suitable for testing some ideas I'd had regarding integrating some ideas
in Kamaelia, with the syntactic sugar in the actor model. Essentially,
to map Kamaelia's inboxes and messages to traditional actor methods, and
maps outboxes to late bound actor methods. Use of standard names and/or
aliases would allow pipelining.

Guild was the result, and it's proven itself useful in a couple of
projects, hence its packaging as a standalone library. Like all such
things, it's a work in progress, but it also has a cleaner to use
version of Kamaelia's STM code, and includes some of the more useful
components like pipelines and backplanes.

If you find it useful or spot a typo, please let me know.
""",
      )
