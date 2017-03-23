# A Guild Overview / Reference

## Key aspects?

Some of the key aspects of guild are:

* Syntax/API is thought of upfront - no one wants to write or maintain
  code they don't like

* Thread oriented. By default actors are threads, and run in their own
  threads. For many linux based servers this is perfectly sufficient.

* It's an actor system that also allows output methods to be late bound
  to input methods of other actors. This allows composition of actors
  into arbitrary pipelines and graphs. Being explicit about this makes the
  syntax of usage a lot clearer

* Actor methods - these are thread safe procedure calls, which will run.
  asynchronous to the caller. Non-blocking.

* Actor functions - these are thread safe function calls. A call to one
  sends the arguments over a threadsafe queue to the actor, and the results
  also come back along a threadsafe queue. These are therefore blocking.
  
  These calls include a timeout.
  
  Furthermore, any exceptions raised in the actor function - which isn't running
  in your thread, are propogated to your thread. This is remarkably powerful
  since it also allows you to have cross thread exceptions safely.

* Late binding (output) methods - these are equivalent to kamaelia's outbox
  concept. For example, a webcam may capture images and called "output". If
  this isn't bound to another actor's input, the image will either fall on the
  floor, or cause an error to be raised.

* This allows a higher leverl thing to bind a late binding output methods
  to an actor methods (such as a "display" method).

* Software transactional memory as a way of sharing data snapshots. For those
  that haven't used STM, it's very similar to version control, just applied to
  variables rather than files.


## Similarities to Kamaelia?

Guild is derived in some levels from my previous work on Kamaelia. Clearly
everything in the previous section is different from kamaelia, so what's
similar?

In Kamaelia's Axon there were a number of different concepts:

  * Inboxes
  * Outboxes
  * The co-ordinating assistant tracker
  * Services
  * "Dynamic" Calls to services
  * Simple software transactional memory
  * A scheduler

In Guild there are similar capabilities:
  * Late bound methods are equivalent to outboxes
  * Actor Methods are equivalent to inboxes
  * Software transactional memory has better support and better syntax
  * System wide services register
      * Replaces the CAT


### Public API Summary

#### guild.actor.py

**System Flags**

* **`guild.actor.strace`**

**Exception classes**

The following exceptions may be raised by the API.

* **`class guild.actor.ActorException(Exception)`** -- Should be the base class for the next two exceptions, but for some reason we didn't do that. Is used as a baseclass in other system parts though.
* **`class guild.actor.UnboundActorMethod(Exception)`** - raisedif an unbound late-bindable method is called.
* **`class guild.actor.ActorNotStartedException(Exception)`** -- Call to an actor function times out. One reason this can be is if the actor is not started, if that's the case this exception will be raised.



**User base classes**

**`class guild.actor.Actor(ActorMixin, _Thread)`**

Default actor base class. You normally want to subclass this. Read in conjunction with ActorMixin

Methods:
  * `__init__(self)` - (no arguments) you need to call this if you override `__init__`
  * `run(self)` - Don't override this. Handles the mechanics of running the actor
  * `stop(self)` - Don't override this. Sets self.killflag in the actor object
    so that it shuts down cleanly


**`class ActorMixin(object)`**

Note this contains the bulk of the core mechanics for communications with the actor.

Methods you can/should override:

  * `__init__(self, *argv, **argd)`
  * `process_start(self)`
  * `@process_method` `process(self)`
  * `@actor_method` `input(self, *argv, **argd)`

Methods you can/should override, but you don't call:
  * `onStop(self)`

Methods you should not override but can call:

  * `@late_bind_safe` `output(self, *argv, **argd)`
  * `@actor_method` `bind(self, source, dest, destmeth)`
  * `go(self)`

Methods you should not override, nor directly call:
  * `interpret(self, command)`
  * `_actor_notify(self)`
  * `_actor_do_queued(self)`

**Method Decorators**

These decorators don't actually create new valid functions. They're
used to tag functions with various data, so that new functions
can be created by the metaclass.

This seemed like a good idea at the time. It means things like inheritance
tend to work more correctly.

  * guild.actor.actor_method(method) - decorator that turns the method into an actor method. Calls to this result in a request to call the method inside the actor's thread. This therefore returns immediately.

  * guild.actor.actor_function(timeout=None) - decorator that turns the method into an actor function. Calls to this result in a request to call the method inside the actor's thread, but also to reply back to the caller thread along a threadsafe pipe. This therefore does not return immediately. Furthermore any exception raised inside the actor thread as a result of the function call is propogated back to the caller.

  * guild.actor.process_method(method): return ("PROCESSMETHOD", method)

  * guild.actor.late_bind_safe(method): return ("LATEBINDSAFE", method)

  * guild.actor.late_bind(method): return ("LATEBIND", method)

  * guild.actor.actor_method_lossy_queue(length) - decorator that turns the method into an actor method. Beyond that the queue has a maximum size. If you try to make a call and the queue is full, it will silently fail. **NOTE: Not actually implemented(!)**

  * guild.actor.actor_method_max_queue(length) - decorator that turns the method into an actor method. Beyond that the queue has a maximum size. If you try to make a call and the queue is full, you'll get an exception. **NOTE: Not actually implemented(!)**


**User functions**

* **`guild.actor.pipe(source, source_box, sink, sinkbox)`** --

* **`guild.actor.pipeline(*actors)`** - for all processes pipe(pred, "output", succ, "input")

* **`guild.actor.wait_for(*actors)`** - wait for each actor - in the sequence give - to exit. This is done via a thread.join()

* **`guild.actor.stop(*actors)`** - send a stop message to given actors

* **`guild.actor.start(*actors)`** - start the given actors, in that sequence.

* **`guild.actor.wait_KeyboardInterrupt()`** - Utility - just checks for keyboard interrupt and then exits



### *PRIVATE* API Summary

**functions**

These aren't 'private', but they not part of the public API, so beware of
using them outside of the implementation of guild.

* **`guild.actor.Print`** - prints arguments to stderr, and flushes immediately. The flushing is useful when debugging things internally to guild.




**Metaclass**

**`class guild.actor.ActorMetaclass(type)`**

We're creating a class with custom behaviour based on information known when
the class is created. That means we have a metaclass. The metaclass is used
to turn what look like function calls into things like actor methods, actor
functions, late methods, process methods etc.

Remember a metaclass works as follows.

* A class statement is a statement, not a declaration
* It's a very fancy way of constructing a dictionary, with some metadata
* The meta data is:
   * The classname
   * The bases the class inherits from
* The dictionary is:
   * A map of names to values
   * The names are attributes of the class
   * Normally, based on the values:
    * Simple values are simple class attributes.
    * Functions become methods in the class

Our decorators change this, such that values that would be functions into values that are tuples. Those tuples are things like: `("ACTORMETHOD", <function object>)` . I describe this as a *tagged functions*, with the tag in this example being `ACTORMETHOD`.

This means our dictionary contains the following things:

* Simple values - these will become class attributes
* Functions - these will become normal methods
* tagged functions - these will be transformed into methods that
  operate inbound queues to the object, and in some cases interact
  with outbound queues.

For each tag / tuple type:

* `(ACTORFUNCTION, function, timeout)` - creates an actor function with the
  timeout period provided by the user. If there's a timeout, the
  _Queue.Empty exception is propogated to the caller

* `(ACTORMETHOD, function)` - appends a request to the inbound queue
  to the actor. The request says "call this function with any provided
  arguments". An actor method is equivalent to Kamaelia's idea of
  inboxes.

* `(ACTORMETHOD, function, maxqueue)` - **NOT CURRENTLY IMPLEMENTED**

* `(ACTORFUNCTION, function, timeout)` - creates an actor function with a
  timeout period of 5 seconds. If there's a timeout, the _Queue.Empty
  exception is propogated to the caller

* `(PROCESSMETHOD, function)` - Similar to an actor method. When called,
  it results in a request to call "function" being added to the run list.
  However, when it's executed by the core, if it returns a value that
  is not false, the process method will be called again and again.
  
  **NOTE:** This might seem a little esoteric, and it's actually turned out to
  not be used, so this may well disappear.

* `(LATEBIND, function)` - See LATEBINDSAFE next
* `(LATEBINDSAFE, function)` - Effectively defines an actor method. HOWEVER,
  this actor method is intended to be called by **this** actor. The reason for
  this is because the actor is expecting this method to actually be replaced
  at run time by a call to a different actors method. (This such latebound
  methods are logically outboxes). The difference between them:

  * LATEBINDSAFE functions have a function body that can provide a minimally
    sufficient implementation in the event that the user of the actor does
    not provide an output.

  * LATEBIND functions are designed to crash the actor in the event that
    no one binds anything to the output. It's preferable that things should
    generally be latebindsafe.

For example, a simple echo protocol actor looks like this:

    class EchoProtocol(Actor):
        @actor_method
        def input(self, chunk):
            self.output(chunk)

        @late_bind_safe
        def output(self, chunk):
            pass

In this example, note that the actor method `input` recieves chunks from
the outside world, and the late bindable method `output` effectively
specifies what the `output` function should look like. This then allows the
input actor method to directly use the output method, expecting it to be
rebound later to something useful.

In the example above, if the output was not connected anywhere, any data
sent to that output would disappear.

If it was vital for this protocol to ensure that data was only sent to
the output if and only if the output was connected, it could be rewritten
as follows:

    class EchoProtocolParanoid(Actor):
        def __init__(self):
            super(EchoProtocolParanoid, self).__init__()
            self.data_out_queue = []

        @actor_method
        def input(self, chunk):
            if chunk is not None:
                self.data_out_queue.append(chunk)
            while len(self.data_out_queue)>0:
                chunk = self.data_out_queue[0]
                try:
                    self.output(chunk)
                    self.data_out_queue.pop(0)
                except UnboundActorMethod as e:
                    # Re-request this method to be re-run later
                    self.input(None) 
                    break

        @late_bind
        def output(self, chunk):
            pass

This is clearly more complex, so it's clear that late_bind_safe methods
are preferable, so long as you're aware that any data sent to an output
may not be connected.

The advantage of this however is that it allows you to test actors
independently of the system they're going into.


