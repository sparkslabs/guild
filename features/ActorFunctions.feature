Feature: Actor functions
  
  In order to allow one thread to request data from another
  As a programmer
  I want to be able to use a normal function call syntax, safely
  
  Actor functions provide the capability to write normal looking functions,
  and declare then actor functions. These can then be called safely from another
  thread.
  
  NB: There is always a risk of deadlock in such a scenario, so at some point the
  ability for actor functions to timeout may be provided.
  
  Scenario: An actor's actor functions do not work when the actor isn't running
    Given we create a SimpleActor class with one actor function combine
    When we create an instance of that class
    But don't start it
    Then it can be used as normal
    But that combine actor function doesn't work

  Scenario: An actor's actor functions work as expected when the actor is running
    Given we create a SimpleActor class with one actor function combine
    When we create an instance of that class
    When we do start it
    Then it can be used as normal
    And that combine actor function works as expected

  Scenario: Failures in Actor Functions can use exceptions
    Given we create a SimpleActor class with an actor function called fails
    When we create an instance of that class
    When we do start it
    Then it can be used as normal
    And that fails actor function raises an exception in the caller thread





