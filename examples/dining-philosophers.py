#!/usr/bin/python

import time
import random

import guild
from guild.actor import Actor, stop, wait_for, start
from guild.stm import Store

ONTABLE = True
PICKEDUP = False


def make_and_lay_table(number_people_table_seats):
    # We know that these operations will all succeed
    table = Store()

    size = table.checkout("size")
    size.set(number_people_table_seats)
    size.commit()

    for forkid in range(number_people_table_seats):
        fork = table.checkout("fork"+str(forkid))
        fork.set(ONTABLE)
        fork.commit()

    return table


class Philosopher(Actor):
    min_munch_time = 1
    def __init__(self, table, seat):
        super(Philosopher, self).__init__()
        self.table = table
        self.seat = seat
        tablesize = table.checkout("size").value  # Assume the table does not change in size!
        self.left = "fork" +str(self.seat)
        print(self.seat, tablesize)
        if self.seat == tablesize-1:
            self.right = "fork0"
        else:
            self.right = "fork"+str(self.seat + 1)
        self.eaten = 0
        print(id(self), ": START", seat, self.left, self.right)

    def think(self):
        print(id(self), ":", "Thinking...", end="")  
        time.sleep(random.random()*0.1)
        print(" ... done")

    def pickup(self):
        table = self.table.checkout()
        try:
            with table.changeset(self.left, self.right) as c:
                if (c[self.left].value == ONTABLE) and (c[self.right].value == ONTABLE):
                    c[self.left].set(PICKEDUP)
                    c[self.right].set(PICKEDUP)
                else:
                    print("Could only get one fork - trying later")
                    return False
        except guild.stm.BusyRetry:
            print(id(self), ":", "FAILED TO PICK UP")
            return False
        time.sleep(self.min_munch_time)
        print(id(self), ":", "Picked up", self.left, self.right)
        return True

    def eat(self):
        print(id(self), ":", "Eating!")
        self.eaten += 1
        time.sleep(random.random()*0.6)

    def dropforks(self):
        table = self.table.checkout()
        while True: # Keep retrying until success
            try:
                with table.changeset(self.left, self.right) as c:
                    c[self.left].set(ONTABLE)
                    c[self.right].set(ONTABLE)
                print(id(self), ":", "Put down forks", self.left, self.right)
                break
            except guild.stm.BusyRetry:
                pass

    def main(self):
        while True:
            yield 1
            self.think()
            got_forks = self.pickup()
            if got_forks:
                self.eat()
                self.dropforks()
                got_forks = False


attendees = 7

table = make_and_lay_table(attendees)

ps = []
for i in range(attendees):
   p = Philosopher(table, i)
   p.min_munch_time = 1
   ps.append(p)

start(*ps)

time.sleep(10)


stop(*ps)
wait_for(*ps)

for p in ps:
    print(id(p), ":", "ATE", p.eaten)
