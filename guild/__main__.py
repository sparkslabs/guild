#!/usr/bin/python

from __future__ import print_function

print("Guild Self Test")

print("  ... test service registry")
import guild
guild.init()
guild.register("hello", 5)
x = guild.lookup("hello")
assert x == 5
print("Self test successful")
