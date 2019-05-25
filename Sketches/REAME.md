# Sketches

This is the usual sketches directory. In here may be things that work or
don't. If they're in here, they're to capture playing around with stuff and
may or may not work. They might seem a good idea. They might seem a bad
idea. But they're sketches, don't judge :-)

Current Sketches:

* `threadtest` - playing around with C++11 threads. Been a while since been
  back to basics.
* `actortest` - simplest possible wrapper around threads to present a simple
   actor API.  In guild terms to create a simple "process_method" actor.  As
   time goes on this will probably be replaced by something more
   appropriate, but for now this works well enough and can be overridden by
   subclasses as required.
* `queuetest` - not started yet, but one of the basics of any actor system
  is the ability to send messages into another actor from another one.  So
  clearly, we ought to have seome sort of queueing system.  This will
  probably morph into a `mailboxtest`.

Once that's running, will look at how to implement the function call
semantics used by Guild, since this does result in usefully clean code.

Perhaps worth noting that while these sketches clearly have a purpose and
path, they'll likely *inform* the API that gets made into a library, rather
than be the final API.
