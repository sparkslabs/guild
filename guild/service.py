#!/usr/bin/python

import time
import sys
import json

try:
    config = json.load(open("/etc/guildservice/config.json"))
except IOError:
    config = json.load(open("../etc/guildservice/config.json"))

logfile = "/var/log/guildservice/service.log"
start = time.time()
count = 0


def log(*what):
    global count
    count = count + 1
    f = open(logfile, "a")
    f.write(time.asctime())
    f.write(" : ")
    f.write(str(start))
    f.write(" : ")
    f.write(str(count))
    f.write(" : ")

    for thing in what:
        f.write(" ")
        f.write(str(thing))
    f.write("\n")
    f.flush()
    f.close()


def main():
    log("startup")
    log(*sys.argv)
    log(config)
    for i in range(10):
        log("testing myservice")
        time.sleep(5)


if __name__ == "__main__":
    logfile = "guild.service.log"
    main()
