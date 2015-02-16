Feature: Actors operate like a normal class

  In order to simplify shifting code into threads cleanly
  As a programmer
  I want to be able to use actors like normal classes
  
  The idea being here is to be able to take a normal class, call it an actor
  and have incremental development. ie mark it an actor, and test, then switch
  some things into threads, and then wait.

  Scenario: An actor is just a class
    Given we create a SimpleActor class but use no special features
    When we create an instance of that class
    Then it can be used as normal
