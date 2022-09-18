#!/usr/bin/python
"""miniguild Example

Example of using multiple behaviours in a single actor
"""


from miniguild import Scheduler, Actor



class Door(Actor):
    class OpenBehaviour:
        def open(self):
            print("OPEN:open.  The Door is already open!")
        def close(self):
            print("OPEN:close. The door is now closed!")
            self.become(Door.ClosedBehaviour)

    class ClosedBehaviour:
        def open(self):
            print("CLOSE:open.  The door is now open!")
            self.become(Door.OpenBehaviour)
        def close(self):
            print("CLOSE:close. The Door is already closed!")

    actor_methods = ["open","close"]
    Behaviours = ClosedBehaviour, OpenBehaviour


if __name__ == "__main__":


    s = Scheduler()
    d = Door()
    s.schedule(d)

    d.open()
    d.open()
    d.close()
    d.close()
    d.open()
    d.open()

    s.run()
