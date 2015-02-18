# -- FILE: features/steps/example_steps.py
from behave import given, when, then, step
from guild.actor import Actor, actor_method, actor_function, ActorNotStartedException
from hamcrest import *
import time
but = when

class UserDefinedException(Exception):
    pass

class SimpleActor(Actor):
    def __init__(self, a, b, c):
        super(SimpleActor, self).__init__()
        self.a = a
        self.b = b
        self.c = c
    #
    def __repr__(self):
        return "SimpleActor"+str((self.a,self.b,self.c))
    def geta(self): return self.a
    def getb(self): return self.b
    def getc(self): return self.c
    def seta(self,v): self.a = v
    def setb(self,v): self.b = v
    def setc(self,v): self.c = v
    #
    @actor_function(0.01)
    def combine(self):
        return (self.a, self.b, self.c)
    #
    @actor_method
    def increment(self):
        self.a += 1
        self.b += 1
        self.c += 1
    #
    @actor_function(0.01)
    def fails(self):
        raise UserDefinedException("Failed!")

@given(u'we create a SimpleActor class but use no special features')
def step_impl(context):
    context.klass = SimpleActor

@given(u'we create a SimpleActor class with one actor function combine')
def step_impl(context):
    context.klass = SimpleActor

@given(u'we create a SimpleActor class with one actor method increment and actor function combine')
def step_impl(context):
    context.klass = SimpleActor

@given(u'we create a SimpleActor class with an actor function called fails')
def step_impl(context):
    context.klass = SimpleActor


@when(u'we create an instance of that class')
def step_impl(context):
    klass = context.klass
    context.value = klass(1,2,3)

@but(u'don\'t start it')
def step_impl(context):
    assert_that(False, equal_to(context.value.is_alive()))

@when(u'we do start it')
def step_impl(context):
    context.value.go()
    assert_that(True, equal_to(context.value.is_alive()))


@then(u'that combine actor function doesn\'t work')
def step_impl(context):
    assert_that(context.value.combine, raises(ActorNotStartedException))

@then(u'that fails actor function raises an exception in the caller thread')
def step_impl(context):
    assert_that(context.value.fails, raises(UserDefinedException))

@then(u'that increment actor method doesn\'t work')
def step_impl(context):
    context.value.increment()
    time.sleep(0.01) # Microsleep to allow context.value.increment a chance to run
    v = context.value.a, context.value.b, context.value.c
    assert_that(v, equal_to((6,5,4)))


@then(u'that combine actor function works as expected')
def step_impl(context):
    assert_that((6,5,4), equal_to(context.value.combine()))

@then(u'that increment actor method works asynchronously as expected')
def step_impl(context):
    context.value.increment()
    time.sleep(0.01) # Microsleep to allow context.value.increment a chance to run
    assert_that(context.value.combine(), equal_to((7,6,5)))

@then(u'it can be used as normal')
def step_impl(context):
    print(str(context.value))
    assert_that("SimpleActor(1, 2, 3)", equal_to(str(context.value)))
    assert_that(1, equal_to(context.value.a))
    assert_that(2, equal_to(context.value.b))
    assert_that(3, equal_to(context.value.c))
    assert_that(1, equal_to(context.value.geta()))
    assert_that(2, equal_to(context.value.getb()))
    assert_that(3, equal_to(context.value.getc()))
    context.value.seta(6)
    context.value.setb(5)
    context.value.setc(4)
    assert_that(6, equal_to(context.value.geta()))
    assert_that(5, equal_to(context.value.getb()))
    assert_that(4, equal_to(context.value.getc()))

