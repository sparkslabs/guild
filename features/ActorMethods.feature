Feature: Actor methods

  In order to allow one thread to call functionality in another (inc pass data)
  As a programmer
  I want to be able to use a normal function call syntax, safely

  Actor methods allow us to call a method on an actor and for the actor to then
  process the method call at a time of its choosing. As a result there is an
  inherent delay here. What actually happens is the method call causes work to
  be added to an inbound queue which is processed later, using the method we've
  decorated as an actor method.
  
  Actors do not try to *hide* functionality they have - just make it safer to
  work with. For example, access to internal attributes is possible, but recommended
  against.

  Scenario: An actor's actor methods do not work when the actor isn't running
    Given we create a SimpleActor class with one actor method increment and actor function combine
    When we create an instance of that class
    But don't start it
    Then it can be used as normal
    But that increment actor method doesn't work

  Scenario: An actor's actor methods run asynchronously to other threads when the actor is running
    Given we create a SimpleActor class with one actor method increment and actor function combine
    When we create an instance of that class
    When we do start it
    Then it can be used as normal
    And that increment actor method works asynchronously as expected
