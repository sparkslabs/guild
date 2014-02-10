#!/usr/bin/python

import time

from guild.av import WebCamTest, SomeDisplay, AudioCapture, WaveWriter
from guild.actor import *

wct = WebCamTest()
d = SomeDisplay()
ac = AudioCapture()
ww = WaveWriter()

pipe(wct, "produce", d, "show")
pipe(ac, "output", ww, "record")

start(wct, d, ac, ww)

time.sleep(6)

stop(wct, d, ac, ww)
wait_for(wct, d, ac, ww)
