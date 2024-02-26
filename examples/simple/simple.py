#!/usr/bin/python


from guild.actor import Actor, actor_method, process_method, late_bind

class Kitten(Actor):
    def __init__(self):
        self.count = 0
        super(Kitten, self).__init__()

    @actor_method 
    def meow(self):
        print("Woof", self)

    def main(self):
        print("MAIN")
        while True:
            self.count += 1
            print(self, "I don't go woof", self.count)
            time.sleep(0.2)
            if self.count >= 10:
                self.stop()
            yield 1



if __name__ == "__main__":
    import time

    kitten = Kitten()
    print("post-create")
    time.sleep(1)

    kitten.start()
    print("post-start")
    time.sleep(1)

    kitten.meow()
    print("post-meow")
    time.sleep(1)

    kitten.stop()
    print("post-stop")
    time.sleep(1)

    kitten.join()
    print("post-join")
    time.sleep(1)

